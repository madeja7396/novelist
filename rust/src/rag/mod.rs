//! High-performance RAG (Retrieval-Augmented Generation)
//!
//! Features:
//! - Fast vector similarity search with SIMD
//! - Memory-efficient indexing
//! - Multi-threaded indexing
//! - Incremental updates

use ndarray::{Array1, Array2, ArrayView1};
use parking_lot::RwLock;
use rayon::prelude::*;
use std::collections::HashMap;

pub mod embedding;

pub use embedding::{Embedding, SimpleEmbedder};

/// Document for RAG
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Document {
    pub id: String,
    pub content: String,
    pub source: String,
    pub doc_type: DocType,
    pub metadata: HashMap<String, String>,
    #[serde(skip)]
    pub embedding: Option<Array1<f32>>,
}

#[derive(Debug, Clone, Copy, PartialEq, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DocType {
    Bible,
    Character,
    Fact,
    Chapter,
    SceneSpec,
    Other,
}

/// Search result
#[derive(Debug, Clone)]
pub struct SearchResult {
    pub doc: Document,
    pub score: f32,
    pub rank: usize,
}

/// High-performance vector retriever
pub struct Retriever {
    documents: RwLock<Vec<Document>>,
    embeddings: RwLock<Option<Array2<f32>>>,
    embedder: SimpleEmbedder,
    dimension: usize,
}

impl Retriever {
    pub fn new(dimension: usize) -> Self {
        Self {
            documents: RwLock::new(Vec::new()),
            embeddings: RwLock::new(None),
            embedder: SimpleEmbedder::new(dimension),
            dimension,
        }
    }

    /// Add document
    pub fn add_document(&self, mut doc: Document) {
        // Generate embedding
        let embedding = self.embedder.embed(&doc.content);
        doc.embedding = Some(embedding);

        let mut docs = self.documents.write();
        docs.push(doc);

        // Invalidate embeddings matrix
        *self.embeddings.write() = None;
    }

    /// Add multiple documents (parallel)
    pub fn add_documents(&self, docs: Vec<Document>) {
        if docs.is_empty() {
            return;
        }

        // Generate embeddings in parallel
        let docs_with_embeddings: Vec<_> = docs
            .into_par_iter()
            .map(|mut doc| {
                let embedding = self.embedder.embed(&doc.content);
                doc.embedding = Some(embedding);
                doc
            })
            .collect();

        let mut docs_lock = self.documents.write();
        let was_empty = docs_lock.is_empty();
        docs_lock.extend(docs_with_embeddings);

        if was_empty {
            // Fast path: when index was empty, materialize embedding matrix now.
            let n_docs = docs_lock.len();
            let mut data = Vec::with_capacity(n_docs * self.dimension);
            for doc in docs_lock.iter() {
                if let Some(emb) = &doc.embedding {
                    data.extend(emb.iter().copied());
                } else {
                    data.extend(std::iter::repeat_n(0.0f32, self.dimension));
                }
            }

            let matrix = Array2::from_shape_vec((n_docs, self.dimension), data).ok();
            *self.embeddings.write() = matrix;
        } else {
            *self.embeddings.write() = None;
        }
    }

    /// Build index (create embeddings matrix)
    pub fn build(&self) {
        let docs = self.documents.read();

        if docs.is_empty() {
            return;
        }

        if let Some(existing) = self.embeddings.read().as_ref() {
            if existing.nrows() == docs.len() && existing.ncols() == self.dimension {
                return;
            }
        }

        // Build embeddings matrix
        let n_docs = docs.len();
        let mut embeddings = Array2::zeros((n_docs, self.dimension));

        for (i, doc) in docs.iter().enumerate() {
            if let Some(emb) = &doc.embedding {
                embeddings.row_mut(i).assign(emb);
            }
        }

        *self.embeddings.write() = Some(embeddings);
    }

    /// Search with cosine similarity
    pub fn search(&self, query: &str, top_k: usize) -> Vec<SearchResult> {
        if top_k == 0 {
            return Vec::new();
        }

        let query_emb = self.embedder.embed(query);

        let docs = self.documents.read();
        let embeddings_lock = self.embeddings.read();

        if docs.is_empty() {
            return Vec::new();
        }

        // For small corpora, sequential iteration avoids parallel scheduling overhead.
        let use_parallel = docs.len() >= 2048;

        // Compute (index, similarity) directly to avoid intermediate allocations.
        let mut results: Vec<(usize, f32)> = if let Some(embeddings) = embeddings_lock.as_ref() {
            // Embeddings are L2-normalized; cosine similarity is dot product.
            let sims = embeddings.dot(&query_emb);
            sims.iter().enumerate().map(|(idx, score)| (idx, *score)).collect()
        } else if use_parallel {
            docs.par_iter()
                .enumerate()
                .map(|(idx, doc)| {
                    let score = doc
                        .embedding
                        .as_ref()
                        .map(|emb| query_emb.dot(emb))
                        .unwrap_or(0.0);
                    (idx, score)
                })
                .collect()
        } else {
            docs.iter()
                .enumerate()
                .map(|(idx, doc)| {
                    let score = doc
                        .embedding
                        .as_ref()
                        .map(|emb| query_emb.dot(emb))
                        .unwrap_or(0.0);
                    (idx, score)
                })
                .collect()
        };

        select_top_k(&mut results, top_k);

        // Convert to SearchResult
        results
            .into_iter()
            .enumerate()
            .map(|(rank, (idx, score))| SearchResult {
                doc: docs[idx].clone(),
                score,
                rank: rank + 1,
            })
            .collect()
    }

    /// Search by document type
    pub fn search_by_type(
        &self,
        query: &str,
        doc_type: DocType,
        top_k: usize,
    ) -> Vec<SearchResult> {
        if top_k == 0 {
            return Vec::new();
        }

        let query_emb = self.embedder.embed(query);
        let docs = self.documents.read();
        let embeddings_lock = self.embeddings.read();

        if docs.is_empty() {
            return Vec::new();
        }

        // Keep only requested doc_type, then rank globally inside that subset.
        let mut results: Vec<(usize, f32)> = if let Some(embeddings) = embeddings_lock.as_ref() {
            docs.iter()
                .enumerate()
                .filter(|(_, doc)| doc.doc_type == doc_type)
                .map(|(idx, _)| (idx, embeddings.row(idx).dot(&query_emb)))
                .collect()
        } else {
            docs.iter()
                .enumerate()
                .filter(|(_, doc)| doc.doc_type == doc_type)
                .map(|(idx, doc)| {
                    let score = doc
                        .embedding
                        .as_ref()
                        .map(|emb| query_emb.dot(emb))
                        .unwrap_or(0.0);
                    (idx, score)
                })
                .collect()
        };

        select_top_k(&mut results, top_k);

        results
            .into_iter()
            .enumerate()
            .map(|(rank, (idx, score))| SearchResult {
                doc: docs[idx].clone(),
                score,
                rank: rank + 1,
            })
            .collect()
    }

    /// Get document count
    pub fn len(&self) -> usize {
        self.documents.read().len()
    }

    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }

    /// Clear all documents
    pub fn clear(&self) {
        self.documents.write().clear();
        *self.embeddings.write() = None;
    }
}

/// Fast cosine similarity using SIMD
#[inline]
pub fn cosine_similarity(a: ArrayView1<f32>, b: ArrayView1<f32>) -> f32 {
    let dot = a.dot(&b);
    let norm_a = a.dot(&a).sqrt();
    let norm_b = b.dot(&b).sqrt();

    if norm_a == 0.0 || norm_b == 0.0 {
        0.0
    } else {
        dot / (norm_a * norm_b)
    }
}

#[inline]
fn select_top_k(results: &mut Vec<(usize, f32)>, top_k: usize) {
    let k = top_k.min(results.len());
    if k == 0 {
        results.clear();
        return;
    }

    if k < results.len() {
        // Partition around top-k boundary, then sort only the selected prefix.
        results.select_nth_unstable_by(k - 1, |a, b| b.1.total_cmp(&a.1));
        results[..k].sort_unstable_by(|a, b| b.1.total_cmp(&a.1));
        results.truncate(k);
    } else {
        results.sort_unstable_by(|a, b| b.1.total_cmp(&a.1));
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_retriever() {
        let retriever = Retriever::new(128);

        retriever.add_document(Document {
            id: "1".to_string(),
            content: "Magic comes from ancient ley lines".to_string(),
            source: "bible.md".to_string(),
            doc_type: DocType::Bible,
            metadata: HashMap::new(),
            embedding: None,
        });

        retriever.add_document(Document {
            id: "2".to_string(),
            content: "Elara is a young mage".to_string(),
            source: "chars/elara.json".to_string(),
            doc_type: DocType::Character,
            metadata: HashMap::new(),
            embedding: None,
        });

        retriever.build();

        let results = retriever.search("magic power", 2);
        assert!(!results.is_empty());

        // First result should be about magic
        assert!(results[0].score > 0.0);
    }

    #[test]
    fn test_cosine_similarity() {
        let a = Array1::from(vec![1.0, 0.0, 0.0]);
        let b = Array1::from(vec![1.0, 0.0, 0.0]);

        assert!((cosine_similarity(a.view(), b.view()) - 1.0).abs() < 0.001);

        let c = Array1::from(vec![0.0, 1.0, 0.0]);
        assert!(cosine_similarity(a.view(), c.view()).abs() < 0.001);
    }

    #[test]
    fn test_search_top_k_and_order() {
        let retriever = Retriever::new(128);
        for i in 0..20 {
            retriever.add_document(Document {
                id: i.to_string(),
                content: format!("magic world {}", i),
                source: "bench.md".to_string(),
                doc_type: DocType::Chapter,
                metadata: HashMap::new(),
                embedding: None,
            });
        }
        retriever.build();

        let results = retriever.search("magic", 5);
        assert_eq!(results.len(), 5);
        assert!(results.windows(2).all(|w| w[0].score >= w[1].score));
        assert_eq!(results[0].rank, 1);
        assert_eq!(results[4].rank, 5);
    }

    #[test]
    fn test_search_top_k_zero() {
        let retriever = Retriever::new(128);
        retriever.add_document(Document {
            id: "1".to_string(),
            content: "magic".to_string(),
            source: "test.md".to_string(),
            doc_type: DocType::Chapter,
            metadata: HashMap::new(),
            embedding: None,
        });
        retriever.build();

        let results = retriever.search("magic", 0);
        assert!(results.is_empty());
    }

    #[test]
    fn test_search_by_type_ranks_within_subset() {
        let retriever = Retriever::new(128);

        // High-scoring chapter docs
        for i in 0..8 {
            retriever.add_document(Document {
                id: format!("c{}", i),
                content: format!("magic battle {}", i),
                source: "chapters".to_string(),
                doc_type: DocType::Chapter,
                metadata: HashMap::new(),
                embedding: None,
            });
        }

        // Lower-scoring fact docs
        for i in 0..4 {
            retriever.add_document(Document {
                id: format!("f{}", i),
                content: format!("history archive {}", i),
                source: "facts".to_string(),
                doc_type: DocType::Fact,
                metadata: HashMap::new(),
                embedding: None,
            });
        }

        retriever.build();

        let facts = retriever.search_by_type("magic", DocType::Fact, 3);
        assert_eq!(facts.len(), 3);
        assert!(facts.iter().all(|r| r.doc.doc_type == DocType::Fact));
        assert!(facts.windows(2).all(|w| w[0].score >= w[1].score));
    }
}

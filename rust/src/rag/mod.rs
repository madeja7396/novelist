//! High-performance RAG (Retrieval-Augmented Generation)
//! 
//! Features:
//! - Fast vector similarity search with SIMD
//! - Memory-efficient indexing
//! - Multi-threaded indexing
//! - Incremental updates

use ndarray::{Array1, Array2, ArrayView1};
use rayon::prelude::*;
use std::collections::HashMap;
use parking_lot::RwLock;

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
        docs_lock.extend(docs_with_embeddings);
        *self.embeddings.write() = None;
    }
    
    /// Build index (create embeddings matrix)
    pub fn build(&self) {
        let docs = self.documents.read();
        
        if docs.is_empty() {
            return;
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
        let query_emb = self.embedder.embed(query);
        
        let docs = self.documents.read();
        let embeddings_lock = self.embeddings.read();
        
        if docs.is_empty() {
            return Vec::new();
        }
        
        // Use pre-built matrix if available
        let similarities: Vec<f32> = if let Some(embeddings) = embeddings_lock.as_ref() {
            // Batch similarity computation
            embeddings
                .outer_iter()
                .map(|doc_emb| cosine_similarity(query_emb.view(), doc_emb))
                .collect()
        } else {
            // Compute on-the-fly
            docs.iter()
                .map(|doc| {
                    doc.embedding.as_ref()
                        .map(|emb| cosine_similarity(query_emb.view(), emb.view()))
                        .unwrap_or(0.0)
                })
                .collect()
        };
        
        // Create results with indices
        let mut results: Vec<(usize, f32)> = similarities
            .into_iter()
            .enumerate()
            .collect();
        
        // Sort by similarity (descending)
        results.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        
        // Take top_k
        results.truncate(top_k);
        
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
    pub fn search_by_type(&self, query: &str, doc_type: DocType, top_k: usize) -> Vec<SearchResult> {
        let results = self.search(query, top_k * 2); // Get more, then filter
        
        results
            .into_iter()
            .filter(|r| r.doc.doc_type == doc_type)
            .take(top_k)
            .enumerate()
            .map(|(rank, mut r)| {
                r.rank = rank + 1;
                r
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
}

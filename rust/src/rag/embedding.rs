//! Embedding generation
//!
//! Lightweight embeddings using TF-IDF or simple neural approaches

use ndarray::Array1;
use std::collections::HashMap;

/// Embedding trait
pub trait Embedding: Send + Sync {
    fn embed(&self, text: &str) -> Array1<f32>;
    fn dimension(&self) -> usize;
}

/// Simple TF-IDF based embedder
/// Fast and lightweight, good for keyword matching
pub struct SimpleEmbedder {
    dimension: usize,
    vocab: HashMap<char, usize>,
    idf: HashMap<char, f32>,
}

impl SimpleEmbedder {
    pub fn new(dimension: usize) -> Self {
        let mut vocab = HashMap::new();

        // Initialize with common characters
        // ASCII
        for c in 'a'..='z' {
            vocab.insert(c, vocab.len());
        }
        for c in '0'..='9' {
            vocab.insert(c, vocab.len());
        }

        // Hiragana
        for c in '\u{3040}'..='\u{309F}' {
            vocab.insert(c, vocab.len());
        }

        // Katakana
        for c in '\u{30A0}'..='\u{30FF}' {
            vocab.insert(c, vocab.len());
        }

        // Common Kanji (subset)
        let common_kanji = "日一国会人年大十二本中長出三同時分上東生国会入見月白明書行気小".chars();
        for c in common_kanji {
            vocab.insert(c, vocab.len());
        }

        // Pad to dimension
        while vocab.len() < dimension {
            vocab.insert('\0', vocab.len());
        }

        // Simple IDF (can be improved with corpus analysis)
        let mut idf = HashMap::new();
        for (c, _) in &vocab {
            // Lower IDF for common characters
            let freq = match c {
                ' ' | '。' | '、' | '.' | ',' => 1.0,
                'の' | 'に' | 'は' | 'を' | 'が' | 'と' => 1.5,
                'a' | 'e' | 'i' | 'o' | 'u' | 't' | 'n' => 1.5,
                _ => 2.0,
            };
            idf.insert(*c, freq);
        }

        Self {
            dimension,
            vocab,
            idf,
        }
    }

    /// Embed text to vector
    pub fn embed(&self, text: &str) -> Array1<f32> {
        let mut vector = Array1::zeros(self.dimension);

        // Character frequency
        let mut char_counts: HashMap<char, usize> = HashMap::new();
        for c in text.chars() {
            *char_counts.entry(c).or_insert(0) += 1;
        }

        // TF-IDF weighting
        let total_chars = text.chars().count().max(1);
        for (c, count) in char_counts {
            if let Some(&idx) = self.vocab.get(&c) {
                if idx < self.dimension {
                    let tf = count as f32 / total_chars as f32;
                    let idf = self.idf.get(&c).copied().unwrap_or(1.0);
                    vector[idx] = tf * idf;
                }
            }
        }

        // L2 normalize
        let norm = vector.dot(&vector).sqrt();
        if norm > 0.0 {
            vector / norm
        } else {
            vector
        }
    }
}

impl Embedding for SimpleEmbedder {
    fn embed(&self, text: &str) -> Array1<f32> {
        self.embed(text)
    }

    fn dimension(&self) -> usize {
        self.dimension
    }
}

/// Zero-copy embedding view
pub struct EmbeddingView<'a> {
    data: &'a [f32],
}

impl<'a> EmbeddingView<'a> {
    pub fn new(data: &'a [f32]) -> Self {
        Self { data }
    }

    pub fn cosine_similarity(&self, other: &Self) -> f32 {
        let dot: f32 = self
            .data
            .iter()
            .zip(other.data.iter())
            .map(|(a, b)| a * b)
            .sum();
        let norm_a: f32 = self.data.iter().map(|x| x * x).sum::<f32>().sqrt();
        let norm_b: f32 = other.data.iter().map(|x| x * x).sum::<f32>().sqrt();

        if norm_a == 0.0 || norm_b == 0.0 {
            0.0
        } else {
            dot / (norm_a * norm_b)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_simple_embedder() {
        let embedder = SimpleEmbedder::new(128);

        let emb1 = embedder.embed("magic and spells");
        let emb2 = embedder.embed("magic power");
        let emb3 = embedder.embed("completely different topic");

        // Similar texts should have higher similarity
        let sim1 = emb1.dot(&emb2);
        let sim2 = emb1.dot(&emb3);

        assert!(sim1 > sim2, "Similar texts should have higher similarity");
    }

    #[test]
    fn test_japanese_embedding() {
        let embedder = SimpleEmbedder::new(128);

        let ja1 = embedder.embed("魔法の力");
        let ja2 = embedder.embed("魔法使い");

        let similarity = ja1.dot(&ja2);
        assert!(similarity > 0.0);
    }
}

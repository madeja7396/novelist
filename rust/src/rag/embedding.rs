//! Embedding generation
//!
//! Lightweight embeddings using TF-IDF or simple neural approaches

use ndarray::Array1;

/// Embedding trait
pub trait Embedding: Send + Sync {
    fn embed(&self, text: &str) -> Array1<f32>;
    fn dimension(&self) -> usize;
}

/// Simple TF-IDF based embedder
/// Fast and lightweight, good for keyword matching
pub struct SimpleEmbedder {
    dimension: usize,
}

impl SimpleEmbedder {
    pub fn new(dimension: usize) -> Self {
        Self { dimension }
    }

    /// Embed text to vector
    pub fn embed(&self, text: &str) -> Array1<f32> {
        let mut vector: Array1<f32> = Array1::zeros(self.dimension);

        // Single-pass weighted frequency with deterministic hashing.
        // This avoids per-text hash map allocation on the hot path.
        let mut total_chars = 0usize;
        for c in text.chars() {
            total_chars += 1;
            let idx = (c as usize) % self.dimension;
            let weight = match c {
                ' ' | '。' | '、' | '.' | ',' => 0.8,
                'の' | 'に' | 'は' | 'を' | 'が' | 'と' => 1.0,
                _ => 1.6,
            };
            vector[idx] += weight;
        }

        if total_chars > 0 {
            vector /= total_chars as f32;
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

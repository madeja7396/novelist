//! Japanese tokenizer using Lindera (MeCab-based)

use super::{Token, TokenType, Tokenizer};
use lindera::tokenizer::Tokenizer as LinderaTokenizer;

/// Japanese tokenizer with Lindera
pub struct JapaneseTokenizer {
    inner: LinderaTokenizer,
}

impl JapaneseTokenizer {
    pub fn new() -> Self {
        let inner = LinderaTokenizer::new().expect("Failed to initialize Lindera");
        Self { inner }
    }
}

impl Default for JapaneseTokenizer {
    fn default() -> Self {
        Self::new()
    }
}

impl Tokenizer for JapaneseTokenizer {
    fn tokenize(&self, text: &str) -> Vec<Token> {
        let mut tokens = Vec::new();
        let mut byte_offset = 0;
        
        // Use Lindera for morphological analysis
        let results = self.inner.tokenize(text);
        
        for token in results {
            let surface = token.text;
            let start = byte_offset;
            let end = start + surface.len();
            
            // Determine token type from part-of-speech if available
            let token_type = if surface.chars().all(|c| c.is_whitespace()) {
                TokenType::Space
            } else if surface.chars().all(|c| c.is_ascii_punctuation()) {
                TokenType::Punctuation
            } else {
                TokenType::Word
            };
            
            tokens.push(Token {
                text: surface.to_string(),
                start,
                end,
                token_type,
            });
            
            byte_offset = end;
        }
        
        tokens
    }
    
    fn estimate_tokens(&self, text: &str) -> usize {
        // Japanese: ~1.5 chars per token on average
        text.chars().count() * 2 / 3
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_japanese_tokenization() {
        let tokenizer = JapaneseTokenizer::new();
        let tokens = tokenizer.tokenize("これは日本語のテストです。");
        
        assert!(!tokens.is_empty());
        // Should have tokens like: これ, は, 日本語, の, テスト, です, 。
        assert!(tokens.len() >= 5);
    }
}

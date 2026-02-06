//! Japanese tokenizer implementation.

use super::{Token, TokenType, Tokenizer};

/// Japanese tokenizer (character-level fallback implementation).
pub struct JapaneseTokenizer;

impl JapaneseTokenizer {
    pub fn new() -> Self {
        Self
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

        for (start, end, surface) in fallback_segments(text) {
            let token_type = classify_surface(surface);
            tokens.push(Token {
                text: surface.to_string(),
                start,
                end,
                token_type,
            });
        }

        tokens
    }

    fn estimate_tokens(&self, text: &str) -> usize {
        // Japanese: ~1.5 chars per token on average
        text.chars().count() * 2 / 3
    }
}

fn fallback_segments(text: &str) -> Vec<(usize, usize, &str)> {
    let mut segments = Vec::new();
    let mut char_indices = text.char_indices().peekable();

    while let Some((start, _)) = char_indices.next() {
        let end = char_indices
            .peek()
            .map(|(idx, _)| *idx)
            .unwrap_or(text.len());
        let surface = &text[start..end];
        segments.push((start, end, surface));
    }

    segments
}

fn classify_surface(surface: &str) -> TokenType {
    if surface.chars().all(|c| c.is_whitespace()) {
        TokenType::Space
    } else if surface.chars().all(|c| c.is_ascii_punctuation()) {
        TokenType::Punctuation
    } else {
        TokenType::Word
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

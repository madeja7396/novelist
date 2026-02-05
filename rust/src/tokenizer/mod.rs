//! Multi-language tokenizer with optimized performance

use unicode_segmentation::UnicodeSegmentation;
use unicode_normalization::UnicodeNormalization;

pub mod japanese;

pub use japanese::JapaneseTokenizer;

/// Token representation
#[derive(Debug, Clone, PartialEq, serde::Serialize, serde::Deserialize)]
pub struct Token {
    pub text: String,
    pub start: usize,
    pub end: usize,
    pub token_type: TokenType,
}

#[derive(Debug, Clone, PartialEq, serde::Serialize, serde::Deserialize)]
pub enum TokenType {
    Word,
    Punctuation,
    Number,
    Space,
    Other,
}

/// Language-specific tokenizers
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Language {
    Japanese,
    English,
    Chinese,
    Korean,
    Auto,
}

/// Main tokenizer trait
pub trait Tokenizer: Send + Sync {
    fn tokenize(&self, text: &str) -> Vec<Token>;
    fn estimate_tokens(&self, text: &str) -> usize;
}

/// Fast multi-language tokenizer
pub struct MultiLanguageTokenizer {
    ja_tokenizer: JapaneseTokenizer,
}

impl MultiLanguageTokenizer {
    pub fn new() -> Self {
        Self {
            ja_tokenizer: JapaneseTokenizer::new(),
        }
    }
    
    /// Detect language from text
    pub fn detect_language(text: &str) -> Language {
        let ja_ratio = text.chars().filter(|c| is_japanese(*c)).count();
        let zh_ratio = text.chars().filter(|c| is_chinese(*c)).count();
        let ko_ratio = text.chars().filter(|c| is_korean(*c)).count();
        
        let total = text.chars().count().max(1);
        
        if ja_ratio * 3 > total {
            Language::Japanese
        } else if zh_ratio * 3 > total {
            Language::Chinese
        } else if ko_ratio * 3 > total {
            Language::Korean
        } else {
            Language::English
        }
    }
    
    /// Tokenize with auto language detection
    pub fn tokenize_auto(&self, text: &str) -> Vec<Token> {
        let lang = Self::detect_language(text);
        
        match lang {
            Language::Japanese => self.ja_tokenizer.tokenize(text),
            _ => self.tokenize_generic(text),
        }
    }
    
    /// Generic tokenizer for non-Japanese text
    fn tokenize_generic(&self, text: &str) -> Vec<Token> {
        let mut tokens = Vec::new();
        let mut start = 0;
        
        for (word, _) in text.split_word_bounds().with_byte_offsets() {
            let end = start + word.len();
            
            let token_type = if word.trim().is_empty() {
                TokenType::Space
            } else if word.chars().all(|c| c.is_ascii_punctuation()) {
                TokenType::Punctuation
            } else if word.chars().all(|c| c.is_ascii_digit()) {
                TokenType::Number
            } else {
                TokenType::Word
            };
            
            tokens.push(Token {
                text: word.to_string(),
                start,
                end,
                token_type,
            });
            
            start = end;
        }
        
        tokens
    }
    
    /// Estimate token count (fast, for budgeting)
    pub fn estimate_tokens_fast(text: &str) -> usize {
        let lang = Self::detect_language(text);
        
        match lang {
            Language::Japanese => {
                // Japanese: ~1.5 chars per token
                text.chars().count() / 3 * 2
            }
            Language::Chinese => {
                // Chinese: ~1.5 chars per token
                text.chars().count() / 3 * 2
            }
            Language::Korean => {
                // Korean: ~2 chars per token
                text.chars().count() / 2
            }
            _ => {
                // English: ~4 chars per token
                text.len() / 4
            }
        }
    }
}

impl Default for MultiLanguageTokenizer {
    fn default() -> Self {
        Self::new()
    }
}

impl Tokenizer for MultiLanguageTokenizer {
    fn tokenize(&self, text: &str) -> Vec<Token> {
        self.tokenize_auto(text)
    }
    
    fn estimate_tokens(&self, text: &str) -> usize {
        Self::estimate_tokens_fast(text)
    }
}

// Language detection helpers
fn is_japanese(c: char) -> bool {
    matches!(c as u32,
        0x3040..=0x309F | // Hiragana
        0x30A0..=0x30FF | // Katakana
        0x4E00..=0x9FFF   // Kanji
    )
}

fn is_chinese(c: char) -> bool {
    matches!(c as u32,
        0x4E00..=0x9FFF | // CJK Unified
        0x3400..=0x4DBF   // CJK Extension A
    ) && !is_japanese(c)
}

fn is_korean(c: char) -> bool {
    matches!(c as u32,
        0xAC00..=0xD7AF | // Hangul Syllables
        0x1100..=0x11FF | // Hangul Jamo
        0x3130..=0x318F   // Hangul Compatibility
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_language_detection() {
        assert_eq!(MultiLanguageTokenizer::detect_language("Hello world"), Language::English);
        assert_eq!(MultiLanguageTokenizer::detect_language("こんにちは"), Language::Japanese);
        assert_eq!(MultiLanguageTokenizer::detect_language("你好世界"), Language::Chinese);
    }
    
    #[test]
    fn test_tokenize_english() {
        let tokenizer = MultiLanguageTokenizer::new();
        let tokens = tokenizer.tokenize("Hello, world!");
        
        assert!(!tokens.is_empty());
        assert_eq!(tokens[0].text, "Hello");
    }
    
    #[test]
    fn test_estimate_tokens() {
        let en = "This is a test sentence.";
        let ja = "これはテスト文章です。";
        
        let en_tokens = MultiLanguageTokenizer::estimate_tokens_fast(en);
        let ja_tokens = MultiLanguageTokenizer::estimate_tokens_fast(ja);
        
        assert!(en_tokens > 0);
        assert!(ja_tokens > 0);
    }
}

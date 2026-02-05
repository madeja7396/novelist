//! Novelist Core - High-performance library for AI novel writing
//!
//! Features:
//! - Fast text tokenization (Japanese/English/Chinese)
//! - Vector similarity search for RAG
//! - Internationalization support
//! - WebAssembly bindings

pub mod ffi;
pub mod i18n;
pub mod models;
pub mod rag;
pub mod tokenizer;

pub use i18n::I18n;
pub use models::*;
pub use rag::{Document, Retriever, SearchResult};
pub use tokenizer::{Token, Tokenizer};

use thiserror::Error;

#[derive(Error, Debug)]
pub enum NovelistError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),

    #[error("Tokenization error: {0}")]
    Tokenization(String),

    #[error("RAG error: {0}")]
    Rag(String),

    #[error("Config error: {0}")]
    Config(String),

    #[error("HTTP error: {0}")]
    Http(#[from] reqwest::Error),
}

pub type Result<T> = std::result::Result<T, NovelistError>;

/// Initialize the library
pub fn init() {
    tracing_subscriber::fmt::init();
    i18n::init();
}

/// Version info
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

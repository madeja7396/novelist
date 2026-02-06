//! FFI bindings for Go interop
//!
//! Exposes Rust core functions to Go via C ABI

use std::ffi::{CStr, CString};
use std::os::raw::{c_char, c_int};

use crate::rag::{DocType, Document, Retriever};
use crate::tokenizer::{MultiLanguageTokenizer, Tokenizer};

/// Tokenize text and return JSON array of tokens
///
/// # Safety
/// `text` must be a valid, non-null, NUL-terminated C string pointer.
#[no_mangle]
pub unsafe extern "C" fn novelist_tokenize(text: *const c_char) -> *mut c_char {
    if text.is_null() {
        return std::ptr::null_mut();
    }

    let c_str = unsafe { CStr::from_ptr(text) };
    let text_str = match c_str.to_str() {
        Ok(s) => s,
        Err(_) => return std::ptr::null_mut(),
    };

    let tokenizer = MultiLanguageTokenizer::new();
    let tokens = tokenizer.tokenize(text_str);

    // Convert to JSON
    let json = serde_json::to_string(&tokens).unwrap_or_default();

    match CString::new(json) {
        Ok(cstring) => cstring.into_raw(),
        Err(_) => std::ptr::null_mut(),
    }
}

/// Free a string allocated by Rust
///
/// # Safety
/// `s` must be a pointer returned by `novelist_tokenize` and must not be freed twice.
#[no_mangle]
pub unsafe extern "C" fn novelist_free_string(s: *mut c_char) {
    if !s.is_null() {
        unsafe {
            let _ = CString::from_raw(s);
        }
    }
}

/// Create a new retriever
#[no_mangle]
pub extern "C" fn novelist_retriever_new(dimension: c_int) -> *mut Retriever {
    let retriever = Retriever::new(dimension as usize);
    Box::into_raw(Box::new(retriever))
}

/// Free a retriever
///
/// # Safety
/// `retriever` must be a pointer returned by `novelist_retriever_new` and must not be freed twice.
#[no_mangle]
pub unsafe extern "C" fn novelist_retriever_free(retriever: *mut Retriever) {
    if !retriever.is_null() {
        unsafe {
            let _ = Box::from_raw(retriever);
        }
    }
}

/// Add document to retriever
///
/// # Safety
/// `retriever` must be a valid pointer from `novelist_retriever_new`.
/// `id` and `content` must be valid, non-null, NUL-terminated C strings.
/// `source` and `doc_type` may be null; if non-null they must be valid C strings.
#[no_mangle]
pub unsafe extern "C" fn novelist_retriever_add(
    retriever: *mut Retriever,
    id: *const c_char,
    content: *const c_char,
    source: *const c_char,
    doc_type: *const c_char,
) {
    if retriever.is_null() || id.is_null() || content.is_null() {
        return;
    }

    let retriever = unsafe { &*retriever };

    let id_str = unsafe { CStr::from_ptr(id).to_string_lossy().into_owned() };
    let content_str = unsafe { CStr::from_ptr(content).to_string_lossy().into_owned() };
    let source_str = if source.is_null() {
        "unknown".to_string()
    } else {
        unsafe { CStr::from_ptr(source).to_string_lossy().into_owned() }
    };

    let doc_type_enum = if doc_type.is_null() {
        DocType::Other
    } else {
        let type_str = unsafe { CStr::from_ptr(doc_type).to_string_lossy() };
        match type_str.as_ref() {
            "bible" => DocType::Bible,
            "character" => DocType::Character,
            "fact" => DocType::Fact,
            "chapter" => DocType::Chapter,
            _ => DocType::Other,
        }
    };

    let doc = Document {
        id: id_str,
        content: content_str,
        source: source_str,
        doc_type: doc_type_enum,
        metadata: std::collections::HashMap::new(),
        embedding: None,
    };

    retriever.add_document(doc);
}

/// Build retriever index
///
/// # Safety
/// `retriever` must be a valid pointer from `novelist_retriever_new`.
#[no_mangle]
pub unsafe extern "C" fn novelist_retriever_build(retriever: *mut Retriever) {
    if !retriever.is_null() {
        let retriever = unsafe { &*retriever };
        retriever.build();
    }
}

/// Search retriever (simplified - returns count)
///
/// # Safety
/// `retriever` must be a valid pointer from `novelist_retriever_new`.
/// `query` must be a valid, non-null, NUL-terminated C string pointer.
#[no_mangle]
pub unsafe extern "C" fn novelist_retriever_search(
    retriever: *mut Retriever,
    query: *const c_char,
    top_k: c_int,
) -> c_int {
    if retriever.is_null() || query.is_null() {
        return 0;
    }

    let retriever = unsafe { &*retriever };
    let query_str = unsafe { CStr::from_ptr(query).to_string_lossy() };

    let results = retriever.search(&query_str, top_k as usize);
    results.len() as c_int
}

/// Get version
#[no_mangle]
pub extern "C" fn novelist_version() -> *const c_char {
    static VERSION: &str = concat!(env!("CARGO_PKG_VERSION"), "\0");
    VERSION.as_ptr() as *const c_char
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ffi_tokenize_and_free() {
        let input = CString::new("Hello world").expect("valid c string");
        let out_ptr = unsafe { novelist_tokenize(input.as_ptr()) };
        assert!(!out_ptr.is_null());

        let out = unsafe { CStr::from_ptr(out_ptr) }
            .to_string_lossy()
            .into_owned();
        assert!(out.contains("Hello"));

        unsafe { novelist_free_string(out_ptr) };
    }

    #[test]
    fn test_ffi_retriever_lifecycle() {
        let retriever = novelist_retriever_new(64);
        assert!(!retriever.is_null());

        let id = CString::new("doc1").expect("valid c string");
        let content = CString::new("magic comes from old ruins").expect("valid c string");
        let source = CString::new("test.md").expect("valid c string");
        let doc_type = CString::new("chapter").expect("valid c string");

        unsafe {
            novelist_retriever_add(
                retriever,
                id.as_ptr(),
                content.as_ptr(),
                source.as_ptr(),
                doc_type.as_ptr(),
            );
            novelist_retriever_build(retriever);
        }

        let query = CString::new("magic").expect("valid c string");
        let count = unsafe { novelist_retriever_search(retriever, query.as_ptr(), 5) };
        assert!(count >= 1);

        unsafe { novelist_retriever_free(retriever) };
    }
}

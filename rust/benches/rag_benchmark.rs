use criterion::{black_box, criterion_group, criterion_main, Criterion};
use novelist_core::rag::{Document, DocType, Retriever};

fn create_test_documents(count: usize) -> Vec<Document> {
    (0..count)
        .map(|i| Document {
            id: format!("doc_{}", i),
            content: format!("This is test document number {} with some content about magic and fantasy worlds.", i),
            source: "test.md".into(),
            doc_type: DocType::Chapter,
            metadata: Default::default(),
            embedding: None,
        })
        .collect()
}

fn benchmark_rag_index(c: &mut Criterion) {
    let retriever = Retriever::new(128);
    let docs = create_test_documents(1000);
    
    c.bench_function("rag_index_1000", |b| {
        b.iter(|| {
            retriever.clear();
            retriever.add_documents(black_box(docs.clone()));
            retriever.build();
        });
    });
}

fn benchmark_rag_search(c: &mut Criterion) {
    let retriever = Retriever::new(128);
    let docs = create_test_documents(1000);
    retriever.add_documents(docs);
    retriever.build();
    
    let query = "magic fantasy world";
    
    c.bench_function("rag_search", |b| {
        b.iter(|| {
            let _ = retriever.search(black_box(query), 10);
        });
    });
}

criterion_group!(benches, benchmark_rag_index, benchmark_rag_search);
criterion_main!(benches);

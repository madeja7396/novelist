use criterion::{black_box, criterion_group, criterion_main, Criterion};
use novelist_core::rag::{DocType, Document, Retriever};

fn create_test_documents(count: usize) -> Vec<Document> {
    (0..count)
        .map(|i| Document {
            id: format!("doc_{}", i),
            content: format!(
                "This is test document number {} with some content about magic and fantasy worlds.",
                i
            ),
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
    let query = "magic fantasy world";

    let retriever_1k = Retriever::new(128);
    retriever_1k.add_documents(create_test_documents(1000));
    retriever_1k.build();

    c.bench_function("rag_search_1000_top10", |b| {
        b.iter(|| {
            let _ = retriever_1k.search(black_box(query), 10);
        });
    });

    let retriever_10k = Retriever::new(128);
    retriever_10k.add_documents(create_test_documents(10_000));
    retriever_10k.build();

    c.bench_function("rag_search_10000_top10", |b| {
        b.iter(|| {
            let _ = retriever_10k.search(black_box(query), 10);
        });
    });
}

criterion_group!(benches, benchmark_rag_index, benchmark_rag_search);
criterion_main!(benches);

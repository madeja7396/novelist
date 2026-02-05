use criterion::{black_box, criterion_group, criterion_main, Criterion, Throughput};
use novelist_core::tokenizer::MultiLanguageTokenizer;

fn benchmark_tokenize_japanese(c: &mut Criterion) {
    let tokenizer = MultiLanguageTokenizer::new();
    let text = "これは日本語のテスト文章です。小説の創作支援システムを開発しています。";

    let mut group = c.benchmark_group("tokenizer");
    group.throughput(Throughput::Bytes(text.len() as u64));

    group.bench_function("tokenize_japanese", |b| {
        b.iter(|| {
            let _ = tokenizer.tokenize(black_box(text));
        });
    });

    group.finish();
}

fn benchmark_tokenize_english(c: &mut Criterion) {
    let tokenizer = MultiLanguageTokenizer::new();
    let text = "This is a test sentence for the novel writing assistant system. It should tokenize quickly.";

    let mut group = c.benchmark_group("tokenizer");
    group.throughput(Throughput::Bytes(text.len() as u64));

    group.bench_function("tokenize_english", |b| {
        b.iter(|| {
            let _ = tokenizer.tokenize(black_box(text));
        });
    });

    group.finish();
}

fn benchmark_language_detection(c: &mut Criterion) {
    let texts = [
        ("japanese", "これは日本語です"),
        ("english", "This is English"),
        ("chinese", "这是中文"),
        ("korean", "한국어입니다"),
    ];

    let mut group = c.benchmark_group("language_detection");

    for (name, text) in texts {
        group.bench_function(name, |b| {
            b.iter(|| {
                let _ = MultiLanguageTokenizer::detect_language(black_box(text));
            });
        });
    }

    group.finish();
}

criterion_group!(
    benches,
    benchmark_tokenize_japanese,
    benchmark_tokenize_english,
    benchmark_language_detection
);
criterion_main!(benches);

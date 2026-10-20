"""Academic Performance Evaluation & Benchmark Script for FeedbackIQ.

Replicates the experimental evaluation framework from Chapter 4 of the project report:
- Table 4.2: Sentiment Classification Results (Precision, Recall, F1, Accuracy)
- Table 4.3: Category and Priority Distribution Analysis
- Table 4.4: Batch Processing & System Latency Performance
"""

import time
from pathlib import Path
import pandas as pd
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split

import config
from ml.model import load_models, create_pipeline
from services.analysis_service import analyze_feedback
from services.db_service import (
    clear_feedback,
    get_results,
    get_summary,
    init_db,
    insert_batch,
)


def evaluate_sentiment_model(data_path=None):
    """Evaluate sentiment classification on a held-out test split (Table 4.2)."""
    if data_path is None:
        data_path = config.DATA_DIR / "training_data.csv"

    df = pd.read_csv(data_path)
    X = df["feedback"].astype(str).tolist()
    y = df["sentiment"].astype(str).tolist()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    pipeline = create_pipeline()
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    print("\n" + "=" * 70)
    print("TABLE 4.2: SENTIMENT CLASSIFICATION RESULTS")
    print("=" * 70)
    print(f"{'Class':<20} | {'Precision':<12} | {'Recall':<12} | {'F1-Score':<12}")
    print("-" * 70)

    classes = ["Positive", "Neutral", "Negative"]
    for cls in classes:
        metrics = report.get(cls, {"precision": 0.0, "recall": 0.0, "f1-score": 0.0})
        print(f"{cls:<20} | {metrics['precision']:<12.3f} | {metrics['recall']:<12.3f} | {metrics['f1-score']:<12.3f}")

    print("-" * 70)
    print(f"{'Overall Accuracy':<20} | {acc:<12.3f} | {'-':<12} | {'-':<12}")
    print("=" * 70)

    return report, acc


def evaluate_category_priority():
    """Evaluate Category vs Priority distribution across dataset (Table 4.3)."""
    data_path = config.DATA_DIR / "training_data.csv"
    df = pd.read_csv(data_path)

    results = []
    for text in df["feedback"].astype(str):
        analysis = analyze_feedback(text)
        results.append(analysis)

    res_df = pd.DataFrame(results)

    print("\n" + "=" * 70)
    print("TABLE 4.3: CATEGORY AND PRIORITY ANALYSIS")
    print("=" * 70)
    print(f"{'Category':<22} | {'Total':<8} | {'High':<8} | {'Medium':<8} | {'Low':<8}")
    print("-" * 70)

    categories = sorted(res_df["category"].unique())
    for cat in categories:
        cat_subset = res_df[res_df["category"] == cat]
        total = len(cat_subset)
        high = sum(cat_subset["priority"] == "High")
        medium = sum(cat_subset["priority"] == "Medium")
        low = sum(cat_subset["priority"] == "Low")
        print(f"{cat:<22} | {total:<8} | {high:<8} | {medium:<8} | {low:<8}")

    print("-" * 70)
    total_all = len(res_df)
    high_all = sum(res_df["priority"] == "High")
    med_all = sum(res_df["priority"] == "Medium")
    low_all = sum(res_df["priority"] == "Low")
    print(f"{'Total All':<22} | {total_all:<8} | {high_all:<8} | {med_all:<8} | {low_all:<8}")
    print("=" * 70)


def evaluate_batch_performance():
    """Benchmark batch analysis and storage throughput (Table 4.4)."""
    sample_pool = [
        "The delivery was incredibly prompt and customer service answered immediately.",
        "Terrible product quality, the plastic broke within one hour. I want a refund asap!",
        "Average experience, the product works fine but shipping was standard.",
        "Charged twice on my bill, this is unacceptable fraud! Fix immediately.",
        "I was pleasantly surprised by the premium packaging and nice gift inside.",
        "I am afraid my credit card details were stolen during checkout.",
        "The mobile app crashes every time I open the cart page.",
        "The return process is very complicated and nobody answers support tickets."
    ]

    benchmark_sizes = [10, 100, 1000]
    bench_db = config.DATABASE_DIR / "benchmark_test.db"

    print("\n" + "=" * 70)
    print("TABLE 4.4: BATCH PROCESSING PERFORMANCE")
    print("=" * 70)
    print(f"{'Number of Entries':<20} | {'Analysis & Storage Time (s)':<28} | {'Dashboard Refresh Time (s)':<25}")
    print("-" * 70)

    for n in benchmark_sizes:
        if bench_db.exists():
            bench_db.unlink()
        init_db(bench_db)

        # Generate n feedback entries
        items = [sample_pool[i % len(sample_pool)] for i in range(n)]

        # Time analysis and storage
        t_start = time.perf_counter()
        processed = [analyze_feedback(text) for text in items]
        insert_batch(processed, db_path=bench_db)
        t_analysis_storage = time.perf_counter() - t_start

        # Time dashboard retrieval & aggregation
        t_dash_start = time.perf_counter()
        _ = get_summary(db_path=bench_db)
        _ = get_results(limit=10, db_path=bench_db)
        t_dash = time.perf_counter() - t_dash_start

        print(f"{n:<20} | {t_analysis_storage:<28.4f} | {t_dash:<25.4f}")

    if bench_db.exists():
        bench_db.unlink()
    print("=" * 70)


if __name__ == "__main__":
    print("Running FeedbackIQ Academic Evaluation & Benchmark Suite...")
    evaluate_sentiment_model()
    evaluate_category_priority()
    evaluate_batch_performance()
    print("\nBenchmark completed successfully!")

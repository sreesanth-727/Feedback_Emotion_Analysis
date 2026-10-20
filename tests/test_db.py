"""
Unit tests for Database Service and Export Service in FeedbackIQ.
"""

import csv
import io
import sqlite3
import pytest

from services.db_service import (
    init_db,
    insert_feedback,
    insert_batch,
    get_results,
    get_summary,
    get_chart_data,
    clear_feedback,
    get_db_connection,
)
from services.export_service import generate_csv_bytes


@pytest.fixture
def temp_db(tmp_path):
    """Provides a fresh temporary SQLite database path for each test."""
    db_file = tmp_path / "test_feedback.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def sample_records():
    """Provides a diverse set of sample feedback records."""
    return [
        {
            "feedback": "Product arrived broken and shattered during delivery, terrible quality!",
            "sentiment": "Negative",
            "emotion": "Anger",
            "category": "Delivery",
            "priority": "High",
            "created_at": "2026-10-20 10:00:00",
        },
        {
            "feedback": "Great fast delivery and nice box!",
            "sentiment": "Positive",
            "emotion": "Joy",
            "category": "Delivery",
            "priority": "Low",
            "created_at": "2026-10-20 10:05:00",
        },
        {
            "feedback": "Customer service was very polite and helpful.",
            "sentiment": "Positive",
            "emotion": "Joy",
            "category": "Customer Service",
            "priority": "Low",
            "created_at": "2026-10-20 10:10:00",
        },
        {
            "feedback": "Late delivery, unacceptable delay, charged twice!",
            "sentiment": "Negative",
            "emotion": "Anger",
            "category": "Payment",
            "priority": "High",
            "created_at": "2026-10-20 10:15:00",
        },
        {
            "feedback": "Average quality product, works as expected.",
            "sentiment": "Neutral",
            "emotion": "Neutral",
            "category": "Product Quality",
            "priority": "Medium",
            "created_at": "2026-10-20 10:20:00",
        },
    ]


class TestDatabaseInit:
    def test_init_db_creates_table_and_columns(self, temp_db):
        with get_db_connection(temp_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='feedback';"
            )
            assert cursor.fetchone() is not None

            cursor = conn.execute("PRAGMA table_info(feedback);")
            columns = {row["name"]: row["type"].upper() for row in cursor.fetchall()}

            assert "id" in columns
            assert "feedback" in columns
            assert "sentiment" in columns
            assert "emotion" in columns
            assert "category" in columns
            assert "priority" in columns
            assert "created_at" in columns

    def test_init_db_in_memory_connection(self):
        conn = sqlite3.connect(":memory:")
        init_db(conn)

        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='feedback';"
        )
        assert cursor.fetchone() is not None
        conn.close()


class TestInsertOperations:
    def test_insert_feedback_single(self, temp_db):
        row_id_1 = insert_feedback(
            feedback="The app is extremely responsive and intuitive.",
            sentiment="Positive",
            emotion="Joy",
            category="Technical Issue",
            priority="Low",
            created_at="2026-10-20 12:00:00",
            db_path=temp_db,
        )
        assert row_id_1 == 1

        row_id_2 = insert_feedback(
            feedback="Payment failed multiple times.",
            sentiment="Negative",
            emotion="Fear",
            category="Payment",
            priority="High",
            db_path=temp_db,
        )
        assert row_id_2 == 2

        results = get_results(db_path=temp_db)
        assert len(results) == 2
        # Order is DESC by id
        assert results[0]["id"] == 2
        assert results[0]["feedback"] == "Payment failed multiple times."
        assert results[0]["priority"] == "High"
        assert results[0]["created_at"] is not None

        assert results[1]["id"] == 1
        assert results[1]["feedback"] == "The app is extremely responsive and intuitive."

    def test_insert_batch(self, temp_db, sample_records):
        count = insert_batch(sample_records, db_path=temp_db)
        assert count == len(sample_records)

        results = get_results(db_path=temp_db)
        assert len(results) == len(sample_records)

    def test_insert_batch_empty(self, temp_db):
        count = insert_batch([], db_path=temp_db)
        assert count == 0

    def test_insert_batch_with_text_key_alias(self, temp_db):
        records = [
            {
                "text": "Support was quick to reply.",
                "sentiment": "Positive",
                "emotion": "Joy",
                "category": "Customer Service",
                "priority": "Low",
            }
        ]
        count = insert_batch(records, db_path=temp_db)
        assert count == 1

        results = get_results(db_path=temp_db)
        assert results[0]["feedback"] == "Support was quick to reply."
        assert results[0]["text"] == "Support was quick to reply."


class TestQueryAndFiltering:
    @pytest.fixture(autouse=True)
    def setup_data(self, temp_db, sample_records):
        insert_batch(sample_records, db_path=temp_db)

    def test_get_results_order_and_text_alias(self, temp_db):
        results = get_results(db_path=temp_db)
        assert len(results) == 5
        # Verify descending order
        ids = [r["id"] for r in results]
        assert ids == sorted(ids, reverse=True)
        # Verify text alias exists
        for r in results:
            assert "feedback" in r
            assert "text" in r
            assert r["text"] == r["feedback"]

    def test_search_text_filter(self, temp_db):
        # Case insensitive substring search
        results = get_results(search_text="delivery", db_path=temp_db)
        assert len(results) == 3
        for r in results:
            assert "delivery" in r["feedback"].lower()

        # Non-matching search
        empty_res = get_results(search_text="nonexistentword999", db_path=temp_db)
        assert len(empty_res) == 0

    def test_sentiment_filter(self, temp_db):
        positive = get_results(sentiment_filter="Positive", db_path=temp_db)
        assert len(positive) == 2
        for r in positive:
            assert r["sentiment"].lower() == "positive"

        negative = get_results(sentiment_filter="negative", db_path=temp_db)
        assert len(negative) == 2
        for r in negative:
            assert r["sentiment"].lower() == "negative"

        neutral = get_results(sentiment_filter="Neutral", db_path=temp_db)
        assert len(neutral) == 1

        # 'All' filter returns everything
        all_res = get_results(sentiment_filter="All", db_path=temp_db)
        assert len(all_res) == 5

    def test_priority_filter(self, temp_db):
        high = get_results(priority_filter="High", db_path=temp_db)
        assert len(high) == 2
        for r in high:
            assert r["priority"].lower() == "high"

        medium = get_results(priority_filter="Medium", db_path=temp_db)
        assert len(medium) == 1

        low = get_results(priority_filter="low", db_path=temp_db)
        assert len(low) == 2

    def test_combined_filters_and_limit(self, temp_db):
        # Delivery + High Priority
        results = get_results(
            search_text="delivery",
            priority_filter="High",
            db_path=temp_db
        )
        assert len(results) == 2

        # With limit=1
        limited = get_results(
            search_text="delivery",
            priority_filter="High",
            limit=1,
            db_path=temp_db
        )
        assert len(limited) == 1


class TestSummaryKPI:
    def test_summary_from_database(self, temp_db, sample_records):
        insert_batch(sample_records, db_path=temp_db)
        summary = get_summary(db_path=temp_db)

        assert summary["total"] == 5
        assert summary["positive"] == 2
        assert summary["neutral"] == 1
        assert summary["negative"] == 2
        assert summary["high"] == 2
        assert summary["medium"] == 1
        assert summary["low"] == 2

        assert summary["positive_pct"] == 40.0
        assert summary["neutral_pct"] == 20.0
        assert summary["negative_pct"] == 40.0
        assert summary["high_pct"] == 40.0

    def test_summary_from_results_parameter(self, sample_records):
        # Calculate summary on in-memory filtered list
        subset = sample_records[:3]  # 1 Negative, 2 Positive
        summary = get_summary(results=subset)

        assert summary["total"] == 3
        assert summary["positive"] == 2
        assert summary["neutral"] == 0
        assert summary["negative"] == 1
        assert summary["positive_pct"] == 66.7
        assert summary["negative_pct"] == 33.3

    def test_summary_empty(self, temp_db):
        summary = get_summary(db_path=temp_db)
        assert summary["total"] == 0
        assert summary["positive"] == 0
        assert summary["neutral"] == 0
        assert summary["negative"] == 0
        assert summary["high"] == 0
        assert summary["medium"] == 0
        assert summary["low"] == 0
        assert summary["positive_pct"] == 0.0
        assert summary["neutral_pct"] == 0.0
        assert summary["negative_pct"] == 0.0
        assert summary["high_pct"] == 0.0


class TestChartData:
    def test_chart_data_structure_and_counts(self, temp_db, sample_records):
        insert_batch(sample_records, db_path=temp_db)
        s_chart, e_chart, c_chart = get_chart_data(db_path=temp_db)

        # Structure checks for Chart.js
        for chart in [s_chart, e_chart, c_chart]:
            assert "labels" in chart
            assert "data" in chart
            assert "datasets" in chart
            assert len(chart["labels"]) == len(chart["data"])
            assert chart["datasets"][0]["data"] == chart["data"]

        # Check counts in sentiment chart
        assert s_chart["Positive"] == 2
        assert s_chart["Neutral"] == 1
        assert s_chart["Negative"] == 2

        # Check emotion chart
        assert e_chart["Anger"] == 2
        assert e_chart["Joy"] == 2
        assert e_chart["Neutral"] == 1

        # Check category chart
        assert c_chart["Delivery"] == 2
        assert c_chart["Payment"] == 1
        assert c_chart["Customer Service"] == 1
        assert c_chart["Product Quality"] == 1

    def test_chart_data_from_in_memory_results(self, sample_records):
        s_chart, e_chart, c_chart = get_chart_data(results=sample_records[:2])
        assert s_chart["Positive"] == 1
        assert s_chart["Negative"] == 1
        assert s_chart["Neutral"] == 0

    def test_chart_data_empty(self, temp_db):
        s_chart, e_chart, c_chart = get_chart_data(db_path=temp_db)
        assert all(v == 0 for v in s_chart["data"])
        assert all(v == 0 for v in e_chart["data"])
        assert all(v == 0 for v in c_chart["data"])


class TestClearFeedback:
    def test_clear_feedback(self, temp_db, sample_records):
        insert_batch(sample_records, db_path=temp_db)
        assert len(get_results(db_path=temp_db)) == 5

        clear_feedback(db_path=temp_db)
        assert len(get_results(db_path=temp_db)) == 0
        summary = get_summary(db_path=temp_db)
        assert summary["total"] == 0


class TestExportService:
    def test_generate_csv_bytes(self, sample_records):
        # Add id field to simulate database rows
        rows = [{"id": idx + 1, **rec} for idx, rec in enumerate(sample_records)]

        csv_buffer = generate_csv_bytes(rows)
        assert isinstance(csv_buffer, io.BytesIO)

        raw_bytes = csv_buffer.getvalue()
        # Verify UTF-8 BOM encoding for Excel compatibility
        assert raw_bytes.startswith(b"\xef\xbb\xbf")

        # Decode using utf-8-sig
        content = raw_bytes.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        expected_columns = ["id", "feedback", "sentiment", "emotion", "category", "priority", "created_at"]
        assert reader.fieldnames == expected_columns

        parsed_rows = list(reader)
        assert len(parsed_rows) == 5
        assert parsed_rows[0]["id"] == "1"
        assert parsed_rows[0]["feedback"] == sample_records[0]["feedback"]
        assert parsed_rows[0]["sentiment"] == "Negative"
        assert parsed_rows[0]["priority"] == "High"

    def test_generate_csv_bytes_empty(self):
        csv_buffer = generate_csv_bytes([])
        raw_bytes = csv_buffer.getvalue()
        assert raw_bytes.startswith(b"\xef\xbb\xbf")

        content = raw_bytes.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        expected_columns = ["id", "feedback", "sentiment", "emotion", "category", "priority", "created_at"]
        assert reader.fieldnames == expected_columns
        assert list(reader) == []


class TestServicesPackageExports:
    def test_services_init_exports(self):
        import services

        expected_exports = [
            "init_db",
            "insert_feedback",
            "insert_batch",
            "get_results",
            "get_summary",
            "get_chart_data",
            "clear_feedback",
            "generate_csv_bytes",
        ]
        for name in expected_exports:
            assert hasattr(services, name)
            assert callable(getattr(services, name))


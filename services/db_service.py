"""
Database service for FeedbackIQ.
Provides embedded SQLite storage, CRUD operations, KPI aggregation,
and Chart.js data generation.
"""

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import sqlite3
import sys

# Ensure project root is available for config import
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import config
except ImportError:
    config = None


@contextmanager
def get_db_connection(db_path=None):
    """
    Context manager providing a SQLite database connection.
    Supports file path (str or Path), sqlite3.Connection object,
    or defaults to config.DB_PATH.
    """
    if isinstance(db_path, sqlite3.Connection):
        db_path.row_factory = sqlite3.Row
        yield db_path
        return

    if db_path is None:
        if config is not None and hasattr(config, "DB_PATH"):
            target_path = config.DB_PATH
        else:
            target_path = Path("database") / "feedback.db"
    else:
        target_path = db_path

    target_str = str(target_path)
    if target_str.startswith("file:"):
        conn = sqlite3.connect(target_str, uri=True)
    elif target_str == ":memory:":
        conn = sqlite3.connect(target_str)
    else:
        file_path = Path(target_str)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(file_path))

    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path=None) -> None:
    """
    Initializes the database and creates the 'feedback' table if not exists.

    Schema:
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      feedback TEXT NOT NULL,
      sentiment TEXT NOT NULL,
      emotion TEXT NOT NULL,
      category TEXT NOT NULL,
      priority TEXT NOT NULL,
      created_at TEXT NOT NULL
    """
    with get_db_connection(db_path) as conn:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feedback TEXT NOT NULL,
                    sentiment TEXT NOT NULL,
                    emotion TEXT NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_sentiment ON feedback(sentiment);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_priority ON feedback(priority);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);")


def insert_feedback(
    feedback: str,
    sentiment: str,
    emotion: str,
    category: str,
    priority: str,
    created_at: str | None = None,
    db_path=None
) -> int:
    """
    Inserts a single feedback record and returns the new row ID.
    """
    init_db(db_path)
    if not created_at:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_connection(db_path) as conn:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO feedback (feedback, sentiment, emotion, category, priority, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (feedback, sentiment, emotion, category, priority, created_at)
            )
            return cursor.lastrowid


def insert_batch(records: list[dict], db_path=None) -> int:
    """
    Inserts a list of record dicts in a single transaction and returns the count inserted.
    Supports either 'feedback' or 'text' key in record dicts.
    """
    if not records:
        return 0

    init_db(db_path)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows_to_insert = []
    for r in records:
        fb = r.get("feedback") if r.get("feedback") is not None else r.get("text", "")
        sent = r.get("sentiment", "Neutral")
        emo = r.get("emotion", "Neutral")
        cat = r.get("category", "General")
        pri = r.get("priority", "Low")
        created = r.get("created_at") or now_str
        rows_to_insert.append((fb, sent, emo, cat, pri, created))

    with get_db_connection(db_path) as conn:
        with conn:
            conn.executemany(
                """
                INSERT INTO feedback (feedback, sentiment, emotion, category, priority, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                rows_to_insert
            )
    return len(rows_to_insert)


def get_results(
    search_text: str = "",
    sentiment_filter: str = "",
    priority_filter: str = "",
    category_filter: str = "",
    limit: int | None = None,
    db_path=None
) -> list[dict]:
    """
    Retrieves feedback rows matching optional search and filter criteria,
    ordered by id DESC.
    """
    init_db(db_path)
    query = "SELECT id, feedback, sentiment, emotion, category, priority, created_at FROM feedback WHERE 1=1"
    params = []

    if search_text and search_text.strip():
        query += " AND LOWER(feedback) LIKE ?"
        params.append(f"%{search_text.strip().lower()}%")

    if sentiment_filter and sentiment_filter.strip() and sentiment_filter.strip().lower() != "all":
        query += " AND LOWER(sentiment) = ?"
        params.append(sentiment_filter.strip().lower())

    if priority_filter and priority_filter.strip() and priority_filter.strip().lower() != "all":
        query += " AND LOWER(priority) = ?"
        params.append(priority_filter.strip().lower())

    if category_filter and category_filter.strip() and category_filter.strip().lower() != "all":
        query += " AND LOWER(category) = ?"
        params.append(category_filter.strip().lower())

    query += " ORDER BY id DESC"

    if limit is not None and isinstance(limit, int) and limit > 0:
        query += " LIMIT ?"
        params.append(limit)

    with get_db_connection(db_path) as conn:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        results = []
        for row in rows:
            d = dict(row)
            # Add alias 'text' for compatibility across services
            if "feedback" in d and "text" not in d:
                d["text"] = d["feedback"]
            results.append(d)
        return results


def get_summary(results: list[dict] | None = None, db_path=None) -> dict:
    """
    Computes summary KPI stats (total, positive, neutral, negative,
    high, medium, low counts, and percentage values).
    If results is None, fetches from database.
    """
    if results is None:
        results = get_results(db_path=db_path)

    total = len(results)
    positive = 0
    neutral = 0
    negative = 0
    high = 0
    medium = 0
    low = 0

    for r in results:
        s = str(r.get("sentiment", "")).strip().capitalize()
        p = str(r.get("priority", "")).strip().capitalize()

        if s == "Positive":
            positive += 1
        elif s == "Neutral":
            neutral += 1
        elif s == "Negative":
            negative += 1

        if p == "High":
            high += 1
        elif p == "Medium":
            medium += 1
        elif p == "Low":
            low += 1

    positive_pct = round((positive / total) * 100, 1) if total > 0 else 0.0
    neutral_pct = round((neutral / total) * 100, 1) if total > 0 else 0.0
    negative_pct = round((negative / total) * 100, 1) if total > 0 else 0.0
    high_pct = round((high / total) * 100, 1) if total > 0 else 0.0

    return {
        "total": total,
        "positive": positive,
        "neutral": neutral,
        "negative": negative,
        "high": high,
        "medium": medium,
        "low": low,
        "positive_pct": positive_pct,
        "neutral_pct": neutral_pct,
        "negative_pct": negative_pct,
        "high_pct": high_pct,
    }


def _format_chart_dict(counts_dict: dict[str, int]) -> dict:
    """
    Formats a count dictionary for Chart.js usage:
    {
        "labels": [...],
        "data": [...],
        "datasets": [{"data": [...]}],
        ... direct key access for counts
    }
    """
    labels = list(counts_dict.keys())
    data = [counts_dict[k] for k in labels]
    chart_dict = {
        "labels": labels,
        "data": data,
        "datasets": [{"data": data}],
    }
    for k, v in counts_dict.items():
        if k not in chart_dict:
            chart_dict[k] = v
    return chart_dict


def get_chart_data(results: list[dict] | None = None, db_path=None) -> tuple[dict, dict, dict]:
    """
    Returns (sentiment_counts, emotion_counts, category_counts) formatted for Chart.js.
    If results is None, queries the database.
    """
    if results is None:
        results = get_results(db_path=db_path)

    sentiment_order = getattr(config, "SENTIMENTS", ["Positive", "Neutral", "Negative"])
    emotion_order = getattr(config, "EMOTIONS", ["Joy", "Anger", "Sadness", "Fear", "Surprise", "Neutral"])
    category_order = getattr(config, "CATEGORIES", [
        "Product Quality",
        "Delivery",
        "Customer Service",
        "Payment",
        "Pricing",
        "Technical Issue",
        "Refund / Return",
    ])

    sentiment_counts = {k: 0 for k in sentiment_order}
    emotion_counts = {k: 0 for k in emotion_order}
    category_counts = {k: 0 for k in category_order}

    for r in results:
        # Sentiment count
        s = str(r.get("sentiment", "")).strip()
        matched_s = next((k for k in sentiment_counts if k.lower() == s.lower()), None)
        if matched_s:
            sentiment_counts[matched_s] += 1
        elif s:
            sentiment_counts[s] = sentiment_counts.get(s, 0) + 1

        # Emotion count
        e = str(r.get("emotion", "")).strip()
        matched_e = next((k for k in emotion_counts if k.lower() == e.lower()), None)
        if matched_e:
            emotion_counts[matched_e] += 1
        elif e:
            emotion_counts[e] = emotion_counts.get(e, 0) + 1

        # Category count
        c = str(r.get("category", "")).strip()
        matched_c = next((k for k in category_counts if k.lower() == c.lower()), None)
        if matched_c:
            category_counts[matched_c] += 1
        elif c:
            category_counts[c] = category_counts.get(c, 0) + 1

    return (
        _format_chart_dict(sentiment_counts),
        _format_chart_dict(emotion_counts),
        _format_chart_dict(category_counts),
    )


def clear_feedback(db_path=None) -> None:
    """
    Clears all rows from the feedback table.
    """
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        with conn:
            conn.execute("DELETE FROM feedback")

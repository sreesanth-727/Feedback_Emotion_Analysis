"""Analysis Service for FeedbackIQ.

Orchestrates text preprocessing, machine learning predictions (sentiment, emotion,
category), rule-based priority assignment, and batch file ingestion.
"""

from datetime import datetime
import io
from pathlib import Path
from typing import Any, Dict, List, Tuple
import pandas as pd

from config import ALLOWED_EXTENSIONS, URGENT_KEYWORDS
from ml.model import predict_all
from ml.preprocess import clean_text
from ml.priority import assign_priority, has_urgent_keyword
from services.db_service import insert_batch, insert_feedback


def get_priority_rationale(sentiment: str, emotion: str, text: str, priority: str) -> str:
    """Generate a human-readable explanation of why a priority was assigned."""
    lower_text = text.lower()
    matched_keywords = [kw for kw in URGENT_KEYWORDS if kw in lower_text]

    if priority == "High":
        reasons = []
        if emotion in {"Anger", "Fear", "Sadness"}:
            reasons.append(f"strong negative emotion ({emotion})")
        if matched_keywords:
            reasons.append(f"urgent keyword(s): {', '.join(matched_keywords[:3])}")
        reason_str = " and ".join(reasons) if reasons else "critical issue detected"
        return f"High priority assigned due to Negative sentiment with {reason_str}. Requires immediate response."

    if priority == "Medium":
        return "Medium priority assigned for negative or mixed feedback without severe urgency signals. Follow standard SLA."

    return "Low priority assigned for positive or neutral feedback. Useful for routine monitoring and satisfaction tracking."


def analyze_feedback(text: str) -> Dict[str, Any]:
    """Run full analysis pipeline on a single feedback text.

    Args:
        text: Raw customer feedback string.

    Returns:
        Dict containing normalized feedback, predictions, priority, rationale, and timestamp.
    """
    cleaned = clean_text(text)
    predictions = predict_all(cleaned)

    sentiment = predictions["sentiment"]
    emotion = predictions["emotion"]
    category = predictions["category"]
    priority = assign_priority(sentiment, emotion, cleaned)
    rationale = get_priority_rationale(sentiment, emotion, cleaned, priority)

    return {
        "feedback": cleaned,
        "sentiment": sentiment,
        "emotion": emotion,
        "category": category,
        "priority": priority,
        "rationale": rationale,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def parse_upload_file(file_storage) -> List[str]:
    """Parse an uploaded CSV or TXT file into a list of feedback strings.

    Args:
        file_storage: Werkzeug FileStorage object or file-like object with a filename.

    Returns:
        List of non-empty feedback string items.

    Raises:
        ValueError: If file extension is unsupported or content cannot be parsed.
    """
    filename = getattr(file_storage, "filename", "") or ""
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '.{extension}'. Please upload a .csv or .txt file."
        )

    # Read binary content
    content_bytes = file_storage.read()
    if not content_bytes:
        return []

    # Handle TXT files
    if extension == "txt":
        text_content = ""
        for encoding in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                text_content = content_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        return [
            line.strip()
            for line in text_content.splitlines()
            if line.strip()
        ]

    # Handle CSV files
    buffer = io.BytesIO(content_bytes)
    df = None
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            buffer.seek(0)
            df = pd.read_csv(buffer, encoding=encoding)
            break
        except Exception:
            continue

    if df is not None and not df.empty:
        possible_column_names = [
            "feedback", "review", "comment", "text", "customer_feedback",
            "feedback_text", "reviews", "comments", "customer feedback"
        ]

        col_map = {str(c).strip().lower(): c for c in df.columns}
        selected_col = None

        for candidate in possible_column_names:
            if candidate in col_map:
                selected_col = col_map[candidate]
                break

        if selected_col is None:
            # Fall back to the first object/string column if available, else first column
            object_cols = [c for c in df.columns if df[c].dtype == object]
            selected_col = object_cols[0] if object_cols else df.columns[0]

        raw_items = df[selected_col].dropna().astype(str).tolist()
        return [item.strip() for item in raw_items if item.strip()]

    # Fallback for CSVs with unquoted commas in rows
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text_content = content_bytes.decode(encoding)
            lines = [line.strip() for line in text_content.splitlines() if line.strip()]
            if not lines:
                return []
            first_line = lines[0].lower().strip().strip('"\'')
            known_headers = {
                "feedback", "review", "comment", "text", "customer_feedback",
                "feedback_text", "reviews", "comments", "customer feedback"
            }
            if any(first_line == h or first_line.startswith(h + ",") for h in known_headers):
                lines = lines[1:]
            return [line.strip().strip('"\'') for line in lines if line.strip()]
        except Exception:
            continue

    return []


def process_batch(feedback_items: List[str], db_path=None) -> Dict[str, Any]:
    """Analyze a list of feedback strings and persist valid ones into the database.

    Args:
        feedback_items: List of feedback strings.
        db_path: Optional SQLite database file path.

    Returns:
        Summary dict containing counts and processed records.
    """
    processed_records = []
    failed_count = 0

    for item in feedback_items:
        try:
            result = analyze_feedback(item)
            processed_records.append(result)
        except Exception:
            failed_count += 1

    saved_count = 0
    if processed_records:
        saved_count = insert_batch(processed_records, db_path=db_path)

    return {
        "total": len(feedback_items),
        "saved": saved_count,
        "failed": failed_count,
        "records": processed_records
    }

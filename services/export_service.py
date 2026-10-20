"""
Export service for FeedbackIQ.
Handles generation of CSV exports with UTF-8 BOM encoding for Excel compatibility.
"""

import csv
import io


def generate_csv_bytes(results: list[dict]) -> io.BytesIO:
    """
    Generates a CSV byte stream from feedback result dictionaries.

    Columns included:
      - id
      - feedback
      - sentiment
      - emotion
      - category
      - priority
      - created_at

    Encoding: utf-8-sig (includes UTF-8 Byte Order Mark for Microsoft Excel compatibility)
    Returns: io.BytesIO buffer positioned at offset 0.
    """
    fieldnames = ["id", "feedback", "sentiment", "emotion", "category", "priority", "created_at"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for row in results:
        row_dict = dict(row)
        # Normalize in case 'text' was supplied instead of 'feedback'
        if "feedback" not in row_dict and "text" in row_dict:
            row_dict["feedback"] = row_dict["text"]
        writer.writerow(row_dict)

    csv_bytes = output.getvalue().encode("utf-8-sig")
    buffer = io.BytesIO(csv_bytes)
    buffer.seek(0)
    return buffer

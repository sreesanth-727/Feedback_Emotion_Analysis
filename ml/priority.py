"""
Rule-based priority assignment engine for FeedbackIQ.
Categorizes feedback into High, Medium, or Low priority based on sentiment,
emotion, and urgent keyword detection.
"""

from typing import List, Set

URGENT_KEYWORDS: List[str] = [
    "refund",
    "broken",
    "damaged",
    "late",
    "never arrived",
    "not arrived",
    "charged twice",
    "hacked",
    "unacceptable",
    "urgent",
    "immediately",
    "asap",
    "fraud",
    "unsafe",
    "cannot access",
    "can't access",
    "scam",
    "cancel",
    "emergency",
    "defective",
]

HIGH_PRIORITY_EMOTIONS: Set[str] = {"Anger", "Fear", "Sadness"}


def has_urgent_keyword(text: str) -> bool:
    """
    Check if the text contains any urgent keywords (case-insensitive substring check).
    """
    if not isinstance(text, str):
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in URGENT_KEYWORDS)


def assign_priority(sentiment: str, emotion: str, text: str) -> str:
    """
    Assign priority (High, Medium, Low) based on sentiment, emotion, and text.

    Rules:
    - High priority:
        sentiment == 'Negative' AND (emotion in {'Anger', 'Fear', 'Sadness'} OR has_urgent_keyword)
    - Medium priority:
        sentiment == 'Negative' (and does not meet High priority criteria)
    - Low priority:
        Otherwise (e.g. sentiment in {'Positive', 'Neutral'})

    Args:
        sentiment: Predicted or actual sentiment ('Positive', 'Neutral', 'Negative').
        emotion: Predicted or actual emotion ('Joy', 'Anger', 'Sadness', 'Fear', 'Surprise', 'Neutral').
        text: Feedback text string.

    Returns:
        'High', 'Medium', or 'Low' priority label.
    """
    sentiment_normalized = sentiment.strip().capitalize() if isinstance(sentiment, str) else ""
    emotion_normalized = emotion.strip().capitalize() if isinstance(emotion, str) else ""

    urgent = has_urgent_keyword(text)

    if sentiment_normalized == "Negative" and (
        emotion_normalized in HIGH_PRIORITY_EMOTIONS or urgent
    ):
        return "High"

    if sentiment_normalized == "Negative":
        return "Medium"

    return "Low"

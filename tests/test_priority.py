"""
Unit tests for rule-based priority assignment in FeedbackIQ.
Tests assign_priority and urgent keyword detection.
"""

import pytest
from ml.priority import (
    assign_priority,
    has_urgent_keyword,
    URGENT_KEYWORDS,
    HIGH_PRIORITY_EMOTIONS,
)


class TestUrgentKeywords:
    """Test suite for keyword-based urgency detection."""

    def test_all_urgent_keywords_present_in_list(self):
        expected_keywords = [
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
        for kw in expected_keywords:
            assert kw in URGENT_KEYWORDS

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("I need a refund immediately", True),
            ("The item arrived BROKEN into pieces", True),
            ("This is completely unacceptable service", True),
            ("Package has not arrived yet", True),
            ("My parcel never arrived at my house", True),
            ("I was charged twice on my card", True),
            ("My account was hacked yesterday", True),
            ("Please send help asap", True),
            ("This company feels like a scam", True),
            ("I want to cancel my subscription right now", True),
            ("Emergency: cannot access my login", True),
            ("This feels unsafe to use", True),
            ("The product is totally defective", True),
            ("It arrived late and cold", True),
            ("I suspect fraud on my credit line", True),
            ("I can't access my dashboard", True),
            ("Love this amazing product so much", False),
            ("The color is blue and it works fine", False),
            ("Everything is okay, standard shipment", False),
        ],
    )
    def test_has_urgent_keyword_detection(self, text, expected):
        assert has_urgent_keyword(text) is expected

    def test_has_urgent_keyword_non_string(self):
        assert has_urgent_keyword(None) is False
        assert has_urgent_keyword(12345) is False
        assert has_urgent_keyword(["refund"]) is False


class TestAssignPriority:
    """Test suite for priority assignment logic."""

    @pytest.mark.parametrize(
        "emotion",
        ["Anger", "Fear", "Sadness", "anger", "fear", "sadness"],
    )
    def test_high_priority_negative_sentiment_with_high_priority_emotions(self, emotion):
        # High priority even without urgent keywords
        priority = assign_priority("Negative", emotion, "The item does not match expectations")
        assert priority == "High"

    def test_high_priority_negative_sentiment_with_urgent_keyword(self):
        # Negative + Neutral emotion, but has urgent keyword "refund"
        priority = assign_priority(
            "Negative", "Neutral", "I demand a full refund for this purchase"
        )
        assert priority == "High"

        # Negative + Surprise emotion, but has urgent keyword "broken"
        priority = assign_priority(
            "Negative", "Surprise", "I was astonished that the glass was broken"
        )
        assert priority == "High"

    def test_medium_priority_negative_without_urgent_keywords_or_high_emotions(self):
        # Negative + Neutral emotion, no urgent keywords
        priority = assign_priority(
            "Negative", "Neutral", "The battery life is slightly below average"
        )
        assert priority == "Medium"

        # Negative + Surprise emotion, no urgent keywords
        priority = assign_priority(
            "Negative", "Surprise", "The color was surprisingly dull"
        )
        assert priority == "Medium"

    @pytest.mark.parametrize("sentiment", ["Positive", "positive", "POSITIVE"])
    def test_low_priority_positive_sentiment(self, sentiment):
        # Positive feedback is always low priority even if mentioning words like "cancel" or "refund"
        assert assign_priority(sentiment, "Joy", "I love this wonderful device!") == "Low"
        assert (
            assign_priority(
                sentiment, "Joy", "I decided not to cancel because it works so well"
            )
            == "Low"
        )

    @pytest.mark.parametrize("sentiment", ["Neutral", "neutral", "NEUTRAL"])
    def test_low_priority_neutral_sentiment(self, sentiment):
        # Neutral feedback is always low priority
        assert (
            assign_priority(sentiment, "Neutral", "Can you explain how the warranty works?")
            == "Low"
        )
        assert (
            assign_priority(
                sentiment, "Neutral", "When will my refund be processed by the bank?"
            )
            == "Low"
        )

    def test_case_insensitivity_and_whitespace(self):
        assert assign_priority(" negative ", " anger ", "device failed") == "High"
        assert assign_priority("NEGATIVE", "FEAR", "device failed") == "High"
        assert assign_priority("positive", "joy", "great quality") == "Low"

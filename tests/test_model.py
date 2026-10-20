"""
Unit tests for Machine Learning pipelines and preprocessing in FeedbackIQ.
Tests clean_text, model creation, training, serialization, loading, and inference.
"""

from pathlib import Path
import pytest
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from ml.preprocess import clean_text
from ml.model import (
    create_pipeline,
    train_models,
    load_models,
    predict_all,
    predict_sentiment,
    predict_emotion,
    predict_category,
    MODELS_DIR,
)

VALID_SENTIMENTS = {"Positive", "Neutral", "Negative"}
VALID_EMOTIONS = {"Joy", "Anger", "Sadness", "Fear", "Surprise", "Neutral"}
VALID_CATEGORIES = {
    "Product Quality",
    "Delivery",
    "Customer Service",
    "Payment",
    "Pricing",
    "Technical Issue",
    "Refund / Return",
}


class TestPreprocess:
    """Tests for text cleaning and validation."""

    def test_clean_text_normal_string(self):
        result = clean_text("  This is a great    product!  \n\t Highly recommended.  ")
        assert result == "This is a great product! Highly recommended."

    def test_clean_text_unicode_normalization(self):
        # Fullwidth Latin letters (e.g. Ｇｏｏｄ) should normalize to ASCII
        fullwidth_text = "Ｇｏｏｄ product"
        cleaned = clean_text(fullwidth_text)
        assert cleaned == "Good product"

    @pytest.mark.parametrize("empty_input", ["", "   ", "\t\t\n\n  ", "\r\n"])
    def test_clean_text_empty_or_whitespace_raises(self, empty_input):
        with pytest.raises(ValueError, match="cannot be empty"):
            clean_text(empty_input)

    @pytest.mark.parametrize("invalid_type", [None, 1234, 45.67, [], {}, True])
    def test_clean_text_non_string_raises(self, invalid_type):
        with pytest.raises(ValueError, match="must be a string"):
            clean_text(invalid_type)


class TestPipelineArchitecture:
    """Tests for model pipeline construction and hyperparameters."""

    def test_create_pipeline_structure(self):
        pipe = create_pipeline()
        assert isinstance(pipe, Pipeline)
        assert "tfidf" in pipe.named_steps
        assert "clf" in pipe.named_steps

        tfidf = pipe.named_steps["tfidf"]
        assert isinstance(tfidf, TfidfVectorizer)
        assert tfidf.lowercase is True
        assert tfidf.ngram_range == (1, 2)
        assert tfidf.sublinear_tf is True

        clf = pipe.named_steps["clf"]
        assert isinstance(clf, LogisticRegression)
        assert clf.max_iter == 1000
        assert clf.class_weight == "balanced"
        assert clf.random_state == 42


class TestModelTrainingAndLoading:
    """Tests for training, serialization, and loading."""

    def test_load_models_from_default_dir(self):
        models = load_models()
        assert isinstance(models, dict)
        assert set(models.keys()) == {"sentiment", "emotion", "category"}
        for key, model in models.items():
            assert isinstance(model, Pipeline)

    def test_load_models_missing_dir_raises(self, tmp_path):
        empty_dir = tmp_path / "non_existent_models"
        with pytest.raises(FileNotFoundError):
            load_models(models_dir=empty_dir)

    def test_train_models_missing_csv_raises(self, tmp_path):
        missing_csv = tmp_path / "missing.csv"
        with pytest.raises(FileNotFoundError):
            train_models(data_path=missing_csv)

    def test_train_models_missing_required_columns_raises(self, tmp_path):
        bad_csv = tmp_path / "bad.csv"
        df = pd.DataFrame({
            "text": ["Great product"],
            "sentiment": ["Positive"]
        })
        df.to_csv(bad_csv, index=False)
        with pytest.raises(ValueError, match="missing required columns"):
            train_models(data_path=bad_csv)

    def test_train_models_custom_path_and_artifacts(self, tmp_path):
        custom_csv = tmp_path / "custom_data.csv"
        custom_models_dir = tmp_path / "custom_models"

        df = pd.DataFrame({
            "feedback": [
                "Amazing quality item",
                "Arrived late and damaged",
                "Average quality product",
                "Customer service was rude",
                "Charged twice for order",
                "Website login broken",
                "Need full refund now"
            ],
            "sentiment": [
                "Positive", "Negative", "Neutral", "Negative",
                "Negative", "Negative", "Negative"
            ],
            "emotion": [
                "Joy", "Anger", "Neutral", "Anger",
                "Anger", "Fear", "Anger"
            ],
            "category": [
                "Product Quality", "Delivery", "Product Quality", "Customer Service",
                "Payment", "Technical Issue", "Refund / Return"
            ],
        })
        df.to_csv(custom_csv, index=False)

        trained = train_models(data_path=custom_csv, models_dir=custom_models_dir)
        assert set(trained.keys()) == {"sentiment", "emotion", "category"}

        assert (custom_models_dir / "sentiment_model.joblib").exists()
        assert (custom_models_dir / "emotion_model.joblib").exists()
        assert (custom_models_dir / "category_model.joblib").exists()

        loaded = load_models(models_dir=custom_models_dir)
        assert set(loaded.keys()) == {"sentiment", "emotion", "category"}


class TestPredictions:
    """Tests for inference functions."""

    @pytest.fixture(autouse=True)
    def ensure_default_models(self):
        """Ensure standard models are loaded before tests."""
        load_models(MODELS_DIR)

    def test_predict_all_valid_text(self):
        text = "The package arrived early and customer support was wonderful!"
        preds = predict_all(text)

        assert isinstance(preds, dict)
        assert set(preds.keys()) == {"sentiment", "emotion", "category"}
        assert preds["sentiment"] in VALID_SENTIMENTS
        assert preds["emotion"] in VALID_EMOTIONS
        assert preds["category"] in VALID_CATEGORIES

    def test_predict_individual_functions(self):
        text = "Terrible experience, completely broken on delivery."
        s = predict_sentiment(text)
        e = predict_emotion(text)
        c = predict_category(text)

        assert s in VALID_SENTIMENTS
        assert e in VALID_EMOTIONS
        assert c in VALID_CATEGORIES

    @pytest.mark.parametrize("invalid_text", ["", "   ", None, 999])
    def test_predict_all_invalid_text_raises(self, invalid_text):
        with pytest.raises(ValueError):
            predict_all(invalid_text)

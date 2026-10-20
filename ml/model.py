"""
Machine Learning Model Pipelines for FeedbackIQ.
Builds, trains, serializes, and serves Scikit-learn pipelines for:
- Sentiment classification (Positive, Neutral, Negative)
- Emotion classification (Joy, Anger, Sadness, Fear, Surprise, Neutral)
- Category classification (Product Quality, Delivery, Customer Service,
                           Payment, Pricing, Technical Issue, Refund / Return)
"""

from pathlib import Path
from typing import Dict, Optional, Tuple, Any

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from ml.preprocess import clean_text
from ml.priority import assign_priority

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
DEFAULT_DATA_PATH = DATA_DIR / "training_data.csv"

# Global in-memory cache for loaded model pipelines
_MODELS: Dict[str, Pipeline] = {}


def create_pipeline() -> Pipeline:
    """
    Construct a TF-IDF + Logistic Regression classification pipeline.
    Uses sublinear TF scaling, unigram + bigram features, balanced class weighting,
    and a fixed random state for reproducibility.
    """
    return Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                sublinear_tf=True,
            ),
        ),
        (
            "clf",
            LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
                random_state=42,
            ),
        ),
    ])


def train_models(
    data_path: Optional[Path | str] = None,
    models_dir: Optional[Path | str] = None,
) -> Dict[str, Pipeline]:
    """
    Train separate sentiment, emotion, and category classification models,
    and serialize them to the models directory.

    Args:
        data_path: Path to the CSV file containing training data.
                   Defaults to data/training_data.csv.
        models_dir: Directory where model artifacts will be saved.
                    Defaults to models/.

    Returns:
        Dictionary mapping model names ('sentiment', 'emotion', 'category')
        to trained Pipeline instances.
    """
    global _MODELS

    csv_path = Path(data_path) if data_path else DEFAULT_DATA_PATH
    save_dir = Path(models_dir) if models_dir else MODELS_DIR

    if not csv_path.exists():
        raise FileNotFoundError(f"Training dataset not found at {csv_path}")

    save_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)

    required_columns = {"feedback", "sentiment", "emotion", "category"}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"Training data missing required columns: {missing}")

    # Drop any nulls and strip whitespace
    df = df.dropna(subset=list(required_columns)).copy()
    texts = [clean_text(str(t)) for t in df["feedback"]]
    sentiments = df["sentiment"].astype(str).str.strip().tolist()
    emotions = df["emotion"].astype(str).str.strip().tolist()
    categories = df["category"].astype(str).str.strip().tolist()

    # Train Sentiment pipeline
    sentiment_model = create_pipeline()
    sentiment_model.fit(texts, sentiments)
    joblib.dump(sentiment_model, save_dir / "sentiment_model.joblib")

    # Train Emotion pipeline
    emotion_model = create_pipeline()
    emotion_model.fit(texts, emotions)
    joblib.dump(emotion_model, save_dir / "emotion_model.joblib")

    # Train Category pipeline
    category_model = create_pipeline()
    category_model.fit(texts, categories)
    joblib.dump(category_model, save_dir / "category_model.joblib")

    trained = {
        "sentiment": sentiment_model,
        "emotion": emotion_model,
        "category": category_model,
    }
    _MODELS = trained
    return trained


def load_models(models_dir: Optional[Path | str] = None) -> Dict[str, Pipeline]:
    """
    Load the sentiment, emotion, and category pipelines from disk.

    Args:
        models_dir: Directory where model artifacts are stored.
                    Defaults to models/.

    Returns:
        Dictionary mapping model names ('sentiment', 'emotion', 'category')
        to loaded Pipeline instances.
    """
    global _MODELS

    target_dir = Path(models_dir) if models_dir else MODELS_DIR

    sentiment_path = target_dir / "sentiment_model.joblib"
    emotion_path = target_dir / "emotion_model.joblib"
    category_path = target_dir / "category_model.joblib"

    for path in (sentiment_path, emotion_path, category_path):
        if not path.exists():
            raise FileNotFoundError(
                f"Model file not found at {path}. Please train models first using train_models()."
            )

    sentiment_model = joblib.load(sentiment_path)
    emotion_model = joblib.load(emotion_path)
    category_model = joblib.load(category_path)

    _MODELS = {
        "sentiment": sentiment_model,
        "emotion": emotion_model,
        "category": category_model,
    }
    return _MODELS


def _ensure_models_loaded() -> Dict[str, Pipeline]:
    """Internal helper to ensure models are loaded into cache."""
    global _MODELS
    if not _MODELS or any(k not in _MODELS for k in ("sentiment", "emotion", "category")):
        load_models()
    return _MODELS


def predict_sentiment(text: str) -> str:
    """Predict sentiment label ('Positive', 'Neutral', 'Negative') for feedback text."""
    cleaned = clean_text(text)
    models = _ensure_models_loaded()
    return str(models["sentiment"].predict([cleaned])[0])


def predict_emotion(text: str) -> str:
    """Predict emotion label for feedback text."""
    cleaned = clean_text(text)
    models = _ensure_models_loaded()
    return str(models["emotion"].predict([cleaned])[0])


def predict_category(text: str) -> str:
    """Predict category label for feedback text."""
    cleaned = clean_text(text)
    models = _ensure_models_loaded()
    return str(models["category"].predict([cleaned])[0])


def predict_all(text: str) -> Dict[str, str]:
    """
    Clean text and predict sentiment, emotion, and category labels.

    Args:
        text: Raw customer feedback string.

    Returns:
        Dictionary with keys 'sentiment', 'emotion', 'category'.

    Raises:
        ValueError: If text is empty, whitespace only, or non-string.
    """
    cleaned = clean_text(text)
    models = _ensure_models_loaded()

    sentiment = str(models["sentiment"].predict([cleaned])[0])
    emotion = str(models["emotion"].predict([cleaned])[0])
    category = str(models["category"].predict([cleaned])[0])

    return {
        "sentiment": sentiment,
        "emotion": emotion,
        "category": category,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("FeedbackIQ: Training NLP & ML Classification Models")
    print("=" * 60)

    trained_models = train_models()
    print(f"Successfully trained and saved 3 models to: {MODELS_DIR}")

    sample_queries = [
        "Amazing product, excellent quality and fast delivery!",
        "The package arrived broken and damaged, worst delivery ever.",
        "I was charged twice, fix my payment immediately!",
        "Can you please tell me when my order will arrive?",
        "I am afraid my account has been hacked and personal info leaked.",
        "I want a refund for this defective item right now.",
        "The upgrade was surprisingly great and much better than expected.",
    ]

    print("\nVerification Predictions:")
    print("-" * 60)
    for q in sample_queries:
        preds = predict_all(q)
        priority = assign_priority(preds["sentiment"], preds["emotion"], q)
        print(f"Text: '{q}'")
        print(f" -> Sentiment : {preds['sentiment']}")
        print(f" -> Emotion   : {preds['emotion']}")
        print(f" -> Category  : {preds['category']}")
        print(f" -> Priority  : {priority}")
        print("-" * 60)

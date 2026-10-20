"""
FeedbackIQ Machine Learning Package.
Provides text preprocessing, sentiment/emotion/category model training,
prediction pipelines, and rule-based priority assignment.
"""

from ml.preprocess import clean_text
from ml.priority import (
    assign_priority,
    has_urgent_keyword,
    URGENT_KEYWORDS,
    HIGH_PRIORITY_EMOTIONS,
)

__all__ = [
    "clean_text",
    "assign_priority",
    "has_urgent_keyword",
    "URGENT_KEYWORDS",
    "HIGH_PRIORITY_EMOTIONS",
    "create_pipeline",
    "train_models",
    "load_models",
    "predict_all",
    "predict_sentiment",
    "predict_emotion",
    "predict_category",
]


def __getattr__(name: str):
    if name in {
        "create_pipeline",
        "train_models",
        "load_models",
        "predict_all",
        "predict_sentiment",
        "predict_emotion",
        "predict_category",
    }:
        import ml.model as _model_module
        return getattr(_model_module, name)
    raise AttributeError(f"module 'ml' has no attribute '{name}'")

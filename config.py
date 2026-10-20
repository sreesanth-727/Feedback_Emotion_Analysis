import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
DATABASE_DIR = BASE_DIR / "database"
DB_PATH = DATABASE_DIR / "feedback.db"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

# Application settings
SECRET_KEY = os.environ.get("SECRET_KEY", "feedbackiq-secure-secret-key-2026")
ALLOWED_EXTENSIONS = {"csv", "txt"}

# ML and taxonomy definitions
SENTIMENTS = ["Positive", "Neutral", "Negative"]
EMOTIONS = ["Joy", "Anger", "Sadness", "Fear", "Surprise", "Neutral"]
CATEGORIES = [
    "Product Quality",
    "Delivery",
    "Customer Service",
    "Payment",
    "Pricing",
    "Technical Issue",
    "Refund / Return"
]

# Priority urgency keywords (from Report Table 3.3 and Annexure)
URGENT_KEYWORDS = [
    "urgent", "immediately", "asap", "fraud",
    "unsafe", "charged twice", "cannot access",
    "can't access", "not arrived", "never arrived",
    "refund", "broken", "damaged", "scam",
    "cancel", "emergency", "defective", "hacked", "unacceptable"
]

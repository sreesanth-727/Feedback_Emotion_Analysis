# AI-Based Customer Feedback & Emotion Analysis System
## Complete Project Blueprint (End-to-End Implementation Guide)

**Project Title:** AI-Based Customer Feedback & Emotion Analysis System  
**Type:** Mini Project (Phase-I Design + Full Implementation Blueprint)  
**Institution:** Sona College of Technology, Department of CSE  
**Tech Stack:** Python 3, Flask, Scikit-learn, Pandas, SQLite, HTML/CSS/JavaScript (Chart.js)  
**Goal:** Lightweight, open-source, locally deployable web application that automatically analyzes customer feedback for **sentiment**, **emotion**, **category**, and **priority**, stores results, and presents an interactive dashboard.

This document is a complete blueprint. Follow it to implement the system from scratch. All design decisions are derived directly from the project report.

---

## 1. Project Overview & Objectives

### Core Problem Solved
Manual reading of large volumes of unstructured customer feedback (reviews, surveys, support tickets) is slow, inconsistent, and does not scale. Important complaints get buried.

### System Capabilities
- Accept single feedback (manual text entry)
- Accept batch uploads (CSV / TXT files)
- Predict **Sentiment**: Positive / Neutral / Negative (TF-IDF + Logistic Regression)
- Detect **Emotion**: Joy, Anger, Sadness, Fear, Surprise (or Neutral)
- Classify **Category**: Product Quality, Delivery, Customer Service, Payment (plus extensions: Pricing, Technical Issue, Refund/Return)
- Assign **Priority**: High / Medium / Low (rule-based + model signals)
- Persist every analysis in SQLite
- Interactive dashboard with summary cards, charts, searchable history table
- One-click CSV export of all analyzed data

### Key Design Principles
- Fully open-source, no commercial licenses
- Lightweight (runs on a standard laptop)
- Modular 4-layer architecture
- Transparent and reproducible ML pipeline
- Single-user local deployment (easily extendable later)

---

## 2. System Architecture

### 2.1 Four-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Presentation Layer                         │
│  (HTML + CSS + JavaScript + Chart.js)                       │
│  • Dashboard, forms, charts, history table, export button   │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP (Flask templates / JSON)
┌───────────────────────────▼─────────────────────────────────┐
│                  Application Layer                          │
│  (Flask routes + request validation + file handling)        │
│  • Routing, input validation, orchestration, CSV export     │
└───────────────────────────┬─────────────────────────────────┘
                            │ Function calls
┌───────────────────────────▼─────────────────────────────────┐
│               NLP & Machine Learning Layer                  │
│  • Preprocessing → TF-IDF → Logistic Regression             │
│  • Emotion / Category prediction                            │
│  • Priority rule engine                                     │
└───────────────────────────┬─────────────────────────────────┘
                            │ SQL / File I/O
┌───────────────────────────▼─────────────────────────────────┐
│                      Data Layer                             │
│  • SQLite database (feedback table)                         │
│  • Saved model files (pickle / joblib)                      │
│  • Training dataset (CSV)                                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow (End-to-End)

1. User enters text **or** uploads CSV/TXT
2. Application Layer validates & parses input
3. Text is cleaned and passed to NLP/ML Layer
4. Sentiment, Emotion, Category, Priority are predicted
5. Results are stored in SQLite
6. Dashboard is refreshed (aggregate stats + history)
7. Optional: Export entire results table as CSV

---

## 3. Complete Folder & File Structure

```
feedback_emotion_analysis/                 # Project root
│
├── app.py                                 # Main Flask application entry point
├── config.py                              # Configuration (paths, constants, priority rules)
├── requirements.txt                       # Exact dependency list
├── README.md                              # Setup & run instructions
│
├── models/                                # Saved ML artifacts
│   ├── sentiment_model.joblib
│   ├── emotion_model.joblib
│   └── category_model.joblib
│
├── data/                                  # Data assets
│   ├── training_data.csv                  # Labeled dataset used for training
│   └── sample_feedback.csv                # Sample file for testing batch upload
│
├── database/                              # Database related
│   └── feedback.db                        # SQLite database (created at runtime)
│
├── ml/                                    # Machine Learning package
│   ├── __init__.py
│   ├── model.py                           # Training + prediction pipelines
│   ├── preprocess.py                      # Text cleaning utilities
│   └── priority.py                        # Rule-based priority assignment
│
├── services/                              # Business logic services
│   ├── __init__.py
│   ├── analysis_service.py                # Orchestrates full analysis
│   ├── db_service.py                      # All SQLite CRUD + aggregates
│   └── export_service.py                  # CSV export logic
│
├── templates/                             # Jinja2 HTML templates
│   ├── base.html                          # Base layout
│   ├── index.html                         # Landing / analysis page
│   ├── dashboard.html                     # Full dashboard
│   └── history.html                       # Optional dedicated history view
│
├── static/                                # Frontend assets
│   ├── css/
│   │   └── style.css                      # Custom styles
│   ├── js/
│   │   └── dashboard.js                   # Chart.js initialization + interactions
│   └── img/                               # Optional logos / icons
│
└── tests/                                 # Optional but recommended
    ├── test_model.py
    ├── test_priority.py
    └── test_db.py
```

---

## 4. Core Dependencies

Create `requirements.txt` with the following (pinned for reproducibility):

```txt
flask==3.0.3
pandas==2.2.2
scikit-learn==1.5.1
joblib==1.4.2
numpy==1.26.4
nltk==3.8.1          # optional – for stopwords if desired
python-dotenv==1.0.1 # optional – for config
```

**Install command:**
```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## 5. Component Responsibilities

| Component                  | File(s)                          | Responsibility |
|---------------------------|----------------------------------|----------------|
| **Flask App**             | `app.py`                         | Route definitions, request handling, template rendering, file upload |
| **Configuration**         | `config.py`                      | Paths, DB URI, priority rules, allowed file extensions, constants |
| **ML Pipelines**          | `ml/model.py`                    | Train & load TF-IDF + LogisticRegression for Sentiment / Emotion / Category |
| **Text Preprocessing**    | `ml/preprocess.py`               | Lowercasing, cleaning, tokenization, stop-word removal |
| **Priority Engine**       | `ml/priority.py`                 | Rule-based High/Medium/Low assignment |
| **Analysis Orchestrator** | `services/analysis_service.py`   | Single entry point: text → full analysis dict |
| **Database Service**      | `services/db_service.py`         | Create table, insert, query aggregates, fetch history |
| **Export Service**        | `services/export_service.py`     | Generate downloadable CSV from database |
| **Frontend Templates**    | `templates/*.html`               | UI structure (forms, cards, charts, table) |
| **Frontend Logic**        | `static/js/dashboard.js`         | Chart.js rendering, AJAX (if used), table search/filter |
| **Styling**               | `static/css/style.css`           | Clean, modern dashboard look |

---

## 6. Detailed Component Design

### 6.1 Database Schema (SQLite)

```sql
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    sentiment TEXT NOT NULL,          -- Positive / Neutral / Negative
    emotion TEXT NOT NULL,            -- Joy / Anger / Sadness / Fear / Surprise / Neutral
    category TEXT NOT NULL,           -- Product Quality / Delivery / ...
    priority TEXT NOT NULL,           -- High / Medium / Low
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6.2 Priority Assignment Rules (from report Table 3.3)

| Priority | Typical Conditions                                      | Suggested Action                  |
|----------|---------------------------------------------------------|-----------------------------------|
| **High** | Negative sentiment + (Anger or Fear) **or** urgent words (refund, broken, late, charged twice, etc.) | Respond & resolve immediately    |
| **Medium** | Negative or mixed feedback without strong urgency     | Review within normal SLA         |
| **Low**  | Positive or Neutral feedback                            | Monitor for trends               |

Implement as a pure function that receives the analysis dict and returns the priority string.

### 6.3 Sentiment / Emotion / Category Models

- **Feature Extraction:** `TfidfVectorizer(lowercase=True, ngram_range=(1,2), sublinear_tf=True)`
- **Classifier:** `LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)`
- Train three separate pipelines (one for each target label)
- Persist with `joblib.dump()` so the app loads instantly at startup

The annexure already provides a solid starter `TRAINING_DATA` list. Expand it or convert it into `data/training_data.csv`.

### 6.4 Main Flask Routes (Recommended)

| Method | Endpoint              | Purpose                              |
|--------|-----------------------|--------------------------------------|
| GET    | `/`                   | Landing page with analysis form      |
| POST   | `/analyze`            | Analyze single text feedback         |
| POST   | `/upload`             | Handle CSV / TXT batch upload        |
| GET    | `/dashboard`          | Full interactive dashboard           |
| GET    | `/api/stats`          | JSON aggregate statistics            |
| GET    | `/api/history`        | JSON paginated history               |
| GET    | `/export`             | Download all results as CSV          |
| GET    | `/clear` (optional)   | Clear database (dev only)            |

### 6.5 Frontend Dashboard Layout (matches report Figure 3.4)

```
┌──────────────────────────────────────────────────────────────┐
│  AI-Based Customer Feedback & Emotion Analysis – Dashboard   │
├────────────┬────────────┬────────────┬───────────────────────┤
│ Total      │ Positive % │ Negative % │ High Priority Count   │
│ Feedback   │            │            │                       │
├────────────┴────────────┴────────────┴───────────────────────┤
│  Sentiment Chart (Pie/Bar)   │   Emotion Chart (Bar)         │
├──────────────────────────────┴───────────────────────────────┤
│  Feedback History Table (searchable / filterable)            │
│  text | sentiment | emotion | category | priority | date     │
├──────────────────────────────────────────────────────────────┤
│  [Upload CSV/TXT]                    [Export CSV]            │
└──────────────────────────────────────────────────────────────┘
```

Use **Chart.js** for the two charts. Keep the UI clean and responsive.

---

## 7. Implementation Roadmap (Step-by-Step)

1. **Project Scaffolding**
   - Create the folder structure above
   - Write `requirements.txt` and install dependencies
   - Create virtual environment

2. **Data & Models**
   - Convert the annexure `TRAINING_DATA` into `data/training_data.csv`
   - Implement `ml/model.py` (train + save three pipelines)
   - Implement `ml/preprocess.py` and `ml/priority.py`
   - Train models once and save to `models/`

3. **Database Layer**
   - Implement `services/db_service.py` (create table, insert, aggregates, fetch)

4. **Core Analysis Service**
   - `services/analysis_service.py` → `analyze(text) → dict`

5. **Flask Application**
   - Write `app.py` with all routes
   - Implement file upload handling (Pandas for CSV, line-by-line for TXT)
   - Wire everything together

6. **Frontend**
   - Create `templates/base.html` + `dashboard.html`
   - Style with `static/css/style.css`
   - Initialize charts in `static/js/dashboard.js`

7. **Testing & Evaluation**
   - Manual single-entry tests
   - Batch upload with 100 / 1000 entries
   - Measure accuracy on a held-out set (populate Table 4.2 style results)
   - Verify priority rules against known urgent examples

8. **Polish**
   - Error handling & flash messages
   - Input validation
   - Responsive design
   - README with clear run instructions

---

## 8. Key Code Skeletons (Ready to Expand)

### 8.1 `ml/model.py` (core of the ML layer)

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

def create_pipeline():
    return Pipeline([
        ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42))
    ])

def train_and_save(texts, labels, model_name: str):
    pipe = create_pipeline()
    pipe.fit(texts, labels)
    joblib.dump(pipe, MODELS_DIR / f"{model_name}.joblib")
    return pipe

def load_model(model_name: str):
    return joblib.load(MODELS_DIR / f"{model_name}.joblib")
```

### 8.2 Priority Logic (`ml/priority.py`)

```python
URGENT_KEYWORDS = {
    "refund", "broken", "damaged", "late", "never arrived",
    "charged twice", "hacked", "unacceptable", "urgent", "immediately"
}

def assign_priority(sentiment: str, emotion: str, text: str) -> str:
    text_lower = text.lower()
    has_urgent = any(kw in text_lower for kw in URGENT_KEYWORDS)

    if sentiment == "Negative" and (emotion in {"Anger", "Fear"} or has_urgent):
        return "High"
    if sentiment == "Negative":
        return "Medium"
    return "Low"
```

### 8.3 Database Service (minimal interface)

```python
def init_db():
    ...

def insert_feedback(text, sentiment, emotion, category, priority):
    ...

def get_summary_stats() -> dict:
    # total, positive_pct, negative_pct, high_priority_count, emotion_counts, etc.
    ...

def get_all_feedback(limit=500) -> list[dict]:
    ...
```

---

## 9. Evaluation Framework (from Chapter 4)

After implementation, record results in the following templates:

- **Sentiment Classification** → Accuracy, Precision, Recall, F1 per class + overall
- **Emotion / Category** → Agreement with manually labeled samples
- **Priority** → Precision & Recall for the High class
- **Performance** → Analysis + storage time for 100 / 1 000 / 10 000 entries
- **Functional** → Upload success, dashboard update, export correctness

---

## 10. Future Extensions (from report Section 5.2)

- Replace rule-based emotion/category with supervised models
- Add transformer models (BERT / DistilBERT) as optional backend
- Multi-language / code-mixed support
- Live ingestion (email, Twitter/X, review APIs)
- Multi-user authentication + PostgreSQL
- Trend analysis, keyword clouds, automatic alerts
- Docker containerization + cloud deployment

---

## 11. Quick Start Commands (After Implementation)

```bash
# 1. Create & activate environment
python -m venv venv
source venv/bin/activate

# 2. Install
pip install -r requirements.txt

# 3. Train models (one-time)
python -m ml.model          # or a dedicated train.py

# 4. Run the application
python app.py

# Open browser → http://127.0.0.1:5000
```

---

## 12. Summary Checklist for a Complete Working System

- [ ] Folder structure created
- [ ] `requirements.txt` installed
- [ ] Training data prepared and models trained + saved
- [ ] SQLite schema + CRUD working
- [ ] Single text analysis working end-to-end
- [ ] CSV and TXT batch upload working
- [ ] Priority rules correctly applied
- [ ] Dashboard shows live stats + charts + history
- [ ] CSV export downloads correct data
- [ ] Basic error handling and validation present
- [ ] README with clear instructions

This blueprint contains everything required to implement a production-quality version of the **AI-Based Customer Feedback & Emotion Analysis System** exactly as described in the project report. Follow the structure and responsibilities above and you will have a clean, maintainable, and fully functional application.
# FeedbackIQ: AI-Based Customer Feedback & Emotion Analysis System

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask 3.0](https://img.shields.io/badge/Flask-3.0%2B-green.svg)](https://flask.palletsprojects.com/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.5%2B-orange.svg)](https://scikit-learn.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

An end-to-end, locally deployable intelligence system developed in accordance with the Sona College of Technology CSE Phase-I specification. **FeedbackIQ** automatically analyzes unstructured customer feedback for **sentiment**, **emotion**, **category**, and **priority**, stores results in an embedded SQLite database, and presents insights through an interactive web dashboard with **Chart.js** visualizations.

---

## Key Capabilities

1. **Multi-Aspect AI Inference:**
   - **Sentiment Classification:** Positive, Neutral, Negative via TF-IDF + Logistic Regression.
   - **Emotion Detection:** Joy, Anger, Sadness, Fear, Surprise, Neutral.
   - **Business Categorization:** Product Quality, Delivery, Customer Service, Payment, Pricing, Technical Issue, Refund / Return.
   - **Rule-Based Priority Scoring:** Triage engine assigning **High**, **Medium**, or **Low** priority based on sentiment, emotion severity (Anger, Fear, Sadness), and 20+ urgency keywords.
2. **Flexible Ingestion:**
   - **Single Analysis:** Test and inspect individual text entries with rationale explanations.
   - **Batch File Upload:** Process large CSV or TXT files in seconds (auto-detects feedback column headers).
3. **Executive Dashboard:**
   - 4 Live KPI Cards (Total feedback, Positive %, Negative %, High-Priority urgency count).
   - Real-time Chart.js charts: Sentiment Doughnut Chart, Emotion Breakdown Bar Chart, and Category Distribution.
   - Recent feedback table with color-coded status badges.
4. **Data Persistence & Audit:**
   - Embedded SQLite database (`database/feedback.db`) with indexing.
   - Searchable, multi-filter audit history (`/history`).
   - One-click CSV Export with UTF-8 BOM encoding for Excel compatibility.
5. **Headless REST API:**
   - `/api/stats`: JSON aggregate metrics and chart distribution payloads.
   - `/api/history`: JSON query and filter endpoint.
   - `/api/analyze`: JSON single-entry inference endpoint.

---

## System Architecture

The application adheres to a modular 4-layer architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                  Presentation Layer                         │
│  (HTML5 + CSS3 + Plus Jakarta Sans + Chart.js)              │
│  • Dashboard, forms, charts, history table, export button   │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP (Jinja2 / JSON)
┌───────────────────────────▼─────────────────────────────────┐
│                  Application Layer                          │
│  (Flask routes + request validation + file handling)        │
│  • Routing, input validation, orchestration, CSV export     │
└───────────────────────────┬─────────────────────────────────┘
                            │ Function calls
┌───────────────────────────▼─────────────────────────────────┐
│               NLP & Machine Learning Layer                  │
│  • Preprocessing (NFKC normalization, cleaning)             │
│  • TF-IDF Vectorizer (ngram 1-2, sublinear_tf)              │
│  • Logistic Regression (balanced class weights)             │
│  • Priority rule engine (Table 3.3)                         │
└───────────────────────────┬─────────────────────────────────┘
                            │ SQL / Joblib I/O
┌───────────────────────────▼─────────────────────────────────┐
│                      Data Layer                             │
│  • SQLite database (database/feedback.db)                   │
│  • Serialized models (models/*.joblib)                      │
│  • Datasets (data/training_data.csv, sample files)          │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
D:\FeedBack\
├── app.py                     # Main Flask application entrypoint & REST routes
├── config.py                  # Project paths, priority keywords, taxonomies
├── benchmark.py               # Academic benchmark replication (Tables 4.2-4.4)
├── requirements.txt           # Python dependency requirements
├── README.md                  # Comprehensive setup and usage guide
│
├── data/
│   ├── training_data.csv      # 148 balanced training examples (Annexure + extensions)
│   ├── sample_feedback.csv    # Sample CSV for batch upload testing
│   └── sample_feedback.txt    # Sample line-by-line TXT for batch testing
│
├── database/
│   └── feedback.db            # SQLite database (auto-initialized at runtime)
│
├── ml/
│   ├── __init__.py            # ML package exports
│   ├── preprocess.py          # Text normalization and input validation
│   ├── model.py               # TF-IDF + LogisticRegression training & inference
│   └── priority.py            # Rule-based priority assignment engine
│
├── models/                    # Serialized model artifacts (.joblib)
│   ├── sentiment_model.joblib
│   ├── emotion_model.joblib
│   └── category_model.joblib
│
├── services/
│   ├── __init__.py            # Service package exports
│   ├── analysis_service.py    # Analysis orchestrator & file parser
│   ├── db_service.py          # SQLite CRUD, KPI aggregations & chart formatting
│   └── export_service.py      # UTF-8 BOM CSV generator
│
├── static/
│   ├── css/style.css          # Modern dashboard stylesheet
│   ├── js/dashboard.js        # Chart.js initialization & UI interactions
│   └── sample_feedback.csv    # Downloadable template for users
│
├── templates/
│   ├── base.html              # Layout shell with navigation & clear modal
│   ├── index.html             # Dashboard with KPI cards, charts & recent table
│   ├── analyze.html           # Single feedback tester with prompt samples
│   ├── upload.html            # Batch upload interface for CSV and TXT
│   ├── history.html           # Searchable and filterable history view
│   └── about.html             # Project architecture & methodology docs
│
└── tests/
    ├── test_app.py            # Flask route integration & API tests (22 tests)
    ├── test_db.py             # Database CRUD, KPIs, export tests (21 tests)
    ├── test_model.py          # ML pipeline, preprocessing tests (24 tests)
    └── test_priority.py       # Priority rule & urgency keyword tests (36 tests)
```

---

## Quick Start Guide

### 1. Prerequisites
Ensure Python 3.10+ is installed on your machine.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. (Optional) Re-train Machine Learning Models
Pre-trained model artifacts are included in `models/`. To retrain from `data/training_data.csv`:
```bash
python -m ml.model
```

### 4. Run the Web Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## Running Automated Tests

Run the full test suite with `pytest`:
```bash
python -m pytest tests/ -v
```
All **103 unit and integration tests** will execute and verify all layers.

---

## Running Academic Benchmarks

Replicate the Chapter 4 experimental evaluation tables from the project report:
```bash
python benchmark.py
```
Outputs:
- **Table 4.2:** Sentiment Classification Results (Precision, Recall, F1, Accuracy)
- **Table 4.3:** Category vs. Priority Cross-Tabulation
- **Table 4.4:** Batch Processing Latency Benchmarks (10, 100, 1000 items)

# Feedback_Emotion_Analysis

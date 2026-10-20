"""Integration and unit tests for FeedbackIQ Flask application routes and API endpoints."""

import io
import pytest
from app import app
from services.db_service import clear_feedback, init_db, insert_feedback


@pytest.fixture
def client():
    """Create a Flask test client with an isolated in-memory or test database."""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    init_db()
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clean_db():
    """Ensure database is clean before each test."""
    clear_feedback()
    yield
    clear_feedback()


class TestDashboardRoutes:
    def test_dashboard_get(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert b"Feedback Analytics Dashboard" in response.data

    def test_dashboard_alias(self, client):
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert b"Feedback Analytics Dashboard" in response.data

    def test_dashboard_with_existing_records(self, client):
        insert_feedback(
            feedback="Great service and fast delivery",
            sentiment="Positive",
            emotion="Joy",
            category="Delivery",
            priority="Low",
        )
        response = client.get("/")
        assert response.status_code == 200
        assert b"Great service and fast delivery" in response.data


class TestAnalyzeRoutes:
    def test_analyze_get(self, client):
        response = client.get("/analyze")
        assert response.status_code == 200
        assert b"Single Feedback Analysis" in response.data

    def test_analyze_post_positive(self, client):
        response = client.post("/analyze", data={
            "feedback": "Outstanding experience, I loved the high quality and prompt support!"
        })
        assert response.status_code == 200
        assert b"Feedback analyzed and recorded successfully." in response.data
        assert b"Positive" in response.data

    def test_analyze_post_urgent_negative(self, client):
        response = client.post("/analyze", data={
            "feedback": "My item arrived completely broken and damaged, refund my money immediately!"
        })
        assert response.status_code == 200
        assert b"Negative" in response.data
        assert b"HIGH" in response.data

    def test_analyze_post_empty(self, client):
        response = client.post("/analyze", data={"feedback": "   "})
        assert response.status_code == 200
        assert b"Please enter customer feedback text" in response.data


class TestUploadRoutes:
    def test_upload_get(self, client):
        response = client.get("/upload")
        assert response.status_code == 200
        assert b"Batch Feedback Upload" in response.data

    def test_upload_post_no_file(self, client):
        response = client.post("/upload", data={}, follow_redirects=True)
        assert response.status_code == 200
        assert b"Please select a CSV or TXT file" in response.data

    def test_upload_post_csv(self, client):
        csv_content = (
            "review\n"
            "The product arrived quickly and works as advertised\n"
            "Terrible customer service, rude staff\n"
            "Average quality, nothing impressive\n"
        )
        data = {
            "file": (io.BytesIO(csv_content.encode("utf-8")), "test_reviews.csv")
        }
        response = client.post("/upload", data=data, content_type="multipart/form-data", follow_redirects=True)
        assert response.status_code == 200
        assert b"Successfully processed and stored 3 feedback entries" in response.data

    def test_upload_post_txt(self, client):
        txt_content = (
            "Superb delivery, arrived early!\n"
            "Completely broken and unusable, refund me ASAP!\n"
        )
        data = {
            "file": (io.BytesIO(txt_content.encode("utf-8")), "test_feedback.txt")
        }
        response = client.post("/upload", data=data, content_type="multipart/form-data", follow_redirects=True)
        assert response.status_code == 200
        assert b"Successfully processed and stored 2 feedback entries" in response.data

    def test_upload_post_invalid_extension(self, client):
        data = {
            "file": (io.BytesIO(b"binary data"), "test.pdf")
        }
        response = client.post("/upload", data=data, content_type="multipart/form-data", follow_redirects=True)
        assert response.status_code == 200
        assert b"Unsupported file type" in response.data


class TestHistoryRoutes:
    def test_history_get(self, client):
        insert_feedback("Battery life is great", "Positive", "Joy", "Product Quality", "Low")
        insert_feedback("Charged twice on my credit card", "Negative", "Anger", "Payment", "High")

        response = client.get("/history")
        assert response.status_code == 200
        assert b"Battery life is great" in response.data
        assert b"Charged twice on my credit card" in response.data

    def test_history_filters(self, client):
        insert_feedback("Battery life is great", "Positive", "Joy", "Product Quality", "Low")
        insert_feedback("Charged twice on my credit card", "Negative", "Anger", "Payment", "High")

        # Filter by sentiment
        response = client.get("/history?sentiment=Negative")
        assert response.status_code == 200
        assert b"Charged twice on my credit card" in response.data
        assert b"Battery life is great" not in response.data

        # Filter by priority
        response_high = client.get("/history?priority=High")
        assert response_high.status_code == 200
        assert b"Charged twice on my credit card" in response_high.data
        assert b"Battery life is great" not in response_high.data

        # Search keyword
        response_search = client.get("/history?search=battery")
        assert response_search.status_code == 200
        assert b"Battery life is great" in response_search.data
        assert b"Charged twice" not in response_search.data


class TestAboutAndExportRoutes:
    def test_about_get(self, client):
        response = client.get("/about")
        assert response.status_code == 200
        assert b"FeedbackIQ" in response.data
        assert b"Architecture" in response.data

    def test_export_csv(self, client):
        insert_feedback("Quality check feedback", "Positive", "Joy", "Product Quality", "Low")
        response = client.get("/export")
        assert response.status_code == 200
        assert response.headers["Content-Type"].startswith("text/csv")
        assert b"Quality check feedback" in response.data


class TestClearHistoryRoute:
    def test_clear_history(self, client):
        insert_feedback("Test item to be deleted", "Neutral", "Neutral", "General", "Low")
        response = client.post("/clear", follow_redirects=True)
        assert response.status_code == 200
        assert b"database cleared successfully" in response.data

        # Verify history is empty
        history_resp = client.get("/history")
        assert b"Test item to be deleted" not in history_resp.data


class TestAPIRoutes:
    def test_api_stats(self, client):
        insert_feedback("Excellent service", "Positive", "Joy", "Customer Service", "Low")
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["summary"]["total"] == 1
        assert "sentiment_counts" in data

    def test_api_history(self, client):
        insert_feedback("API history entry", "Neutral", "Neutral", "General", "Low")
        response = client.get("/api/history")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["count"] == 1
        assert data["records"][0]["feedback"] == "API history entry"

    def test_api_analyze_success(self, client):
        response = client.post("/api/analyze", json={
            "text": "The delivery was delayed and damaged, refund immediately"
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data["status"] == "success"
        assert data["data"]["priority"] == "High"
        assert data["data"]["sentiment"] == "Negative"

    def test_api_analyze_invalid(self, client):
        response = client.post("/api/analyze", json={})
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"


class TestErrorHandlers:
    def test_404_handler(self, client):
        response = client.get("/non-existent-route-404")
        assert response.status_code == 404
        assert b"404 - Page Not Found" in response.data

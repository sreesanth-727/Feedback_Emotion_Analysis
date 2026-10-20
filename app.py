"""FeedbackIQ - AI-Based Customer Feedback & Emotion Analysis System.

Main Flask application module wiring the presentation, application,
NLP/machine learning, and data persistence layers.
"""

from datetime import datetime
import io
import os
from pathlib import Path
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

import config
from services.analysis_service import (
    analyze_feedback,
    parse_upload_file,
    process_batch,
)
from services.db_service import (
    clear_feedback,
    get_chart_data,
    get_results,
    get_summary,
    init_db,
    insert_feedback,
)
from services.export_service import generate_csv_bytes

app = Flask(
    __name__,
    template_folder=str(config.TEMPLATES_DIR),
    static_folder=str(config.STATIC_DIR),
)
app.secret_key = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload limit

# Initialize database on startup
init_db()


@app.route("/")
@app.route("/dashboard")
def index():
    """Main dashboard showing KPI summary cards, interactive charts, and recent feedback."""
    stats = get_summary()
    sentiment_counts, emotion_counts, category_counts = get_chart_data()
    recent_feedback = get_results(limit=10)

    return render_template(
        "index.html",
        page="dashboard",
        stats=stats,
        summary=stats,
        recent_feedback=recent_feedback,
        feedbacks=recent_feedback,
        sentiment_counts=sentiment_counts,
        emotion_counts=emotion_counts,
        category_counts=category_counts,
    )


@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    """Single feedback analysis view for testing individual customer inputs."""
    result = None
    feedback_text = ""

    if request.method == "POST":
        feedback_text = request.form.get("feedback", "").strip()

        if not feedback_text:
            flash("Please enter customer feedback text to analyze.", "error")
            return render_template(
                "analyze.html",
                page="analyze",
                result=None,
                text=""
            )

        try:
            result = analyze_feedback(feedback_text)
            insert_feedback(
                feedback=result["feedback"],
                sentiment=result["sentiment"],
                emotion=result["emotion"],
                category=result["category"],
                priority=result["priority"],
                created_at=result["created_at"],
            )
            flash("Feedback analyzed and recorded successfully.", "success")
        except ValueError as val_err:
            flash(str(val_err), "error")
        except Exception as err:
            app.logger.exception("Feedback analysis failed")
            flash(f"Analysis failed: {err}", "error")

    return render_template(
        "analyze.html",
        page="analyze",
        result=result,
        text=feedback_text
    )


@app.route("/upload", methods=["GET", "POST"])
def upload():
    """Batch file upload endpoint supporting CSV and TXT files."""
    if request.method == "POST":
        uploaded_file = request.files.get("file")

        if not uploaded_file or not uploaded_file.filename:
            flash("Please select a CSV or TXT file to upload.", "error")
            return redirect(url_for("upload"))

        try:
            items = parse_upload_file(uploaded_file)

            if not items:
                flash(
                    "The uploaded file contains no valid customer feedback rows.",
                    "warning"
                )
                return redirect(url_for("upload"))

            batch_result = process_batch(items)
            saved = batch_result.get("saved", 0)
            failed = batch_result.get("failed", 0)

            if saved > 0:
                flash(
                    f"Successfully processed and stored {saved} feedback entries. "
                    f"(Skipped: {failed})",
                    "success",
                )
                return redirect(url_for("index"))
            else:
                flash(
                    "No valid feedback entries could be analyzed from the file.",
                    "error"
                )
                return redirect(url_for("upload"))

        except ValueError as val_err:
            flash(str(val_err), "error")
            return redirect(url_for("upload"))
        except Exception as err:
            app.logger.exception("Upload processing encountered an error")
            flash(f"Could not process the file: {err}", "error")
            return redirect(url_for("upload"))

    return render_template("upload.html", page="upload")


@app.route("/history")
def history():
    """Searchable and filterable history view of all analyzed feedback entries."""
    search_text = request.args.get("search", request.args.get("q", "")).strip()
    sentiment_filter = request.args.get("sentiment", "").strip()
    priority_filter = request.args.get("priority", "").strip()
    category_filter = request.args.get("category", "").strip()

    valid_sentiments = {"Positive", "Neutral", "Negative"}
    valid_priorities = {"High", "Medium", "Low"}

    if sentiment_filter and sentiment_filter not in valid_sentiments:
        sentiment_filter = ""
    if priority_filter and priority_filter not in valid_priorities:
        priority_filter = ""

    results = get_results(
        search_text=search_text,
        sentiment_filter=sentiment_filter,
        priority_filter=priority_filter,
        category_filter=category_filter,
    )

    return render_template(
        "history.html",
        page="history",
        results=results,
        feedbacks=results,
        search=search_text,
        selected_sentiment=sentiment_filter,
        selected_priority=priority_filter,
        selected_category=category_filter,
    )


@app.route("/about")
def about():
    """About page explaining project architecture, NLP/ML models, and methodology."""
    return render_template("about.html", page="about")


@app.route("/export")
def export_csv():
    """Export analyzed feedback records as a downloadable Excel-ready CSV file."""
    search_text = request.args.get("search", "").strip()
    sentiment_filter = request.args.get("sentiment", "").strip()
    priority_filter = request.args.get("priority", "").strip()
    category_filter = request.args.get("category", "").strip()

    results = get_results(
        search_text=search_text,
        sentiment_filter=sentiment_filter,
        priority_filter=priority_filter,
        category_filter=category_filter,
    )

    output = generate_csv_bytes(results)
    filename = f"feedbackiq_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return send_file(
        output,
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename,
    )


@app.route("/clear", methods=["POST", "GET"], endpoint="clear_history")
@app.route("/clear_history", methods=["POST", "GET"], endpoint="clear")
def clear():
    """Clear all stored feedback history from the database (for demo/testing resets)."""
    clear_feedback()
    flash("Customer feedback database cleared successfully.", "success")
    return redirect(url_for("index"))


# =========================================================================
# REST API Endpoints (For AJAX / Headless consumption)
# =========================================================================

@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Return JSON aggregate summary and Chart.js distribution data."""
    summary = get_summary()
    sentiment_counts, emotion_counts, category_counts = get_chart_data()
    return jsonify({
        "status": "success",
        "summary": summary,
        "sentiment_counts": sentiment_counts,
        "emotion_counts": emotion_counts,
        "category_counts": category_counts,
    })


@app.route("/api/history", methods=["GET"])
def api_history():
    """Return JSON filtered feedback history list."""
    search_text = request.args.get("search", "").strip()
    sentiment_filter = request.args.get("sentiment", "").strip()
    priority_filter = request.args.get("priority", "").strip()
    category_filter = request.args.get("category", "").strip()
    limit = request.args.get("limit", type=int)

    results = get_results(
        search_text=search_text,
        sentiment_filter=sentiment_filter,
        priority_filter=priority_filter,
        category_filter=category_filter,
        limit=limit,
    )
    return jsonify({
        "status": "success",
        "count": len(results),
        "records": results,
    })


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """API endpoint to analyze text and persist the result."""
    payload = request.get_json(silent=True) or {}
    text = payload.get("text") or payload.get("feedback")

    if not text or not isinstance(text, str) or not text.strip():
        return jsonify({
            "status": "error",
            "message": "Missing required 'text' or 'feedback' string in JSON body."
        }), 400

    try:
        result = analyze_feedback(text)
        row_id = insert_feedback(
            feedback=result["feedback"],
            sentiment=result["sentiment"],
            emotion=result["emotion"],
            category=result["category"],
            priority=result["priority"],
            created_at=result["created_at"],
        )
        result["id"] = row_id
        return jsonify({
            "status": "success",
            "data": result,
        }), 201
    except Exception as err:
        return jsonify({
            "status": "error",
            "message": str(err),
        }), 400


# =========================================================================
# Error Handlers
# =========================================================================

@app.errorhandler(404)
def page_not_found(error):
    return (
        "<!DOCTYPE html><html><head><title>404 Not Found</title></head>"
        "<body style='font-family:sans-serif; text-align:center; padding:4rem;'>"
        "<h1>404 - Page Not Found</h1>"
        "<p>The requested page does not exist.</p>"
        "<p><a href='/'>&larr; Return to FeedbackIQ Dashboard</a></p>"
        "</body></html>",
        404,
    )


@app.errorhandler(500)
def internal_server_error(error):
    return (
        "<!DOCTYPE html><html><head><title>500 Server Error</title></head>"
        "<body style='font-family:sans-serif; text-align:center; padding:4rem;'>"
        "<h1>500 - Internal Server Error</h1>"
        "<p>An unexpected error occurred while processing the request.</p>"
        "<p><a href='/'>&larr; Return to FeedbackIQ Dashboard</a></p>"
        "</body></html>",
        500,
    )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)

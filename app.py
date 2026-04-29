"""
StudyVibe Flask Web Application.

A web UI for the music recommender pipeline with:
- Student / Work / Personal mood sections
- Free-text activity input
- Language and era selectors
- Real-time recommendations with pipeline trace visualization
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from src.agent import run_pipeline
from src.catalog import LastFmClient
from src.guardrails import RecommendRequest, GuardrailError
from pydantic import ValidationError

# Load environment variables from .env file (LASTFM_API_KEY etc.)
load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")

# Initialize Last.fm client (reads LASTFM_API_KEY from .env)
lastfm_client = LastFmClient()
if lastfm_client.is_configured:
    print("[OK] Last.fm API configured - online music database enabled")
else:
    print("[WARN] LASTFM_API_KEY not set - online music database disabled (CSV-only mode)")


@app.route("/", methods=["GET"])
def index():
    """Serve the main UI page."""
    from src.activities import SECTIONS
    # Pass SECTIONS structure to template for rendering tabs and mood grids
    sections_data = {
        section: {
            mood: {
                "display_name": profile.display_name,
                "description": profile.description,
            }
            for mood, profile in moods.items()
        }
        for section, moods in SECTIONS.items()
    }
    return render_template("index.html", sections_json=json.dumps(sections_data))


@app.route("/api/recommend", methods=["POST"])
def recommend():
    """
    Main API endpoint.
    
    Request JSON:
    {
        "section": "student" (optional),
        "mood": "exam_cram" (optional),
        "free_text": "studying for final",
        "language": "English",
        "era": "2026",
        "use_lastfm": true,
        "k": 5
    }
    
    Response JSON:
    {
        "recommendations": [...],
        "pipeline_steps": [...],
        "error": null
    }
    """
    try:
        # Validate request body
        req_data = request.get_json() or {}
        req = RecommendRequest(**req_data)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400
    except Exception as e:
        return jsonify({"error": f"Request parsing error: {e}"}), 400

    try:
        # Run pipeline
        result = run_pipeline(
            free_text=req.free_text,
            section=req.section,
            mood=req.mood,
            language=req.language,
            era=req.era,
            use_lastfm=req.use_lastfm,
            k=req.k,
            lastfm_client=lastfm_client,
        )

        # Build response
        response = {
            "recommendations": result.recommendations,
            "pipeline_steps": [
                {
                    "name": s.name,
                    "input": s.input,
                    "output": s.output,
                    "latency_ms": round(s.latency_ms, 2),
                    "note": s.note,
                }
                for s in result.steps
            ],
            "intent": result.intent,
            "error": result.error,
        }

        if result.error:
            return jsonify(response), 400

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": f"Pipeline error: {str(e)}"}), 500


@app.route("/healthz", methods=["GET"])
def healthz():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({"error": "not found"}), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Create logs directory if needed
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Run app
    app.run(debug=True, host="0.0.0.0", port=5000)

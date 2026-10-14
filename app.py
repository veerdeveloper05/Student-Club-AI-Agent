import os
import sys

# Ensure UTF-8 output encoding for Windows terminals with emojis
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from flask import Flask, render_template, request, jsonify
from agent.club_agent import ClubAgent
from config import CLUBS_DATA_PATH, GEMINI_API_KEY, HOST, PORT, DEBUG

app = Flask(__name__, static_folder="static", template_folder="templates")

# ── Force UTF-8 charset on all HTML responses ──────────────────────────────
@app.after_request
def set_utf8_charset(response):
    if 'text/html' in response.content_type:
        response.content_type = 'text/html; charset=utf-8'
    return response

# ── Jinja2 filter: convert emoji chars to safe HTML entities ───────────────
def emoji_to_entity(text):
    """Convert each non-ASCII char to its &#x....; HTML numeric entity."""
    if not text:
        return text
    result = []
    for ch in str(text):
        cp = ord(ch)
        if cp > 127:
            result.append(f'&#x{cp:X};')
        else:
            result.append(ch)
    from markupsafe import Markup
    return Markup(''.join(result))

app.jinja_env.filters['emoji'] = emoji_to_entity

# Initialize the club information agent
agent = ClubAgent(data_path=CLUBS_DATA_PATH, gemini_api_key=GEMINI_API_KEY)


@app.route("/")
def index():
    """Renders the main student club assistant web interface."""
    clubs = agent.get_all_clubs()
    mode = agent.get_mode()
    return render_template("index.html", clubs=clubs, mode=mode)


@app.route("/api/status", methods=["GET"])
def get_status():
    """Returns the operational status and operating mode of the assistant."""
    return jsonify({
        "status": "online",
        "service": "Student Club Information AI Agent",
        "mode": agent.get_mode(),
        "clubs_count": len(agent.get_all_clubs())
    })


@app.route("/api/clubs", methods=["GET"])
def get_clubs():
    """Returns the list of all registered student clubs."""
    return jsonify({
        "success": True,
        "count": len(agent.get_all_clubs()),
        "clubs": agent.get_all_clubs()
    })


@app.route("/api/clubs/<club_id>", methods=["GET"])
def get_club(club_id):
    """Returns detailed information for a specific club."""
    club = agent.get_club_by_id(club_id)
    if not club:
        return jsonify({
            "success": False,
            "error": f"Club with ID '{club_id}' not found."
        }), 404
    return jsonify({
        "success": True,
        "club": club
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint.
    Receives user query, runs it through the ClubAgent,
    and returns a structured response.
    """
    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({
            "success": False,
            "error": "Message cannot be empty."
        }), 400

    response = agent.answer(user_message)

    return jsonify({
        "success": True,
        "reply": response.get("reply", ""),
        "club_id": response.get("club_id"),
        "suggestions": response.get("suggestions", []),
        "mode": agent.get_mode()
    })


if __name__ == "__main__":
    print("=" * 60)
    print("🎓 Student Club Information AI Agent")
    print(f"🚀 Running on: http://{HOST}:{PORT}")
    print(f"🧠 Operating Mode: {agent.get_mode()}")
    print("=" * 60)
    app.run(host=HOST, port=PORT, debug=DEBUG)

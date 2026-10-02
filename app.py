import io
import os
import secrets
import time

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file,
)
from dotenv import load_dotenv

from src.chains import (
    generate_study_plan,
    explain_topic,
    generate_quiz,
    get_public_quiz,
    grade_quiz,
)
from src.elevenlabs_tts import text_to_speech
from src.config import validate_config


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

# Maximum incoming request size: 2 MB
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024


# ============================================================
# QUIZ SESSION STORAGE
# ============================================================

"""
Development / hackathon-friendly in-memory quiz storage.

Structure:

quiz_sessions = {
    "random_quiz_id": {
        "quiz": {...},
        "created_at": 1234567890
    }
}

The complete quiz, including correct answers and explanations,
remains on the server.

The frontend receives only the public quiz.
"""

quiz_sessions = {}

# Quiz remains valid for 2 hours.
QUIZ_SESSION_TTL = 2 * 60 * 60

# Maximum number of active quiz sessions.
MAX_QUIZ_SESSIONS = 100


# ============================================================
# HELPER: JSON BODY
# ============================================================

def get_json_body():
    """
    Safely return JSON request body as a dictionary.
    """
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return None

    return data


# ============================================================
# HELPER: CLEAN STRING
# ============================================================

def clean_string(value, default=""):
    """
    Convert a value to a stripped string.
    """
    if value is None:
        return default

    return str(value).strip()


# ============================================================
# HELPER: CLEAN QUIZ SESSIONS
# ============================================================

def cleanup_quiz_sessions():
    """
    Remove expired quiz sessions.

    Also keeps the in-memory dictionary from becoming
    unnecessarily large during hackathon/demo usage.
    """

    current_time = time.time()

    expired_ids = [
        quiz_id
        for quiz_id, session in quiz_sessions.items()
        if current_time - session.get("created_at", 0)
        > QUIZ_SESSION_TTL
    ]

    for quiz_id in expired_ids:
        quiz_sessions.pop(quiz_id, None)

    # Keep only the newest sessions.
    if len(quiz_sessions) > MAX_QUIZ_SESSIONS:

        sorted_sessions = sorted(
            quiz_sessions.items(),
            key=lambda item: item[1].get("created_at", 0),
        )

        number_to_remove = (
            len(quiz_sessions) - MAX_QUIZ_SESSIONS
        )

        for quiz_id, _ in sorted_sessions[:number_to_remove]:
            quiz_sessions.pop(quiz_id, None)


# ============================================================
# HELPER: CREATE QUIZ ID
# ============================================================

def create_quiz_id():
    """
    Generate a cryptographically strong random quiz ID.
    """
    return secrets.token_urlsafe(24)


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def index():
    """
    Render the main CampusAI frontend.
    """
    return render_template("index.html")


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health():
    """
    Simple backend health-check endpoint.
    """

    return jsonify({
        "success": True,
        "status": "online",
        "app": "CampusAI",
    })


# ============================================================
# CONFIGURATION STATUS
# ============================================================

@app.get("/api/config")
def config_status():
    """
    Check whether required API keys are configured.
    """

    try:
        config_ok, config_message = validate_config()

        return jsonify({
            "configured": config_ok,
            "message": config_message,
        })

    except Exception as exc:

        print(
            f"[ERROR] Configuration check failed: {exc}"
        )

        return jsonify({
            "configured": False,
            "message": "Configuration check failed.",
        }), 500


# ============================================================
# AI GENERATION API
# ============================================================

@app.post("/api/generate")
def generate():
    """
    Main AI generation endpoint.

    Supported features:
        1. study_planner
        2. tutor

    Interactive quiz generation uses:
        /api/quiz/start
    """

    data = get_json_body()

    if data is None:
        return jsonify({
            "success": False,
            "error": "Invalid or empty JSON request.",
        }), 400

    feature = clean_string(
        data.get("feature")
    )

    payload = data.get(
        "payload",
        {},
    )

    if not isinstance(payload, dict):
        return jsonify({
            "success": False,
            "error": "Payload must be a JSON object.",
        }), 400

    if not feature:
        return jsonify({
            "success": False,
            "error": "Feature is required.",
        }), 400

    try:

        # ====================================================
        # STUDY PLANNER
        # ====================================================

        if feature == "study_planner":

            subject = clean_string(
                payload.get("subject")
            )

            hours = payload.get(
                "hours",
                "",
            )

            days = payload.get(
                "days",
                "",
            )

            level = clean_string(
                payload.get(
                    "level",
                    "Beginner",
                ),
                default="Beginner",
            )

            if not subject:
                return jsonify({
                    "success": False,
                    "error": (
                        "Please enter your subjects "
                        "or topics."
                    ),
                }), 400

            result = generate_study_plan(
                subject=subject,
                hours=hours,
                days=days,
                level=level,
            )

        # ====================================================
        # AI TUTOR
        # ====================================================

        elif feature == "tutor":

            topic = clean_string(
                payload.get("topic")
            )

            level = clean_string(
                payload.get(
                    "level",
                    "Beginner",
                ),
                default="Beginner",
            )

            if not topic:
                return jsonify({
                    "success": False,
                    "error": "Please enter a topic.",
                }), 400

            result = explain_topic(
                topic=topic,
                level=level,
            )

        # ====================================================
        # OLD QUIZ ROUTE
        # ====================================================

        elif feature == "quiz":

            return jsonify({
                "success": False,
                "error": (
                    "Interactive quizzes now use "
                    "/api/quiz/start."
                ),
            }), 400

        # ====================================================
        # UNKNOWN FEATURE
        # ====================================================

        else:

            return jsonify({
                "success": False,
                "error": (
                    f"Unknown feature: {feature}"
                ),
            }), 400

        # ====================================================
        # RETURN AI RESPONSE
        # ====================================================

        return jsonify({
            "success": True,
            "feature": feature,
            "result": result,
        })

    except Exception as exc:

        print(
            f"[ERROR] AI generation failed: {exc}"
        )

        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


# ============================================================
# START INTERACTIVE QUIZ
# ============================================================

@app.post("/api/quiz/start")
def start_quiz():
    """
    Generate a new interactive quiz.

    Request:

    {
        "topic": "Machine Learning",
        "difficulty": "Medium",
        "count": 10
    }

    Response:

    {
        "success": true,
        "quiz": {
            "quiz_id": "...",
            "title": "...",
            "topic": "...",
            "difficulty": "...",
            "questions": [...]
        }
    }

    IMPORTANT:
    correct_answer and explanation are never sent
    to the frontend during the quiz.
    """

    cleanup_quiz_sessions()

    data = get_json_body()

    if data is None:
        return jsonify({
            "success": False,
            "error": "Invalid or empty JSON request.",
        }), 400

    # --------------------------------------------------------
    # Read input
    # --------------------------------------------------------

    topic = clean_string(
        data.get("topic")
    )

    difficulty = clean_string(
        data.get(
            "difficulty",
            "Medium",
        ),
        default="Medium",
    )

    count = data.get(
        "count",
        5,
    )

    # --------------------------------------------------------
    # Validate topic
    # --------------------------------------------------------

    if not topic:
        return jsonify({
            "success": False,
            "error": "Please enter a quiz topic.",
        }), 400

    # --------------------------------------------------------
    # Validate question count
    # --------------------------------------------------------

    try:
        count = int(count)

    except (TypeError, ValueError):

        return jsonify({
            "success": False,
            "error": (
                "Number of questions must be "
                "a valid number."
            ),
        }), 400

    # Keep quiz size between 1 and 20.
    count = max(
        1,
        min(count, 20),
    )

    # --------------------------------------------------------
    # Validate difficulty
    # --------------------------------------------------------

    allowed_difficulties = {
        "Easy",
        "Medium",
        "Hard",
    }

    if difficulty not in allowed_difficulties:
        difficulty = "Medium"

    # --------------------------------------------------------
    # Generate quiz
    # --------------------------------------------------------

    try:

        print(
            f"[INFO] Generating quiz | "
            f"Topic: {topic} | "
            f"Difficulty: {difficulty} | "
            f"Questions: {count}"
        )

        full_quiz = generate_quiz(
            topic=topic,
            difficulty=difficulty,
            count=count,
        )

        # ----------------------------------------------------
        # Create server-side quiz session
        # ----------------------------------------------------

        quiz_id = create_quiz_id()

        quiz_sessions[quiz_id] = {
            "quiz": full_quiz,
            "created_at": time.time(),
        }

        # ----------------------------------------------------
        # Remove correct answers and explanations
        # ----------------------------------------------------

        public_quiz = get_public_quiz(
            full_quiz
        )

        # ====================================================
        # IMPORTANT FIX
        #
        # Frontend expects:
        #
        # currentQuiz.quiz_id
        #
        # Therefore quiz_id MUST be inside the quiz object.
        # ====================================================

        public_quiz["quiz_id"] = quiz_id

        print(
            f"[INFO] Quiz created successfully: "
            f"{quiz_id}"
        )

        return jsonify({
            "success": True,
            "quiz": public_quiz,
        })

    except Exception as exc:

        print(
            f"[ERROR] Quiz generation failed: {exc}"
        )

        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


# ============================================================
# SUBMIT INTERACTIVE QUIZ
# ============================================================

@app.post("/api/quiz/submit")
def submit_quiz():
    """
    Submit and grade an interactive quiz.

    Request:

    {
        "quiz_id": "...",
        "answers": {
            "1": "A",
            "2": "C",
            "3": "B"
        }
    }

    The correct answers remain server-side.
    """

    cleanup_quiz_sessions()

    data = get_json_body()

    if data is None:
        return jsonify({
            "success": False,
            "error": "Invalid or empty JSON request.",
        }), 400

    # --------------------------------------------------------
    # Read quiz ID
    # --------------------------------------------------------

    quiz_id = clean_string(
        data.get("quiz_id")
    )

    answers = data.get(
        "answers",
        {},
    )

    # --------------------------------------------------------
    # Validate quiz ID
    # --------------------------------------------------------

    if not quiz_id:

        return jsonify({
            "success": False,
            "error": "Quiz ID is required.",
        }), 400

    # --------------------------------------------------------
    # Validate answers
    # --------------------------------------------------------

    if not isinstance(answers, dict):

        return jsonify({
            "success": False,
            "error": (
                "Answers must be provided "
                "as a JSON object."
            ),
        }), 400

    # --------------------------------------------------------
    # Find quiz session
    # --------------------------------------------------------

    session = quiz_sessions.get(
        quiz_id
    )

    if session is None:

        return jsonify({
            "success": False,
            "error": (
                "Quiz session expired or "
                "could not be found. "
                "Please start a new quiz."
            ),
        }), 404

    # --------------------------------------------------------
    # Check expiration
    # --------------------------------------------------------

    created_at = session.get(
        "created_at",
        0,
    )

    if time.time() - created_at > QUIZ_SESSION_TTL:

        quiz_sessions.pop(
            quiz_id,
            None,
        )

        return jsonify({
            "success": False,
            "error": (
                "This quiz session has expired. "
                "Please start a new quiz."
            ),
        }), 410

    # --------------------------------------------------------
    # Retrieve full server-side quiz
    # --------------------------------------------------------

    full_quiz = session.get(
        "quiz"
    )

    if not isinstance(full_quiz, dict):

        return jsonify({
            "success": False,
            "error": "Invalid quiz session data.",
        }), 500

    # --------------------------------------------------------
    # Grade quiz
    # --------------------------------------------------------

    try:

        result = grade_quiz(
            quiz_data=full_quiz,
            user_answers=answers,
        )

        # ====================================================
        # IMPORTANT:
        #
        # DO NOT delete the session here.
        #
        # The frontend's "Try Again" button reuses the
        # current quiz. Keeping the session allows that.
        #
        # cleanup_quiz_sessions() will remove it automatically
        # after QUIZ_SESSION_TTL.
        # ====================================================

        print(
            f"[INFO] Quiz submitted | "
            f"Quiz ID: {quiz_id} | "
            f"Score: "
            f"{result.get('score')}/"
            f"{result.get('total')}"
        )

        return jsonify({
            "success": True,
            "quiz_id": quiz_id,
            "result": result,
        })

    except Exception as exc:

        print(
            f"[ERROR] Quiz grading failed: {exc}"
        )

        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


# ============================================================
# ELEVENLABS TEXT-TO-SPEECH API
# ============================================================

@app.post("/api/tts")
def tts():
    """
    Convert AI-generated text into MP3 audio
    using ElevenLabs.
    """

    data = get_json_body()

    if data is None:
        return jsonify({
            "success": False,
            "error": "Invalid or empty JSON request.",
        }), 400

    text = clean_string(
        data.get("text")
    )

    if not text:
        return jsonify({
            "success": False,
            "error": (
                "No text supplied for "
                "voice generation."
            ),
        }), 400

    # Prevent unnecessarily large TTS requests.
    if len(text) > 12000:
        return jsonify({
            "success": False,
            "error": (
                "Text is too long for voice generation. "
                "Please use a shorter response."
            ),
        }), 400

    try:

        print(
            "[INFO] Generating ElevenLabs voice..."
        )

        audio = text_to_speech(
            text
        )

        return send_file(
            io.BytesIO(audio),
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="campusai_voice.mp3",
        )

    except Exception as exc:

        print(
            f"[ERROR] ElevenLabs TTS failed: {exc}"
        )

        return jsonify({
            "success": False,
            "error": str(exc),
        }), 500


# ============================================================
# ERROR HANDLER: 404
# ============================================================

@app.errorhandler(404)
def not_found(error):
    """
    Handle unknown routes.
    """

    return jsonify({
        "success": False,
        "error": "Endpoint not found.",
    }), 404


# ============================================================
# ERROR HANDLER: 413
# ============================================================

@app.errorhandler(413)
def request_too_large(error):
    """
    Handle oversized requests.
    """

    return jsonify({
        "success": False,
        "error": "Request is too large.",
    }), 413


# ============================================================
# ERROR HANDLER: 500
# ============================================================

@app.errorhandler(500)
def internal_error(error):
    """
    Handle unexpected server errors.
    """

    return jsonify({
        "success": False,
        "error": "Internal server error.",
    }), 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            5000,
        )
    )

    print("=" * 60)
    print("🎓 CampusAI")
    print("🚀 Flask backend starting...")
    print(
        f"🌐 http://127.0.0.1:{port}"
    )
    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True,
    )
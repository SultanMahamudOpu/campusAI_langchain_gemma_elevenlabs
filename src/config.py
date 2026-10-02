import os
from dotenv import load_dotenv


# ============================================================
# Load Environment Variables
# ============================================================

load_dotenv()


# ============================================================
# Environment Helper
# ============================================================

def get_env(
    name: str,
    default: str | None = None
) -> str | None:
    """
    Safely retrieve an environment variable.

    Removes unnecessary whitespace and returns the default
    value if the variable is not available.
    """

    value = os.getenv(name, default)

    if value is None:
        return None

    value = value.strip()

    return value if value else default


# ============================================================
# API Keys
# ============================================================

GOOGLE_API_KEY = get_env("GOOGLE_API_KEY")

ELEVENLABS_API_KEY = get_env("ELEVENLABS_API_KEY")


# ============================================================
# Model Configuration
# ============================================================

GEMMA_MODEL = get_env(
    "GEMMA_MODEL",
    "gemma-3-4b-it",
)

ELEVENLABS_MODEL = get_env(
    "ELEVENLABS_MODEL",
    "eleven_multilingual_v2",
)

ELEVENLABS_VOICE_ID = get_env(
    "ELEVENLABS_VOICE_ID",
    "JBFqnCBsd6RMkjVDRZzb",
)


# ============================================================
# Gemma Configuration Validation
# ============================================================

def validate_gemma_config():
    """
    Validate Gemma/Google AI configuration.

    Returns:
        tuple[bool, str]
    """

    if not GOOGLE_API_KEY:
        return (
            False,
            "GOOGLE_API_KEY is missing. "
            "Please check your .env file.",
        )

    if not GEMMA_MODEL:
        return (
            False,
            "GEMMA_MODEL is missing.",
        )

    return True, "Gemma configuration looks good."


# ============================================================
# ElevenLabs Configuration Validation
# ============================================================

def validate_tts_config():
    """
    Validate ElevenLabs text-to-speech configuration.

    Returns:
        tuple[bool, str]
    """

    if not ELEVENLABS_API_KEY:
        return (
            False,
            "ELEVENLABS_API_KEY is missing. "
            "Please check your .env file.",
        )

    if not ELEVENLABS_MODEL:
        return (
            False,
            "ELEVENLABS_MODEL is missing.",
        )

    if not ELEVENLABS_VOICE_ID:
        return (
            False,
            "ELEVENLABS_VOICE_ID is missing.",
        )

    return True, "ElevenLabs configuration looks good."


# ============================================================
# Overall Configuration Validation
# ============================================================

def validate_config():
    """
    Validate the complete CampusAI configuration.

    Returns:
        tuple[bool, str]
    """

    gemma_ok, gemma_message = validate_gemma_config()

    if not gemma_ok:
        return False, gemma_message

    tts_ok, tts_message = validate_tts_config()

    if not tts_ok:
        return False, tts_message

    return True, "CampusAI configuration looks good."


# ============================================================
# Configuration Summary
# ============================================================

def get_config_summary():
    """
    Return a safe configuration summary.

    API keys are never exposed.
    """

    return {
        "gemma_model": GEMMA_MODEL,
        "elevenlabs_model": ELEVENLABS_MODEL,
        "elevenlabs_voice_id": ELEVENLABS_VOICE_ID,
        "google_api_configured": bool(GOOGLE_API_KEY),
        "elevenlabs_configured": bool(ELEVENLABS_API_KEY),
    }
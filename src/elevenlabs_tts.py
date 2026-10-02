from elevenlabs.client import ElevenLabs

from src.config import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_MODEL,
    ELEVENLABS_VOICE_ID,
)


# ============================================================
# ElevenLabs Client
# ============================================================

def get_elevenlabs_client() -> ElevenLabs:
    """
    Create and return an ElevenLabs client.

    Raises:
        ValueError: If the ElevenLabs API key is missing.
    """

    if not ELEVENLABS_API_KEY:
        raise ValueError(
            "ELEVENLABS_API_KEY is missing. "
            "Please add it to your .env file."
        )

    return ElevenLabs(
        api_key=ELEVENLABS_API_KEY
    )


# ============================================================
# Text-to-Speech
# ============================================================

def text_to_speech(text: str) -> bytes:
    """
    Convert text into MP3 audio using ElevenLabs.

    Args:
        text: Text to synthesize.

    Returns:
        MP3 audio as bytes.

    Raises:
        TypeError: If text is not a string.
        ValueError: If the input text or configuration is missing.
        RuntimeError: If ElevenLabs fails to generate audio.
    """

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if not isinstance(text, str):
        raise TypeError(
            "text_to_speech() expects text to be a string."
        )

    text = text.strip()

    if not text:
        raise ValueError(
            "Cannot synthesize empty text."
        )

    # --------------------------------------------------------
    # Validate ElevenLabs configuration
    # --------------------------------------------------------

    if not ELEVENLABS_MODEL:
        raise ValueError(
            "ELEVENLABS_MODEL is missing."
        )

    if not ELEVENLABS_VOICE_ID:
        raise ValueError(
            "ELEVENLABS_VOICE_ID is missing."
        )

    # --------------------------------------------------------
    # Get ElevenLabs client
    # --------------------------------------------------------

    client = get_elevenlabs_client()

    # --------------------------------------------------------
    # Generate speech
    # --------------------------------------------------------

    try:

        audio_stream = client.text_to_speech.convert(
            text=text,
            voice_id=ELEVENLABS_VOICE_ID,
            model_id=ELEVENLABS_MODEL,
            output_format="mp3_44100_128",
        )

        # ElevenLabs returns an iterable audio stream.
        audio_bytes = b"".join(audio_stream)

    except Exception as exc:

        raise RuntimeError(
            f"ElevenLabs text-to-speech generation failed: {exc}"
        ) from exc

    # --------------------------------------------------------
    # Validate generated audio
    # --------------------------------------------------------

    if not audio_bytes:
        raise RuntimeError(
            "ElevenLabs returned empty audio data."
        )

    return audio_bytes
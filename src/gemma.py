from langchain_google_genai import ChatGoogleGenerativeAI

from src.config import (
    GOOGLE_API_KEY,
    GEMMA_MODEL,
)


# ============================================================
# Gemma Model
# ============================================================

def get_gemma() -> ChatGoogleGenerativeAI:
    """
    Create and return the configured Gemma model.

    The API key and model name are loaded centrally
    from src.config.
    """

    # --------------------------------------------------------
    # Validate API key
    # --------------------------------------------------------

    if not GOOGLE_API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY is missing. "
            "Please add it to your .env file."
        )

    # --------------------------------------------------------
    # Validate model name
    # --------------------------------------------------------

    if not GEMMA_MODEL:
        raise ValueError(
            "GEMMA_MODEL is missing. "
            "Please check your .env file."
        )

    # --------------------------------------------------------
    # Create Gemma model
    # --------------------------------------------------------

    try:

        model = ChatGoogleGenerativeAI(
            model=GEMMA_MODEL,
            google_api_key=GOOGLE_API_KEY,

            # Balanced creativity for academic tasks
            temperature=0.4,

            # Enough output for study plans, explanations,
            # and multi-question quizzes
            max_output_tokens=2048,
        )

        return model

    except Exception as exc:

        raise RuntimeError(
            f"Failed to initialize Gemma model "
            f"'{GEMMA_MODEL}': {exc}"
        ) from exc
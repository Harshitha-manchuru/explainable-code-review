"""
Thin wrapper around the Gemini API. Falls back to a deterministic
offline stub when no API key is configured (app.config.USE_LLM_STUB),
so the full pipeline remains runnable without network access.
"""

import logging

from app.config import (
    GEMINI_API_KEY,
    GEMINI_MAX_OUTPUT_TOKENS,
    GEMINI_MODEL_NAME,
    GEMINI_TEMPERATURE,
    USE_LLM_STUB,
)

logger = logging.getLogger(__name__)

_genai_model = None

if not USE_LLM_STUB:
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)
    _genai_model = genai.GenerativeModel(GEMINI_MODEL_NAME)


def _stub_response(prompt: str) -> str:
    """
    Deterministic offline fallback used when GEMINI_API_KEY is not set.
    Extracts the rule title and rationale embedded in the prompt by the
    prompt template and reformats them as a plain explanation, so the
    rest of the pipeline (faithfulness checking, JSON shape) behaves
    identically whether or not a real LLM call was made.
    """
    rationale_marker = "Rationale:"
    title_marker = "Rule Title:"

    title = ""
    rationale = ""

    if title_marker in prompt:
        after_title = prompt.split(title_marker, 1)[1].lstrip("\n")
        title = after_title.split("\n", 1)[0].strip()

    if rationale_marker in prompt:
        after_rationale = prompt.split(rationale_marker, 1)[1].lstrip("\n")
        rationale = after_rationale.split("\n\n", 1)[0].strip()

    if not title and not rationale:
        return (
            "This line does not follow the cited style rule. Review the "
            "rule's rationale and adjust the code to match the recommended "
            "pattern shown in the good example."
        )

    return (
        f"This code does not follow the rule '{title}'. {rationale} "
        "Compare your code against the good example to see the recommended "
        "fix."
    )


def generate_text(prompt: str) -> str:
    """
    Sends the prompt to Gemini and returns the generated text. In stub
    mode, returns a deterministic offline explanation instead.
    """
    if USE_LLM_STUB:
        logger.info("USE_LLM_STUB is True; returning offline stub response.")
        return _stub_response(prompt)

    try:
        response = _genai_model.generate_content(
            prompt,
            generation_config={
                "temperature": GEMINI_TEMPERATURE,
                "max_output_tokens": GEMINI_MAX_OUTPUT_TOKENS,
            },
        )
        if response and response.text:
            return response.text.strip()
        return _stub_response(prompt)
    except Exception as exc:  # noqa: BLE001 - any SDK failure falls back safely
        logger.error("Gemini call failed: %s. Falling back to stub.", exc)
        return _stub_response(prompt)

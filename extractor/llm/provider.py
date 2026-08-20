"""
LLM provider manager.

Uses OpenRouter as the primary provider and
Ollama as the local fallback.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


# ============================================================
# Configuration
# ============================================================

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openai/gpt-oss-20b:free",
)

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434/v1",
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:7b",
)


# ============================================================
# Clients
# ============================================================

openrouter_client = None

if OPENROUTER_API_KEY:

    openrouter_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )


ollama_client = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama",
)


# ============================================================
# Provider Call
# ============================================================

def generate_response(
    messages: list[dict],
) -> tuple[str, str]:
    """
    Generate an LLM response.

    OpenRouter is attempted first.

    If OpenRouter fails, Ollama is used as
    the local fallback.

    Returns:
        (response_text, provider_name)
    """

    # --------------------------------------------------------
    # OpenRouter
    # --------------------------------------------------------

    if openrouter_client:

        try:

            response = openrouter_client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=messages,
                temperature=0,
                max_tokens=3000,
            )

            content = response.choices[0].message.content

            if content:

                return content, "openrouter"

        except Exception as exc:

            print(
                f"OpenRouter failed: {exc}"
            )

            print(
                "Switching to local Ollama..."
            )

    # --------------------------------------------------------
    # Ollama fallback
    # --------------------------------------------------------

    try:

        response = ollama_client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=messages,
            temperature=0,
            max_tokens=3000,
        )

        content = response.choices[0].message.content

        if content:

            return content, "ollama"

    except Exception as exc:

        raise RuntimeError(
            "Both OpenRouter and Ollama failed.\n"
            f"Ollama error: {exc}"
        ) from exc

    raise RuntimeError(
        "Both LLM providers returned empty responses."
    )
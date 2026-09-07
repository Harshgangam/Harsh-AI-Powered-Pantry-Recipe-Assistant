"""
src/llm_client.py

Groq LLM client for the Pantry & Recipe Assistant.

Model: llama-3.3-70b-versatile (same as original)
MAX_TOKENS increased to 1024 to allow richer recipe suggestions.
TEMPERATURE slightly raised to 0.3 for friendlier, more natural recipe answers.
"""

import os
from groq import Groq, APIError, APIConnectionError, RateLimitError

MODEL = "qwen/qwen3.8-27b"   # Available on this Groq account
MAX_TOKENS = 1024       # Increased: recipes need more tokens than tech support answers
TEMPERATURE = 0.3       # Slightly higher: friendlier tone for a recipe assistant

_client: Groq | None = None


def get_client() -> Groq:
    """Lazily initialises and returns the Groq client (singleton)."""
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable is not set. "
                "Add it to your .env file."
            )
        _client = Groq(api_key=api_key)
    return _client


def call_llm(messages: list[dict]) -> str:
    """
    Sends a message list to the Groq LLM and returns the response text.

    Parameters
    ----------
    messages : OpenAI-style list of {"role": ..., "content": ...} dicts.

    Returns
    -------
    str — The LLM's response text (stripped).

    Raises
    ------
    RuntimeError with a descriptive code on API failures.
    """
    try:
        client = get_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
        return response.choices[0].message.content.strip()

    except RateLimitError:
        raise RuntimeError("rate_limit")
    except APIConnectionError:
        raise RuntimeError("connection_error")
    except APIError as e:
        raise RuntimeError(f"api_error:{e.status_code}")

"""Wraps LLM API calls (Groq or Anthropic) and extracts Python code blocks.

Features:
- Dual-provider support (Groq / Anthropic) with auto-detection
- Deterministic generation (temperature=0)
- Request timeout (30s)
- Model name tracking for logging
"""

import os
import re

try:
    from dotenv import load_dotenv
    load_dotenv()
except (ImportError, Exception):
    pass

# Try loading from streamlit secrets if in a Streamlit context
try:
    import streamlit as st
    for _k in ("GROQ_API_KEY", "ANTHROPIC_API_KEY", "LLM_PROVIDER", "GROQ_MODEL", "ANTHROPIC_MODEL"):
        if hasattr(st, "secrets") and _k in st.secrets and not os.getenv(_k):
            os.environ[_k] = str(st.secrets[_k])
except Exception:
    pass

from prompts import RETRY_PROMPT, SYSTEM_PROMPT, build_user_message



CODE_BLOCK_PATTERN = re.compile(r"```[a-zA-Z0-9_-]*\s*\n?(.*?)```", re.DOTALL)

DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-20250514"

GROQ_MODEL_FALLBACKS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]

REQUEST_TIMEOUT = 30  # seconds


def extract_code(response_text: str) -> str:
    """Extract Python code from a markdown fenced block or raw response."""
    # Strip reasoning tags (e.g. <think>...</think>, <thought>...</thought>)
    text = re.sub(
        r"<(?:think|thought)>.*?(?:</(?:think|thought)>|(?=```)|$)",
        "",
        response_text,
        flags=re.DOTALL,
    ).strip()
    match = CODE_BLOCK_PATTERN.search(text)
    if match:
        return match.group(1).strip()

    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()

    return text



def _provider() -> str:
    """Detect which LLM provider to use based on env vars."""
    explicit = os.getenv("LLM_PROVIDER", "").lower()
    if explicit in ("groq", "anthropic"):
        return explicit
    if os.getenv("GROQ_API_KEY"):
        return "groq"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    raise EnvironmentError(
        "No API key found. Enter your GROQ_API_KEY in the sidebar or set GROQ_API_KEY in Streamlit Cloud Secrets / .env"
    )


def _default_model(provider: str) -> str:
    """Return the default model for the given provider."""
    if provider == "groq":
        return os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
    return os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)


def _call_groq(system: str, user_content: str, model: str) -> str:
    """Call the Groq API with automatic fallback if a model is deprecated/unavailable."""
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY not set.")

    client = Groq(api_key=api_key, timeout=REQUEST_TIMEOUT)

    # Sequence of models to attempt: requested model first, then known fallbacks
    models_to_try = [model] + [m for m in GROQ_MODEL_FALLBACKS if m != model]
    last_error = None

    for m in models_to_try:
        try:
            response = client.chat.completions.create(
                model=m,
                max_tokens=2048,
                temperature=0,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            err_msg = str(exc).lower()
            if "model_not_found" in err_msg or "does not exist" in err_msg or "404" in err_msg:
                last_error = exc
                continue
            raise exc

    if last_error:
        raise last_error
    return ""


def _call_anthropic(system: str, user_content: str, model: str) -> str:
    """Call the Anthropic Claude API."""
    from anthropic import Anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY not set.")

    client = Anthropic(api_key=api_key, timeout=REQUEST_TIMEOUT)
    message = client.messages.create(
        model=model,
        max_tokens=2048,
        temperature=0,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )
    return message.content[0].text


def generate_code(
    schema: str,
    question: str,
    *,
    error: str | None = None,
    previous_code: str | None = None,
    model: str | None = None,
) -> str:
    """Send schema + question to the configured LLM and return extracted pandas code.

    Returns the extracted Python code string.
    """
    provider = _provider()
    model = model or _default_model(provider)
    system = SYSTEM_PROMPT.format(schema=schema)

    if error and previous_code:
        user_content = RETRY_PROMPT.format(error=error, code=previous_code)
    else:
        user_content = build_user_message(question)

    if provider == "groq":
        response_text = _call_groq(system, user_content, model)
    else:
        response_text = _call_anthropic(system, user_content, model)

    return extract_code(response_text)


def get_model_info() -> dict[str, str]:
    """Return current provider and model name for logging."""
    try:
        provider = _provider()
        model = _default_model(provider)
        return {"provider": provider, "model": model}
    except EnvironmentError:
        return {"provider": "none", "model": "none"}


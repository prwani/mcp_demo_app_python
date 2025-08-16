import os
from typing import Optional, TYPE_CHECKING, Any

try:
    from openai import AzureOpenAI
except Exception:  # pragma: no cover - SDK optional in dev
    AzureOpenAI = None  # type: ignore

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

client: Any = None
if AzureOpenAI and AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY:
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version=AZURE_OPENAI_API_VERSION,
    )

def _use_max_completion_tokens() -> bool:
    """Return True if we should use max_completion_tokens instead of max_tokens.

    Newer Azure OpenAI models/APIs (e.g., gpt-5 with 2025-04-01-preview) reject max_tokens
    in favor of max_completion_tokens. We'll default to max_completion_tokens when either:
      - The deployment name suggests a newer model (e.g., starts with 'gpt-5' or 'o4'), or
      - The API version is the 2025-xx-xx preview.
    """
    model = (AZURE_OPENAI_DEPLOYMENT or "").lower()
    if model.startswith("gpt-5") or model.startswith("o4"):
        return True
    # Simple version check: prefer the new param on 2025 API versions
    return AZURE_OPENAI_API_VERSION.startswith("2025-")


def ask_llm(prompt: str) -> str:
    if not client:
        return "LLM is not configured. Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY."
    # Prefer Responses API for gpt-5/2025 APIs; fall back to Chat Completions otherwise
    prefer_responses = _use_max_completion_tokens()

    if prefer_responses:
        try:
            # Responses API (new) — supports gpt-5 best; uses max_output_tokens
            r = client.responses.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                input=prompt,
                max_output_tokens=200,
            )
            # Try convenience attr first
            if hasattr(r, "output_text") and getattr(r, "output_text"):
                return getattr(r, "output_text")
            # Structured fallback
            out = getattr(r, "output", None) or []
            for item in out:
                for content in getattr(item, "content", []) or []:
                    text = getattr(content, "text", None)
                    if text:
                        return text
        except Exception:
            # Fall through to Chat Completions as a compatibility fallback
            pass

    # Chat Completions path (legacy and compatibility)
    kwargs = {
        "model": AZURE_OPENAI_DEPLOYMENT,
        "messages": [{"role": "user", "content": prompt}],
    }
    if _use_max_completion_tokens():
        kwargs["max_completion_tokens"] = 200
    else:
        kwargs["max_tokens"] = 200
        # Only set temperature for legacy/older models
        kwargs["temperature"] = 0.2

    try:
        resp = client.chat.completions.create(**kwargs)
    except Exception as e:
        msg = str(e)
        # Fallback: swap token param and retry once if unsupported
        if "Unsupported parameter" in msg and "max_tokens" in msg:
            kwargs.pop("max_tokens", None)
            kwargs["max_completion_tokens"] = 200
            resp = client.chat.completions.create(**kwargs)
        elif "Unsupported parameter" in msg and "max_completion_tokens" in msg:
            kwargs.pop("max_completion_tokens", None)
            kwargs["max_tokens"] = 200
            resp = client.chat.completions.create(**kwargs)
        elif ("Unsupported value" in msg or "unsupported_val" in msg) and "temperature" in msg:
            # Remove temperature and retry once
            kwargs.pop("temperature", None)
            resp = client.chat.completions.create(**kwargs)
        else:
            raise
    return resp.choices[0].message.content or ""

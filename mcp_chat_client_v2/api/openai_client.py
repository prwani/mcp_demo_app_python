import os
from typing import Any, Optional, Dict

try:
    from openai import AzureOpenAI
except Exception:  # SDK optional
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

def _use_max_completion_tokens(deployment: Optional[str], api_version: Optional[str]) -> bool:
    model = (deployment or "").lower()
    if model.startswith("gpt-5") or model.startswith("o4"):
        return True
    ver = (api_version or "")
    return ver.startswith("2025-")

def ask_llm(prompt: str) -> str:
    if not client:
        return "LLM is not configured. Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY."
    prefer_responses = _use_max_completion_tokens(AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_VERSION)

    if prefer_responses:
        try:
            r = client.responses.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                input=prompt,
                max_output_tokens=200,
            )
            if hasattr(r, "output_text") and getattr(r, "output_text"):
                return getattr(r, "output_text")
            out = getattr(r, "output", None) or []
            for item in out:
                for content in getattr(item, "content", []) or []:
                    text = getattr(content, "text", None)
                    if text:
                        return text
        except Exception:
            pass

    kwargs = {
        "model": AZURE_OPENAI_DEPLOYMENT,
        "messages": [{"role": "user", "content": prompt}],
    }
    if _use_max_completion_tokens(AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_VERSION):
        kwargs["max_completion_tokens"] = 200
    else:
        kwargs["max_tokens"] = 200
        kwargs["temperature"] = 0.2

    try:
        resp = client.chat.completions.create(**kwargs)
    except Exception as e:
        msg = str(e)
        if "Unsupported parameter" in msg and "max_tokens" in msg:
            kwargs.pop("max_tokens", None)
            kwargs["max_completion_tokens"] = 200
            resp = client.chat.completions.create(**kwargs)
        elif "Unsupported parameter" in msg and "max_completion_tokens" in msg:
            kwargs.pop("max_completion_tokens", None)
            kwargs["max_tokens"] = 200
            resp = client.chat.completions.create(**kwargs)
        elif ("Unsupported value" in msg or "unsupported_val" in msg) and "temperature" in msg:
            kwargs.pop("temperature", None)
            resp = client.chat.completions.create(**kwargs)
        else:
            raise
    return resp.choices[0].message.content or ""


def ask_llm_with_config(prompt: str, cfg: Optional[Dict[str, str]]) -> str:
    """Use a per-request Azure OpenAI configuration if provided; else fallback to default ask_llm."""
    if not cfg:
        return ask_llm(prompt)
    if not AzureOpenAI:
        return "LLM is not configured. Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY."
    endpoint = cfg.get("endpoint")
    key = cfg.get("key")
    api_version = cfg.get("api_version") or AZURE_OPENAI_API_VERSION
    deployment = cfg.get("deployment") or AZURE_OPENAI_DEPLOYMENT
    if not endpoint or not key:
        return ask_llm(prompt)
    temp_client = AzureOpenAI(api_key=key, azure_endpoint=endpoint, api_version=api_version)
    prefer_responses = _use_max_completion_tokens(deployment, api_version)

    if prefer_responses:
        try:
            r = temp_client.responses.create(model=deployment, input=prompt, max_output_tokens=200)
            if hasattr(r, "output_text") and getattr(r, "output_text"):
                return getattr(r, "output_text")
            out = getattr(r, "output", None) or []
            for item in out:
                for content in getattr(item, "content", []) or []:
                    text = getattr(content, "text", None)
                    if text:
                        return text
        except Exception:
            pass
    kwargs = {"model": deployment, "messages": [{"role": "user", "content": prompt}]}
    if _use_max_completion_tokens(deployment, api_version):
        kwargs["max_completion_tokens"] = 200
    else:
        kwargs["max_tokens"] = 200
        kwargs["temperature"] = 0.2
    try:
        resp = temp_client.chat.completions.create(**kwargs)
    except Exception as e:
        msg = str(e)
        if "Unsupported parameter" in msg and "max_tokens" in msg:
            kwargs.pop("max_tokens", None)
            kwargs["max_completion_tokens"] = 200
            resp = temp_client.chat.completions.create(**kwargs)
        elif "Unsupported parameter" in msg and "max_completion_tokens" in msg:
            kwargs.pop("max_completion_tokens", None)
            kwargs["max_tokens"] = 200
            resp = temp_client.chat.completions.create(**kwargs)
        elif ("Unsupported value" in msg or "unsupported_val" in msg) and "temperature" in msg:
            kwargs.pop("temperature", None)
            resp = temp_client.chat.completions.create(**kwargs)
        else:
            raise
    return resp.choices[0].message.content or ""

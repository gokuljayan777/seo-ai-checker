# seo_app/services/analyzer_llm.py
import os
import json
import time
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

# Graceful import / compatibility across openai versions
try:
    # new v1+ package style
    from openai import OpenAI as OpenAIClient
    _OPENAI_NEW = True
except Exception:
    _OPENAI_NEW = False

import openai  # best-effort import (older versions expose functions)

# Load API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    if _OPENAI_NEW:
        # new client will fetch key from env or set below
        client = OpenAIClient(api_key=OPENAI_API_KEY)
    else:
        openai.api_key = OPENAI_API_KEY
        client = None
else:
    client = None
    if not _OPENAI_NEW:
        # leave openai.api_key as-is (maybe set elsewhere)
        pass

MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "20"))
LLM_CACHE_DAYS = int(os.getenv("LLM_CACHE_DAYS", "7"))


def _build_prompt(parsed: Dict[str, Any]) -> str:
    snippet = parsed.get("raw_html_snippet", "")[:2000]
    title = parsed.get("title", "")
    meta = parsed.get("meta_description", "")
    h1s = parsed.get("h1", [])
    h1_text = " | ".join(h1s[:3]) if isinstance(h1s, list) else str(h1s)
    wc = parsed.get("word_count", 0)
    issues = parsed.get("issues", [])
    # Handle both dict format (from crawler) and string format (from analyzer_rules)
    issues_text = "; ".join([
        f"{it.get('code')}: {it.get('message')}" if isinstance(it, dict) else str(it)
        for it in issues
    ]) or "none"

    prompt = f"""
You are an SEO assistant. Given page metadata below, generate a JSON object ONLY (no explanation, no commentary).
The JSON must parse cleanly by `json.loads()` and must contain exactly these keys:
- improved_title (string)
- improved_meta_description (string)
- improved_h1 (string)
- seo_summary (string)
- suggestions (array of strings)

Page context:
TITLE: {title}
META: {meta}
H1: {h1_text}
WORD_COUNT: {wc}
ISSUES: {issues_text}
HTML_SNIPPET: {snippet}

Output example:
{{
  "improved_title": "string",
  "improved_meta_description": "string",
  "improved_h1": "string",
  "seo_summary": "string",
  "suggestions": ["string","string"]
}}

Produce ONLY the JSON object (no markdown, no commentary). Values should be concise and avoid newlines.
"""
    return prompt.strip()


def _extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        cand = text[start:end+1]
        try:
            return json.loads(cand)
        except Exception:
            try:
                return json.loads(cand.replace("'", '"'))
            except Exception:
                return None
    return None


def _call_llm(prompt: str, max_tokens: int = 500, temperature: float = 0.0, timeout: int = LLM_TIMEOUT):
    """
    Unified wrapper that calls either new client (OpenAI()) or old openai.ChatCompletion API.
    Returns the assistant text.
    """
    if _OPENAI_NEW:
        # Use the new OpenAI client
        if client is None:
            raise ValueError("OPENAI_API_KEY not set for OpenAI client")
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful SEO assistant that must output ONLY JSON."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        # new resp structure: resp.choices[0].message.content
        if hasattr(resp, "choices") and len(resp.choices) > 0:
            # In some versions choice objects are dict-like
            first = resp.choices[0]
            # try attribute access
            assistant_text = None
            if hasattr(first, "message") and getattr(first.message, "get", None):
                assistant_text = first.message.get("content")
            elif hasattr(first, "message") and hasattr(first.message, "content"):
                assistant_text = first.message.content
            else:
                # fallback to dict access
                assistant_text = first.get("message", {}).get("content") if isinstance(first, dict) else None
            assistant_text = assistant_text or ""
            return assistant_text
        # fallback
        return str(resp)
    else:
        # Old openai (pre-1.0)
        # openai.ChatCompletion.create(...) returns choices -> message.content or text
        resp = openai.ChatCompletion.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful SEO assistant that must output ONLY JSON."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
        )
        # older packages may return choices[0].message.content or choices[0].text
        if "choices" in resp and len(resp["choices"]) > 0:
            ch = resp["choices"][0]
            if ch.get("message") and ch["message"].get("content"):
                return ch["message"]["content"]
            if ch.get("text"):
                return ch["text"]
        return json.dumps(resp)


def generate_suggestions(parsed: Dict[str, Any], max_retries: int = 1) -> Dict[str, Any]:
    """
    Call the LLM and return a dict:
      { improved_title, improved_meta_description, improved_h1, seo_summary, suggestions }
    """
    # verify API availability
    if _OPENAI_NEW and client is None:
        return {"ok": False, "error": "OPENAI_API_KEY not set in environment"}
    if (not _OPENAI_NEW) and getattr(openai, "api_key", None) is None:
        return {"ok": False, "error": "OPENAI_API_KEY not set in environment"}

    prompt = _build_prompt(parsed)

    for attempt in range(max_retries + 1):
        try:
            assistant_text = _call_llm(prompt, max_tokens=500, temperature=0.0, timeout=LLM_TIMEOUT)
            parsed_json = _extract_json_from_text(assistant_text or "")
            if parsed_json is None:
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                raise ValueError("LLM returned unparsable output", assistant_text)

            required = ["improved_title", "improved_meta_description", "improved_h1", "seo_summary", "suggestions"]
            missing = [k for k in required if k not in parsed_json]
            for k in missing:
                parsed_json[k] = "" if k != "suggestions" else []
            if not isinstance(parsed_json.get("suggestions", []), list):
                parsed_json["suggestions"] = [str(parsed_json.get("suggestions"))]

            return parsed_json

        except Exception as e:
            # If OpenAI API error or parsing error, retry up to max_retries
            if attempt < max_retries:
                time.sleep(1)
                continue
            # return structured failure object instead of raising inside view
            return {"ok": False, "error": str(e)}

    # unreachable
    return {"ok": False, "error": "LLM failure after retries"}

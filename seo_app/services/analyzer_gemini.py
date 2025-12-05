# seo_app/services/analyzer_gemini.py
import os
import json
import time
from typing import Any, Dict, Optional

import google.generativeai as genai

# Load API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "20"))


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


def _call_gemini(prompt: str, max_tokens: int = 500, temperature: float = 0.0):
    """
    Call Google Gemini API.
    Returns the assistant text.
    """
    if GEMINI_API_KEY is None:
        raise ValueError("GEMINI_API_KEY not set in environment")
    
    try:
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )
        return response.text or ""
    except Exception as e:
        raise ValueError(f"Gemini API error: {str(e)}")


def generate_suggestions(parsed: Dict[str, Any], max_retries: int = 1) -> Dict[str, Any]:
    """
    Call Gemini and return a dict:
      { improved_title, improved_meta_description, improved_h1, seo_summary, suggestions }
    """
    if GEMINI_API_KEY is None:
        raise ValueError("GEMINI_API_KEY not set in environment")

    prompt = _build_prompt(parsed)

    for attempt in range(max_retries + 1):
        try:
            assistant_text = _call_gemini(prompt, max_tokens=500, temperature=0.0)
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
            if attempt < max_retries:
                time.sleep(1)
                continue
            return {"ok": False, "error": str(e)}

    return {"ok": False, "error": "LLM failure after retries"}

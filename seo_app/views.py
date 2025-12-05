# seo_app/views.py
import os
import sys
import traceback
from datetime import timedelta

from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .services.crawler import fetch_html, parse_page
from .services.analyzer_rules import run_all_rules

from .models import Page, PageAnalysis

# LLM service - using Gemini (free tier, no credits needed)
try:
    from .services.analyzer_gemini import generate_suggestions
except Exception as e:
    print(f"Warning: Could not import Gemini analyzer: {e}")
    generate_suggestions = None  # safe fallback


@api_view(["GET", "POST"])
def analyze_url(request):
    if request.method == "GET":
        return Response({"message": "API working. Use POST {'url': '...'}"})

    url = request.data.get("url")
    if not url:
        return Response({"error": "URL missing"}, status=status.HTTP_400_BAD_REQUEST)

    # Fetch
    fetch_res = fetch_html(url)
    if not fetch_res["ok"]:
        return Response(
            {
                "error": "Failed to fetch",
                "details": fetch_res["error"],
                "url": fetch_res["url"],
            },
            status=502,
        )

    # Parse
    parsed = parse_page(fetch_res["html"], base_url=fetch_res["url"])

    # Analyze with rules
    score, breakdown, issues = run_all_rules(parsed)
    
    # Add issues to parsed dict for LLM (required by _build_prompt)
    parsed["issues"] = issues

    # Compose base result
    result = {
        "url": fetch_res["url"],
        "status_code": fetch_res["status_code"],
        **parsed,
        "score": score,
        "score_breakdown": breakdown,
        "rule_issues": issues,
    }

    # -------------------------
    # Save Page + PageAnalysis
    # -------------------------
    page, _ = Page.objects.get_or_create(url=fetch_res["url"])
    pa = PageAnalysis.objects.create(
        page=page,
        status_code=fetch_res["status_code"],
        title=parsed.get("title", ""),
        meta_description=parsed.get("meta_description", ""),
        h1=parsed.get("h1", []),
        h2=parsed.get("h2", []),
        h3=parsed.get("h3", []),
        images=parsed.get("images", []),
        word_count=parsed.get("word_count", 0),
        score=score,
        score_breakdown=breakdown,
        rule_issues=issues,
        raw_html_snippet=parsed.get("raw_html_snippet", ""),
    )

    # -------------------------
    # LLM suggestions & caching
    # -------------------------
    # Only attempt LLM generation if generate_suggestions is available
    if generate_suggestions:
        try:
            force_llm = request.GET.get("force_llm", "false").lower() == "true"
            use_cache = False

            # TTL from env or default
            try:
                ttl_days = int(os.getenv("LLM_CACHE_DAYS", "7"))
            except Exception:
                ttl_days = 7

            if pa.llm_suggestions and pa.llm_generated_at and not force_llm:
                age = timezone.now() - pa.llm_generated_at
                if age < timedelta(days=ttl_days):
                    use_cache = True

            if use_cache:
                # reuse cached suggestions
                result["llm_suggestions"] = pa.llm_suggestions or {}
                result["llm_generated_at"] = pa.llm_generated_at
            else:
                # call LLM (may raise); keep it guarded so we don't break response
                try:
                    llm_out = generate_suggestions(parsed)
                    pa.llm_suggestions = llm_out or {}
                    pa.llm_model = os.getenv("LLM_MODEL", "") or pa.llm_model
                    pa.llm_generated_at = timezone.now()
                    pa.save(update_fields=["llm_suggestions", "llm_model", "llm_generated_at"])
                    result["llm_suggestions"] = pa.llm_suggestions
                    result["llm_generated_at"] = pa.llm_generated_at
                except Exception as e:
                    # log the error but don't fail the request
                    print("LLM generation failed:", e, file=sys.stderr)
                    traceback.print_exc()
        except Exception as e:
            # defensive catch-all for any unexpected error in LLM flow
            print("LLM caching flow error:", e, file=sys.stderr)
            traceback.print_exc()

    # Return full result (LLM fields included if available)
    return Response(result)

# seo_app/views/audit_views.py
"""
SEO Audit Views
"""

import os
import sys
import traceback
from datetime import timedelta

from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..services.crawler import fetch_html, parse_page
from ..services.analyzer_rules import run_all_rules
from ..services.analyzer_advanced import run_advanced_rules

from ..models import Page, PageAnalysis, AuditHistory

# LLM service - using Gemini (free tier, no credits needed)
try:
    from ..services.analyzer_gemini import generate_suggestions
except Exception as e:
    print(f"Warning: Could not import Gemini analyzer: {e}")
    generate_suggestions = None  # safe fallback

# Fallback suggestion generator (rule-based, always available)
from ..services.analyzer_suggestions import generate_suggestions_from_issues

# Sitemap crawler for analyzing entire sites
try:
    from ..services.sitemap_crawler import crawl_site_from_sitemap
except Exception as e:
    print(f"Warning: Could not import sitemap crawler: {e}")
    crawl_site_from_sitemap = None


@api_view(["GET", "POST"])
def analyze_url(request):
    if request.method == "GET":
        return Response({"message": "API working. Use POST {'url': '...'} or {'url': '...', 'crawl_site': true}"})

    url = request.data.get("url")
    crawl_site = request.data.get("crawl_site", False)
    
    if not url:
        return Response({"error": "URL missing"}, status=status.HTTP_400_BAD_REQUEST)

    # If crawl_site is True, use sitemap crawler
    if crawl_site and crawl_site_from_sitemap:
        try:
            # Allow forcing LLM suggestions during site crawl
            force_llm = (request.GET.get("force_llm", "false").lower() == "true") or bool(request.data.get("force_llm", False))
            result = crawl_site_from_sitemap(url, max_pages=500, force_llm=force_llm)
            return Response(result)
        except Exception as e:
            print(f"Sitemap crawl failed: {e}", file=sys.stderr)
            traceback.print_exc()
            return Response(
                {"error": "Sitemap crawl failed", "details": str(e)},
                status=502,
            )

    # Single page analysis (original flow)
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

    # Analyze with basic rules
    score, breakdown, issues = run_all_rules(parsed)
    
    # Analyze with advanced rules (Core Web Vitals, Mobile, Schema, Security, etc.)
    advanced_score, advanced_breakdown, advanced_issues = run_advanced_rules(
        parsed, 
        html=fetch_res["html"], 
        base_url=fetch_res["url"]
    )
    
    # Combine scores: basic rules (40%) + advanced rules (60%)
    combined_score = int((score * 0.4) + (advanced_score * 0.6))
    
    # Combine all issues
    all_issues = issues + advanced_issues
    
    # Add issues to parsed dict for LLM (required by _build_prompt)
    parsed["issues"] = all_issues

    # Transform issues from flat strings to array of objects for frontend
    # Expected format: [{"code": "issue_slug", "message": "issue text"}, ...]
    formatted_issues = [
        {
            "code": issue.lower().replace(" ", "_").replace("(", "").replace(")", ""),
            "message": issue
        }
        for issue in all_issues
    ]
    
    # Categorize issues by severity
    critical_issues = []
    warning_issues = []
    info_issues = []
    
    critical_keywords = ["missing", "no h1", "noindex", "ssl", "https"]
    warning_keywords = ["short", "long", "multiple", "thin", "broken"]
    
    for issue in formatted_issues:
        msg_lower = issue["message"].lower()
        if any(kw in msg_lower for kw in critical_keywords):
            critical_issues.append(issue)
        elif any(kw in msg_lower for kw in warning_keywords):
            warning_issues.append(issue)
        else:
            info_issues.append(issue)

    # Compose comprehensive audit report
    audit_report = {
        "total_issues": len(formatted_issues),
        "critical_count": len(critical_issues),
        "warnings_count": len(warning_issues),
        "info_count": len(info_issues),
        "critical": critical_issues[:10],  # Top 10
        "warnings": warning_issues[:10],
        "info": info_issues[:10],
    }

    # Compose base result
    result = {
        "url": fetch_res["url"],
        "status_code": fetch_res["status_code"],
        **parsed,
        "score": combined_score,
        "basic_score": score,
        "advanced_score": advanced_score,
        "score_breakdown": breakdown,
        "advanced_breakdown": advanced_breakdown,
        "audit_report": audit_report,
        "rule_issues": all_issues,
        "issues": formatted_issues,  # use formatted version for frontend
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
        score=combined_score,
        score_breakdown=breakdown + advanced_breakdown,  # Combined breakdowns
        rule_issues=all_issues,
        raw_html_snippet=parsed.get("raw_html_snippet", ""),
    )
    
    # Save audit history for trend tracking
    try:
        AuditHistory.objects.create(
            page=page,
            score=combined_score,
            issues_count=len(formatted_issues),
            critical_issues=len(critical_issues),
        )
    except Exception as e:
        print(f"Failed to save audit history: {e}", file=sys.stderr)

    # -------------------------
    # LLM suggestions & caching
    # -------------------------
    # Try to get LLM suggestions from Gemini, fall back to rule-based suggestions
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
            # Try LLM first (Gemini)
            llm_out = None
            if generate_suggestions:
                try:
                    llm_out = generate_suggestions(parsed)
                    # Check if it's an error response
                    if llm_out and llm_out.get("ok") is False:
                        llm_out = None  # Fall back to rule-based
                except Exception as e:
                    # log the error but don't fail; use fallback
                    print("LLM generation failed:", e, file=sys.stderr)
                    llm_out = None
            
            # Use fallback if LLM unavailable or failed
            if llm_out is None:
                llm_out = generate_suggestions_from_issues(parsed)
                result["llm_suggestions"] = {**llm_out, "fallback": True}
            else:
                result["llm_suggestions"] = llm_out or {}
            
            # Save to database
            pa.llm_suggestions = result["llm_suggestions"]
            pa.llm_model = os.getenv("LLM_MODEL", "fallback-rule-based")
            pa.llm_generated_at = timezone.now()
            pa.save(update_fields=["llm_suggestions", "llm_model", "llm_generated_at"])
            result["llm_generated_at"] = pa.llm_generated_at
    except Exception as e:
        # defensive catch-all for any unexpected error in suggestions flow
        print("Suggestions generation error:", e, file=sys.stderr)
        traceback.print_exc()
        # Provide fallback even on error
        result["llm_suggestions"] = generate_suggestions_from_issues(parsed)

    return Response(result)

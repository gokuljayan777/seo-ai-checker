# seo_app/views/keyword_views.py
"""
Keyword Research API Views
"""

import logging
from datetime import datetime

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import Domain, Keyword, KeywordRanking
from ..services.keyword_research import (
    compare_keywords,
    get_keyword_recommendations,
    search_keywords,
)

logger = logging.getLogger(__name__)


@api_view(["POST"])
def keyword_search(request):
    """
    Search for keywords with volume, difficulty, intent analysis.

    POST /api/keywords/search/
    {
        "keyword": "best seo tools",
        "limit": 10  (optional)
    }
    """
    try:
        keyword = request.data.get("keyword", "").strip()
        limit = request.data.get("limit", 10)

        if not keyword:
            return Response(
                {"error": "Keyword is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        if len(keyword) > 500:
            return Response(
                {"error": "Keyword too long (max 500 chars)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get keyword research data
        result = search_keywords(keyword, limit=limit)

        # Store in database for tracking
        try:
            kw_obj, _ = Keyword.objects.get_or_create(
                keyword=keyword,
                defaults={
                    "search_volume": result.get("search_volume", 0),
                    "keyword_difficulty": result.get("keyword_difficulty", 0),
                    "cpc": result.get("cpc", 0.0),
                    "intent": result.get("intent", "informational"),
                    "trend_score": result.get("trend_score", []),
                },
            )
        except Exception as e:
            logger.warning(f"Could not save keyword to database: {e}")

        return Response({"ok": True, "data": result})

    except Exception as e:
        logger.error(f"Keyword search error: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def keyword_difficulty(request):
    """
    Get keyword difficulty analysis.

    POST /api/keywords/difficulty/
    {
        "keyword": "best seo tools"
    }
    """
    try:
        keyword = request.data.get("keyword", "").strip()

        if not keyword:
            return Response(
                {"error": "Keyword is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        result = search_keywords(keyword)

        return Response(
            {
                "ok": True,
                "keyword": keyword,
                "difficulty": result.get("keyword_difficulty", 0),
                "difficulty_level": result.get("competition", "Medium"),
                "search_volume": result.get("search_volume", 0),
                "ranking_difficulty": "This keyword is "
                + result.get("competition", "Medium").lower()
                + " competition",
            }
        )

    except Exception as e:
        logger.error(f"Difficulty analysis error: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def keyword_related(request):
    """
    Get related keywords and variations.

    POST /api/keywords/related/
    {
        "keyword": "best seo tools",
        "limit": 10  (optional)
    }
    """
    try:
        keyword = request.data.get("keyword", "").strip()
        limit = request.data.get("limit", 10)

        if not keyword:
            return Response(
                {"error": "Keyword is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        result = search_keywords(keyword, limit=limit)

        return Response(
            {
                "ok": True,
                "primary_keyword": keyword,
                "related_keywords": result.get("related_keywords", []),
                "intent": result.get("intent", "informational"),
                "difficulty": result.get("keyword_difficulty", 0),
            }
        )

    except Exception as e:
        logger.error(f"Related keywords error: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def keyword_compare(request):
    """
    Compare multiple keywords.

    POST /api/keywords/compare/
    {
        "keywords": ["seo tools", "best seo tools", "free seo tools"]
    }
    """
    try:
        keywords = request.data.get("keywords", [])

        if not keywords or len(keywords) == 0:
            return Response(
                {"error": "At least one keyword is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(keywords) > 10:
            return Response(
                {"error": "Maximum 10 keywords for comparison"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = compare_keywords(keywords)

        return Response({"ok": True, "comparison": result})

    except Exception as e:
        logger.error(f"Keyword comparison error: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def keyword_recommendations(request):
    """
    Get keyword recommendations for a domain.

    POST /api/keywords/recommendations/
    {
        "domain": "example.com",
        "industry": "saas"  (optional: saas, ecommerce, services, content, tech)
    }
    """
    try:
        domain = request.data.get("domain", "").strip()
        industry = request.data.get("industry", "")

        if not domain:
            return Response(
                {"error": "Domain is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        recommendations = get_keyword_recommendations(domain, industry)

        return Response(
            {
                "ok": True,
                "domain": domain,
                "industry": industry,
                "recommendations": recommendations,
            }
        )

    except Exception as e:
        logger.error(f"Keyword recommendations error: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET", "POST"])
def keyword_trends(request):
    """
    Get keyword trends and historical data.

    GET /api/keywords/trends/?keyword=seo+tools
    """
    try:
        keyword = request.GET.get("keyword") or request.data.get("keyword")

        if not keyword:
            return Response(
                {"error": "Keyword is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        result = search_keywords(keyword)

        return Response(
            {
                "ok": True,
                "keyword": keyword,
                "trend_score": result.get("trend_score", []),
                "search_volume": result.get("search_volume", 0),
                "difficulty": result.get("keyword_difficulty", 0),
                "months": [
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                ],
            }
        )

    except Exception as e:
        logger.error(f"Keyword trends error: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def track_keyword_ranking(request):
    """
    Track keyword ranking for a domain.

    POST /api/keywords/track-ranking/
    {
        "domain": "example.com",
        "keyword": "best seo tools",
        "position": 1
    }
    """
    try:
        domain_str = request.data.get("domain", "").strip()
        keyword_str = request.data.get("keyword", "").strip()
        position = request.data.get("position", 0)

        if not domain_str or not keyword_str:
            return Response(
                {"error": "Domain and keyword are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get or create domain
        domain, _ = Domain.objects.get_or_create(domain=domain_str)

        # Get or create keyword
        kw, _ = Keyword.objects.get_or_create(keyword=keyword_str)

        # Create ranking record
        ranking, created = KeywordRanking.objects.get_or_create(
            domain=domain,
            keyword=kw,
            recorded_date__date=datetime.now().date(),
            defaults={
                "position": position,
                "url": request.data.get("url", ""),
                "search_volume": kw.search_volume,
            },
        )

        if not created:
            ranking.position = position
            ranking.save()

        return Response(
            {
                "ok": True,
                "message": "Ranking tracked successfully",
                "domain": domain_str,
                "keyword": keyword_str,
                "position": position,
            }
        )

    except Exception as e:
        logger.error(f"Ranking tracking error: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def keyword_list(request):
    """
    Get all tracked keywords.

    GET /api/keywords/list/?limit=20
    """
    try:
        limit = int(request.GET.get("limit", 20))

        keywords = Keyword.objects.all().order_by("-search_volume")[:limit]

        data = [
            {
                "id": kw.id,
                "keyword": kw.keyword,
                "search_volume": kw.search_volume,
                "difficulty": kw.keyword_difficulty,
                "intent": kw.intent,
                "cpc": kw.cpc,
            }
            for kw in keywords
        ]

        return Response({"ok": True, "count": len(data), "keywords": data})

    except Exception as e:
        logger.error(f"Keyword list error: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

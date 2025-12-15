# seo_app/views/competitor_views.py
"""
Competitor Analysis API Endpoints
- Analyze individual competitors
- Compare multiple competitors
- Track SERP positions
- Analyze content and strategies
"""

import logging

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from seo_app.models import Competitor, Domain
from seo_app.services.competitor_analysis import CompetitorAnalyzer

logger = logging.getLogger(__name__)
analyzer = CompetitorAnalyzer()


@api_view(["POST"])
def analyze_competitor(request):
    """
    Analyze a competitor domain.

    POST /api/competitors/analyze/
    Body: {"domain": "example.com"}
    """
    try:
        domain = request.data.get("domain", "").strip()

        if not domain:
            return Response(
                {"error": "domain field is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Normalize domain
        if not domain.startswith(("http://", "https://")):
            domain = domain.lower()

        analysis = analyzer.analyze_competitor(domain)

        # Save to database
        try:
            domain_obj, _ = Domain.objects.get_or_create(name=domain)
            comp, _ = Competitor.objects.get_or_create(
                domain=domain_obj,
                defaults={
                    "estimated_traffic": analysis.get("estimated_monthly_traffic", 0),
                    "estimated_backlinks": analysis.get("estimated_backlinks", 0),
                    "domain_authority": analysis.get("domain_authority", 0),
                },
            )
        except Exception as db_error:
            logger.warning(f"Could not save competitor to DB: {db_error}")

        return Response({"ok": True, "data": analysis})

    except Exception as e:
        logger.error(f"Error in analyze_competitor: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def compare_competitors(request):
    """
    Compare multiple competitors side-by-side.

    POST /api/competitors/compare/
    Body: {"domains": ["example1.com", "example2.com", "example3.com"]}
    """
    try:
        domains = request.data.get("domains", [])

        if not domains or not isinstance(domains, list):
            return Response(
                {"error": "domains must be a list of domain names"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Limit to 10 domains
        domains = domains[:10]

        comparison = analyzer.compare_competitors(domains)

        return Response({"ok": True, "comparison": comparison})

    except Exception as e:
        logger.error(f"Error in compare_competitors: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def get_competitor_strategies(request):
    """
    Get strategic insights about a competitor.

    POST /api/competitors/strategies/
    Body: {"domain": "example.com"}
    """
    try:
        domain = request.data.get("domain", "").strip()

        if not domain:
            return Response(
                {"error": "domain field is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        strategies = analyzer.get_competitor_strategies(domain)

        return Response({"ok": True, "data": strategies})

    except Exception as e:
        logger.error(f"Error in get_competitor_strategies: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def track_serp_positions(request):
    """
    Track competitor's SERP positions for given keywords.

    POST /api/competitors/track-serp/
    Body: {"domain": "example.com", "keywords": ["keyword1", "keyword2"]}
    """
    try:
        domain = request.data.get("domain", "").strip()
        keywords = request.data.get("keywords", [])

        if not domain:
            return Response(
                {"error": "domain field is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not keywords or not isinstance(keywords, list):
            return Response(
                {"error": "keywords must be a list"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Limit to 20 keywords
        keywords = keywords[:20]

        positions = analyzer.track_serp_positions(domain, keywords)

        return Response({"ok": True, "data": positions})

    except Exception as e:
        logger.error(f"Error in track_serp_positions: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def analyze_competitor_content(request):
    """
    Analyze competitor's content quality and strategy.

    POST /api/competitors/analyze-content/
    Body: {"domain": "example.com"}
    """
    try:
        domain = request.data.get("domain", "").strip()

        if not domain:
            return Response(
                {"error": "domain field is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        content_analysis = analyzer.analyze_competitor_content(domain)

        return Response({"ok": True, "data": content_analysis})

    except Exception as e:
        logger.error(f"Error in analyze_competitor_content: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET", "POST"])
def list_competitors(request):
    """
    List all tracked competitors or get competitor by domain.

    GET /api/competitors/list/
    POST /api/competitors/list/
    Body: {"domain": "example.com"} (optional - filter by domain)
    """
    try:
        if request.method == "POST":
            domain = request.data.get("domain")
            competitors = Competitor.objects.filter(domain__name=domain)
        else:
            competitors = Competitor.objects.all()[:50]

        data = [
            {
                "domain": c.domain.name,
                "estimated_traffic": c.estimated_traffic,
                "estimated_backlinks": c.estimated_backlinks,
                "domain_authority": c.domain_authority,
                "tracked_since": (
                    c.created_at.isoformat() if hasattr(c, "created_at") else None
                ),
            }
            for c in competitors
        ]

        return Response({"ok": True, "count": len(data), "competitors": data})

    except Exception as e:
        logger.error(f"Error in list_competitors: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# seo_app/views/backlink_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from seo_app.services.backlink_analysis import BacklinkAnalyzer
import logging

logger = logging.getLogger(__name__)
backlink = BacklinkAnalyzer()


@api_view(['POST'])
def analyze_backlinks(request):
    """POST /api/backlinks/analyze/  Body: {"domain": "example.com"}"""
    try:
        domain = request.data.get('domain', '').strip()
        if not domain:
            return Response({'error': 'domain is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = backlink.analyze_domain(domain)
        return Response({'ok': True, 'data': result})
    except Exception as e:
        logger.error(f"Error in analyze_backlinks: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def top_referrers(request):
    """POST /api/backlinks/top-referrers/ Body: {"domain": "example.com", "limit": 10}"""
    try:
        domain = request.data.get('domain', '').strip()
        limit = int(request.data.get('limit', 10))
        if not domain:
            return Response({'error': 'domain is required'}, status=status.HTTP_400_BAD_REQUEST)
        data = backlink._top_referrers(domain, limit=limit)
        return Response({'ok': True, 'top_referrers': data})
    except Exception as e:
        logger.error(f"Error in top_referrers: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def anchor_texts(request):
    """POST /api/backlinks/anchor-texts/ Body: {"domain": "example.com", "limit": 10}"""
    try:
        domain = request.data.get('domain', '').strip()
        limit = int(request.data.get('limit', 10))
        if not domain:
            return Response({'error': 'domain is required'}, status=status.HTTP_400_BAD_REQUEST)
        data = backlink._anchor_texts(domain, limit=limit)
        return Response({'ok': True, 'anchor_texts': data})
    except Exception as e:
        logger.error(f"Error in anchor_texts: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def link_gap(request):
    """POST /api/backlinks/link-gap/ Body: {"source": "example.com", "target": "competitor.com"}"""
    try:
        source = request.data.get('source', '').strip()
        target = request.data.get('target', '').strip()
        if not source or not target:
            return Response({'error': 'source and target are required'}, status=status.HTTP_400_BAD_REQUEST)
        data = backlink.compare_link_gap(source, target)
        return Response({'ok': True, 'data': data})
    except Exception as e:
        logger.error(f"Error in link_gap: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def backlink_growth(request):
    """POST /api/backlinks/growth/ Body: {"domain": "example.com"}"""
    try:
        domain = request.data.get('domain', '').strip()
        if not domain:
            return Response({'error': 'domain is required'}, status=status.HTTP_400_BAD_REQUEST)
        data = backlink._estimate_backlink_growth(domain)
        return Response({'ok': True, 'growth': data})
    except Exception as e:
        logger.error(f"Error in backlink_growth: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def backlink_audit(request):
    """POST /api/backlinks/audit/ Body: {"domain": "example.com"}"""
    try:
        domain = request.data.get('domain', '').strip()
        if not domain:
            return Response({'error': 'domain is required'}, status=status.HTTP_400_BAD_REQUEST)
        analysis = backlink.analyze_domain(domain)
        audit = {
            'domain': domain,
            'toxic_score': analysis.get('toxic_score', 0),
            'warnings': [] if analysis.get('toxic_score', 0) < 50 else ['High toxic backlink score detected'],
        }
        return Response({'ok': True, 'audit': audit})
    except Exception as e:
        logger.error(f"Error in backlink_audit: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

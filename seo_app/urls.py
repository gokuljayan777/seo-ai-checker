from django.urls import path
from .views import (
    analyze_url,
    keyword_search,
    keyword_difficulty,
    keyword_related,
    keyword_compare,
    keyword_recommendations,
    keyword_trends,
    track_keyword_ranking,
    keyword_list,
    analyze_competitor,
    compare_competitors,
    get_competitor_strategies,
    track_serp_positions,
    analyze_competitor_content,
    list_competitors,
    analyze_backlinks,
    top_referrers,
    anchor_texts,
    link_gap,
    backlink_growth,
    backlink_audit,
)

urlpatterns = [
    # Original SEO Audit endpoints
    path('analyze/', analyze_url),
    
    # Keyword Research endpoints (Phase 3)
    path('keywords/search/', keyword_search, name='keyword_search'),
    path('keywords/difficulty/', keyword_difficulty, name='keyword_difficulty'),
    path('keywords/related/', keyword_related, name='keyword_related'),
    path('keywords/compare/', keyword_compare, name='keyword_compare'),
    path('keywords/recommendations/', keyword_recommendations, name='keyword_recommendations'),
    path('keywords/trends/', keyword_trends, name='keyword_trends'),
    path('keywords/track-ranking/', track_keyword_ranking, name='track_keyword_ranking'),
    path('keywords/list/', keyword_list, name='keyword_list'),
    
    # Competitor Analysis endpoints (Phase 4)
    path('competitors/analyze/', analyze_competitor, name='analyze_competitor'),
    path('competitors/compare/', compare_competitors, name='compare_competitors'),
    path('competitors/strategies/', get_competitor_strategies, name='competitor_strategies'),
    path('competitors/track-serp/', track_serp_positions, name='track_serp_positions'),
    path('competitors/analyze-content/', analyze_competitor_content, name='analyze_competitor_content'),
    path('competitors/list/', list_competitors, name='list_competitors'),
    # Backlink Analysis endpoints (Phase 5)
    path('backlinks/analyze/', analyze_backlinks, name='backlink_analyze'),
    path('backlinks/top-referrers/', top_referrers, name='backlink_top_referrers'),
    path('backlinks/anchor-texts/', anchor_texts, name='backlink_anchor_texts'),
    path('backlinks/link-gap/', link_gap, name='backlink_link_gap'),
    path('backlinks/growth/', backlink_growth, name='backlink_growth'),
    path('backlinks/audit/', backlink_audit, name='backlink_audit'),
]

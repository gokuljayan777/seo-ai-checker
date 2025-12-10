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
]

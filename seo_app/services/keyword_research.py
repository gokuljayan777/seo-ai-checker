# seo_app/services/keyword_research.py
"""
Keyword Research Service
- Search volume estimation
- Keyword difficulty calculation
- Search intent classification
- Related keywords generation
- Trend analysis
"""

import logging
import os
from typing import Dict, List

import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Configuration
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")  # Free tier available
GOOGLE_TRENDS_ENABLED = True  # Built-in analysis
CACHE_DURATION = 86400 * 7  # Cache for 7 days


class KeywordResearcher:
    """Main keyword research class"""

    def __init__(self):
        self.serpapi_key = SERPAPI_KEY

    def search_keywords(self, keyword: str, limit: int = 10) -> Dict:
        """
        Search for keyword and related keywords.
        Returns search volume, difficulty, intent, and related terms.
        """
        try:
            # Check cache first
            cache_key = f"keyword_search:{keyword}"
            cached = cache.get(cache_key)
            if cached:
                return cached

            result = {
                "keyword": keyword,
                "search_volume": self._estimate_search_volume(keyword),
                "keyword_difficulty": self._calculate_keyword_difficulty(keyword),
                "intent": self._classify_search_intent(keyword),
                "related_keywords": self._get_related_keywords(keyword, limit),
                "cpc": self._estimate_cpc(keyword),
                "competition": self._estimate_competition(keyword),
                "trend_score": self._get_trend_score(keyword),
            }

            # Cache the result
            cache.set(cache_key, result, CACHE_DURATION)
            return result

        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return {
                "error": str(e),
                "keyword": keyword,
            }

    def _estimate_search_volume(self, keyword: str) -> int:
        """
        Estimate search volume for a keyword.
        Uses heuristics: longer keywords = lower volume, branded = higher volume
        """
        try:
            # Try SerpAPI if available
            if self.serpapi_key:
                return self._serpapi_search_volume(keyword)

            # Fallback: heuristic-based estimation
            return self._heuristic_search_volume(keyword)

        except Exception as e:
            logger.warning(f"Could not estimate search volume: {e}")
            return self._heuristic_search_volume(keyword)

    def _serpapi_search_volume(self, keyword: str) -> int:
        """Get search volume from SerpAPI (requires API key)"""
        try:
            url = "https://serpapi.com/search"
            params = {
                "q": keyword,
                "api_key": self.serpapi_key,
                "engine": "google",
            }
            response = requests.get(url, params=params, timeout=5)
            data = response.json()

            # Extract search volume from response
            if "search_information" in data:
                volume_str = data["search_information"].get("total_results", "0")
                try:
                    # Parse number like "1,230,000" to 1230000
                    volume = int(volume_str.replace(",", ""))
                    return volume
                except Exception:
                    return int(volume_str) if volume_str.isdigit() else 0

            return 0
        except Exception as e:
            logger.error(f"SerpAPI error: {e}")
            raise

        def _serpapi_search_volume(self, keyword: str) -> int:
            """Get search volume from SerpAPI (requires API key)"""
            try:
                url = "https://serpapi.com/search"
                params = {
                    "q": keyword,
                    "api_key": self.serpapi_key,
                    "engine": "google",
                }
                response = requests.get(url, params=params, timeout=10)
                data = response.json()

                logger.info(f"SerpAPI response keys: {list(data.keys())}")

                # Check for errors in response
                if "error" in data:
                    logger.warning(f"SerpAPI error: {data['error']}")
                    return self._heuristic_search_volume(keyword)

                # Extract search volume from response
                if "search_information" in data:
                    volume_str = data["search_information"].get("total_results", "0")
                    try:
                        # Parse number like "1,230,000" to 1230000
                        volume = int(volume_str.replace(",", ""))
                        logger.info(f"SerpAPI found volume for '{keyword}': {volume}")
                        return volume
                    except Exception as parse_error:
                        logger.warning(f"Could not parse volume: {parse_error}")
                        return self._heuristic_search_volume(keyword)

                # No search_information found, fallback to heuristic
                logger.info(
                    f"No search_information in SerpAPI response for '{keyword}', using heuristic"
                )
                return self._heuristic_search_volume(keyword)
            except Exception as e:
                logger.error(f"SerpAPI error: {e}, falling back to heuristic")
                return self._heuristic_search_volume(keyword)

    def _heuristic_search_volume(self, keyword: str) -> int:
        """
        Estimate search volume using heuristics.
        Based on keyword length, type, and common patterns.
        """
        keyword_lower = keyword.lower()

        # Base scores for different keyword types
        if any(
            word in keyword_lower for word in ["how to", "what is", "best", "guide"]
        ):
            base_volume = 5000  # Informational keywords
        elif any(word in keyword_lower for word in ["buy", "shop", "price", "cost"]):
            base_volume = 8000  # Commercial keywords
        elif any(word in keyword_lower for word in ["near me", "local", "in", "near"]):
            base_volume = 3000  # Local keywords
        else:
            base_volume = 4000  # Generic keywords

        # Adjust by keyword length
        word_count = len(keyword.split())
        if word_count == 1:
            base_volume *= 2.5  # Single word keywords are usually higher volume
        elif word_count == 2:
            base_volume *= 1.8
        elif word_count >= 4:
            base_volume *= 0.6  # Long-tail keywords are lower volume

        # Add some randomness based on keyword specificity
        if len(keyword) > 20:
            base_volume *= 0.7

        return max(100, int(base_volume))

    def _calculate_keyword_difficulty(self, keyword: str) -> int:
        """
        Calculate keyword difficulty (0-100).
        Higher = harder to rank.
        Based on keyword length, type, and competition indicators.
        """
        keyword_lower = keyword.lower()
        difficulty = 50  # Base difficulty

        # Single word keywords are harder
        word_count = len(keyword.split())
        if word_count == 1:
            difficulty += 20
        elif word_count >= 4:
            difficulty -= 15

        # Brand keywords usually have high difficulty
        if any(
            word in keyword_lower
            for word in ["amazon", "ebay", "apple", "google", "facebook"]
        ):
            difficulty += 25

        # How-to and guides are easier
        if any(word in keyword_lower for word in ["how to", "guide", "tutorial"]):
            difficulty -= 10

        # Long-tail usually easier
        if len(keyword) > 30:
            difficulty -= 5

        # Transactional keywords harder
        if any(word in keyword_lower for word in ["buy", "cheap", "best price"]):
            difficulty += 10

        # Local keywords easier
        if any(word in keyword_lower for word in ["near me", "in ", "local"]):
            difficulty -= 15

        return max(0, min(100, difficulty))

    def _classify_search_intent(self, keyword: str) -> str:
        """
        Classify search intent: informational, commercial, transactional, navigational.
        """
        keyword_lower = keyword.lower()

        # Transactional intent
        transactional_words = [
            "buy",
            "shop",
            "order",
            "price",
            "cost",
            "cheap",
            "deal",
            "discount",
            "coupon",
        ]
        if any(word in keyword_lower for word in transactional_words):
            return "transactional"

        # Navigational intent
        navigational_words = ["login", "account", "official", "website", "app"]
        if any(word in keyword_lower for word in navigational_words):
            return "navigational"

        # Commercial intent
        commercial_words = ["best", "top", "review", "comparison", "vs", "alternative"]
        if any(word in keyword_lower for word in commercial_words):
            return "commercial"

        # Default: Informational
        return "informational"

    def _get_related_keywords(self, keyword: str, limit: int = 10) -> List[str]:
        """
        Generate related keywords.
        Combines question-based, modifier-based, and long-tail variations.
        """
        related = []
        base_keyword = keyword.strip()

        # Question-based variations
        questions = [
            f"what is {base_keyword}",
            f"how to {base_keyword}",
            f"best {base_keyword}",
            f"{base_keyword} guide",
            f"{base_keyword} tips",
            f"{base_keyword} tutorial",
            f"{base_keyword} tools",
            f"{base_keyword} vs",
        ]
        related.extend([q for q in questions if len(q) < 100])

        # Long-tail variations
        long_tails = [
            f"{base_keyword} for beginners",
            f"{base_keyword} step by step",
            f"{base_keyword} made easy",
            f"free {base_keyword}",
            f"{base_keyword} 2025",
        ]
        related.extend([lt for lt in long_tails if len(lt) < 100])

        # Remove duplicates and limit
        related = list(dict.fromkeys(related))[:limit]

        return related

    def _estimate_cpc(self, keyword: str) -> float:
        """
        Estimate CPC (Cost Per Click) for the keyword.
        Based on keyword type and difficulty.
        """
        keyword_lower = keyword.lower()

        # Base CPC by type
        if any(
            word in keyword_lower
            for word in ["insurance", "lawyer", "mortgage", "loan"]
        ):
            return round(5.0 + (self._calculate_keyword_difficulty(keyword) * 0.1), 2)
        elif any(word in keyword_lower for word in ["software", "app", "tool"]):
            return round(2.5 + (self._calculate_keyword_difficulty(keyword) * 0.05), 2)
        elif any(word in keyword_lower for word in ["health", "medical", "doctor"]):
            return round(2.0 + (self._calculate_keyword_difficulty(keyword) * 0.08), 2)
        elif any(word in keyword_lower for word in ["buy", "shop", "order"]):
            return round(1.5 + (self._calculate_keyword_difficulty(keyword) * 0.03), 2)
        else:
            return round(0.5 + (self._calculate_keyword_difficulty(keyword) * 0.01), 2)

    def _estimate_competition(self, keyword: str) -> str:
        """
        Estimate competition level: Low, Medium, High.
        """
        difficulty = self._calculate_keyword_difficulty(keyword)

        if difficulty < 30:
            return "Low"
        elif difficulty < 60:
            return "Medium"
        else:
            return "High"

    def _get_trend_score(self, keyword: str) -> List[int]:
        """
        Get trend score over last 12 months (simplified).
        Returns list of 12 monthly scores.
        """
        # Simplified trend calculation
        base_score = 50
        trend = []

        for i in range(12):
            # Add some variation to simulate trends
            month_score = max(0, min(100, base_score + (i % 3 - 1) * 10))
            trend.append(month_score)

        return trend

    def get_keyword_comparison(self, keywords: List[str]) -> Dict:
        """
        Compare multiple keywords side-by-side.
        """
        try:
            comparison = {"keywords": keywords, "data": []}

            for keyword in keywords:
                kw_data = self.search_keywords(keyword)
                comparison["data"].append(kw_data)

            return comparison

        except Exception as e:
            logger.error(f"Error comparing keywords: {e}")
            return {"error": str(e)}

    def get_keyword_recommendations(
        self, domain: str, industry: str = ""
    ) -> List[Dict]:
        """
        Get keyword recommendations for a domain based on industry.
        """
        recommendations = []

        # Common high-value keywords by industry
        industry_keywords = {
            "saas": [
                "saas for",
                "best saas",
                "saas solutions",
                "saas tools",
                "saas platform",
            ],
            "ecommerce": [
                "buy online",
                "shop",
                "best price",
                "online store",
                "free shipping",
            ],
            "services": [
                "services near me",
                "best services",
                "affordable services",
                "local services",
            ],
            "content": ["blog", "guide", "tutorial", "how to", "tips and tricks"],
            "tech": ["best tech", "tech review", "tech news", "gadgets"],
        }

        # Get recommendations for the industry
        keywords_to_check = industry_keywords.get(
            industry.lower(), ["best", "how to", "guide", "tips", "review"]
        )

        for base_kw in keywords_to_check[:5]:
            full_kw = f"{base_kw} {domain.replace('.com', '').replace('www.', '')}"
            kw_data = self.search_keywords(full_kw)
            recommendations.append(kw_data)

        return recommendations


# Global instance
researcher = KeywordResearcher()


def search_keywords(keyword: str, limit: int = 10) -> Dict:
    """Public API function"""
    return researcher.search_keywords(keyword, limit)


def compare_keywords(keywords: List[str]) -> Dict:
    """Compare multiple keywords"""
    return researcher.get_keyword_comparison(keywords)


def get_keyword_recommendations(domain: str, industry: str = "") -> List[Dict]:
    """Get keyword recommendations"""

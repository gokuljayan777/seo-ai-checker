from django.test import TestCase

from seo_app.services.competitor_analysis import CompetitorAnalyzer


class CompetitorAnalysisTests(TestCase):
    def setUp(self):
        self.ca = CompetitorAnalyzer()

    def test_estimate_traffic_deterministic_and_positive(self):
        t1 = self.ca._estimate_traffic("example.com")
        t2 = self.ca._estimate_traffic("example.com")
        self.assertIsInstance(t1, int)
        self.assertGreater(t1, 0)
        self.assertEqual(t1, t2)

    def test_estimate_backlinks_positive_and_int(self):
        b = self.ca._estimate_backlinks("example.com")
        self.assertIsInstance(b, int)
        self.assertGreaterEqual(b, 50)

    def test_estimate_domain_authority_range(self):
        auth = self.ca._estimate_domain_authority("example.com")
        self.assertIsInstance(auth, int)
        self.assertGreaterEqual(auth, 1)
        self.assertLessEqual(auth, 100)

    def test_get_serp_position_consistent_and_in_range(self):
        p1 = self.ca._get_serp_position("example.com", "best tools")
        p2 = self.ca._get_serp_position("example.com", "best tools")
        self.assertEqual(p1["position"], p2["position"])
        self.assertGreaterEqual(p1["position"], 1)
        self.assertLessEqual(p1["position"], 20)

    def test_analyze_competitor_returns_expected_keys(self):
        res = self.ca.analyze_competitor("example.com")
        for k in [
            "domain",
            "estimated_monthly_traffic",
            "estimated_backlinks",
            "domain_authority",
            "content_quality_score",
            "main_keywords",
            "top_pages",
        ]:
            self.assertIn(k, res)

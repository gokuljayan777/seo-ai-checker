from django.test import TestCase

from seo_app.services.backlink_analysis import BacklinkAnalyzer


class BacklinkServiceTests(TestCase):

    def setUp(self):
        self.analyzer = BacklinkAnalyzer()

    def test_estimate_backlinks(self):
        r = self.analyzer._estimate_total_backlinks("example.com")
        self.assertIsInstance(r, int)
        self.assertGreater(r, 0)

    def test_referrers(self):
        refs = self.analyzer._top_referrers("example.com", limit=5)
        self.assertEqual(len(refs), 5)
        self.assertIn("referrer", refs[0])

    def test_anchor_texts(self):
        anchors = self.analyzer._anchor_texts("example.com", limit=3)
        self.assertEqual(len(anchors), 3)
        self.assertIsInstance(anchors[0][0], str)

    def test_compare_link_gap(self):
        gap = self.analyzer.compare_link_gap("example.com", "example.org")
        self.assertIn("missing_for_source", gap)
        self.assertIn("missing_for_target", gap)

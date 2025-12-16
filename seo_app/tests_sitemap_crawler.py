from unittest.mock import Mock, patch

from django.test import TestCase

from seo_app.services import sitemap_crawler as sc
from seo_app.models import Page, PageAnalysis


class SitemapCrawlerTests(TestCase):
    def test_parse_sitemap_xml_urlset_returns_urls(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url>
            <loc>https://example.com/</loc>
          </url>
          <url>
            <loc>https://example.com/blog</loc>
          </url>
        </urlset>
        """

        urls = sc._parse_sitemap_xml(xml, "https://example.com/sitemap.xml")
        self.assertIn("https://example.com/", urls)
        self.assertIn("https://example.com/blog", urls)

    def test_parse_sitemap_xml_index_returns_sitemaps(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <sitemap>
            <loc>https://example.com/sitemap1.xml</loc>
          </sitemap>
        </sitemapindex>
        """

        sitemaps = sc._parse_sitemap_xml(xml, "https://example.com/sitemap_index.xml")
        self.assertEqual(sitemaps, ["https://example.com/sitemap1.xml"])

    @patch("seo_app.services.sitemap_crawler.requests.get")
    def test_fetch_all_urls_from_sitemaps_handles_nested(self, mock_get):
        # sitemap index -> two nested sitemaps -> urlsets
        index_xml = """<?xml version="1.0"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <sitemap><loc>https://example.com/sitemap1.xml</loc></sitemap>
          <sitemap><loc>https://example.com/sitemap2.xml</loc></sitemap>
        </sitemapindex>
        """

        s1_xml = """<?xml version="1.0"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://example.com/a</loc></url>
        </urlset>
        """

        s2_xml = """<?xml version="1.0"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://example.com/b</loc></url>
        </urlset>
        """

        def side_effect(url, headers=None, timeout=10):
            m = Mock()
            m.status_code = 200
            if url.endswith("sitemap_index.xml"):
                m.text = index_xml
            elif url.endswith("sitemap1.xml"):
                m.text = s1_xml
            elif url.endswith("sitemap2.xml"):
                m.text = s2_xml
            else:
                m.status_code = 404
                m.text = ""
            return m

        mock_get.side_effect = side_effect

        urls = sc._fetch_all_urls_from_sitemaps(["https://example.com/sitemap_index.xml"], max_urls=50)
        self.assertIn("https://example.com/a", urls)
        self.assertIn("https://example.com/b", urls)

    @patch("seo_app.services.sitemap_crawler.fetch_html")
    @patch("seo_app.services.sitemap_crawler.run_all_rules")
    @patch("seo_app.services.sitemap_crawler.parse_page")
    @patch("seo_app.services.sitemap_crawler._find_sitemaps")
    @patch("seo_app.services.sitemap_crawler.requests.get")
    def test_crawl_site_from_sitemap_end_to_end(self, mock_get, mock_find, mock_parse, mock_rules, mock_fetch):
        # Provide a sitemap with one page
        sitemap_xml = """<?xml version="1.0"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://example.com/page1</loc></url>
        </urlset>
        """

        m = Mock()
        m.status_code = 200
        m.text = sitemap_xml
        mock_get.return_value = m

        mock_find.return_value = ["https://example.com/sitemap.xml"]

        mock_fetch.return_value = {
            "ok": True,
            "url": "https://example.com/page1",
            "html": "<html><head><title>Test</title></head><body><h1>H1</h1></body></html>",
            "status_code": 200,
        }

        mock_parse.return_value = {
            "title": "Test",
            "meta_description": "",
            "h1": ["H1"],
            "h2": [],
            "h3": [],
            "images": [],
            "word_count": 100,
            "raw_html_snippet": "",
        }

        mock_rules.return_value = (80, {"title": 20}, [])

        res = sc.crawl_site_from_sitemap("https://example.com", max_pages=10)

        self.assertTrue(res["ok"])
        self.assertEqual(res["pages_analyzed"], 1)
        self.assertEqual(len(res["pages"]), 1)
        page = res["pages"][0]
        self.assertEqual(page["status"], "success")
        self.assertEqual(page["url"], "https://example.com/page1")

        # DB objects created
        self.assertTrue(Page.objects.filter(url="https://example.com/page1").exists())
        self.assertTrue(PageAnalysis.objects.filter(page__url="https://example.com/page1").exists())

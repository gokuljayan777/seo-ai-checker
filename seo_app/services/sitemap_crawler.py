# seo_app/services/sitemap_crawler.py
import os
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any
from collections import deque
from bs4 import BeautifulSoup
from .crawler import fetch_html, parse_page
from .analyzer_rules import run_all_rules
from ..models import Page, PageAnalysis
from django.utils import timezone

# Optional LLM hook: try to import generate_suggestions (Gemini/OpenAI wrappers)
try:
    from .analyzer_gemini import generate_suggestions
except Exception:
    try:
        from .analyzer_llm import generate_suggestions
    except Exception:
        generate_suggestions = None

DEFAULT_HEADERS = {
    "User-Agent": "SEO-AI-Checker/1.0 (+https://example.com)"
}


def _get_domain(url: str) -> str:
    """Extract domain from URL"""
    parsed = urlparse(url)
    return parsed.netloc


def _find_sitemaps(base_url: str, timeout: int = 10) -> List[str]:
    """
    Find sitemap URLs by:
    1. Checking robots.txt
    2. Trying common sitemap paths
    Returns list of sitemap URLs to process
    """
    sitemaps = []
    domain = _get_domain(base_url)
    protocol = urlparse(base_url).scheme or "https"
    base_domain = f"{protocol}://{domain}"
    
    # 1. Try robots.txt
    robots_url = f"{base_domain}/robots.txt"
    try:
        resp = requests.get(robots_url, headers=DEFAULT_HEADERS, timeout=timeout)
        if resp.status_code == 200:
            for line in resp.text.split('\n'):
                line = line.strip().lower()
                if line.startswith('sitemap:'):
                    sitemap_url = line.split(':', 1)[1].strip()
                    if sitemap_url and sitemap_url not in sitemaps:
                        sitemaps.append(sitemap_url)
    except Exception:
        pass
    
    # 2. Try common sitemap paths
    common_paths = [
        '/sitemap.xml',
        '/sitemap_index.xml',
        '/sitemaps/sitemap.xml',
        '/sitemap1.xml',
    ]
    for path in common_paths:
        sitemap_url = f"{base_domain}{path}"
        if sitemap_url not in sitemaps:
            sitemaps.append(sitemap_url)
    
    return sitemaps


def _parse_sitemap_xml(xml_content: str, base_url: str) -> List[str]:
    """
    Parse sitemap XML and extract URLs.
    Handles both <url> entries and nested sitemaps.
    Returns list of page URLs
    """
    urls = []
    try:
        root = ET.fromstring(xml_content)
        
        # Try with namespace first
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        # Check if this is a sitemap index (contains sitemaps)
        sitemaps = root.findall('sm:sitemap/sm:loc', ns)
        if not sitemaps:
            # Try without namespace
            sitemaps = root.findall('sitemap/loc')
        
        if sitemaps:
            # This is a sitemap index, return nested sitemap URLs
            return [sm.text for sm in sitemaps if sm.text]
        
        # Extract page URLs - try with namespace first
        url_elements = root.findall('sm:url/sm:loc', ns)
        if not url_elements:
            # Try without namespace
            url_elements = root.findall('url/loc')
        
        urls = [url.text for url in url_elements if url.text]
        
        if urls:
            print(f"Extracted {len(urls)} URLs from sitemap")
        else:
            print(f"No URLs found in sitemap. Root tag: {root.tag}, Children: {[child.tag for child in root[:5]]}")
    except Exception as e:
        print(f"Error parsing sitemap XML: {e}")
    
    return urls


def _fetch_all_urls_from_sitemaps(sitemap_urls: List[str], max_urls: int = 500, timeout: int = 10) -> List[str]:
    """
    Recursively fetch all URLs from sitemaps (handles sitemap indices)
    Returns flattened list of all page URLs
    """
    all_urls = []
    visited_sitemaps = set()
    to_process = sitemap_urls[:]
    
    while to_process and len(all_urls) < max_urls:
        sitemap_url = to_process.pop(0)
        
        if sitemap_url in visited_sitemaps:
            continue
        visited_sitemaps.add(sitemap_url)
        
        try:
            resp = requests.get(sitemap_url, headers=DEFAULT_HEADERS, timeout=timeout)
            if resp.status_code == 200:
                urls = _parse_sitemap_xml(resp.text, sitemap_url)
                
                # Check if URLs look like sitemaps (contain sitemap in domain)
                for url in urls:
                    if url.endswith('.xml') and 'sitemap' in url.lower():
                        # It's another sitemap, add to processing queue
                        to_process.append(url)
                    else:
                        # It's a page URL
                        if url not in all_urls:
                            all_urls.append(url)
                            if len(all_urls) >= max_urls:
                                break
        except Exception as e:
            print(f"Error fetching sitemap {sitemap_url}: {e}")
    
    return all_urls[:max_urls]


def _crawl_site_bfs_fallback(base_url: str, max_pages: int = 50) -> List[str]:
    """
    Fallback BFS crawler when sitemap is not available.
    Crawls internal links up to max_pages.
    Returns list of discovered page URLs
    """
    domain = _get_domain(base_url)
    visited = set()
    queue = deque([(base_url, 0)])
    discovered_urls = []
    
    while queue and len(discovered_urls) < max_pages:
        url, depth = queue.popleft()
        
        if url in visited or depth > 2:  # Max depth 2
            continue
        
        visited.add(url)
        
        try:
            fetch_res = fetch_html(url)
            if not fetch_res["ok"]:
                continue
            
            discovered_urls.append(fetch_res["url"])
            
            # Extract links from page
            soup = BeautifulSoup(fetch_res["html"], "html.parser")
            for link in soup.find_all("a", href=True):
                href = link["href"]
                abs_url = urljoin(fetch_res["url"], href)
                
                # Only crawl internal links (same domain)
                if _get_domain(abs_url) == domain:
                    # Remove fragment
                    clean_url = abs_url.split("#")[0]
                    if clean_url not in visited and clean_url not in [u for u, _ in queue]:
                        queue.append((clean_url, depth + 1))
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            continue
    
    print(f"BFS fallback discovered {len(discovered_urls)} pages")
    return discovered_urls


def crawl_site_from_sitemap(base_url: str, max_pages: int = 500, force_llm: bool = False) -> Dict[str, Any]:
    """
    Main function: crawl site using sitemaps
    Returns summary of crawled pages
    """
    # Find sitemaps
    sitemap_urls = _find_sitemaps(base_url)
    
    if not sitemap_urls:
        return {
            "ok": False,
            "error": "No sitemaps found for this domain",
            "base_url": base_url,
            "pages_analyzed": 0,
            "pages": []
        }
    
    # Fetch all URLs from sitemaps
    page_urls = _fetch_all_urls_from_sitemaps(sitemap_urls, max_urls=max_pages)
    
    # If sitemap extraction failed, fall back to BFS crawling
    if not page_urls:
        print(f"No URLs from sitemap, falling back to BFS crawler")
        page_urls = _crawl_site_bfs_fallback(base_url, max_pages=min(50, max_pages))
    
    if not page_urls:
        return {
            "ok": False,
            "error": "Could not discover pages from sitemap or by crawling",
            "base_url": base_url,
            "pages_analyzed": 0,
            "pages": []
        }
    
    # Analyze each page
    analyzed_pages = []
    for page_url in page_urls:
        try:
            # Fetch page
            fetch_res = fetch_html(page_url)
            if not fetch_res["ok"]:
                analyzed_pages.append({
                    "url": page_url,
                    "status": "error",
                    "error": fetch_res["error"]
                })
                continue
            
            # Parse and analyze
            parsed = parse_page(fetch_res["html"], base_url=fetch_res["url"])
            parsed["issues"] = []  # Will be populated by rules
            
            score, breakdown, issues = run_all_rules(parsed)
            parsed["issues"] = issues
            
            # Save to database
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
                score=score,
                score_breakdown=breakdown,
                rule_issues=issues,
                raw_html_snippet=parsed.get("raw_html_snippet", ""),
            )

            # Optionally call LLM per-page (if available). Use force_llm to bypass any cache.
            try:
                if generate_suggestions and (force_llm or os.getenv("FORCE_LLM_PER_PAGE", "false").lower() == "true"):
                    try:
                        llm_out = generate_suggestions(parsed)
                    except Exception as le:
                        llm_out = {"ok": False, "error": str(le)}
                    pa.llm_suggestions = llm_out or {}
                    pa.llm_model = os.getenv("LLM_MODEL", "") or pa.llm_model
                    pa.llm_generated_at = timezone.now()
                    pa.save(update_fields=["llm_suggestions", "llm_model", "llm_generated_at"])
            except Exception:
                # don't let LLM failures break the crawl
                pass
            
            analyzed_pages.append({
                "url": fetch_res["url"],
                "status": "success",
                "status_code": fetch_res["status_code"],
                "score": score,
                "title": parsed.get("title", ""),
                "issues_count": len(issues),
            })
        except Exception as e:
            analyzed_pages.append({
                "url": page_url,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "ok": True,
        "base_url": base_url,
        "sitemaps_found": sitemap_urls,
        "pages_analyzed": len([p for p in analyzed_pages if p["status"] == "success"]),
        "pages_failed": len([p for p in analyzed_pages if p["status"] == "error"]),
        "pages": analyzed_pages,
        "analyzed_at": timezone.now().isoformat()
    }

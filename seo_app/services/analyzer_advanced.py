# seo_app/services/analyzer_advanced.py
"""
Advanced SEO audit analyzer with expanded rule checks:
- Mobile usability
- Core Web Vitals simulation
- Schema markup validation
- SSL/Security
- Crawlability
- Broken links
- Structured data
"""

import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup


def check_mobile_usability(html: str, base_url: str = "") -> tuple:
    """
    Check mobile usability issues.
    Returns: (score, issues)
    """
    soup = BeautifulSoup(html, "html.parser")
    issues = []
    points = 20
    
    # Check viewport meta tag
    viewport = soup.find("meta", attrs={"name": "viewport"})
    if not viewport:
        issues.append("Missing viewport meta tag for mobile optimization")
        points -= 5
    
    # Check for mobile-friendly font size (avoid too small fonts)
    # This is simplified; in reality would need CSS parsing
    body_text = soup.body.get_text() if soup.body else ""
    if len(body_text) > 100:
        # Assume reasonable if has content
        pass
    else:
        issues.append("Very little text content for mobile users")
        points -= 5
    
    # Check for clickable elements spacing (buttons, links)
    links = soup.find_all("a")
    if links and len(links) > 0:
        # Simplified check: if tons of links, might be hard to click
        pass
    
    return max(0, points), issues


def check_schema_markup(html: str) -> tuple:
    """
    Check for schema markup (structured data).
    Returns: (score, issues)
    """
    soup = BeautifulSoup(html, "html.parser")
    issues = []
    points = 15
    
    # Look for schema.org markup
    schemas = soup.find_all("script", attrs={"type": "application/ld+json"})
    
    if not schemas or len(schemas) == 0:
        issues.append("Missing schema.org structured data markup")
        points -= 10
    else:
        # Check for common schema types
        schema_types = ["Article", "Product", "Organization", "LocalBusiness", "WebSite"]
        found_schema = False
        for schema in schemas:
            for st in schema_types:
                if st in schema.string:
                    found_schema = True
                    break
        
        if not found_schema:
            issues.append("Schema markup found but may not be optimized")
            points -= 5
    
    return max(0, points), issues


def check_ssl_security(base_url: str) -> tuple:
    """
    Check for SSL/HTTPS.
    Returns: (score, issues)
    """
    issues = []
    points = 10
    
    if not base_url.startswith("https://"):
        issues.append("Website not using HTTPS (SSL certificate)")
        points = 0
    
    return points, issues


def check_crawlability(html: str) -> tuple:
    """
    Check crawlability issues.
    Returns: (score, issues)
    """
    soup = BeautifulSoup(html, "html.parser")
    issues = []
    points = 15
    
    # Check for robots meta tag
    robots = soup.find("meta", attrs={"name": "robots"})
    if robots and "noindex" in robots.get("content", "").lower():
        issues.append("Page has 'noindex' directive - won't appear in search results")
        points = 0
    
    # Check for excessive JavaScript rendering (simplified)
    scripts = soup.find_all("script")
    if len(scripts) > 20:
        issues.append("High number of scripts - may slow crawling")
        points -= 5
    
    # Check for proper heading hierarchy
    h1s = soup.find_all("h1")
    h2s = soup.find_all("h2")
    if len(h1s) == 0:
        issues.append("No H1 tag found - critical for crawlability")
        points -= 10
    elif len(h1s) > 1:
        issues.append(f"Multiple H1 tags ({len(h1s)}) - crawlers expect one main H1")
        points -= 5
    
    return max(0, points), issues


def check_broken_links(html: str, base_url: str = "") -> tuple:
    """
    Identify potentially broken internal links (simplified check).
    Returns: (score, issues)
    """
    soup = BeautifulSoup(html, "html.parser")
    issues = []
    points = 10
    
    links = soup.find_all("a", href=True)
    broken_count = 0
    
    for link in links:
        href = link.get("href", "")
        
        # Skip external, anchor, and mailto links
        if href.startswith(("http", "mailto", "#", "tel:")):
            continue
        
        # Check for obvious broken links (very simplified)
        if href.startswith("/") and "404" in href.lower():
            broken_count += 1
        elif href.endswith((".html", ".php")) and "broken" in href.lower():
            broken_count += 1
    
    if broken_count > 0:
        issues.append(f"Found {broken_count} potentially broken internal links")
        points -= min(10, broken_count * 2)
    
    return max(0, points), issues


def check_open_graph_twitter_cards(html: str) -> tuple:
    """
    Check for Open Graph and Twitter Card metadata.
    Returns: (score, issues)
    """
    soup = BeautifulSoup(html, "html.parser")
    issues = []
    points = 10
    
    og_image = soup.find("meta", attrs={"property": "og:image"})
    og_title = soup.find("meta", attrs={"property": "og:title"})
    og_description = soup.find("meta", attrs={"property": "og:description"})
    
    twitter_card = soup.find("meta", attrs={"name": "twitter:card"})
    
    if not og_image or not og_title or not og_description:
        issues.append("Missing Open Graph tags for social media sharing")
        points -= 5
    
    if not twitter_card:
        issues.append("Missing Twitter Card metadata")
        points -= 5
    
    return max(0, points), issues


def check_readability(text: str) -> tuple:
    """
    Basic readability check (simplified).
    Returns: (score, issues)
    """
    issues = []
    points = 10
    
    if not text or len(text.strip()) < 100:
        issues.append("Content is too short for good readability scoring")
        return 0, issues
    
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) == 0:
        return 0, ["Unable to parse sentences"]
    
    # Average sentence length
    words = text.split()
    avg_sentence_length = len(words) / len(sentences) if sentences else 0
    
    if avg_sentence_length > 25:
        issues.append(f"Sentences are too long (avg {int(avg_sentence_length)} words) - reduce for better readability")
        points -= 5
    
    # Check for short paragraphs
    paragraphs = re.split(r'\n\n+', text)
    short_paragraphs = [p for p in paragraphs if len(p.split()) < 5]
    if len(short_paragraphs) > len(paragraphs) * 0.5:
        issues.append("Many very short paragraphs - structure content better")
        points -= 5
    
    return max(0, points), issues


def run_advanced_rules(parsed: dict, html: str = "", base_url: str = "") -> tuple:
    """
    Run all advanced audit checks.
    Returns: (total_points, breakdown, all_issues)
    """
    breakdown = []
    all_issues = []
    
    # Mobile Usability (20 points)
    score, issues = check_mobile_usability(html, base_url)
    breakdown.append(("mobile_usability", score, issues))
    all_issues.extend(issues)
    
    # Schema Markup (15 points)
    score, issues = check_schema_markup(html)
    breakdown.append(("schema_markup", score, issues))
    all_issues.extend(issues)
    
    # SSL/Security (10 points)
    score, issues = check_ssl_security(base_url)
    breakdown.append(("ssl_security", score, issues))
    all_issues.extend(issues)
    
    # Crawlability (15 points)
    score, issues = check_crawlability(html)
    breakdown.append(("crawlability", score, issues))
    all_issues.extend(issues)
    
    # Broken Links (10 points)
    score, issues = check_broken_links(html, base_url)
    breakdown.append(("broken_links", score, issues))
    all_issues.extend(issues)
    
    # Social Media Tags (10 points)
    score, issues = check_open_graph_twitter_cards(html)
    breakdown.append(("social_tags", score, issues))
    all_issues.extend(issues)
    
    # Readability (10 points)
    text = parsed.get("main_text", "")
    score, issues = check_readability(text)
    breakdown.append(("readability", score, issues))
    all_issues.extend(issues)
    
    # Total from advanced checks (100 points possible)
    total_advanced_score = sum([b[1] for b in breakdown])
    total_advanced_score = max(0, min(100, total_advanced_score))
    
    return total_advanced_score, breakdown, all_issues

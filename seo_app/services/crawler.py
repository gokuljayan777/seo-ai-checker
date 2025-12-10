# seo_app/services/crawler.py
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "User-Agent": "SEO-AI-Checker/1.0 (+https://example.com)"
}

def _clean(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()

def fetch_html(url: str, timeout: int = 15):
    """
    Fetch a URL and return a dict: { ok, status_code, url, html, error }
    - Normalizes URL to include scheme (prefers https:// if missing).
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url  # prefer https by default

    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        resp.raise_for_status()
        return {
            "ok": True,
            "status_code": resp.status_code,
            "url": resp.url,
            "html": resp.text,
            "error": None,
        }
    except requests.exceptions.RequestException as exc:
        return {
            "ok": False,
            "status_code": getattr(exc.response, "status_code", None),
            "url": url,
            "html": None,
            "error": str(exc),
        }

def parse_page(html: str, base_url: str = ""):
    """
    Parse HTML and return a structured dict with title, meta_description,
    headings, images (absolute src + alt), word_count, and issues (simple rules).
    """
    soup = BeautifulSoup(html or "", "html.parser")

    # Title
    title_tag = soup.find("title")
    title = _clean(title_tag.get_text()) if title_tag else ""

    # Meta description (name="description" or og:description)
    md = ""
    desc = soup.find("meta", attrs={"name": lambda v: v and v.lower() == "description"})
    if desc and desc.get("content"):
        md = _clean(desc["content"])
    else:
        og = soup.find("meta", attrs={"property": lambda v: v and v.lower() == "og:description"})
        if og and og.get("content"):
            md = _clean(og["content"])

    # Headings
    def get_headings(tag):
        return [_clean(h.get_text()) for h in soup.find_all(tag)]

    h1 = get_headings("h1")
    h2 = get_headings("h2")
    h3 = get_headings("h3")

    # Images: absolute src + alt
    images = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or ""
        if src:
            src = urljoin(base_url, src)
        images.append({"src": src, "alt": (img.get("alt") or "").strip()})

    # Attempt to extract main text: prefer <main>, <article>, then biggest div/section, fallback to body
    def extract_main_text():
        main = soup.find("main") or soup.find("article")
        if main:
            t = _clean(main.get_text(separator=" ", strip=True))
            if len(t) > 50:
                return t
        # choose largest div/section
        best = ""
        for tag in soup.find_all(["div", "section"], recursive=True):
            t = _clean(tag.get_text(separator=" ", strip=True))
            if len(t) > len(best):
                best = t
        if len(best) > 50:
            return best
        body = soup.body
        return _clean(body.get_text(separator=" ", strip=True)) if body else ""

    main_text = extract_main_text()
    words = [w for w in re.split(r"\s+", main_text) if w]
    word_count = len(words)

    # Simple rules / issues
    issues = []
    if not title:
        issues.append({"code": "missing_title", "message": "Title tag is missing."})
    else:
        if len(title) < 20:
            issues.append({"code": "short_title", "message": "Title is very short."})
        if len(title) > 80:
            issues.append({"code": "long_title", "message": "Title is very long (might be truncated)."})
    if not md:
        issues.append({"code": "missing_meta_description", "message": "Meta description is missing."})
    else:
        if len(md) < 50:
            issues.append({"code": "short_meta", "message": "Meta description is very short."})
        if len(md) > 320:
            issues.append({"code": "long_meta", "message": "Meta description is very long."})
    if len(h1) == 0:
        issues.append({"code": "missing_h1", "message": "No H1 found."})
    elif len(h1) > 1:
        issues.append({"code": "multiple_h1", "message": f"Multiple H1 tags found ({len(h1)})."})
    if word_count < 200:
        issues.append({"code": "thin_content", "message": f"Low word count ({word_count}). Consider expanding content."})
    imgs_without_alt = [img for img in images if not img["alt"]]
    if imgs_without_alt:
        issues.append({"code": "missing_image_alt", "message": f"{len(imgs_without_alt)} images missing alt text."})

    return {
        "title": title,
        "meta_description": md,
        "h1": h1,
        "h2": h2,
        "h3": h3,
        "images": images,
        "word_count": word_count,
        "main_text": main_text,  # For readability analysis
        "issues": issues,
        "raw_html_snippet": (html or "")[:8000],
    }

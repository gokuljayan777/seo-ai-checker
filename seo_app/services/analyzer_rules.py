# seo_app/services/analyzer_rules.py

def score_title(title: str):
    if not title:
        return 0, ["Title missing"]

    if 30 <= len(title) <= 60:
        return 20, []
    elif len(title) < 30:
        return 12, ["Title too short"]
    else:
        return 15, ["Title too long"]

def score_meta(md: str):
    if not md:
        return 0, ["Meta description missing"]

    if 50 <= len(md) <= 160:
        return 20, []
    elif len(md) < 50:
        return 10, ["Meta description short"]
    else:
        return 14, ["Meta description long"]

def score_h1(h1_list):
    n = len(h1_list)

    if n == 0:
        return 0, ["Missing H1"]
    if n == 1:
        return 15, []
    if n > 1:
        return 7, [f"Multiple H1 tags ({n})"]

def score_word_count(wc: int):
    if wc >= 800:
        return 20, []
    elif wc >= 300:
        # scale 10–20
        points = int(10 + (wc - 300) / 500 * 10)
        return points, []
    else:
        return 5, [f"Thin content ({wc} words)"]

def score_images(images):
    if not images:
        return 5, ["No images present"]

    total = len(images)
    with_alt = sum(1 for img in images if img.get("alt") and img["alt"].strip())

    pct = with_alt / total
    points = int(pct * 10)

    issues = []
    if with_alt < total:
        issues.append(f"{total - with_alt} images missing alt")

    return points, issues

def run_all_rules(parsed):
    """
    parsed = result from parse_page()
    Returns:
        score: int 0–100
        breakdown: list of (component, score, issues)
        issues: flat list for UI
    """
    title = parsed["title"]
    md = parsed["meta_description"]
    h1 = parsed["h1"]
    wc = parsed["word_count"]
    images = parsed["images"]

    breakdown = []
    all_issues = []

    # Title
    s, issues = score_title(title)
    breakdown.append(("title", s, issues))
    all_issues.extend(issues)

    # Meta
    s, issues = score_meta(md)
    breakdown.append(("meta_description", s, issues))
    all_issues.extend(issues)

    # H1
    s, issues = score_h1(h1)
    breakdown.append(("h1", s, issues))
    all_issues.extend(issues)

    # Word count
    s, issues = score_word_count(wc)
    breakdown.append(("content", s, issues))
    all_issues.extend(issues)

    # Images
    s, issues = score_images(images)
    breakdown.append(("images", s, issues))
    all_issues.extend(issues)

    # Total score = sum of all components but capped at 100
    total_score = sum([b[1] for b in breakdown])
    total_score = max(0, min(100, total_score))

    return total_score, breakdown, all_issues

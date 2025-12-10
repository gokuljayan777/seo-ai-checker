# seo_app/services/analyzer_suggestions.py
"""
Fallback suggestion generator that creates SEO suggestions based on detected issues.
This works without any LLM API calls, so it's always available and free.
"""

def generate_suggestions_from_issues(parsed: dict) -> dict:
    """
    Generate SEO suggestions based on detected issues without calling LLM.
    Returns dict with improved_title, improved_meta_description, improved_h1, seo_summary, suggestions.
    """
    title = parsed.get("title", "")
    meta = parsed.get("meta_description", "")
    h1s = parsed.get("h1", [])
    word_count = parsed.get("word_count", 0)
    images = parsed.get("images", [])
    issues = parsed.get("issues", [])
    
    # Extract issue codes for easy checking
    issue_codes = []
    if isinstance(issues, list):
        for issue in issues:
            if isinstance(issue, dict):
                issue_codes.append(issue.get("code", ""))
            elif isinstance(issue, str):
                issue_codes.append(issue.lower().replace(" ", "_").replace("(", "").replace(")", ""))
    
    suggestions = []
    improved_title = title
    improved_meta = meta
    improved_h1 = h1s[0] if h1s else ""
    
    # Title suggestions
    title_len = len(title)
    if title_len < 30:
        improved_title = title + " | Your Complete Guide"
        suggestions.append("Expand your title to 30-60 characters. Current: {} chars".format(title_len))
    elif title_len > 60:
        improved_title = title[:57] + "..."
        suggestions.append("Shorten your title to under 60 characters for better SERP display. Current: {} chars".format(title_len))
    
    # Meta description suggestions
    meta_len = len(meta)
    if meta_len == 0:
        improved_meta = title + " - Learn more about this topic in our comprehensive guide."
        suggestions.append("Add a meta description (50-160 chars) to improve CTR in search results")
    elif meta_len < 50:
        improved_meta = meta + " Discover more insights and best practices."
        suggestions.append("Expand meta description to 50+ characters. Current: {} chars".format(meta_len))
    elif meta_len > 160:
        improved_meta = meta[:157] + "..."
        suggestions.append("Shorten meta description to under 160 characters. Current: {} chars".format(meta_len))
    
    # H1 suggestions
    h1_count = len(h1s)
    if h1_count == 0:
        improved_h1 = title
        suggestions.append("Add a single H1 tag that clearly describes the main topic of the page")
    elif h1_count > 1:
        improved_h1 = h1s[0]
        suggestions.append("Use only one H1 per page. Currently found: {}. Keep the main one, convert others to H2/H3.".format(h1_count))
    
    # Content length suggestions
    if word_count < 300:
        suggestions.append("Expand content to at least 300 words (preferably 800+). Current: {} words".format(word_count))
    elif word_count < 800:
        suggestions.append("Consider expanding to 800+ words for better SEO performance. Current: {} words".format(word_count))
    
    # Image suggestions
    images_without_alt = [img for img in images if not img.get("alt", "").strip()]
    if len(images_without_alt) > 0:
        suggestions.append("Add descriptive alt text to {} images for better accessibility and SEO".format(len(images_without_alt)))
    if len(images) == 0:
        suggestions.append("Consider adding relevant images to improve engagement and reduce bounce rate")
    
    # Add unique suggestions based on specific issues
    for code in issue_codes:
        if "thin_content" in code and "content length" not in "\n".join(suggestions):
            suggestions.append("Content seems thin. Add more valuable content to improve SEO ranking")
        elif "multiple_h1" in code and "only one H1" not in "\n".join(suggestions):
            suggestions.append("Search engines prefer pages with a single H1. Restructure your heading hierarchy.")
    
    # Generate summary
    seo_summary = f"Your page '{title}' scores {word_count} words and has {len(issues)} SEO issues. "
    if len(issues) > 0:
        issue_messages = []
        for it in issues[:3]:
            if isinstance(it, dict):
                msg = it.get('message', str(it))
            else:
                msg = str(it)
            issue_messages.append(msg[:30])
        seo_summary += f"Key issues to fix: {', '.join(issue_messages)}. "
    seo_summary += "Focus on content quality, proper heading structure, and descriptive metadata."
    
    # Remove duplicates from suggestions
    suggestions = list(dict.fromkeys(suggestions))
    
    return {
        "improved_title": improved_title,
        "improved_meta_description": improved_meta,
        "improved_h1": improved_h1,
        "seo_summary": seo_summary,
        "suggestions": suggestions[:10]  # Limit to top 10 suggestions
    }

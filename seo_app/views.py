from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .services.crawler import fetch_html, parse_page
from .services.analyzer_rules import run_all_rules


@api_view(["GET", "POST"])
def analyze_url(request):
    if request.method == "GET":
        return Response({"message": "API working. Use POST {'url': '...'}"})

    url = request.data.get("url")
    if not url:
        return Response({"error": "URL missing"}, status=status.HTTP_400_BAD_REQUEST)

    # Fetch
    fetch_res = fetch_html(url)
    if not fetch_res["ok"]:
        return Response(
            {
                "error": "Failed to fetch",
                "details": fetch_res["error"],
                "url": fetch_res["url"],
            },
            status=502,
        )

    # Parse
    parsed = parse_page(fetch_res["html"], base_url=fetch_res["url"])

    # Analyze with rules
    score, breakdown, issues = run_all_rules(parsed)

    # Full response
    result = {
        "url": fetch_res["url"],
        "status_code": fetch_res["status_code"],
        **parsed,
        "score": score,
        "score_breakdown": breakdown,
        "rule_issues": issues,
    }

    return Response(result)

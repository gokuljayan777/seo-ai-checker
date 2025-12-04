from django.db import models


class Page(models.Model):
    url = models.URLField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.url


class PageAnalysis(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="analyses")

    status_code = models.IntegerField(null=True, blank=True)

    # Core extracted SEO data
    title = models.TextField(blank=True)
    meta_description = models.TextField(blank=True)
    h1 = models.JSONField(default=list)
    h2 = models.JSONField(default=list)
    h3 = models.JSONField(default=list)
    images = models.JSONField(default=list)
    word_count = models.IntegerField(default=0)

    # Rule analyzer results
    score = models.IntegerField(default=0)
    score_breakdown = models.JSONField(default=list)
    rule_issues = models.JSONField(default=list)

    # HTML (optional: store snippet only)
    raw_html_snippet = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.page.url} @ {self.created_at}"

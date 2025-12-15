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

    # HTML snippet
    raw_html_snippet = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # --- LLM Integration ---
    llm_model = models.CharField(max_length=128, blank=True)  # e.g., "gpt-4o-mini"
    llm_suggestions = models.JSONField(default=dict, blank=True)
    llm_generated_at = models.DateTimeField(null=True, blank=True)  # <-- REQUIRED

    def __str__(self):
        return f"Analysis for {self.page.url} @ {self.created_at}"


# ============================================================================
# ENHANCED MODELS FOR SEMRUSH-LIKE FEATURES
# ============================================================================


class Domain(models.Model):
    """Represents a domain being tracked"""

    domain = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Cached metrics (updated periodically)
    domain_authority = models.FloatField(null=True, blank=True)  # 0-100
    estimated_monthly_traffic = models.IntegerField(null=True, blank=True)
    total_backlinks = models.IntegerField(default=0)
    referring_domains = models.IntegerField(default=0)

    def __str__(self):
        return self.domain


class Keyword(models.Model):
    """SEO keyword data"""

    INTENT_CHOICES = [
        ("informational", "Informational"),
        ("commercial", "Commercial"),
        ("transactional", "Transactional"),
        ("navigational", "Navigational"),
    ]

    keyword = models.CharField(max_length=500)
    search_volume = models.IntegerField(default=0)
    keyword_difficulty = models.IntegerField(default=0)  # 0-100
    cpc = models.FloatField(default=0.0)  # Cost per click for paid ads
    intent = models.CharField(
        max_length=20, choices=INTENT_CHOICES, default="informational"
    )

    # Trend data
    trend_score = models.JSONField(default=list)  # List of monthly trend scores

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("keyword",)

    def __str__(self):
        return f"{self.keyword} (Vol: {self.search_volume})"


class KeywordRanking(models.Model):
    """Track keyword rankings for a domain over time"""

    domain = models.ForeignKey(
        Domain, on_delete=models.CASCADE, related_name="keyword_rankings"
    )
    keyword = models.ForeignKey(
        Keyword, on_delete=models.CASCADE, related_name="rankings"
    )

    position = models.IntegerField()  # 1, 2, 3, etc.
    url = models.URLField()  # The ranking URL
    search_volume = models.IntegerField(default=0)  # Cached from Keyword

    recorded_date = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ("domain", "keyword", "recorded_date")

    def __str__(self):
        return f"{self.domain} - {self.keyword} (Pos: {self.position})"


class Competitor(models.Model):
    """Track competitor domains"""

    domain = models.ForeignKey(
        Domain, on_delete=models.CASCADE, related_name="competitor_of"
    )
    competitor_domain = models.ForeignKey(
        Domain, on_delete=models.CASCADE, related_name="competing_against"
    )

    keywords_in_common = models.IntegerField(default=0)  # Number of shared top rankings
    estimated_competitor_traffic = models.IntegerField(default=0)

    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("domain", "competitor_domain")

    def __str__(self):
        return f"{self.domain} vs {self.competitor_domain}"


class Backlink(models.Model):
    """Backlink data for a domain"""

    QUALITY_CHOICES = [
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
    ]

    target_domain = models.ForeignKey(
        Domain, on_delete=models.CASCADE, related_name="backlinks"
    )
    source_url = models.URLField()
    source_domain = models.CharField(max_length=255)

    anchor_text = models.TextField(blank=True)
    link_type = models.CharField(
        max_length=20,
        choices=[("dofollow", "DoFollow"), ("nofollow", "NoFollow")],
        default="dofollow",
    )
    quality = models.CharField(
        max_length=10, choices=QUALITY_CHOICES, default="medium"
    )  # Based on DA/DR

    target_url = models.URLField(null=True, blank=True)
    source_domain_authority = models.FloatField(default=0)  # DA of source

    found_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  # Mark as lost if removed

    class Meta:
        unique_together = ("target_domain", "source_url", "target_url")

    def __str__(self):
        return f"{self.source_domain} → {self.target_domain}"


class ContentPage(models.Model):
    """Track important content pages and their performance"""

    domain = models.ForeignKey(
        Domain, on_delete=models.CASCADE, related_name="content_pages"
    )
    url = models.URLField()
    title = models.CharField(max_length=500, blank=True)

    word_count = models.IntegerField(default=0)
    internal_links = models.IntegerField(default=0)
    external_links = models.IntegerField(default=0)

    # SEO metrics
    primary_keyword = models.ForeignKey(
        Keyword, on_delete=models.SET_NULL, null=True, blank=True
    )
    seo_score = models.IntegerField(default=0)

    # Content performance
    engagement_score = models.FloatField(default=0)  # 0-100

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("domain", "url")

    def __str__(self):
        return f"{self.domain} - {self.url}"


class SiteMetrics(models.Model):
    """Historical metrics for a domain (snapshots over time)"""

    domain = models.ForeignKey(
        Domain, on_delete=models.CASCADE, related_name="metrics_history"
    )

    organic_traffic = models.IntegerField(default=0)
    organic_keywords = models.IntegerField(default=0)
    domain_authority = models.FloatField(default=0)
    total_backlinks = models.IntegerField(default=0)
    referring_domains = models.IntegerField(default=0)

    seo_health_score = models.IntegerField(default=0)  # 0-100

    recorded_date = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ("domain", "recorded_date")

    def __str__(self):
        return f"{self.domain} - {self.recorded_date}"


class AuditHistory(models.Model):
    """Track audit scores over time for trend analysis"""

    page = models.ForeignKey(
        Page, on_delete=models.CASCADE, related_name="audit_history"
    )

    score = models.IntegerField(default=0)
    issues_count = models.IntegerField(default=0)
    critical_issues = models.IntegerField(default=0)

    recorded_date = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ("page", "recorded_date")

    def __str__(self):
        return f"{self.page.url} - {self.recorded_date} (Score: {self.score})"

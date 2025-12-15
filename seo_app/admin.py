from django.contrib import admin
from .models import Page, PageAnalysis, Domain, Backlink, Keyword, Competitor

# Register main models for admin UI
admin.site.register(Page)
admin.site.register(PageAnalysis)
admin.site.register(Domain)
admin.site.register(Backlink)
admin.site.register(Keyword)
admin.site.register(Competitor)

from django.contrib import admin

from .models import Backlink, Competitor, Domain, Keyword, Page, PageAnalysis

# Register main models for admin UI
admin.site.register(Page)
admin.site.register(PageAnalysis)
admin.site.register(Domain)
admin.site.register(Backlink)
admin.site.register(Keyword)
admin.site.register(Competitor)

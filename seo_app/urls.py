from django.urls import path
from .views import analyze_url

urlpatterns = [
    path('analyze/', analyze_url),
]

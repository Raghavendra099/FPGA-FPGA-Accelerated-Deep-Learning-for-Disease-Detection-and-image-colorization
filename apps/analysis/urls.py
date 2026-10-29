"""
URL routing for Analysis results and history.
"""
from django.urls import path
from . import views

app_name = "analysis"

urlpatterns = [
    path("history/", views.history_view, name="history"),
    path("<str:analysis_id>/", views.detail_view, name="detail"),
]

"""
URL routing for Reports app.
"""
from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("", views.list_view, name="list"),
    path("download/<str:analysis_id>/", views.download_report, name="download"),
]

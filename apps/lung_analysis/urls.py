"""
URL routing for Lung Disease Analysis.
"""
from django.urls import path
from . import views

app_name = "lung_analysis"

urlpatterns = [
    path("", views.index_view, name="index"),
]

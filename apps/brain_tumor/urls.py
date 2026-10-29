"""
URL routing for Brain Tumor Analysis.
"""
from django.urls import path
from . import views

app_name = "brain_tumor"

urlpatterns = [
    path("", views.index_view, name="index"),
]

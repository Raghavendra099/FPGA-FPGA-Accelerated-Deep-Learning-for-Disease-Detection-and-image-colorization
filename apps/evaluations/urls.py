"""
URL routing for Model Evaluation app.
"""
from django.urls import path
from . import views

app_name = "evaluations"

urlpatterns = [
    path("", views.index_view, name="index"),
]

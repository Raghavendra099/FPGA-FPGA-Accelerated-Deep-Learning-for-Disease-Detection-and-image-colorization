"""
URL routing for Image Colorization Studio.
"""
from django.urls import path
from . import views

app_name = "colorization"

urlpatterns = [
    path("", views.studio_view, name="studio"),
    path("run/<str:image_id>/", views.run_colorization, name="run"),
]

"""
URL routing for IoT Devices app.
"""
from django.urls import path
from . import views

app_name = "devices"

urlpatterns = [
    path("", views.index_view, name="index"),
    path("api/ingest/", views.api_device_ingest, name="api_ingest"),
]

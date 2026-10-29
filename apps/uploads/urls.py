"""
URL configuration for QR uploads app.
"""
from django.urls import path
from . import views

app_name = "uploads"

urlpatterns = [
    path("sessions/new/", views.create_session_view, name="create_session"),
    path("direct/", views.direct_upload_view, name="direct_upload"),
    path("mobile/upload/<str:token>/", views.mobile_upload_page, name="mobile_upload_page"),
    path("api/sessions/<str:token>/upload/", views.api_upload_image, name="api_upload"),
    path("api/sessions/<str:session_id>/status/", views.api_session_status, name="api_session_status"),
]

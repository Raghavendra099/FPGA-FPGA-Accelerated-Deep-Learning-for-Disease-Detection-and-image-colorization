"""
Root URL Configuration for SmartMed AI.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from apps.uploads.views import mobile_upload_page

urlpatterns = [
    path("", lambda req: redirect("dashboard:index"), name="home"),
    path("auth/", include("apps.authentication.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("uploads/", include("apps.uploads.urls")),
    path("mobile/upload/<str:token>/", mobile_upload_page, name="root_mobile_upload"),
    path("review/", include("apps.review.urls")),
    path("colorization/", include("apps.colorization.urls")),
    path("lung-analysis/", include("apps.lung_analysis.urls")),
    path("brain-tumor/", include("apps.brain_tumor.urls")),
    path("analysis/", include("apps.analysis.urls")),
    path("reports/", include("apps.reports.urls")),
    path("evaluations/", include("apps.evaluations.urls")),
    path("devices/", include("apps.devices.urls")),
    path("audit/", include("apps.audit.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

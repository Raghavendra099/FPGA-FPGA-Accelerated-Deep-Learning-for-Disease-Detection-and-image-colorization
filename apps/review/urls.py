"""
Review URL routing.
"""
from django.urls import path
from . import views

app_name = "review"

urlpatterns = [
    path("pending/", views.pending_list_view, name="pending_list"),
    path("<str:image_id>/", views.review_detail_view, name="detail"),
]

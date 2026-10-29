"""
Channels WebSocket routing for SmartMed AI.
"""
from django.urls import re_path
from apps.uploads.consumers import UploadSessionConsumer
from apps.review.consumers import ReviewConsumer

websocket_urlpatterns = [
    re_path(r"^ws/sessions/(?P<session_id>[\w-]+)/$", UploadSessionConsumer.as_asgi()),
    re_path(r"^ws/reviews/$", ReviewConsumer.as_asgi()),
]

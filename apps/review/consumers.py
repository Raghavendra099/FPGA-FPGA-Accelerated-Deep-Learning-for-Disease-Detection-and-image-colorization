"""
Django Channels WebSocket consumer for Pending Review page real-time updates.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class ReviewConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "review_updates"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        logger.info("WebSocket connected for Review Updates")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def review_event(self, event):
        await self.send(text_data=json.dumps({
            "event": event.get("event"),
            "data": event.get("data"),
            "message": event.get("message", "")
        }))

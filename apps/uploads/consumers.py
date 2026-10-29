"""
Django Channels WebSocket consumers for real-time mobile upload sessions.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class UploadSessionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.room_group_name = f"session_{self.session_id}"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        logger.info("WebSocket connected for session: %s", self.session_id)
        await self.send(text_data=json.dumps({
            "event": "CONNECTED",
            "session_id": self.session_id,
            "message": "Real-time session synchronized"
        }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info("WebSocket disconnected for session: %s", self.session_id)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get("action")
            if action == "PING":
                await self.send(text_data=json.dumps({"event": "PONG"}))
        except Exception as e:
            logger.error("Error processing WebSocket message: %s", e)

    # Handler for group_send
    async def session_event(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "event": event.get("event"),
            "data": event.get("data"),
            "message": event.get("message", "")
        }))

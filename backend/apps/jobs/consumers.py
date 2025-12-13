"""
WebSocket consumer for job progress updates.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class JobProgressConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for job progress updates.
    Subscribes to job_<job_id> channel group.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.job_id = self.scope['url_route']['kwargs']['job_id']
        self.group_name = f'job_{self.job_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave room group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle message from WebSocket."""
        # Echo back for testing (can be removed)
        data = json.loads(text_data)
        await self.send(text_data=json.dumps({
            'type': 'echo',
            'message': data
        }))
    
    async def job_event(self, event):
        """
        Receive event from group.
        This is called when emit_event() sends to the group.
        """
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event['data']))


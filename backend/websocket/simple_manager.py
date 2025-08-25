"""
Simple WebSocket Connection Manager
Basic implementation for testing WebSocket functionality
"""

import json
import asyncio
from typing import Dict, List, Any
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger


class SimpleConnectionManager:
    """Simple WebSocket connection manager for testing"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_subscriptions: Dict[str, List[str]] = {}
        
    def add_connection(self, client_id: str, websocket: WebSocket):
        """Add new WebSocket connection"""
        self.active_connections[client_id] = websocket
        self.client_subscriptions[client_id] = []
        logger.info(f"Added WebSocket connection: {client_id}")
        
    def remove_connection(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_subscriptions:
            del self.client_subscriptions[client_id]
        logger.info(f"Removed WebSocket connection: {client_id}")
        
    async def send_message(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                return False
        return False
        
    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
            
        message_text = json.dumps(message)
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message_text)
            except Exception as e:
                logger.error(f"Failed to broadcast to {client_id}: {e}")
                disconnected_clients.append(client_id)
                
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.remove_connection(client_id)
            
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
        
    def get_client_subscriptions(self, client_id: str) -> List[str]:
        """Get subscriptions for a client"""
        return self.client_subscriptions.get(client_id, [])
        
    def add_client_subscription(self, client_id: str, event: str):
        """Add subscription for a client"""
        if client_id not in self.client_subscriptions:
            self.client_subscriptions[client_id] = []
        if event not in self.client_subscriptions[client_id]:
            self.client_subscriptions[client_id].append(event)
            
    def remove_client_subscription(self, client_id: str, event: str):
        """Remove subscription for a client"""
        if client_id in self.client_subscriptions:
            if event in self.client_subscriptions[client_id]:
                self.client_subscriptions[client_id].remove(event)
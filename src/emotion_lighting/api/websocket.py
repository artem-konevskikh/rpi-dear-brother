from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json
import logging
from typing import List, Dict, Any
import time

logger = logging.getLogger("emotion_lighting")


class WebSocketManager:
    """WebSocket connection manager for real-time updates"""

    def __init__(self, emotion_tracker, touch_tracker, database):
        """Initialize the WebSocket manager

        Args:
            emotion_tracker: EmotionTracker instance
            touch_tracker: TouchTracker instance
            database: Database instance
        """
        self.emotion_tracker = emotion_tracker
        self.touch_tracker = touch_tracker
        self.database = database

        # Active WebSocket connections
        self.active_connections: List[WebSocket] = []

        # Last state - prevents sending duplicate data
        self.last_state: Dict[str, Any] = {}

        # Running flag
        self.running = False

    async def connect(self, websocket: WebSocket):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections.append(websocket)

        # Send initial state
        await self.send_personal_message(await self._get_current_state(), websocket)

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(
        self, message: Dict[str, Any], websocket: WebSocket
    ):
        """Send a message to a specific client"""
        if isinstance(message, dict):
            await websocket.send_json(message)
        else:
            await websocket.send_text(str(message))

    async def broadcast(self, message: Dict[str, Any]):
        """Send a message to all connected clients"""
        if not self.active_connections:
            return

        # Only broadcast if the state has changed
        state_str = json.dumps(message, sort_keys=True)
        last_state_str = json.dumps(self.last_state, sort_keys=True)

        if state_str != last_state_str:
            self.last_state = message
            for connection in self.active_connections:
                try:
                    await self.send_personal_message(message, connection)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    # Client might be disconnected, remove it
                    if connection in self.active_connections:
                        self.active_connections.remove(connection)

    async def _get_current_state(self) -> Dict[str, Any]:
        """Get the current system state for WebSocket responses"""
        from datetime import datetime
        import sqlite3

        emotion, confidence = self.emotion_tracker.get_current_emotion()
        touch_stats = self.touch_tracker.get_statistics()
        daily_stats = self.database.get_daily_stats()

        # Get total stats
        total_stats = self.database.get_total_stats()

        return {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "emotion": {
                "current": emotion,
                "confidence": confidence,
                "counts": daily_stats.get("emotion_counts", {}),
            },
            "touch": {
                "active_touches": touch_stats.get("active_touches", 0),
                "today_touches": touch_stats.get("today_touches", 0),
                "today_total_duration": touch_stats.get("today_total_duration", 0),
                "today_max_duration": touch_stats.get("today_max_duration", 0),
            },
            "daily_stats": {
                "avg_touch_duration": daily_stats.get("avg_touch_duration", 0),
                "max_touch_duration": daily_stats.get("max_touch_duration", 0),
                "total_touch_duration": daily_stats.get("total_touch_duration", 0),
            },
            "total_stats": total_stats,
        }

    async def websocket_endpoint(self, websocket: WebSocket):
        """WebSocket endpoint handler"""
        await self.connect(websocket)
        try:
            while True:
                # Just keep the connection alive and wait for broadcast messages
                await websocket.receive_text()
        except WebSocketDisconnect:
            self.disconnect(websocket)

    async def update_loop(self):
        """Background task for updating connected clients"""
        while self.running:
            try:
                # Get current state
                current_state = await self._get_current_state()

                # Broadcast to all clients
                await self.broadcast(current_state)

                # Efficient sleep that allows for clean shutdown
                await asyncio.sleep(
                    0.25
                )  # Update 4 times per second - adjust for Raspberry Pi

            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                await asyncio.sleep(1)  # Back off on error

    def start(self):
        """Start the WebSocket manager"""
        self.running = True

    def stop(self):
        """Stop the WebSocket manager"""
        self.running = False

from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import ujson
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import the models
from .models import SystemState, EmotionData, TouchData, DailyStats, TotalStats

logger = logging.getLogger("emotion_lighting")


class WebSocketManager:
    """WebSocket connection manager for real-time updates"""

    def __init__(
        self, emotion_tracker, touch_tracker, database, update_interval: float = 0.25
    ):
        """Initialize the WebSocket manager

        Args:
            emotion_tracker: EmotionTracker instance
            touch_tracker: TouchTracker instance
            database: Database instance
            update_interval: Time between update broadcasts in seconds (default: 0.25)
        """
        self.emotion_tracker = emotion_tracker
        self.touch_tracker = touch_tracker
        self.database = database
        self.update_interval = update_interval

        # Active WebSocket connections
        self.active_connections: List[WebSocket] = []

        # Last state - prevents sending duplicate data
        self.last_state: Dict[str, Any] = {}

        # Running flag and task reference
        self.running = False
        self._update_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket) -> None:
        """Connect a new WebSocket client and send initial state

        Args:
            websocket: The client WebSocket connection
        """
        await websocket.accept()
        self.active_connections.append(websocket)

        # Send initial state
        current_state = await self._get_current_state()
        await self._send_personal_message(current_state, websocket)
        logger.debug(
            f"New client connected. Active connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """Disconnect a WebSocket client

        Args:
            websocket: The client WebSocket connection to remove
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.debug(
                f"Client disconnected. Active connections: {len(self.active_connections)}"
            )

    async def _send_personal_message(
        self, message: Dict[str, Any], websocket: WebSocket
    ) -> None:
        """Send a message to a specific client

        Args:
            message: The message to send (as dict)
            websocket: The recipient WebSocket
        """
        try:
            if isinstance(message, dict):
                await websocket.send_json(message)
            else:
                await websocket.send_text(str(message))
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            # Client might be disconnected, remove it
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Send a message to all connected clients if state has changed

        Args:
            message: The message to broadcast to all clients
        """
        if not self.active_connections:
            return

        # Only broadcast if the state has changed
        state_str = ujson.dumps(message, sort_keys=True)
        last_state_str = ujson.dumps(self.last_state, sort_keys=True)

        if state_str != last_state_str:
            self.last_state = message.copy()  # Use copy to prevent reference issues

            # Create a list to track connections to remove
            disconnected = []

            for connection in self.active_connections:
                try:
                    await self._send_personal_message(message, connection)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    disconnected.append(connection)

            # Remove disconnected clients after iterating
            for connection in disconnected:
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

    async def _get_current_state(self) -> Dict[str, Any]:
        """Get the current system state for WebSocket responses

        Returns:
            Dict containing the current system state
        """
        try:
            emotion, confidence = self.emotion_tracker.get_current_emotion()
            
            # Handle case when touch_tracker is None (--no-touch mode)
            if self.touch_tracker:
                touch_stats = self.touch_tracker.get_statistics()
            else:
                # Provide default values when touch sensor is disabled
                touch_stats = {
                    "active_touches": 0,
                    "today_touches": 0,
                    "today_total_duration": 0,
                    "today_max_duration": 0
                }
                
            daily_stats_data = self.database.get_daily_stats()
            total_stats_data = self.database.get_total_stats()

            # Create proper model instances
            emotion_data = EmotionData(
                current=emotion,
                confidence=confidence,
                counts=daily_stats_data.get("emotion_counts", {}),
            )

            touch_data = TouchData(
                active_touches=touch_stats.get("active_touches", 0),
                today_touches=touch_stats.get("today_touches", 0),
                today_total_duration=touch_stats.get("today_total_duration", 0),
                today_max_duration=touch_stats.get("today_max_duration", 0),
            )

            daily_stats = DailyStats(
                avg_touch_duration=daily_stats_data.get("avg_touch_duration", 0),
                max_touch_duration=daily_stats_data.get("max_touch_duration", 0),
                total_touch_duration=daily_stats_data.get("total_touch_duration", 0),
            )

            # Create the total stats if data is available
            total_stats = None
            if total_stats_data:
                total_stats = TotalStats(
                    total_emotions=total_stats_data.get("total_emotions", 0),
                    dominant_emotion=total_stats_data.get("dominant_emotion", ""),
                    emotion_counts=total_stats_data.get("emotion_counts", {}),
                    total_touches=total_stats_data.get("total_touches", 0),
                    avg_touch_duration=total_stats_data.get("avg_touch_duration", 0),
                    max_touch_duration=total_stats_data.get("max_touch_duration", 0),
                    total_touch_duration=total_stats_data.get(
                        "total_touch_duration", 0
                    ),
                )

            # Create the system state using the proper model
            system_state = SystemState(
                time=datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),  # Match the format in routes.py
                emotion=emotion_data,
                touch=touch_data,
                daily_stats=daily_stats,
                total_stats=total_stats,
            )

            # Convert to dict and add client count (which isn't part of the model)
            result = system_state.dict()
            result["client_count"] = len(self.active_connections)
            return result

        except Exception as e:
            logger.error(f"Error getting current state: {e}")
            # Return a minimal state in case of error
            return {"error": str(e), "time": datetime.now().isoformat()}

    async def websocket_endpoint(self, websocket: WebSocket) -> None:
        """WebSocket endpoint handler for FastAPI routes

        Args:
            websocket: The client WebSocket connection
        """
        await self.connect(websocket)
        try:
            while True:
                # Keep connection alive and handle any incoming messages
                data = await websocket.receive_text()
                # Could process client messages here if needed
        except WebSocketDisconnect:
            self.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.disconnect(websocket)

    async def update_loop(self) -> None:
        """Background task for updating connected clients"""
        logger.info("WebSocket update loop started")
        while self.running:
            try:
                # Get current state and broadcast to all clients
                current_state = await self._get_current_state()
                await self.broadcast(current_state)

                # Efficient sleep that allows for clean shutdown
                await asyncio.sleep(self.update_interval)

            except asyncio.CancelledError:
                logger.info("Update loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                # Back off on error to prevent rapid failure loops
                await asyncio.sleep(1)

        logger.info("WebSocket update loop stopped")

    def start(self) -> None:
        """Start the WebSocket manager"""
        if self.running:
            logger.warning("WebSocket manager already running")
            return

        self.running = True
        # Create and store a reference to the task
        self._update_task = asyncio.create_task(self.update_loop())
        logger.info("WebSocket manager started")

    async def stop(self) -> None:
        """Stop the WebSocket manager gracefully"""
        logger.info("Stopping WebSocket manager...")
        self.running = False

        # Cancel update task if it exists
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
            self._update_task = None

        # Close all connections
        for connection in self.active_connections[:]:  # Make a copy to safely iterate
            try:
                await connection.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket connection: {e}")

        self.active_connections.clear()
        logger.info("WebSocket manager stopped")

from fastapi import APIRouter, HTTPException, WebSocket, status
from datetime import datetime
import logging
from functools import lru_cache

from .models import SystemState, DailyStats, TotalStats

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["emotion-lighting"])


class EmotionLightingAPI:
    """API endpoints for the Emotion Lighting system"""

    def __init__(self, emotion_tracker, touch_tracker, database, websocket_manager):
        """Initialize the API

        Args:
            emotion_tracker: EmotionTracker instance
            touch_tracker: TouchTracker instance
            database: Database instance
            websocket_manager: WebSocketManager instance
        """
        self.emotion_tracker = emotion_tracker
        self.touch_tracker = touch_tracker
        self.database = database
        self.websocket_manager = websocket_manager

        # Register routes
        self._setup_routes()

    def _setup_routes(self):
        """Set up API routes"""

        @router.get("/status", response_model=SystemState)
        async def get_status():
            """Get the current system status"""
            try:
                return await self._get_current_state()
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve system status",
                )

        @router.get("/daily-stats", response_model=DailyStats)
        async def get_daily_stats():
            """Get daily statistics"""
            try:
                # Use cached daily stats with a short TTL
                return self._get_cached_daily_stats()
            except Exception as e:
                logger.error(f"Error getting daily stats: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve daily statistics",
                )

        @router.get("/total-stats", response_model=TotalStats)
        async def get_total_stats():
            """Get total (all-time) statistics"""
            try:
                # Use cached total stats with a longer TTL
                return self._get_cached_total_stats()
            except Exception as e:
                logger.error(f"Error getting total stats: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve total statistics",
                )

        @router.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            try:
                await self.websocket_manager.websocket_endpoint(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

    @staticmethod
    def _format_datetime() -> str:
        """Format current datetime for responses"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Cache daily stats for 5 minutes (300 seconds)
    @lru_cache(maxsize=1)
    def _get_cached_daily_stats(self):
        """Get cached daily statistics with TTL"""
        # Get the current timestamp to the nearest 5 minutes to use as a cache key
        cache_key = int(datetime.now().timestamp() // 300)
        # The cache_key isn't used directly but forces a cache invalidation every 5 minutes
        return self.database.get_daily_stats()

    # Cache total stats for 15 minutes (900 seconds)
    @lru_cache(maxsize=1)
    def _get_cached_total_stats(self):
        """Get cached total statistics with TTL"""
        # Get the current timestamp to the nearest 15 minutes to use as a cache key
        cache_key = int(datetime.now().timestamp() // 900)
        # The cache_key isn't used directly but forces a cache invalidation every 15 minutes
        return self.database.get_total_stats()

    async def _get_current_state(self) -> SystemState:
        """Get the current system state for API responses"""
        # Fetch data in parallel if these were async methods
        # For now, get the data sequentially
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
            
        # Use cached daily stats for better performance
        daily_stats = self._get_cached_daily_stats()

        # Use dict.get() with default values to handle missing keys
        return SystemState(
            time=self._format_datetime(),
            emotion={
                "current": emotion,
                "confidence": confidence,
                "counts": daily_stats.get("emotion_counts", {}),
            },
            touch={
                "active_touches": touch_stats.get("active_touches", 0),
                "today_touches": touch_stats.get("today_touches", 0),
                "today_total_duration": touch_stats.get("today_total_duration", 0),
                "today_max_duration": touch_stats.get("today_max_duration", 0),
            },
            daily_stats={
                "avg_touch_duration": daily_stats.get("avg_touch_duration", 0),
                "max_touch_duration": daily_stats.get("max_touch_duration", 0),
                "total_touch_duration": daily_stats.get("total_touch_duration", 0),
            },
        )

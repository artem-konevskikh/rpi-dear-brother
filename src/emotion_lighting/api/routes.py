from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Any
from datetime import datetime

from .models import SystemState, TotalStats

# Create router
router = APIRouter(prefix="/api", tags=["emotion-lighting"])


class EmotionLightingAPI:
    """API endpoints for the Emotion Lighting system"""

    def __init__(self, emotion_tracker, touch_tracker, database):
        """Initialize the API

        Args:
            emotion_tracker: EmotionTracker instance
            touch_tracker: TouchTracker instance
            database: Database instance
        """
        self.emotion_tracker = emotion_tracker
        self.touch_tracker = touch_tracker
        self.database = database

        # Register routes
        self._setup_routes()

    def _setup_routes(self):
        """Set up API routes"""

        @router.get("/status", response_model=SystemState)
        async def get_status():
            """Get the current system status"""
            return await self._get_current_state()

        @router.get("/daily-stats", response_model=Dict[str, Any])
        async def get_daily_stats():
            """Get daily statistics"""
            daily_stats = self.database.get_daily_stats()
            return daily_stats

        @router.get("/total-stats", response_model=Dict[str, Any])
        async def get_total_stats():
            """Get total (all-time) statistics"""
            # Use the database method to get total stats
            total_stats = self.database.get_total_stats()
            return total_stats

    async def _get_current_state(self) -> SystemState:
        """Get the current system state for API responses"""
        emotion, confidence = self.emotion_tracker.get_current_emotion()
        touch_stats = self.touch_tracker.get_statistics()
        daily_stats = self.database.get_daily_stats()

        return SystemState(
            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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

    def _get_all_emotions(self):
        """Get all emotion records from the database"""
        conn = self.database._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT emotion, confidence, duration FROM emotion_events")
        emotions = cursor.fetchall()
        conn.close()
        return emotions

    def _get_all_touches(self):
        """Get all touch records from the database"""
        conn = self.database._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT electrode, duration FROM touch_events")
        touches = cursor.fetchall()
        conn.close()
        return touches

    def _get_dominant_emotion(self, emotions):
        """Calculate the dominant emotion from all records"""
        if not emotions:
            return "neutral"

        counts = {}
        for emotion, _, _ in emotions:
            counts[emotion] = counts.get(emotion, 0) + 1

        # Find emotion with highest count
        return max(counts.items(), key=lambda x: x[1])[0] if counts else "neutral"

    def _count_emotions(self, emotions):
        """Count occurrences of each emotion"""
        counts = {}
        for emotion, _, _ in emotions:
            counts[emotion] = counts.get(emotion, 0) + 1
        return counts

    def _calculate_avg_duration(self, touches):
        """Calculate average touch duration"""
        if not touches:
            return 0.0
        total_duration = sum(duration for _, duration in touches)
        return total_duration / len(touches)

    def _calculate_max_duration(self, touches):
        """Calculate maximum touch duration"""
        if not touches:
            return 0.0
        return max(duration for _, duration in touches)

    def _calculate_total_duration(self, touches):
        """Calculate total touch duration"""
        if not touches:
            return 0.0
        return sum(duration for _, duration in touches)

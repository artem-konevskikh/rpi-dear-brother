from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime


class EmotionData(BaseModel):
    """Model for emotion data"""

    current: str = Field(..., description="Current detected emotion")
    confidence: float = Field(..., description="Confidence level of emotion detection")
    counts: Dict[str, int] = Field(
        default_factory=dict, description="Counts of emotions for the day"
    )


class TouchData(BaseModel):
    """Model for touch interaction data"""

    active_touches: int = Field(..., description="Currently active touches")
    today_touches: int = Field(..., description="Total touches today")
    today_total_duration: float = Field(..., description="Total touch duration today")
    today_max_duration: float = Field(..., description="Maximum touch duration today")


class DailyStats(BaseModel):
    """Model for daily statistics"""

    avg_touch_duration: float = Field(..., description="Average touch duration")
    max_touch_duration: float = Field(..., description="Maximum touch duration")
    total_touch_duration: float = Field(..., description="Total touch duration")


class SystemState(BaseModel):
    """Model for the complete system state"""

    time: str = Field(..., description="Current system time")
    emotion: EmotionData
    touch: TouchData
    daily_stats: DailyStats


class TotalStats(BaseModel):
    """Model for total statistics (all-time)"""

    total_emotions: int
    dominant_emotion: str
    emotion_counts: Dict[str, int]
    total_touches: int
    avg_touch_duration: float
    max_touch_duration: float
    total_touch_duration: float

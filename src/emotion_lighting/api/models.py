from pydantic import BaseModel, Field
from typing import Dict, Optional

# Removed unused imports: List, Any, datetime


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


class TotalStats(BaseModel):
    """Model for total statistics (all-time)"""

    total_emotions: int = Field(
        ..., description="Total number of emotion events recorded"
    )
    dominant_emotion: str = Field(..., description="Most frequently detected emotion")
    emotion_counts: Dict[str, int] = Field(
        ..., description="Count of each emotion type"
    )
    total_touches: int = Field(..., description="Total number of touch interactions")
    avg_touch_duration: float = Field(
        ..., description="Average duration of all touches"
    )
    max_touch_duration: float = Field(
        ..., description="Maximum touch duration recorded"
    )
    total_touch_duration: float = Field(
        ..., description="Total accumulated touch duration"
    )


class SystemState(BaseModel):
    """Model for the complete system state"""

    time: str = Field(..., description="Current system time")
    emotion: EmotionData = Field(..., description="Current emotion data")
    touch: TouchData = Field(..., description="Current touch data")
    daily_stats: DailyStats = Field(..., description="Statistics for today")
    total_stats: Optional[TotalStats] = Field(
        None, description="Total system statistics"
    )

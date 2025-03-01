import sqlite3
import time
import datetime
import threading
from collections import Counter


class EmotionDatabase:
    """Database for storing emotion and touch data"""

    def __init__(self, db_path="emotion_data.db"):
        """Initialize the database

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.lock = threading.Lock()
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Emotion events table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS emotion_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                emotion TEXT NOT NULL,
                confidence REAL NOT NULL,
                duration REAL NOT NULL
            )
            """)

            # Touch events table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS touch_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                electrode INTEGER NOT NULL,
                duration REAL NOT NULL
            )
            """)

            # Daily statistics table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                date TEXT PRIMARY KEY,
                dominant_emotion TEXT NOT NULL,
                emotion_counts TEXT NOT NULL,
                touch_count INTEGER NOT NULL,
                avg_touch_duration REAL NOT NULL,
                max_touch_duration REAL NOT NULL,
                total_touch_duration REAL NOT NULL
            )
            """)

            conn.commit()
            conn.close()

    def log_emotion(self, emotion, confidence, duration):
        """Log an emotion event to the database

        Args:
            emotion: Detected emotion
            confidence: Confidence level (0-1)
            duration: Duration in seconds
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            timestamp = time.time()
            cursor.execute(
                "INSERT INTO emotion_events (timestamp, emotion, confidence, duration) VALUES (?, ?, ?, ?)",
                (timestamp, emotion, confidence, duration),
            )

            conn.commit()
            conn.close()

    def log_touch(self, electrode, duration):
        """Log a touch event to the database

        Args:
            electrode: Electrode number
            duration: Duration in seconds
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            timestamp = time.time()
            cursor.execute(
                "INSERT INTO touch_events (timestamp, electrode, duration) VALUES (?, ?, ?)",
                (timestamp, electrode, duration),
            )

            conn.commit()
            conn.close()

    def update_daily_stats(self):
        """Update daily statistics in the database"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get today's timestamp range
            today_start = datetime.datetime.combine(
                datetime.datetime.now().date(), datetime.time.min
            ).timestamp()

            today_end = datetime.datetime.combine(
                datetime.datetime.now().date(), datetime.time.max
            ).timestamp()

            # Get emotion data for today
            cursor.execute(
                "SELECT emotion FROM emotion_events WHERE timestamp BETWEEN ? AND ?",
                (today_start, today_end),
            )
            emotions = [row[0] for row in cursor.fetchall()]

            # Count emotions and find dominant
            emotion_counts = Counter(emotions)
            dominant_emotion = (
                emotion_counts.most_common(1)[0][0] if emotion_counts else "neutral"
            )

            # Get touch data for today
            cursor.execute(
                "SELECT duration FROM touch_events WHERE timestamp BETWEEN ? AND ?",
                (today_start, today_end),
            )
            touch_durations = [row[0] for row in cursor.fetchall()]

            # Calculate touch statistics
            touch_count = len(touch_durations)
            avg_touch_duration = (
                sum(touch_durations) / touch_count if touch_count > 0 else 0
            )
            max_touch_duration = max(touch_durations) if touch_count > 0 else 0
            total_touch_duration = sum(touch_durations)

            # Store daily stats
            cursor.execute(
                """
                INSERT OR REPLACE INTO daily_stats 
                (date, dominant_emotion, emotion_counts, touch_count, 
                avg_touch_duration, max_touch_duration, total_touch_duration)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    today,
                    dominant_emotion,
                    str(dict(emotion_counts)),
                    touch_count,
                    avg_touch_duration,
                    max_touch_duration,
                    total_touch_duration,
                ),
            )

            conn.commit()
            conn.close()

    def get_daily_stats(self, date=None):
        """Get statistics for a specific day

        Args:
            date: Date string in YYYY-MM-DD format, or None for today

        Returns:
            dict: Daily statistics
        """
        if date is None:
            date = datetime.datetime.now().strftime("%Y-%m-%d")

        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM daily_stats WHERE date = ?", (date,))

            row = cursor.fetchone()

            if row:
                # Parse the emotion_counts string back to a dictionary
                emotion_counts_str = row[2]
                # Safely evaluate the string representation of the dictionary
                emotion_counts = eval(emotion_counts_str)

                stats = {
                    "date": row[0],
                    "dominant_emotion": row[1],
                    "emotion_counts": emotion_counts,
                    "touch_count": row[3],
                    "avg_touch_duration": row[4],
                    "max_touch_duration": row[5],
                    "total_touch_duration": row[6],
                }
            else:
                stats = {
                    "date": date,
                    "dominant_emotion": "neutral",
                    "emotion_counts": {},
                    "touch_count": 0,
                    "avg_touch_duration": 0,
                    "max_touch_duration": 0,
                    "total_touch_duration": 0,
                }

            conn.close()

            return stats

    def get_all_stats(self, days=7):
        """Get statistics for the last N days

        Args:
            days: Number of days to retrieve

        Returns:
            list: List of daily statistics dictionaries
        """
        stats_list = []

        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Calculate date range
            end_date = datetime.datetime.now().date()
            start_date = end_date - datetime.timedelta(days=days - 1)

            for i in range(days):
                current_date = start_date + datetime.timedelta(days=i)
                date_str = current_date.strftime("%Y-%m-%d")

                cursor.execute("SELECT * FROM daily_stats WHERE date = ?", (date_str,))

                row = cursor.fetchone()

                if row:
                    # Parse the emotion_counts string back to a dictionary
                    emotion_counts_str = row[2]
                    # Safely evaluate the string representation of the dictionary
                    emotion_counts = eval(emotion_counts_str)

                    stats = {
                        "date": row[0],
                        "dominant_emotion": row[1],
                        "emotion_counts": emotion_counts,
                        "touch_count": row[3],
                        "avg_touch_duration": row[4],
                        "max_touch_duration": row[5],
                        "total_touch_duration": row[6],
                    }
                else:
                    stats = {
                        "date": date_str,
                        "dominant_emotion": "neutral",
                        "emotion_counts": {},
                        "touch_count": 0,
                        "avg_touch_duration": 0,
                        "max_touch_duration": 0,
                        "total_touch_duration": 0,
                    }

                stats_list.append(stats)

            conn.close()

            return stats_list

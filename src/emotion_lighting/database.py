import sqlite3
import time
import datetime
import threading
from collections import Counter
import ast


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

    def _get_connection(self):
        """Get a database connection

        Returns:
            sqlite3.Connection: Database connection
        """
        return sqlite3.connect(self.db_path)

    def _get_connection_context(self):
        """Get a database connection as a context manager"""
        class ConnectionContext:
            def __init__(self, db_path):
                self.db_path = db_path
                self.conn = None
                
            def __enter__(self):
                self.conn = sqlite3.connect(self.db_path)
                return self.conn
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.conn:
                    self.conn.commit()
                    self.conn.close()
                    
        return ConnectionContext(self.db_path)

    def _create_tables(self):
        """Create database tables if they don't exist"""
        with self.lock, self._get_connection_context() as conn:
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

            # Create indexes for faster queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_emotion_events_timestamp ON emotion_events(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_touch_events_timestamp ON touch_events(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_emotion_events_emotion ON emotion_events(emotion)")

    def log_emotion(self, emotion, confidence, duration):
        """Log an emotion event to the database

        Args:
            emotion: Detected emotion
            confidence: Confidence level (0-1)
            duration: Duration in seconds
        """
        timestamp = time.time()
        
        with self.lock, self._get_connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO emotion_events (timestamp, emotion, confidence, duration) VALUES (?, ?, ?, ?)",
                (timestamp, emotion, confidence, duration),
            )

    def log_touch(self, electrode, duration):
        """Log a touch event to the database

        Args:
            electrode: Electrode number
            duration: Duration in seconds
        """
        timestamp = time.time()
        
        with self.lock, self._get_connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO touch_events (timestamp, electrode, duration) VALUES (?, ?, ?)",
                (timestamp, electrode, duration),
            )

    def _get_date_range(self, date=None):
        """Helper method to get timestamp range for a date
        
        Args:
            date: Optional datetime.date object, defaults to today
            
        Returns:
            tuple: (start_timestamp, end_timestamp)
        """
        if date is None:
            date = datetime.datetime.now().date()
        elif isinstance(date, str):
            date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
            
        start_timestamp = datetime.datetime.combine(date, datetime.time.min).timestamp()
        end_timestamp = datetime.datetime.combine(date, datetime.time.max).timestamp()
        return start_timestamp, end_timestamp

    def update_daily_stats(self):
        """Update daily statistics in the database with optimized queries"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        today_start, today_end = self._get_date_range()

        with self.lock, self._get_connection_context() as conn:
            cursor = conn.cursor()

            # Get emotion counts with a single query
            cursor.execute(
                """
                SELECT emotion, COUNT(*) as count 
                FROM emotion_events 
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY emotion
                """,
                (today_start, today_end),
            )
            emotion_data = cursor.fetchall()
            emotion_counts = {emotion: count for emotion, count in emotion_data}

            # Find dominant emotion
            dominant_emotion = "neutral"
            max_count = 0
            for emotion, count in emotion_counts.items():
                if count > max_count:
                    max_count = count
                    dominant_emotion = emotion

            # Get touch statistics with aggregation in SQL
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as touch_count,
                    AVG(duration) as avg_duration,
                    MAX(duration) as max_duration,
                    SUM(duration) as total_duration
                FROM touch_events 
                WHERE timestamp BETWEEN ? AND ?
                """,
                (today_start, today_end),
            )
            touch_stats = cursor.fetchone()

            touch_count = touch_stats[0] or 0
            avg_touch_duration = touch_stats[1] or 0
            max_touch_duration = touch_stats[2] or 0
            total_touch_duration = touch_stats[3] or 0

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

    def get_daily_stats(self, date=None):
        """Get statistics for a specific day

        Args:
            date: Date string in YYYY-MM-DD format, or None for today

        Returns:
            dict: Daily statistics
        """
        if date is None:
            date = datetime.datetime.now().strftime("%Y-%m-%d")

        with self.lock, self._get_connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM daily_stats WHERE date = ?", (date,))
            row = cursor.fetchone()

            if row:
                try:
                    # Parse the emotion_counts string back to a dictionary
                    emotion_counts_str = row[2]
                    # Use ast.literal_eval for safer dictionary parsing
                    emotion_counts = ast.literal_eval(emotion_counts_str)
                    
                    stats = {
                        "date": row[0],
                        "dominant_emotion": row[1],
                        "emotion_counts": emotion_counts,
                        "touch_count": row[3],
                        "avg_touch_duration": row[4],
                        "max_touch_duration": row[5],
                        "total_touch_duration": row[6],
                    }
                except (SyntaxError, ValueError) as e:
                    # Fallback if parsing fails
                    stats = {
                        "date": row[0],
                        "dominant_emotion": row[1],
                        "emotion_counts": {},
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

            return stats

    def get_all_stats(self, days=7):
        """Get statistics for the last N days

        Args:
            days: Number of days to retrieve

        Returns:
            list: List of daily statistics dictionaries
        """
        # Calculate date range
        end_date = datetime.datetime.now().date()
        start_date = end_date - datetime.timedelta(days=days - 1)
        date_range = [(start_date + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
        
        with self.lock, self._get_connection_context() as conn:
            cursor = conn.cursor()
            
            # Fetch all available stats for the date range in a single query
            placeholders = ",".join(["?"] * len(date_range))
            cursor.execute(
                f"SELECT * FROM daily_stats WHERE date IN ({placeholders}) ORDER BY date",
                date_range
            )
            rows = cursor.fetchall()
            
            # Convert to dictionary for easy lookup
            stats_dict = {}
            for row in rows:
                try:
                    emotion_counts = ast.literal_eval(row[2])
                except (SyntaxError, ValueError):
                    emotion_counts = {}
                    
                stats_dict[row[0]] = {
                    "date": row[0],
                    "dominant_emotion": row[1],
                    "emotion_counts": emotion_counts,
                    "touch_count": row[3],
                    "avg_touch_duration": row[4],
                    "max_touch_duration": row[5],
                    "total_touch_duration": row[6],
                }
            
            # Create the final list with default values for missing dates
            stats_list = []
            for date_str in date_range:
                if date_str in stats_dict:
                    stats_list.append(stats_dict[date_str])
                else:
                    stats_list.append({
                        "date": date_str,
                        "dominant_emotion": "neutral",
                        "emotion_counts": {},
                        "touch_count": 0,
                        "avg_touch_duration": 0,
                        "max_touch_duration": 0,
                        "total_touch_duration": 0,
                    })
            
            return stats_list

    def get_total_stats(self):
        """Get total statistics with optimized queries"""
        with self.lock, self._get_connection_context() as conn:
            cursor = conn.cursor()

            # Get emotion data in a single query
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM emotion_events) as total_emotions,
                    e.emotion as dominant_emotion
                FROM (
                    SELECT emotion, COUNT(*) as count
                    FROM emotion_events
                    GROUP BY emotion
                    ORDER BY count DESC
                    LIMIT 1
                ) e
            """)

            result = cursor.fetchone()
            total_emotions = result[0] if result and result[0] is not None else 0
            dominant_emotion = result[1] if result and result[1] is not None else "neutral"

            # Get emotion counts
            cursor.execute(
                "SELECT emotion, COUNT(*) FROM emotion_events GROUP BY emotion"
            )
            emotion_data = cursor.fetchall()
            emotion_counts = {emotion: count for emotion, count in emotion_data}

            # Get touch data with a single query
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_touches,
                    AVG(duration) as avg_duration,
                    MAX(duration) as max_duration,
                    SUM(duration) as total_duration
                FROM touch_events
            """)

            touch_stats = cursor.fetchone()
            total_touches = touch_stats[0] if touch_stats and touch_stats[0] is not None else 0
            avg_touch_duration = touch_stats[1] if touch_stats and touch_stats[1] is not None else 0
            max_touch_duration = touch_stats[2] if touch_stats and touch_stats[2] is not None else 0
            total_touch_duration = touch_stats[3] if touch_stats and touch_stats[3] is not None else 0

            return {
                "total_emotions": total_emotions,
                "dominant_emotion": dominant_emotion,
                "emotion_counts": emotion_counts,
                "total_touches": total_touches,
                "avg_touch_duration": avg_touch_duration,
                "max_touch_duration": max_touch_duration,
                "total_touch_duration": total_touch_duration,
            }

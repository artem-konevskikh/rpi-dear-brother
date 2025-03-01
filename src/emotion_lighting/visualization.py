import cv2
import numpy as np
import threading
import time
import datetime


class Visualization:
    """Minimalist sci-fi UI for displaying emotion and statistics"""

    # Emotion pictograms with corresponding colors (BGR for OpenCV)
    EMOTION_ICONS = {
        "happy": {
            "color": (0, 255, 255),
            "eyes": [(185, 175), (255, 175)],
            "mouth": [(170, 220), (220, 260), (270, 220)],
        },
        "sad": {
            "color": (255, 0, 0),
            "eyes": [(185, 175), (255, 175)],
            "mouth": [(170, 230), (220, 190), (270, 230)],
        },
        "angry": {
            "color": (0, 0, 255),
            "eyes": [(185, 175), (255, 175)],
            "mouth": [(190, 230), (220, 220), (250, 230)],
        },
        "neutral": {
            "color": (255, 255, 255),
            "eyes": [(185, 175), (255, 175)],
            "mouth": [(190, 220), (250, 220)],
        },
        "fear": {
            "color": (128, 0, 128),
            "eyes": [(185, 175), (255, 175)],
            "mouth": [(190, 210), (220, 200), (250, 210)],
        },
        "surprise": {
            "color": (255, 255, 0),
            "eyes": [(185, 165), (255, 165)],
            "mouth": [(220, 240), (220, 240), (220, 240)],
        },
        "disgust": {
            "color": (0, 128, 0),
            "eyes": [(185, 175), (255, 175)],
            "mouth": [(170, 210), (220, 220), (270, 210)],
        },
    }

    # All supported emotions for the chart
    ALL_EMOTIONS = ["happy", "sad", "angry", "neutral", "fear", "surprise"]

    def __init__(
        self,
        emotion_tracker,
        touch_tracker,
        database,
        window_name="EMOTION LIGHTING SYSTEM",
    ):
        """Initialize the visualization

        Args:
            emotion_tracker: EmotionTracker instance
            touch_tracker: TouchTracker instance
            database: Database instance
            window_name: Name of the window
        """
        self.emotion_tracker = emotion_tracker
        self.touch_tracker = touch_tracker
        self.database = database
        self.window_name = window_name

        # Set up the canvas
        self.canvas_width = 800
        self.canvas_height = 600

        # Visualization state
        self.running = False
        self.lock = threading.Lock()

    def start(self):
        """Start the visualization"""
        if self.running:
            return

        self.running = True

        # Create window
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.canvas_width, self.canvas_height)

        # Main visualization loop
        try:
            while self.running:
                # Create and display visualization frame
                frame = self._create_visualization()
                cv2.imshow(self.window_name, frame)

                # Check for key presses (q to quit)
                key = cv2.waitKey(100) & 0xFF
                if key == ord("q"):
                    self.running = False

                # Sleep to reduce CPU usage
                time.sleep(0.1)
        finally:
            cv2.destroyAllWindows()

    def stop(self):
        """Stop the visualization"""
        self.running = False

    def _create_visualization(self):
        """Create visualization frame

        Returns:
            numpy.ndarray: Image frame for display
        """
        # Create a black canvas
        canvas = np.zeros((self.canvas_height, self.canvas_width, 3), dtype=np.uint8)

        # Draw grid pattern
        self._draw_grid(canvas)

        # Draw hexagonal border
        self._draw_hexagonal_border(canvas)

        # Draw sections
        self._draw_section_dividers(canvas)
        self._draw_section_titles(canvas)

        # Draw content
        self._draw_emotion_section(canvas)
        self._draw_touch_section(canvas)
        self._draw_emotion_chart(canvas)
        self._draw_touch_metrics(canvas)

        # Draw system time
        self._draw_system_time(canvas)

        return canvas

    def _draw_grid(self, canvas):
        """Draw grid pattern for sci-fi effect

        Args:
            canvas: Canvas to draw on
        """
        # Draw small grid
        for x in range(0, self.canvas_width, 10):
            cv2.line(canvas, (x, 0), (x, self.canvas_height), (24, 24, 24), 1)

        for y in range(0, self.canvas_height, 10):
            cv2.line(canvas, (0, y), (self.canvas_width, y), (24, 24, 24), 1)

        # Draw larger grid
        for x in range(0, self.canvas_width, 100):
            cv2.line(canvas, (x, 0), (x, self.canvas_height), (32, 32, 32), 1)

        for y in range(0, self.canvas_height, 100):
            cv2.line(canvas, (0, y), (self.canvas_width, y), (32, 32, 32), 1)

    def _draw_hexagonal_border(self, canvas):
        """Draw hexagonal border around the interface

        Args:
            canvas: Canvas to draw on
        """
        points = np.array(
            [[50, 50], [750, 50], [780, 300], [750, 550], [50, 550], [20, 300]],
            np.int32,
        )

        points = points.reshape((-1, 1, 2))
        cv2.polylines(canvas, [points], True, (64, 64, 64), 2)

    def _draw_section_dividers(self, canvas):
        """Draw section dividers

        Args:
            canvas: Canvas to draw on
        """
        # Vertical divider
        cv2.line(canvas, (400, 70), (400, 530), (64, 64, 64), 1)

        # Horizontal divider
        cv2.line(canvas, (100, 300), (700, 300), (64, 64, 64), 1)

    def _draw_section_titles(self, canvas):
        """Draw section titles with rectangular borders

        Args:
            canvas: Canvas to draw on
        """
        # Interface title
        cv2.putText(
            canvas,
            self.window_name,
            (400, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        cv2.line(canvas, (250, 50), (550, 50), (64, 64, 64), 1)

        # Define section titles and positions
        sections = [
            {"title": "CURRENT EMOTION", "x": 220, "y": 100, "left": 80, "right": 360},
            {
                "title": "INTERACTION DATA",
                "x": 580,
                "y": 100,
                "left": 440,
                "right": 720,
            },
            {"title": "EMOTION TRACKING", "x": 220, "y": 340, "left": 80, "right": 360},
            {"title": "SYSTEM STATUS", "x": 580, "y": 340, "left": 440, "right": 720},
        ]

        # Draw each section title with rectangular border
        for section in sections:
            # Draw rectangular border
            cv2.rectangle(
                canvas,
                (section["left"], section["y"] - 20),
                (section["right"], section["y"] + 10),
                (85, 85, 85),
                1,
            )

            # Draw title text
            cv2.putText(
                canvas,
                section["title"],
                (section["x"], section["y"]),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

    def _draw_emotion_section(self, canvas):
        """Draw the emotion pictogram section

        Args:
            canvas: Canvas to draw on
        """
        # Get current emotion
        emotion, _ = self.emotion_tracker.get_current_emotion()

        # Default to neutral if emotion is not recognized
        if emotion not in self.EMOTION_ICONS:
            emotion = "neutral"

        # Get icon and color
        icon_data = self.EMOTION_ICONS[emotion]
        color = icon_data["color"]

        # Draw colored face circle
        cv2.circle(canvas, (220, 200), 70, color, -1)  # Filled circle

        # Draw eyes (black circles)
        for eye_pos in icon_data["eyes"]:
            cv2.circle(canvas, eye_pos, 12, (0, 0, 0), -1)

        # Draw mouth
        if len(icon_data["mouth"]) == 2:  # Straight line for neutral
            cv2.line(canvas, icon_data["mouth"][0], icon_data["mouth"][1], (0, 0, 0), 5)
        else:  # Curve for other emotions
            pts = np.array(icon_data["mouth"], np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(canvas, [pts], False, (0, 0, 0), 5)

        # Draw emotion name
        cv2.putText(
            canvas,
            emotion.upper(),
            (220, 290),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

    def _draw_touch_section(self, canvas):
        """Draw the touch interaction section

        Args:
            canvas: Canvas to draw on
        """
        # Get touch statistics
        touch_stats = self.touch_tracker.get_statistics()

        # Draw hexagonal touch count display
        center_x, center_y = 580, 190
        size = 70

        # Create hexagon points
        hex_points = []
        for i in range(6):
            angle_deg = 60 * i - 30
            angle_rad = np.pi / 180 * angle_deg
            x = center_x + size * np.cos(angle_rad)
            y = center_y + size * np.sin(angle_rad)
            hex_points.append((int(x), int(y)))

        # Draw hexagon
        points = np.array(hex_points, np.int32)
        points = points.reshape((-1, 1, 2))
        cv2.polylines(canvas, [points], True, (102, 102, 102), 2)

        # Draw touch count label
        cv2.putText(
            canvas,
            "TOUCHES",
            (center_x, center_y - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        # Draw touch count
        cv2.putText(
            canvas,
            str(touch_stats["today_touches"]),
            (center_x, center_y + 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        # Draw "TODAY" label
        cv2.putText(
            canvas,
            "TODAY",
            (center_x, center_y + 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (153, 153, 153),
            1,
            cv2.LINE_AA,
        )

    def _draw_emotion_chart(self, canvas):
        """Draw the emotion distribution bar chart

        Args:
            canvas: Canvas to draw on
        """
        # Get daily stats
        stats = self.database.get_daily_stats()

        # Title
        cv2.putText(
            canvas,
            "DAILY EMOTION PROFILE",
            (220, 440),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        # Get emotion counts
        emotion_counts = stats["emotion_counts"]
        max_count = (
            max(emotion_counts.values()) if emotion_counts else 1
        )  # Avoid division by zero

        # Draw 6 emotion bars
        bar_width = 40
        bar_height = 70
        bar_spacing = 10
        start_x = 120  # Adjusted to center the 6 bars

        for i, emotion in enumerate(self.ALL_EMOTIONS):
            x = start_x + i * (bar_width + bar_spacing)
            y = 450

            # Get count for this emotion (0 if not present)
            count = emotion_counts.get(emotion, 0)

            # Calculate height proportion
            height_proportion = count / max_count if max_count > 0 else 0
            bar_value_height = int(bar_height * height_proportion)

            # Draw bar outline
            cv2.rectangle(
                canvas, (x, y), (x + bar_width, y + bar_height), (68, 68, 68), 1
            )

            # Draw filled portion of bar
            if bar_value_height > 0:
                cv2.rectangle(
                    canvas,
                    (x, y + bar_height - bar_value_height),
                    (x + bar_width, y + bar_height),
                    (51, 51, 51),
                    -1,
                )

            # Draw emotion label
            cv2.putText(
                canvas,
                emotion[:3].upper(),
                (x + bar_width // 2, y + bar_height + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

    def _draw_touch_metrics(self, canvas):
        """Draw touch metrics section

        Args:
            canvas: Canvas to draw on
        """
        # Get touch statistics
        touch_stats = self.touch_tracker.get_statistics()

        # Get daily stats
        stats = self.database.get_daily_stats()

        # Title
        cv2.putText(
            canvas,
            "TOUCH METRICS",
            (580, 440),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        # Metrics list
        metrics = [
            {"label": "AVG DURATION:", "value": f"{stats['avg_touch_duration']:.1f}s"},
            {"label": "MAX DURATION:", "value": f"{stats['max_touch_duration']:.1f}s"},
            {"label": "TOTAL TIME:", "value": f"{stats['total_touch_duration']:.1f}s"},
        ]

        # Draw metrics
        y = 470
        for metric in metrics:
            # Label (left-aligned)
            cv2.putText(
                canvas,
                metric["label"],
                (490, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (170, 170, 170),
                1,
                cv2.LINE_AA,
            )

            # Value (right-aligned)
            cv2.putText(
                canvas,
                metric["value"],
                (670, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

            y += 20

    def _draw_system_time(self, canvas):
        """Draw system time at the bottom

        Args:
            canvas: Canvas to draw on
        """
        # Get current time
        now = datetime.datetime.now()
        time_str = f"SYS: {now.strftime('%Y-%m-%d | %H:%M:%S')}"

        cv2.putText(
            canvas,
            time_str,
            (400, 570),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (153, 153, 153),
            1,
            cv2.LINE_AA,
        )

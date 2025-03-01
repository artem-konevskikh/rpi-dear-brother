import dearpygui.dearpygui as dpg
import datetime
import time
import threading
import math


class DearPyGuiVisualization:
    """Minimalist sci-fi UI for displaying emotion and statistics using Dear PyGui"""

    # Emotion data with corresponding colors (RGB for Dear PyGui)
    EMOTION_DATA = {
        "happy": {"color": (255, 255, 0), "mouth_curve": 0.5},  # Smile
        "sad": {"color": (0, 0, 255), "mouth_curve": -0.5},  # Frown
        "angry": {"color": (255, 0, 0), "mouth_curve": -0.2},  # Slight frown with bent
        "neutral": {"color": (255, 255, 255), "mouth_curve": 0.0},  # Straight line
        "fear": {"color": (128, 0, 128), "mouth_curve": -0.3},  # Slight wary frown
        "surprise": {
            "color": (0, 255, 255),
            "mouth_curve": 0.0,
            "mouth_open": True,
        },  # Open mouth
        "disgust": {"color": (0, 128, 0), "mouth_curve": -0.3},  # Frown with bent
    }

    # All emotions to display in chart
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

        # Window dimensions
        self.window_width = 800
        self.window_height = 600

        # State management
        self.running = False
        self.lock = threading.Lock()

        # Current state
        self.current_emotion = "neutral"
        self.touch_stats = {
            "today_touches": 0,
            "today_total_duration": 0,
            "today_max_duration": 0,
        }
        self.emotion_counts = {}
        self.daily_stats = {
            "avg_touch_duration": 0.0,
            "max_touch_duration": 0.0,
            "total_touch_duration": 0.0,
        }

    def start(self):
        """Start the visualization"""
        if self.running:
            return

        self.running = True

        # Initialize Dear PyGui
        dpg.create_context()

        # Create fonts
        with dpg.font_registry():
            # Load default font at different sizes
            self.default_font = dpg.add_font("C:/Windows/Fonts/consola.ttf", 16)
            self.title_font = dpg.add_font("C:/Windows/Fonts/consola.ttf", 20)
            self.large_font = dpg.add_font("C:/Windows/Fonts/consola.ttf", 40)

        # Create viewport
        dpg.create_viewport(
            title=self.window_name, width=self.window_width, height=self.window_height
        )
        dpg.set_viewport_vsync(True)

        # Main window
        with dpg.window(
            label=self.window_name,
            width=self.window_width,
            height=self.window_height,
            no_title_bar=True,
            no_resize=True,
            no_move=True,
            no_scrollbar=True,
            no_collapse=True,
        ):
            # Setup theme for dark sci-fi look
            self._setup_theme()

            # Create main elements
            with dpg.drawlist(width=self.window_width, height=self.window_height):
                # These will be updated in the update function
                self.background_id = dpg.add_draw_layer()
                self.main_content_id = dpg.add_draw_layer()

            # Create update timer
            with dpg.handler_registry():
                dpg.add_mouse_click_handler(
                    callback=lambda: None
                )  # Dummy to keep window responsive

        # Set the refresh callback
        dpg.set_viewport_resize_callback(self._on_resize)

        # Setup and start the interface
        dpg.setup_dearpygui()
        dpg.show_viewport()

        # Start update thread
        self.update_thread = threading.Thread(target=self._update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()

        # Start rendering
        try:
            while dpg.is_dearpygui_running() and self.running:
                dpg.render_dearpygui_frame()
        finally:
            self.running = False
            dpg.destroy_context()

    def stop(self):
        """Stop the visualization"""
        self.running = False

    def _setup_theme(self):
        """Setup theme for sci-fi look"""
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                # Background color
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (8, 8, 8, 255))
                # Text color
                dpg.add_theme_color(dpg.mvThemeCol_Text, (220, 220, 220, 255))
                # Border color
                dpg.add_theme_color(dpg.mvThemeCol_Border, (64, 64, 64, 255))
                # Disable title bar padding
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0, 0)
                dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 0, 0)

        dpg.bind_theme(global_theme)

    def _update_loop(self):
        """Background thread to update data and redraw UI"""
        while self.running:
            # Get current data
            self._update_data()

            # Update the UI
            dpg.delete_item(self.background_id, children_only=True)
            dpg.delete_item(self.main_content_id, children_only=True)

            with dpg.mutex():
                # Draw background
                with dpg.draw_node(tag=self.background_id):
                    self._draw_background()

                # Draw content
                with dpg.draw_node(tag=self.main_content_id):
                    self._draw_main_content()

            # Update every 100ms
            time.sleep(0.1)

    def _update_data(self):
        """Update data from trackers and database"""
        with self.lock:
            # Get current emotion
            emotion, _ = self.emotion_tracker.get_current_emotion()
            self.current_emotion = (
                emotion if emotion in self.EMOTION_DATA else "neutral"
            )

            # Get touch statistics
            self.touch_stats = self.touch_tracker.get_statistics()

            # Get daily stats
            daily_stats = self.database.get_daily_stats()
            self.emotion_counts = daily_stats["emotion_counts"]

            self.daily_stats = {
                "avg_touch_duration": daily_stats["avg_touch_duration"],
                "max_touch_duration": daily_stats["max_touch_duration"],
                "total_touch_duration": daily_stats["total_touch_duration"],
            }

    def _draw_background(self):
        """Draw the background with grid and hexagonal border"""
        # Draw grid pattern
        # Small grid
        for x in range(0, self.window_width, 10):
            dpg.draw_line((x, 0), (x, self.window_height), color=(24, 24, 24))

        for y in range(0, self.window_height, 10):
            dpg.draw_line((0, y), (self.window_width, y), color=(24, 24, 24))

        # Larger grid
        for x in range(0, self.window_width, 100):
            dpg.draw_line((x, 0), (x, self.window_height), color=(32, 32, 32))

        for y in range(0, self.window_height, 100):
            dpg.draw_line((0, y), (self.window_width, y), color=(32, 32, 32))

        # Draw hexagonal border
        points = [
            (50, 50),
            (750, 50),
            (780, 300),
            (750, 550),
            (50, 550),
            (20, 300),
            (50, 50),  # Close the polygon
        ]
        dpg.draw_polyline(points, color=(64, 64, 64), thickness=2)

        # Draw dividers
        dpg.draw_line((400, 70), (400, 530), color=(64, 64, 64))
        dpg.draw_line((100, 300), (700, 300), color=(64, 64, 64))

    def _draw_main_content(self):
        """Draw the main content of the interface"""
        # Title
        dpg.draw_text((400, 40), self.window_name, color=(255, 255, 255), size=20)
        dpg.draw_line((250, 50), (550, 50), color=(64, 64, 64))

        # Section titles with rectangular borders
        sections = [
            {
                "title": "CURRENT EMOTION",
                "pos": (220, 100),
                "rect": [(80, 80), (360, 120)],
            },
            {
                "title": "INTERACTION DATA",
                "pos": (580, 100),
                "rect": [(440, 80), (720, 120)],
            },
            {
                "title": "EMOTION TRACKING",
                "pos": (220, 340),
                "rect": [(80, 320), (360, 360)],
            },
            {
                "title": "SYSTEM STATUS",
                "pos": (580, 340),
                "rect": [(440, 320), (720, 360)],
            },
        ]

        for section in sections:
            # Draw rectangular border
            rect_min = section["rect"][0]
            rect_max = section["rect"][1]
            dpg.draw_rectangle(
                rect_min, rect_max, color=(85, 85, 85), fill=(0, 0, 0, 0)
            )

            # Draw title text
            dpg.draw_text(section["pos"], section["title"], color=(255, 255, 255))

        # Draw emotion face
        self._draw_emotion_face()

        # Draw touch data
        self._draw_touch_data()

        # Draw emotion chart
        self._draw_emotion_chart()

        # Draw touch metrics
        self._draw_touch_metrics()

        # Draw system time
        self._draw_system_time()

    def _draw_emotion_face(self):
        """Draw the emotion face with appropriate expression"""
        center = (220, 200)
        radius = 70

        # Get emotion data
        emotion_data = self.EMOTION_DATA.get(
            self.current_emotion, self.EMOTION_DATA["neutral"]
        )
        color = emotion_data["color"]
        mouth_curve = emotion_data["mouth_curve"]
        mouth_open = emotion_data.get("mouth_open", False)

        # Draw face circle
        dpg.draw_circle(center, radius, color=color, fill=color)

        # Draw eyes (black circles)
        left_eye = (center[0] - 35, center[0] - 25)
        right_eye = (center[0] + 35, center[0] - 25)

        dpg.draw_circle(left_eye, 12, color=(0, 0, 0), fill=(0, 0, 0))
        dpg.draw_circle(right_eye, 12, color=(0, 0, 0), fill=(0, 0, 0))

        # Draw mouth
        mouth_center = (center[0], center[1] + 20)

        if mouth_open:
            # Draw surprised open mouth (circle)
            dpg.draw_circle(mouth_center, 15, color=(0, 0, 0), fill=(0, 0, 0))
        else:
            # Draw curved mouth
            mouth_width = 50
            curve_height = int(mouth_width * mouth_curve)

            if mouth_curve == 0:  # Straight line for neutral
                dpg.draw_line(
                    (center[0] - mouth_width // 2, center[1] + 20),
                    (center[0] + mouth_width // 2, center[1] + 20),
                    color=(0, 0, 0),
                    thickness=5,
                )
            else:
                # Draw curved mouth using polyline approximation
                points = []
                for i in range(11):  # 11 points for smooth curve
                    t = i / 10.0  # Parameter from 0 to 1
                    x = center[0] - mouth_width // 2 + mouth_width * t
                    # Quadratic curve: y = a * (x - h)² + k
                    y = (
                        center[1]
                        + 20
                        + 4
                        * curve_height
                        * (t - 0.5) ** 2
                        * (-1 if curve_height > 0 else 1)
                    )
                    points.append((x, y))

                dpg.draw_polyline(points, color=(0, 0, 0), thickness=5)

        # Draw emotion name
        dpg.draw_text(
            (center[0], center[1] + 90),
            self.current_emotion.upper(),
            color=(255, 255, 255),
        )

    def _draw_touch_data(self):
        """Draw touch data with hexagonal display"""
        center = (580, 190)
        size = 70

        # Create hexagon points
        points = []
        for i in range(7):  # 7 points to close the hexagon
            angle_deg = 60 * i - 30
            angle_rad = math.pi / 180 * angle_deg
            x = center[0] + size * math.cos(angle_rad)
            y = center[1] + size * math.sin(angle_rad)
            points.append((x, y))

        # Draw hexagon
        dpg.draw_polyline(points, color=(102, 102, 102), thickness=2)

        # Draw touch count label
        dpg.draw_text((center[0], center[1] - 20), "TOUCHES", color=(255, 255, 255))

        # Draw touch count
        touch_count = str(self.touch_stats["today_touches"])
        text_width = len(touch_count) * 10  # Approximate text width
        dpg.draw_text(
            (center[0] - text_width // 2, center[1]),
            touch_count,
            color=(255, 255, 255),
            size=30,
        )

        # Draw "TODAY" label
        dpg.draw_text((center[0], center[1] + 35), "TODAY", color=(153, 153, 153))

    def _draw_emotion_chart(self):
        """Draw the emotion distribution bar chart"""
        # Get max count for scaling
        max_count = (
            max(self.emotion_counts.values()) if self.emotion_counts else 1
        )  # Avoid division by zero

        # Draw title
        dpg.draw_text((220, 380), "DAILY EMOTION PROFILE", color=(255, 255, 255))

        # Draw 6 emotion bars
        bar_width = 40
        bar_height = 70
        bar_spacing = 10
        start_x = 120  # Adjusted to center the 6 bars

        for i, emotion in enumerate(self.ALL_EMOTIONS):
            x = start_x + i * (bar_width + bar_spacing)
            y = 400

            # Get count for this emotion (0 if not present)
            count = self.emotion_counts.get(emotion, 0)

            # Calculate height proportion
            height_proportion = count / max_count if max_count > 0 else 0
            bar_value_height = int(bar_height * height_proportion)

            # Draw bar outline
            dpg.draw_rectangle(
                (x, y),
                (x + bar_width, y + bar_height),
                color=(68, 68, 68),
                fill=(0, 0, 0, 0),
            )

            # Draw filled portion of bar
            if bar_value_height > 0:
                dpg.draw_rectangle(
                    (x, y + bar_height - bar_value_height),
                    (x + bar_width, y + bar_height),
                    color=(51, 51, 51),
                    fill=(51, 51, 51),
                )

            # Draw emotion label
            label = emotion[:3].upper()
            dpg.draw_text(
                (x + bar_width // 2, y + bar_height + 10), label, color=(255, 255, 255)
            )

    def _draw_touch_metrics(self):
        """Draw touch metrics"""
        # Title
        dpg.draw_text((580, 380), "TOUCH METRICS", color=(255, 255, 255))

        # Metrics
        metrics = [
            {
                "label": "AVG DURATION:",
                "value": f"{self.daily_stats['avg_touch_duration']:.1f}s",
            },
            {
                "label": "MAX DURATION:",
                "value": f"{self.daily_stats['max_touch_duration']:.1f}s",
            },
            {
                "label": "TOTAL TIME:",
                "value": f"{self.daily_stats['total_touch_duration']:.1f}s",
            },
        ]

        y = 410
        for metric in metrics:
            # Label (left-aligned)
            dpg.draw_text((490, y), metric["label"], color=(170, 170, 170))

            # Value (right-aligned)
            value_width = len(metric["value"]) * 8  # Approximate text width
            dpg.draw_text(
                (670 - value_width, y), metric["value"], color=(255, 255, 255)
            )

            y += 20

    def _draw_system_time(self):
        """Draw system time at the bottom"""
        # Get current time
        now = datetime.datetime.now()
        time_str = f"SYS: {now.strftime('%Y-%m-%d | %H:%M:%S')}"

        # Draw time
        text_width = len(time_str) * 8  # Approximate text width
        dpg.draw_text((400 - text_width // 2, 570), time_str, color=(153, 153, 153))

    def _on_resize(self, sender, app_data):
        """Handle viewport resize"""
        self.window_width = app_data[0]
        self.window_height = app_data[1]


# Example of how to use this visualization
if __name__ == "__main__":
    import sys

    # Mock tracker and database classes for testing
    class MockEmotionTracker:
        def get_current_emotion(self):
            emotions = ["happy", "sad", "angry", "neutral", "fear", "surprise"]
            import random

            return random.choice(emotions), 0.85

    class MockTouchTracker:
        def get_statistics(self):
            return {
                "active_touches": 2,
                "today_touches": 42,
                "today_total_duration": 120.5,
                "today_max_duration": 5.6,
            }

    class MockDatabase:
        def get_daily_stats(self):
            return {
                "date": "2025-03-01",
                "dominant_emotion": "happy",
                "emotion_counts": {
                    "happy": 35,
                    "neutral": 18,
                    "sad": 7,
                    "surprise": 4,
                    "disgust": 1,
                },
                "touch_count": 42,
                "avg_touch_duration": 2.8,
                "max_touch_duration": 5.6,
                "total_touch_duration": 120.5,
            }

    # Create and start visualization
    viz = DearPyGuiVisualization(
        MockEmotionTracker(), MockTouchTracker(), MockDatabase()
    )

    try:
        viz.start()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        viz.stop()

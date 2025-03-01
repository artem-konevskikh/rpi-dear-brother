import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
import datetime
import time
import threading
import math


class CustomTkinterVisualization:
    """Minimalist sci-fi UI for displaying emotion and statistics using CustomTkinter"""

    # Emotion data with corresponding colors (RGB for PIL)
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

        # Set appearance mode
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Initialize the root window
        self.root = None
        self.canvas = None

        # Image references (to prevent garbage collection)
        self.image_refs = {}

    def start(self):
        """Start the visualization"""
        if self.running:
            return

        self.running = True

        # Initialize CustomTkinter window
        self.root = ctk.CTk()
        self.root.title(self.window_name)
        self.root.geometry(f"{self.window_width}x{self.window_height}")
        self.root.resizable(True, True)
        self.root.configure(fg_color="#080808")  # Dark background
        self.root.protocol("WM_DELETE_WINDOW", self.stop)  # Handle window close

        # Create canvas for drawing
        self.canvas = tk.Canvas(
            self.root,
            width=self.window_width,
            height=self.window_height,
            bg="#080808",  # Dark background
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind resize event
        self.root.bind("<Configure>", self._on_resize)

        # Start update thread
        self.update_thread = threading.Thread(target=self._update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()

        # Start Tk mainloop
        self.root.mainloop()

    def stop(self):
        """Stop the visualization"""
        self.running = False
        if self.root:
            self.root.quit()
            self.root.destroy()

    def _update_loop(self):
        """Background thread to update data and redraw UI"""
        while self.running:
            try:
                # Get current data
                self._update_data()

                # Update the UI - must be done from the main thread
                self.root.after(0, self._redraw_ui)

                # Update every 100ms
                time.sleep(0.1)
            except Exception as e:
                print(f"Update error: {e}")
                # Keep thread alive even if there's an error
                time.sleep(1)

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

    def _redraw_ui(self):
        """Redraw the entire UI"""
        if not self.running or not self.canvas:
            return

        # Clear the canvas
        self.canvas.delete("all")

        # Get current canvas size
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        # Adjust if not properly initialized yet
        if width < 10:
            width = self.window_width
        if height < 10:
            height = self.window_height

        # Draw background
        self._draw_background(width, height)

        # Draw content
        self._draw_title(width, height)
        self._draw_section_dividers(width, height)
        self._draw_section_titles(width, height)
        self._draw_emotion_face(width, height)
        self._draw_touch_data(width, height)
        self._draw_emotion_chart(width, height)
        self._draw_touch_metrics(width, height)
        self._draw_system_time(width, height)

    def _draw_background(self, width, height):
        """Draw the background with grid and hexagonal border"""
        # Draw grid pattern - small grid
        for x in range(0, width, 10):
            self.canvas.create_line(x, 0, x, height, fill="#181818", width=1)

        for y in range(0, height, 10):
            self.canvas.create_line(0, y, width, y, fill="#181818", width=1)

        # Larger grid
        for x in range(0, width, 100):
            self.canvas.create_line(x, 0, x, height, fill="#202020", width=1)

        for y in range(0, height, 100):
            self.canvas.create_line(0, y, width, y, fill="#202020", width=1)

        # Calculate proportional points for hexagonal border
        scale_x = width / self.window_width
        scale_y = height / self.window_height

        # Draw hexagonal border
        points = [
            50 * scale_x,
            50 * scale_y,
            (width - 50 * scale_x),
            50 * scale_y,
            (width - 20 * scale_x),
            height / 2,
            (width - 50 * scale_x),
            (height - 50 * scale_y),
            50 * scale_x,
            (height - 50 * scale_y),
            20 * scale_x,
            height / 2,
        ]
        self.canvas.create_polygon(points, outline="#404040", fill="", width=2)

    def _draw_title(self, width, height):
        """Draw the title at the top"""
        self.canvas.create_text(
            width / 2,
            40 * (height / self.window_height),
            text=self.window_name,
            font=("Courier", int(14 * (height / self.window_height))),
            fill="white",
        )

        # Line under title
        line_width = 300 * (width / self.window_width)
        self.canvas.create_line(
            (width / 2) - (line_width / 2),
            50 * (height / self.window_height),
            (width / 2) + (line_width / 2),
            50 * (height / self.window_height),
            fill="#404040",
            width=1,
        )

    def _draw_section_dividers(self, width, height):
        """Draw section dividers"""
        # Vertical divider
        self.canvas.create_line(
            width / 2,
            70 * (height / self.window_height),
            width / 2,
            530 * (height / self.window_height),
            fill="#404040",
            width=1,
        )

        # Horizontal divider
        h_divider_y = 300 * (height / self.window_height)
        self.canvas.create_line(
            100 * (width / self.window_width),
            h_divider_y,
            (width - 100 * (width / self.window_width)),
            h_divider_y,
            fill="#404040",
            width=1,
        )

    def _draw_section_titles(self, width, height):
        """Draw section titles with rectangular borders"""
        # Define section titles and positions
        scale_x = width / self.window_width
        scale_y = height / self.window_height

        sections = [
            {
                "title": "CURRENT EMOTION",
                "x": 220 * scale_x,
                "y": 100 * scale_y,
                "left": 80 * scale_x,
                "right": 360 * scale_x,
                "top": 80 * scale_y,
                "bottom": 120 * scale_y,
            },
            {
                "title": "INTERACTION DATA",
                "x": 580 * scale_x,
                "y": 100 * scale_y,
                "left": 440 * scale_x,
                "right": 720 * scale_x,
                "top": 80 * scale_y,
                "bottom": 120 * scale_y,
            },
            {
                "title": "EMOTION TRACKING",
                "x": 220 * scale_x,
                "y": 340 * scale_y,
                "left": 80 * scale_x,
                "right": 360 * scale_x,
                "top": 320 * scale_y,
                "bottom": 360 * scale_y,
            },
            {
                "title": "SYSTEM STATUS",
                "x": 580 * scale_x,
                "y": 340 * scale_y,
                "left": 440 * scale_x,
                "right": 720 * scale_x,
                "top": 320 * scale_y,
                "bottom": 360 * scale_y,
            },
        ]

        # Draw each section title with rectangular border
        for section in sections:
            # Draw rectangular border
            self.canvas.create_rectangle(
                section["left"],
                section["top"],
                section["right"],
                section["bottom"],
                outline="#555555",
                width=1,
            )

            # Draw title text
            self.canvas.create_text(
                section["x"],
                section["y"],
                text=section["title"],
                font=("Courier", int(12 * scale_y)),
                fill="white",
            )

    def _draw_emotion_face(self, width, height):
        """Draw the emotion face with appropriate expression"""
        scale_x = width / self.window_width
        scale_y = height / self.window_height

        center_x = 220 * scale_x
        center_y = 200 * scale_y
        radius = 70 * min(scale_x, scale_y)

        # Get emotion data
        emotion_data = self.EMOTION_DATA.get(
            self.current_emotion, self.EMOTION_DATA["neutral"]
        )
        color = emotion_data["color"]
        mouth_curve = emotion_data["mouth_curve"]
        mouth_open = emotion_data.get("mouth_open", False)

        # Create a PIL image for drawing the face
        img_size = int(radius * 3)
        img = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw face circle
        center_in_img = (img_size // 2, img_size // 2)
        draw.ellipse(
            [
                center_in_img[0] - radius,
                center_in_img[1] - radius,
                center_in_img[0] + radius,
                center_in_img[1] + radius,
            ],
            fill=color,
        )

        # Draw eyes (black circles)
        eye_offset_x = 35 * min(scale_x, scale_y)
        eye_offset_y = 25 * min(scale_x, scale_y)
        eye_radius = 12 * min(scale_x, scale_y)

        # Left eye
        left_eye = (center_in_img[0] - eye_offset_x, center_in_img[1] - eye_offset_y)
        draw.ellipse(
            [
                left_eye[0] - eye_radius,
                left_eye[1] - eye_radius,
                left_eye[0] + eye_radius,
                left_eye[1] + eye_radius,
            ],
            fill=(0, 0, 0),
        )

        # Right eye
        right_eye = (center_in_img[0] + eye_offset_x, center_in_img[1] - eye_offset_y)
        draw.ellipse(
            [
                right_eye[0] - eye_radius,
                right_eye[1] - eye_radius,
                right_eye[0] + eye_radius,
                right_eye[1] + eye_radius,
            ],
            fill=(0, 0, 0),
        )

        # Draw mouth
        mouth_y = center_in_img[1] + (20 * min(scale_x, scale_y))
        mouth_width = 50 * min(scale_x, scale_y)
        mouth_thickness = 5 * min(scale_x, scale_y)

        if mouth_open:
            # Draw surprised open mouth (circle)
            draw.ellipse(
                [
                    center_in_img[0] - 15 * min(scale_x, scale_y),
                    mouth_y - 15 * min(scale_x, scale_y),
                    center_in_img[0] + 15 * min(scale_x, scale_y),
                    mouth_y + 15 * min(scale_x, scale_y),
                ],
                fill=(0, 0, 0),
            )
        else:
            # Draw curved mouth
            if mouth_curve == 0:  # Straight line for neutral
                draw.line(
                    [
                        center_in_img[0] - mouth_width // 2,
                        mouth_y,
                        center_in_img[0] + mouth_width // 2,
                        mouth_y,
                    ],
                    fill=(0, 0, 0),
                    width=int(mouth_thickness),
                )
            else:
                # Draw curved mouth using a bezier curve approximation
                points = []
                for i in range(11):  # 11 points for smooth curve
                    t = i / 10.0  # Parameter from 0 to 1
                    x = center_in_img[0] - mouth_width // 2 + mouth_width * t
                    # Quadratic curve: y = a * (x - h)² + k
                    curve_height = 4 * mouth_curve * mouth_width
                    y = mouth_y + curve_height * (t - 0.5) ** 2 * (
                        -1 if curve_height > 0 else 1
                    )
                    points.append((x, y))

                # Draw curve
                for i in range(len(points) - 1):
                    draw.line(
                        [points[i], points[i + 1]],
                        fill=(0, 0, 0),
                        width=int(mouth_thickness),
                    )

        # Convert PIL image to PhotoImage and keep reference
        photo_img = ImageTk.PhotoImage(img)
        self.image_refs["face"] = (
            photo_img  # Keep reference to prevent garbage collection
        )

        # Display on canvas
        face_pos_x = center_x - (img_size // 2)
        face_pos_y = center_y - (img_size // 2)
        self.canvas.create_image(face_pos_x, face_pos_y, image=photo_img, anchor="nw")

        # Draw emotion name
        self.canvas.create_text(
            center_x,
            center_y + 90 * scale_y,
            text=self.current_emotion.upper(),
            font=("Courier", int(14 * scale_y)),
            fill="white",
        )

    def _draw_touch_data(self, width, height):
        """Draw touch data with hexagonal display"""
        scale_x = width / self.window_width
        scale_y = height / self.window_height

        center_x = 580 * scale_x
        center_y = 190 * scale_y
        size = 70 * min(scale_x, scale_y)

        # Create hexagon points
        points = []
        for i in range(6):
            angle_deg = 60 * i - 30
            angle_rad = math.pi / 180 * angle_deg
            x = center_x + size * math.cos(angle_rad)
            y = center_y + size * math.sin(angle_rad)
            points.append(x)
            points.append(y)

        # Draw hexagon
        self.canvas.create_polygon(points, outline="#666666", fill="", width=2)

        # Draw touch count label
        self.canvas.create_text(
            center_x,
            center_y - 20 * scale_y,
            text="TOUCHES",
            font=("Courier", int(12 * scale_y)),
            fill="white",
        )

        # Draw touch count value
        self.canvas.create_text(
            center_x,
            center_y + 10 * scale_y,
            text=str(self.touch_stats["today_touches"]),
            font=("Courier", int(24 * scale_y)),
            fill="white",
        )

        # Draw "TODAY" label
        self.canvas.create_text(
            center_x,
            center_y + 35 * scale_y,
            text="TODAY",
            font=("Courier", int(10 * scale_y)),
            fill="#999999",
        )

    def _draw_emotion_chart(self, width, height):
        """Draw the emotion distribution bar chart"""
        scale_x = width / self.window_width
        scale_y = height / self.window_height

        # Draw title
        self.canvas.create_text(
            220 * scale_x,
            380 * scale_y,
            text="DAILY EMOTION PROFILE",
            font=("Courier", int(12 * scale_y)),
            fill="white",
        )

        # Get max count for scaling
        max_count = (
            max(self.emotion_counts.values()) if self.emotion_counts else 1
        )  # Avoid division by zero

        # Draw 6 emotion bars
        bar_width = 40 * scale_x
        bar_height = 70 * scale_y
        bar_spacing = 10 * scale_x
        start_x = 120 * scale_x  # Adjusted to center the 6 bars
        y = 400 * scale_y

        for i, emotion in enumerate(self.ALL_EMOTIONS):
            x = start_x + i * (bar_width + bar_spacing)

            # Get count for this emotion (0 if not present)
            count = self.emotion_counts.get(emotion, 0)

            # Calculate height proportion
            height_proportion = count / max_count if max_count > 0 else 0
            bar_value_height = int(bar_height * height_proportion)

            # Draw bar outline
            self.canvas.create_rectangle(
                x, y, x + bar_width, y + bar_height, outline="#444444", fill=""
            )

            # Draw filled portion of bar
            if bar_value_height > 0:
                self.canvas.create_rectangle(
                    x,
                    y + bar_height - bar_value_height,
                    x + bar_width,
                    y + bar_height,
                    outline="#333333",
                    fill="#333333",
                )

            # Draw emotion label
            self.canvas.create_text(
                x + bar_width / 2,
                y + bar_height + 15 * scale_y,
                text=emotion[:3].upper(),
                font=("Courier", int(10 * scale_y)),
                fill="white",
            )

    def _draw_touch_metrics(self, width, height):
        """Draw touch metrics"""
        scale_x = width / self.window_width
        scale_y = height / self.window_height

        # Title
        self.canvas.create_text(
            580 * scale_x,
            380 * scale_y,
            text="TOUCH METRICS",
            font=("Courier", int(12 * scale_y)),
            fill="white",
        )

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

        y = 410 * scale_y
        for metric in metrics:
            # Label (left-aligned)
            self.canvas.create_text(
                490 * scale_x,
                y,
                text=metric["label"],
                font=("Courier", int(10 * scale_y)),
                fill="#AAAAAA",
                anchor="w",
            )

            # Value (right-aligned)
            self.canvas.create_text(
                670 * scale_x,
                y,
                text=metric["value"],
                font=("Courier", int(10 * scale_y)),
                fill="white",
                anchor="e",
            )

            y += 20 * scale_y

    def _draw_system_time(self, width, height):
        """Draw system time at the bottom"""
        scale_x = width / self.window_width
        scale_y = height / self.window_height

        # Get current time
        now = datetime.datetime.now()
        time_str = f"SYS: {now.strftime('%Y-%m-%d | %H:%M:%S')}"

        # Draw time
        self.canvas.create_text(
            width / 2,
            570 * scale_y,
            text=time_str,
            font=("Courier", int(10 * scale_y)),
            fill="#999999",
        )

    def _on_resize(self, event):
        """Handle window resize event"""
        # Only redraw if size really changed
        if event.width != self.window_width or event.height != self.window_height:
            self.window_width = event.width
            self.window_height = event.height
            self._redraw_ui()


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
    viz = CustomTkinterVisualization(
        MockEmotionTracker(), MockTouchTracker(), MockDatabase()
    )

    try:
        viz.start()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        viz.stop()

import threading
import time


class LEDController:
    """Control the LED strip based on emotions and touch interactions"""

    # Mapping emotions to colors (RGB)
    EMOTION_COLORS = {
        "happy": (255, 255, 0),  # Yellow
        "sad": (0, 0, 255),  # Blue
        "angry": (255, 0, 0),  # Red
        "neutral": (255, 255, 255),  # White
        "fear": (128, 0, 128),  # Purple
        "surprise": (0, 255, 255),  # Cyan
        "disgust": (0, 128, 0),  # Green
    }

    # Default emotion
    DEFAULT_EMOTION = "neutral"

    def __init__(self, led_strip):
        """Initialize the LED controller

        Args:
            led_strip: LedStrip instance
        """
        self.led_strip = led_strip

        # State tracking
        self.current_emotion = self.DEFAULT_EMOTION
        self.target_intensity = 0.5  # Default 50% brightness
        self.current_intensity = 0.5

        # Thread management
        self.lock = threading.Lock()

    def set_emotion_color(self, emotion):
        """Set the LED color based on emotion

        Args:
            emotion: Emotion string
        """
        with self.lock:
            self.current_emotion = emotion
            color = self.EMOTION_COLORS.get(
                emotion, self.EMOTION_COLORS[self.DEFAULT_EMOTION]
            )

            # Update LED strip color (with short transition)
            self.led_strip.change_color(color, steps=20)

    def set_intensity(self, intensity):
        """Set the LED intensity/brightness

        Args:
            intensity: Value between 0.0 (off) and 1.0 (full brightness)
        """
        with self.lock:
            self.target_intensity = max(0.0, min(1.0, intensity))

            # Apply the intensity to the LED strip
            self.led_strip.set_intensity(self.target_intensity)
            self.current_intensity = self.target_intensity

    def fade_to_standby(self, duration=5.0):
        """Fade to a low brightness standby mode

        Args:
            duration: Fade duration in seconds
        """
        standby_intensity = 0.1  # 10% brightness for standby

        with self.lock:
            current = self.current_intensity
            delta = standby_intensity - current
            steps = int(duration * 10)  # 10 steps per second

            for i in range(steps):
                progress = (i + 1) / steps
                new_intensity = current + (delta * progress)
                self.led_strip.set_intensity(new_intensity)
                time.sleep(duration / steps)

            self.current_intensity = standby_intensity

    def clear(self):
        """Turn off all LEDs"""
        self.led_strip.clear()
        self.current_intensity = 0.0

import threading
import time


class LEDController:
    """Control the LED strip based on emotions and touch interactions"""

    # Mapping emotions to colors (RGB)
    EMOTION_COLORS = {
        "happy": (128, 128, 0),  # Yellow
        "sad": (0, 0, 128),  # Blue
        "angry": (128, 0, 0),  # Red
        "neutral": (128, 128, 128),  # Light Gray
        "fear": (64, 0, 64),  # Purple
        "surprise": (0, 128, 128),  # Cyan
        "disgust": (0, 64, 0),  # Green
        "no_face": (64, 64, 128),  # Soft blue for shimmer effect
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
            # Don't change color if we're in touch mode
            if hasattr(self, 'in_touch_mode') and self.in_touch_mode:
                return
                
            self.current_emotion = emotion
            color = self.EMOTION_COLORS.get(
                emotion, self.EMOTION_COLORS[self.DEFAULT_EMOTION]
            )

            # For 'no_face' emotion, use shimmer effect
            # if emotion == "no_face":
            #     # Start shimmer in a separate thread to avoid blocking
            #     shimmer_thread = threading.Thread(
            #         target=self.led_strip.shimmer,
            #         args=(color, 0.1),
            #         daemon=True
            #     )
            #     shimmer_thread.start()
            # else:
            #     # Stop any active shimmer effect before changing color
            #     self.led_strip._shimmer_active = False
            #     # Update LED strip color (with short transition)
            #     self.led_strip.change_color(color, steps=20)

            shimmer_thread = threading.Thread(
                target=self.led_strip.shimmer,
                args=(color, 0.1),
                daemon=True
            )
            shimmer_thread.start()

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
        
    def flash_touch_feedback(self):
        """Change the LEDs to white when touched
        
        This method changes the LED color to white when the touch sensor is activated.
        It does not return to the emotion color - that happens in return_from_touch().
        """
        with self.lock:
            # Set touch mode flag to prevent emotion tracker from changing colors
            self.in_touch_mode = True
            
            # Change to white with quick transition
            self.led_strip.change_color((255, 255, 255), steps=15)
            
    def return_from_touch(self):
        """Return to the current emotion color after touch is released"""
        with self.lock:
            # Clear touch mode flag to allow emotion tracker to change colors again
            self.in_touch_mode = False
            
            # Use current emotion color instead of saved color
            color = self.EMOTION_COLORS.get(
                self.current_emotion, self.EMOTION_COLORS[self.DEFAULT_EMOTION]
            )
            
            # Return to current emotion color
            self.led_strip.change_color(color, steps=10)
            
            # Clean up any saved values if they exist
            if hasattr(self, 'saved_color'):
                delattr(self, 'saved_color')
            if hasattr(self, 'saved_intensity'):
                delattr(self, 'saved_intensity')

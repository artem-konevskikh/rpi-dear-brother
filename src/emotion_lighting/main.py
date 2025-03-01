import time
import argparse
import signal
import sys

from emotion_lighting.led_strip import LedStrip
from emotion_lighting.mpr121_touch_sensor import MPR121TouchSensor
from emotion_lighting.database import EmotionDatabase
from emotion_lighting.led_controller import LEDController
from emotion_lighting.emotion_tracker import EmotionTracker
from emotion_lighting.touch_tracker import TouchTracker
from emotion_lighting.gui_visualization import CustomTkinterVisualization


class EmotionLightingApp:
    """Main application for Emotion Lighting system"""

    def __init__(
        self,
        led_device="/dev/spidev0.0",
        led_count=30,
        led_freq=800,
        touch_address=0x5A,
        touch_bus=1,
        camera_id=0,
        db_path="emotion_data.db",
    ):
        """Initialize the emotion lighting application

        Args:
            led_device: SPI device for LED strip
            led_count: Number of LEDs in the strip
            led_freq: LED strip frequency
            touch_address: I2C address of MPR121
            touch_bus: I2C bus number
            camera_id: Camera device ID
            db_path: Path to SQLite database file
        """
        print("Initializing Emotion Lighting system...")

        # Initialize components
        self.database = EmotionDatabase(db_path)
        print("Database initialized.")

        self.led_strip = LedStrip(led_device, led_count, led_freq)
        print("LED strip initialized.")

        self.led_controller = LEDController(self.led_strip)
        print("LED controller initialized.")

        self.touch_sensor = MPR121TouchSensor(touch_address, touch_bus)
        print("Touch sensor initialized.")

        self.touch_tracker = TouchTracker(
            self.database, self.led_controller, self.touch_sensor
        )
        print("Touch tracker initialized.")

        self.emotion_tracker = EmotionTracker(
            self.database, self.led_controller, camera_id
        )
        print("Emotion tracker initialized.")

        # Initialize visualization
        self.visualization = CustomTkinterVisualization(
            self.emotion_tracker, self.touch_tracker, self.database
        )
        print("Visualization interface initialized.")

        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        print("Emotion Lighting system ready.")

    def start(self):
        """Start the emotion lighting system"""
        # Start LED controller with default values
        self.led_controller.set_emotion_color("neutral")
        self.led_controller.set_intensity(0.5)

        # Start trackers
        self.touch_tracker.start()
        self.emotion_tracker.start()

        # Start visualization (blocks until closed)
        self.visualization.start()

    def stop(self):
        """Stop the emotion lighting system"""
        print("\nShutting down Emotion Lighting system...")

        # Stop visualization first
        self.visualization.stop()

        # Stop trackers
        self.emotion_tracker.stop()
        self.touch_tracker.stop()

        # Fade out LEDs
        self.led_controller.fade_to_standby(2.0)
        time.sleep(0.5)
        self.led_controller.clear()

        print("Shutdown complete.")

    def _signal_handler(self, signum, frame):
        """Handle termination signals"""
        self.stop()
        sys.exit(0)


def main():
    """Entry point for the application"""
    parser = argparse.ArgumentParser(description="Emotion Interactive Lighting System")
    parser.add_argument(
        "--led-device",
        type=str,
        default="/dev/spidev0.0",
        help="SPI device for LED strip",
    )
    parser.add_argument(
        "--led-count", type=int, default=30, help="Number of LEDs in the strip"
    )
    parser.add_argument("--led-freq", type=int, default=800, help="LED strip frequency")
    parser.add_argument(
        "--touch-address",
        type=int,
        default=0x5A,
        help="I2C address of MPR121 (default: 0x5A)",
    )
    parser.add_argument(
        "--touch-bus", type=int, default=1, help="I2C bus number (default: 1)"
    )
    parser.add_argument("--camera", type=int, default=0, help="Camera device ID")
    parser.add_argument(
        "--db", type=str, default="emotion_data.db", help="Path to SQLite database file"
    )

    args = parser.parse_args()

    app = EmotionLightingApp(
        led_device=args.led_device,
        led_count=args.led_count,
        led_freq=args.led_freq,
        touch_address=args.touch_address,
        touch_bus=args.touch_bus,
        camera_id=args.camera,
        db_path=args.db,
    )

    try:
        app.start()
    except ImportError as e:
        if "customtkinter" in str(e):
            print("Error: CustomTkinter is required but not installed.")
            print("Please install it with: pip install customtkinter")
        else:
            print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        app.stop()


if __name__ == "__main__":
    main()

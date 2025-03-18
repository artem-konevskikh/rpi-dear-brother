import time
import argparse
import signal
import os
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("emotion_lighting.main")


# Lazy imports to reduce startup time and memory usage
def import_components():
    from emotion_lighting.led_strip import LedStrip
    from emotion_lighting.mpr121_touch_sensor import MPR121TouchSensor
    from emotion_lighting.database import EmotionDatabase
    from emotion_lighting.led_controller import LEDController
    from emotion_lighting.emotion_tracker import EmotionTracker
    from emotion_lighting.touch_tracker import TouchTracker
    from emotion_lighting.web_server import EmotionWebServer

    return {
        "LedStrip": LedStrip,
        "MPR121TouchSensor": MPR121TouchSensor,
        "EmotionDatabase": EmotionDatabase,
        "LEDController": LEDController,
        "EmotionTracker": EmotionTracker,
        "TouchTracker": TouchTracker,
        "EmotionWebServer": EmotionWebServer,
    }


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
        no_touch=False,
    ):
        """Initialize the emotion lighting application"""
        logger.info("Initializing Emotion Lighting system...")

        # Import components only when needed
        components = import_components()

        # Initialize components with error handling
        try:
            # Database should be initialized first
            self.database = components["EmotionDatabase"](db_path)
            logger.info("Database initialized.")

            # Initialize LED components
            self.led_strip = components["LedStrip"](led_device, led_count, led_freq)
            logger.info("LED strip initialized.")

            self.led_controller = components["LEDController"](self.led_strip)
            logger.info("LED controller initialized.")

            # Initialize sensors and trackers conditionally based on no_touch flag
            if no_touch:
                logger.info("Touch sensor disabled by --no-touch flag.")
                self.touch_sensor = None
                self.touch_tracker = None
            else:
                try:
                    # Initialize touch sensor
                    self.touch_sensor = components["MPR121TouchSensor"](
                        touch_address, touch_bus
                    )
                    logger.info("Touch sensor initialized.")

                    # Initialize touch tracker
                    self.touch_tracker = components["TouchTracker"](
                        self.database, self.led_controller, self.touch_sensor
                    )
                    logger.info("Touch tracker initialized.")
                except Exception as e:
                    logger.error(f"Failed to initialize touch components: {e}")
                    self.touch_sensor = None
                    self.touch_tracker = None
                    logger.info("Continuing without touch functionality.")

            self.emotion_tracker = components["EmotionTracker"](
                self.database, self.led_controller, camera_id
            )
            logger.info("Emotion tracker initialized.")

            # Initialize web server
            self.web_server = components["EmotionWebServer"](
                self.emotion_tracker, self.touch_tracker, self.database
            )
            logger.info("Web server initialized.")

            # Setup signal handlers after all components are ready
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

            self.running = False
            logger.info("Emotion Lighting system ready.")

        except Exception as e:
            logger.error(f"Initialization error: {e}")
            # Clean up any resources that were initialized
            self.stop()
            raise

    def start(self):
        """Start the emotion lighting system"""
        if self.running:
            return

        self.running = True

        # Set initial LED state
        try:
            self.led_controller.set_emotion_color("neutral")
            self.led_controller.set_intensity(0.5)
        except Exception as e:
            logger.error(f"Error setting initial LED state: {e}")

        # Start components in order
        try:
            # Start trackers first
            if self.touch_tracker:
                self.touch_tracker.start()
            self.emotion_tracker.start()

            # Start web server last
            self.web_server.start()
        except Exception as e:
            logger.error(f"Error starting components: {e}")
            self.stop()
            raise

        # Main loop - keep as efficient as possible
        try:
            while self.running:
                # Sleep efficiently to reduce CPU usage
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            self.stop()

    def stop(self):
        """Stop the emotion lighting system"""
        if not hasattr(self, "running") or not self.running:
            return

        logger.info("Shutting down Emotion Lighting system...")
        self.running = False

        # Stop components in reverse order of initialization
        try:
            # Web server first
            logger.info("Stopping web server...")
            if hasattr(self, "web_server"):
                self.web_server.stop()

            # Trackers next
            logger.info("Stopping trackers...")
            if hasattr(self, "emotion_tracker"):
                self.emotion_tracker.stop()
            if hasattr(self, "touch_tracker") and self.touch_tracker:
                self.touch_tracker.stop()

            # LEDs last
            logger.info("Turning off LEDs...")
            if hasattr(self, "led_controller"):
                try:
                    self.led_controller.fade_to_standby(0.5)  # Faster fade for shutdown
                    time.sleep(0.3)  # Reduced sleep time
                    self.led_controller.clear()
                except Exception as e:
                    logger.warning(f"LED shutdown warning: {e}")
                    # Direct attempt if fade fails
                    if hasattr(self, "led_strip"):
                        self.led_strip.clear()

            logger.info("Shutdown complete.")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            # Last resort - force LED strip off
            if hasattr(self, "led_strip"):
                try:
                    self.led_strip.clear()
                except Exception as e2:
                    logger.error(f"Failed to clear LED strip: {e2}")

    def _signal_handler(self, signum, frame):
        """Handle termination signals with clean exit"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        # Force exit after clean shutdown attempt
        os._exit(0)


def main():
    """Entry point for the application"""
    # Use fewer arguments to simplify startup
    parser = argparse.ArgumentParser(description="Emotion Interactive Lighting System")
    parser.add_argument(
        "--led-device", type=str, default="/dev/spidev0.0", help="SPI device for LEDs"
    )
    parser.add_argument("--led-count", type=int, default=30, help="Number of LEDs")
    parser.add_argument("--led-freq", type=int, default=800, help="LED frequency")
    parser.add_argument("--touch-address", type=int, default=0x5A, help="I2C address")
    parser.add_argument("--touch-bus", type=int, default=1, help="I2C bus number")
    parser.add_argument("--camera", type=int, default=0, help="Camera device ID")
    parser.add_argument(
        "--db", type=str, default="emotion_data.db", help="Database path"
    )
    parser.add_argument(
        "--no-touch", action="store_true", help="Disable touch sensor functionality"
    )

    args = parser.parse_args()

    # Create and run the application with error handling
    app = None
    try:
        # Initialize app
        app = EmotionLightingApp(
            led_device=args.led_device,
            led_count=args.led_count,
            led_freq=args.led_freq,
            touch_address=args.touch_address,
            touch_bus=args.touch_bus,
            camera_id=args.camera,
            db_path=args.db,
            no_touch=args.no_touch,
        )

        # Start the app
        app.start()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user.")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
    finally:
        # Clean shutdown
        if app:
            app.stop()


if __name__ == "__main__":
    main()

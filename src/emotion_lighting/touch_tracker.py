import time
import threading
from collections import deque


class TouchTracker:
    """Track touch interactions using the MPR121 sensor"""

    def __init__(self, database, led_controller, touch_sensor):
        """Initialize the touch tracker

        Args:
            database: Database instance for logging touch data
            led_controller: LED controller for changing brightness based on touch
            touch_sensor: MPR121TouchSensor instance
        """
        self.database = database
        self.led_controller = led_controller
        self.touch_sensor = touch_sensor

        # State tracking
        self.running = False
        self.touch_history = deque(maxlen=20)  # Store recent touch events
        self.intensity_cooldown = 0  # Cooldown counter for intensity changes

        # Today's statistics (cached)
        self.today_touches = 0
        self.today_total_duration = 0.0
        self.today_max_duration = 0.0

        # Thread management
        self.thread = None
        self.lock = threading.Lock()

    def start(self):
        """Start touch tracking"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._tracking_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop touch tracking"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)

    def get_statistics(self):
        """Get current touch statistics

        Returns:
            dict: Touch statistics
        """
        with self.lock:
            active_touches = 0
            if self.touch_sensor.current_touches:
                active_touches = sum(1 for t in self.touch_sensor.current_touches if t)

            return {
                "active_touches": active_touches,
                "today_touches": self.today_touches,
                "today_total_duration": self.today_total_duration,
                "today_max_duration": self.today_max_duration,
            }

    def _tracking_loop(self):
        """Main touch tracking loop"""
        last_update_time = 0

        while self.running:
            # Update touch sensor
            self.touch_sensor.update()

            current_time = time.time()
            # Process touch input at 10Hz
            if current_time - last_update_time > 0.1:
                last_update_time = current_time

                # Process touch activity
                self._process_touch_activity()

            # Sleep to reduce CPU usage
            time.sleep(0.01)

    def _process_touch_activity(self):
        """Process touch sensor data"""
        # Get current touch data
        touch_status = self.touch_sensor.current_touches
        active_touches = sum(1 for t in touch_status if t)

        # Add to history
        self.touch_history.append(active_touches)

        # Decrease cooldown counter
        if self.intensity_cooldown > 0:
            self.intensity_cooldown -= 1

        # Process completed touches - check for electrodes that were previously touched but now released
        for i in range(12):
            # Check if touch was just released
            if (
                hasattr(self.touch_sensor, "previous_touches")
                and self.touch_sensor.previous_touches[i]
                and not touch_status[i]
            ):
                # A touch was just released, get its duration
                durations = self.touch_sensor.get_touch_durations(i)
                if durations and len(durations) > 0:
                    last_duration = durations[-1]

                    # Log touch event in database
                    self.database.log_touch(i, last_duration)

                    # Update cached statistics
                    with self.lock:
                        self.today_touches += 1
                        self.today_total_duration += last_duration
                        self.today_max_duration = max(
                            self.today_max_duration, last_duration
                        )

                    # Update daily stats in database
                    self.database.update_daily_stats()
                    
                    # Return to emotion color when touch is released
                    # Only do this if all electrodes are now released
                    if sum(1 for t in touch_status if t) == 0:
                        self.led_controller.return_from_touch()

        # Store current touches for next iteration
        if not hasattr(self.touch_sensor, "previous_touches"):
            self.touch_sensor.previous_touches = [False] * 12
        self.touch_sensor.previous_touches = touch_status.copy()

        # Calculate average touch activity over history
        avg_touches = (
            sum(self.touch_history) / len(self.touch_history)
            if self.touch_history
            else 0
        )

        # Get total duration of active touches
        durations = []
        for i in range(12):
            if self.touch_sensor.current_touches[i]:
                # Add all durations for this electrode
                electrode_durations = self.touch_sensor.get_touch_durations(i)
                if electrode_durations:
                    durations.extend(electrode_durations)

        avg_duration = sum(durations) / len(durations) if durations else 0

        # Change to white when touched (only if not already in touch state)
        if avg_touches > 0 and sum(self.touch_sensor.previous_touches) == 0:
            # Change to white when touched
            self.led_controller.flash_touch_feedback()
            self.intensity_cooldown = 3  # Cooldown to prevent rapid changes

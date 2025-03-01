import time
from pi5neo import Pi5Neo


class LedStrip:
    def __init__(self, device, num_leds, frequency):
        self.neo = Pi5Neo(device, num_leds, frequency)
        self.current_color = (0, 0, 0)  # Default color is off
        self.steps = 100  # Default steps for transitions
        self.intensity = 0.5  # Default intensity at 50%

    def change_color(self, color, steps=None):
        """Fades LED strip from current color to new color

        Args:
            color (tuple): Target color (R, G, B)
            steps (int, optional): Number of steps for the fade. Uses self.steps if None.
        """
        # Use instance steps if not provided
        if steps is None:
            steps = self.steps
        else:
            self.steps = steps  # Update instance steps if provided

        # Store the target color at full intensity
        target_color = color

        # Apply intensity to the target color for the actual display
        scaled_target = self._apply_intensity(target_color)

        for step in range(steps):
            for led in range(self.neo.num_leds):
                # Calculate transition color with current intensity applied
                transition_color = tuple(
                    int(
                        self.current_color[c]
                        + ((scaled_target[c] - self.current_color[c]) * (step / steps))
                    )
                    for c in range(3)
                )
                self.neo.set_led_color(led, *transition_color)
            self.neo.update_strip()
            time.sleep(0.01)

        # Update current color to the scaled target color
        self.current_color = scaled_target
        # Store the unscaled color for future reference
        self._full_intensity_color = target_color

    def set_intensity(self, intensity):
        """Sets the intensity/brightness of the LED strip

        Args:
            intensity (float): Value between 0.0 (off) and 1.0 (full brightness)
        """
        # Ensure intensity is within valid range
        self.intensity = max(0.0, min(1.0, intensity))

        # Update the current color with the new intensity
        if hasattr(self, "_full_intensity_color"):
            scaled_color = self._apply_intensity(self._full_intensity_color)
            for led in range(self.neo.num_leds):
                self.neo.set_led_color(led, *scaled_color)
            self.neo.update_strip()
            self.current_color = scaled_color

    def _apply_intensity(self, color):
        """Apply current intensity to a color

        Args:
            color (tuple): Original RGB color at full intensity

        Returns:
            tuple: Color with intensity applied
        """
        return tuple(int(c * self.intensity) for c in color)

    def clear(self):
        """Clears the LED strip"""
        self.neo.fill_strip(0, 0, 0)
        self.neo.update_strip()
        self.current_color = (0, 0, 0)  # Update current color to off
        self._full_intensity_color = (0, 0, 0)

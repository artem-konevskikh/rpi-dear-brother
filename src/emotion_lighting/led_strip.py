import time
from pi5neo import Pi5Neo


class LedStrip:
    def __init__(self, device, num_leds, frequency):
        self.neo = Pi5Neo(device, num_leds, frequency)

    def change_color(self, color1, color2, steps=100):
        """Fades LED strip from color1 to color2

        Args:
            color1 (tuple): Starting color (R, G, B)
            color2 (tuple): Ending color (R, G, B)
            steps (int, optional): Number of steps for the fade. Defaults to 100.
        """
        for step in range(steps):
            for led in range(self.neo.num_leds):
                color = tuple(
                    int(color1[c] + ((color2[c] - color1[c]) * (step / steps)))
                    for c in range(3)
                )
                self.neo.set_led_color(led, *color)
            self.neo.update_strip()
            time.sleep(0.01)

    def clear(self):
        """Clears the LED strip"""
        self.neo.fill_strip(0, 0, 0)
        self.neo.update_strip()


# Example usage
if __name__ == "__main__":
    led_strip = LedStrip("/dev/spidev0.0", 10, 800)

    led_strip.change_color((255, 0, 0), (0, 255, 0))
    led_strip.clear()
    led_strip.change_color((0, 255, 0), (0, 0, 255))
    led_strip.clear()
    led_strip.change_color((0, 0, 255), (255, 0, 0))
    led_strip.clear()

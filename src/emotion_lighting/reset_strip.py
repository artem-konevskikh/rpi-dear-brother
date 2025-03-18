#!/usr/bin/env python3

import sys
from pi5neo import Pi5Neo

def reset_strip(num_leds):
    # Initialize LED strip with basic configuration
    # Using default SPI device and frequency
    strip = Pi5Neo('/dev/spidev0.0', num_leds, 800000)
    
    # Turn off all LEDs by setting RGB values to 0
    strip.fill_strip(0, 0, 0)
    strip.update_strip()

if __name__ == '__main__':
    num_leds = 300
    reset_strip(num_leds)

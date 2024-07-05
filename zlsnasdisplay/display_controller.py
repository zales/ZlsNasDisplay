#! /usr/bin/env python3

from zlsnasdisplay.waveshare_epd import epd2in9_V2


class DisplayController:
    def __init__(self):
        """Initialize the display"""
        self.epd = epd2in9_V2.EPD()
        self.epd.init()

    def update_display(self, image):
        """Update the display with the given image"""
        self.epd.display_partial(self.epd.get_buffer(image))

    def clear_display(self):
        """Clear the display"""
        self.epd.clear(0xFF)

    def sleep_display(self):
        """Put the display to sleep"""
        self.epd.sleep()

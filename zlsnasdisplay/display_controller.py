#! /usr/bin/env python3

from typing import TYPE_CHECKING

from zlsnasdisplay.waveshare_epd import epd2in9_V2

if TYPE_CHECKING:
    from PIL import Image


class DisplayController:
    def __init__(self) -> None:
        """Initialize the display"""
        self.epd = epd2in9_V2.EPD()
        self.epd.init()

    def update_display(self, image: "Image.Image") -> None:
        """Update the display with partial update for smooth transitions"""
        self.epd.display_partial(self.epd.get_buffer(image))

    def clear_display(self) -> None:
        """Clear the display"""
        self.epd.clear(0xFF)

    def sleep_display(self) -> None:
        """Put the display to sleep"""
        self.epd.sleep()

#! /usr/bin/env python3
# -*- coding:utf-8 -*-

from PIL import Image, ImageDraw, ImageFont
from display_controller import DisplayController
from system_operations import SystemOperations
from network_operations import NetworkOperations
import os


class DisplayRenderer:
    def __init__(self):
        """ Initialize the display renderer"""
        self.display_controller = DisplayController()

        self.display_controller.clear_display()

        # Define directories for fonts and the e-paper display library
        fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fonts')

        # Load fonts
        self.font34 = ImageFont.truetype(os.path.join(fontdir, 'Ubuntu-Regular.ttf'), 34)
        self.font24 = ImageFont.truetype(os.path.join(fontdir, 'Ubuntu-Regular.ttf'), 24)
        self.font14 = ImageFont.truetype(os.path.join(fontdir, 'Ubuntu-Light.ttf'), 14)

        self.nfont50 = ImageFont.truetype(os.path.join(fontdir, 'MaterialSymbolsRounded.ttf'), 50)
        self.nfont24 = ImageFont.truetype(os.path.join(fontdir, 'MaterialSymbolsRounded.ttf'), 24)
        self.nfont14 = ImageFont.truetype(os.path.join(fontdir, 'MaterialSymbolsRounded.ttf'), 14)

        # Create an image
        self.image = Image.new('1', (self.display_controller.epd.height, self.display_controller.epd.width), 255)
        self.draw = ImageDraw.Draw(self.image)

        # Draw a horizontal line
        self.draw.line([(110, 10), (110, 110)], fill=0, width=0)
        # Draw a horizontal line
        self.draw.line([(215, 10),(215, 110)], fill=0, width=0)
        # Draw a horizontal line
        self.draw.line([(0, 110),(297, 110)], fill=0, width=0)

    def update_display_and_save_image(self):
        """ Update the display and save the image"""
        self.display_controller.update_display(self.image)
        self.image.save("/mnt/web-display/tmp/display-dev.png", "PNG")

    def render_cpu_load(self):
        """ Render CPU load"""
        self.draw.rectangle((0, 0, 109, 67), fill=255)

        self.draw.line(((30, 10), (109, 10)), fill=0, width=0)

        self.draw.text((1, 0), "cpu", font=self.font14, fill=0)
        # Draw CPU usage, memory usage, swap memory usage, and CPU temperature
        self.draw.text((10, 12), "\ue30d", font=self.nfont24, fill=0)  # Unicode icon for CPU
        self.draw.text((40, 12), f"{SystemOperations().get_cpu_load()}%", font=self.font24, fill=0)  # CPU percentage
        self.draw.text((10, 42), "\ue1ff", font=self.nfont24, fill=0)  # Unicode icon for temperature
        self.draw.text((40, 42), f"{SystemOperations().get_cpu_temperature()}°C", font=self.font24, fill=0)  # CPU temperature

        self.update_display_and_save_image()

    def get_updates(self):
        """ Get updates for the display"""
        self.draw.rectangle((216, 68, 296, 100), fill=255)

        self.draw.text((216,68), "apt", font=self.font14, fill=0)
        self.draw.line([(240, 76),(296, 76)], fill=0, width=0)
        self.draw.text((220, 80), "\uf5f4", font=self.nfont24, fill=0)  # Unicode icon for package
        self.draw.text((250, 80), f"{SystemOperations().check_updates()}", font=self.font24, fill=0)  # Swap memory percentage

        self.update_display_and_save_image()

    def render_signal_strength(self):
        """ Render signal strength"""
        self.draw.rectangle((125, 111, 204, 128), fill=255)

        self.draw.text((216,68), "apt", font=self.font14, fill=0)
        self.draw.line([(240, 76),(296, 76)], fill=0, width=0)
        self.draw.text((125, 110), f"\ue63e", font=self.nfont14, fill=0)  # Unicode icon for wifi
        self.draw.text((140, 110), f"{NetworkOperations.get_signal_strength()} dBm", font=self.font14, fill=0)  # CPU temperature

        self.update_display_and_save_image()

    def render_mem(self):
        """ Render memory stats"""
        self.draw.rectangle((0,73, 109, 109), fill=255)

        self.draw.text((1,68), "mem", font=self.font14, fill=0)
        self.draw.line([(38, 76),(108, 76)], fill=0, width=0)
        self.draw.text((10, 80), "\ue322", font=self.nfont24, fill=0)  # Unicode icon for memory
        self.draw.text((40, 80), f"{SystemOperations.get_mem()}%", font=self.font24, fill=0)  # Memory percentage

        self.update_display_and_save_image()

    def render_nvme_stats(self):
        """ Render NVME stats"""
        self.draw.rectangle((111,0, 214, 68), fill=255)

        # DISK
        self.draw.text((112,0), "nvme", font=self.font14, fill=0)
        self.draw.line([(150, 10),(215, 10)], fill=0, width=0)
        self.draw.text((120, 12), "\uf7a4", font=self.nfont24, fill=0)  # Unicode icon for Hard Drive
        self.draw.text((150, 12), f"{SystemOperations.get_nvme_usage()}%", font=self.font24, fill=0)  # CPU percentage
        self.draw.text((120, 42), "\ue1ff", font=self.nfont24, fill=0)  # Unicode icon for temperature
        self.draw.text((150, 42), f"{SystemOperations.get_nvme_temp()} °C", font=self.font24, fill=0)  # Nvme temperature

        self.update_display_and_save_image()

    def render_fan_speed(self):
        """ Render fan speed"""
        self.draw.rectangle((112, 70, 214, 109), fill=255)

        self.draw.text((112,68), "fan", font=self.font14, fill=0)
        self.draw.line([(135, 76),(215, 76)], fill=0, width=0)
        self.draw.text((120, 80), "\uf168", font=self.nfont24, fill=0)  # Unicode icon for fan
        self.draw.text((150, 80), f"{SystemOperations.get_fan_speed()}", font=self.font24, fill=0)  # Fan speed

        self.update_display_and_save_image()

    def render_ip_address(self):
        """ Render IP address"""
        self.draw.rectangle((0, 111, 109, 128), fill=255)

        self.draw.text((5, 110), f"\ue80d", font=self.nfont14, fill=0)  # Unicode icon for network
        self.draw.text((20, 110), f"{NetworkOperations.get_ip_address()}", font=self.font14, fill=0)  # Ip address

        self.update_display_and_save_image()

    def render_uptime(self):
        """ Render uptime"""
        self.draw.rectangle((205, 111, 296, 128), fill=255)

        uptime = SystemOperations.get_uptime()

        self.draw.text((205, 110), f"\ue923", font=self.nfont14, fill=0)  # Unicode icon for uptime
        self.draw.text((220, 110), f"{uptime[0]}d {uptime[1]}h {uptime[2]}m", font=self.font14, fill=0)  # uptime

        self.update_display_and_save_image()
    
    def render_current_traffic(self):
        """ Render current traffic"""
        self.draw.rectangle((216, 0, 296, 68), fill=255)

        network = NetworkOperations.get_current_traffic()
        self.draw.text((216,0), "net (Mb/s)", font=self.font14, fill=0)
        self.draw.line([(282, 10),(296, 10)], fill=0, width=0)
        self.draw.text((220, 12), "\uf090", font=self.nfont24, fill=0)  # Unicode icon download
        self.draw.text((245, 12), f"{round(network[0], 2)}", font=self.font24, fill=0)  # download
        self.draw.text((220, 42), "\uf09b", font=self.nfont24, fill=0)  # Unicode icon for upload
        self.draw.text((245, 42), f"{round(network[1], 2)}", font=self.font24, fill=0)  # upload

        self.update_display_and_save_image()

    def go_to_sleep(self):
        """ Render the display"""
        self.draw.rectangle((0, 0, 296, 128), fill=0)
        self.draw.line([(140, 15), (140, 110)], fill=255, width=0)
        self.draw.text((155, 36), "ZlsNas", font=self.font34, fill=255)
        self.draw.text((70, 36), "\ue80d", font=self.nfont50, fill=255)
        self.draw.text((160, 71), "Sleeping...", font=self.font14, fill=255)

        self.update_display_and_save_image()

        self.display_controller.sleep_display()

#! /usr/bin/env python3

import os

from PIL import Image, ImageDraw, ImageFont

from zlsnasdisplay.display_controller import DisplayController
from zlsnasdisplay.network_operations import NetworkOperations, TrafficMonitor
from zlsnasdisplay.system_operations import SystemOperations


class DisplayRenderer:
    def __init__(self, display_image_path, is_root):
        """Initialize the display renderer"""
        self.display_controller = DisplayController()

        self.display_controller.clear_display()

        self.display_image_path = display_image_path
        self.is_root = is_root

        # Define directories for fonts and the e-paper display library
        fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fonts")

        # Load fonts
        self.font34 = ImageFont.truetype(os.path.join(fontdir, "Ubuntu-Regular.ttf"), 34)
        self.font24 = ImageFont.truetype(os.path.join(fontdir, "Ubuntu-Regular.ttf"), 24)
        self.font20 = ImageFont.truetype(os.path.join(fontdir, "Ubuntu-Regular.ttf"), 20)
        self.font14 = ImageFont.truetype(os.path.join(fontdir, "Ubuntu-Light.ttf"), 14)

        self.nfont50 = ImageFont.truetype(os.path.join(fontdir, "MaterialSymbolsRounded.ttf"), 50)
        self.nfont24 = ImageFont.truetype(os.path.join(fontdir, "MaterialSymbolsRounded.ttf"), 24)
        self.nfont14 = ImageFont.truetype(os.path.join(fontdir, "MaterialSymbolsRounded.ttf"), 14)

        # Create an image
        self.image = Image.new(
            "1", (self.display_controller.epd.height, self.display_controller.epd.width), 255
        )
        self.draw = ImageDraw.Draw(self.image)

        # Draw a horizontal line
        self.draw.line([(98, 10), (98, 110)], fill=0, width=0)
        # Draw a horizontal line
        self.draw.line([(203, 10), (203, 110)], fill=0, width=0)
        # Draw a horizontal line
        self.draw.line([(0, 110), (297, 110)], fill=0, width=0)

    def update_display_and_save_image(self):
        """Update the display and save the image"""
        self.display_controller.update_display(self.image)
        if self.display_image_path:
            self.image.save(self.display_image_path, "PNG")

    def render_cpu_load(self):
        """Render CPU load"""
        self.draw.rectangle((0, 0, 97, 67), fill=255)

        self.draw.line(((26, 10), (97, 10)), fill=0, width=0)

        self.draw.text((1, 0), "cpu", font=self.font14, fill=0)
        # Draw CPU usage
        self.draw.text((10, 12), "\ue30d", font=self.nfont24, fill=0)  # Unicode icon for CPU
        self.draw.text(
            (40, 12), f"{SystemOperations().get_cpu_load()}%", font=self.font24, fill=0
        )  # CPU percentage
        self.draw.text(
            (10, 42), "\ue1ff", font=self.nfont24, fill=0
        )  # Unicode icon for temperature
        self.draw.text(
            (40, 42), f"{SystemOperations().get_cpu_temperature()}°C", font=self.font24, fill=0
        )  # CPU temperature

        self.update_display_and_save_image()

    def get_updates(self):
        """Get updates for the display"""
        self.draw.rectangle((204, 68, 248, 109), fill=255)

        self.draw.text((204, 67), "apt", font=self.font14, fill=0)
        self.draw.line([(226, 76), (248, 76)], fill=0, width=0)
        number_of_updates = SystemOperations().check_updates(self.is_root)
        if number_of_updates == 0:
            self.draw.text((214, 80), "\ue8e8", font=self.nfont24, fill=0)
        else:
            self.draw.text(
                (214, 80), f"{number_of_updates}", font=self.font24, fill=0
            )  # Number of available updates

        self.update_display_and_save_image()

    def check_net(self):
        """Check network status"""
        self.draw.rectangle((249, 79, 296, 109), fill=255)

        self.draw.text((250, 67), "net", font=self.font14, fill=0)
        self.draw.line([(249, 76), (249, 110)], fill=0, width=0)
        self.draw.line([(272, 76), (297, 76)], fill=0, width=0)
        if NetworkOperations.check_internet_connection():
            self.draw.text((260, 80), "\ue2bf", font=self.nfont24, fill=0)
        else:
            self.draw.text((260, 80), "\uf1ca", font=self.nfont24, fill=0)

        self.update_display_and_save_image()

    def render_signal_strength(self):
        """Render signal strength"""
        self.draw.rectangle((125, 111, 204, 128), fill=255)

        signal = NetworkOperations.get_signal_strength()

        if signal:
            self.draw.text((125, 110), "\ue63e", font=self.nfont14, fill=0)  # Unicode icon for wifi
            self.draw.text((140, 110), f"{signal} dBm", font=self.font14, fill=0)  # CPU temperature
        else:
            self.draw.text((125, 110), "\ue1da", font=self.nfont14, fill=0)  # Unicode icon for wifi

        self.update_display_and_save_image()

    def render_mem(self):
        """Render memory stats"""
        self.draw.rectangle((0, 73, 97, 109), fill=255)

        self.draw.text((1, 67), "mem", font=self.font14, fill=0)
        self.draw.line([(34, 76), (97, 76)], fill=0, width=0)
        self.draw.text((10, 80), "\ue322", font=self.nfont24, fill=0)  # Unicode icon for memory
        self.draw.text(
            (40, 80), f"{SystemOperations.get_mem()}%", font=self.font24, fill=0
        )  # Memory percentage

        self.update_display_and_save_image()

    def render_nvme_stats(self):
        """Render NVME stats"""
        self.draw.rectangle((111, 0, 202, 68), fill=255)

        # DISK
        self.draw.text((100, 0), "nvme", font=self.font14, fill=0)
        self.draw.line([(138, 10), (203, 10)], fill=0, width=0)
        self.draw.text(
            (108, 12), "\uf7a4", font=self.nfont24, fill=0
        )  # Unicode icon for Hard Drive
        self.draw.text(
            (138, 12), f"{SystemOperations.get_nvme_usage()}%", font=self.font24, fill=0
        )  # CPU percentage
        self.draw.text(
            (108, 42), "\ue1ff", font=self.nfont24, fill=0
        )  # Unicode icon for temperature
        self.draw.text(
            (138, 42), f"{SystemOperations.get_nvme_temp()}°C", font=self.font24, fill=0
        )  # Nvme temperature

        self.update_display_and_save_image()

    def render_fan_speed(self):
        """Render fan speed"""
        self.draw.rectangle((100, 70, 202, 109), fill=255)

        self.draw.text((100, 67), "fan", font=self.font14, fill=0)
        self.draw.line([(122, 76), (203, 76)], fill=0, width=0)
        self.draw.text((108, 80), "\uf168", font=self.nfont24, fill=0)  # Unicode icon for fan
        self.draw.text(
            (138, 80), f"{SystemOperations.get_fan_speed()}", font=self.font24, fill=0
        )  # Fan speed

        self.update_display_and_save_image()

    def render_ip_address(self):
        """Render IP address"""
        self.draw.rectangle((0, 111, 109, 128), fill=255)

        ip_address = NetworkOperations.get_ip_address()
        self.draw.text((5, 110), "\ue80d", font=self.nfont14, fill=0)  # Unicode icon for network

        if ip_address:
            self.draw.text((20, 110), f"{ip_address}", font=self.font14, fill=0)  # Ip address
        else:
            self.draw.text((20, 110), "No IP address!", font=self.font14, fill=0)

        self.update_display_and_save_image()

    def render_uptime(self):
        """Render uptime"""
        self.draw.rectangle((205, 111, 296, 128), fill=255)

        uptime = SystemOperations.get_uptime()

        self.draw.text((205, 110), "\ue923", font=self.nfont14, fill=0)  # Unicode icon for uptime
        self.draw.text(
            (220, 110), f"{uptime[0]}d {uptime[1]}h {uptime[2]}m", font=self.font14, fill=0
        )  # uptime

        self.update_display_and_save_image()

    def render_current_traffic(self):
        """Render current traffic"""
        self.draw.rectangle((204, 0, 296, 68), fill=255)

        network = TrafficMonitor().get_current_traffic()
        self.draw.text((204, 0), "down", font=self.font14, fill=0)
        self.draw.line([(242, 10), (261, 10)], fill=0, width=0)
        self.draw.text((263, 0), f"{network[1]}/s", font=self.font14, fill=0)
        self.draw.text((208, 10), "\uf090", font=self.nfont24, fill=0)  # Unicode icon download
        self.draw.text((233, 14), f"{round(network[0], 2)}", font=self.font20, fill=0)  # download

        self.draw.text((204, 33), "up", font=self.font14, fill=0)
        self.draw.line([(222, 43), (261, 43)], fill=0, width=0)
        self.draw.text((263, 33), f"{network[3]}/s", font=self.font14, fill=0)
        self.draw.text((208, 44), "\uf09b", font=self.nfont24, fill=0)  # Unicode icon for upload
        self.draw.text((233, 48), f"{round(network[2], 2)}", font=self.font20, fill=0)  # upload

        self.update_display_and_save_image()

    def go_to_sleep(self):
        """Render the display"""
        self.draw.rectangle((0, 0, 296, 128), fill=0)
        self.draw.rectangle((136, 15, 139, 110), fill=255, width=0)
        self.draw.text((155, 36), "ZlsNas", font=self.font34, fill=255)
        self.draw.text((65, 36), "\ue80d", font=self.nfont50, fill=255)
        self.draw.text((160, 71), "Sleeping...", font=self.font14, fill=255)

        self.update_display_and_save_image()

        self.display_controller.sleep_display()

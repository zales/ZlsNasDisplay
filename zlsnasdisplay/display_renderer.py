#! /usr/bin/env python3

import logging
import os

from PIL import Image, ImageDraw, ImageFont

from zlsnasdisplay import display_config as cfg
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

        # Initialize TrafficMonitor instance to reuse (prevents memory leak)
        self.traffic_monitor = TrafficMonitor()

        # Define directories for fonts and the e-paper display library
        fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fonts")

        # Load fonts with validation
        self.font34 = self._load_font(fontdir, "Ubuntu-Regular.ttf", 34)
        self.font24 = self._load_font(fontdir, "Ubuntu-Regular.ttf", 24)
        self.font20 = self._load_font(fontdir, "Ubuntu-Regular.ttf", 20)
        self.font14 = self._load_font(fontdir, "Ubuntu-Light.ttf", 14)

        self.nfont50 = self._load_font(fontdir, "MaterialSymbolsRounded.ttf", 50)
        self.nfont24 = self._load_font(fontdir, "MaterialSymbolsRounded.ttf", 24)
        self.nfont14 = self._load_font(fontdir, "MaterialSymbolsRounded.ttf", 14)

        # Create an image
        self.image = Image.new(
            "1", (self.display_controller.epd.height, self.display_controller.epd.width), 255
        )
        self.draw = ImageDraw.Draw(self.image)

    def _load_font(self, fontdir: str, font_name: str, size: int) -> ImageFont.FreeTypeFont:
        """Load a font file with validation and fallback to default font."""
        font_path = os.path.join(fontdir, font_name)
        try:
            if not os.path.exists(font_path):
                raise FileNotFoundError(f"Font file not found: {font_path}")
            return ImageFont.truetype(font_path, size)
        except (FileNotFoundError, OSError, IOError) as e:
            logging.warning(f"Failed to load font {font_name}: {e}. Using default font.")
            # Return default PIL font as fallback
            return ImageFont.load_default()

    def render_grid(self):
        """Render display stats grid"""
        self.draw.rectangle((0, 0, cfg.DISPLAY_WIDTH, cfg.DISPLAY_HEIGHT), fill=255)

        # Draw vertical divider lines
        self.draw.line(
            [(cfg.VERTICAL_LINE_1, 10), (cfg.VERTICAL_LINE_1, cfg.HORIZONTAL_LINE_MAIN)],
            fill=0,
            width=0,
        )
        self.draw.line(
            [(cfg.VERTICAL_LINE_2, 10), (cfg.VERTICAL_LINE_2, cfg.HORIZONTAL_LINE_MAIN)],
            fill=0,
            width=0,
        )
        # Draw main horizontal divider
        self.draw.line(
            [(0, cfg.HORIZONTAL_LINE_MAIN), (cfg.DISPLAY_WIDTH + 1, cfg.HORIZONTAL_LINE_MAIN)],
            fill=0,
            width=0,
        )

        ## CPU

        self.draw.line(((26, cfg.CPU_LINE_Y), (99, cfg.CPU_LINE_Y)), fill=0, width=0)
        self.draw.text((1, cfg.CPU_LABEL_Y), "cpu", font=self.font14, fill=0)
        # Draw CPU usage
        self.draw.text(
            (cfg.CPU_ICON_X, cfg.CPU_ICON_Y_LOAD), cfg.ICON_CPU, font=self.nfont24, fill=0
        )
        self.draw.text(
            (cfg.CPU_ICON_X, cfg.CPU_ICON_Y_TEMP),
            cfg.ICON_TEMPERATURE,
            font=self.nfont24,
            fill=0,
        )

        ## UPDATES
        self.draw.text((cfg.APT_LABEL_X, cfg.APT_LABEL_Y), "apt", font=self.font14, fill=0)
        self.draw.line([(226, cfg.APT_LINE_Y), (248, cfg.APT_LINE_Y)], fill=0, width=0)

        ## CHECK NET
        self.draw.text((cfg.NET_LABEL_X, cfg.NET_LABEL_Y), "net", font=self.font14, fill=0)
        self.draw.line(
            [(cfg.NET_LINE_X, cfg.NET_LINE_Y), (cfg.NET_LINE_X, cfg.HORIZONTAL_LINE_MAIN)],
            fill=0,
            width=0,
        )
        self.draw.line(
            [(272, cfg.NET_LINE_Y), (cfg.DISPLAY_WIDTH + 1, cfg.NET_LINE_Y)], fill=0, width=0
        )

        # MEM
        self.draw.text((cfg.MEM_LABEL_X, cfg.MEM_LABEL_Y), "mem", font=self.font14, fill=0)
        self.draw.line(
            [(34, cfg.MEM_LINE_Y), (cfg.SECTION_CPU_RIGHT, cfg.MEM_LINE_Y)], fill=0, width=0
        )
        self.draw.text(
            (cfg.MEM_ICON_X, cfg.MEM_ICON_Y), cfg.ICON_MEMORY, font=self.nfont24, fill=0
        )

        # DISK
        self.draw.text((cfg.NVME_LABEL_X, cfg.NVME_LABEL_Y), "nvme", font=self.font14, fill=0)
        self.draw.line(
            [(140, cfg.NVME_LINE_Y), (cfg.SECTION_NVME_RIGHT, cfg.NVME_LINE_Y)], fill=0, width=0
        )
        self.draw.text(
            (cfg.NVME_ICON_X, cfg.NVME_ICON_Y_DISK),
            cfg.ICON_HARD_DRIVE,
            font=self.nfont24,
            fill=0,
        )
        self.draw.text(
            (cfg.NVME_ICON_X, cfg.NVME_ICON_Y_TEMP),
            cfg.ICON_TEMPERATURE,
            font=self.nfont24,
            fill=0,
        )

        # FAN
        self.draw.text((cfg.FAN_LABEL_X, cfg.FAN_LABEL_Y), "fan", font=self.font14, fill=0)
        self.draw.line(
            [(124, cfg.FAN_LINE_Y), (cfg.SECTION_NVME_RIGHT, cfg.FAN_LINE_Y)], fill=0, width=0
        )
        self.draw.text(
            (cfg.FAN_ICON_X, cfg.FAN_ICON_Y), cfg.ICON_FAN, font=self.nfont24, fill=0
        )

        # IP
        self.draw.text(
            (cfg.IP_ICON_X, cfg.IP_ICON_Y), cfg.ICON_NETWORK, font=self.nfont14, fill=0
        )

        # UPTIME
        self.draw.text(
            (cfg.UPTIME_ICON_X, cfg.UPTIME_ICON_Y), cfg.ICON_UPTIME, font=self.nfont14, fill=0
        )

        # TRAFFIC
        self.draw.text(
            (cfg.TRAFFIC_DOWN_LABEL_X, cfg.TRAFFIC_DOWN_LABEL_Y), "down", font=self.font14, fill=0
        )
        self.draw.line(
            [(242, cfg.TRAFFIC_DOWN_LINE_Y), (261, cfg.TRAFFIC_DOWN_LINE_Y)], fill=0, width=0
        )
        self.draw.text(
            (cfg.TRAFFIC_DOWN_ICON_X, cfg.TRAFFIC_DOWN_ICON_Y),
            cfg.ICON_DOWNLOAD,
            font=self.nfont24,
            fill=0,
        )
        self.draw.text(
            (cfg.TRAFFIC_UP_LABEL_X, cfg.TRAFFIC_UP_LABEL_Y), "up", font=self.font14, fill=0
        )
        self.draw.line(
            [(222, cfg.TRAFFIC_UP_LINE_Y), (261, cfg.TRAFFIC_UP_LINE_Y)], fill=0, width=0
        )
        self.draw.text(
            (cfg.TRAFFIC_UP_ICON_X, cfg.TRAFFIC_UP_ICON_Y),
            cfg.ICON_UPLOAD,
            font=self.nfont24,
            fill=0,
        )

    def update_display_and_save_image(self):
        """Update the display and save the image"""
        self.display_controller.update_display(self.image)
        if self.display_image_path:
            self.image.save(self.display_image_path, "BMP")

    def render_cpu_load(self):
        """Render CPU load"""
        self.draw.rectangle((39, 17, 97, 67), fill=255)

        self.draw.text(
            (cfg.CPU_VALUE_X, cfg.CPU_VALUE_Y_LOAD),
            f"{SystemOperations().get_cpu_load()}%",
            font=self.font24,
            fill=0,
        )

        self.draw.text(
            (cfg.CPU_VALUE_X, cfg.CPU_VALUE_Y_TEMP),
            f"{SystemOperations().get_cpu_temperature()}°C",
            font=self.font24,
            fill=0,
        )

    def get_updates(self):
        """Get updates for the display"""
        self.draw.rectangle((214, 83, 248, 105), fill=255)

        number_of_updates = SystemOperations().check_updates(self.is_root)
        if number_of_updates == 0:
            self.draw.text(
                (cfg.APT_VALUE_X, cfg.APT_VALUE_Y), cfg.ICON_CHECK, font=self.nfont24, fill=0
            )
        else:
            self.draw.text(
                (cfg.APT_VALUE_X, cfg.APT_VALUE_Y),
                f"{number_of_updates}",
                font=self.font24,
                fill=0,
            )

    def check_net(self):
        """Check network status"""
        self.draw.rectangle((260, 83, 284, 105), fill=255)

        if NetworkOperations.check_internet_connection():
            self.draw.text(
                (cfg.NET_ICON_X, cfg.NET_ICON_Y), cfg.ICON_WIFI_OK, font=self.nfont24, fill=0
            )
        else:
            self.draw.text(
                (cfg.NET_ICON_X, cfg.NET_ICON_Y), cfg.ICON_WIFI_OFF, font=self.nfont24, fill=0
            )

    def render_signal_strength(self):
        """Render signal strength"""
        self.draw.rectangle((125, 111, 200, 128), fill=255)

        signal = NetworkOperations.get_signal_strength()

        if signal:
            self.draw.text(
                (cfg.SIGNAL_ICON_X, cfg.SIGNAL_ICON_Y),
                cfg.ICON_WIFI_SIGNAL,
                font=self.nfont14,
                fill=0,
            )
            self.draw.text(
                (cfg.SIGNAL_VALUE_X, cfg.SIGNAL_VALUE_Y),
                f"{signal} dBm",
                font=self.font14,
                fill=0,
            )
        else:
            self.draw.text(
                (cfg.SIGNAL_ICON_X, cfg.SIGNAL_ICON_Y),
                cfg.ICON_WIFI_NO_SIGNAL,
                font=self.nfont14,
                fill=0,
            )

    def render_mem(self):
        """Render memory stats"""
        self.draw.rectangle((40, 86, 97, 104), fill=255)

        self.draw.text(
            (cfg.MEM_VALUE_X, cfg.MEM_VALUE_Y),
            f"{SystemOperations.get_mem()}%",
            font=self.font24,
            fill=0,
        )

    def render_nvme_stats(self):
        """Render NVME stats"""
        self.draw.rectangle((139, 17, 200, 65), fill=255)

        self.draw.text(
            (cfg.NVME_VALUE_X, cfg.NVME_VALUE_Y_DISK),
            f"{SystemOperations.get_nvme_usage()}%",
            font=self.font24,
            fill=0,
        )
        self.draw.text(
            (cfg.NVME_VALUE_X, cfg.NVME_VALUE_Y_TEMP),
            f"{SystemOperations.get_nvme_temp()}°C",
            font=self.font24,
            fill=0,
        )

    def render_fan_speed(self):
        """Render fan speed"""
        self.draw.rectangle((135, 85, 200, 104), fill=255)

        self.draw.text(
            (cfg.FAN_VALUE_X, cfg.FAN_VALUE_Y),
            f"{SystemOperations.get_fan_speed()}",
            font=self.font24,
            fill=0,
        )

    def render_ip_address(self):
        """Render IP address"""
        self.draw.rectangle((20, 113, 123, 126), fill=255)

        ip_address = NetworkOperations.get_ip_address()

        if ip_address:
            self.draw.text(
                (cfg.IP_VALUE_X, cfg.IP_VALUE_Y), f"{ip_address}", font=self.font14, fill=0
            )
        else:
            self.draw.text(
                (cfg.IP_VALUE_X, cfg.IP_VALUE_Y), "No IP address!", font=self.font14, fill=0
            )

    def render_uptime(self):
        """Render uptime"""
        self.draw.rectangle((220, 113, cfg.DISPLAY_WIDTH, 125), fill=255)

        uptime = SystemOperations.get_uptime()
        self.draw.text(
            (cfg.UPTIME_VALUE_X, cfg.UPTIME_VALUE_Y),
            f"{uptime[0]}d {uptime[1]}h {uptime[2]}m",
            font=self.font14,
            fill=0,
        )

    def render_current_traffic(self):
        """Render current traffic"""

        network = self.traffic_monitor.get_current_traffic()
        self.draw.rectangle((263, 1, cfg.DISPLAY_WIDTH, 17), fill=255)
        self.draw.text(
            (cfg.TRAFFIC_DOWN_UNIT_X, cfg.TRAFFIC_DOWN_UNIT_Y),
            f"{network[1]}/s",
            font=self.font14,
            fill=0,
        )
        self.draw.rectangle((233, 16, cfg.DISPLAY_WIDTH, 33), fill=255)
        self.draw.text(
            (cfg.TRAFFIC_DOWN_VALUE_X, cfg.TRAFFIC_DOWN_VALUE_Y),
            f"{round(network[0], 2)}",
            font=self.font20,
            fill=0,
        )
        self.draw.rectangle((263, 35, cfg.DISPLAY_WIDTH, 50), fill=255)
        self.draw.text(
            (cfg.TRAFFIC_UP_UNIT_X, cfg.TRAFFIC_UP_UNIT_Y),
            f"{network[3]}/s",
            font=self.font14,
            fill=0,
        )
        self.draw.rectangle((233, 52, cfg.DISPLAY_WIDTH, 68), fill=255)
        self.draw.text(
            (cfg.TRAFFIC_UP_VALUE_X, cfg.TRAFFIC_UP_VALUE_Y),
            f"{round(network[2], 2)}",
            font=self.font20,
            fill=0,
        )

    def go_to_sleep(self):
        """Render the display"""
        self.draw.rectangle((0, 0, cfg.DISPLAY_WIDTH, cfg.DISPLAY_HEIGHT), fill=0)
        self.draw.rectangle((136, 15, 139, cfg.HORIZONTAL_LINE_MAIN), fill=255, width=0)
        self.draw.text((155, 36), "ZlsNas", font=self.font34, fill=255)
        self.draw.text((65, 36), cfg.ICON_NETWORK, font=self.nfont50, fill=255)
        self.draw.text((160, 71), "Sleeping...", font=self.font14, fill=255)

        self.update_display_and_save_image()

        self.display_controller.sleep_display()

    def startup(self):
        """Render the display loading"""
        self.draw.rectangle((0, 0, cfg.DISPLAY_WIDTH, cfg.DISPLAY_HEIGHT), fill=255)
        self.draw.rectangle((136, 15, 139, cfg.HORIZONTAL_LINE_MAIN), fill=0, width=0)
        self.draw.text((155, 36), "ZlsNas", font=self.font34, fill=0)
        self.draw.text((65, 36), cfg.ICON_NETWORK, font=self.nfont50, fill=0)
        self.draw.text((160, 71), "Loading...", font=self.font14, fill=0)

        self.update_display_and_save_image()

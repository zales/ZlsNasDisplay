#! /usr/bin/env python3

import logging
import os
import signal
import time
from typing import Any, Callable

from PIL import Image, ImageDraw, ImageFont

from zlsnasdisplay import display_config as cfg
from zlsnasdisplay.config import Config
from zlsnasdisplay.display_controller import DisplayController
from zlsnasdisplay.network_operations import NetworkOperations, TrafficMonitor
from zlsnasdisplay.system_operations import SystemOperations


class DisplayRenderer:
    def __init__(
        self,
        display_image_path: str | None,
        is_root: bool,
        display_controller: DisplayController | None = None,
    ):
        """Initialize the display renderer with optional dependency injection."""
        self.display_controller = display_controller or DisplayController()

        self.display_controller.clear_display()

        self.display_image_path = display_image_path
        self.is_root = is_root

        # Initialize singleton instances to reuse (prevents memory leak and improves performance)
        self.traffic_monitor = TrafficMonitor()
        self.system_ops = SystemOperations()
        self.network_ops = NetworkOperations()

        # Cache for slow operations
        self._cache: dict[str, tuple[Any, float]] = {}
        self._cache_ttl = {
            "internet_check": float(Config.DISPLAY_CACHE_TTL_INTERNET),
            "signal_strength": float(Config.DISPLAY_CACHE_TTL_SIGNAL),
            "ip_address": float(Config.DISPLAY_CACHE_TTL_IP),
        }

        # Define directories for fonts and the e-paper display library
        fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fonts")

        # Load fonts with validation
        self.font34 = self._load_font(fontdir, "Ubuntu-Regular.ttf", 34)
        self.font26 = self._load_font(
            fontdir, "Ubuntu-Regular.ttf", 26
        )  # New larger font for main values
        self.font24 = self._load_font(fontdir, "Ubuntu-Regular.ttf", 24)
        self.font20 = self._load_font(fontdir, "Ubuntu-Regular.ttf", 20)
        self.font14 = self._load_font(fontdir, "Ubuntu-Light.ttf", 14)

        self.nfont50 = self._load_font(fontdir, "MaterialSymbolsRounded.ttf", 50)
        self.nfont24 = self._load_font(fontdir, "MaterialSymbolsRounded.ttf", 24)
        self.nfont14 = self._load_font(fontdir, "MaterialSymbolsRounded.ttf", 14)

        # Create an image in 1-bit mode for partial updates
        self.image = Image.new(
            "1", (self.display_controller.epd.height, self.display_controller.epd.width), 255
        )
        self.draw = ImageDraw.Draw(self.image)

    def _get_cached_value(self, key: str, fetch_func: Callable[[], Any]) -> Any:
        """Get value from cache or fetch if expired."""
        now = time.time()
        if key in self._cache:
            value, timestamp = self._cache[key]
            if now - timestamp < self._cache_ttl.get(key, 0):
                return value

        # Cache miss or expired - fetch new value
        value = fetch_func()
        self._cache[key] = (value, now)
        return value

    def _load_font(
        self, fontdir: str, font_name: str, size: int
    ) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Load a font file with validation and fallback to default font."""
        font_path = os.path.join(fontdir, font_name)
        try:
            if not os.path.exists(font_path):
                raise FileNotFoundError(f"Font file not found: {font_path}")
            return ImageFont.truetype(font_path, size)
        except (FileNotFoundError, OSError) as e:
            logging.warning(f"Failed to load font {font_name}: {e}. Using default font.")
            # Return default PIL font as fallback
            return ImageFont.load_default()

    def _is_value_critical(
        self, value: float, threshold_high: float, threshold_critical: float
    ) -> tuple[bool, bool]:
        """Check if a value exceeds thresholds.

        Args:
            value: Current value
            threshold_high: High threshold
            threshold_critical: Critical threshold

        Returns:
            Tuple of (is_high, is_critical)
        """
        is_critical = value >= threshold_critical
        is_high = value >= threshold_high and not is_critical
        return is_high, is_critical

    def _draw_text_with_highlight(
        self,
        x: int,
        y: int,
        text: str,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
        is_critical: bool = False,
    ) -> None:
        """Draw text with optional highlighting for critical values.

        Args:
            x: X coordinate
            y: Y coordinate
            text: Text to draw
            font: Font to use
            is_critical: If True, invert colors to highlight
        """
        if is_critical:
            # Get text bounding box
            bbox = self.draw.textbbox((x, y), text, font=font)
            # Draw inverted background
            self.draw.rectangle(bbox, fill=0)
            # Draw white text
            self.draw.text((x, y), text, font=font, fill=255)
        else:
            # Normal black text on white
            self.draw.text((x, y), text, font=font, fill=0)

    def render_grid(self) -> None:
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
        self.draw.text((cfg.MEM_ICON_X, cfg.MEM_ICON_Y), cfg.ICON_MEMORY, font=self.nfont24, fill=0)

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
        self.draw.text((cfg.FAN_ICON_X, cfg.FAN_ICON_Y), cfg.ICON_FAN, font=self.nfont24, fill=0)

        # IP
        self.draw.text((cfg.IP_ICON_X, cfg.IP_ICON_Y), cfg.ICON_NETWORK, font=self.nfont14, fill=0)

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

    def _timeout_handler(self, _signum: int, _frame: Any) -> None:
        """Handler for timeout signal."""
        raise TimeoutError("Display update operation timed out")

    def update_display_and_save_image(self) -> None:
        """Update the display and save the image with timeout protection."""
        try:
            # Set up timeout signal (only works on Unix-like systems)
            signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.alarm(Config.DISPLAY_UPDATE_TIMEOUT)

            try:
                self.display_controller.update_display(self.image)
                if self.display_image_path:
                    self.image.save(self.display_image_path, "BMP")
            finally:
                # Cancel the alarm
                signal.alarm(0)

        except TimeoutError:
            logging.error(f"Display update timed out after {Config.DISPLAY_UPDATE_TIMEOUT} seconds")
        except Exception as e:
            logging.error(f"Display update failed: {e}", exc_info=True)

    def render_cpu_load(self) -> None:
        """Render CPU load and temperature with threshold highlighting"""
        self.draw.rectangle((39, 17, 97, 67), fill=255)

        # Get CPU metrics
        cpu_load = self.system_ops.get_cpu_load()
        cpu_temp = self.system_ops.get_cpu_temperature()

        # Check thresholds
        _, cpu_critical = self._is_value_critical(
            cpu_load, cfg.THRESHOLD_CPU_HIGH, cfg.THRESHOLD_CPU_CRITICAL
        )
        _, temp_critical = self._is_value_critical(
            cpu_temp, cfg.THRESHOLD_TEMP_HIGH, cfg.THRESHOLD_TEMP_CRITICAL
        )

        # Draw CPU load with highlighting
        self._draw_text_with_highlight(
            cfg.CPU_VALUE_X,
            cfg.CPU_VALUE_Y_LOAD,
            f"{cpu_load}%",
            self.font24,
            is_critical=cpu_critical,
        )

        # Draw temperature with highlighting
        self._draw_text_with_highlight(
            cfg.CPU_VALUE_X,
            cfg.CPU_VALUE_Y_TEMP,
            f"{cpu_temp}°C",
            self.font24,
            is_critical=temp_critical,
        )

    def get_updates(self) -> None:
        """Get updates for the display"""
        self.draw.rectangle((214, 83, 248, 105), fill=255)

        number_of_updates = self.system_ops.check_updates(self.is_root)
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

    def check_net(self) -> None:
        """Check network status"""
        self.draw.rectangle((260, 83, 284, 105), fill=255)

        is_connected = self._get_cached_value(
            "internet_check", self.network_ops.check_internet_connection
        )
        if is_connected:
            self.draw.text(
                (cfg.NET_ICON_X, cfg.NET_ICON_Y), cfg.ICON_WIFI_OK, font=self.nfont24, fill=0
            )
        else:
            self.draw.text(
                (cfg.NET_ICON_X, cfg.NET_ICON_Y), cfg.ICON_WIFI_OFF, font=self.nfont24, fill=0
            )

    def render_signal_strength(self) -> None:
        """Render signal strength"""
        self.draw.rectangle((125, 111, 200, 128), fill=255)

        signal = self._get_cached_value(
            "signal_strength", lambda: self.network_ops.get_signal_strength()
        )

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

    def render_mem(self) -> None:
        """Render memory stats with threshold highlighting"""
        self.draw.rectangle((40, 86, 97, 104), fill=255)

        # Get memory usage
        mem_usage = self.system_ops.get_mem()

        # Check thresholds
        _, mem_critical = self._is_value_critical(
            mem_usage, cfg.THRESHOLD_MEM_HIGH, cfg.THRESHOLD_MEM_CRITICAL
        )

        # Draw memory usage with highlighting
        self._draw_text_with_highlight(
            cfg.MEM_VALUE_X, cfg.MEM_VALUE_Y, f"{mem_usage}%", self.font26, is_critical=mem_critical
        )

    def render_nvme_stats(self) -> None:
        """Render NVME stats with threshold highlighting"""
        self.draw.rectangle((139, 17, 200, 65), fill=255)

        # Get NVME metrics
        nvme_usage = self.system_ops.get_nvme_usage()
        nvme_temp = self.system_ops.get_nvme_temp()

        # Check thresholds
        _, disk_critical = self._is_value_critical(
            nvme_usage, cfg.THRESHOLD_DISK_HIGH, cfg.THRESHOLD_DISK_CRITICAL
        )
        _, temp_critical = self._is_value_critical(
            nvme_temp, cfg.THRESHOLD_TEMP_HIGH, cfg.THRESHOLD_TEMP_CRITICAL
        )

        # Draw disk usage with highlighting
        self._draw_text_with_highlight(
            cfg.NVME_VALUE_X,
            cfg.NVME_VALUE_Y_DISK,
            f"{nvme_usage}%",
            self.font26,
            is_critical=disk_critical,
        )

        # Draw temperature with highlighting
        self._draw_text_with_highlight(
            cfg.NVME_VALUE_X,
            cfg.NVME_VALUE_Y_TEMP,
            f"{nvme_temp}°C",
            self.font26,
            is_critical=temp_critical,
        )

    def render_fan_speed(self) -> None:
        """Render fan speed"""
        self.draw.rectangle((135, 85, 200, 104), fill=255)

        self.draw.text(
            (cfg.FAN_VALUE_X, cfg.FAN_VALUE_Y),
            f"{self.system_ops.get_fan_speed()}",
            font=self.font24,
            fill=0,
        )

    def render_ip_address(self) -> None:
        """Render full IP address"""
        self.draw.rectangle((20, 113, 123, 126), fill=255)

        ip_address = self._get_cached_value(
            "ip_address", lambda: self.network_ops.get_ip_address()
        )

        if ip_address:
            self.draw.text((cfg.IP_VALUE_X, cfg.IP_VALUE_Y), ip_address, font=self.font14, fill=0)
        else:
            self.draw.text((cfg.IP_VALUE_X, cfg.IP_VALUE_Y), "No IP!", font=self.font14, fill=0)

    def render_uptime(self) -> None:
        """Render uptime"""
        self.draw.rectangle((220, 113, cfg.DISPLAY_WIDTH, 125), fill=255)

        uptime = self.system_ops.get_uptime()
        self.draw.text(
            (cfg.UPTIME_VALUE_X, cfg.UPTIME_VALUE_Y),
            f"{uptime[0]}d {uptime[1]}h {uptime[2]}m",
            font=self.font14,
            fill=0,
        )

    def render_current_traffic(self) -> None:
        """Render current traffic"""

        network = self.traffic_monitor.get_current_traffic()

        # DOWNLOAD section
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

        # UPLOAD section
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

    def go_to_sleep(self) -> None:
        """Render the display"""
        self.draw.rectangle((0, 0, cfg.DISPLAY_WIDTH, cfg.DISPLAY_HEIGHT), fill=0)
        self.draw.rectangle((136, 15, 139, cfg.HORIZONTAL_LINE_MAIN), fill=255, width=0)
        self.draw.text((155, 36), "ZlsNas", font=self.font34, fill=255)
        self.draw.text((65, 36), cfg.ICON_NETWORK, font=self.nfont50, fill=255)
        self.draw.text((160, 71), "Sleeping...", font=self.font14, fill=255)

        self.update_display_and_save_image()

        self.display_controller.sleep_display()

    def startup(self) -> None:
        """Render the display loading"""
        self.draw.rectangle((0, 0, cfg.DISPLAY_WIDTH, cfg.DISPLAY_HEIGHT), fill=255)
        self.draw.rectangle((136, 15, 139, cfg.HORIZONTAL_LINE_MAIN), fill=0, width=0)
        self.draw.text((155, 36), "ZlsNas", font=self.font34, fill=0)
        self.draw.text((65, 36), cfg.ICON_NETWORK, font=self.nfont50, fill=0)
        self.draw.text((160, 71), "Loading...", font=self.font14, fill=0)

        self.update_display_and_save_image()

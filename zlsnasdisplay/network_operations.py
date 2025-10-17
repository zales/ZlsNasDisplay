#! /usr/bin/env python3
import logging
import socket
import subprocess
import time

import psutil
import requests


class NetworkOperations:
    @staticmethod
    def check_internet_connection() -> bool:
        """Detect an internet connection."""

        try:
            r = requests.get("https://google.com", timeout=5)
            r.raise_for_status()
            logging.debug("Internet connection detected.")
            return True
        except (
            requests.RequestException,
            requests.ConnectionError,
            requests.Timeout,
            Exception,
        ) as ex:
            logging.debug("Internet connection not detected.")
            logging.debug(f"{ex}")
            return False

    @staticmethod
    def get_signal_strength(interface: str = "wlan0") -> int | None:
        """Get the signal strength of the wireless network."""
        try:
            output = subprocess.check_output(
                ["/usr/sbin/iwconfig", interface],
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=5,
            )
            lines = output.split("\n")

            for line in lines:
                if "Signal level" in line:
                    index_start = line.index("Signal level=") + len("Signal level=")
                    index_end = line.index(" dBm")
                    signal_level = line[index_start:index_end]
                    return int(signal_level)

            # If signal strength information is not found
            logging.debug(f"Signal level not found in iwconfig output for {interface}")
            return None
        except subprocess.CalledProcessError as e:
            logging.debug(f"Error running iwconfig: {e.output}")
            return None
        except subprocess.TimeoutExpired:
            logging.warning(f"iwconfig command timed out for interface {interface}")
            return None
        except (ValueError, IndexError) as e:
            logging.warning(f"Failed to parse signal strength: {e}")
            return None
        except FileNotFoundError:
            logging.warning("iwconfig command not found - install wireless-tools package")
            return None

    @staticmethod
    def get_ip_address() -> str | None:
        """Get the IP address of the wireless network."""
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            return ip_address
        except socket.gaierror as e:
            logging.debug(f"Failed to resolve hostname to IP address: {e}")
            return None
        except Exception as e:
            logging.warning(f"Unexpected error getting IP address: {e}")
            return None


class TrafficMonitor:
    def get_current_traffic(self) -> tuple[float, str, float, str]:
        """Get the current network traffic."""
        try:
            interval = 1
            # Getting network traffic information
            net_io_start = psutil.net_io_counters()

            # Waiting for the specified interval
            time.sleep(interval)

            # Getting network traffic information after the start values
            net_io_end = psutil.net_io_counters()

            # Calculating the difference in network traffic
            download_bytes = net_io_end.bytes_recv - net_io_start.bytes_recv
            upload_bytes = net_io_end.bytes_sent - net_io_start.bytes_sent

            # Calculate download speed and choose appropriate unit
            download_speed, download_unit = self._choose_unit(download_bytes / interval)

            # Calculate upload speed and choose appropriate unit
            upload_speed, upload_unit = self._choose_unit(upload_bytes / interval)

            return download_speed, download_unit, upload_speed, upload_unit
        except (AttributeError, ValueError, TypeError, ZeroDivisionError) as e:
            logging.warning(f"Failed to get network traffic: {e}")
            return 0.0, "B", 0.0, "B"

    @staticmethod
    def _choose_unit(speed: float) -> tuple[float, str]:
        """Choose appropriate unit for speed."""
        for unit in ["B", "kB", "MB"]:
            if speed < 1024:
                return speed, unit
            speed /= 1024
        return speed, "GB"  # If speed exceeds GB/s

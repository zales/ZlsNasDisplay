#! /usr/bin/env python3
import logging
import subprocess
import time

import psutil
import requests as requests


class NetworkOperations:
    @staticmethod
    def check_internet_connection():
        """Detect an internet connection."""

        connection = None
        # noinspection PyBroadException
        try:
            r = requests.get("https://google.com")
            r.raise_for_status()
            logging.debug("Internet connection detected.")
            connection = True
        except Exception as ex:
            logging.debug("Internet connection not detected.")
            logging.debug(f"{ex}")
            connection = False
        finally:
            return connection

    def get_signal_strength(self="wlan0"):
        """Get the signal strength of the wireless network."""
        try:
            output = subprocess.check_output(
                ["/usr/sbin/iwconfig", self], stderr=subprocess.STDOUT, universal_newlines=True
            )
            lines = output.split("\n")

            for line in lines:
                if "Signal level" in line:
                    index_start = line.index("Signal level=") + len("Signal level=")
                    index_end = line.index(" dBm")
                    signal_level = line[index_start:index_end]
                    return int(signal_level)

            # If signal strength information is not found
            return None
        except subprocess.CalledProcessError as e:
            logging.debug(f"Error running iwconfig: {e.output}")
            return None

    @staticmethod
    def get_ip_address():
        """Get the IP address of the wireless network."""
        return psutil.net_if_addrs()["wlan0"][0].address

    @staticmethod
    def get_current_traffic():
        """Get the current network traffic."""

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

        # Converting bytes to megabytes and calculating the speed in MB/s
        download_speed = download_bytes / interval / (1024 * 1024)
        upload_speed = upload_bytes / interval / (1024 * 1024)

        return download_speed, upload_speed


#! /usr/bin/env python3
import ipaddress
import logging
import socket
import threading
import time

import psutil


class NetworkOperations:
    @staticmethod
    def _is_private_ip(ip: str) -> bool:
        """Check if IP address is private, loopback, or link-local."""
        try:
            addr = ipaddress.ip_address(ip)
            return addr.is_private or addr.is_loopback or addr.is_link_local
        except ValueError:
            # Invalid IP format, treat as private for safety
            return True

    @staticmethod
    def check_internet_connection() -> bool:
        """Detect internet connection via DNS query (faster than HTTP request)."""
        try:
            # Try to connect to Google's DNS server (8.8.8.8) on port 53
            # This is faster than HTTP request and works even if HTTP is blocked
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(3)
                sock.connect(("8.8.8.8", 53))
            logging.debug("Internet connection detected.")
            return True
        except (OSError, socket.timeout) as ex:
            logging.debug("Internet connection not detected.")
            logging.debug(f"{ex}")
            return False

    @staticmethod
    def get_signal_strength(interface: str = "wlan0") -> int | None:
        """Get the signal strength of the wireless network from /proc/net/wireless."""
        try:
            with open("/proc/net/wireless") as f:
                for line in f:
                    if interface in line:
                        # Format: Inter-| sta-|   Quality        |   Discarded packets
                        #  face | tus | link level noise |  nwid  crypt   frag  retry
                        # Example: wlan0: 0000   70.  -40.  -256        0      0      0
                        parts = line.split()
                        if len(parts) >= 4:
                            # parts[2] is link quality, parts[3] is signal level in dBm
                            signal_str = parts[3].rstrip(".")
                            return int(signal_str)
            # If interface not found in /proc/net/wireless
            logging.debug(f"Interface {interface} not found in /proc/net/wireless")
            return None
        except FileNotFoundError:
            logging.warning("/proc/net/wireless not found - wireless extensions not available")
            return None
        except (ValueError, IndexError) as e:
            logging.warning(f"Failed to parse signal strength from /proc/net/wireless: {e}")
            return None
        except Exception as e:
            logging.warning(f"Unexpected error reading signal strength: {e}")
            return None

    @staticmethod
    def get_ip_address(interface: str = "wlan0") -> str | None:
        """Get the IPv4 address of the specified network interface with fallback.

        Tries the specified interface first (default: wlan0).
        If not found or no valid IP, tries eth0.
        If still not found, returns the first valid non-loopback IP from any interface.
        """
        try:
            addrs = psutil.net_if_addrs()

            # Try specified interface first
            if interface in addrs:
                for addr in addrs[interface]:
                    if addr.family == socket.AF_INET:  # IPv4
                        ip = addr.address
                        # Use proper IP validation
                        if not NetworkOperations._is_private_ip(ip):
                            return ip

            # Fallback: Try eth0 if wlan0 was requested
            if interface == "wlan0" and "eth0" in addrs:
                for addr in addrs["eth0"]:
                    if addr.family == socket.AF_INET:
                        ip = addr.address
                        if not NetworkOperations._is_private_ip(ip):
                            return ip

            # Last resort: Return first valid IP from any interface
            for iface, iface_addrs in addrs.items():
                if iface.startswith("lo"):  # Skip loopback
                    continue
                for addr in iface_addrs:
                    if addr.family == socket.AF_INET:
                        ip = addr.address
                        # Use proper IP validation - allows private IPs as fallback
                        if not NetworkOperations._is_private_ip(ip):
                            logging.debug(f"Using IP from fallback interface {iface}: {ip}")
                            return ip

            # Ultimate fallback: Return first private IP if no public IP found
            for iface, iface_addrs in addrs.items():
                if iface.startswith("lo"):
                    continue
                for addr in iface_addrs:
                    if addr.family == socket.AF_INET:
                        ip = addr.address
                        # Accept any non-loopback IP
                        try:
                            addr_obj = ipaddress.ip_address(ip)
                            if not addr_obj.is_loopback:
                                logging.debug(f"Using private IP from interface {iface}: {ip}")
                                return ip
                        except ValueError:
                            continue

            logging.debug("No valid IPv4 address found on any interface")
            return None
        except Exception as e:
            logging.warning(f"Unexpected error getting IP address: {e}")
            return None


class TrafficMonitor:
    def __init__(self) -> None:
        """Initialize traffic monitor with cached measurements and thread safety."""
        self.last_measurement: psutil._common.snetio | None = None
        self.last_time: float | None = None
        self._lock = threading.Lock()

    def get_current_traffic(self) -> tuple[float, str, float, str]:
        """Get current network traffic using cached measurements (thread-safe, non-blocking)."""
        with self._lock:
            try:
                now = time.time()
                net_io_now = psutil.net_io_counters()

                if self.last_measurement is None or self.last_time is None:
                    # First measurement - initialize cache and return zeros
                    self.last_measurement = net_io_now
                    self.last_time = now
                    return 0.0, "B", 0.0, "B"

                # Calculate time interval since last measurement
                interval = now - self.last_time
                if interval < 0.1:  # Too soon, avoid division by very small numbers
                    return 0.0, "B", 0.0, "B"

                # Calculate bytes transferred since last measurement
                download_bytes = net_io_now.bytes_recv - self.last_measurement.bytes_recv
                upload_bytes = net_io_now.bytes_sent - self.last_measurement.bytes_sent

                # Update cache
                self.last_measurement = net_io_now
                self.last_time = now

                # Calculate speeds and choose appropriate units
                download_speed, download_unit = self._choose_unit(download_bytes / interval)
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

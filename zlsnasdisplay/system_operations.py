#! /usr/bin/env python3

import datetime
import logging

import apt
import psutil
from gpiozero import CPUTemperature

from zlsnasdisplay.network_operations import NetworkOperations


class SystemOperations:
    cpu = CPUTemperature(min_temp=30, max_temp=90)

    def get_cpu_temperature(self) -> int:
        """Get the CPU temperature in Celsius"""
        try:
            return int(self.cpu.temperature)
        except (AttributeError, ValueError, TypeError) as e:
            logging.warning(f"Failed to get CPU temperature: {e}")
            return 0

    @staticmethod
    def get_cpu_load() -> int:
        """Get the CPU load in percentage"""
        try:
            return int(psutil.cpu_percent())
        except (AttributeError, ValueError, TypeError) as e:
            logging.warning(f"Failed to get CPU load: {e}")
            return 0

    @staticmethod
    def get_fan_speed() -> int:
        """Get the fan speed in RPM"""
        try:
            fans = psutil.sensors_fans()
            if fans and "pwmfan" in fans and fans["pwmfan"]:
                return int(fans["pwmfan"][0].current)
            logging.debug("Fan sensor 'pwmfan' not available")
            return 0
        except (KeyError, IndexError, AttributeError, ValueError, TypeError) as e:
            logging.warning(f"Failed to get fan speed: {e}")
            return 0

    @staticmethod
    def check_updates(is_root: bool) -> int:
        """Check for available updates and return the number of packages that need to be updated."""
        try:
            # Initialize package manager cache
            cache = apt.Cache()
            # Update package informationa
            if is_root and NetworkOperations.check_internet_connection():
                cache.update()
            # Update package list
            cache.open(None)
            # Number of packages that need to be updated
            to_be_upgraded = sum(1 for pkg in cache if pkg.is_upgradable)
            # Close the cache
            cache.close()
            return to_be_upgraded
        except Exception as e:
            logging.warning(f"Failed to check for updates: {e}")
            return 0

    @staticmethod
    def get_mem() -> int:
        """Get the memory usage in percentage"""
        try:
            return int(psutil.virtual_memory().percent)
        except (AttributeError, ValueError, TypeError) as e:
            logging.warning(f"Failed to get memory usage: {e}")
            return 0

    @staticmethod
    def get_nvme_usage() -> int:
        """Get the NVMe disk usage in percentage"""
        try:
            return int(psutil.disk_usage("/").percent)
        except (AttributeError, ValueError, TypeError, OSError) as e:
            logging.warning(f"Failed to get NVMe disk usage: {e}")
            return 0

    @staticmethod
    def get_nvme_temp() -> int:
        """Get the NVMe disk temperature in Celsius"""
        try:
            temps = psutil.sensors_temperatures()
            if temps and "nvme" in temps and temps["nvme"]:
                return int(temps["nvme"][0].current)
            logging.debug("NVMe temperature sensor not available")
            return 0
        except (KeyError, IndexError, AttributeError, ValueError, TypeError) as e:
            logging.warning(f"Failed to get NVMe temperature: {e}")
            return 0

    @staticmethod
    def get_uptime() -> tuple[int, int, int]:
        """Get the system uptime in days, hours, and minutes"""
        try:
            # Getting system uptime information
            uptime_seconds = psutil.boot_time()
            # Converting time from seconds to a datetime object
            uptime_datetime = datetime.datetime.fromtimestamp(uptime_seconds)
            # Getting current time
            current_time = datetime.datetime.now()
            # Calculating system uptime
            system_uptime = current_time - uptime_datetime
            # Getting the number of days, hours, and minutes
            days = system_uptime.days
            hours, remainder = divmod(system_uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)

            return days, hours, minutes
        except (AttributeError, ValueError, TypeError, OSError) as e:
            logging.warning(f"Failed to get system uptime: {e}")
            return 0, 0, 0

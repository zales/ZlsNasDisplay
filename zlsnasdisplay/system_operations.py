#! /usr/bin/env python3

import datetime

import apt
import psutil
from gpiozero import CPUTemperature


class SystemOperations:
    cpu = CPUTemperature(min_temp=30, max_temp=90)

    def get_cpu_temperature(self):
        """Get the CPU temperature in Celsius"""
        return int(self.cpu.temperature)

    @staticmethod
    def get_cpu_load():
        """Get the CPU load in percentage"""
        return int(psutil.cpu_percent())

    @staticmethod
    def get_fan_speed():
        """Get the fan speed in RPM"""
        return psutil.sensors_fans()["pwmfan"][0].current

    @staticmethod
    def check_updates(is_root):
        """Check for available updates and return the number of packages that need to be updated."""
        # Initialize package manager cache
        cache = apt.Cache()
        # Update package informationa
        if is_root:
            cache.update()
        # Update package list
        cache.open(None)
        # Number of packages that need to be updated
        to_be_upgraded = sum(1 for pkg in cache if pkg.is_upgradable)
        # Close the cache
        cache.close()
        return to_be_upgraded

    @staticmethod
    def get_mem():
        """Get the memory usage in percentage"""
        return int(psutil.virtual_memory().percent)

    @staticmethod
    def get_nvme_usage():
        """Get the NVMe disk usage in percentage"""
        return int(psutil.disk_usage("/").percent)

    @staticmethod
    def get_nvme_temp():
        """Get the NVMe disk temperature in Celsius"""
        return int(psutil.sensors_temperatures()["nvme"][0].current)

    @staticmethod
    def get_uptime():
        """Get the system uptime in days, hours, and minutes"""
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

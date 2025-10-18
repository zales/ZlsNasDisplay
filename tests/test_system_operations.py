#! /usr/bin/env python3

import datetime
from unittest import mock

import pytest

from zlsnasdisplay.system_operations import SystemOperations


class TestSystemOperations:
    """Tests for SystemOperations class."""

    def test_get_cpu_load_success(self):
        """Test successful CPU load retrieval using cached cpu_times."""
        # Create mock cpu_times namedtuple-like objects
        from collections import namedtuple
        CPUTimes = namedtuple('scputimes', ['user', 'nice', 'system', 'idle', 'iowait'])

        # First call - initial measurement
        initial_times = CPUTimes(user=1000.0, nice=50.0, system=500.0, idle=3000.0, iowait=450.0)
        # Second call - after some CPU usage (55% usage: 550 active out of 1000 total)
        final_times = CPUTimes(user=1300.0, nice=60.0, system=690.0, idle=3400.0, iowait=550.0)

        with mock.patch("zlsnasdisplay.system_operations.psutil.cpu_times") as mock_cpu_times:
            with mock.patch("zlsnasdisplay.system_operations.psutil.cpu_percent") as mock_cpu_percent:
                mock_cpu_times.side_effect = [initial_times, final_times]

                # First call - initialize cache
                result1 = SystemOperations.get_cpu_load()
                assert result1 == 0  # First call returns 0

                # Second call - calculate from deltas
                result2 = SystemOperations.get_cpu_load()
                # Total delta = 1000, idle delta = 400 + 100 = 500, usage = (1000-500)/1000 = 50%
                assert 45 <= result2 <= 55  # Allow some rounding variance

    def test_get_cpu_load_exception(self):
        """Test CPU load retrieval with exception."""
        with mock.patch("zlsnasdisplay.system_operations.psutil.cpu_times") as mock_cpu:
            mock_cpu.side_effect = AttributeError("Test error")
            result = SystemOperations.get_cpu_load()
            assert result == 0

    def test_get_fan_speed_success(self):
        """Test successful fan speed retrieval."""
        mock_fan = mock.MagicMock()
        mock_fan.current = 2500.0

        with mock.patch("zlsnasdisplay.system_operations.psutil.sensors_fans") as mock_fans:
            mock_fans.return_value = {"pwmfan": [mock_fan]}
            result = SystemOperations.get_fan_speed()
            assert result == 2500

    def test_get_fan_speed_missing_sensor(self):
        """Test fan speed retrieval when sensor is missing."""
        with mock.patch("zlsnasdisplay.system_operations.psutil.sensors_fans") as mock_fans:
            mock_fans.return_value = {}
            result = SystemOperations.get_fan_speed()
            assert result == 0

    def test_get_fan_speed_empty_list(self):
        """Test fan speed retrieval when sensor list is empty."""
        with mock.patch("zlsnasdisplay.system_operations.psutil.sensors_fans") as mock_fans:
            mock_fans.return_value = {"pwmfan": []}
            result = SystemOperations.get_fan_speed()
            assert result == 0

    def test_get_fan_speed_exception(self):
        """Test fan speed retrieval with exception."""
        with mock.patch("zlsnasdisplay.system_operations.psutil.sensors_fans") as mock_fans:
            mock_fans.side_effect = KeyError("Test error")
            result = SystemOperations.get_fan_speed()
            assert result == 0

    def test_get_mem_success(self):
        """Test successful memory usage retrieval."""
        mock_mem = mock.MagicMock()
        mock_mem.percent = 62.5

        with mock.patch(
            "zlsnasdisplay.system_operations.psutil.virtual_memory"
        ) as mock_virtual_mem:
            mock_virtual_mem.return_value = mock_mem
            result = SystemOperations.get_mem()
            assert result == 62

    def test_get_mem_exception(self):
        """Test memory usage retrieval with exception."""
        with mock.patch(
            "zlsnasdisplay.system_operations.psutil.virtual_memory"
        ) as mock_virtual_mem:
            mock_virtual_mem.side_effect = AttributeError("Test error")
            result = SystemOperations.get_mem()
            assert result == 0

    def test_get_nvme_usage_success(self):
        """Test successful NVMe disk usage retrieval."""
        mock_disk = mock.MagicMock()
        mock_disk.percent = 75.3

        with mock.patch("zlsnasdisplay.system_operations.psutil.disk_usage") as mock_disk_usage:
            mock_disk_usage.return_value = mock_disk
            result = SystemOperations.get_nvme_usage()
            assert result == 75
            mock_disk_usage.assert_called_once_with("/")

    def test_get_nvme_usage_exception(self):
        """Test NVMe disk usage retrieval with exception."""
        with mock.patch("zlsnasdisplay.system_operations.psutil.disk_usage") as mock_disk_usage:
            mock_disk_usage.side_effect = OSError("Test error")
            result = SystemOperations.get_nvme_usage()
            assert result == 0

    def test_get_nvme_temp_success(self):
        """Test successful NVMe temperature retrieval."""
        mock_temp = mock.MagicMock()
        mock_temp.current = 45.0

        with mock.patch(
            "zlsnasdisplay.system_operations.psutil.sensors_temperatures"
        ) as mock_temps:
            mock_temps.return_value = {"nvme": [mock_temp]}
            result = SystemOperations.get_nvme_temp()
            assert result == 45

    def test_get_nvme_temp_missing_sensor(self):
        """Test NVMe temperature retrieval when sensor is missing."""
        with mock.patch(
            "zlsnasdisplay.system_operations.psutil.sensors_temperatures"
        ) as mock_temps:
            mock_temps.return_value = {}
            result = SystemOperations.get_nvme_temp()
            assert result == 0

    def test_get_nvme_temp_empty_list(self):
        """Test NVMe temperature retrieval when sensor list is empty."""
        with mock.patch(
            "zlsnasdisplay.system_operations.psutil.sensors_temperatures"
        ) as mock_temps:
            mock_temps.return_value = {"nvme": []}
            result = SystemOperations.get_nvme_temp()
            assert result == 0

    def test_get_nvme_temp_exception(self):
        """Test NVMe temperature retrieval with exception."""
        with mock.patch(
            "zlsnasdisplay.system_operations.psutil.sensors_temperatures"
        ) as mock_temps:
            mock_temps.side_effect = KeyError("Test error")
            result = SystemOperations.get_nvme_temp()
            assert result == 0

    def test_get_uptime_success(self):
        """Test successful uptime retrieval."""
        # Mock boot time to 2 days, 3 hours, 30 minutes ago
        mock_boot_time = (
            datetime.datetime.now() - datetime.timedelta(days=2, hours=3, minutes=30)
        ).timestamp()

        with mock.patch("zlsnasdisplay.system_operations.psutil.boot_time") as mock_boot:
            mock_boot.return_value = mock_boot_time
            days, hours, minutes = SystemOperations.get_uptime()

            assert days == 2
            assert hours == 3
            # Minutes might be 29 or 30 due to timing, so allow a small range
            assert 29 <= minutes <= 31

    def test_get_uptime_exception(self):
        """Test uptime retrieval with exception."""
        with mock.patch("zlsnasdisplay.system_operations.psutil.boot_time") as mock_boot:
            mock_boot.side_effect = OSError("Test error")
            result = SystemOperations.get_uptime()
            assert result == (0, 0, 0)

    def test_check_updates_success_with_updates(self):
        """Test successful update check with available updates."""
        mock_cache = mock.MagicMock()
        mock_pkg1 = mock.MagicMock()
        mock_pkg1.is_upgradable = True
        mock_pkg2 = mock.MagicMock()
        mock_pkg2.is_upgradable = False
        mock_pkg3 = mock.MagicMock()
        mock_pkg3.is_upgradable = True

        mock_cache.__iter__ = mock.Mock(return_value=iter([mock_pkg1, mock_pkg2, mock_pkg3]))

        with mock.patch("zlsnasdisplay.system_operations.apt.Cache") as mock_apt:
            with mock.patch(
                "zlsnasdisplay.system_operations.NetworkOperations.check_internet_connection"
            ) as mock_net:
                mock_apt.return_value = mock_cache
                mock_net.return_value = True

                result = SystemOperations.check_updates(is_root=True)

                assert result == 2
                mock_cache.update.assert_called_once()
                mock_cache.open.assert_called_once()
                mock_cache.close.assert_called_once()

    def test_check_updates_no_internet(self):
        """Test update check without internet connection."""
        mock_cache = mock.MagicMock()
        mock_cache.__iter__ = mock.Mock(return_value=iter([]))

        with mock.patch("zlsnasdisplay.system_operations.apt.Cache") as mock_apt:
            with mock.patch(
                "zlsnasdisplay.system_operations.NetworkOperations.check_internet_connection"
            ) as mock_net:
                mock_apt.return_value = mock_cache
                mock_net.return_value = False

                result = SystemOperations.check_updates(is_root=True)

                assert result == 0
                mock_cache.update.assert_not_called()

    def test_check_updates_not_root(self):
        """Test update check when not running as root."""
        mock_cache = mock.MagicMock()
        mock_cache.__iter__ = mock.Mock(return_value=iter([]))

        with mock.patch("zlsnasdisplay.system_operations.apt.Cache") as mock_apt:
            with mock.patch(
                "zlsnasdisplay.system_operations.NetworkOperations.check_internet_connection"
            ) as mock_net:
                mock_apt.return_value = mock_cache
                mock_net.return_value = True

                result = SystemOperations.check_updates(is_root=False)

                assert result == 0
                mock_cache.update.assert_not_called()

    def test_check_updates_exception(self):
        """Test update check with exception."""
        with mock.patch("zlsnasdisplay.system_operations.apt.Cache") as mock_apt:
            mock_apt.side_effect = Exception("Test error")
            result = SystemOperations.check_updates(is_root=True)
            assert result == 0

#! /usr/bin/env python3

"""Tests for Matter device integration."""

import unittest
from unittest.mock import MagicMock, patch

import pytest


class TestMatterDevice(unittest.TestCase):
    """Test Matter device functionality."""

    @patch("zlsnasdisplay.matter_device.CIRCUITMATTER_AVAILABLE", True)
    @patch("zlsnasdisplay.matter_device.cm")
    def test_create_matter_device_success(self, mock_cm: MagicMock) -> None:
        """Test successful Matter device creation."""
        from zlsnasdisplay.matter_device import create_matter_device

        device = create_matter_device("TestNAS", 0xFFF1, 0x8001)
        assert device is not None
        assert device.device_name == "TestNAS"

    @patch("zlsnasdisplay.matter_device.CIRCUITMATTER_AVAILABLE", False)
    def test_create_matter_device_unavailable(self) -> None:
        """Test Matter device creation when CircuitMatter is unavailable."""
        from zlsnasdisplay.matter_device import create_matter_device

        device = create_matter_device()
        assert device is None

    @patch("zlsnasdisplay.matter_device.CIRCUITMATTER_AVAILABLE", True)
    @patch("zlsnasdisplay.matter_device.cm")
    @patch("zlsnasdisplay.matter_device.SystemOperations")
    def test_cpu_temperature_sensor_update(
        self, mock_sys_ops: MagicMock, mock_cm: MagicMock
    ) -> None:
        """Test CPU temperature sensor updates."""
        from zlsnasdisplay.matter_device import CPUTemperatureSensor

        # Mock system operations
        mock_system_ops = MagicMock()
        mock_system_ops.get_cpu_temperature.return_value = 45.5

        sensor = CPUTemperatureSensor("CPU Temp", mock_system_ops)
        sensor.update_temperature()

        # Matter expects temperature in 0.01°C units
        assert sensor._temp.MeasuredValue == 4550

    @patch("zlsnasdisplay.matter_device.CIRCUITMATTER_AVAILABLE", True)
    @patch("zlsnasdisplay.matter_device.cm")
    @patch("zlsnasdisplay.matter_device.SystemOperations")
    def test_nvme_temperature_sensor_update(
        self, mock_sys_ops: MagicMock, mock_cm: MagicMock
    ) -> None:
        """Test NVMe temperature sensor updates."""
        from zlsnasdisplay.matter_device import NVMeTemperatureSensor

        # Mock static method
        mock_sys_ops.get_nvme_temp.return_value = 38.2

        sensor = NVMeTemperatureSensor("NVMe Temp")
        sensor.update_temperature()

        # Matter expects temperature in 0.01°C units
        assert sensor._temp.MeasuredValue == 3820

    @patch("zlsnasdisplay.matter_device.CIRCUITMATTER_AVAILABLE", True)
    @patch("zlsnasdisplay.matter_device.cm")
    @patch("zlsnasdisplay.matter_device.SystemOperations")
    @patch("zlsnasdisplay.matter_device.NetworkOperations")
    @patch("zlsnasdisplay.matter_device.TrafficMonitor")
    def test_matter_device_start(
        self,
        mock_traffic: MagicMock,
        mock_net_ops: MagicMock,
        mock_sys_ops: MagicMock,
        mock_cm: MagicMock,
    ) -> None:
        """Test starting the Matter device."""
        from zlsnasdisplay.matter_device import NASMatterDevice

        device = NASMatterDevice("TestNAS")
        mock_matter_instance = MagicMock()
        mock_cm.CircuitMatter.return_value = mock_matter_instance

        device.start()

        assert device.matter is not None
        mock_matter_instance.add_device.assert_called()

    @patch("zlsnasdisplay.matter_device.CIRCUITMATTER_AVAILABLE", True)
    @patch("zlsnasdisplay.matter_device.cm")
    @patch("zlsnasdisplay.matter_device.SystemOperations")
    @patch("zlsnasdisplay.matter_device.NetworkOperations")
    @patch("zlsnasdisplay.matter_device.TrafficMonitor")
    def test_matter_device_update_metrics(
        self,
        mock_traffic: MagicMock,
        mock_net_ops: MagicMock,
        mock_sys_ops: MagicMock,
        mock_cm: MagicMock,
    ) -> None:
        """Test updating Matter device metrics."""
        from zlsnasdisplay.matter_device import NASMatterDevice

        # Mock system operations instance
        mock_sys_instance = MagicMock()
        mock_sys_instance.get_cpu_temperature.return_value = 50.0
        mock_sys_ops.return_value = mock_sys_instance
        mock_sys_ops.get_nvme_temp.return_value = 40.0

        device = NASMatterDevice("TestNAS")
        device.update_metrics()

        # Verify temperature sensors were updated
        mock_sys_instance.get_cpu_temperature.assert_called()

    @patch("zlsnasdisplay.matter_device.CIRCUITMATTER_AVAILABLE", True)
    @patch("zlsnasdisplay.matter_device.cm")
    @patch("zlsnasdisplay.matter_device.SystemOperations")
    @patch("zlsnasdisplay.matter_device.NetworkOperations")
    @patch("zlsnasdisplay.matter_device.TrafficMonitor")
    def test_matter_device_process_packets(
        self,
        mock_traffic: MagicMock,
        mock_net_ops: MagicMock,
        mock_sys_ops: MagicMock,
        mock_cm: MagicMock,
    ) -> None:
        """Test processing Matter packets."""
        from zlsnasdisplay.matter_device import NASMatterDevice

        device = NASMatterDevice("TestNAS")
        mock_matter_instance = MagicMock()
        mock_cm.CircuitMatter.return_value = mock_matter_instance

        device.start()
        device.process_packets()

        mock_matter_instance.process_packets.assert_called_once()

    @patch("zlsnasdisplay.matter_device.CIRCUITMATTER_AVAILABLE", False)
    def test_matter_device_unavailable_raises(self) -> None:
        """Test that creating Matter device raises when CircuitMatter unavailable."""
        from zlsnasdisplay.matter_device import NASMatterDevice

        with pytest.raises(ImportError):
            NASMatterDevice("TestNAS")

    @patch("zlsnasdisplay.matter_device.CIRCUITMATTER_AVAILABLE", True)
    @patch("zlsnasdisplay.matter_device.cm")
    @patch("zlsnasdisplay.matter_device.SystemOperations")
    @patch("zlsnasdisplay.matter_device.NetworkOperations")
    @patch("zlsnasdisplay.matter_device.TrafficMonitor")
    def test_matter_device_is_available(
        self,
        mock_traffic: MagicMock,
        mock_net_ops: MagicMock,
        mock_sys_ops: MagicMock,
        mock_cm: MagicMock,
    ) -> None:
        """Test checking if Matter is available."""
        from zlsnasdisplay.matter_device import NASMatterDevice

        device = NASMatterDevice("TestNAS")
        assert device.is_available() is True


if __name__ == "__main__":
    unittest.main()

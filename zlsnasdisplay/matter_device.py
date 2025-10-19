#! /usr/bin/env python3

"""
Matter Device Integration for ZlsNasDisplay

Exposes NAS system metrics as Matter sensors using CircuitMatter.
Uses standard Matter clusters for maximum compatibility with Matter controllers.
"""

import logging
from typing import Optional

try:
    import circuitmatter as cm
    from circuitmatter.clusters.general.identify import Identify
    from circuitmatter.clusters.measurement.relative_humidity_measurement import (
        RelativeHumidityMeasurement,
    )
    from circuitmatter.clusters.measurement.temperature_measurement import (
        TemperatureMeasurement,
    )
    from circuitmatter.device_types.simple_device import SimpleDevice

    CIRCUITMATTER_AVAILABLE = True
except ImportError as e:
    CIRCUITMATTER_AVAILABLE = False
    logging.warning(f"CircuitMatter not available - Matter integration disabled: {e}")

    # Create dummy classes if CircuitMatter not available
    class SimpleDevice:  # type: ignore[no-redef]
        """Dummy SimpleDevice class when CircuitMatter is not available."""

        pass

    class TemperatureMeasurement:  # type: ignore[no-redef]
        """Dummy TemperatureMeasurement class when CircuitMatter is not available."""

        pass

from zlsnasdisplay.network_operations import NetworkOperations, TrafficMonitor
from zlsnasdisplay.system_operations import SystemOperations


# Patch for CircuitMatter serialization bugs in system model clusters
# Override restore method to skip problematic clusters
def patched_restore(self: SimpleDevice, nonvolatile: dict) -> None:  # type: ignore[misc]
    """Restore device state, skipping clusters with serialization bugs."""
    self.nonvolatile = nonvolatile
    for server in self.servers:
        cluster_hex = hex(server.CLUSTER_ID)
        # Skip clusters that have serialization issues with Structure->dict conversion
        # 0x001D = Descriptor, 0x001F = AccessControl, 0x001E = Binding
        if server.CLUSTER_ID in (0x001D, 0x001F, 0x001E):
            continue
        if cluster_hex not in nonvolatile:
            nonvolatile[cluster_hex] = {}
        server.restore(nonvolatile[cluster_hex])


# Monkey patch SimpleDevice.restore
SimpleDevice.restore = patched_restore  # type: ignore[method-assign]


class CPUTemperatureSensor(SimpleDevice):  # type: ignore[misc]
    """Matter temperature sensor for CPU temperature."""

    DEVICE_TYPE_ID = 0x0302  # Temperature Sensor
    REVISION = 2

    def __init__(self, name: str, system_ops: SystemOperations) -> None:
        super().__init__(name)
        self.system_ops = system_ops

        self._identify = Identify()
        self.servers.append(self._identify)

        self._temp = TemperatureMeasurement()
        self.servers.append(self._temp)
        # Initialize with current temperature
        self.update_temperature()

    def restore(self, nonvolatile: dict) -> None:  # type: ignore[override]
        """Restore device state and set user labels."""
        super().restore(nonvolatile)
        # Set user labels after restore to help identify this sensor
        if not self.user_label.LabelList:
            label1 = self.user_label.LabelStruct()
            label1.Label = "type"
            label1.Value = "CPU"
            label2 = self.user_label.LabelStruct()
            label2.Label = "location"
            label2.Value = "Processor"
            self.user_label.LabelList = [label1, label2]

    def update_temperature(self) -> None:
        """Update the temperature measurement from system."""
        temp_celsius = self.system_ops.get_cpu_temperature()
        # Matter expects temperature in 0.01°C units (hundredths of a degree)
        self._temp.MeasuredValue = int(temp_celsius * 100)


class NVMeTemperatureSensor(SimpleDevice):  # type: ignore[misc]
    """Matter temperature sensor for NVMe disk temperature."""

    DEVICE_TYPE_ID = 0x0302  # Temperature Sensor
    REVISION = 2

    def __init__(self, name: str) -> None:
        super().__init__(name)

        self._identify = Identify()
        self.servers.append(self._identify)

        self._temp = TemperatureMeasurement()
        self.servers.append(self._temp)
        # Initialize with current temperature
        self.update_temperature()

    def restore(self, nonvolatile: dict) -> None:  # type: ignore[override]
        """Restore device state and set user labels."""
        super().restore(nonvolatile)
        # Set user labels after restore to help identify this sensor
        if not self.user_label.LabelList:
            label1 = self.user_label.LabelStruct()
            label1.Label = "type"
            label1.Value = "NVMe"
            label2 = self.user_label.LabelStruct()
            label2.Label = "location"
            label2.Value = "Storage"
            self.user_label.LabelList = [label1, label2]

    def update_temperature(self) -> None:
        """Update the temperature measurement from system."""
        temp_celsius = SystemOperations.get_nvme_temp()
        # Matter expects temperature in 0.01°C units (hundredths of a degree)
        self._temp.MeasuredValue = int(temp_celsius * 100)


class CPULoadSensor(SimpleDevice):  # type: ignore[misc]
    """Matter humidity sensor for CPU load (using humidity cluster for percentage)."""

    DEVICE_TYPE_ID = 0x0307  # Humidity Sensor
    REVISION = 3

    def __init__(self, name: str, system_ops: SystemOperations) -> None:
        super().__init__(name)
        self.system_ops = system_ops

        self._identify = Identify()
        self.servers.append(self._identify)

        self._humidity = RelativeHumidityMeasurement()
        self.servers.append(self._humidity)
        # Initialize with current CPU load
        self.update_load()

    def restore(self, nonvolatile: dict) -> None:  # type: ignore[override]
        """Restore device state and set user labels."""
        super().restore(nonvolatile)
        # Set user labels after restore to help identify this sensor
        if not self.user_label.LabelList:
            label1 = self.user_label.LabelStruct()
            label1.Label = "type"
            label1.Value = "CPU Load"
            label2 = self.user_label.LabelStruct()
            label2.Label = "unit"
            label2.Value = "percent"
            self.user_label.LabelList = [label1, label2]

    def update_load(self) -> None:
        """Update the CPU load measurement from system."""
        cpu_load = self.system_ops.get_cpu_load()
        # Humidity cluster expects value in 0.01% units (hundredths of a percent)
        self._humidity.MeasuredValue = int(cpu_load * 100)


class MemoryUsageSensor(SimpleDevice):  # type: ignore[misc]
    """Matter humidity sensor for memory usage (using humidity cluster for percentage)."""

    DEVICE_TYPE_ID = 0x0307  # Humidity Sensor
    REVISION = 3

    def __init__(self, name: str, system_ops: SystemOperations) -> None:
        super().__init__(name)
        self.system_ops = system_ops

        self._identify = Identify()
        self.servers.append(self._identify)

        self._humidity = RelativeHumidityMeasurement()
        self.servers.append(self._humidity)
        # Initialize with current memory usage
        self.update_usage()

    def restore(self, nonvolatile: dict) -> None:  # type: ignore[override]
        """Restore device state and set user labels."""
        super().restore(nonvolatile)
        # Set user labels after restore to help identify this sensor
        if not self.user_label.LabelList:
            label1 = self.user_label.LabelStruct()
            label1.Label = "type"
            label1.Value = "Memory"
            label2 = self.user_label.LabelStruct()
            label2.Label = "unit"
            label2.Value = "percent"
            self.user_label.LabelList = [label1, label2]

    def update_usage(self) -> None:
        """Update the memory usage measurement from system."""
        mem_usage = self.system_ops.get_mem()
        # Humidity cluster expects value in 0.01% units (hundredths of a percent)
        self._humidity.MeasuredValue = int(mem_usage * 100)


class DiskUsageSensor(SimpleDevice):  # type: ignore[misc]
    """Matter humidity sensor for disk usage (using humidity cluster for percentage)."""

    DEVICE_TYPE_ID = 0x0307  # Humidity Sensor
    REVISION = 3

    def __init__(self, name: str, system_ops: SystemOperations) -> None:
        super().__init__(name)
        self.system_ops = system_ops

        self._identify = Identify()
        self.servers.append(self._identify)

        self._humidity = RelativeHumidityMeasurement()
        self.servers.append(self._humidity)
        # Initialize with current disk usage
        self.update_usage()

    def restore(self, nonvolatile: dict) -> None:  # type: ignore[override]
        """Restore device state and set user labels."""
        super().restore(nonvolatile)
        # Set user labels after restore to help identify this sensor
        if not self.user_label.LabelList:
            label1 = self.user_label.LabelStruct()
            label1.Label = "type"
            label1.Value = "Disk"
            label2 = self.user_label.LabelStruct()
            label2.Label = "unit"
            label2.Value = "percent"
            self.user_label.LabelList = [label1, label2]

    def update_usage(self) -> None:
        """Update the disk usage measurement from system."""
        disk_usage = self.system_ops.get_nvme_usage()
        # Humidity cluster expects value in 0.01% units (hundredths of a percent)
        self._humidity.MeasuredValue = int(disk_usage * 100)


class NASMatterDevice:
    """
    Main Matter device that exposes NAS metrics as multiple sensor endpoints.

    Provides:
    - CPU Temperature sensor
    - NVMe Temperature sensor

    Each metric is exposed as a separate Matter endpoint for better organization
    and compatibility with Matter controllers like Home Assistant.
    """

    def __init__(
        self,
        device_name: str = "ZlsNAS",
        vendor_id: int = 0xFFF1,
        product_id: int = 0x8001,
    ) -> None:
        """
        Initialize the Matter device.

        Args:
            device_name: Human-readable device name
            vendor_id: Matter vendor ID (0xFFF1 = test vendor)
            product_id: Matter product ID
        """
        if not CIRCUITMATTER_AVAILABLE:
            raise ImportError("CircuitMatter library is not installed")

        self.device_name = device_name
        self.matter: Optional[cm.CircuitMatter] = None

        # Initialize system operations
        self.system_ops = SystemOperations()
        self.network_ops = NetworkOperations()
        self.traffic_monitor = TrafficMonitor()

        # Create Matter sensors with descriptive names
        self.cpu_temp_sensor = CPUTemperatureSensor(
            "CPU Temperature", self.system_ops
        )
        self.nvme_temp_sensor = NVMeTemperatureSensor("NVMe Temperature")
        self.cpu_load_sensor = CPULoadSensor("CPU Load", self.system_ops)
        self.memory_sensor = MemoryUsageSensor("Memory Usage", self.system_ops)
        self.disk_sensor = DiskUsageSensor("Disk Usage", self.system_ops)

        logging.info(f"Initialized Matter device: {device_name}")

    def start(self, vendor_id: int = 0xFFF1, product_id: int = 0x8001) -> None:
        """Start the Matter server."""
        if not CIRCUITMATTER_AVAILABLE:
            raise ImportError("CircuitMatter library is not installed")

        # Configure CircuitMatter logging
        # Set to INFO to see commissioning messages, DEBUG for full protocol details
        cm_logger = logging.getLogger("circuitmatter")
        cm_logger.setLevel(logging.INFO)

        self.matter = cm.CircuitMatter(
            vendor_id=vendor_id,
            product_id=product_id,
            product_name=self.device_name
        )

        # Add all sensor devices
        self.matter.add_device(self.cpu_temp_sensor)
        self.matter.add_device(self.nvme_temp_sensor)
        self.matter.add_device(self.cpu_load_sensor)
        self.matter.add_device(self.memory_sensor)
        self.matter.add_device(self.disk_sensor)

        # Store commissioning info for QR code display
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.discriminator = self.matter.nonvolatile["discriminator"]
        self.passcode = self.matter.nonvolatile["passcode"]

        logging.info("Matter device started - ready for commissioning")
        logging.info("Scan the QR code displayed in the console to add device")

    def update_metrics(self) -> None:
        """Update all sensor values from system metrics."""
        try:
            self.cpu_temp_sensor.update_temperature()
            self.nvme_temp_sensor.update_temperature()
            self.cpu_load_sensor.update_load()
            self.memory_sensor.update_usage()
            self.disk_sensor.update_usage()
        except Exception as e:
            logging.error(f"Failed to update Matter metrics: {e}")

    def process_packets(self) -> None:
        """Process incoming Matter packets. Should be called regularly."""
        if self.matter is not None:
            self.matter.process_packets()

    def is_available(self) -> bool:
        """Check if Matter integration is available."""
        return CIRCUITMATTER_AVAILABLE

    def get_qr_code_image(self, box_size: int = 2) -> Optional[any]:
        """
        Generate QR code as PIL Image for Matter commissioning.

        Args:
            box_size: Size of each QR code box in pixels

        Returns:
            PIL Image object or None if not available
        """
        if not CIRCUITMATTER_AVAILABLE or not hasattr(self, 'discriminator'):
            return None

        try:
            from circuitmatter import pase
            from PIL import Image
            import qrcode

            # Generate QR code data
            qr_data = pase.compute_qr_code(
                self.vendor_id,
                self.product_id,
                self.discriminator,
                self.passcode
            )

            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=box_size,
                border=1,
            )
            qr.add_data("MT:" + qr_data)
            qr.make(fit=True)

            # Convert to PIL Image (black and white)
            qr_img = qr.make_image(fill_color="black", back_color="white")

            return qr_img

        except Exception as e:
            logging.error(f"Failed to generate QR code: {e}")
            return None

    def get_manual_code(self) -> Optional[str]:
        """Get the manual pairing code for Matter commissioning."""
        if not CIRCUITMATTER_AVAILABLE or not hasattr(self, 'passcode'):
            return None
        # PersistentDictionary uses dict access syntax
        if self.matter and "manual_code" in self.matter.nonvolatile:
            return self.matter.nonvolatile["manual_code"]
        return None


def create_matter_device(
    device_name: str = "ZlsNAS",
    vendor_id: int = 0xFFF1,
    product_id: int = 0x8001,
) -> Optional[NASMatterDevice]:
    """
    Factory function to create a Matter device.

    Returns:
        NASMatterDevice instance or None if CircuitMatter is not available
    """
    if not CIRCUITMATTER_AVAILABLE:
        logging.warning("CircuitMatter not available - Matter integration disabled")
        return None

    try:
        device = NASMatterDevice(device_name, vendor_id, product_id)
        return device
    except Exception as e:
        logging.error(f"Failed to create Matter device: {e}")
        return None

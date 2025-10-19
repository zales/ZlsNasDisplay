"""Pytest configuration and fixtures for testing without hardware dependencies."""

import sys
from unittest.mock import MagicMock

# Mock hardware dependencies BEFORE any imports
# This prevents GPIO/SPI initialization errors in CI environments


def mock_hardware_modules():
    """Mock hardware-specific modules for testing without Raspberry Pi."""
    # Mock lgpio (low-level GPIO library)
    mock_lgpio = MagicMock()
    sys.modules["lgpio"] = mock_lgpio

    # Mock spidev (SPI library)
    mock_spidev = MagicMock()
    mock_spi_instance = MagicMock()
    mock_spidev.SpiDev.return_value = mock_spi_instance
    sys.modules["spidev"] = mock_spidev

    # Mock gpiozero with proper pin factory
    mock_gpiozero = MagicMock()

    # Create mock LED class
    class MockLED:
        def __init__(self, *args, **kwargs):
            self.value = 0

        def on(self):
            self.value = 1

        def off(self):
            self.value = 0

        def close(self):
            pass

    # Create mock Button class
    class MockButton:
        def __init__(self, *args, **kwargs):
            self.value = 0

        def close(self):
            pass

    mock_gpiozero.LED = MockLED
    mock_gpiozero.Button = MockButton
    mock_gpiozero.CPUTemperature = MagicMock
    sys.modules["gpiozero"] = mock_gpiozero


# Mock hardware modules before any test imports
mock_hardware_modules()

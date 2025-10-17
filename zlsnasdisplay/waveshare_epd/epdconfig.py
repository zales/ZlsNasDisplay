import logging
import time
from typing import List

import gpiozero
import spidev

logger = logging.getLogger(__name__)


class RaspberryPi:
    """Raspberry Pi GPIO and SPI interface for e-ink display"""

    # Pin definition
    RST_PIN = 17
    DC_PIN = 25
    CS_PIN = 8
    BUSY_PIN = 24
    PWR_PIN = 18

    def __init__(self) -> None:
        self.SPI = spidev.SpiDev()
        self.GPIO_RST_PIN = gpiozero.LED(self.RST_PIN)
        self.GPIO_DC_PIN = gpiozero.LED(self.DC_PIN)
        self.GPIO_PWR_PIN = gpiozero.LED(self.PWR_PIN)
        self.GPIO_BUSY_PIN = gpiozero.Button(self.BUSY_PIN, pull_up=False)

    def digital_write(self, pin: int, value: int) -> None:
        """Write digital value to GPIO pin"""
        if pin == self.RST_PIN:
            if value:
                self.GPIO_RST_PIN.on()
            else:
                self.GPIO_RST_PIN.off()
        elif pin == self.DC_PIN:
            if value:
                self.GPIO_DC_PIN.on()
            else:
                self.GPIO_DC_PIN.off()
        elif pin == self.PWR_PIN:
            if value:
                self.GPIO_PWR_PIN.on()
            else:
                self.GPIO_PWR_PIN.off()

    def digital_read(self, pin: int) -> int:
        """Read digital value from GPIO pin"""
        if pin == self.BUSY_PIN:
            return self.GPIO_BUSY_PIN.value
        elif pin == self.RST_PIN:
            return self.RST_PIN
        elif pin == self.DC_PIN:
            return self.DC_PIN
        elif pin == self.PWR_PIN:
            return self.PWR_PIN
        return 0

    def delay_ms(self, delay_time: int) -> None:
        """Delay for specified milliseconds"""
        time.sleep(delay_time / 1000.0)

    def spi_writebyte(self, data: List[int]) -> None:
        """Write single bytes via SPI"""
        self.SPI.writebytes(data)

    def spi_writebyte2(self, data: List[int]) -> None:
        """Write large buffer via SPI (optimized)"""
        self.SPI.writebytes2(data)

    def module_init(self) -> int:
        """Initialize SPI and GPIO modules"""
        self.GPIO_PWR_PIN.on()

        # SPI device, bus = 0, device = 0
        self.SPI.open(0, 0)
        self.SPI.max_speed_hz = 4000000
        self.SPI.mode = 0b00
        return 0

    def module_exit(self, cleanup: bool = False) -> None:
        """Shutdown SPI and GPIO modules"""
        logger.debug("spi end")
        self.SPI.close()

        self.GPIO_RST_PIN.off()
        self.GPIO_DC_PIN.off()
        self.GPIO_PWR_PIN.off()
        logger.debug("close 5V, Module enters 0 power consumption ...")

        if cleanup:
            self.GPIO_RST_PIN.close()
            self.GPIO_DC_PIN.close()
            self.GPIO_PWR_PIN.close()
            self.GPIO_BUSY_PIN.close()

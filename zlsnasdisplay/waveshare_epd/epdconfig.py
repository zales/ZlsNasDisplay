import logging
import time

import gpiozero
import spidev

logger = logging.getLogger(__name__)


class RaspberryPi:
    # Pin definition
    RST_PIN = 17
    DC_PIN = 25
    CS_PIN = 8
    BUSY_PIN = 24
    PWR_PIN = 18

    def __init__(self):
        self.SPI = spidev.SpiDev()
        self.GPIO_RST_PIN = gpiozero.LED(self.RST_PIN)
        self.GPIO_DC_PIN = gpiozero.LED(self.DC_PIN)
        self.GPIO_PWR_PIN = gpiozero.LED(self.PWR_PIN)
        self.GPIO_BUSY_PIN = gpiozero.Button(self.BUSY_PIN, pull_up=False)

    def digital_write(self, pin, value):
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

    def digital_read(self, pin):
        if pin == self.BUSY_PIN:
            return self.GPIO_BUSY_PIN.value
        elif pin == self.RST_PIN:
            return self.RST_PIN
        elif pin == self.DC_PIN:
            return self.DC_PIN
        elif pin == self.PWR_PIN:
            return self.PWR_PIN

    def delay_ms(self, delay_time):
        time.sleep(delay_time / 1000.0)

    def spi_writebyte(self, data):
        self.SPI.writebytes(data)

    def spi_writebyte2(self, data):
        self.SPI.writebytes2(data)

    def module_init(self):
        self.GPIO_PWR_PIN.on()

        # SPI device, bus = 0, device = 0
        self.SPI.open(0, 0)
        self.SPI.max_speed_hz = 4000000
        self.SPI.mode = 0b00
        return 0

    def module_exit(self, cleanup=False):
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

import logging
import time
from typing import List, Optional

from PIL import Image

from zlsnasdisplay.waveshare_epd.epdconfig import RaspberryPi

# Display resolution
EPD_WIDTH = 128
EPD_HEIGHT = 296
GRAY1 = 0xFF  # white
GRAY2 = 0xC0
GRAY3 = 0x80  # gray
GRAY4 = 0x00  # Blackest

# EPD2IN9 commands
DRIVER_OUTPUT_CONTROL = 0x01
SET_GATE_DRIVING_VOLTAGE = 0x03
SET_SOURCE_OUTPUT_VOLTAGE = 0x04
BOOSTER_SOFT_START_CONTROL = 0x0C
GATE_SCAN_START_POSITION = 0x0F
DEEP_SLEEP_MODE = 0x10
DATA_ENTRY_MODE_SETTING = 0x11
SW_RESET = 0x12
TEMPERATURE_SENSOR_CONTROL = 0x1A
MASTER_ACTIVATION = 0x20
DISPLAY_UPDATE_CONTROL_1 = 0x21
DISPLAY_UPDATE_CONTROL_2 = 0x22
WRITE_RAM_1 = 0x24
WRITE_RAM_2 = 0x26
READ_RAM = 0x27
WRITE_VCOM_REGISTER = 0x2C
WRITE_LUT_REGISTER = 0x32
SET_DUMMY_LINE_PERIOD = 0x3A
SET_GATE_TIME = 0x3B
BORDER_WAVEFORM_CONTROL = 0x3C
SET_RAM_X_ADDRESS_START_END_POSITION = 0x44
SET_RAM_Y_ADDRESS_START_END_POSITION = 0x45
SET_RAM_X_ADDRESS_COUNTER = 0x4E
SET_RAM_Y_ADDRESS_COUNTER = 0x4F
TERMINATE_FRAME_READ_WRITE = 0xFF

logger = logging.getLogger(__name__)

display = RaspberryPi()


class EPD:
    def __init__(self):
        self.reset_pin = display.RST_PIN
        self.dc_pin = display.DC_PIN
        self.busy_pin = display.BUSY_PIN
        self.cs_pin = display.CS_PIN
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.GRAY1 = GRAY1  # white
        self.GRAY2 = GRAY2
        self.GRAY3 = GRAY3  # gray
        self.GRAY4 = GRAY4  # Blackest
        self._current_lut: Optional[List[int]] = None  # Cache current LUT to avoid redundant updates

    WF_PARTIAL_2IN9 = [
        0x0,
        0x40,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x80,
        0x80,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x40,
        0x40,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x80,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0A,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x1,
        0x1,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x1,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x22,
        0x22,
        0x22,
        0x22,
        0x22,
        0x22,
        0x0,
        0x0,
        0x0,
        0x22,
        0x17,
        0x41,
        0xB0,
        0x32,
        0x36,
    ]

    WS_20_30 = [
        0x80,
        0x66,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x40,
        0x0,
        0x0,
        0x0,
        0x10,
        0x66,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x20,
        0x0,
        0x0,
        0x0,
        0x80,
        0x66,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x40,
        0x0,
        0x0,
        0x0,
        0x10,
        0x66,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x20,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x14,
        0x8,
        0x0,
        0x0,
        0x0,
        0x0,
        0x2,
        0xA,
        0xA,
        0x0,
        0xA,
        0xA,
        0x0,
        0x1,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x14,
        0x8,
        0x0,
        0x1,
        0x0,
        0x0,
        0x1,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x1,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x44,
        0x44,
        0x44,
        0x44,
        0x44,
        0x44,
        0x0,
        0x0,
        0x0,
        0x22,
        0x17,
        0x41,
        0x0,
        0x32,
        0x36,
    ]

    Gray4 = [
        0x00,
        0x60,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x20,
        0x60,
        0x10,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x28,
        0x60,
        0x14,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x2A,
        0x60,
        0x15,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x90,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x02,
        0x00,
        0x05,
        0x14,
        0x00,
        0x00,
        0x1E,
        0x1E,
        0x00,
        0x00,
        0x00,
        0x00,
        0x01,
        0x00,
        0x02,
        0x00,
        0x05,
        0x14,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x24,
        0x22,
        0x22,
        0x22,
        0x23,
        0x32,
        0x00,
        0x00,
        0x00,
        0x22,
        0x17,
        0x41,
        0xAE,
        0x32,
        0x28,
    ]

    WF_FULL = [
        0x90,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x60,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x90,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x60,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x19,
        0x19,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x24,
        0x42,
        0x22,
        0x22,
        0x23,
        0x32,
        0x00,
        0x00,
        0x00,
        0x22,
        0x17,
        0x41,
        0xAE,
        0x32,
        0x38,
    ]

    # Hardware reset
    def reset(self) -> None:
        display.digital_write(self.reset_pin, 1)
        display.delay_ms(50)
        display.digital_write(self.reset_pin, 0)
        display.delay_ms(2)
        display.digital_write(self.reset_pin, 1)
        display.delay_ms(50)

    def send_command(self, command: int) -> None:
        display.digital_write(self.dc_pin, 0)
        display.digital_write(self.cs_pin, 0)
        display.spi_writebyte([command])
        display.digital_write(self.cs_pin, 1)

    def send_data(self, data: int) -> None:
        display.digital_write(self.dc_pin, 1)
        display.digital_write(self.cs_pin, 0)
        display.spi_writebyte([data])
        display.digital_write(self.cs_pin, 1)

    # send a lot of data
    def send_data2(self, data: List[int]) -> None:
        display.digital_write(self.dc_pin, 1)
        display.digital_write(self.cs_pin, 0)
        display.spi_writebyte2(data)
        display.digital_write(self.cs_pin, 1)

    def send_command_with_data(self, command: int, data: List[int]) -> None:
        """Send command followed by multiple data bytes (optimized for batch operations)"""
        self.send_command(command)
        for byte in data:
            self.send_data(byte)

    def read_busy(self, timeout: int = 5000) -> int:  # 5000 ms default timeout
        logger.debug("e-Paper busy")
        start_time = time.time()
        while display.digital_read(self.busy_pin) == 1:  # 0: idle, 1: busy
            if (time.time() - start_time) * 1000 > timeout:
                logger.error("Timeout waiting for e-Paper busy.")
                return -1
            display.delay_ms(20)
        logger.debug("e-Paper busy release")
        return 0

    def turn_on_display(self) -> None:
        self.send_command(DISPLAY_UPDATE_CONTROL_2)  # DISPLAY_UPDATE_CONTROL_2
        self.send_data(0xC7)
        self.send_command(MASTER_ACTIVATION)  # MASTER_ACTIVATION
        self.read_busy()

    def turn_on_display_partial(self) -> None:
        self.send_command(DISPLAY_UPDATE_CONTROL_2)  # DISPLAY_UPDATE_CONTROL_2
        self.send_data(0x0F)
        self.send_command(MASTER_ACTIVATION)  # MASTER_ACTIVATION
        self.read_busy()

    def lut(self, lut: List[int]) -> None:
        """Write LUT register data (first 153 bytes)"""
        self.send_command(WRITE_LUT_REGISTER)
        for i in range(0, 153):
            self.send_data(lut[i])
        self.read_busy()

    def set_lut(self, lut: List[int]) -> None:
        """
        Set Look-Up Table with caching to avoid redundant updates.
        LUT updates are expensive, so we cache the current LUT.
        """
        # Check if this LUT is already loaded
        if self._current_lut is not None and self._current_lut == lut:
            logger.debug("LUT already loaded, skipping update")
            return

        logger.debug("Loading new LUT")
        self.lut(lut)
        self.send_command(0x3F)
        self.send_data(lut[153])
        self.send_command(SET_GATE_DRIVING_VOLTAGE)  # gate voltage
        self.send_data(lut[154])
        self.send_command(SET_SOURCE_OUTPUT_VOLTAGE)  # source voltage
        self.send_data(lut[155])  # VSH
        self.send_data(lut[156])  # VSH2
        self.send_data(lut[157])  # VSL
        self.send_command(WRITE_VCOM_REGISTER)  # VCOM
        self.send_data(lut[158])

        # Cache the LUT
        self._current_lut = lut

    def set_window(self, x_start: int, y_start: int, x_end: int, y_end: int) -> None:
        """Set the display window for RAM operations"""
        self.send_command(
            SET_RAM_X_ADDRESS_START_END_POSITION
        )  # SET_RAM_X_ADDRESS_START_END_POSITION
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self.send_data((x_start >> 3) & 0xFF)
        self.send_data((x_end >> 3) & 0xFF)
        self.send_command(
            SET_RAM_Y_ADDRESS_START_END_POSITION
        )  # SET_RAM_Y_ADDRESS_START_END_POSITION
        self.send_data(y_start & 0xFF)
        self.send_data((y_start >> 8) & 0xFF)
        self.send_data(y_end & 0xFF)
        self.send_data((y_end >> 8) & 0xFF)

    def set_cursor(self, x: int, y: int) -> None:
        """Set the cursor position for RAM operations"""
        self.send_command(SET_RAM_X_ADDRESS_COUNTER)  # SET_RAM_X_ADDRESS_COUNTER
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self.send_data(x & 0xFF)

        self.send_command(SET_RAM_Y_ADDRESS_COUNTER)  # SET_RAM_Y_ADDRESS_COUNTER
        self.send_data(y & 0xFF)
        self.send_data((y >> 8) & 0xFF)

    def basic_init(self) -> int:
        """Basic initialization sequence for the display"""
        if display.module_init() != 0:
            return -1
        self.reset()
        self.read_busy()
        self.send_command(SW_RESET)  # SWRESET
        self.read_busy()
        self.send_command(DRIVER_OUTPUT_CONTROL)  # Driver output control
        self.send_data(READ_RAM)
        self.send_data(DRIVER_OUTPUT_CONTROL)
        self.send_data(0x00)
        self.send_command(DATA_ENTRY_MODE_SETTING)  # data entry mode
        self.send_data(SET_GATE_DRIVING_VOLTAGE)
        self.set_window(0, 0, self.width - 1, self.height - 1)
        self.set_cursor(0, 0)
        self.read_busy()
        return 0

    def init(self) -> int:
        """Initialize display with standard refresh mode"""
        if self.basic_init() != 0:
            return -1
        self.set_lut(self.WS_20_30)
        self.send_command(DISPLAY_UPDATE_CONTROL_1)
        self.send_data(0x00)
        self.send_data(0x80)
        return 0

    def init_fast(self) -> int:
        """Initialize display with fast refresh mode"""
        if self.basic_init() != 0:
            return -1
        self.send_command(BORDER_WAVEFORM_CONTROL)
        self.send_data(0x05)
        self.send_command(DISPLAY_UPDATE_CONTROL_1)
        self.send_data(0x00)
        self.send_data(0x80)
        self.set_lut(self.WF_FULL)
        return 0

    def init_4_gray(self) -> int:
        """Initialize display with 4-level grayscale mode"""
        if self.basic_init() != 0:
            return -1
        self.read_busy()
        self.send_command(BORDER_WAVEFORM_CONTROL)
        self.send_data(SET_SOURCE_OUTPUT_VOLTAGE)
        self.set_cursor(1, 0)
        self.read_busy()
        self.set_lut(self.Gray4)
        return 0

    def get_buffer(self, image: Image.Image) -> List[int]:
        """
        Convert PIL Image to display buffer with optimized bit operations.
        Uses bytearray for better performance and in-place modifications.
        """
        buf_size = (self.width // 8) * self.height
        logger.debug("bufsiz = %d", buf_size)

        # Use bytearray instead of list for better performance
        buf = bytearray([0xFF] * buf_size)
        image_monocolor = image.convert("1")
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()
        if pixels is None:
            return list(buf)
        logger.debug("imwidth = %d, imheight = %d", imwidth, imheight)

        width_bytes = self.width // 8

        if imwidth == self.width and imheight == self.height:
            logger.debug("Vertical")
            # Optimized vertical layout processing
            for y in range(imheight):
                y_offset = y * width_bytes
                for x in range(imwidth):
                    if pixels[x, y] == 0:
                        byte_idx = y_offset + (x >> 3)  # x // 8
                        buf[byte_idx] &= ~(0x80 >> (x & 7))  # x % 8

        elif imwidth == self.height and imheight == self.width:
            logger.debug("Horizontal")
            # Optimized horizontal layout processing
            for y in range(imheight):
                for x in range(imwidth):
                    if pixels[x, y] == 0:
                        newx = y
                        newy = self.height - x - 1
                        byte_idx = (newy * width_bytes) + (newx >> 3)
                        buf[byte_idx] &= ~(0x80 >> (y & 7))

        return list(buf)  # Convert back to list for compatibility

    def get_buffer_4_gray(self, image: Image.Image) -> List[int]:
        """Convert PIL Image to 4-level grayscale buffer"""
        logger.debug("bufsiz = %d", int(self.width / 8) * self.height)
        buf = [0xFF] * (int(self.width / 4) * self.height)
        image_monocolor = image.convert("L")
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()
        if pixels is None:
            return buf
        i = 0
        logger.debug("imwidth = %d, imheight = %d", imwidth, imheight)
        if imwidth == self.width and imheight == self.height:
            logger.debug("Vertical")
            for y in range(imheight):
                for x in range(imwidth):
                    # Get pixel value and ensure it's an int
                    pixel_val = pixels[x, y]
                    if isinstance(pixel_val, tuple):
                        pixel_val = pixel_val[0]
                    pixel_val = int(pixel_val)

                    # Set the bits for the column of pixels at the current position.
                    if pixel_val == 0xC0:
                        pixels[x, y] = 0x80
                    elif pixel_val == 0x80:
                        pixels[x, y] = 0x40
                    i = i + 1
                    if i % 4 == 0:
                        # Get previous pixels and ensure they're ints
                        p0 = pixels[x - 3, y]
                        p1 = pixels[x - 2, y]
                        p2 = pixels[x - 1, y]
                        p3 = pixels[x, y]
                        if isinstance(p0, tuple):
                            p0 = p0[0]
                        if isinstance(p1, tuple):
                            p1 = p1[0]
                        if isinstance(p2, tuple):
                            p2 = p2[0]
                        if isinstance(p3, tuple):
                            p3 = p3[0]

                        buf[int((x + (y * self.width)) / 4)] = (
                            (int(p0) & 0xC0)
                            | ((int(p1) & 0xC0) >> 2)
                            | ((int(p2) & 0xC0) >> 4)
                            | ((int(p3) & 0xC0) >> 6)
                        )

        elif imwidth == self.height and imheight == self.width:
            logger.debug("Horizontal")
            for x in range(imwidth):
                for y in range(imheight):
                    newx = y
                    newy = self.height - x - 1

                    # Get pixel value and ensure it's an int
                    pixel_val = pixels[x, y]
                    if isinstance(pixel_val, tuple):
                        pixel_val = pixel_val[0]
                    pixel_val = int(pixel_val)

                    if pixel_val == 0xC0:
                        pixels[x, y] = 0x80
                    elif pixel_val == 0x80:
                        pixels[x, y] = 0x40
                    i = i + 1
                    if i % 4 == 0:
                        # Get previous pixels and ensure they're ints
                        p0 = pixels[x, y - 3]
                        p1 = pixels[x, y - 2]
                        p2 = pixels[x, y - 1]
                        p3 = pixels[x, y]
                        if isinstance(p0, tuple):
                            p0 = p0[0]
                        if isinstance(p1, tuple):
                            p1 = p1[0]
                        if isinstance(p2, tuple):
                            p2 = p2[0]
                        if isinstance(p3, tuple):
                            p3 = p3[0]

                        buf[int((newx + (newy * self.width)) / 4)] = (
                            (int(p0) & 0xC0)
                            | ((int(p1) & 0xC0) >> 2)
                            | ((int(p2) & 0xC0) >> 4)
                            | ((int(p3) & 0xC0) >> 6)
                        )
        return buf

    def display(self, image: Optional[List[int]]) -> None:
        """Full display update"""
        if image is None:
            logger.warning("No image data provided to display method")
            return
        self.send_command(WRITE_RAM_1)  # WRITE_RAM
        self.send_data2(image)
        self.turn_on_display()

    def display_base(self, image: Optional[List[int]]) -> None:
        """Display base image (writes to both RAM buffers)"""
        if image is None:
            logger.warning("No image data provided to display method")
            return

        self.send_command(WRITE_RAM_1)  # WRITE_RAM
        self.send_data2(image)

        self.send_command(WRITE_RAM_2)  # WRITE_RAM
        self.send_data2(image)

        self.turn_on_display()

    def display_4_gray(self, image: List[int]) -> None:
        """Display 4-level grayscale image"""
        self.send_command(WRITE_RAM_1)
        for i in range(0, 4736):
            temp3 = 0
            for j in range(0, 2):
                temp1 = image[i * 2 + j]
                for k in range(0, 2):
                    temp2 = temp1 & 0xC0
                    if temp2 == 0xC0:
                        temp3 |= 0x00
                    elif temp2 == 0x00:
                        temp3 |= 0x01
                    elif temp2 == 0x80:
                        temp3 |= 0x01
                    else:  # 0x40
                        temp3 |= 0x00
                    temp3 <<= 1

                    temp1 <<= 2
                    temp2 = temp1 & 0xC0
                    if temp2 == 0xC0:
                        temp3 |= 0x00
                    elif temp2 == 0x00:
                        temp3 |= 0x01
                    elif temp2 == 0x80:
                        temp3 |= 0x01
                    else:  # 0x40
                        temp3 |= 0x00
                    if j != 1 or k != 1:
                        temp3 <<= 1
                    temp1 <<= 2
            self.send_data(temp3)

        self.send_command(WRITE_RAM_2)
        for i in range(0, 4736):
            temp3 = 0
            for j in range(0, 2):
                temp1 = image[i * 2 + j]
                for k in range(0, 2):
                    temp2 = temp1 & 0xC0
                    if temp2 == 0xC0:
                        temp3 |= 0x00
                    elif temp2 == 0x00:
                        temp3 |= 0x01
                    elif temp2 == 0x80:
                        temp3 |= 0x00
                    else:  # 0x40
                        temp3 |= 0x01
                    temp3 <<= 1

                    temp1 <<= 2
                    temp2 = temp1 & 0xC0
                    if temp2 == 0xC0:
                        temp3 |= 0x00
                    elif temp2 == 0x00:
                        temp3 |= 0x01
                    elif temp2 == 0x80:
                        temp3 |= 0x00
                    else:  # 0x40
                        temp3 |= 0x01
                    if j != 1 or k != 1:
                        temp3 <<= 1
                    temp1 <<= 2
            self.send_data(temp3)

        self.turn_on_display()

    def display_partial(self, image: Optional[List[int]]) -> None:
        """
        Optimized partial display update.
        Removes redundant reset and uses LUT caching.
        """
        if image is None:
            logger.warning("No image data provided to display method")
            return

        # Soft reset - optimized to minimal timing
        display.digital_write(self.reset_pin, 0)
        display.delay_ms(2)
        display.digital_write(self.reset_pin, 1)
        display.delay_ms(2)

        # Set partial update LUT (cached if already loaded)
        self.set_lut(self.WF_PARTIAL_2IN9)

        # Configure partial update - batch data
        self.send_command_with_data(0x37, [0x00, 0x00, 0x00, 0x00, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00])

        self.send_command(BORDER_WAVEFORM_CONTROL)  # Border Wavefrom
        self.send_data(0x80)

        self.send_command(DISPLAY_UPDATE_CONTROL_2)
        self.send_data(0xC0)
        self.send_command(MASTER_ACTIVATION)
        self.read_busy()

        # Set full display window
        self.set_window(0, 0, self.width - 1, self.height - 1)
        self.set_cursor(0, 0)

        # Write image buffer and trigger partial update
        self.send_command(WRITE_RAM_1)  # WRITE_RAM
        self.send_data2(image)
        self.turn_on_display_partial()

    def clear(self, color: int = 0xFF) -> None:
        """Clear the display to specified color (0xFF = white, 0x00 = black)"""
        if self.width % 8 == 0:
            linewidth = int(self.width / 8)
        else:
            linewidth = int(self.width / 8) + 1

        buffer = [color] * int(self.height * linewidth)
        self.send_command(WRITE_RAM_1)  # WRITE_RAM
        self.send_data2(buffer)
        self.turn_on_display()
        self.send_command(WRITE_RAM_2)  # WRITE_RAM
        self.send_data2(buffer)
        self.turn_on_display()

    def sleep(self) -> None:
        """Put display into deep sleep mode"""
        self.send_command(DEEP_SLEEP_MODE)  # DEEP_SLEEP_MODE
        self.send_data(DRIVER_OUTPUT_CONTROL)

        display.delay_ms(2000)
        display.module_exit()

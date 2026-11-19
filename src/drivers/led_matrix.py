from machine import Pin, SPI
import framebuf
import time

class Max7219Matrix(framebuf.FrameBuffer):
    """
    High-level MicroPython API and SPI driver for MAX7219 8x8 LED matrix modules
    (single or daisy-chained, e.g., 32x8 4-in-1 module) on Raspberry Pi Pico W.
    All comments and docstrings are in English.
    """

    # MAX7219 Register Map
    _REG_NOOP         = 0x00
    _REG_DIGIT0       = 0x01
    _REG_DECODE_MODE  = 0x09
    _REG_INTENSITY    = 0x0A
    _REG_SCAN_LIMIT   = 0x0B
    _REG_SHUTDOWN     = 0x0C
    _REG_DISPLAY_TEST = 0x0F

    def __init__(self, num_matrices: int = 4, spi_id: int = 0, sck_pin: int = 2,
                 mosi_pin: int = 3, cs_pin: int = 5, baudrate: int = 10000000,
                 brightness: int = 3):
        """
        Initialize the MAX7219 SPI LED matrix chain.
        :param num_matrices: Number of 8x8 matrices daisy-chained (e.g., 4 for 32x8 module).
        :param spi_id: Hardware SPI bus ID (0 or 1).
        :param sck_pin: GPIO pin for SPI CLK (default GP2).
        :param mosi_pin: GPIO pin for SPI DIN/MOSI (default GP3).
        :param cs_pin: GPIO pin for Chip Select / LOAD (default GP5).
        :param baudrate: SPI clock frequency in Hz (up to 10 MHz).
        :param brightness: Initial brightness level from 0 (dim) to 15 (max).
        """
        self.num_matrices = max(1, int(num_matrices))
        self.width = 8 * self.num_matrices
        self.height = 8

        self.cs = Pin(cs_pin, Pin.OUT, value=1)
        self.spi = SPI(
            spi_id,
            baudrate=baudrate,
            polarity=0,
            phase=0,
            sck=Pin(sck_pin),
            mosi=Pin(mosi_pin)
        )

        # MONO_HLSB maps 1 byte per 8 horizontal pixels per row across the chain
        self.buffer = bytearray(self.num_matrices * self.height)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_HLSB)

        self._init_display()
        self.set_brightness(brightness)
        self.clear()

    def _write_all(self, register: int, data: int):
        """Broadcast a register/data command pair to every MAX7219 in the chain."""
        self.cs.value(0)
        for _ in range(self.num_matrices):
            self.spi.write(bytearray([register, data]))
        self.cs.value(1)

    def _init_display(self):
        """Configure MAX7219 registers for raw matrix mode."""
        self._write_all(self._REG_SHUTDOWN, 0x00)      # Shutdown mode during setup
        self._write_all(self._REG_DISPLAY_TEST, 0x00)  # Disable display test
        self._write_all(self._REG_DECODE_MODE, 0x00)   # No BCD decode (raw LEDs)
        self._write_all(self._REG_SCAN_LIMIT, 0x07)    # Scan all 8 rows (0-7)
        self._write_all(self._REG_SHUTDOWN, 0x01)      # Normal operation

    def set_brightness(self, level: int):
        """Set LED intensity from 0 (minimum) to 15 (maximum)."""
        level = max(0, min(15, int(level)))
        self._write_all(self._REG_INTENSITY, level)

    def power(self, on: bool = True):
        """Turn the display on or enter low-power shutdown mode."""
        self._write_all(self._REG_SHUTDOWN, 0x01 if on else 0x00)

    def test_mode(self, enable: bool = True):
        """Force all LEDs on at full brightness for hardware testing."""
        self._write_all(self._REG_DISPLAY_TEST, 0x01 if enable else 0x00)

    def clear(self, update: bool = True):
        """Clear all LEDs."""
        self.fill(0)
        if update:
            self.show()

    def show(self):
        """Push the current framebuffer content to the MAX7219 matrices."""
        for row in range(8):
            self.cs.value(0)
            for m in range(self.num_matrices):
                # Send farthest matrix first in daisy-chain shift register order
                byte_idx = row * self.num_matrices + m
                self.spi.write(bytearray([self._REG_DIGIT0 + row, self.buffer[byte_idx]]))
            self.cs.value(1)

    def show_text(self, text: str, x: int = 0, y: int = 0, clear_first: bool = True):
        """
        Display static text on the matrix.
        :param text: String to render (each character is 8x8 pixels).
        :param x: Horizontal pixel offset.
        :param y: Vertical pixel offset.
        """
        if clear_first:
            self.fill(0)
        self.text(str(text), x, y, 1)
        self.show()

    def scroll_text(self, text: str, delay_ms: int = 40, loop: int = 1):
        """
        Scroll a message smoothly from right to left across the matrix chain.
        :param text: Message string to scroll.
        :param delay_ms: Frame delay in milliseconds (controls scroll speed).
        :param loop: Number of times to repeat the scroll (0 = infinite).
        """
        msg = str(text)
        text_width = len(msg) * 8
        count = 0

        while loop == 0 or count < loop:
            for x in range(self.width, -text_width - 1, -1):
                self.fill(0)
                self.text(msg, x, 0, 1)
                self.show()
                time.sleep_ms(delay_ms)
            count += 1

    def show_distance(self, distance_cm: float, unit: str = "cm", decimals: int = 0):
        """
        Format and display a distance in centimeters ('cm') or inches ('in').
        Automatically adapts precision to fit the available matrix width.
        """
        if distance_cm is None or distance_cm < 0:
            self.show_text("ERR" if self.width < 32 else "OUT")
            return

        unit_clean = unit.lower().strip()
        if unit_clean in ("in", "inch", "inches", "pouces", "po"):
            val = distance_cm / 2.54
            suffix = "in"
        else:
            val = distance_cm
            suffix = "cm"

        if self.width >= 32:
            # 4 matrices (32px wide = 4 chars): e.g. "42cm" or "16in"
            text_str = f"{val:.{decimals}f}{suffix}"
            if len(text_str) > 4:
                text_str = f"{int(round(val))}{suffix}"
        else:
            text_str = f"{int(round(val))}"

        self.show_text(text_str)

    def show_bar(self, value: float, max_value: float = 100.0):
        """
        Display a horizontal level/progress bar across the full width of the chain.
        """
        self.fill(0)
        ratio = max(0.0, min(1.0, value / max_value)) if max_value > 0 else 0.0
        fill_cols = int(round(self.width * ratio))
        if fill_cols > 0:
            self.fill_rect(0, 1, fill_cols, 6, 1)
        self.show()


# =====================================================================
# TEST SCRIPT (Executed only when the file is run directly)
# =====================================================================
if __name__ == "__main__":
    # Default SPI0 wiring: SCK = GP2, MOSI/DIN = GP3, CS = GP5
    # Change num_matrices=1 if using a single 8x8 module instead of a 4-in-1 (32x8)
    matrix = Max7219Matrix(num_matrices=4, spi_id=0, sck_pin=2, mosi_pin=3, cs_pin=5, brightness=4)

    print("1. Hardware test (all LEDs on briefly)...")
    matrix.test_mode(True)
    time.sleep(0.5)
    matrix.test_mode(False)

    print("2. Static text display...")
    matrix.show_text("PICO")
    time.sleep(1.2)

    print("3. Distance display (cm and inches)...")
    matrix.show_distance(42.0, unit="cm")
    time.sleep(1.2)
    matrix.show_distance(42.0, unit="in")
    time.sleep(1.2)

    print("4. Progress bar animation...")
    for v in range(0, 101, 10):
        matrix.show_bar(v, max_value=100)
        time.sleep_ms(80)

    print("5. Scrolling text...")
    matrix.scroll_text("MAX7219 SPI READY", delay_ms=35, loop=1)
    matrix.clear()
from machine import Pin, I2C
import framebuf
import time

class SH1106_I2C(framebuf.FrameBuffer):
    """
    Low-level MicroPython driver for SH1106 OLED controller (128x64) via I2C.
    Includes the 2-column hardware offset specific to the SH1106 controller.
    """
    def __init__(self, width: int, height: int, i2c: I2C, addr: int = 0x3C):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def write_cmd(self, cmd: int):
        self.i2c.writeto(self.addr, bytearray([0x80, cmd]))

    def write_data(self, buf: bytearray):
        self.i2c.writeto(self.addr, b'\x40' + buf)

    def init_display(self):
        cmds = [
            0xAE,        # Display OFF
            0x02, 0x10,  # Column address offset (2 pixels for SH1106)
            0x40,        # Display start line 0
            0xB0,        # Page address 0
            0x81, 0xCF,  # Contrast control
            0xA1,        # Segment remap (normal)
            0xA6,        # Normal display (non-inverted)
            0xA8, 0x3F,  # Multiplex ratio (64)
            0xAD, 0x8B,  # DC-DC ON
            0x33,        # Charge pump 9V
            0xC8,        # COM scan direction (remapped)
            0xD3, 0x00,  # Display offset 0
            0xD5, 0x80,  # Oscillator frequency
            0xD9, 0x1F,  # Pre-charge period
            0xDA, 0x12,  # COM pins hardware configuration
            0xDB, 0x40,  # VCOMH deselect level
            0xAF         # Display ON
        ]
        for cmd in cmds:
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def show(self):
        for page in range(self.pages):
            self.write_cmd(0xB0 + page)
            self.write_cmd(0x02)  # Low column start address (offset 2)
            self.write_cmd(0x10)  # High column start address
            start = page * self.width
            end = start + self.width
            self.write_data(self.buffer[start:end])


class OledDisplay:
    """
    High-level API for the 128x64 SH1106 OLED display on Raspberry Pi Pico W.
    Supports displaying distances (cm/inches), progress bars, messages,
    and customizable dashboards.
    """
    def __init__(self, sda_pin: int = 0, scl_pin: int = 1, i2c_id: int = 0, addr: int = 0x3C, freq: int = 400000):
        self.i2c = I2C(i2c_id, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=freq)
        self.oled = SH1106_I2C(128, 64, self.i2c, addr=addr)
        self.width = 128
        self.height = 64

    def clear(self, update: bool = True):
        """Clear the screen."""
        self.oled.fill(0)
        if update:
            self.oled.show()

    def set_contrast(self, level: int):
        """Set display brightness (0 to 255)."""
        level = max(0, min(255, int(level)))
        self.oled.write_cmd(0x81)
        self.oled.write_cmd(level)

    def invert(self, state: bool = True):
        """Invert display colors (white background / black text)."""
        self.oled.write_cmd(0xA7 if state else 0xA6)

    def power(self, on: bool = True):
        """Turn the OLED panel on or off without losing buffer contents."""
        self.oled.write_cmd(0xAF if on else 0xAE)

    def draw_big_text(self, text: str, x: int, y: int, scale: int = 2):
        """
        Render scaled-up text (integer scale >= 1) using a temporary framebuffer
        for crisp pixel-doubled output.
        """
        if scale <= 1:
            self.oled.text(text, x, y, 1)
            return

        w = len(text) * 8
        h = 8
        buf = bytearray((w * h) // 8 + 8)
        fb = framebuf.FrameBuffer(buf, w, h, framebuf.MONO_HLSB)
        fb.fill(0)
        fb.text(text, 0, 0, 1)

        for py in range(h):
            for px in range(w):
                if fb.pixel(px, py):
                    self.oled.fill_rect(x + px * scale, y + py * scale, scale, scale, 1)

    def show_message(self, title: str, lines: list = None, center: bool = True):
        """
        Display an inverted header banner at the top and up to 4 lines of text below.
        """
        self.clear(update=False)
        # Inverted title banner
        self.oled.fill_rect(0, 0, self.width, 12, 1)
        tx = max(2, (self.width - len(title) * 8) // 2) if center else 4
        self.oled.text(title[:15], tx, 2, 0)

        if lines:
            for idx, line in enumerate(lines[:4]):
                y = 18 + idx * 11
                text_str = str(line)[:16]
                lx = max(0, (self.width - len(text_str) * 8) // 2) if center else 2
                self.oled.text(text_str, lx, y, 1)
        self.oled.show()

    def show_distance(self, distance_cm: float, unit: str = "cm", title: str = "DISTANCE",
                      max_range_cm: float = 100.0, show_bar: bool = True, decimals: int = 1):
        """
        Display a distance in centimeters ('cm') or inches ('in' / 'inch')
        with large-scale formatting and an optional progress bar.
        
        :param distance_cm: Measured value in centimeters.
        :param unit: 'cm' for centimeters, 'in' or 'inch' for inches.
        :param title: Header title shown at the top of the screen.
        :param max_range_cm: Max distance for progress bar scaling (in cm).
        :param show_bar: Show or hide the bottom graphical bar.
        :param decimals: Number of decimal places to display.
        """
        self.clear(update=False)

        # 1. Header
        self.oled.text(title[:16], 0, 0, 1)
        self.oled.hline(0, 10, self.width, 1)

        # 2. Out-of-range or sensor error handling
        if distance_cm is None or distance_cm < 0:
            self.draw_big_text("OUT RANGE", 10, 26, scale=2)
            self.oled.show()
            return

        # 3. Unit conversion
        unit_clean = unit.lower().strip()
        if unit_clean in ("in", "inch", "inches", "pouces", "po"):
            value = distance_cm / 2.54
            unit_label = "in"
        else:
            value = distance_cm
            unit_label = "cm"

        # 4. Centered large-format value display
        val_str = f"{value:.{decimals}f}"
        scale = 3 if len(val_str) <= 4 else 2
        y_pos = 18 if show_bar else 24

        total_w = (len(val_str) * 8 * scale) + 4 + (len(unit_label) * 8)
        start_x = max(0, (self.width - total_w) // 2)

        self.draw_big_text(val_str, start_x, y_pos, scale=scale)
        unit_x = start_x + (len(val_str) * 8 * scale) + 4
        unit_y = y_pos + (8 * scale) - 8
        self.oled.text(unit_label, unit_x, unit_y, 1)

        # 5. Proportional progress bar
        if show_bar and max_range_cm > 0:
            bar_y = 50
            bar_h = 12
            self.oled.rect(0, bar_y, self.width, bar_h, 1)
            ratio = max(0.0, min(1.0, distance_cm / max_range_cm))
            fill_w = int((self.width - 4) * ratio)
            if fill_w > 0:
                self.oled.fill_rect(2, bar_y + 2, fill_w, bar_h - 4, 1)

        self.oled.show()

    def show_dashboard(self, items: dict):
        """
        Display up to 4 aligned key/value pairs (ideal for multi-sensor views).
        e.g., {'Dist': '24.5 cm', 'Status': 'OK', 'Mode': 'Auto'}
        """
        self.clear(update=False)
        for idx, (key, val) in enumerate(list(items.items())[:4]):
            y = 4 + idx * 15
            k_str = f"{key}:"
            v_str = str(val)
            self.oled.text(k_str, 0, y, 1)
            vx = max(len(k_str) * 8 + 4, self.width - len(v_str) * 8)
            self.oled.text(v_str, vx, y, 1)
            if idx < 3:
                self.oled.hline(0, y + 11, self.width, 1)
        self.oled.show()


# =====================================================================
# TEST SCRIPT (Executed only when the file is run directly)
# =====================================================================
if __name__ == "__main__":
    # Default wiring: SDA = GP0 (pin 1), SCL = GP1 (pin 2)
    display = OledDisplay(sda_pin=0, scl_pin=1, addr=0x3C)

    print("1. Displaying welcome message...")
    display.show_message("SYSTEM READY", ["OLED SH1106", "128x64 I2C", "Pico W OK"])
    time.sleep(2)

    print("2. Simulating distance measurements in centimeters...")
    for d in [12.4, 35.8, 68.2, 95.0]:
        display.show_distance(d, unit="cm", title="FRONT SENSOR", max_range_cm=100)
        time.sleep(0.8)

    print("3. Simulating distance measurements in inches...")
    for d in [12.4, 35.8, 68.2]:
        display.show_distance(d, unit="in", title="FRONT SENSOR", max_range_cm=100)
        time.sleep(0.8)

    print("4. Displaying dashboard...")
    display.show_dashboard({
        "Dist CM": "42.5 cm",
        "Dist IN": "16.7 in",
        "Alert": "NONE",
        "Buzzer": "ACTIVE"
    })

from led_matrix import Max7219Matrix
import time

matrix = Max7219Matrix(num_matrices=1, spi_id=0, sck_pin=18, mosi_pin=19, cs_pin=17, brightness=4)

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

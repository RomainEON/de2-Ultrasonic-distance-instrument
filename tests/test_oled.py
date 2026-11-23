from machine import I2C, Pin
from sh1106 import SH1106_I2C
import time


def main():
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100_000)
    oled = SH1106_I2C(i2c)

    oled.fill(0)
    oled.text("Raspberry Pi", 0, 0)
    oled.text("Pico W", 0, 8)
    oled.rect(0, 20, 100, 20, 1)
    oled.text("I2C display", 4, 26)
    oled.rect(0, 40, 70, 20, 1)
    oled.text("LAB n*6", 4, 46)
    oled.hline(0, 62, 128, 1)
    oled.show()

    try:
        while True:
            
            time.sleep(2)

    except KeyboardInterrupt:
        oled.fill(0)
        oled.show()

if __name__ == "__main__":
    main()
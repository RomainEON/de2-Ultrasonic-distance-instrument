import time
from machine import Pin
from gpio_devices import Button

button_pressed = False


def button_handler(pin):
    global button_pressed
    button_pressed = True


def main():
    global button_pressed
    button = Button(2)
    cm_mode = True

    print("Press the button to toggle unit; press Ctrl+C to stop.")

    try:
        button.pin.irq(
            trigger=Pin.IRQ_FALLING,
            handler=button_handler
        )

        while True:
            if button_pressed:
                button_pressed = False
                cm_mode = not cm_mode
                print(f"Button pressed! Current mode: {'cm' if cm_mode else 'in'}")

            time.sleep_ms(100)

    except KeyboardInterrupt:
        print("\nProgram stopped. Exiting...")
        button.pin.irq(handler=None)


if __name__ == "__main__":
    main()
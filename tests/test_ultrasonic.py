from ultrasonic import HCSR04
import time

sensor = HCSR04(trigger_pin=14, echo_pin=15, echo_timeout_us=10000)


def main():
    print("Measuring distance; press Ctrl+C to stop.")

    try:
        while True:
            distance = sensor.distance_cm()
            print(f"Distance: {distance:.1f} cm")
            time.sleep_ms(100)

    except KeyboardInterrupt:
        print("\nProgram stopped. Exiting...")


if __name__ == "__main__":
    main()
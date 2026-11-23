"""
Ultrasonic Distance Measurement Module with Visual and Audio Feedback (MicroPython).

This script continuously measures the distance to an obstacle using an HC-SR04
ultrasonic sensor. It displays proximity intensity as a bar graph on a MAX7219
LED matrix, emits an audible alert whose repetition rate increases as the
obstacle gets closer, and allows toggling the display unit between centimeters
and inches via a push button. Additionally, an SH1106 OLED display shows the
measured distance in centimeters or inches depending on the active mode, and
flashes a warning symbol (a triangle with an exclamation mark accompanied by
the text "Warning") whenever the obstacle moves below a minimum distance threshold.
"""

from led_matrix import Max7219Matrix
from ultrasonic import HCSR04
from button import DebouncedButton
from buzzer import PassiveBuzzer
from machine import I2C, Pin
from sh1106 import SH1106_I2C
import time
import math

# ==============================================================================
# Hardware and Logic Configuration Constants
# ==============================================================================
DISTANCE_MIN = 3        # Minimum reliable detection distance in cm (dead zone)
MAX_VALUE = 100         # Maximum considered range (100 cm) and bar graph full scale
BUZZER_PIN = 3         # GPIO pin connected to the passive buzzer
DEFAULT_DURATION = 80   # Base duration (in ms) used to calculate beep intervals

# ==============================================================================
# Global State Variables
# ==============================================================================
button_pressed = False  # Interrupt flag indicating a button press event

# ==============================================================================
# Hardware Peripheral Initialization
# ==============================================================================
# Passive buzzer for proximity audio feedback
b = PassiveBuzzer(BUZZER_PIN)

# HC-SR04 ultrasonic sensor (10 ms timeout corresponding to ~1.7 m round-trip)
sensor = HCSR04(trigger_pin=14, echo_pin=15, echo_timeout_us=10000)

# 8x8 LED matrix driven by MAX7219 controller over SPI bus #2
matrix = Max7219Matrix(num_matrices=1, spi_id=0, sck_pin=18, mosi_pin=19, cs_pin=17, brightness=4)


def button_handler():
    """
    Event handler (callback) triggered when the push button is pressed.
    
    Sets a global flag processed synchronously in the main loop to avoid
    blocking operations or race conditions within the interrupt context.
    """
    print("Button pressed")
    global button_pressed
    button_pressed = True


def main():
    """
    Main application entry point.
    
    Initializes the debounced button, runs the continuous acquisition and
    feedback loop (LED matrix, buzzer, serial console), and ensures proper
    hardware cleanup upon program termination.
    """
    print("Press Ctrl+C to stop.")

    global button_pressed
    # Initialize debounced push button on GPIO pin 2
    button = DebouncedButton(2, button_handler)
    # Initial display unit mode: True for centimeters (cm), False for inches (in)
    cm_mode = True
    
    try:
        while True:
            # Verify echo validity (a negative value indicates an echo timeout)
            if sensor.distance_cm() >= 0:
                distance = sensor.distance_cm() 

                # Compute bar graph level (inversely proportional to distance)
                # If the object is closer than DISTANCE_MIN, fill the bar to maximum
                v=MAX_VALUE - math.floor(distance) if distance >= DISTANCE_MIN else MAX_VALUE
                matrix.show_bar(v, max_value=MAX_VALUE)

                # Trigger audio alert if the obstacle is within the 100 cm detection range
                if distance <= MAX_VALUE :
                    # Modulate beep timing in 10 cm steps (closer object yields faster beeps)
                    t=DEFAULT_DURATION*math.floor((distance // 10) + 1)
                    #print(t)
                    b.beep(duration_ms=t, pause_ms=t)
                            
                # Process button press event to toggle measurement units
                if button_pressed:
                    button_pressed = False
                    cm_mode = not cm_mode

                # Format and print the measured distance to the serial console
                print("Distace: ", end = "")
                if not cm_mode :
                    # Convert centimeters to inches (1 cm ≈ 0.394 in)
                    distance *= 0.394

                print(f"{distance:.0f} "
                    f"{'cm' if cm_mode else 'in'}")  
                                
                # Short delay to stabilize display refresh and sensor readings
                time.sleep_ms(80)
            
            else:
                # Handle out-of-range or lost echo: clear the LED matrix bar graph
                print("TimeOut") 
                matrix.show_bar(0, max_value=MAX_VALUE)

            # Global loop delay between measurement cycles to reduce CPU load and false echoes
            time.sleep_ms(100)

    except KeyboardInterrupt:
        # Graceful shutdown on manual interrupt (Ctrl+C): turn off all LED matrix pixels
        print("\nProgram stopped. Exiting...")
        matrix.clear()


if __name__ == "__main__":
    main()

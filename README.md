# de2-Ultrasonic-distance-instrumentProject #6: Ultrasonic Distance Instrument

Team Members and Contributions

Manuel BEAUZOR: [Describe contribution here]

Romain EON: [Describe contribution here]

Roberto NATRELLA: [Describe contribution here]

Problem Statement and Solution Summary

This project provides a contactless, real-time distance measurement instrument powered by a Raspberry Pi Pico W and MicroPython. The system utilizes an HC-SR04 ultrasonic transducer to measure range, displaying numerical values and units (cm/inch) on a 128x64 SH1106 OLED display. Simultaneously, it drives an 8x8 LED Matrix to provide an intuitive visual proximity gauge. An acoustic warning system using a piezo buzzer alerts the user when objects cross critical thresholds, and a tactile push-button allows for dynamic unit toggling.

Hardware Inventory and Pin Allocation

Microcontroller: Raspberry Pi Pico W

Ultrasonic Sensor: HC-SR04 (Trig: GP14 / Echo: GP15)

OLED Display: 128x64 SH1106 (I2C0 Bus - SDA: GP4 / SCL: GP5)

LED Matrix: 8x8 with MAX7219 Driver (SPI0 Bus - SCK: GP16 / SS: GP17 / MOSI: GP19)

Buzzer Module: Active/Passive Piezo Speaker (PWM Output: GP2)

User Control: Tactile Push Button (Digital Input: GP3)

Note: Please refer to the docs/week1_project6_proposal.pdf document for the detailed hardware wiring schematic and blueprints.

Setup and Operating Instructions

Flash the Raspberry Pi Pico W with the latest MicroPython firmware.

Upload the project directory structure to the Pico W. Ensure all hardware component classes are properly located in src/drivers/.

Install any necessary dependencies listed in requirements.txt.

Execute src/main.py to initialize the asynchronous tasks and start the system.

Timing and Concurrency Plan

To ensure a highly responsive interactive system, the architecture avoids blocking operations and time.sleep() calls. It relies entirely on MicroPython's uasyncio cooperative concurrency framework:

sensor_loop(): 100 ms (10 Hz) - Triggers the sensor and calculates distance.

oled_update_loop(): 200 ms (5 Hz) - Renders numeric distance and unit labels.

matrix_update_loop(): 100 ms (10 Hz) - Updates the bar-graph/distance gauge.

alarm_monitor_loop(): 50 ms (20 Hz) - Evaluates thresholds and triggers buzzer patterns.

button_isr_handler(): Event-driven - Debounced interrupt for unit toggling.

Project Outputs

Poster Presentation: [Link to PDF poster - To be added in Week 4]

Demonstration Video: [Link to video - To be added in Week 5]
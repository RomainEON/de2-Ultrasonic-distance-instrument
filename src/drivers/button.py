"""
===============================================================================
File:        button.py
Version:     1.0.0
Author:      EON Romain
Date:        2026-11-12
Target:      MicroPython
Interface:   GPIO (IRQ)
# Description: MicroPython push-button driver with software debounce filtering
#              and hardware interrupt (IRQ) callback support.
===============================================================================
"""

import time
from machine import Pin

class DebouncedButton:
    """
    Push-button driver with software debounce filtering and interrupt (IRQ) handling.
    """
    def __init__(self, pin_id, callback, debounce_ms=200):
        """
        pin_id: GPIO pin number
        callback: Function to execute on valid button press
        debounce_ms: Dead time in milliseconds to ignore physical bounces
        """
        # Configure pin as input with Pull-Down resistor
        self.pin = Pin(pin_id, Pin.IN, Pin.PULL_UP)
        self.callback = callback
        self.debounce_ms = debounce_ms
        self.last_press = 0
        
        # Attach interrupt: triggers _isr_handler on a rising edge (button press)
        self.pin.irq(trigger=Pin.IRQ_FALLING, handler=self._isr_handler)

    def _isr_handler(self, pin):
        """Hardware interrupt handler called automatically on state change."""
        current_time = time.ticks_ms()
        
        # If the elapsed time since the last press is greater than the debounce delay
        if time.ticks_diff(current_time, self.last_press) > self.debounce_ms:
            self.last_press = current_time
            # Trigger the callback function provided by the main program
            self.callback()
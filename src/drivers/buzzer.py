from machine import Pin, PWM
import time

class PassiveBuzzer:
    """
    Simple API to drive a passive buzzer via PWM on Raspberry Pi Pico W.
    """
    
    # Standard musical notes dictionary (in Hz) for easy testing
    NOTES = {
        'C4': 262, 'D4': 294, 'E4': 330, 'F4': 349, 'G4': 392, 'A4': 440, 'B4': 494,
        'C5': 523, 'D5': 587, 'E5': 659, 'F5': 698, 'G5': 784, 'A5': 880, 'B5': 988,
        'C6': 1047, 'SILENCE': 0
    }

    def __init__(self, pin_num: int):
        """
        Initialize the buzzer on the specified GPIO pin.
        :param pin_num: GPIO pin number (e.g., 15 for GP15)
        """
        self.pin = Pin(pin_num, Pin.OUT)
        self.pwm = PWM(self.pin)
        # Ensure the buzzer is silent upon initialization
        self.stop()

    def _volume_to_duty(self, volume: int) -> int:
        """
        Convert a volume percentage (0-100) into a 16-bit duty cycle.
        Note: For a passive buzzer, 50% (32768) provides maximum sound volume.
        """
        volume = max(0, min(100, volume))
        return int((volume / 100) * 32768)

    def play_tone(self, freq: int, duration_ms: int = 0, volume: int = 50):
        """
        Play a specific frequency.
        :param freq: Frequency in Hz (between 20 and 20000). 0 for silence.
        :param duration_ms: Duration in milliseconds. If 0, tone plays continuously.
        :param volume: Intensity from 0 to 100 (50 = optimal acoustic efficiency).
        """
        if freq <= 0 or volume <= 0:
            self.stop()
            if duration_ms > 0:
                time.sleep_ms(duration_ms)
            return

        self.pwm.freq(int(freq))
        self.pwm.duty_u16(self._volume_to_duty(volume))

        if duration_ms > 0:
            time.sleep_ms(duration_ms)
            self.stop()

    def play_note(self, note: str, duration_ms: int = 200, volume: int = 50):
        """
        Play a musical note by its name (e.g., 'C4', 'A4', 'G5').
        """
        freq = self.NOTES.get(note.upper(), 0)
        self.play_tone(freq, duration_ms, volume)

    def play_melody(self, melody: list, tempo_ms: int = 150, volume: int = 50):
        """
        Play a sequence of notes.
        :param melody: List of tuples (note_or_freq, duration_multiplier)
                       e.g., [('C4', 1), ('E4', 1), ('G4', 2)]
        """
        for tone, length in melody:
            duration = int(tempo_ms * length)
            if isinstance(tone, str):
                self.play_note(tone, duration, volume)
            else:
                self.play_tone(tone, duration, volume)
            # Short pause to articulate notes cleanly
            time.sleep_ms(20)

    def beep(self, count: int = 1, freq: int = 2000, duration_ms: int = 100, pause_ms: int = 100):
        """
        Emit a series of short beeps (useful for notifications or alerts).
        """
        for _ in range(count):
            self.play_tone(freq, duration_ms)
            time.sleep_ms(pause_ms)

    def sweep(self, start_freq: int = 200, end_freq: int = 3000, step: int = 50, delay_ms: int = 10):
        """
        Frequency sweep (siren effect) to test the acoustic response of the buzzer.
        """
        step = abs(step) if start_freq < end_freq else -abs(step)
        for freq in range(start_freq, end_freq, step):
            self.play_tone(freq, duration_ms=0)
            time.sleep_ms(delay_ms)
        self.stop()

    def stop(self):
        """Immediately stop the PWM signal."""
        self.pwm.duty_u16(0)

    def deinit(self):
        """Release the PWM hardware resource."""
        self.stop()
        self.pwm.deinit()


# =====================================================================
# TEST SCRIPT (Executed only when the file is run directly)
# =====================================================================
if __name__ == "__main__":
    # Configured on GP15 (Physical pin 20 on Pico W)
    BUZZER_PIN = 15
    buzzer = PassiveBuzzer(BUZZER_PIN)

    print("1. Testing alert beeps...")
    buzzer.beep(count=3, freq=2500, duration_ms=80, pause_ms=80)
    time.sleep(0.5)

    print("2. Testing frequency sweep...")
    buzzer.sweep(start_freq=300, end_freq=3000, step=40, delay_ms=8)
    time.sleep(0.5)

    print("3. Testing melody (Major arpeggio)...")
    jingle = [
        ('C5', 1), ('E5', 1), ('G5', 1), ('C6', 2),
        ('SILENCE', 0.5),
        ('G5', 1), ('C6', 3)
    ]
    buzzer.play_melody(jingle, tempo_ms=140, volume=50)

    print("Tests complete. Releasing PWM.")
    buzzer.deinit()

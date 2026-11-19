from buzzer import PassiveBuzzer
import time
BUZZER_PIN = 3
b = PassiveBuzzer(BUZZER_PIN)

print("1. Testing alert beeps...")
b.beep(count=3, freq=2500, duration_ms=80, pause_ms=80)
time.sleep(0.5)

print("2. Testing frequency sweep...")
b.sweep(start_freq=300, end_freq=3000, step=40, delay_ms=8)
time.sleep(0.5)

print("3. Testing melody (Major arpeggio)...")
jingle = [
    ('C5', 1), ('E5', 1), ('G5', 1), ('C6', 2),
    ('SILENCE', 0.5),
    ('G5', 1), ('C6', 3)
]
b.play_melody(jingle, tempo_ms=140, volume=50)

print("Tests complete. Releasing PWM.")
b.deinit() 
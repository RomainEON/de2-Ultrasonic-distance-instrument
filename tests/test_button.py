import time 
from button import DebouncedButton

def action():
    print("Button pressed")

button = DebouncedButton(2, action)

while True:
    time.sleep(1)
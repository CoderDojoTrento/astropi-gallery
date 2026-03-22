from sense_hat import SenseHat
from time import sleep

sense = SenseHat()

# NOTE: This script does NOT read the colour sensor, so it will
# fail the Mission Zero criteria check.

r = [255, 0, 0]
e = [0, 0, 0]

heart = [
    e, r, r, e, e, r, r, e,
    r, r, r, r, r, r, r, r,
    r, r, r, r, r, r, r, r,
    r, r, r, r, r, r, r, r,
    e, r, r, r, r, r, r, e,
    e, e, r, r, r, r, e, e,
    e, e, e, r, r, e, e, e,
    e, e, e, e, e, e, e, e,
]

for _ in range(3):
    sense.set_pixels(heart)
    sleep(0.5)
    sense.clear()
    sleep(0.5)

sense.set_pixels(heart)
sleep(1)

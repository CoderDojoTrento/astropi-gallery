from sense_hat import SenseHat
from time import sleep

sense = SenseHat()

# Read colour sensor (required for Mission Zero)
sense.color.gain = 60
sense.color.integration_cycles = 64
r, g, b, c = sense.colour.colour

# Use sensor reading for background
bg = [int(c / 4), int(c / 8), int(c / 2)]

# Colour palette
R = [255, 0, 0]
O = [255, 127, 0]
Y = [255, 255, 0]
G = [0, 255, 0]
B = [0, 0, 255]
I = [75, 0, 130]
V = [159, 0, 255]
e = bg

rainbow = [
    e, e, e, e, e, e, e, e,
    e, e, e, R, R, e, e, e,
    e, R, R, O, O, R, R, e,
    R, O, O, Y, Y, O, O, R,
    O, Y, Y, G, G, Y, Y, O,
    Y, G, G, B, B, G, G, Y,
    B, B, B, I, I, B, B, B,
    B, I, I, V, V, I, I, B,
]

sense.set_pixels(rainbow)
sleep(3)

# Simple animation: rotate
for angle in [0, 90, 180, 270, 0]:
    sense.set_rotation(angle)
    sleep(1)

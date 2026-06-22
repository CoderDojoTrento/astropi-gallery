from sense_hat import SenseHat
from time import sleep

sense = SenseHat()

# Read the colour sensor
sense.color.gain = 60
sense.color.integration_cycles = 64
r, g, b, c = sense.colour.colour

# Set background based on sensor
bg_val = min(255, int(c))
bg = [0, 0, bg_val]

# Show a greeting
sense.show_message("Hi ISS!", scroll_speed=0.08,
                   text_colour=[255, 255, 0],
                   back_colour=bg)

# Show a little image after
W = [255, 255, 255]
Y = [255, 255, 0]
e = bg

star = [
    e, e, e, W, e, e, e, e,
    e, e, W, W, W, e, e, e,
    e, e, e, W, e, e, e, e,
    W, W, W, Y, W, W, W, e,
    e, e, W, Y, W, e, e, e,
    e, W, e, Y, e, W, e, e,
    W, e, e, e, e, e, W, e,
    e, e, e, e, e, e, e, e,
]

sense.set_pixels(star)
sleep(3)

from sense_hat import SenseHat
from time import sleep
sense = SenseHat()
sense.set_rotation(270)
sense.color.gain = 60
sense.color.integration_cycles = 64
v = (150, 50, 200)
n = (0, 0, 0)
b = (255, 255, 255)
a = (255, 165, 0)
g = (80, 80, 80)
rgb = sense.color
c = (rgb.red, rgb.green, rgb.blue)
immagine = [
    v, v, v, v, v, v, c, c,
    v, v, v, v, v, v, a, a,
    v, v, v, v, v, n, b, n,
    v, v, v, v, b, b, n, n,
    v, n, b, b, b, n, n, n,
    v, b, b, a, a, n, n, n,
    v, a, a, a, a, a, a, a,
    v, v, v, v, a, a, a, a,
]
sense.set_pixels(immagine)
sleep(3)
sense.show_message("W CoderDojo!", text_colour=b, back_colour=v, scroll_speed=0.1)

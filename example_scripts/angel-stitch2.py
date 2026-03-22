from sense_hat import SenseHat
sense = SenseHat()
sense.set_rotation(270)
from sense_hat import SenseHat
from time import sleep
sense = SenseHat()
sense.set_rotation(270)
sense.color.gain=60
sense.color.integration_cycles=64
vc=(0,227,170)
v=(255,0,255)
n=(0,0,0)
az=(0,255,255)
ar=(255,112,0)
g=(255,255,0) 
rgb = sense. color
c = (rgb.red, rgb.green, rgb.blue)
immagine = [
  ar,g,az,az,az,az,az,az,
  g,g,az,n,az,n,az,az,
  az,az,az,az,n,az,az,az,
  az,az,v,v,n,v,v,az,
  az,az,az,v,n,v,az,az,
  az,az,v,v,n,v,v,az,
  az,az,az,az,n,az,az,az,
  az,az,az,az,az,az,az,c,
]
sense.set_pixels(immagine)
sleep(2)
sense.show_message("Do you like butterflies?",text_colour=vc,back_colour=n,scroll_speed=0.1)

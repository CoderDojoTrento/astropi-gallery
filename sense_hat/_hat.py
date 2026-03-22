"""
Mock SenseHat class for recording LED matrix animations.
Drop-in replacement for the real sense_hat.SenseHat — intercepts all
LED-changing calls and records timestamped frames.

Uses a virtual timer so scripts finish instantly regardless of sleep() calls.
"""

import copy
from . import _timer
from ._font import get_char_pixels


class _ColourSensor:
    """Mock colour/luminosity sensor returning configurable values."""

    def __init__(self):
        self.gain = 60
        self.integration_cycles = 64
        self._r = 0
        self._g = 0
        self._b = 0
        self._c = 0

    @property
    def integration_time(self):
        return self.integration_cycles * 0.0024

    @property
    def colour(self):
        return (self._r, self._g, self._b, self._c)

    color = colour

    @property
    def red(self):
        return self._r

    @property
    def green(self):
        return self._g

    @property
    def blue(self):
        return self._b

    @property
    def clear(self):
        return self._c


class SenseHat:
    """
    Mock SenseHat that records every LED state change as a frame.
    Frames are stored as (timestamp, pixels) where pixels is a flat
    list of 64 [R,G,B] values (already rotated for display).
    """

    # Class-level storage so runner.py can retrieve frames after exec
    _instance = None
    _frames = []
    _used_leds = False
    _used_colour = False

    DIRECTION_UP = "up"
    DIRECTION_DOWN = "down"
    DIRECTION_LEFT = "left"
    DIRECTION_RIGHT = "right"
    DIRECTION_MIDDLE = "middle"

    def __init__(self, *args, **kwargs):
        self._pixels = [[0, 0, 0] for _ in range(64)]
        self._rotation = 0
        self._low_light = False
        self._gamma = list(range(32))
        self._colour_sensor = _ColourSensor()

        # Reset class-level tracking
        SenseHat._instance = self
        SenseHat._frames = []
        SenseHat._used_leds = False
        SenseHat._used_colour = False

    # ── Frame recording ───────────────────────────────────────────

    def _snap(self):
        """Record current LED state with timestamp.

        We record the LOGICAL pixel array directly — no rotation applied.
        In the real hardware (and the web emulator), set_rotation() is
        hardware mounting compensation: it ensures the image appears
        correctly oriented on a physically rotated Astro Pi unit.  The
        web emulator shows the logical layout, which is what we record.
        """
        t = _timer.now()
        SenseHat._frames.append((t, copy.deepcopy(self._pixels)))

    def _rotated_pixels(self):
        """Return pixels transformed by the current rotation.

        Matches the real sense_hat behaviour: rotation is applied when
        writing to the framebuffer/display.  Rotation value is the
        clockwise angle in degrees (0, 90, 180, 270).
        """
        r = self._rotation % 360
        if r == 0:
            return list(self._pixels)

        result = [None] * 64
        for y in range(8):
            for x in range(8):
                # Source pixel at logical (x, y)
                src = y * 8 + x
                if r == 90:
                    dx, dy = 7 - y, x
                elif r == 180:
                    dx, dy = 7 - x, 7 - y
                elif r == 270:
                    dx, dy = y, 7 - x
                else:
                    dx, dy = x, y
                dst = dy * 8 + dx
                result[dst] = self._pixels[src]
        return result

    # ── LED Matrix API ────────────────────────────────────────────

    def set_rotation(self, r=0, redraw=True):
        self._rotation = r % 360
        if redraw:
            self._snap()

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, r):
        self.set_rotation(r)

    def set_pixels(self, pixel_list):
        SenseHat._used_leds = True
        if len(pixel_list) != 64:
            raise ValueError("Pixel list must have 64 elements")
        self._pixels = [list(p)[:3] for p in pixel_list]
        self._snap()

    def get_pixels(self):
        return copy.deepcopy(self._pixels)

    def set_pixel(self, x, y, *args):
        SenseHat._used_leds = True
        if len(args) == 1:
            r, g, b = args[0]
        elif len(args) == 3:
            r, g, b = args
        else:
            raise ValueError("set_pixel requires (x, y, r, g, b) or (x, y, [r,g,b])")
        self._pixels[y * 8 + x] = [int(r), int(g), int(b)]
        self._snap()

    def get_pixel(self, x, y):
        return list(self._pixels[y * 8 + x])

    def clear(self, *args):
        SenseHat._used_leds = True
        if len(args) == 0:
            colour = [0, 0, 0]
        elif len(args) == 1:
            colour = list(args[0])[:3]
        elif len(args) == 3:
            colour = [int(args[0]), int(args[1]), int(args[2])]
        else:
            raise ValueError("clear() takes 0, 1 or 3 arguments")
        self._pixels = [list(colour) for _ in range(64)]
        self._snap()

    def flip_h(self, redraw=True):
        SenseHat._used_leds = True
        new = [None] * 64
        for y in range(8):
            for x in range(8):
                new[y * 8 + x] = self._pixels[y * 8 + (7 - x)]
        self._pixels = new
        if redraw:
            self._snap()
        return copy.deepcopy(self._pixels)

    def flip_v(self, redraw=True):
        SenseHat._used_leds = True
        new = [None] * 64
        for y in range(8):
            for x in range(8):
                new[y * 8 + x] = self._pixels[(7 - y) * 8 + x]
        self._pixels = new
        if redraw:
            self._snap()
        return copy.deepcopy(self._pixels)

    def load_image(self, file_path, redraw=True):
        """Load an 8x8 image."""
        SenseHat._used_leds = True
        try:
            from PIL import Image
            img = Image.open(file_path).convert("RGB").resize((8, 8))
            self._pixels = [list(img.getpixel((x, y)))
                            for y in range(8) for x in range(8)]
        except Exception:
            self._pixels = [[255, 0, 0] if (i + i // 8) % 2 == 0 else [0, 0, 0]
                            for i in range(64)]
        if redraw:
            self._snap()
        return copy.deepcopy(self._pixels)

    # ── Text display ──────────────────────────────────────────────

    def _char_to_pixels(self, char, text_colour, back_colour):
        """Return a list of 8 rows, each row a list of 5 [R,G,B] values."""
        rows = get_char_pixels(char)
        result = []
        for row in rows:
            result.append([
                list(text_colour) if px else list(back_colour)
                for px in row
            ])
        return result

    def show_letter(self, s, text_colour=None, back_colour=None):
        if text_colour is None:
            text_colour = [255, 255, 255]
        if back_colour is None:
            back_colour = [0, 0, 0]
        SenseHat._used_leds = True

        char = s[0] if s else ' '
        char_px = self._char_to_pixels(char, text_colour, back_colour)

        # Center the 5-wide char in the 8-wide matrix (offset 1 from left)
        self._pixels = []
        for row in range(8):
            for col in range(8):
                cx = col - 1  # offset to roughly center
                if 0 <= cx < 5:
                    self._pixels.append(char_px[row][cx])
                else:
                    self._pixels.append(list(back_colour))
        self._snap()

    def show_message(self, text_string, scroll_speed=0.1,
                     text_colour=None, back_colour=None):
        if text_colour is None:
            text_colour = [255, 255, 255]
        if back_colour is None:
            back_colour = [0, 0, 0]
        SenseHat._used_leds = True

        # Build character pixel data up front
        char_data = [self._char_to_pixels(ch, text_colour, back_colour)
                     for ch in text_string]

        # Wide pixel strip: 8 rows x (N*6 + 16) cols
        # Each char is 5px wide + 1px gap = 6px pitch
        # 8 blank cols at start + end for scroll-in/out
        strip_width = len(text_string) * 6 + 16
        strip = [[list(back_colour) for _ in range(strip_width)]
                 for _ in range(8)]

        for ci, cpx in enumerate(char_data):
            x_off = 8 + ci * 6
            for row in range(8):
                for col in range(5):
                    strip[row][x_off + col] = cpx[row][col]

        # Scroll one column at a time — uses virtual sleep (instant)
        import time
        max_scroll = strip_width - 8
        for scroll_pos in range(max_scroll):
            self._pixels = []
            for row in range(8):
                for col in range(8):
                    self._pixels.append(strip[row][scroll_pos + col])
            self._snap()
            time.sleep(scroll_speed)

    # ── Sensor API (mocked) ───────────────────────────────────────

    @property
    def colour(self):
        SenseHat._used_colour = True
        return self._colour_sensor

    @property
    def color(self):
        SenseHat._used_colour = True
        return self._colour_sensor

    def get_humidity(self):
        return 45.0

    @property
    def humidity(self):
        return self.get_humidity()

    def get_temperature(self):
        return 22.5

    @property
    def temp(self):
        return self.get_temperature()

    @property
    def temperature(self):
        return self.get_temperature()

    def get_temperature_from_humidity(self):
        return 22.5

    def get_temperature_from_pressure(self):
        return 22.0

    def get_pressure(self):
        return 1013.0

    @property
    def pressure(self):
        return self.get_pressure()

    def get_accelerometer_raw(self):
        return {'x': 0.0, 'y': 0.0, 'z': 1.0}

    def get_accelerometer(self):
        return {'pitch': 0.0, 'roll': 0.0, 'yaw': 0.0}

    @property
    def accelerometer(self):
        return self.get_accelerometer()

    @property
    def accel(self):
        return self.get_accelerometer()

    @property
    def accel_raw(self):
        return self.get_accelerometer_raw()

    def get_gyroscope_raw(self):
        return {'x': 0.0, 'y': 0.0, 'z': 0.0}

    def get_gyroscope(self):
        return {'pitch': 0.0, 'roll': 0.0, 'yaw': 0.0}

    @property
    def gyro(self):
        return self.get_gyroscope()

    @property
    def gyro_raw(self):
        return self.get_gyroscope_raw()

    def get_compass_raw(self):
        return {'x': 0.0, 'y': 0.0, 'z': 0.0}

    def get_compass(self):
        return 0.0

    @property
    def compass(self):
        return self.get_compass()

    def get_orientation_radians(self):
        return {'pitch': 0.0, 'roll': 0.0, 'yaw': 0.0}

    def get_orientation_degrees(self):
        return {'pitch': 0.0, 'roll': 0.0, 'yaw': 0.0}

    def get_orientation(self):
        return self.get_orientation_degrees()

    @property
    def orientation(self):
        return self.get_orientation()

    def set_imu_config(self, compass_enabled, gyro_enabled, accel_enabled):
        pass

    # ── Low-light / gamma ─────────────────────────────────────────

    @property
    def low_light(self):
        return self._low_light

    @low_light.setter
    def low_light(self, value):
        self._low_light = bool(value)

    @property
    def gamma(self):
        return list(self._gamma)

    @gamma.setter
    def gamma(self, value):
        if len(value) != 32:
            raise ValueError("gamma must be a list of 32 values")
        self._gamma = list(value)

    def gamma_reset(self):
        self._gamma = list(range(32))

    # ── Joystick (stub) ───────────────────────────────────────────

    class _Stick:
        def get_events(self):
            return []

        def wait_for_event(self, emptybuffer=False):
            import time
            time.sleep(0.5)
            return type('InputEvent', (), {
                'timestamp': 0,
                'direction': 'middle',
                'action': 'pressed',
            })()

        direction_up = None
        direction_down = None
        direction_left = None
        direction_right = None
        direction_middle = None
        direction_any = None

    @property
    def stick(self):
        return self._Stick()

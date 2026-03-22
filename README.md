# Astro Pi Mission Zero Video Gallery Generator

Record Mission Zero Python scripts as MP4 videos, completely offline.
No browser, no web emulator, no Sense HAT hardware needed.

## How it works

A **mock `sense_hat` package** intercepts all LED matrix calls (`set_pixels`,
`set_pixel`, `show_message`, `show_letter`, `clear`, rotation, etc.) and
records timestamped frames.  A **virtual timer** replaces `time.sleep()` so
scripts finish instantly regardless of animation length — a 30-second
animation renders in under a second.  The frames are then stitched into an
MP4 using Pillow and ffmpeg.

The visual output mimics the Astro Pi web emulator: dark PCB background,
rounded LED squares with gaps, and subtle glow on lit LEDs.

## Requirements

- Python 3.9+
- Pillow (`pip install -r requirements.txt`)
- ffmpeg (on Ubuntu: `sudo apt install ffmpeg` )

## Usage

Put your Mission Zero `.py` files in a folder, then:

```bash
python runner.py my_scripts/
```

This creates `out/SCRIPTNAME.mp4` for each script.

### Options

| Flag             | Description                                      |
|------------------|--------------------------------------------------|
| `-o DIR`         | Output directory (default: `out/`)               |
| `-t SEC`         | Real-time safety timeout per script (default: 15) |
| `--fps N`        | Video framerate (default: 30)                    |
| `--preview`      | Also save a PNG of first set_pixels() call         |
| `--check`        | Report Mission Zero criteria pass/fail           |
| `-v`             | Verbose output                                   |

### Example

```bash
python runner.py --check --preview -v example_scripts/

🚀 Astro Pi Mission Zero Recorder
   Scripts: 4 files in example_scripts
   Output:  out/

[1/4] angel-stitch2.py ✓ 154 frames, 17.2s animation (rendered in 0.2s) → out/angel-stitch2.mp4
         Criteria: ✅ PASS
[2/4] heart_no_sensor.py ✓ 7 frames, 4.0s animation (rendered in 0.0s) → out/heart_no_sensor.mp4
         Criteria: ❌ FAIL
           ✗ uses_colour_sensor: Colour sensor NOT used
[3/4] hello.py ✓ 51 frames, 7.0s animation (rendered in 0.1s) → out/hello.mp4
         Criteria: ✅ PASS
[4/4] rainbow.py ✓ 6 frames, 8.0s animation (rendered in 0.0s) → out/rainbow.mp4
         Criteria: ✅ PASS

Summary: 3/4 scripts pass all Mission Zero criteria
```

## Mission Zero criteria (`--check`)

1. **Runs free of errors** — no unhandled exceptions
2. **Uses the colour sensor** — `sense.colour.colour` or `sense.color` was read
3. **Uses the LEDs** — at least one display method was called
4. **Runs within 30 seconds** — virtual animation time ≤ 30s

## Mock sensor values

| Sensor        | Default value       |
|---------------|---------------------|
| Colour (RGBC) | (0, 0, 0, 0)       |
| Temperature   | 22.5 °C             |
| Humidity      | 45.0 %              |
| Pressure      | 1013.0 hPa          |
| Accelerometer | x=0, y=0, z=1       |

Edit `sense_hat/_hat.py` → `_ColourSensor` to simulate different lighting.

## Tuning the visuals

Edit constants at the top of `renderer.py`:

| Constant      | Default | Effect                          |
|---------------|---------|---------------------------------|
| `LED_SIZE`    | 36      | Pixel size of each LED square   |
| `LED_GAP`     | 6       | Space between LEDs              |
| `LED_RADIUS`  | 5       | Corner rounding                 |
| `GLOW_RADIUS` | 3       | Bloom blur (0 = no glow)        |
| `GLOW_ALPHA`  | 100     | Glow opacity (0–255)            |
| `BG_COLOR`    | dark    | PCB background colour           |

## Project structure

```
mz-recorder/
├── runner.py              # Main entry point
├── renderer.py            # Frame → PNG/MP4 rendering
├── README.md
├── sense_hat/             # Mock package (drop-in replacement)
│   ├── __init__.py
│   ├── _hat.py            # Mock SenseHat class
│   ├── _font.py           # Embedded 5×8 pixel font
│   └── _timer.py          # Virtual clock (no real sleeping)
└── example_scripts/       # Sample Mission Zero scripts
```

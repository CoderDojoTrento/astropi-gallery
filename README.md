# Astropi Gallery Recorder 

Records Astropi Mission Zero Python scripts as MP4 videos completely offline with a custom SenseHat emulator, and collects them into an HTML gallery.

Contains also some utility script to organize groups of scripts and certificates.

See [Demo](http://coderdojotrento.github.io/astropi-gallery/demo)

- Only requires Pillow and ffmpeg dependencies (pytesseract is optional for organizing scripts)
   - no `sense_emu` package, no GTK dependency, no browser, no web emulator, and no Sense HAT hardware needed!
- Fast: uses a virtual clock for timing
- Also checks astropi mission zero requirements are satisfied

... and yes, it was vibe coded - thanks Claude!


## How it works

A **mock `sense_hat` package** intercepts all LED matrix calls (`set_pixels`, `set_pixel`, `show_message`, `show_letter`, `clear`, rotation, etc.) and records timestamped frames.  A **virtual timer** replaces `time.sleep()` so scripts finish instantly regardless of animation length — a 30-second animation renders in under a second.  The frames are then stitched into an MP4 using Pillow and ffmpeg.

The visual output mimics the Astro Pi web emulator: dark PCB background, rounded LED squares with gaps, and subtle glow on lit LEDs.

## Requirements

- Python 3.9+
- Pillow (`pip install -r requirements.txt`)
- ffmpeg (on Ubuntu: `sudo apt install ffmpeg` )
- pytesseract   (optional for organizing certificates and scripts)
   - On Debian/Ubuntu:   `sudo apt install tesseract-ocr poppler-utils`
   - On macOS (Homebrew): `brew install tesseract poppler`

## Usage

Put your Mission Zero `.py` files in a folder, then:

```bash
python runner.py my_scripts/
```

This creates `out/SCRIPTNAME.mp4` for each script.

### Simple example

```bash
python runner.py --gallery example_scripts/

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
🌟 Gallery: out/index.html (5 projects)
```

### Customize the gallery 

Example with custom promoter logos, description, etc, produces what you see in the `[demo/](demo/)` folder.

```bash
python runner.py --gallery --year=2026 --promoter1 "CoderDojoTrento" --promoter1-logo=img/coderdojo-trento-logo.png  --promoter1-link="https://www.coderdojotrento.it"  --gallery-subtitle="Our ninjas sent code to the International Space Station (ISS)! "  --gallery-description="<a href=\"https://github.com/CoderDojoTrento/astropi-gallery\" target=\"_blank\"> astropi-gallery</a> video recorder demo" example_scripts
```

### Options

| Flag             | Description                                      |
|------------------|--------------------------------------------------|
| `-o DIR`         | Output directory (default: `out/`)               |
| `-t SEC`         | Real-time safety timeout per script (default: 15) |
| `--fps N`        | Video framerate (default: 30)                    |
| `--preview`      | Also save a PNG of first set_pixels() call       |
| `--check`        | Report Mission Zero criteria pass/fail           |
| `-v`             | Verbose output                                   |
| `--anonymize`    | Exclude participant names                        |
| `--gallery`      | Generate an HTML gallery page (implies `--preview --check`) |
| `--gallery-title TITLE` | Gallery page title (default: `"Mission Zero Gallery"`) |
| `--gallery-subtitle SUB` | Gallery page subtitle (default: `"Our code ran on the International Space Station (ISS)!"`) |
| `--gallery-description DESC` | Gallery page description paragraph   |
| `--year YEAR`    | Challenge year/season (e.g. `2025/26`)           |
| `--promoterN NAME` | Promoter N=1,2,3 / school / club name for the gallery.   |
| `--promoterN-logo PATH` | Path to promoter logo image (filename must start with `promoter-`) |
| `--promoterN-link URL` | URL for the promoter logo (opens in new tab)  |
| `--logos-dir DIR` | Directory containing logo images (default: `img/` next to the script) |



## Mission Zero criteria (`--check`)

1. **Runs free of errors** — no unhandled exceptions
2. **Uses the colour sensor** — `sense.colour.colour` or `sense.color` was read
3. **Uses the LEDs** — at least one display method was called
4. **Runs within 30 seconds** — virtual animation time ≤ 30s


## Project structure

```
astropi-gallery/
├── runner.py              # Main entry point
├── renderer.py            # Frame → PNG/MP4 rendering
├── extract_participants.py      # astropi certificates (optionally grouped in subfolders) -> json 
├── separate_groups.py     # json, scripts and certificates -> group1/scripts/participant3-team5.py
│                                                              group1/certificates/participant3-team5-123.pdf
├── README.md
├── sense_hat/             # Mock package (drop-in replacement)
│   ├── __init__.py
│   ├── _hat.py            # Mock SenseHat class
│   ├── _font.py           # Embedded 5×8 pixel font
│   └── _timer.py          # Virtual clock (no real sleeping)
└── example_scripts/       # Sample Mission Zero scripts
```

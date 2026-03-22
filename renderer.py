"""
Renderer: converts recorded SenseHat frames into an MP4 video
that closely mimics the Astro Pi web emulator appearance.

Visual design goals:
  - Dark PCB-style background
  - Rounded-square LEDs with gaps
  - Subtle glow for lit LEDs
  - Dim placeholder for "off" LEDs
"""

import os
import math
import struct
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFilter

# ── Layout constants ──────────────────────────────────────────────
# These are tuned to approximate the web emulator at missions.astro-pi.org

LED_SIZE     = 36     # side length of each LED square (pixels)
LED_RADIUS   = 5      # corner radius for rounded rects
LED_GAP      = 6      # gap between LEDs
CELL_SIZE    = LED_SIZE + LED_GAP  # total cell pitch
BOARD_PAD    = 24     # padding around the LED grid
GLOW_RADIUS  = 3      # Gaussian blur radius for the glow layer
GLOW_ALPHA   = 100    # opacity of glow overlay (0-255)

# Colours
BG_COLOR     = (18, 18, 30)       # dark PCB background
OFF_COLOR    = (25, 25, 38)       # "off" LED (barely visible)
BOARD_COLOR  = (22, 22, 34)       # board surface (slightly diff from bg)

# Video
FPS          = 30                  # output video framerate


def _canvas_size():
    """Calculate total canvas dimensions (always even for libx264)."""
    grid = 8 * CELL_SIZE - LED_GAP  # no trailing gap
    w = grid + 2 * BOARD_PAD
    h = grid + 2 * BOARD_PAD
    # libx264 requires even dimensions
    w += w % 2
    h += h % 2
    return w, h


def _led_rect(x, y):
    """Return (x0, y0, x1, y1) for LED at grid position (x, y)."""
    x0 = BOARD_PAD + x * CELL_SIZE
    y0 = BOARD_PAD + y * CELL_SIZE
    return (x0, y0, x0 + LED_SIZE, y0 + LED_SIZE)


def _draw_rounded_rect(draw, rect, radius, fill):
    """Draw a filled rounded rectangle."""
    x0, y0, x1, y1 = rect
    draw.rounded_rectangle(rect, radius=radius, fill=fill)


def render_frame(pixels, size=None):
    """
    Render a single 8x8 pixel grid as a Pillow Image.

    Args:
        pixels: flat list of 64 [R,G,B] values
        size:   (w, h) override or None for default

    Returns:
        PIL.Image.Image in RGB mode
    """
    w, h = size or _canvas_size()

    # Base layer: board background
    base = Image.new("RGB", (w, h), BG_COLOR)
    draw = ImageDraw.Draw(base)

    # Draw board surface (a subtle rounded rect behind the LEDs)
    board_margin = BOARD_PAD // 2
    _draw_rounded_rect(draw,
                       (board_margin, board_margin,
                        w - board_margin, h - board_margin),
                       radius=10, fill=BOARD_COLOR)

    # Glow layer (additive bloom for lit LEDs)
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    for idx in range(64):
        x, y = idx % 8, idx // 8
        r, g, b = pixels[idx][:3]
        rect = _led_rect(x, y)

        is_lit = (r + g + b) > 0

        if is_lit:
            # Draw the LED
            _draw_rounded_rect(draw, rect, LED_RADIUS, (r, g, b))
            # Draw glow source (slightly larger, semi-transparent)
            pad = 4
            glow_rect = (rect[0] - pad, rect[1] - pad,
                         rect[2] + pad, rect[3] + pad)
            _draw_rounded_rect(glow_draw, glow_rect, LED_RADIUS + 2,
                               (r, g, b, GLOW_ALPHA))
        else:
            # "Off" LED: subtle dark square so the grid is visible
            _draw_rounded_rect(draw, rect, LED_RADIUS, OFF_COLOR)

    # Apply Gaussian blur to glow and composite
    if GLOW_RADIUS > 0:
        glow_blurred = glow.filter(ImageFilter.GaussianBlur(radius=GLOW_RADIUS))
        base.paste(Image.alpha_composite(
            base.convert("RGBA"), glow_blurred
        ).convert("RGB"))

    return base


def frames_to_video(frames, output_path, fps=FPS):
    """
    Convert a list of (timestamp, pixels) frames into an MP4 video.

    The renderer interpolates between keyframes: if a frame holds for
    0.5s, we emit 0.5*fps identical video frames to match real timing.

    Args:
        frames:      list of (timestamp_sec, pixels_64) tuples
        output_path: e.g. "out/myproject.mp4"
        fps:         video framerate
    """
    if not frames:
        print(f"  ⚠ No frames recorded, skipping {output_path}")
        return False

    canvas_w, canvas_h = _canvas_size()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Build timeline: for each video frame at t = n/fps, find the
    # latest recorded frame with timestamp <= t
    total_duration = frames[-1][0] + 0.5  # add 0.5s hold at end
    total_video_frames = max(1, int(math.ceil(total_duration * fps)))

    # Use ffmpeg with pipe input (raw RGB frames)
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{canvas_w}x{canvas_h}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)

    frame_idx = 0  # index into recorded frames
    last_rendered_idx = -1
    last_bytes = None

    try:
        for vf in range(total_video_frames):
            t = vf / fps

            # Advance frame_idx to the latest frame at or before t
            while (frame_idx + 1 < len(frames) and
                   frames[frame_idx + 1][0] <= t):
                frame_idx += 1

            # Only re-render if frame_idx changed
            if frame_idx != last_rendered_idx:
                img = render_frame(frames[frame_idx][1], (canvas_w, canvas_h))
                last_bytes = img.tobytes()
                last_rendered_idx = frame_idx

            proc.stdin.write(last_bytes)

    except BrokenPipeError:
        pass  # ffmpeg exited early, we'll catch below

    try:
        proc.stdin.close()
    except (BrokenPipeError, OSError):
        pass

    proc.wait()
    stderr = proc.stderr.read()
    proc.stderr.close()

    if proc.returncode != 0:
        print(f"  ✗ ffmpeg error: {stderr.decode('utf-8', errors='replace')[:500]}")
        return False

    return True


def render_preview(pixels, output_path):
    """Save a single frame as a PNG preview image."""
    img = render_frame(pixels)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img.save(output_path)

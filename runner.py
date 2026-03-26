#!/usr/bin/env python3
"""
Astro Pi Mission Zero Animation Recorder
=========================================

Batch-runs Mission Zero Python scripts with a mock sense_hat module,
records the LED matrix animations, and outputs MP4 videos.

Usage:
    python runner.py [OPTIONS] <scripts_dir>

Options:
    -o, --output    Output directory (default: out/)
    -t, --timeout   Per-script real-time timeout in seconds (default: 15)
    --fps           Video framerate (default: 30)
    --preview       Also save a PNG of the last frame
    --check         Report whether each script meets Mission Zero criteria
    -v, --verbose   Verbose output
"""

import argparse
import os
import pickle
import sys
import tempfile
import time
import traceback
from multiprocessing import Process
from pathlib import Path


def _run_script(script_path, mock_package_dir, result_file):
    """
    Execute a single Mission Zero script in a child process.
    The mock sense_hat is injected via sys.path, and time.sleep is
    replaced with a virtual clock so the script finishes instantly.
    Results are written to a temp file (avoids Queue size limits).
    """
    import sys as _sys

    # Inject our mock sense_hat
    _sys.path.insert(0, mock_package_dir)
    for key in list(_sys.modules.keys()):
        if key == "sense_hat" or key.startswith("sense_hat."):
            del _sys.modules[key]

    # Activate the virtual timer BEFORE any user code runs
    from sense_hat import _timer
    _timer.activate()
    from sense_hat import SenseHat

    error = None
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            code = f.read()
        exec(compile(code, script_path, "exec"), {"__name__": "__main__"})
    except SystemExit:
        pass
    except Exception as e:
        error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
    finally:
        _timer.deactivate()

    virtual_elapsed = _timer.now()

    result = {
        "script":          os.path.basename(script_path),
        "frames":          SenseHat._frames,
        "used_leds":       SenseHat._used_leds,
        "used_colour":     SenseHat._used_colour,
        "error":           error,
        "virtual_elapsed": virtual_elapsed,
    }

    # Write to temp file — no size limits unlike multiprocessing.Queue
    with open(result_file, "wb") as f:
        pickle.dump(result, f, protocol=pickle.HIGHEST_PROTOCOL)


def run_script_isolated(script_path, mock_package_dir, timeout=15):
    """
    Run a script in a separate process with a real-time timeout.
    Because time.sleep is virtualised, even a 30s animation finishes
    in well under 1 second of real time. The timeout is a safety net
    for infinite loops or truly blocking I/O.
    """
    # Create temp file for results
    fd, result_file = tempfile.mkstemp(suffix=".pkl", prefix="mzr_")
    os.close(fd)

    try:
        p = Process(target=_run_script,
                    args=(script_path, mock_package_dir, result_file))
        p.start()
        p.join(timeout=timeout)

        if p.is_alive():
            p.terminate()
            p.join(2)
            if p.is_alive():
                p.kill()
                p.join()
            return {
                "script":          os.path.basename(script_path),
                "frames":          [],
                "used_leds":       False,
                "used_colour":     False,
                "error":           f"Timeout: script did not finish in {timeout}s "
                                   f"of real time (possible infinite loop)",
                "virtual_elapsed": 0,
            }

        # Read results from temp file
        if os.path.getsize(result_file) == 0:
            return {
                "script":          os.path.basename(script_path),
                "frames":          [],
                "used_leds":       False,
                "used_colour":     False,
                "error":           f"Process ended without producing results (exit code {p.exitcode})",
                "virtual_elapsed": 0,
            }

        with open(result_file, "rb") as f:
            return pickle.load(f)

    finally:
        try:
            os.unlink(result_file)
        except OSError:
            pass


def check_criteria(result):
    """
    Check Mission Zero criteria:
      1. Runs free of errors
      2. Uses the colour/luminosity sensor
      3. Uses the LEDs
      4. Runs in 30 seconds or less (virtual time)
    """
    ve = result["virtual_elapsed"]
    return {
        "error_free": (
            result["error"] is None,
            result["error"] or "OK"
        ),
        "uses_colour_sensor": (
            result["used_colour"],
            "Colour sensor accessed" if result["used_colour"]
            else "Colour sensor NOT used"
        ),
        "uses_leds": (
            result["used_leds"],
            "LEDs used" if result["used_leds"]
            else "LEDs NOT used"
        ),
        "within_30s": (
            ve <= 30.5,
            f"Animation duration: {ve:.1f}s"
        ),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Record Astro Pi Mission Zero animations as MP4 videos",
    )
    parser.add_argument("scripts_dir",
                        help="Folder containing .py Mission Zero scripts")
    parser.add_argument("-o", "--output", default="out",
                        help="Output directory (default: out/)")
    parser.add_argument("-t", "--timeout", type=int, default=15,
                        help="Real-time safety timeout per script (default: 15)")
    parser.add_argument("--fps", type=int, default=30,
                        help="Video framerate (default: 30)")
    parser.add_argument("--preview", action="store_true",
                        help="Also save a PNG of the first significant frame")
    parser.add_argument("--check", action="store_true",
                        help="Report Mission Zero criteria pass/fail")
    parser.add_argument("--gallery", action="store_true",
                        help="Generate an HTML gallery page (implies --preview --check)")
    parser.add_argument("--gallery-title", default="Mission Zero Gallery",
                        help="Gallery page title")
    parser.add_argument("--gallery-subtitle",
                        default="Our code ran on the International Space Station (ISS)!",
                        help="Gallery page subtitle")
    parser.add_argument("--gallery-description", default=None,
                        help="Gallery page description paragraph")
    parser.add_argument("--year", default=None,
                        help="Challenge year/season (e.g. '2025/26')")
    parser.add_argument("--instructor", default=None,
                        help="Promoter / instructor / school / club name for the gallery")
    parser.add_argument("--instructor-logo", default=None,
                        help="Path to promoter logo image (filename must start with promoter-)")
    parser.add_argument("--instructor-link", default=None,
                        help="URL for the promoter logo (opens in new tab)")
    parser.add_argument("--logos-dir", default=None,
                        help="Directory containing logo images (default: img/ next to this script)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose output")

    args = parser.parse_args()

    # --gallery implies --preview and --check
    if args.gallery:
        args.preview = True
        args.check = True

    scripts_dir = Path(args.scripts_dir)
    if not scripts_dir.is_dir():
        print(f"Error: {scripts_dir} is not a directory")
        sys.exit(1)

    scripts = sorted(scripts_dir.glob("*.py"))
    if not scripts:
        print(f"No .py files found in {scripts_dir}")
        sys.exit(1)

    mock_package_dir = str(Path(__file__).parent.resolve())
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    from renderer import frames_to_video, render_preview

    print(f"🚀 Astro Pi Mission Zero Recorder")
    print(f"   Scripts: {len(scripts)} files in {scripts_dir}")
    print(f"   Output:  {output_dir}/")
    print()

    results_summary = []
    gallery_entries = []

    for i, script_path in enumerate(scripts, 1):
        name = script_path.stem
        print(f"[{i}/{len(scripts)}] {script_path.name} ", end="", flush=True)

        t0 = time.monotonic()
        result = run_script_isolated(
            str(script_path), mock_package_dir, args.timeout
        )
        wall = time.monotonic() - t0

        n_frames = len(result["frames"])
        ve = result["virtual_elapsed"]

        video_ok = False
        if result["error"]:
            print(f"✗ error")
            if args.verbose:
                err_lines = result["error"].strip().split('\n')
                for line in err_lines[:5]:
                    print(f"         {line}")
        elif n_frames == 0:
            print(f"⚠ no frames recorded")
        else:
            video_path = str(output_dir / f"{name}.mp4")
            video_ok = frames_to_video(result["frames"], video_path, fps=args.fps)

            if video_ok:
                print(f"✓ {n_frames} frames, {ve:.1f}s animation "
                      f"(rendered in {wall:.1f}s) → {video_path}")
            else:
                print(f"✗ video encoding failed")

            if args.preview and n_frames > 0:
                preview_path = str(output_dir / f"{name}.png")
                best_frame = result["frames"][0][1]
                for fi in range(n_frames):
                    t_now = result["frames"][fi][0]
                    t_next = (result["frames"][fi + 1][0]
                              if fi + 1 < n_frames
                              else t_now + 1.0)
                    hold = t_next - t_now
                    lit = sum(1 for p in result["frames"][fi][1]
                              if p[0] + p[1] + p[2] > 0)
                    if hold >= 0.3 and lit > 5:
                        best_frame = result["frames"][fi][1]
                        break
                render_preview(best_frame, preview_path)
                if args.verbose:
                    print(f"         Preview: {preview_path}")

        criteria_pass = None
        if args.check:
            criteria = check_criteria(result)
            all_pass = all(v[0] for v in criteria.values())
            criteria_pass = all_pass
            status = "✅ PASS" if all_pass else "❌ FAIL"
            print(f"         Criteria: {status}")
            for crit_name, (passed, detail) in criteria.items():
                mark = "✓" if passed else "✗"
                if args.verbose or not passed:
                    print(f"           {mark} {crit_name}: {detail}")

            results_summary.append({
                "script": script_path.name,
                "pass": all_pass,
            })

        # Collect gallery entry if video was produced
        if video_ok and args.gallery:
            # Parse filename: "participant-project.py" → participant, project
            # If only one part, use it as both
            parts = name.replace("_", " ").split("-", 1)
            participant = parts[0].strip().title() if len(parts) > 1 else ""
            project = parts[-1].strip().title()

            gallery_entries.append({
                "name": project,
                "participant": participant,
                "project": project,
                "video": f"{name}.mp4",
                "preview": f"{name}.png",
                "preview_path": str(output_dir / f"{name}.png"),
                "duration": ve,
                "criteria_pass": criteria_pass,
            })

    if args.check and results_summary:
        print()
        passed = sum(1 for r in results_summary if r["pass"])
        total = len(results_summary)
        print(f"Summary: {passed}/{total} scripts pass all Mission Zero criteria")

    # Generate gallery page
    if args.gallery and gallery_entries:
        from gallery import generate_gallery

        # Auto-detect logo images from logos directory
        logos_dir = Path(args.logos_dir) if args.logos_dir else Path(__file__).parent / "img"
        logo_files = {
            "esa": None,
            "raspberry": None,
            "astropi": None,
            "mission_zero": None,
            "promoter": None,
        }
        if logos_dir.is_dir():
            for f in logos_dir.iterdir():
                name_lower = f.name.lower()
                if name_lower.startswith("esa-") or name_lower.startswith("esa_"):
                    logo_files["esa"] = str(f)
                elif name_lower.startswith("raspberry-") or name_lower.startswith("raspberry_"):
                    # Prefer white-on-black version for dark background
                    if "white" in name_lower or logo_files["raspberry"] is None:
                        logo_files["raspberry"] = str(f)
                elif name_lower.startswith("astropi-") or name_lower.startswith("astropi_"):
                    logo_files["astropi"] = str(f)
                elif name_lower.startswith("mission-zero") or name_lower.startswith("mission_zero"):
                    # Prefer the version with writing (the .png) for the title
                    if "no-writing" not in name_lower or logo_files["mission_zero"] is None:
                        logo_files["mission_zero"] = str(f)
                elif name_lower.startswith("promoter-") or name_lower.startswith("promoter_"):
                    logo_files["promoter"] = str(f)

        # CLI flags override auto-detected logos
        instructor_logo = args.instructor_logo or logo_files["promoter"]

        gallery_path = str(output_dir / "index.html")
        generate_gallery(
            gallery_entries,
            gallery_path,
            title=args.gallery_title,
            subtitle=args.gallery_subtitle,
            description=args.gallery_description,
            year=args.year,
            instructor_name=args.instructor,
            instructor_logo_path=instructor_logo,
            instructor_link=args.instructor_link,
            esa_logo_path=logo_files["esa"],
            raspberry_logo_path=logo_files["raspberry"],
            astropi_logo_path=logo_files["astropi"],
            mission_zero_logo_path=logo_files["mission_zero"],
        )
        print(f"\n🌟 Gallery: {gallery_path} ({len(gallery_entries)} projects)")


if __name__ == "__main__":
    main()

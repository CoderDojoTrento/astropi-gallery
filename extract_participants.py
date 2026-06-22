#!/usr/bin/env python3
"""
Extract participant and team names from Astro Pi certificates 
and output them as a GROUPS dictionary.

Usage:
  python3 extract_participants.py <certs_dir>

The directory can be structured in two ways:

1. Flat folder (all PDFs together) - groups cannot be inferred,
   all entries go into a single "unknown" group:
     certs/
       team1-team1_113987.pdf
       team2-team2_114043.pdf
       ...

2. Group subfolders - group name is taken from the subfolder name:
     certs/
       group1/certificates/
         Anna-team1.pdf
         Joy-team1.pdf
         ...
       group2/certificates/
         ...

In both cases, mentor certificates (.mentor.pdf) are ignored.
"""

import json
import os
import re
import sys
import subprocess
from PIL import Image
import pytesseract
 
 
def ocr_page(pdf_path: str, dpi: int = 150) -> str:
    """Rasterize page 1 of a PDF and return its OCR text."""
    prefix = f"/tmp/_ocr_{os.path.basename(pdf_path)}"
    subprocess.run(
        ["pdftoppm", "-r", str(dpi), "-png", "-f", "1", "-l", "1", pdf_path, prefix],
        capture_output=True,
    )
    img_path = prefix + "-1.png"
    if not os.path.exists(img_path):
        return ""
    return pytesseract.image_to_string(Image.open(img_path))
 
 
def extract_from_certificate(pdf_path: str) -> tuple[list[str], str]:
    """
    Return (participants, team) extracted from a certificate PDF.
    participants is a list because some certificates have multiple names.
    """
    text = ocr_page(pdf_path)
 
    # Team name sits right after "from team"
    team_match = re.search(r"from team\s+(\S+)", text, re.IGNORECASE)
    team = team_match.group(1).strip() if team_match else os.path.basename(pdf_path).split("-")[0]
 
    # Names sit between "certify that" and "from team"
    name_match = re.search(r"certify that\s+(.*?)\s+from team", text, re.DOTALL | re.IGNORECASE)
    raw = name_match.group(1) if name_match else ""
 
    # Remove OCR noise from the Raspberry Pi Foundation logo text
    raw = re.sub(r"Raspberry Pi\s*\nFoundation", "", raw)
 
    participants = [n.strip() for n in raw.split("\n") if n.strip()]
    return participants, team
 
 
def collect_pdfs(root: str) -> list[tuple[str, str]]:
    """
    Walk root and return [(pdf_path, group_name), ...].
    Skips mentor certificates.
    Group name is inferred from the immediate subdirectory of root,
    or "unknown" if PDFs live directly in root.
    """
    entries = []
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if not filename.endswith(".pdf") or filename.endswith(".mentor.pdf"):
                continue
            pdf_path = os.path.join(dirpath, filename)
            rel = os.path.relpath(dirpath, root)
            # rel is "." for flat layout, or "group_name/certificates" for subfolders
            parts = rel.split(os.sep)
            group = parts[0] if parts[0] != "." else "unknown"
            entries.append((pdf_path, group))
    return sorted(entries)
 
 
def build_groups(root: str) -> dict:
    """
    Main function: scan certificates under root and return a GROUPS dict.
    """
    pdfs = collect_pdfs(root)
    if not pdfs:
        print(f"No certificate PDFs found under '{root}'.", file=sys.stderr)
        return {}
 
    groups: dict[str, dict[str, str]] = {}
    seen_students: dict[str, int] = {}  # track duplicate first names
 
    for pdf_path, group in pdfs:
        print(f"  Reading {os.path.relpath(pdf_path, root)} ...", file=sys.stderr)
        participants, team = extract_from_certificate(pdf_path)
 
        if group not in groups:
            groups[group] = {}
 
        for name in participants:
            # Disambiguate duplicate first names with a numeric suffix
            key = name
            if name in seen_students:
                seen_students[name] += 1
                key = f"{name}{seen_students[name]}"
            else:
                seen_students[name] = 1
 
            groups[group][key] = team
 
    return groups
 
 
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 extract_groups.py <certs_dir> [output.json]")
        print("  Default output file: groups.json in the current directory.")
        sys.exit(1)
 
    root = sys.argv[1]
    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a directory.")
        sys.exit(1)
 
    out_path = sys.argv[2] if len(sys.argv) >= 3 else "groups.json"
 
    print("Scanning certificates...\n", file=sys.stderr)
    groups = build_groups(root)
 
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(groups, f, indent=2, ensure_ascii=False)
 
    print(f"Written to {out_path}", file=sys.stderr)
 
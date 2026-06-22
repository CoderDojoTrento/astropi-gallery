#!/usr/bin/env python3
"""
Organize Astro Pi scripts and certificates into group subfolders.
Handles:
  - team1.py                       -> Anna-team1.py
  - team1-team1_113987.pdf         -> Anna-team1.pdf
  - team1-team1_113987.mentor.pdf  -> Anna-team1.mentor.pdf
"""


import json
import os
import shutil
import sys
 
def build_team_index(groups: dict) -> dict:
    """
    Build lookup: team_slug (lowercase) -> (group, [students], team)
    A team can have multiple participants (e.g. crab2228 has Alessandro and Francesco).
    Disambiguation suffixes (Gabriel2, Davide2 …) are stripped from student names.
    """
    team_to_info = {}
    for group, members in groups.items():
        for student, team in members.items():
            real_student = student.rstrip("23")  # strip disambiguation suffix
            key = team.lower()
            if key not in team_to_info:
                team_to_info[key] = (group, [], team)
            team_to_info[key][1].append(real_student)
    return team_to_info
 
 
def load_groups(json_path: str) -> dict:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)
 
 
def team_slug_from_filename(filename):
    """
    Extract team slug from either:
      adidas11.py                          -> adidas11
      adidas11-adidas11_113987.pdf         -> adidas11
      adidas11-adidas11_113987.mentor.pdf  -> adidas11
    """
    name = filename.split(".")[0]      # drop all extensions
    return name.split("-")[0].lower()  # take part before first dash
 
 
def new_filename(student, team, filename):
    """
    Build destination filename preserving all extensions.
      adidas11.py                         -> Isabel-adidas11.py
      adidas11-adidas11_113987.pdf        -> Isabel-adidas11.pdf
      adidas11-adidas11_113987.mentor.pdf -> Isabel-adidas11.mentor.pdf
    """
    dot_idx = filename.index(".")
    ext = filename[dot_idx:]           # e.g. ".mentor.pdf" or ".py"
    return f"{student}-{team}{ext}"
 
 
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 organize_astropi.py <folder> [--groups groups.json] [--dry-run] [--include-mentor]")
        print("  Organizes .py scripts and .pdf certificates into group subfolders.")
        print("  --groups <file>   path to groups JSON file (default: groups.json)")
        print("  --include-mentor  also copy the mentor .pdf certificates (skipped by default)")
        sys.exit(1)
 
    src_dir = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    include_mentor = "--include-mentor" in sys.argv
 
    # Resolve groups JSON path
    groups_path = "groups.json"
    if "--groups" in sys.argv:
        idx = sys.argv.index("--groups")
        if idx + 1 >= len(sys.argv):
            print("Error: --groups requires a file path argument.")
            sys.exit(1)
        groups_path = sys.argv[idx + 1]
 
    if not os.path.isfile(groups_path):
        print(f"Error: groups file '{groups_path}' not found.")
        print("  Run extract_groups.py first to generate it.")
        sys.exit(1)
 
    TEAM_TO_INFO = build_team_index(load_groups(groups_path))
 
    if not os.path.isdir(src_dir):
        print(f"Error: '{src_dir}' is not a directory.")
        sys.exit(1)
 
    files = [
        f for f in os.listdir(src_dir)
        if os.path.isfile(os.path.join(src_dir, f))
        and (f.endswith(".py") or f.endswith(".pdf"))
        and (include_mentor or not f.endswith(".mentor.pdf"))
    ]
 
    if not files:
        print("No .py or .pdf files found.")
        sys.exit(0)
 
    unmatched = []
 
    for filename in sorted(files):
        slug = team_slug_from_filename(filename)
        if slug not in TEAM_TO_INFO:
            unmatched.append(filename)
            continue
 
        group, students, team = TEAM_TO_INFO[slug]
        subdir = "certificates" if filename.endswith(".pdf") else "scripts"
        dest_dir = os.path.join(src_dir, group, subdir)
        src_path = os.path.join(src_dir, filename)
 
        for student in students:
            new_name = new_filename(student, team, filename)
            dest_path = os.path.join(dest_dir, new_name)
            print(f"{'[DRY RUN] ' if dry_run else ''}{filename}  ->  {group}/{subdir}/{new_name}")
            if not dry_run:
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copy2(src_path, dest_path)
 
    if unmatched:
        print("\nNo match found for:")
        for f in unmatched:
            print(f"  {f}")
 
 
if __name__ == "__main__":
    main()
 
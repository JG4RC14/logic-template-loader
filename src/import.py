#!/usr/bin/env python3
"""Import WAVs from a generated CSV manifest into existing Logic Pro 12.4 tracks.

Requires macOS Accessibility permission for Terminal. The correct project must
already be open in Logic, and the specified anchor TRACK HEADER selected.
UI automation cannot detect duplicate regions or verify import completion.
"""
import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

APPLE_SCRIPT = r'''
on run argv
    set wavPath to item 1 of argv
    set stepsDown to (item 2 of argv) as integer
    tell application "Logic Pro" to activate
    delay 0.8
    tell application "System Events"
        repeat stepsDown times
            key code 125 -- Down Arrow, track header selection
            delay 0.15
        end repeat
        delay 0.3
        key code 36 -- Return: return playhead to bar 1 in tested setup
        delay 0.45
        keystroke "i" using {shift down, command down}
        delay 1.3
        keystroke "g" using {shift down, command down}
        delay 0.5
        keystroke wavPath
        delay 0.5
        key code 36 -- navigate to full path
        delay 0.9
        key code 36 -- import
        delay 2.0
    end tell
end run
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('song', help='Song folder name in generated projects')
    p.add_argument('--root', type=Path, default=REPO_ROOT / 'recordings' / 'Generated_Projects')
    p.add_argument('--start-track', type=int, default=1)
    p.add_argument('--end-track', type=int, default=None)
    p.add_argument('--selected-track', type=int, default=1, help='Track header selected before running (default 1)')
    p.add_argument('--auto', action='store_true', help='No IMPORT or NEXT prompts')
    p.add_argument('--pause', type=float, default=3.0, help='Extra delay between imports in auto mode')
    p.add_argument('--execute', action='store_true', help='Send keystrokes; otherwise preview')
    args = p.parse_args()
    if args.pause < 0:
        p.error('--pause must be >= 0')
    manifest = args.root.expanduser().resolve() / args.song / 'track_manifest.csv'
    if not manifest.is_file():
        p.error(f'Missing manifest: {manifest}')
    with manifest.open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        p.error('Manifest is empty')
    try:
        ordered = all(int(row['logic_track_number']) == i for i, row in enumerate(rows, 1))
    except (KeyError, ValueError) as exc:
        p.error(f'Invalid manifest: {exc}')
    if not ordered:
        p.error('Manifest track numbers must be consecutive, starting at 1')
    end = args.end_track if args.end_track is not None else len(rows)
    if not 1 <= args.selected_track <= args.start_track <= end <= len(rows):
        p.error(f'Require 1 <= selected-track <= start-track <= end-track <= {len(rows)}')
    batch = rows[args.start_track - 1:end]
    for row in batch:
        if not Path(row['import_path']).is_file():
            p.error(f'Missing WAV: {row["import_path"]}')
    print(f'Project: {args.song} | tracks {args.start_track}-{end}')
    for row in batch:
        print(f'  {row["logic_track_number"]}. {row["logic_track_name"]}: {row["wav_filename"]}')
    if not args.execute:
        print('DRY RUN: no keystrokes sent. Add --execute to import.')
        return
    if sys.platform != 'darwin':
        p.error('Logic Pro automation requires macOS')
    print(f'Open {args.song}.logicx in Logic and select track HEADER #{args.selected_track}.')
    print('WARNING: cannot detect existing regions, wrong project, dialogs, or successful placement.')
    if args.auto:
        print('AUTO: starting in 5 seconds; do not interact with Logic until finished.', flush=True)
        time.sleep(5)
    elif input('Type IMPORT to proceed: ').strip() != 'IMPORT':
        print('Cancelled')
        return
    previous = args.selected_track
    for row in batch:
        number = int(row['logic_track_number'])
        print(f'Importing track {number}: {row["logic_track_name"]}', flush=True)
        result = subprocess.run(['osascript', '-e', APPLE_SCRIPT,
                                 str(Path(row['import_path']).resolve()), str(number - previous)],
                                capture_output=True, text=True)
        if result.returncode:
            sys.exit(f'AppleScript error: {result.stderr.strip()}')
        previous = number
        if number != end:
            if args.auto:
                time.sleep(args.pause)
            elif input('Verify track/bar 1, then type NEXT (anything else stops): ').strip() != 'NEXT':
                print('Stopped. Inspect project and save manually.')
                return
    print('Keystrokes sent. Verify regions and save manually in Logic (Command+S).')


if __name__ == '__main__':
    main()

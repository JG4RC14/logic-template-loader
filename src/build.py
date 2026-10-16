#!/usr/bin/env python3
"""Create Logic project shells and CSV manifests from a repository guide.json.

Dry-run by default. WAV staging uses hard links to avoid duplicating audio.
Never destructively edit staged WAVs: hard links share the original data.
"""
import argparse
import csv
import json
import os
import shutil
import sys
import wave
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_guide(path):
    with path.open(encoding='utf-8') as f:
        guide = json.load(f)
    if not isinstance(guide, dict) or not guide:
        raise ValueError('guide.json must be a nonempty object of track names to WAV filenames')
    for name, filename in guide.items():
        if not isinstance(name, str) or not name.strip() or not isinstance(filename, str):
            raise ValueError('Every track name and filename must be a nonempty string')
        if Path(filename).name != filename or not filename.lower().endswith('.wav'):
            raise ValueError(f'Invalid WAV filename for {name}: {filename!r}')
    return list(guide.items())  # JSON insertion order = Logic track order


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=REPO_ROOT / 'recordings', help='Folder containing song subfolders')
    p.add_argument('--guide', type=Path, default=REPO_ROOT / 'guide.json')
    p.add_argument('--template', type=Path, default=None, help='Logic .logicx template (default: ROOT/Souluna_Template.logicx)')
    p.add_argument('--output', type=Path, default=None, help='Default: ROOT/Generated_Projects')
    p.add_argument('--sample-rate', type=int, default=96000)
    p.add_argument('--execute', action='store_true', help='Create projects; otherwise validate only')
    args = p.parse_args()
    root = args.root.expanduser().resolve()
    guide_path = args.guide.expanduser().resolve()
    template = (args.template or root / 'Souluna_Template.logicx').expanduser().resolve()
    output = (args.output or root / 'Generated_Projects').expanduser().resolve()
    try:
        tracks = load_guide(guide_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        p.error(str(exc))
    if not root.is_dir() or not template.exists():
        p.error(f'Missing recordings root or Logic template: {root}, {template}')
    if output in (root, root.parent, template, Path.home()) or output.is_relative_to(template):
        p.error('Unsafe output destination')
    if args.execute and output.exists() and any(output.iterdir()):
        p.error('Output is not empty. Choose a new destination; existing projects will not be overwritten.')
    songs = sorted(d for d in root.iterdir() if d.is_dir() and d != output
                   and d.suffix.lower() != '.logicx' and not d.name.startswith('Generated_')
                   and any(f.is_file() and f.suffix.lower() == '.wav' for f in d.iterdir()))
    if not songs:
        p.error('No song directories containing WAV files found')
    plans, errors = [], []
    for song in songs:
        files = {f.name.casefold(): f for f in song.iterdir() if f.is_file() and f.suffix.lower() == '.wav'}
        resolved = []
        for index, (name, filename) in enumerate(tracks, 1):
            source = files.get(filename.casefold())
            if source is None:
                errors.append(f'{song.name}: missing {filename} for track {index} ({name})')
            resolved.append((index, name, source))
        for source in {source for _, _, source in resolved if source is not None}:
            try:
                with wave.open(str(source), 'rb') as wav:
                    rate = wav.getframerate()
                if rate != args.sample_rate:
                    errors.append(f'{song.name}/{source.name}: {rate} Hz, expected {args.sample_rate} Hz')
            except (wave.Error, EOFError, OSError) as exc:
                errors.append(f'{source}: cannot inspect WAV: {exc}')
        plans.append((song, resolved))
    print(f'Guide: {guide_path}\nTemplate: {template}\nSongs: {len(plans)}\nTracks/song: {len(tracks)}\nOutput: {output}')
    for song, rows in plans:
        print(f'  {song.name}: {sum(src is not None for _, _, src in rows)}/{len(rows)}')
    if errors:
        for error in errors:
            print('ERROR:', error, file=sys.stderr)
        sys.exit(1)
    if not args.execute:
        print('DRY RUN: nothing written. Add --execute to build.')
        return
    ancestor = output
    while not ancestor.exists():
        ancestor = ancestor.parent
    for _, rows in plans:
        for _, _, source in rows:
            if source.stat().st_dev != ancestor.stat().st_dev:
                p.error(f'Hard linking requires same filesystem: {source}')
    output.mkdir(parents=True, exist_ok=True)
    for song, rows in plans:
        dest = output / song.name
        dest.mkdir()
        project = dest / f'{song.name}.logicx'
        if template.is_dir():
            shutil.copytree(template, project)
        else:
            shutil.copy2(template, project)
        audio_dir = dest / 'Audio_To_Import'
        audio_dir.mkdir()
        for source in {source for _, _, source in rows}:
            os.link(source, audio_dir / source.name)
        with (dest / 'track_manifest.csv').open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['logic_track_number', 'logic_track_name', 'wav_filename', 'import_path'])
            for number, name, source in rows:
                writer.writerow([number, name, source.name, str(audio_dir / source.name)])
        with (dest / 'track_manifest.json').open('w', encoding='utf-8') as f:
            json.dump([{'track': number, 'name': name, 'wav': source.name}
                       for number, name, source in rows], f, indent=2)
        print(f'Created {project}')
    print('Audio staged using hard links; import into Logic separately. Do not destructively edit staged WAVs.')


if __name__ == '__main__':
    main()

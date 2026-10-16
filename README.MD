# Logic Session Automator 

#### *NOTE : You can download this repo as a zip, and place wherever you want to store your project, in case you don't know how to clone repositories, or want to re-use and keep files.*

A Python-based automation tool that helps create and populate Logic Pro projects using multitrack WAV recordings.

Originally built to simplify my own band's recording workflow, this project automates repetitive session setup while preserving the plugins, routing, and channel configurations from an existing Logic Pro template.

## Requirements

- macOS with Logic Pro installed (tested with Logic Pro 12.4)
- Python 3.10+
- A Logic Pro project template
- Multitrack WAV recordings

**Stock Python!** No third-party dependencies or `pip install` required.


## 1. Configure Your Template

Make sure you have a Logic Pro template named `template.logicx` in the root of your recordings directory, as expected by your builder configuration.

Preferably, your template should already contain the tracks, plugins, routing, and initial mixing settings you want to use for every song.

Next, configure `guide.json` at the root of the repository. This file determines which WAV files belong to each Logic track.

Example:

```json
{
    "KICK": "12BDRUM.WAV",
    "SNARE": "10SNARE.WAV",
    "BASS": "07BASS.WAV",
    "LEAD-GUITAR": "04LEAD.WAV",
    "LEAD-VOCAL": "01VOCAL.WAV"
}
```

**Important:** Make sure the order of the tracks in `guide.json` matches the order of the tracks in your Logic template. Filenames must also match the recordings you're importing.

## 2. Organize Your Recordings

Place your recordings inside the `recordings` directory, with each song in its own folder.

For example:

```text
logic-session-automator/
├── guide.json
├── template.logicx
├── src/
│   ├── build.py
│   └── import.py
└── recordings/
    ├── SONG 1/
    │   ├── Vocal.WAV
    │   └── Guitar.WAV
    └── SONG 2/
        ├── Vocal.WAV
        └── Guitar.WAV
```

Each song folder should contain the WAV files referenced in `guide.json`.

## 3. Generate Your Logic Projects

Open Terminal, navigate to the repository, and run:

```bash
python3 src/build.py
```

This performs a validation run without creating files.

Once everything looks good, execute the builder:

```bash
python3 src/build.py --execute
```

The script generates a project folder for each song, including a copy of your Logic template, staged audio files, and a CSV manifest mapping each recording to its destination track.

## 4. Import Your Audio into Logic Pro

Before running the importer, open the generated `.logicx` project for the song you want to import.

Make sure:

- The correct Logic project is open.
- The first track in your template is selected.
- No additional dialogs are open.
- Terminal has permission to control Logic Pro through macOS Accessibility settings.

### Option A: Import an Entire Song

To import every track automatically:

```bash
python3 src/import.py "SONG 1" --auto --execute
```

Replace `SONG 1` with the exact folder name of your recording.

### Option B: Import Individual Tracks

To import only a specific track:

```bash
python3 src/import.py "SONG 1" --start-track 1 --end-track 1 --execute
```

You can also import a range of tracks:

```bash
python3 src/import.py "SONG 1" --start-track 2 --end-track 5 --execute
```

The importer uses macOS keyboard automation to navigate Logic Pro, import the WAV recordings, and position them at the beginning of the project.

**Important:** The importer does not currently detect audio regions that have already been imported. Running it multiple times on the same tracks may create duplicates.

## Notes & Precautions

- **Sample Rate:** Make sure your Logic Pro project supports the sample rate of your WAV files. The original workflow was developed using 96 kHz recordings.
- **Backups:** Always create backups of your original recordings and Logic template before running the automation.
- **Track Order:** Your `guide.json` must match the order of tracks in your Logic template.
- **File Naming:** WAV filenames must match the names referenced in `guide.json`.
- **macOS Permissions:** Terminal may request Accessibility permissions to control Logic Pro.
- **Automation:** Avoid using the keyboard or mouse while an automated import is running.
- **Verification:** Always inspect the imported regions and save your project after confirming everything is correct.
- **Storage:** The builder may use hard links to avoid duplicating large audio files. Hard-linked files share the same underlying data, so destructive modifications can affect the originals.

## Future Improvements

This project is still evolving. Potential improvements include:

- Automatic project opening and saving
- Better import validation and error handling
- A configurable command-line interface
- Support for additional recording workflows
- AI-assisted audio analysis and mixing

## Why I Built This

As both a software developer and musician, I wanted to find a way to spend less time preparing recording sessions and more time actually making music.

What started as a repetitive process of creating projects, importing recordings, and organizing tracks became an opportunity to build a reusable automation tool with Python.

This project is an example of how programming can solve practical problems outside of a traditional software engineering environment.
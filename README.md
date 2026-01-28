# Desktop Organizer AI Agent (macOS)

Automatically organizes your Mac desktop by classifying files into folders and using Claude's vision to intelligently rename screenshots based on their content.

## Features

- **File Classification**: Sorts files into categories (Documents, Images, Videos, Code, etc.)
- **Smart Screenshot Renaming**: Analyzes screenshots and renames them descriptively (e.g., `Code-Snippet-Python.png`)
- **Safe Mode**: Dry-run option to preview changes

## File Categories

| Category | Extensions |
|----------|-----------|
| Documents | .pdf, .doc, .docx, .txt, .xls, .xlsx, .ppt, .pptx, .csv, .md, .pages, .numbers, .keynote |
| Images | .jpg, .jpeg, .png, .gif, .svg, .webp, .heic, .psd |
| Videos | .mp4, .avi, .mkv, .mov, .webm |
| Audio | .mp3, .wav, .flac, .aac, .m4a |
| Archives | .zip, .rar, .7z, .tar, .gz, .dmg |
| Code | .py, .js, .ts, .html, .css, .java, .go, .tf, .yaml, .json, .sh |
| Shortcuts | .webloc |
| Other | Everything else |

## Setup

```bash
# Install dependency
pip install anthropic

# Set your API key (add to ~/.zshrc for persistence)
export ANTHROPIC_API_KEY='your-key-here'
```

## Usage

```bash
# Preview changes first (recommended!)
./run_organizer.sh --dry-run

# Run for real
./run_organizer.sh
```

Or directly:
```bash
python desktop_organizer.py --dry-run
python desktop_organizer.py
```

## Screenshot Renaming

Detects macOS screenshots like:
- `Screenshot 2024-01-15 at 10.30.45 AM.png`

And renames them based on content:
- `Code-Snippet-Python.png`
- `Website-Login-Page.png`
- `Terminal-Command-Output.png`

## Logs

Actions are logged to `desktop_organizer.log` in the current directory.

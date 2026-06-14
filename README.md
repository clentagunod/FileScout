# FileScout — Automatic File Organizer

FileScout monitors a folder and automatically sorts files into subfolders based on type, renaming them with a date prefix.

---

## Project Structure

```
filescout/
├── main.py              ← Entry point (run this)
├── settings.json        ← All configuration (edit here)
│
├── core/
│   ├── config.py        ← Loads and validates settings.json
│   ├── organizer.py     ← File classification + move logic
│   ├── watcher.py       ← Polls directory for new files
│   └── shell.py         ← Interactive terminal interface
│
└── utils/
    └── logger.py        ← Colored console + file logging
```

---

## Requirements

- Python 3.10+ (uses `str | None` union syntax)
- No third-party packages required — stdlib only

---

## How to Run

### Interactive mode (recommended)
```
python main.py
```

### Auto-start watching a folder
```
python main.py start filescout "C:/Users/YourName/Downloads"
```

### Shell commands (once inside FileScout)

| Command | Description |
|---|---|
| `start filescout <path>` | Start watching a directory |
| `scan filescout <path>` | One-time scan and organize |
| `status` | Show watcher status |
| `rules` | List active sorting rules |
| `stop` | Stop the active watcher |
| `help` | Show all commands |
| `exit` | Quit FileScout |

---

## Configuration — settings.json

All behavior is controlled via `settings.json`. Key sections:

### `app`
```json
{
  "name": "FileScout",
  "poll_interval_seconds": 3,
  "log_to_file": true
}
```
Change `name` to rename the app and its shell prompt.

### `rename`
```json
{
  "enabled": true,
  "date_format": "%Y-%m-%d",
  "separator": "_",
  "preserve_original_name": true
}
```
Files are renamed like: `2025-06-14_report.pdf`

### `rules`
Add, remove, or toggle rules per file type:
```json
{
  "name": "Code",
  "extensions": [".py", ".js", ".html"],
  "destination_folder": "Code",
  "enabled": false
}
```
Set `"enabled": false` to disable a rule without deleting it.

### `duplicate_handling`
```json
{
  "strategy": "rename",
  "suffix_format": "({n})"
}
```
Strategies: `rename` (default), `skip`, `overwrite`

### `ignore`
```json
{
  "hidden_files": true,
  "temp_extensions": [".tmp", ".part", ".crdownload"],
  "filenames": [".DS_Store", "Thumbs.db"]
}
```

---

## Log File

FileScout writes a `filescout.log` in the project folder (configurable). Each run appends to it.
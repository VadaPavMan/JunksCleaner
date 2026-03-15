# 🧹 Junks Cleaner

> A lightweight, modern system cleaning utility for Windows — built with Python and CustomTkinter.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows%2011-0078D4?style=flat-square&logo=windows)
![Status](https://img.shields.io/badge/Status-Alpha%20v0.1.0-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## What is Junks Cleaner?

Junks Cleaner is an open-source system cleaning tool that helps you reclaim disk space and keep your Windows machine clean. It scans and safely removes temporary files, browser caches, recycle bin contents, and other junk left behind by the OS and applications.

Built with a **functionality-first philosophy** — every feature is fully working before the next one is added. No half-baked features, no bloat.

---

## Features

### ✅ Phase 1 — Temp File Cleaner (Current)
- Scans all standard Windows temp locations
- Displays found files in a sortable, scrollable table
- Per-file checkbox selection — choose exactly what to delete
- Background scanning — UI never freezes
- Confirmation dialog before any deletion
- Handles locked/in-use files gracefully

### 🔜 Coming Soon
| Phase | Feature |
|-------|---------|
| 2 | Browser Cache Cleaner (Chrome, Edge, Firefox, Brave) |
| 3 | Recycle Bin Cleaner |
| 4 | Windows Update Cache |
| 5 | Duplicate File Finder |
| 6 | Settings, themes, exclusion lists |
| 7 | Linux support |

---

## Screenshots

> *(Screenshots will be added after v0.1.0 release)*

---

## Requirements

- Python 3.10 or higher
- Windows 10 / 11
- pip packages listed in `requirements.txt`

---

## Installation

**1. Clone the repository**
```bash
git clone https://github.com/VadaPavMan/JunksCleaner.git
cd JunksCleaner
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Run the setup script (first time only)**
```bash
python fix_setup.py
```

**4. Launch the app**
```bash
python main.py
```

> **Note:** Some cleaning targets (e.g. `C:\Windows\Temp`) require administrator privileges. Right-click your terminal and choose "Run as administrator" for full access.

---

## Project Structure

```
JunksCleaner/
├── main.py                  ← Entry point
├── requirements.txt
├── fix_setup.py             ← First-time setup helper
│
├── app/                     ← App lifecycle and global state
│   ├── app.py               ← CTk window setup
│   └── state.py             ← Global state singleton
│
├── ui/                      ← All UI code
│   ├── main_window.py       ← Root layout
│   ├── sidebar.py           ← Navigation panel
│   ├── components/          ← Reusable widgets
│   │   ├── file_table.py
│   │   ├── progress_bar.py
│   │   ├── confirm_dialog.py
│   │   └── status_bar.py
│   └── pages/               ← One file per feature
│       ├── temp_cleaner_page.py
│       ├── browser_cleaner_page.py
│       └── ...
│
├── core/                    ← Cleaning logic (no UI imports)
│   ├── base_cleaner.py      ← Abstract base class
│   └── temp_cleaner.py
│
├── os_platform/             ← OS-specific paths and APIs
│   ├── detector.py
│   ├── windows/
│   └── linux/
│
├── utils/                   ← Shared helpers
│   ├── logger.py
│   ├── thread_worker.py
│   └── file_utils.py
│
└── config/                  ← Settings and defaults
    ├── settings.py
    └── default_config.json
```

---

## Architecture

The project follows a strict **layered architecture**:

```
ui/  →  core/  →  os_platform/  →  utils/
```

- `ui/` reads from `app/state.py` to display data
- `core/` writes results to `app/state.py` after operations
- `core/` **never** imports from `ui/` — cleaning logic is fully independent
- `os_platform/` isolates all OS-specific code so adding Linux support only touches that layer
- Every long-running operation runs on a background thread via `utils/thread_worker.py`

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request.

**Good first issues:**
- Adding a new browser to the browser cache cleaner
- Adding Linux temp paths in `os_platform/linux/paths.py`
- UI improvements and theming

---

## Development Setup

```bash
git clone https://github.com/VadaPavMan/JunksCleaner.git
cd JunksCleaner
pip install -r requirements.txt
python main.py
```

To run with verbose logging, set `log_level` to `DEBUG` in `config/default_config.json`. Logs are written to `logs/junkscleaner.log`.

---

## Author

**Harsh Rajbhar** — [@VadaPavMan](https://github.com/VadaPavMan)

> Built as a learning project to sharpen Python skills while building something genuinely useful.
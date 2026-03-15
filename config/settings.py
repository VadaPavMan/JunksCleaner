"""
config/settings.py

Loads settings from default_config.json.
Provides a simple get/set/save interface used across the app.

Uses __file__-relative paths so this works regardless of which
directory the user runs main.py from — including OneDrive paths.
"""

import json
import os

# Paths resolved relative to THIS file, not the working directory
_CONFIG_DIR  = os.path.dirname(os.path.abspath(__file__))
_CONFIG_FILE = os.path.join(_CONFIG_DIR, "default_config.json")

# Built-in defaults — used if JSON is missing or corrupt
_DEFAULTS = {
    "appearance_mode": "dark",
    "color_theme":     "blue",
    "window_width":    960,
    "window_height":   620,
    "log_level":       "DEBUG",
}


class Settings:
    """
    Simple key-value settings store backed by a JSON file.

    Usage:
        from config.settings import settings
        settings.get("appearance_mode", "dark")
        settings.set("window_width", 1024)
        settings.save()
    """

    def __init__(self):
        self._data: dict = dict(_DEFAULTS)
        self._load()

    def _load(self):
        """
        Load settings from JSON. Falls back to built-in defaults silently.
        Does NOT import the logger here — settings loads very early,
        before logging is configured, so print() is used only.
        """
        if not os.path.exists(_CONFIG_FILE):
            print(f"[Settings] Config not found at {_CONFIG_FILE}, using defaults")
            return
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            self._data.update(loaded)
        except json.JSONDecodeError as e:
            print(f"[Settings] Bad JSON in config file: {e} — using defaults")
        except OSError as e:
            print(f"[Settings] Cannot read config file: {e} — using defaults")

    def save(self):
        """Write current settings back to the JSON file."""
        try:
            with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except OSError as e:
            print(f"[Settings] Cannot save config: {e}")

    def get(self, key: str, default=None):
        """Get a setting value. Returns default if key not found."""
        return self._data.get(key, default)

    def set(self, key: str, value):
        """Set a setting value in memory. Call save() to persist it."""
        self._data[key] = value

    def all(self) -> dict:
        """Return a copy of all settings."""
        return dict(self._data)


# Module-level singleton
# Import this everywhere:   from config.settings import settings
settings = Settings()
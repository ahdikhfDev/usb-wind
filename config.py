import os
import sys
import json
import platform
from pathlib import Path
from typing import Optional
from datetime import datetime


def get_os() -> str:
    return platform.system().lower()


def get_config_dir() -> Path:
    if get_os() == "windows":
        config_dir = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "USBBackupAgent"
    elif get_os() == "darwin":
        config_dir = Path.home() / "Library" / "Application Support" / "USBBackupAgent"
    else:
        config_dir = Path.home() / ".config" / "usb_backup_agent"
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_home_folders() -> list[Path]:
    home = Path.home()
    folders = []
    
    for name in ["Documents", "Desktop", "Downloads", "Pictures"]:
        folder = home / name
        if folder.exists():
            folders.append(folder)
    
    return folders


class Config:
    DEFAULT_CONFIG = {
        "marker_file": "_usb_backup_marker.txt",
        "lock_file": "_backup_running.lock",
        "check_interval": 60,
        "backup_dir_name": "hasil_backup",
        "source_folders": [str(f) for f in get_home_folders()],
        "target_extensions": {
            ".jpg": 5, ".jpeg": 5, ".png": 5,
            ".gif": 5, ".webp": 5,
            ".docx": 10, ".xlsx": 10, ".pptx": 10,
            ".pdf": 15,
            ".txt": 5, ".csv": 5,
        },
        "enable_compression": False,
        "enable_incremental": True,
        "incremental_method": "mtime",
        "conflict_resolution": "skip",
        "exclude_patterns": [
            "node_modules",
            ".git",
            "__pycache__",
            "*.tmp",
            "*.temp",
            "Thumbs.db",
            ".DS_Store",
        ],
        "min_free_space_mb": 100,
        "dry_run": False,
        "log_level": "INFO",
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = get_config_dir() / "config.json"
        
        self._config = {}
        self.load()
    
    def load(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self._config = {**self.DEFAULT_CONFIG, **loaded}
            except (json.JSONDecodeError, IOError):
                self._config = self.DEFAULT_CONFIG.copy()
        else:
            self._config = self.DEFAULT_CONFIG.copy()
    
    def save(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
            return False
    
    def get(self, key: str, default=None):
        return self._config.get(key, default)
    
    def set(self, key: str, value):
        self._config[key] = value
    
    def __getitem__(self, key: str):
        return self._config[key]
    
    def __setitem__(self, key: str, value):
        self._config[key] = value
    
    def to_dict(self) -> dict:
        return self._config.copy()
    
    def reset_to_default(self):
        self._config = self.DEFAULT_CONFIG.copy()
        self.save()


def load_config(config_path: Optional[Path] = None) -> Config:
    return Config(config_path)


def save_config(config: Config) -> bool:
    return config.save()

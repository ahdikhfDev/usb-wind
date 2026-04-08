import os
import sys
import json
import platform
from pathlib import Path
from typing import Optional


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


def get_usb_path() -> Optional[Path]:
    script_dir = Path(__file__).parent
    if get_os() == "windows":
        for letter in "EFGHIJKLMNOPQRSTUVWXYZ":
            drive = Path(f"{letter}:")
            if (drive / "_usb_backup_marker.txt").exists():
                return drive
    else:
        volumes = Path("/Volumes")
        if volumes.exists():
            for vol in volumes.iterdir():
                if vol.name not in ["Macintosh HD"]:
                    marker = vol / "_usb_backup_marker.txt"
                    if marker.exists():
                        return vol
    return None


class Config:
    DEFAULT_CONFIG = {
        "marker_file": "_usb_backup_marker.txt",
        "lock_file": "_backup_running.lock",
        "backup_dir_name": "hasil_backup",
        
        "source_folders": [
            str(Path.home() / "Documents"),
            str(Path.home() / "Desktop"),
            str(Path.home() / "Downloads"),
            str(Path.home() / "Pictures"),
        ],
        
        "target_extensions": {
            ".jpg": 50, ".jpeg": 50, ".png": 50, ".gif": 50, ".webp": 50,
            ".heic": 50, ".heif": 50, ".raw": 50, ".bmp": 50, ".svg": 50,
            ".tiff": 50, ".tif": 50, ".ico": 50,
            
            ".mp4": 50, ".mov": 50, ".avi": 50, ".mkv": 50, ".webm": 50,
            ".m4v": 50, ".flv": 50, ".wmv": 50, ".mpeg": 50, ".mpg": 50,
            
            ".mp3": 50, ".wav": 50, ".m4a": 50, ".flac": 50, ".aac": 50,
            ".ogg": 50, ".wma": 50, ".opus": 50,
            
            ".pdf": 50, ".doc": 50, ".docx": 50, ".xls": 50, ".xlsx": 50,
            ".ppt": 50, ".pptx": 50, ".txt": 50, ".rtf": 50, ".csv": 50,
            ".odt": 50, ".ods": 50, ".odp": 50, ".pages": 50, ".numbers": 50,
            ".key": 50,
            
            ".py": 5, ".js": 5, ".ts": 5, ".tsx": 5, ".jsx": 5,
            ".html": 5, ".css": 5, ".scss": 5, ".sass": 5,
            ".json": 5, ".xml": 5, ".yaml": 5, ".yml": 5,
            ".md": 5, ".sh": 5, ".bat": 5, ".ps1": 5,
            ".c": 5, ".cpp": 5, ".h": 5, ".java": 5,
            ".swift": 5, ".kt": 5, ".go": 5, ".rs": 5,
            ".rb": 5, ".php": 5, ".sql": 5,
            
            ".zip": 50, ".rar": 50, ".7z": 50, ".tar": 50, ".gz": 50,
            ".epub": 50, ".srt": 50, ".vtt": 50,
        },
        
        "max_file_size_mb": 50,
        
        "exclude_patterns": [
            "node_modules", ".git", "__pycache__", ".venv", "venv",
            "*.tmp", "*.temp", "*.cache", "*.log",
            "Thumbs.db", ".DS_Store", "desktop.ini",
            "$RECYCLE.BIN", ".Spotlight-V100", ".Trashes",
            ".fseventsd", ".TemporaryItems",
        ],
        
        "exclude_folder_names": [
            "node_modules", ".git", "__pycache__", ".venv", "venv",
            ".npm", ".yarn", ".cache", "Library", ".android",
            "Android", ".gradle", "build", "dist", ".next",
        ],
        
        "enable_compression": False,
        "enable_incremental": True,
        "conflict_resolution": "skip",
        
        "usb_volume_name": "Untitled 1",
        
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
        except IOError:
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

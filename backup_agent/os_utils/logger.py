import os
import sys
import platform
import logging
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler


def get_os() -> str:
    return platform.system().lower()


def get_log_dir() -> Path:
    if get_os() == "windows":
        log_dir = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "USBBackupAgent" / "logs"
    elif get_os() == "darwin":
        log_dir = Path.home() / "Library" / "Logs" / "USBBackupAgent"
    else:
        log_dir = Path.home() / ".local" / "share" / "usb_backup_agent" / "logs"
    
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logging(name: str = "usb_backup", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if logger.handlers:
        return logger
    
    log_dir = get_log_dir()
    log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=7,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "usb_backup") -> logging.Logger:
    return logging.getLogger(name)


def cleanup_old_logs(days: int = 30):
    log_dir = get_log_dir()
    if not log_dir.exists():
        return
    
    now = datetime.now().timestamp()
    cutoff = now - (days * 86400)
    
    for log_file in log_dir.glob("*.log*"):
        try:
            if log_file.stat().st_mtime < cutoff:
                log_file.unlink()
        except Exception:
            pass

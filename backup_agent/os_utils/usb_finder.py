import os
import sys
import platform
import subprocess
import re
from pathlib import Path
from typing import Optional


def get_os() -> str:
    return platform.system().lower()


def get_username() -> str:
    if get_os() == "windows":
        return os.environ.get("USERNAME", "user")
    return os.environ.get("USER", "user")


def get_script_dir() -> Path:
    return Path(__file__).parent.parent


def find_usb_by_name(volume_name: str = "Untitled 1") -> Optional[Path]:
    if get_os() == "windows":
        return _find_usb_windows_by_name(volume_name)
    elif get_os() == "darwin":
        return _find_usb_macos_by_name(volume_name)
    else:
        return _find_usb_linux_by_name(volume_name)


def _find_usb_windows_by_name(volume_name: str) -> Optional[Path]:
    try:
        result = subprocess.run(
            ["wmic", "volume", "get", "DriveLetter,Label"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split("\n"):
            if volume_name.lower() in line.lower():
                match = re.search(r"([A-Z]:)\\?", line)
                if match:
                    return Path(match.group(1))
    except Exception:
        pass
    
    for letter in "DEFGHIJKLMNOPQRSTUVWXYZ":
        drive = Path(f"{letter}:")
        if drive.exists():
            try:
                label = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", f"(Get-Volume -DriveLetter '{letter}').FileSystemLabel"],
                    capture_output=True, text=True, timeout=5
                ).stdout.strip()
                if volume_name.lower() in label.lower():
                    return drive
            except Exception:
                continue
    
    return None


def _find_usb_macos_by_name(volume_name: str) -> Optional[Path]:
    volumes = Path("/Volumes")
    if not volumes.exists():
        return None
    
    for vol in volumes.iterdir():
        if vol.name == volume_name:
            return vol
    
    return None


def _find_usb_linux_by_name(volume_name: str) -> Optional[Path]:
    username = get_username()
    paths_to_check = [
        Path(f"/media/{username}/{volume_name}"),
        Path(f"/run/media/{username}/{volume_name}"),
        Path(f"/mnt/{volume_name}"),
        Path(f"/media/{volume_name}"),
    ]
    
    for path in paths_to_check:
        if path.exists() and path.is_dir():
            return path
    
    return None


def find_usb(marker_file: str = "_usb_backup_marker.txt") -> Optional[Path]:
    script_dir = get_script_dir()
    
    if get_os() == "windows":
        for letter in "DEFGHIJKLMNOPQRSTUVWXYZ":
            drive = Path(f"{letter}:")
            if (drive / marker_file).exists():
                return drive
    else:
        volumes = Path("/Volumes")
        if volumes.exists():
            for vol in volumes.iterdir():
                if vol.name not in ["Macintosh HD"]:
                    marker = vol / marker_file
                    if marker.exists():
                        return vol
    
    fallback_name = "Untitled 1"
    usb_by_name = find_usb_by_name(fallback_name)
    if usb_by_name:
        return usb_by_name
    
    return None


def find_first_removable_usb() -> Optional[Path]:
    if get_os() == "darwin":
        return _find_first_removable_macos()
    elif get_os() == "windows":
        return _find_first_removable_windows()
    else:
        return _find_first_removable_linux()


def _find_first_removable_macos() -> Optional[Path]:
    volumes = Path("/Volumes")
    if not volumes.exists():
        return None
    
    for vol in volumes.iterdir():
        if vol.name in ["Macintosh HD"]:
            continue
        
        try:
            result = subprocess.run(
                ["diskutil", "info", str(vol)],
                capture_output=True, text=True, timeout=5
            )
            if "External" in result.stdout or "Removable" in result.stdout:
                if "Internal" not in result.stdout:
                    return vol
        except Exception:
            continue
    
    return None


def _find_first_removable_windows() -> Optional[Path]:
    try:
        result = subprocess.run(
            ["wmic", "diskdrive", "get", "Caption,InterfaceType"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split("\n"):
            if "USB" in line or "Removable" in line:
                match = re.search(r"([A-Z]:)", line)
                if match:
                    drive = Path(f"{match.group(1)}:")
                    if drive.exists():
                        return drive
    except Exception:
        pass
    
    return None


def _find_first_removable_linux() -> Optional[Path]:
    username = get_username()
    paths = [
        Path(f"/media/{username}"),
        Path(f"/run/media/{username}"),
        Path("/mnt"),
        Path("/media"),
    ]
    
    for base in paths:
        if not base.exists():
            continue
        try:
            for vol in base.iterdir():
                if vol.is_dir():
                    return vol
        except PermissionError:
            continue
    
    return None


def get_usb_info(usb_path: Path) -> dict:
    info = {
        "path": str(usb_path),
        "name": usb_path.name,
        "total_space": 0,
        "free_space": 0,
        "used_space": 0,
    }
    
    try:
        if get_os() == "darwin":
            total, free = _get_space_macos(usb_path)
            info["total_space"] = total
            info["free_space"] = free
            info["used_space"] = total - free
        elif get_os() == "windows":
            total, free = _get_space_windows(usb_path)
            info["total_space"] = total
            info["free_space"] = free
            info["used_space"] = total - free
        else:
            stat = os.statvfs(usb_path)
            info["total_space"] = stat.f_blocks * stat.f_frsize
            info["free_space"] = stat.f_bavail * stat.f_frsize
            info["used_space"] = (stat.f_blocks - stat.f_bfree) * stat.f_frsize
    except Exception:
        pass
    
    return info


def _get_space_macos(path: Path) -> tuple[int, int]:
    try:
        result = subprocess.run(
            ["df", "-k", str(path)],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 2:
            parts = lines[1].split()
            if len(parts) >= 4:
                total_kb = int(parts[1]) * 1024
                free_kb = int(parts[3]) * 1024
                return total_kb, free_kb
    except Exception:
        pass
    return 0, 0


def _get_space_windows(path: Path) -> tuple[int, int]:
    try:
        drive = str(path).rstrip("/\\")
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-PSDrive -Name '{drive[0]}' | Select-Object Used,Free | Format-List)"],
            capture_output=True, text=True, timeout=5
        )
        total = free = 0
        for line in result.stdout.split("\n"):
            line = line.strip()
            if "Used" in line:
                val = int(re.search(r'\d+', line.replace(",", "")))
                total = val
            elif "Free" in line:
                val = int(re.search(r'\d+', line.replace(",", "")))
                free = val
        return total, free
    except Exception:
        return 0, 0


def format_bytes(bytes_val: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f}PB"

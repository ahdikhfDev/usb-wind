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


class USBFinder:
    def __init__(self, marker_file: str = "_usb_backup_marker.txt"):
        self.marker_file = marker_file
        self._cache = {}

    def find(self) -> list[Path]:
        os_type = get_os()
        if os_type == "windows":
            return self._find_windows()
        elif os_type == "darwin":
            return self._find_macos()
        else:
            return self._find_linux()

    def _find_windows(self) -> list[Path]:
        drives = []
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = Path(f"{letter}:/")
            if self._is_valid_usb(drive):
                drives.append(drive)
        return drives

    def _find_macos(self) -> list[Path]:
        volumes = Path("/Volumes")
        if not volumes.exists():
            return []
        
        drives = []
        for vol in volumes.iterdir():
            if self._is_valid_usb(vol) and vol.name not in ["Macintosh HD"]:
                drives.append(vol)
        
        media = Path("/media")
        if media.exists():
            try:
                for user in media.iterdir():
                    if user.is_dir():
                        for vol in user.iterdir():
                            if self._is_valid_usb(vol):
                                drives.append(vol)
            except PermissionError:
                pass
        
        return drives

    def _find_linux(self) -> list[Path]:
        drives = []
        username = get_username()
        
        paths_to_check = [
            Path(f"/media/{username}"),
            Path(f"/run/media/{username}"),
            Path("/mnt"),
            Path("/media"),
        ]
        
        for base_path in paths_to_check:
            if not base_path.exists():
                continue
            try:
                if base_path == Path("/media") or base_path == Path("/mnt"):
                    for vol in base_path.iterdir():
                        if vol.is_dir() and self._is_valid_usb(vol):
                            drives.append(vol)
                else:
                    for vol in base_path.iterdir():
                        if vol.is_dir() and self._is_valid_usb(vol):
                            drives.append(vol)
            except PermissionError:
                continue
        
        return drives

    def _is_valid_usb(self, path: Path) -> bool:
        if not path.exists() or not path.is_dir():
            return False
        
        marker = path / self.marker_file
        if marker.exists():
            return True
        
        return self._is_removable_drive(path)

    def _is_removable_drive(self, path: Path) -> bool:
        os_type = get_os()
        
        if os_type == "windows":
            return self._is_removable_windows(path)
        elif os_type == "darwin":
            return self._is_removable_macos(path)
        else:
            return self._is_removable_linux(path)

    def _is_removable_windows(self, path: Path) -> bool:
        try:
            drive_letter = str(path).rstrip("/\\").replace(":", "")
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", 
                 f"(Get-Volume -DriveLetter '{drive_letter[0]}' | Select-Object -ExpandProperty DriveType)"],
                capture_output=True, text=True, timeout=5
            )
            return "Removable" in result.stdout
        except Exception:
            return False

    def _is_removable_macos(self, path: Path) -> bool:
        try:
            vol_name = path.name
            result = subprocess.run(
                ["diskutil", "info", str(path)],
                capture_output=True, text=True, timeout=5
            )
            if "Removable" in result.stdout or "External" in result.stdout:
                return True
            if "Removable" not in result.stdout and "Internal" in result.stdout:
                return False
            return vol_name != "Macintosh HD"
        except Exception:
            return False

    def _is_removable_linux(self, path: Path) -> bool:
        try:
            for child in path.iterdir():
                if child.name.startswith("sd"):
                    device = Path("/sys/block") / child.name
                    if device.exists():
                        rem_file = device / "removable"
                        if rem_file.exists():
                            return rem_file.read_text().strip() == "1"
            return True
        except Exception:
            return True

    def get_info(self, usb_path: Path) -> dict:
        info = {
            "path": str(usb_path),
            "name": usb_path.name,
            "total_space": 0,
            "free_space": 0,
            "is_removable": self._is_removable_drive(usb_path),
        }
        
        try:
            if get_os() == "windows":
                total, free = self._get_space_windows(usb_path)
                info["total_space"] = total
                info["free_space"] = free
            elif get_os() == "darwin":
                total, free = self._get_space_macos(usb_path)
                info["total_space"] = total
                info["free_space"] = free
            else:
                stat = os.statvfs(usb_path)
                info["total_space"] = stat.f_blocks * stat.f_frsize
                info["free_space"] = stat.f_bavail * stat.f_frsize
        except Exception:
            pass
        
        return info

    def _get_space_windows(self, path: Path) -> tuple[int, int]:
        try:
            drive = str(path).rstrip("/\\")
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"(Get-PSDrive -Name '{drive[0]}' | Select-Object -ExpandProperty Used),(Get-PSDrive -Name '{drive[0]}' | Select-Object -ExpandProperty Free)"],
                capture_output=True, text=True, timeout=5
            )
            lines = result.stdout.strip().split("\n")
            if len(lines) >= 2:
                used = int(lines[0].strip()) if lines[0].strip().isdigit() else 0
                free = int(lines[1].strip()) if lines[1].strip().isdigit() else 0
                return used + free, free
        except Exception:
            pass
        return 0, 0

    def _get_space_macos(self, path: Path) -> tuple[int, int]:
        try:
            result = subprocess.run(
                ["diskutil", "info", str(path)],
                capture_output=True, text=True, timeout=5
            )
            total = free = 0
            for line in result.stdout.split("\n"):
                if "Total Size" in line:
                    match = re.search(r"\((\d+)\)", line)
                    if match:
                        total = int(match.group(1))
                elif "Volume Free Space" in line:
                    match = re.search(r"\((\d+)\)", line)
                    if match:
                        free = int(match.group(1))
            return total, free
        except Exception:
            return 0, 0


def find_usb_drives(marker_file: str = "_usb_backup_marker.txt") -> list[Path]:
    finder = USBFinder(marker_file)
    return finder.find()


def get_usb_info(usb_path: Path, marker_file: str = "_usb_backup_marker.txt") -> dict:
    finder = USBFinder(marker_file)
    return finder.get_info(usb_path)

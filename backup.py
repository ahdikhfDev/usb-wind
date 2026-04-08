#!/usr/bin/env python3
import os
import sys
import shutil
import hashlib
import platform
import time
import fnmatch
import zipfile
import gzip
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import Config, load_config
from os_utils import find_usb_drives, get_usb_info, notify, notify_progress, enable_autostart, get_logger, setup_logging


def get_os() -> str:
    return platform.system().lower()


class BackupAgent:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or load_config()
        self.logger = setup_logging()
        self._running = False
    
    def find_usb(self):
        marker = self.config.get("marker_file", "_usb_backup_marker.txt")
        drives = find_usb_drives(marker)
        return drives[0] if drives else None
    
    def is_locked(self, usb: Path) -> bool:
        lock_file = usb / self.config.get("lock_file", "_backup_running.lock")
        return lock_file.exists()
    
    def set_lock(self, usb: Path):
        lock_file = usb / self.config.get("lock_file", "_backup_running.lock")
        lock_file.write_text(f"running since {datetime.now().isoformat()}")
    
    def remove_lock(self, usb: Path):
        lock_file = usb / self.config.get("lock_file", "_backup_running.lock")
        if lock_file.exists():
            lock_file.unlink()
    
    def already_backed_up_today(self, usb: Path) -> bool:
        today = datetime.now().strftime("%Y-%m-%d")
        backup_dir = usb / self.config.get("backup_dir_name", "hasil_backup")
        if not backup_dir.exists():
            return False
        return any(d.name.startswith(today) for d in backup_dir.iterdir())
    
    def should_exclude(self, file_path: Path) -> bool:
        patterns = self.config.get("exclude_patterns", [])
        str_path = str(file_path)
        
        for pattern in patterns:
            if fnmatch.fnmatch(str_path, f"*{pattern}*"):
                return True
            if pattern in str_path.split(os.sep):
                return True
        return False
    
    def get_file_checksum(self, file_path: Path) -> str:
        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5.update(chunk)
        return md5.hexdigest()
    
    def should_backup_file(self, file: Path, last_backup_info: dict) -> bool:
        if not self.config.get("enable_incremental", True):
            return True
        
        method = self.config.get("incremental_method", "mtime")
        
        if method == "mtime":
            file_mtime = file.stat().st_mtime
            stored_mtime = last_backup_info.get("mtime", 0)
            return file_mtime > stored_mtime
        
        elif method == "checksum":
            try:
                file_checksum = self.get_file_checksum(file)
                return file_checksum != last_backup_info.get("checksum")
            except Exception:
                return True
        
        return True
    
    def get_file_info(self, file: Path, method: str = "mtime") -> dict:
        info = {"mtime": file.stat().st_mtime}
        if method == "checksum":
            try:
                info["checksum"] = self.get_file_checksum(file)
            except Exception:
                pass
        return info
    
    def check_space(self, usb: Path) -> tuple[bool, str]:
        min_free = self.config.get("min_free_space_mb", 100) * 1024 * 1024
        try:
            info = get_usb_info(usb)
            if info["free_space"] < min_free:
                return False, f"USB space insufficient: {info['free_space'] / (1024*1024):.1f}MB free"
        except Exception as e:
            self.logger.warning(f"Could not check space: {e}")
        return True, "OK"
    
    def count_files_to_backup(self, dry_run: bool = False) -> tuple[int, int]:
        source_folders = [Path(f) for f in self.config.get("source_folders", [])]
        extensions = self.config.get("target_extensions", {})
        total_files = 0
        total_size = 0
        
        for folder in source_folders:
            if not folder.exists():
                continue
            for file in folder.rglob("*"):
                if not file.is_file():
                    continue
                if self.should_exclude(file):
                    continue
                ext = file.suffix.lower()
                if ext not in extensions:
                    continue
                try:
                    size_mb = file.stat().st_size / (1024 * 1024)
                    if size_mb > extensions[ext]:
                        continue
                except OSError:
                    continue
                total_files += 1
                try:
                    total_size += file.stat().st_size
                except OSError:
                    pass
        
        return total_files, total_size
    
    def do_backup(self, usb: Path, dry_run: bool = False) -> dict:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_dir_name = self.config.get("backup_dir_name", "hasil_backup")
        dest_root = usb / backup_dir_name / timestamp
        
        if not dry_run:
            dest_root.mkdir(parents=True, exist_ok=True)
        
        source_folders = [Path(f) for f in self.config.get("source_folders", [])]
        extensions = self.config.get("target_extensions", {})
        conflict_res = self.config.get("conflict_resolution", "skip")
        
        copied = skipped_conflict = skipped_size = skipped_ext = skipped_excluded = 0
        total_bytes = 0
        
        all_files = []
        for folder in source_folders:
            if not folder.exists():
                continue
            for file in folder.rglob("*"):
                if file.is_file():
                    all_files.append(file)
        
        total = len(all_files)
        
        for idx, file in enumerate(all_files):
            if self.should_exclude(file):
                skipped_excluded += 1
                continue
            
            ext = file.suffix.lower()
            if ext not in extensions:
                skipped_ext += 1
                continue
            
            try:
                size_mb = file.stat().st_size / (1024 * 1024)
                if size_mb > extensions[ext]:
                    skipped_size += 1
                    continue
            except OSError:
                continue
            
            try:
                rel = file.relative_to(Path.home())
            except ValueError:
                rel = Path(file.name)
            
            dest = dest_root / rel
            
            if not dry_run:
                if dest.exists():
                    if conflict_res == "skip":
                        skipped_conflict += 1
                        continue
                    elif conflict_res == "overwrite":
                        pass
                    elif conflict_res == "rename":
                        dest = dest_root / f"{rel.stem}_{int(time.time())}{rel.suffix}"
                
                dest.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(file, dest)
                    copied += 1
                    total_bytes += file.stat().st_size
                except (OSError, PermissionError):
                    pass
        
            progress = int((idx + 1) / total * 100) if total > 0 else 100
            if idx % 10 == 0:
                notify_progress("USB Backup Agent", f"Processing files... {idx+1}/{total}", progress)
        
        enable_compression = self.config.get("enable_compression", False)
        if enable_compression and copied > 0 and not dry_run:
            self._compress_backup(dest_root)
        
        return {
            "copied": copied,
            "skipped_conflict": skipped_conflict,
            "skipped_size": skipped_size,
            "skipped_ext": skipped_ext,
            "skipped_excluded": skipped_excluded,
            "total_bytes": total_bytes,
            "dest_path": str(dest_root),
        }
    
    def _compress_backup(self, backup_dir: Path):
        try:
            zip_path = backup_dir.parent / f"{backup_dir.name}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file in backup_dir.rglob("*"):
                    if file.is_file():
                        zf.write(file, file.relative_to(backup_dir))
            
            shutil.rmtree(backup_dir)
            self.logger.info(f"Compressed backup to {zip_path}")
        except Exception as e:
            self.logger.error(f"Compression failed: {e}")
    
    def check_and_backup(self):
        usb = self.find_usb()
        if not usb:
            return
        
        if self.is_locked(usb):
            self.logger.info("Backup already in progress, skipping...")
            return
        
        if self.already_backed_up_today(usb):
            self.logger.info("Already backed up today, skipping...")
            return
        
        space_ok, space_msg = self.check_space(usb)
        if not space_ok:
            self.logger.warning(f"Space check failed: {space_msg}")
            notify("USB Backup Warning", space_msg)
            return
        
        dry_run = self.config.get("dry_run", False)
        
        if dry_run:
            self.logger.info("Dry run mode - preview only")
            total_files, total_size = self.count_files_to_backup()
            notify("USB Backup Preview", f"Would backup {total_files} files (~{total_size/(1024*1024):.1f}MB)")
            return
        
        self.set_lock(usb)
        try:
            notify("USB Backup Agent", "USB detected, starting backup...")
            
            result = self.do_backup(usb)
            
            msg = (
                f"{result['copied']} files backed up "
                f"({result['total_bytes']/(1024*1024):.1f}MB).\n"
                f"Excluded: {result['skipped_ext']} ext, "
                f"{result['skipped_size']} size, "
                f"{result['skipped_excluded']} patterns"
            )
            notify("USB Backup Complete", msg)
            
            self.logger.info(f"Backup complete: {result}")
            
        except Exception as e:
            notify("USB Backup Error", str(e)[:100])
            self.logger.error(f"Backup error: {e}")
        finally:
            self.remove_lock(usb)
    
    def run(self):
        self.logger.info("USB Backup Agent started")
        interval = self.config.get("check_interval", 60)
        
        while True:
            try:
                self.check_and_backup()
            except Exception as e:
                self.logger.error(f"Check error: {e}")
            
            time.sleep(interval)


def main():
    agent = BackupAgent()
    agent.run()


if __name__ == "__main__":
    main()

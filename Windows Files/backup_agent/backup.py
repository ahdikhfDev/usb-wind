#!/usr/bin/env python3
import os
import sys
import shutil
import fnmatch
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from config import Config, load_config
from os_utils import find_usb, find_usb_by_name, get_usb_info, notify, notify_progress, setup_logging, get_logger


class BackupAgent:
    def __init__(self, config: Config = None):
        self.config = config or load_config()
        self.logger = setup_logging()
        self.stats = {
            "total_files": 0,
            "copied": 0,
            "skipped_ext": 0,
            "skipped_size": 0,
            "skipped_excluded": 0,
            "skipped_unchanged": 0,
            "total_size": 0,
            "skipped_size_total": 0,
        }
    
    def get_usb(self):
        target_name = self.config.get("usb_volume_name", "Untitled 1")
        usb = find_usb_by_name(target_name)
        
        if not usb:
            usb = find_usb()
        
        return usb
    
    def get_last_backup_time(self, usb: Path) -> float:
        backup_dir = usb / self.config.get("backup_dir_name", "hasil_backup")
        if not backup_dir.exists():
            return 0
        
        folders = [d for d in backup_dir.iterdir() if d.is_dir()]
        if not folders:
            return 0
        
        latest = max(f.stat().st_mtime for f in folders)
        return latest
    
    def should_exclude(self, file_path: Path) -> bool:
        patterns = self.config.get("exclude_patterns", [])
        str_path = str(file_path)
        
        for pattern in patterns:
            if fnmatch.fnmatch(str_path, f"*{pattern}*"):
                return True
            if pattern in str_path.split(os.sep):
                return True
            if file_path.name == pattern:
                return True
        
        folder_excludes = self.config.get("exclude_folder_names", [])
        parts = file_path.parts
        for part in parts:
            if part in folder_excludes:
                return True
        
        return False
    
    def get_modified_files(self, last_backup_time: float) -> list[tuple[Path, Path]]:
        source_folders = [Path(f) for f in self.config.get("source_folders", [])]
        extensions = self.config.get("target_extensions", {})
        max_size_mb = self.config.get("max_file_size_mb", 50)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        modified_files = []
        
        for folder in source_folders:
            if not folder.exists():
                continue
            
            for file in folder.rglob("*"):
                if not file.is_file():
                    continue
                
                if self.should_exclude(file):
                    self.stats["skipped_excluded"] += 1
                    continue
                
                ext = file.suffix.lower()
                if ext not in extensions:
                    self.stats["skipped_ext"] += 1
                    continue
                
                try:
                    size = file.stat().st_size
                    if size > max_size_bytes:
                        self.stats["skipped_size"] += 1
                        self.stats["skipped_size_total"] += size
                        continue
                except OSError:
                    continue
                
                self.stats["total_files"] += 1
                
                if last_backup_time > 0:
                    file_mtime = file.stat().st_mtime
                    if file_mtime <= last_backup_time:
                        self.stats["skipped_unchanged"] += 1
                        continue
                
                try:
                    rel = file.relative_to(Path.home())
                except ValueError:
                    rel = Path(file.name)
                
                modified_files.append((file, rel))
        
        return modified_files
    
    def run_backup(self, usb: Path, dry_run: bool = False):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_dir_name = self.config.get("backup_dir_name", "hasil_backup")
        dest_root = usb / backup_dir_name / timestamp
        
        if not dry_run:
            dest_root.mkdir(parents=True, exist_ok=True)
        
        last_backup_time = self.get_last_backup_time(usb)
        
        if last_backup_time > 0:
            self.logger.info(f"Last backup: {datetime.fromtimestamp(last_backup_time)}")
        else:
            self.logger.info("No previous backup found - backing up all files")
        
        modified_files = self.get_modified_files(last_backup_time)
        
        if not modified_files:
            self.logger.info("No modified files to backup")
            return
        
        total = len(modified_files)
        self.logger.info(f"Found {total} modified files to backup")
        
        for idx, (file, rel) in enumerate(modified_files):
            dest = dest_root / rel
            
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(file, dest)
                    self.stats["copied"] += 1
                    self.stats["total_size"] += file.stat().st_size
                except (OSError, PermissionError) as e:
                    self.logger.warning(f"Failed to copy {file}: {e}")
                    continue
            
            progress = int((idx + 1) / total * 100)
            if idx % 5 == 0:
                notify_progress("USB Backup", f"Backing up... {idx+1}/{total}", progress)
        
        if dry_run:
            self.stats["copied"] = total
    
    def print_summary(self):
        size_mb = self.stats["total_size"] / (1024 * 1024)
        skipped_mb = self.stats["skipped_size_total"] / (1024 * 1024)
        
        print("\n" + "=" * 50)
        print("BACKUP SUMMARY")
        print("=" * 50)
        print(f"  Files backed up:     {self.stats['copied']}")
        print(f"  Total size:          {size_mb:.1f} MB")
        print("-" * 50)
        print(f"  Skipped (unchanged): {self.stats['skipped_unchanged']}")
        print(f"  Skipped (excluded):  {self.stats['skipped_excluded']}")
        print(f"  Skipped (extension): {self.stats['skipped_ext']}")
        print(f"  Skipped (too large): {self.stats['skipped_size']} ({skipped_mb:.1f} MB)")
        print("=" * 50)
    
    def run(self):
        self.logger.info("USB Backup Agent started")
        
        notify("USB Backup", "Starting backup process...")
        
        usb = self.get_usb()
        
        if not usb:
            notify("USB Backup Error", "USB 'Untitled 1' not found!")
            self.logger.error("USB not found")
            print("\nERROR: USB 'Untitled 1' not found!")
            print("Make sure the USB is connected and has the marker file.")
            sys.exit(1)
        
        usb_info = get_usb_info(usb)
        self.logger.info(f"USB found: {usb_info['name']}")
        print(f"\nUSB found: {usb_info['name']}")
        print(f"Free space: {usb_info['free_space'] / (1024**3):.1f} GB")
        
        dry_run = self.config.get("dry_run", False)
        
        if dry_run:
            print("\n[DRY RUN MODE - No files will be copied]")
        
        try:
            self.run_backup(usb, dry_run)
            self.print_summary()
            
            if self.stats["copied"] > 0:
                notify("Backup Complete", f"{self.stats['copied']} files backed up ({self.stats['total_size']/(1024*1024):.1f} MB)")
            else:
                notify("Backup Complete", "No new files to backup")
            
            self.logger.info("Backup completed successfully")
            
        except Exception as e:
            notify("Backup Error", str(e)[:100])
            self.logger.error(f"Backup failed: {e}")
            print(f"\nERROR: {e}")
            sys.exit(1)


def main():
    agent = BackupAgent()
    agent.run()


if __name__ == "__main__":
    main()

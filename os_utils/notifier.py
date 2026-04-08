import os
import sys
import platform
import subprocess
import threading
from typing import Optional


def get_os() -> str:
    return platform.system().lower()


class Notifier:
    def __init__(self):
        self.os_type = get_os()
    
    def send(self, title: str, message: str, progress: Optional[int] = None):
        if self.os_type == "windows":
            self._notify_windows(title, message, progress)
        elif self.os_type == "darwin":
            self._notify_macos(title, message, progress)
        else:
            self._notify_linux(title, message, progress)
    
    def _notify_windows(self, title: str, message: str, progress: Optional[int] = None):
        escaped_title = title.replace('"', "'").replace("`", "'")
        escaped_msg = message.replace('"', "'").replace("`", "'")
        
        if progress is not None:
            escaped_msg = f"{escaped_msg} [{progress}%]"
        
        script = f'''
Add-Type -AssemblyName System.Windows.Forms
$n = New-Object System.Windows.Forms.NotifyIcon
$n.Icon = [System.Drawing.SystemIcons]::Information
$n.Visible = $true
$n.ShowBalloonTip(8000, "{escaped_title}", "{escaped_msg}", [System.Windows.Forms.ToolTipIcon]::Info)
Start-Sleep -s 8
$n.Dispose()
'''
        try:
            subprocess.Popen(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", script],
                creationflags=0x08000000 if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
        except Exception:
            pass
    
    def _notify_macos(self, title: str, message: str, progress: Optional[int] = None):
        if progress is not None:
            message = f"{message} [{progress}%]"
        
        escaped_msg = message.replace('"', '\\"').replace("'", "\\'")
        escaped_title = title.replace('"', '\\"').replace("'", "\\'")
        
        script = f'display notification "{escaped_msg}" with title "{escaped_title}"'
        
        try:
            subprocess.Popen(["osascript", "-e", script])
        except Exception:
            pass
    
    def _notify_linux(self, title: str, message: str, progress: Optional[int] = None):
        if progress is not None:
            message = f"{message} [{progress}%]"
        
        escaped_title = title.replace('"', '\\"')
        escaped_msg = message.replace('"', '\\"')
        
        try:
            subprocess.Popen(["notify-send", "-a", "USB Backup Agent", escaped_title, escaped_msg])
        except FileNotFoundError:
            try:
                subprocess.Popen(["zenity", "--notification", "--text", f"{escaped_title}\n{escaped_msg}"])
            except FileNotFoundError:
                pass


_notifier = None


def _get_notifier() -> Notifier:
    global _notifier
    if _notifier is None:
        _notifier = Notifier()
    return _notifier


def notify(title: str, message: str):
    _get_notifier().send(title, message)


def notify_progress(title: str, message: str, progress: int):
    _get_notifier().send(title, message, progress)


def notify_async(title: str, message: str):
    thread = threading.Thread(target=notify, args=(title, message), daemon=True)
    thread.start()


def notify_progress_async(title: str, message: str, progress: int):
    thread = threading.Thread(target=notify_progress, args=(title, message, progress), daemon=True)
    thread.start()

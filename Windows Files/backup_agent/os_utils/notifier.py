import os
import platform
import subprocess
import threading
from typing import Optional


def get_os() -> str:
    return platform.system().lower()


def notify(title: str, message: str, progress: Optional[int] = None):
    if get_os() == "windows":
        _notify_windows(title, message, progress)
    elif get_os() == "darwin":
        _notify_macos(title, message, progress)
    else:
        _notify_linux(title, message, progress)


def _notify_windows(title: str, message: str, progress: Optional[int] = None):
    if progress is not None:
        message = f"{message} [{progress}%]"
    
    escaped_title = title.replace('"', "'").replace("`", "'")
    escaped_msg = message.replace('"', "'").replace("`", "'")
    
    script = f'''
Add-Type -AssemblyName System.Windows.Forms
$n = New-Object System.Windows.Forms.NotifyIcon
$n.Icon = [System.Drawing.SystemIcons]::Information
$n.Visible = $true
$n.ShowBalloonTip(5000, "{escaped_title}", "{escaped_msg}", [System.Windows.Forms.ToolTipIcon]::Info)
Start-Sleep -s 6
$n.Dispose()
'''
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", script],
            creationflags=0x08000000 if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
    except Exception:
        pass


def _notify_macos(title: str, message: str, progress: Optional[int] = None):
    if progress is not None:
        message = f"{message} [{progress}%]"
    
    escaped_msg = message.replace('"', '\\"').replace("'", "\\'")
    escaped_title = title.replace('"', '\\"').replace("'", "\\'")
    
    script = f'display notification "{escaped_msg}" with title "{escaped_title}"'
    
    try:
        subprocess.Popen(["osascript", "-e", script])
    except Exception:
        pass


def _notify_linux(title: str, message: str, progress: Optional[int] = None):
    if progress is not None:
        message = f"{message} [{progress}%]"
    
    escaped_title = title.replace('"', '\\"')
    escaped_msg = message.replace('"', '\\"')
    
    try:
        subprocess.Popen(["notify-send", "-a", "USB Backup", escaped_title, escaped_msg])
    except FileNotFoundError:
        try:
            subprocess.Popen(["zenity", "--notification", "--text", f"{escaped_title}\n{escaped_msg}"])
        except FileNotFoundError:
            pass


def notify_async(title: str, message: str, progress: Optional[int] = None):
    thread = threading.Thread(target=notify, args=(title, message, progress), daemon=True)
    thread.start()


def notify_progress(title: str, message: str, progress: int):
    notify(title, message, progress)

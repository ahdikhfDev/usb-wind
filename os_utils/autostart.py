import os
import sys
import platform
import subprocess
from pathlib import Path
from typing import Optional
import shutil


def get_os() -> str:
    return platform.system().lower()


def get_username() -> str:
    if get_os() == "windows":
        return os.environ.get("USERNAME", "user")
    return os.environ.get("USER", "user")


def get_script_path() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


def enable_autostart(agent_name: str = "USBBackupAgent") -> tuple[bool, str]:
    os_type = get_os()
    script_path = get_script_path()
    
    if os_type == "windows":
        return _enable_autostart_windows(agent_name, script_path)
    elif os_type == "darwin":
        return _enable_autostart_macos(agent_name, script_path)
    else:
        return _enable_autostart_linux(agent_name, script_path)


def _enable_autostart_windows(agent_name: str, script_path: Path) -> tuple[bool, str]:
    backup_py = script_path / "backup.py"
    
    if not backup_py.exists():
        return False, "backup.py not found"
    
    try:
        subprocess.run(
            ["schtasks", "/delete", "/tn", agent_name, "/f"],
            capture_output=True, timeout=10
        )
    except Exception:
        pass
    
    try:
        pythonw = shutil.which("pythonw") or shutil.which("python")
        if not pythonw:
            pythonw = "python"
        
        result = subprocess.run([
            "schtasks", "/create",
            "/tn", agent_name,
            "/tr", f'"{pythonw}" "{backup_py}"',
            "/sc", "ONLOGON",
            "/ru", get_username(),
            "/rl", "HIGHEST",
            "/f"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            subprocess.Popen([pythonw, str(backup_py)], creationflags=0x08000000 if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
            return True, "Autostart enabled via Task Scheduler"
        else:
            return False, f"Failed: {result.stderr}"
    except Exception as e:
        return False, str(e)


def _enable_autostart_macos(agent_name: str, script_path: Path) -> tuple[bool, str]:
    backup_py = script_path / "backup.py"
    
    if not backup_py.exists():
        return False, "backup.py not found"
    
    launch_agents = Path.home() / "Library" / "LaunchAgents"
    launch_agents.mkdir(parents=True, exist_ok=True)
    
    plist_path = launch_agents / f"com.usbbackup.{agent_name}.plist"
    
    plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.usbbackup.{agent_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{backup_py}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/usb_backup_{agent_name}.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/usb_backup_{agent_name}.err</string>
</dict>
</plist>
'''
    
    try:
        plist_path.write_text(plist_content)
        subprocess.run(["launchctl", "load", str(plist_path)], check=False)
        subprocess.Popen(["/usr/bin/python3", str(backup_py)])
        return True, "Autostart enabled via LaunchAgent"
    except Exception as e:
        return False, str(e)


def _enable_autostart_linux(agent_name: str, script_path: Path) -> tuple[bool, str]:
    backup_py = script_path / "backup.py"
    
    if not backup_py.exists():
        return False, "backup.py not found"
    
    xdg_config = Path.home() / ".config"
    autostart_dir = xdg_config / "autostart"
    autostart_dir.mkdir(parents=True, exist_ok=True)
    
    desktop_file = autostart_dir / f"usb-backup-{agent_name}.desktop"
    
    python3_path = shutil.which("python3") or "python3"
    
    desktop_content = f'''[Desktop Entry]
Type=Application
Name=USB Backup Agent
Comment=Automatic USB backup when connected
Exec={python3_path} {backup_py}
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
'''
    
    try:
        desktop_file.write_text(desktop_content)
        subprocess.Popen([python3_path, str(backup_py)])
        return True, "Autostart enabled via XDG autostart"
    except Exception as e:
        return False, str(e)


def disable_autostart(agent_name: str = "USBBackupAgent") -> tuple[bool, str]:
    os_type = get_os()
    
    if os_type == "windows":
        return _disable_autostart_windows(agent_name)
    elif os_type == "darwin":
        return _disable_autostart_macos(agent_name)
    else:
        return _disable_autostart_linux(agent_name)


def _disable_autostart_windows(agent_name: str) -> tuple[bool, str]:
    try:
        subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True, timeout=5)
        subprocess.run(["taskkill", "/f", "/im", "pythonw.exe"], capture_output=True, timeout=5)
    except Exception:
        pass
    
    try:
        result = subprocess.run(
            ["schtasks", "/delete", "/tn", agent_name, "/f"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return True, "Autostart disabled"
        else:
            return True, "Task not found (already disabled)"
    except Exception as e:
        return False, str(e)


def _disable_autostart_macos(agent_name: str) -> tuple[bool, str]:
    try:
        subprocess.run(["pkill", "-f", "backup.py"], capture_output=True, timeout=5)
    except Exception:
        pass
    
    plist_path = Path.home() / "Library" / "LaunchAgents" / f"com.usbbackup.{agent_name}.plist"
    
    try:
        subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True, check=False)
        if plist_path.exists():
            plist_path.unlink()
        return True, "Autostart disabled"
    except Exception as e:
        return False, str(e)


def _disable_autostart_linux(agent_name: str) -> tuple[bool, str]:
    try:
        subprocess.run(["pkill", "-f", "backup.py"], capture_output=True, timeout=5)
    except Exception:
        pass
    
    desktop_file = Path.home() / ".config" / "autostart" / f"usb-backup-{agent_name}.desktop"
    
    try:
        if desktop_file.exists():
            desktop_file.unlink()
        return True, "Autostart disabled"
    except Exception as e:
        return False, str(e)


def is_autostart_enabled(agent_name: str = "USBBackupAgent") -> bool:
    os_type = get_os()
    
    if os_type == "windows":
        try:
            result = subprocess.run(
                ["schtasks", "/query", "/tn", agent_name],
                capture_output=True, text=True, timeout=10
            )
            return "USBBackupAgent" in result.stdout
        except Exception:
            return False
    
    elif os_type == "darwin":
        plist_path = Path.home() / "Library" / "LaunchAgents" / f"com.usbbackup.{agent_name}.plist"
        return plist_path.exists()
    
    else:
        desktop_file = Path.home() / ".config" / "autostart" / f"usb-backup-{agent_name}.desktop"
        return desktop_file.exists()

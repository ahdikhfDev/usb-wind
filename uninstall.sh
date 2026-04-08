#!/usr/bin/env bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

AGENT_NAME="USBBackupAgent"

detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == *"mingw"* ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

clear
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           ███████╗███████╗ ██████╗ █████╗ ██████╗ ███████╗  ║
║           ██╔════╝██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝  ║
║           █████╗  ███████╗██║     ███████║██████╔╝█████╗    ║
║           ██╔══╝  ╚════██║██║     ██╔══██║██╔═══╝ ██╔══╝    ║
║           ███████╗███████║╚██████╗██║  ██║██║     ███████╗  ║
║           ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝     ╚══════╝  ║
║                                                              ║
║                  USB Backup Agent - Uninstaller             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF

echo ""

stop_processes() {
    echo -e "${YELLOW}[*] Stopping running processes...${NC}"
    
    if pgrep -f "backup.py" > /dev/null 2>&1; then
        pkill -f "backup.py" 2>/dev/null || true
        echo -e "${GREEN}[✓] Stopped backup.py processes${NC}"
    else
        echo -e "${YELLOW}[!] No running processes found${NC}"
    fi
    
    if command -v taskkill &> /dev/null; then
        taskkill /f /im python.exe 2>/dev/null || true
        taskkill /f /im pythonw.exe 2>/dev/null || true
    fi
    
    echo ""
}

remove_autostart() {
    OS_TYPE=$(detect_os)
    
    echo -e "${YELLOW}[*] Removing autostart configuration...${NC}"
    
    case $OS_TYPE in
        macos)
            PLIST_FILE="$HOME/Library/LaunchAgents/com.usbbackup.$AGENT_NAME.plist"
            if [ -f "$PLIST_FILE" ]; then
                launchctl unload "$PLIST_FILE" 2>/dev/null || true
                rm -f "$PLIST_FILE"
                echo -e "${GREEN}[✓] Removed macOS LaunchAgent${NC}"
            else
                echo -e "${YELLOW}[!] LaunchAgent not found${NC}"
            fi
            ;;
        
        linux)
            DESKTOP_FILE="$HOME/.config/autostart/usb-backup-$AGENT_NAME.desktop"
            if [ -f "$DESKTOP_FILE" ]; then
                rm -f "$DESKTOP_FILE"
                echo -e "${GREEN}[✓] Removed Linux autostart entry${NC}"
            else
                echo -e "${YELLOW}[!] Autostart entry not found${NC}"
            fi
            ;;
        
        windows)
            if command -v schtasks &> /dev/null; then
                schtasks /delete /tn "$AGENT_NAME" /f 2>/dev/null
                if [ $? -eq 0 ]; then
                    echo -e "${GREEN}[✓] Removed Windows Task Scheduler entry${NC}"
                else
                    echo -e "${YELLOW}[!] Task not found${NC}"
                fi
            fi
            ;;
        
        *)
            echo -e "${RED}[!] Unsupported OS${NC}"
            ;;
    esac
    
    echo ""
}

cleanup_files() {
    echo -e "${YELLOW}[*] Cleaning up configuration files...${NC}"
    
    case $(detect_os) in
        macos)
            CONFIG_DIR="$HOME/Library/Application Support/USBBackupAgent"
            LOG_DIR="$HOME/Library/Logs/USBBackupAgent"
            ;;
        linux)
            CONFIG_DIR="$HOME/.config/usb_backup_agent"
            LOG_DIR="$HOME/.local/share/usb_backup_agent/logs"
            ;;
        windows)
            CONFIG_DIR="$LOCALAPPDATA/USBBackupAgent"
            LOG_DIR="$LOCALAPPDATA/USBBackupAgent/logs"
            ;;
        *)
            CONFIG_DIR="$HOME/.usb_backup_agent"
            LOG_DIR="$HOME/.usb_backup_agent/logs"
            ;;
    esac
    
    if [ -d "$CONFIG_DIR" ]; then
        rm -rf "$CONFIG_DIR"
        echo -e "${GREEN}[✓] Removed config directory${NC}"
    fi
    
    if [ -d "$LOG_DIR" ]; then
        rm -rf "$LOG_DIR"
        echo -e "${GREEN}[✓] Removed log directory${NC}"
    fi
    
    echo ""
}

print_summary() {
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    UNINSTALL COMPLETE                         ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${BOLD}Removed:${NC}"
    echo "  ✓ Backup processes"
    echo "  ✓ Autostart entries"
    echo "  ✓ Configuration files"
    echo "  ✓ Log files"
    echo ""
    echo -e "${YELLOW}[!] Note: USB marker file and backup results were preserved.${NC}"
    echo ""
}

main() {
    stop_processes
    remove_autostart
    cleanup_files
    print_summary
    
    echo "Press Enter to exit..."
    read
}

main "$@"

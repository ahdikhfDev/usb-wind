#!/usr/bin/env bash
set -e

VERSION="2.0.0"
AGENT_NAME="USBBackupAgent"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup.py"
CONFIG_SCRIPT="$SCRIPT_DIR/config.py"
CONFIG_DIR=""
LOG_DIR=""

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

init_paths() {
    OS_TYPE=$(detect_os)
    USER_NAME=$(whoami)
    
    case $OS_TYPE in
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
║              USB Backup Agent v2.0 - Cross Platform          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF

echo ""
echo -e "${CYAN}Platform:${NC} $(detect_os | tr 'a-z' 'A-Z')"
echo -e "${CYAN}User:${NC} $USER_NAME"
echo -e "${CYAN}Version:${NC} $VERSION"
echo ""

check_python() {
    echo -e "${YELLOW}[*] Checking Python installation...${NC}"
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}[✗] Python not found!${NC}"
        echo ""
        echo "Please install Python first:"
        echo "  macOS: brew install python"
        echo "  Linux: sudo apt install python3 (Debian/Ubuntu)"
        echo "         sudo dnf install python3 (Fedora)"
        echo "  Windows: Download from https://python.org"
        echo ""
        read -p "Press Enter to exit..."
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
    echo -e "${GREEN}[✓] Found: $PYTHON_VERSION${NC}"
    echo ""
}

check_dependencies() {
    echo -e "${YELLOW}[*] Checking dependencies...${NC}"
    
    OS_TYPE=$(detect_os)
    
    if [[ "$OS_TYPE" == "macos" ]]; then
        if ! command -v osascript &> /dev/null; then
            echo -e "${YELLOW}[!] osascript not found - notifications may not work${NC}"
        fi
    elif [[ "$OS_TYPE" == "linux" ]]; then
        if ! command -v notify-send &> /dev/null; then
            echo -e "${YELLOW}[!] notify-send not found - install libnotify-bin${NC}"
        fi
    fi
    
    echo -e "${GREEN}[✓] Core dependencies OK${NC}"
    echo ""
}

create_marker() {
    echo -e "${YELLOW}[*] Creating marker file...${NC}"
    
    if [[ -f "$SCRIPT_DIR/_usb_backup_marker.txt" ]]; then
        echo -e "${GREEN}[✓] Marker file already exists${NC}"
    else
        echo "USB Backup Agent Marker - DO NOT DELETE" > "$SCRIPT_DIR/_usb_backup_marker.txt"
        echo -e "${GREEN}[✓] Marker file created${NC}"
    fi
    
    if [[ ! -d "$SCRIPT_DIR/hasil_backup" ]]; then
        mkdir -p "$SCRIPT_DIR/hasil_backup"
        echo -e "${GREEN}[✓] Backup folder created${NC}"
    fi
    
    echo ""
}

interactive_config() {
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                  CONFIGURATION SETUP                          ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    
    echo -e "${BOLD}Source Folders to Backup:${NC}"
    echo "  1) Documents, Desktop, Downloads, Pictures (Default)"
    echo "  2) Documents only"
    echo "  3) Custom folder selection"
    echo "  4) All default folders"
    read -p "Select option [1-4, default: 1]: " folder_opt
    folder_opt="${folder_opt:-1}"
    
    case $folder_opt in
        1)
            SOURCE_FOLDERS='["~/Documents", "~/Desktop", "~/Downloads", "~/Pictures"]'
            ;;
        2)
            SOURCE_FOLDERS='["~/Documents"]'
            ;;
        3)
            echo "Enter folder paths (absolute paths, comma separated):"
            read -r -p "Folders: " custom_folders
            custom_folders=$(echo "$custom_folders" | sed "s/,/\", \"/g")
            SOURCE_FOLDERS="[\"$custom_folders\"]"
            ;;
        *)
            SOURCE_FOLDERS='["~/Documents", "~/Desktop", "~/Downloads", "~/Pictures"]'
            ;;
    esac
    
    echo ""
    echo -e "${BOLD}Backup Options:${NC}"
    read -p "Enable compression (zip)? [y/N]: " enable_compress
    ENABLE_COMPRESS="false"
    if [[ "$enable_compress" =~ ^[Yy]$ ]]; then
        ENABLE_COMPRESS="true"
    fi
    
    read -p "Enable incremental backup (only changed files)? [Y/n]: " enable_incremental
    ENABLE_INCREMENTAL="true"
    if [[ "$enable_incremental" =~ ^[Nn]$ ]]; then
        ENABLE_INCREMENTAL="false"
    fi
    
    echo ""
    echo -e "${BOLD}Conflict Resolution:${NC}"
    echo "  1) Skip existing files (default)"
    echo "  2) Overwrite existing files"
    echo "  3) Rename with timestamp"
    read -p "Select [1-3, default: 1]: " conflict_opt
    conflict_opt="${conflict_opt:-1}"
    
    case $conflict_opt in
        1) CONFLICT_RES="skip" ;;
        2) CONFLICT_RES="overwrite" ;;
        *) CONFLICT_RES="rename" ;;
    esac
    
    echo ""
    echo -e "${BOLD}Check Interval:${NC}"
    echo "  How often to check for USB (in seconds)?"
    read -p "Interval [60, default: 60]: " check_interval
    CHECK_INTERVAL="${check_interval:-60}"
    
    echo ""
    echo -e "${BOLD}Dry Run Mode:${NC}"
    echo "  Preview what would be backed up without actually copying?"
    read -p "Enable dry run? [y/N]: " dry_run
    DRY_RUN="false"
    if [[ "$dry_run" =~ ^[Yy]$ ]]; then
        DRY_RUN="true"
    fi
    
    CONFIG_JSON=$(cat << CONFIG_EOF
{
    "source_folders": $SOURCE_FOLDERS,
    "enable_compression": $ENABLE_COMPRESS,
    "enable_incremental": $ENABLE_INCREMENTAL,
    "conflict_resolution": "$CONFLICT_RES",
    "check_interval": $CHECK_INTERVAL,
    "dry_run": $DRY_RUN,
    "marker_file": "_usb_backup_marker.txt",
    "lock_file": "_backup_running.lock",
    "backup_dir_name": "hasil_backup",
    "target_extensions": {
        ".jpg": 5, ".jpeg": 5, ".png": 5,
        ".gif": 5, ".webp": 5,
        ".docx": 10, ".xlsx": 10, ".pptx": 10,
        ".pdf": 15,
        ".txt": 5, ".csv": 5
    },
    "exclude_patterns": [
        "node_modules", ".git", "__pycache__",
        "*.tmp", "*.temp", "Thumbs.db", ".DS_Store"
    ],
    "min_free_space_mb": 100,
    "log_level": "INFO"
}
CONFIG_EOF
)
    
    mkdir -p "$CONFIG_DIR"
    echo "$CONFIG_JSON" > "$CONFIG_DIR/config.json"
    
    echo -e "${GREEN}[✓] Configuration saved${NC}"
    echo ""
}

setup_autostart() {
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                  AUTOSTART SETUP                             ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    
    echo -e "${BOLD}Enable automatic startup?${NC}"
    echo "  The backup agent will run in the background when you log in."
    echo ""
    read -p "Enable autostart? [Y/n]: " enable_autostart
    
    if [[ ! "$enable_autostart" =~ ^[Nn]$ ]]; then
        OS_TYPE=$(detect_os)
        
        case $OS_TYPE in
            macos)
                setup_macos_autostart
                ;;
            linux)
                setup_linux_autostart
                ;;
            windows)
                setup_windows_autostart
                ;;
            *)
                echo -e "${RED}[!] Unsupported OS for autostart${NC}"
                ;;
        esac
    else
        echo -e "${YELLOW}[!] Autostart skipped${NC}"
    fi
    
    echo ""
}

setup_macos_autostart() {
    echo -e "${YELLOW}[*] Setting up macOS LaunchAgent...${NC}"
    
    LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
    mkdir -p "$LAUNCH_AGENTS"
    
    PLIST_FILE="$LAUNCH_AGENTS/com.usbbackup.$AGENT_NAME.plist"
    
    cat > "$PLIST_FILE" << PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.usbbackup.$AGENT_NAME</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$BACKUP_SCRIPT</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/usb_backup.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/usb_backup.err</string>
</dict>
</plist>
PLIST_EOF
    
    launchctl load "$PLIST_FILE" 2>/dev/null || true
    
    echo -e "${GREEN}[✓] macOS autostart configured${NC}"
}

setup_linux_autostart() {
    echo -e "${YELLOW}[*] Setting up Linux autostart...${NC}"
    
    XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
    AUTOSTART_DIR="$XDG_CONFIG_HOME/autostart"
    mkdir -p "$AUTOSTART_DIR"
    
    DESKTOP_FILE="$AUTOSTART_DIR/usb-backup-$AGENT_NAME.desktop"
    
    cat > "$DESKTOP_FILE" << DESKTOP_EOF
[Desktop Entry]
Type=Application
Name=USB Backup Agent
Comment=Automatic USB backup when connected
Exec=/usr/bin/python3 $BACKUP_SCRIPT
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
DESKTOP_EOF
    
    echo -e "${GREEN}[✓] Linux autostart configured${NC}"
}

setup_windows_autostart() {
    echo -e "${YELLOW}[*] Setting up Windows Task Scheduler...${NC}"
    
    if command -v schtasks &> /dev/null; then
        schtasks /delete /tn "$AGENT_NAME" /f 2>/dev/null || true
        
        PYTHON_CMD=$(where python 2>/dev/null | head -1 || echo "python")
        
        schtasks /create \
            /tn "$AGENT_NAME" \
            /tr "\"$PYTHON_CMD\" \"$BACKUP_SCRIPT\"" \
            /sc ONLOGON \
            /ru "$USER_NAME" \
            /rl HIGHEST \
            /f > /dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}[✓] Windows autostart configured${NC}"
        else
            echo -e "${YELLOW}[!] Could not configure autostart - try running as Administrator${NC}"
        fi
    else
        echo -e "${RED}[!] Task Scheduler not available${NC}"
    fi
}

start_agent() {
    echo ""
    echo -e "${YELLOW}[*] Starting USB Backup Agent...${NC}"
    
    $PYTHON_CMD "$BACKUP_SCRIPT" &
    AGENT_PID=$!
    
    sleep 2
    
    if ps -p $AGENT_PID > /dev/null 2>&1; then
        echo -e "${GREEN}[✓] Agent started (PID: $AGENT_PID)${NC}"
    else
        echo -e "${YELLOW}[!] Agent may have started in background${NC}"
    fi
}

print_summary() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    INSTALLATION COMPLETE                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${BOLD}Summary:${NC}"
    echo "  Config location: $CONFIG_DIR/config.json"
    echo "  Log location:    $LOG_DIR"
    echo "  Check interval:  ${CHECK_INTERVAL:-60} seconds"
    echo ""
    echo -e "${BOLD}Usage:${NC}"
    echo "  1. Copy this USB to any computer"
    echo "  2. When you insert the USB, backup starts automatically"
    echo "  3. Files are saved to: USB:/hasil_backup/DATE_TIME/"
    echo ""
    echo -e "${BOLD}Commands:${NC}"
    echo "  To uninstall:   ./uninstall.sh"
    echo "  To view logs:    tail -f $LOG_DIR/*.log"
    echo ""
    echo -e "${GREEN}Happy backing up! 🎉${NC}"
    echo ""
}

main() {
    init_paths
    check_python
    check_dependencies
    create_marker
    interactive_config
    setup_autostart
    start_agent
    print_summary
    
    echo "Press Enter to exit..."
    read
}

main "$@"

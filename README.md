# USB Backup Agent v2.0

Backup otomatis ke USB saat dicolokkan. Cross-platform: Windows, macOS, Linux.

## Fitur

- **Cross-Platform**: Jalan di Windows, macOS, dan Linux
- **Auto-Detection USB**: Deteksi drive USB secara otomatis
- **Smart Backup**: 
  - Incremental backup (hanya file yang berubah)
  - Exclude patterns (node_modules, .git, dll.)
  - Compression mode (zip)
  - Conflict resolution (skip/overwrite/rename)
- **Interactive Installer**: Menu setup interaktif
- **Progress Notification**: Notifikasi real-time saat backup
- **Logging System**: Log tersimpan di location terpisah OS

## Struktur Project

```
usb-backup-agent/
├── backup.py           # Main script
├── config.py           # Configuration manager
├── install.sh          # Interactive installer (cross-platform)
├── uninstall.sh        # Uninstaller (cross-platform)
├── os_utils/
│   ├── usb_finder.py   # USB detection per OS
│   ├── notifier.py     # Notifications per OS
│   ├── autostart.py    # Auto-start per OS
│   └── logger.py       # Logging utility
└── README.md
```

## Instalasi

### Windows, macOS, Linux

```bash
# Clone atau download project ini ke USB
cd usb-backup-agent

# Jalankan installer (interaktif)
./install.sh
```

### Catatan untuk Windows

Jalankan via:
- Git Bash: `./install.sh`
- WSL: `./install.sh`
- Command Prompt/PowerShell: `bash install.sh`

## Konfigurasi

Installer akan menanyakan:

1. **Source folders** - Folder mana yang di-backup
2. **Compression** - Enable zip compression
3. **Incremental** - Only backup changed files
4. **Conflict resolution** - Skip/Overwrite/Rename
5. **Check interval** - Berapa detik cek USB
6. **Dry run** - Preview mode

## Cara Kerja

1. USB dicolokkan ke komputer
2. Agent mendeteksi USB via marker file
3. Cek apakah sudah di-backup hari ini
4. Jika belum, mulai backup otomatis
5. File tersimpan di `USB:/hasil_backup/TANGGAL_WAKTU/`

## Uninstall

```bash
./uninstall.sh
```

## Log

- **Windows**: `%LOCALAPPDATA%/USBBackupAgent/logs/`
- **macOS**: `~/Library/Logs/USBBackupAgent/`
- **Linux**: `~/.local/share/usb_backup_agent/logs/`

## Extension & Size Limits Default

| Extension | Max Size (MB) |
|-----------|---------------|
| .jpg, .png, .gif, .webp | 5 |
| .docx, .xlsx, .pptx | 10 |
| .pdf | 15 |
| .txt, .csv | 5 |

## Lisensi

MIT License

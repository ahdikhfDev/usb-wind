# 🪟 Windows - Panduan Lengkap

## ⚡ Quick Start (3 Langkah)

```
1. Colokkan USB ke PC Windows
2. Buka folder "Windows Files"
3. Double-click "install.bat"
4. SELESAI! ✓
```

---

## 📁 Struktur File

```
📁 Windows Files/
│
├── 📄 Backup Now.bat        ← Backup manual (1x klik)
├── 📄 backup-loop.bat      ← Auto-detect (dijalankan otomatis)
├── 📄 install.bat          ← Setup auto-start (KLIK INI!)
├── 📄 uninstall.bat         ← Hapus auto-start
│
├── 📁 python-embed/       ← Python portable (NO INSTALL!)
├── 📁 backup_agent/       ← Core script
└── 📄 backup.py           ← Wrapper
```

---

## 🚀 Cara Kerja

### Setup Awal (Sekali Aja)
```
1. Double-click "install.bat"
2. Tekan Enter
3. ✅ Auto-start aktif!
```

### Depoisnya (Otomatis Forever)
```
Windows Start
    │
    ├── Script jalan otomatis di background
    │
    ├── Cek USB tiap 60 detik
    │   │
    │   ├── USB "Untitled 1" belum colok?
    │   │   └── 💤 Idle, tunggu 60 detik
    │   │
    │   └── USB "Untitled 1" dicolok?
    │       └── ⚡ AUTO BACKUP!
    │
    └── Loop forever
```

---

## 🔧 Fitur

| Fitur | Keterangan |
|-------|------------|
| **Auto-Detect USB** | Script auto-detect USB "Untitled 1" |
| **Incremental Backup** | Cuma backup file yang berubah |
| **Safe** | File yang sudah masuk tetap aman kalau dicabut |
| **Checkpoint** | Resume dari posisi terakhir |
| **Python Portable** | Nggak perlu install Python! |

---

## 🛡️ Safety

| Pertanyaan | Jawaban |
|-----------|---------|
| USB dicabut tengah backup? | ✅ File yang sudah masuk AMAN |
| Nggak butuh internet? | ✅ Offline work |
| Bikin virus? | ❌ Nggak, cuma backup |
| Data aman? | ✅✅ Ya |

---

## ❓ Troubleshooting

| Error | Solusi |
|-------|--------|
| "Python not found" | Pastikan folder `python-embed/` ada |
| "Access denied" | Right-click → Run as Administrator |
| Nggak auto-start | Jalankan `install.bat` lagi |
| Double-click nggak work | Buka Command Prompt, ketik `install.bat` |

---

## 📊 Flow Diagram

```
┌─────────────────────────────────────────────┐
│  PERTAMA KALI                               │
├─────────────────────────────────────────────┤
│                                              │
│  1. Colok USB                               │
│  2. Buka "Windows Files/"                  │
│  3. Double-click "install.bat"              │
│  ✅ Auto-start aktif!                       │
│                                              │
└─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│  SETELAH SETUP (Otomatic)                  │
├─────────────────────────────────────────────┤
│                                              │
│  Windows Start → Script jalan otomatis      │
│                                              │
│  Colok USB "Untitled 1"                     │
│      │                                       │
│      ├── Cek file yang berubah              │
│      ├── Copy ke USB                        │
│      └── 🔔 Notification popup              │
│                                              │
└─────────────────────────────────────────────┘
```

---

## 📋 Catatan Penting

| Hal | Keterangan |
|-----|------------|
| **Nama USB** | Pastikan USB namanya "Untitled 1" |
| **Python** | Sudah include di USB, nggak perlu install |
| **Admin Rights** | Kadang butuh Run as Administrator |
| **Backup Location** | `USB:/hasil_backup/TANGGAL_WAKTU/` |

---

## 🗑️ Uninstall

```bash
# Buka folder Windows Files/
# Double-click "uninstall.bat"
```

---

## 📞 Kontak

Butuh bantuan? Buat issue di GitHub.

---

**Nggak perlu install Python! Semua sudah ada di USB!** 🎉

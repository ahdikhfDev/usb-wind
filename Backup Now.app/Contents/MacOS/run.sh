#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup_agent/backup.py"

cd "$SCRIPT_DIR"

/usr/bin/python3 "$BACKUP_SCRIPT"

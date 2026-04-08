#!/usr/bin/env python3
import sys
import os
from pathlib import Path

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir))
    
    from backup_agent.backup import BackupAgent
    
    agent = BackupAgent()
    agent.run()

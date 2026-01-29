#!/usr/bin/env python3
"""
Restore From Point - Sovereign Sanctuary Elite

Restore system state from a verified restore point.

Version: 2.0.0
Author: Manus AI for Architect

SAFETY GUARANTEES:
- Requires explicit --confirm flag
- Creates backup before restore
- Verifies restore point integrity first
- Logs all actions to ledger
"""

import json
import hashlib
import shutil
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

LEDGER_PATH = Path("evidence/ledger.jsonl")
BACKUP_DIR = Path("RESTORE_BACKUPS")

# ═══════════════════════════════════════════════════════════════════
# CORE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def sha256_file(path: Path) -> str:
    """Calculate SHA-256 hash of a file"""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()


def load_manifest(restore_dir: Path) -> Dict[str, Any]:
    """Load manifest from restore point"""
    manifest_path = restore_dir / "MANIFEST.json"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def verify_restore_point(restore_dir: Path, manifest: Dict[str, Any]) -> bool:
    """Verify all files in restore point before restoring"""
    print("Verifying restore point integrity...")
    
    for file_info in manifest["files"]:
        file_path = restore_dir / file_info["path"]
        
        if not file_path.exists():
            print(f"  ❌ Missing: {file_info['path']}")
            return False
        
        actual_hash = sha256_file(file_path)
        if actual_hash != file_info["sha256"]:
            print(f"  ❌ Hash mismatch: {file_info['path']}")
            return False
        
        print(f"  ✅ Verified: {file_info['path']}")
    
    return True


def create_backup(files: List[Dict[str, Any]]) -> str:
    """Create backup of current files before restore"""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_id = f"BACKUP_{stamp}"
    backup_dir = BACKUP_DIR / backup_id
    backup_dir.mkdir(parents=True)
    
    print(f"Creating backup: {backup_id}")
    
    for file_info in files:
        source = Path(file_info["path"])
        if source.exists():
            dest = backup_dir / file_info["path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            print(f"  📦 Backed up: {file_info['path']}")
    
    return backup_id


def restore_files(restore_dir: Path, files: List[Dict[str, Any]]) -> int:
    """Restore files from restore point"""
    restored = 0
    
    for file_info in files:
        source = restore_dir / file_info["path"]
        dest = Path(file_info["path"])
        
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        
        print(f"  ✅ Restored: {file_info['path']}")
        restored += 1
    
    return restored


def log_restore(restore_id: str, backup_id: str, file_count: int) -> None:
    """Log the restore operation to the ledger"""
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "event": "RESTORE_EXECUTED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "restore_id": restore_id,
        "backup_id": backup_id,
        "file_count": file_count
    }
    
    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main() -> int:
    """
    Restore from a restore point.
    
    Returns:
        0 on success, 1 on failure
    """
    parser = argparse.ArgumentParser(
        description="Restore system state from a restore point"
    )
    parser.add_argument(
        "restore_point",
        help="Path to the restore point directory"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm the restore operation (required)"
    )
    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="Skip creating backup before restore (not recommended)"
    )
    
    args = parser.parse_args()
    restore_dir = Path(args.restore_point)
    
    print("\n" + "=" * 60)
    print("SOVEREIGN SANCTUARY ELITE - RESTORE FROM POINT")
    print("=" * 60)
    print(f"Restore Point: {restore_dir}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}Z")
    print("-" * 60)
    
    # Check restore point exists
    if not restore_dir.exists():
        print(f"❌ Restore point not found: {restore_dir}")
        return 1
    
    # Load manifest
    try:
        manifest = load_manifest(restore_dir)
    except Exception as e:
        print(f"❌ Failed to load manifest: {e}")
        return 1
    
    print(f"Restore ID: {manifest['restore_id']}")
    print(f"Created: {manifest['created_utc']}")
    print(f"Files: {len(manifest['files'])}")
    print("-" * 60)
    
    # Verify restore point
    if not verify_restore_point(restore_dir, manifest):
        print("\n❌ RESTORE ABORTED - Restore point verification failed")
        return 1
    
    print("\n✅ Restore point verified")
    
    # Check confirmation
    if not args.confirm:
        print("\n⚠️  DRY RUN MODE")
        print("To execute restore, add --confirm flag")
        print(f"\nCommand: python restore_from_point.py {restore_dir} --confirm")
        return 0
    
    print("-" * 60)
    print("EXECUTING RESTORE...")
    
    # Create backup
    backup_id = "NONE"
    if not args.skip_backup:
        backup_id = create_backup(manifest["files"])
        print(f"\n✅ Backup created: {backup_id}")
    else:
        print("\n⚠️  Skipping backup (--skip-backup flag)")
    
    # Restore files
    print("\nRestoring files...")
    restored = restore_files(restore_dir, manifest["files"])
    
    # Log to ledger
    log_restore(manifest["restore_id"], backup_id, restored)
    
    # Print summary
    print("-" * 60)
    print("✅ RESTORE COMPLETED SUCCESSFULLY")
    print(f"   Restore ID: {manifest['restore_id']}")
    print(f"   Backup ID:  {backup_id}")
    print(f"   Files:      {restored}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

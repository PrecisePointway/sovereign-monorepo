#!/usr/bin/env python3
"""
Module Registry Promoter
========================
Promotes validated modules from dev to prod with audit trail.
"""

import json
import sys
import hashlib
import shutil
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DEV_PATH = BASE_DIR / "dev" / "modules.json"
PROD_PATH = BASE_DIR / "prod" / "modules.json"
AUDIT_LOG = BASE_DIR / "audit.log"


def load_json(path: Path) -> list:
    """Load and parse JSON file."""
    if not path.exists():
        return []
    with open(path, "r") as f:
        return json.load(f)


def save_json(path: Path, data: list):
    """Save data to JSON file with pretty formatting."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def compute_hash(path: Path) -> str:
    """Compute SHA256 hash of file."""
    if not path.exists():
        return "none"
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def log_audit(action: str, details: str):
    """Append to audit log."""
    timestamp = datetime.utcnow().isoformat() + "Z"
    entry = f"{timestamp} | {action} | {details}\n"
    with open(AUDIT_LOG, "a") as f:
        f.write(entry)
    print(f"AUDIT: {entry.strip()}")


def validate_for_prod(modules: list) -> list[str]:
    """Check modules are valid for prod promotion."""
    errors = []
    for i, module in enumerate(modules):
        if module.get("status") == "Draft":
            errors.append(f"[{i}] '{module.get('name')}' has Draft status — cannot promote")
    return errors


def main():
    print("=" * 50)
    print("MODULE REGISTRY PROMOTION: DEV → PROD")
    print("=" * 50)
    
    # Check dev exists
    if not DEV_PATH.exists():
        print(f"ERROR: Dev registry not found: {DEV_PATH}")
        sys.exit(1)
    
    # Load dev modules
    dev_modules = load_json(DEV_PATH)
    print(f"Dev modules loaded: {len(dev_modules)}")
    
    # Filter: only Active, Parked, Deprecated go to prod
    promotable = [m for m in dev_modules if m.get("status") != "Draft"]
    draft_count = len(dev_modules) - len(promotable)
    
    print(f"Promotable (non-Draft): {len(promotable)}")
    print(f"Skipped (Draft): {draft_count}")
    
    if not promotable:
        print("WARNING: No modules to promote")
        sys.exit(0)
    
    # Validate for prod
    errors = validate_for_prod(promotable)
    if errors:
        print("PROMOTION BLOCKED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    
    # Backup current prod if exists
    if PROD_PATH.exists():
        backup_path = PROD_PATH.with_suffix(f".backup.{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json")
        shutil.copy(PROD_PATH, backup_path)
        print(f"Backup created: {backup_path.name}")
    
    # Compute hashes
    dev_hash = compute_hash(DEV_PATH)
    old_prod_hash = compute_hash(PROD_PATH)
    
    # Write to prod
    save_json(PROD_PATH, promotable)
    new_prod_hash = compute_hash(PROD_PATH)
    
    # Audit
    log_audit("PROMOTE", f"dev({dev_hash[:8]}) → prod({new_prod_hash[:8]}) | {len(promotable)} modules")
    
    print("-" * 50)
    print("PROMOTION COMPLETE")
    print(f"  Prod modules: {len(promotable)}")
    print(f"  Prod hash: {new_prod_hash[:16]}...")
    print("-" * 50)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Module Registry Diff
====================
Compare dev and prod registries to see what would change on promotion.
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DEV_PATH = BASE_DIR / "dev" / "modules.json"
PROD_PATH = BASE_DIR / "prod" / "modules.json"


def load_json(path: Path) -> list:
    """Load and parse JSON file."""
    if not path.exists():
        return []
    with open(path, "r") as f:
        return json.load(f)


def modules_to_dict(modules: list) -> dict:
    """Convert module list to dict keyed by name."""
    return {m["name"]: m for m in modules if "name" in m}


def main():
    print("=" * 50)
    print("MODULE REGISTRY DIFF: DEV vs PROD")
    print("=" * 50)
    
    dev_modules = load_json(DEV_PATH)
    prod_modules = load_json(PROD_PATH)
    
    dev_dict = modules_to_dict(dev_modules)
    prod_dict = modules_to_dict(prod_modules)
    
    dev_names = set(dev_dict.keys())
    prod_names = set(prod_dict.keys())
    
    # New in dev (not in prod)
    new_modules = dev_names - prod_names
    # Removed from dev (in prod but not dev)
    removed_modules = prod_names - dev_names
    # Common (check for changes)
    common_modules = dev_names & prod_names
    
    changed_modules = []
    for name in common_modules:
        if dev_dict[name] != prod_dict[name]:
            changed_modules.append(name)
    
    # Draft modules (won't be promoted)
    draft_modules = [m["name"] for m in dev_modules if m.get("status") == "Draft"]
    
    print(f"\nDev modules: {len(dev_modules)}")
    print(f"Prod modules: {len(prod_modules)}")
    
    print(f"\n--- NEW (will be added to prod) ---")
    if new_modules:
        for name in sorted(new_modules):
            status = dev_dict[name].get("status", "?")
            if status == "Draft":
                print(f"  [SKIP] {name} (Draft)")
            else:
                print(f"  [ADD]  {name} ({status})")
    else:
        print("  (none)")
    
    print(f"\n--- CHANGED (will be updated in prod) ---")
    if changed_modules:
        for name in sorted(changed_modules):
            old_status = prod_dict[name].get("status", "?")
            new_status = dev_dict[name].get("status", "?")
            if new_status == "Draft":
                print(f"  [SKIP] {name} (now Draft)")
            else:
                print(f"  [UPD]  {name} ({old_status} → {new_status})")
    else:
        print("  (none)")
    
    print(f"\n--- REMOVED (will be deleted from prod) ---")
    if removed_modules:
        for name in sorted(removed_modules):
            print(f"  [DEL]  {name}")
    else:
        print("  (none)")
    
    print(f"\n--- DRAFT (will NOT be promoted) ---")
    if draft_modules:
        for name in sorted(draft_modules):
            print(f"  [HOLD] {name}")
    else:
        print("  (none)")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import re
import sys


SITREP_PATH = "evidence/visuals/SWOT_SITREP_20251224.mmd"
KEYFRAMES_PATH = "evidence/visuals/FC_Keyframes_2025.mmd"


def exists(path: str) -> bool:
    return os.path.exists(path) and os.path.isfile(path)


def status_visuals() -> str:
    if not exists(KEYFRAMES_PATH):
        return "🔴"
    if not exists(f"{KEYFRAMES_PATH}.sha256.txt"):
        return "🟡"
    return "🟢"


def status_automation() -> str:
    required = [
        "tools/update_sitrep.py",
        "tools/autopilot.py",
        "tools/flight_control_daemon.py",
        ".run/Engage_Autopilot.run.xml",
        ".run/Flight_Control_Daemon.run.xml",
    ]
    present = [p for p in required if exists(p)]
    if len(present) == len(required):
        return "🟢"
    if present:
        return "🟡"
    return "🔴"


def replace_status_line(text: str, key: str, emoji: str) -> tuple[str, bool]:
    # Matches lines like: "      Visuals_Not_Started 🔴"
    pattern = re.compile(rf"^(?P<indent>\s*){re.escape(key)}(?:\s+[🟢🟡🔴])?\s*$", re.MULTILINE)

    def repl(m: re.Match[str]) -> str:
        return f"{m.group('indent')}{key} {emoji}"

    new_text, n = pattern.subn(repl, text)
    return new_text, n > 0


def main() -> int:
    if not exists(SITREP_PATH):
        print(f"ERROR: SITREP mindmap not found: {SITREP_PATH}")
        return 2

    with open(SITREP_PATH, "r", encoding="utf-8") as f:
        original = f.read()

    updated = original
    changed_any = False

    updated, changed = replace_status_line(updated, "Automation_Pending", status_automation())
    changed_any = changed_any or changed

    updated, changed = replace_status_line(updated, "Visuals_Not_Started", status_visuals())
    changed_any = changed_any or changed

    if updated != original:
        with open(SITREP_PATH, "w", encoding="utf-8", newline="\n") as f:
            f.write(updated)
        print(f"UPDATED: {SITREP_PATH}")
        return 0

    if not changed_any:
        print("No SITREP_STATUS keys matched; no changes made.")
        return 0

    print("No changes needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

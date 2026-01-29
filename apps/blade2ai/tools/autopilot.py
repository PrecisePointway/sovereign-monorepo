#!/usr/bin/env python3
import os
import subprocess
import sys


def run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def main() -> int:
    # Seal keyframes first (if present), then update and re-seal SITREP.
    keyframes = "evidence/visuals/FC_Keyframes_2025.mmd"
    sitrep = "evidence/visuals/SWOT_SITREP_20251224.mmd"

    if os.path.isfile(keyframes):
        rc = run([sys.executable, "tools/seal_file.py", keyframes])
        if rc != 0:
            return rc

    rc = run([sys.executable, "tools/update_sitrep.py"])
    if rc != 0:
        return rc

    rc = run([sys.executable, "tools/seal_file.py", sitrep])
    if rc != 0:
        return rc

    print("AUTOPILOT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

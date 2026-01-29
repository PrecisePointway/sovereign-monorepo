#!/usr/bin/env python3
import glob
import os
import sys
import subprocess


def run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def main() -> int:
    patterns = sys.argv[1:] or [
        "evidence/visuals/*.mmd",
        "evidence/debates/*.md",
        "evidence/visuals/*.md",
    ]

    files: list[str] = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))

    files = sorted(set(files))
    if not files:
        print("No files matched.")
        return 0

    for f in files:
        if os.path.isfile(f):
            rc = run([sys.executable, "tools/seal_file.py", f])
            if rc != 0:
                return rc

    print(f"SEALED {len(files)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

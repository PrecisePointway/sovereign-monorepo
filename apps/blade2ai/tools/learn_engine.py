#!/usr/bin/env python3
"""Learning Engine (stdlib-only)

Reads self-heal monitor events (JSONL) and produces a small Markdown report.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_EVENTS = Path("evidence/session-logs/self_heal_events.jsonl")
DEFAULT_REPORT = Path("evidence/visuals/LEARNING_REPORT.md")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    events: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception:
                continue
    return events


def render_report(events: list[dict[str, Any]], source: Path) -> str:
    event_types = Counter(e.get("event", "unknown") for e in events)

    lines: list[str] = []
    lines.append("# Learning Report")
    lines.append(f"**Generated (UTC):** {utc_now_iso()}")
    lines.append(f"**Source:** {source.as_posix()}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Total events: {len(events)}")
    lines.append("")
    lines.append("## Event Types")
    for k, v in event_types.most_common():
        lines.append(f"- {k}: {v}")

    # Quick heuristic: highlight recurring unreachable nodes.
    unreachable = [e for e in events if e.get("event") == "node_unreachable"]
    node_counts = Counter(e.get("node", "unknown") for e in unreachable)

    if node_counts:
        lines.append("")
        lines.append("## Recurring Unreachables")
        for node, count in node_counts.most_common(5):
            lines.append(f"- {node}: {count}")

    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Analyze self-heal events and write a Markdown learning report")
    ap.add_argument("--events", type=str, default=str(DEFAULT_EVENTS), help="Path to JSONL events")
    ap.add_argument("--out", type=str, default=str(DEFAULT_REPORT), help="Path to write Markdown report")
    args = ap.parse_args()

    events_path = Path(args.events)
    out_path = Path(args.out)

    events = load_events(events_path)
    report = render_report(events, events_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8", newline="\n")

    # Seal the report (receipt-backed).
    try:
        subprocess.run([sys.executable, "tools/seal_file.py", str(out_path)], check=False)
    except Exception:
        pass

    print(f"WROTE: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Self-Heal Monitor (stdlib-first)

Continuous health monitoring across configured swarm nodes.
- Writes a small, diffable status report to evidence/visuals/SWARM_STATUS.md
- Appends JSONL events to evidence/session-logs/self_heal_events.jsonl
- Optionally triggers ops/self_heal_pc2.ps1 when PC2 is unreachable

Design goals:
- Deterministic, low-dependency (no required third-party packages)
- Safe by default (no destructive actions unless explicitly enabled)
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LOGS_DIR = Path("logs")
SELF_HEAL_LOG = LOGS_DIR / "self_heal.log"


DEFAULT_CONFIG: dict[str, Any] = {
    "nodes": {
        "PC1_blade": {"ip": "100.94.217.81", "role": "primary"},
        "PC2_echo": {"ip": "100.94.217.82", "role": "compute"},
        "PC4_local": {"ip": "127.0.0.1", "role": "controller"},
    },
    "thresholds": {
        "consecutive_failures_for_recovery": 3,
        "ping_timeout_ms": 1000,
    },
}


EVIDENCE_DIR = Path("evidence")
STATUS_MD = EVIDENCE_DIR / "visuals" / "SWARM_STATUS.md"
EVENTS_JSONL = EVIDENCE_DIR / "session-logs" / "self_heal_events.jsonl"
SITREP_MD_DEFAULT = EVIDENCE_DIR / "SITREP.md"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_config(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return DEFAULT_CONFIG
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_CONFIG


def ping(ip: str, timeout_ms: int) -> bool:
    if sys.platform.startswith("win"):
        cmd = ["ping", "-n", "1", "-w", str(int(timeout_ms)), ip]
    else:
        # -W is in seconds on most platforms
        cmd = ["ping", "-c", "1", "-W", str(max(1, int(timeout_ms / 1000))), ip]

    try:
        cp = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return cp.returncode == 0
    except Exception:
        return False


def append_event(event: dict[str, Any]) -> None:
    EVENTS_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with open(EVENTS_JSONL, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")


def append_log_line(line: str) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(SELF_HEAL_LOG, "a", encoding="utf-8", newline="\n") as f:
        f.write(line.rstrip("\n") + "\n")


@dataclass(frozen=True)
class NodeStatus:
    name: str
    ip: str
    role: str
    reachable: bool


def write_status_report(hostname: str, statuses: list[NodeStatus]) -> None:
    STATUS_MD.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# Swarm Status (Always-On)")
    lines.append(f"**Last Update (UTC):** {utc_now_iso()}")
    lines.append(f"**Reporter:** {hostname}")
    lines.append("")
    lines.append("## Nodes")

    for s in statuses:
        icon = "✅" if s.reachable else "🚨"
        lines.append(f"- {icon} **{s.name}** ({s.ip}) — {s.role}")

    lines.append("")
    lines.append("## Recovery")
    lines.append("- Default: no recovery actions (safe mode)")
    lines.append("- Enable PC2 recovery with: `--enable-recovery`")

    STATUS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_sitrep_md(sitrep_path: Path, statuses: list[NodeStatus]) -> None:
    sitrep_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# 🛡️ SYSTEM SITREP (LIVE)")
    lines.append(f"**Last Updated (UTC):** {utc_now_iso()}")
    lines.append("")
    lines.append("## 🌐 SWARM STATUS")
    for s in statuses:
        icon = "🟢" if s.reachable else "🔴"
        lines.append(f"- **{s.name}:** {icon} ({'ONLINE' if s.reachable else 'UNREACHABLE'})")
    lines.append("")
    sitrep_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def maybe_trigger_pc2_recovery(
    enabled: bool,
    pc2_ip: str,
    reason: str,
) -> None:
    if not enabled:
        return

    script = Path("ops") / "self_heal_pc2.ps1"
    if not script.exists():
        append_event(
            {
                "event": "pc2_recovery_skipped_missing_script",
                "timestamp_utc": utc_now_iso(),
                "pc2_ip": pc2_ip,
                "reason": reason,
            }
        )
        return

    # Use pwsh if available; fall back to powershell.
    shell = "pwsh" if shutil_which("pwsh") else "powershell"

    cmd = [
        shell,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        "-TargetIp",
        pc2_ip,
        "-RestartExplorer",
    ]

    append_event(
        {
            "event": "pc2_recovery_triggered",
            "timestamp_utc": utc_now_iso(),
            "pc2_ip": pc2_ip,
            "reason": reason,
            "command": " ".join(cmd),
        }
    )

    try:
        subprocess.run(cmd)
    except Exception as e:
        append_event(
            {
                "event": "pc2_recovery_failed",
                "timestamp_utc": utc_now_iso(),
                "pc2_ip": pc2_ip,
                "error": str(e),
            }
        )


def shutil_which(exe: str) -> str | None:
    # Minimal stdlib implementation (avoid importing shutil just for which).
    paths = os.environ.get("PATH", "").split(os.pathsep)
    exts = [""]
    if sys.platform.startswith("win"):
        exts = os.environ.get("PATHEXT", ".EXE").split(os.pathsep)

    for p in paths:
        p = p.strip('"')
        if not p:
            continue
        for ext in exts:
            cand = Path(p) / f"{exe}{ext}"
            if cand.exists() and cand.is_file():
                return str(cand)
    return None


def cpu_percent_total() -> float | None:
    # Best-effort, stdlib-first CPU utilization sampling.
    # - Windows: PowerShell Get-Counter
    # - Unix: 1-min load average normalized by CPU count
    try:
        if sys.platform.startswith("win"):
            shell = "pwsh" if shutil_which("pwsh") else "powershell"
            cmd = [
                shell,
                "-NoProfile",
                "-Command",
                "(Get-Counter '\\Processor(_Total)\\% Processor Time').CounterSamples.CookedValue",
            ]
            out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
            val = float(out.decode("utf-8", "replace").strip())
            if val < 0:
                return 0.0
            if val > 100:
                return 100.0
            return val

        # Non-Windows fallback: load average as a coarse proxy.
        getloadavg = getattr(os, "getloadavg", None)
        if not callable(getloadavg):
            return None
        load1, _, _ = getloadavg()
        cores = os.cpu_count() or 1
        return max(0.0, min(100.0, (float(load1) / float(cores)) * 100.0))
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Blade2AI self-heal monitor (stdlib-first)")
    ap.add_argument("--interval", type=int, default=60, help="Loop interval in seconds")
    ap.add_argument("--config", type=str, default="config/swarm_config.json", help="Config path")
    ap.add_argument(
        "--enable-recovery",
        action="store_true",
        help="Enable PC2 recovery triggers when unreachable",
    )
    args = ap.parse_args()

    config = load_config(args.config)
    thresholds = config.get("thresholds", {})
    paths_cfg: dict[str, Any] = config.get("paths", {}) if isinstance(config.get("paths", {}), dict) else {}

    consecutive_failures_for_recovery = int(thresholds.get("consecutive_failures_for_recovery", 3))
    ping_timeout_ms = int(thresholds.get("ping_timeout_ms", 1000))
    cpu_percent_alert = float(thresholds.get("cpu_percent_alert", 85))

    nodes: dict[str, Any] = config.get("nodes", {})

    sitrep_path = Path(str(paths_cfg.get("sitrep", SITREP_MD_DEFAULT.as_posix())))
    sealer_path = str(paths_cfg.get("sealer", "tools/seal_file.py"))

    hostname = socket.gethostname()
    failure_streak: dict[str, int] = {name: 0 for name in nodes.keys()}
    cpu_high_active = False

    append_event(
        {
            "event": "self_heal_monitor_started",
            "timestamp_utc": utc_now_iso(),
            "hostname": hostname,
            "enable_recovery": bool(args.enable_recovery),
            "interval": int(args.interval),
        }
    )

    while True:
        # Hot-reload config each loop so operators can adjust nodes/thresholds without restarts.
        config = load_config(args.config)
        thresholds = config.get("thresholds", {})
        paths_cfg = config.get("paths", {}) if isinstance(config.get("paths", {}), dict) else {}
        consecutive_failures_for_recovery = int(thresholds.get("consecutive_failures_for_recovery", 3))
        ping_timeout_ms = int(thresholds.get("ping_timeout_ms", 1000))
        cpu_percent_alert = float(thresholds.get("cpu_percent_alert", cpu_percent_alert))
        nodes = config.get("nodes", {})

        sitrep_path = Path(str(paths_cfg.get("sitrep", SITREP_MD_DEFAULT.as_posix())))
        sealer_path = str(paths_cfg.get("sealer", "tools/seal_file.py"))

        # Keep failure streak map in sync with node set.
        for name in list(failure_streak.keys()):
            if name not in nodes:
                del failure_streak[name]
        for name in nodes.keys():
            failure_streak.setdefault(name, 0)

        statuses: list[NodeStatus] = []
        pc2_unreachable = False

        # Resource resilience: detect local CPU spike.
        cpu_pct = cpu_percent_total()
        if cpu_pct is not None and cpu_pct >= cpu_percent_alert:
            if not cpu_high_active:
                cpu_high_active = True
                append_event(
                    {
                        "event": "learning_event",
                        "kind": "high_cpu_load",
                        "timestamp_utc": utc_now_iso(),
                        "hostname": hostname,
                        "cpu_percent": round(float(cpu_pct), 2),
                        "threshold": float(cpu_percent_alert),
                    }
                )
                append_log_line(
                    f"[LEARNING] {time.strftime('%Y-%m-%d %H:%M:%S')} LEARNING EVENT: High CPU Load ({cpu_pct:.2f}% >= {cpu_percent_alert:.2f}%)"
                )
        else:
            cpu_high_active = False

        for name, node_cfg in nodes.items():
            ip = str(node_cfg.get("ip", ""))
            role = str(node_cfg.get("role", ""))
            reachable = ping(ip, ping_timeout_ms)

            if reachable:
                if failure_streak.get(name, 0) != 0:
                    append_event(
                        {
                            "event": "node_recovered",
                            "timestamp_utc": utc_now_iso(),
                            "node": name,
                            "ip": ip,
                        }
                    )
                failure_streak[name] = 0
            else:
                failure_streak[name] = failure_streak.get(name, 0) + 1
                append_event(
                    {
                        "event": "node_unreachable",
                        "timestamp_utc": utc_now_iso(),
                        "node": name,
                        "ip": ip,
                        "streak": failure_streak[name],
                    }
                )

            # Treat any PC2_* node as the recovery target.
            if name.startswith("PC2_") and not reachable:
                pc2_unreachable = True

            statuses.append(NodeStatus(name=name, ip=ip, role=role, reachable=reachable))

        write_status_report(hostname=hostname, statuses=statuses)

        # Also write a simple SITREP.md for the Phase 1/2 spec.
        write_sitrep_md(sitrep_path=sitrep_path, statuses=statuses)

        # Seal outputs (receipt-backed even without the daemon).
        try:
            subprocess.run([sys.executable, sealer_path, str(STATUS_MD)], check=False)
            subprocess.run([sys.executable, sealer_path, str(sitrep_path)], check=False)
        except Exception:
            pass

        pc2_streak = 0
        for k, v in failure_streak.items():
            if k.startswith("PC2_"):
                pc2_streak = max(pc2_streak, v)

        pc2_ip_target = ""
        for k, node_cfg in nodes.items():
            if k.startswith("PC2_"):
                pc2_ip_target = str((node_cfg or {}).get("ip", ""))
                break

        if pc2_unreachable and pc2_streak >= consecutive_failures_for_recovery:
            maybe_trigger_pc2_recovery(
                enabled=bool(args.enable_recovery),
                pc2_ip=pc2_ip_target,
                reason=f"unreachable_streak_{pc2_streak}",
            )

        time.sleep(max(1, int(args.interval)))


if __name__ == "__main__":
    raise SystemExit(main())

# Blade2AI Workspace (meta-repo)

Tracks repos as submodules (pinned commits) and includes audit-grade tooling under `tools/`.

## Operational Readiness (Unified Activation Sequence)

Runbook: `docs/OPERATIONAL_READINESS_PROTOCOL.md`

Minimal operator sequence:

```powershell
gh auth status
git submodule sync --recursive
git submodule update --init --recursive

pwsh .\blade.ps1 -Sitrep
pwsh .\run-elite.ps1 -WhatIf
pwsh .\run-elite.ps1
pwsh -File .\launch_loops.ps1
```

## Flight Control (Always-On)

- Engage autopilot once: `python tools/autopilot.py`
- Run the always-on daemon: `python tools/flight_control_daemon.py`
	- Watches `evidence/` for `.md`/`.mmd` changes
	- Seals changed files and updates the SITREP mindmap via autopilot

## Self-Heal + Learn Loops (stdlib-first)

- Self-heal monitor (writes `evidence/visuals/SWARM_STATUS.md` + receipts):
	- Spec path (wrapper): `python scripts/ops/self_heal_monitor.py --interval 60`
	- Canonical path: `python tools/self_heal_monitor.py --interval 60`
	- Enable PC2 recovery triggers: `python tools/self_heal_monitor.py --interval 60 --enable-recovery`

- Learning report (reads JSONL events and emits a Markdown report + receipt):
	- Spec path (wrapper): `python scripts/ops/learn_engine.py`
	- Canonical path: `python tools/learn_engine.py`

## Launch Loops (Windows)

- Start monitor + watchdog in the background: `pwsh -File ./launch_loops.ps1`

## PC2 Emergency Recovery (manual)

- Ping only: `pwsh -File ops/self_heal_pc2.ps1 -PingOnly`
- Attempt Explorer restart via WinRM: `pwsh -File ops/self_heal_pc2.ps1 -RestartExplorer`
- Force reboot (requires permissions): `pwsh -File ops/self_heal_pc2.ps1 -ForceReboot`

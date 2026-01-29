# Operational Readiness Protocol (Unified Activation Sequence)

date_utc: 2025-12-25
scope: repo-wide

## Goals
- Establish a single, repeatable operator sequence that:
  - Verifies repo integrity and pinned submodules
  - Produces receipts/evidence via authoritative entrypoints
  - Activates always-on loops without drifting the repo state

## Preconditions (P0)
- Windows PowerShell 7 (`pwsh`) available
- Git for Windows installed and on PATH
- Python available (repo prefers `.venv\\Scripts\\python.exe` when present)
- GitHub auth for private repos (HTTPS via `gh` is supported)

## Unified Activation Sequence

### 1) Repo + Auth preflight
From repo root:
- `gh auth status`
- `git status -sb`
- `git submodule sync --recursive`
- `git submodule update --init --recursive`

Pass condition:
- `git submodule update` completes without errors
- repo is either clean, or you explicitly understand any local modifications

### 2) Generate operator situational awareness (SITREP)
- `pwsh .\\blade.ps1 -Sitrep`

Pass condition:
- `evidence\\SITREP.md` (or other SITREP artifact) updates deterministically

### 3) Run-to-end verification with receipts (WhatIf first)
- Dry run (no writes): `pwsh .\\run-elite.ps1 -WhatIf`
- Real run (writes receipts): `pwsh .\\run-elite.ps1`

Pass condition:
- A receipt is written to `evidence\\session-logs\\` (per `run-elite.ps1` contract)

### 4) Activate always-on loops
- `pwsh -File .\\launch_loops.ps1`

Pass condition:
- `logs\\heal.pid` and `logs\\watchdog.pid` exist
- `evidence\\visuals\\SWARM_STATUS.md` begins updating over time

## Fast verification checklist
- `git remote show origin`
- `git submodule status --recursive`
- `Get-ChildItem evidence\\session-logs | Sort-Object LastWriteTime -Descending | Select-Object -First 5`
- `Get-Content logs\\heal.pid; Get-Content logs\\watchdog.pid`

## Troubleshooting (common)
- Submodule recursion errors: run `git submodule sync --recursive` then `git submodule update --init --recursive`.
- Private repo auth errors (HTTPS): run `gh auth login` then `gh auth setup-git`.
- Loops don’t start: confirm `.venv\\Scripts\\python.exe` exists; otherwise ensure `python` is on PATH.

## Notes
- Keep receipt schemas stable: downstream tooling expects receipt filenames and fields.
- Prefer `-WhatIf` when exploring; `run-elite.ps1` avoids writes under `-WhatIf`.

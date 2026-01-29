# Sovereign Monorepo

**STATUS: SEASON 2 CLOSED — OPEN SOURCE**

---

## Canonical Governance Document

> **CANONICAL / NON-NEGOTIABLE**
>
> The authoritative governance boundary for this repository is defined in:
>
> **[Sovereign_Governance_Core_Boundary.pdf](./Sovereign_Governance_Core_Boundary.pdf)**
>
> This document is immutable. It defines what is core, what is not, and what constitutes misuse. All contributors, auditors, partners, and regulators must reference this document before any action.

---

## Overview

This monorepo consolidates all Sovereign ecosystem components into a single, governed structure. It is designed to prevent accidental activation, authority creep, and misuse during the pre-Season 3 phase.

**WARNING:** This repository is **OBSERVATIONAL ONLY**. No enforcement, no automated decisions, no downstream hooks until Season 3 Kernel v0 is deployed.

## Critical Documents

Before making any changes, you **must** read and understand:

| Document | Purpose | Status |
| :--- | :--- | :--- |
| [Sovereign_Governance_Core_Boundary.pdf](./Sovereign_Governance_Core_Boundary.pdf) | **CANONICAL** — Defines the governance core boundary | Immutable |
| [CORE_BOUNDARY.md](./CORE_BOUNDARY.md) | Markdown source for the governance boundary | Source |
| [AUTHORITY_CLASSIFICATION.md](./AUTHORITY_CLASSIFICATION.md) | Classifies all components by authority level | Active |
| [MISUSE_SIGNALS.md](./MISUSE_SIGNALS.md) | Log for observed misuse signals | Active |

## Repository Structure

```
sovereign/
├── Sovereign_Governance_Core_Boundary.pdf   # CANONICAL
├── CORE_BOUNDARY.md
├── AUTHORITY_CLASSIFICATION.md
├── MISUSE_SIGNALS.md
├── README.md
│
├── infra/                       # Infrastructure (GOVERNANCE CORE)
│   ├── core/                    # sovereign-infra
│   ├── deploy/                  # sovereign-deploy
│   └── safe-os/                 # SAFE-OS
│
├── apps/                        # Applications
│   ├── elite/                   # sovereign-sanctuary-elite
│   ├── web-stack/               # sovereign-web-stack
│   └── blade2ai/                # Blade2AI
│
├── agents/                      # AI Agents (EXPERIMENTAL)
│   ├── sovereign-agent/
│   └── gesture-protocol/
│
├── modules/                     # Shared Modules
│   └── registry/
│
├── domains/                     # Domain Applications
│   └── agricoop/
│
└── docs/                        # Documentation
    ├── protocol/                # sovereign-protocol-docs
    ├── season2/                 # season2-rise-of-partnership
    ├── architecture/
    └── archive/                 # Historical artifacts (NO AUTHORITY)
```

## Rules of Engagement

1. **No direct pushes to main.** All changes require a pull request with explicit purpose, scope statement, and rollback plan.

2. **No enforcement until Season 3 Kernel v0.** All governance logic is observational only.

3. **Log all misuse signals.** Any attempt to treat non-core components as authoritative must be logged in `MISUSE_SIGNALS.md`.

4. **Respect the Core Boundary.** Only components listed in `CORE_BOUNDARY.md` may contain governance logic.

5. **Reference the CANONICAL PDF.** The PDF is the authoritative source for governance boundaries.

---

## License

This project is open source. See [LICENSE](./LICENSE) for details.

---

**Version:** 2.0.0
**Date:** January 29, 2026
**Status:** Season 2 Closed — Open Source

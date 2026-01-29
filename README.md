# Sovereign Monorepo

**WARNING: This repository is OBSERVATIONAL ONLY. No enforcement, no automated decisions, no downstream hooks until Season 3 Kernel v0 is deployed.**

---

## Overview

This monorepo consolidates all Sovereign ecosystem components into a single, governed structure. It is designed to prevent accidental activation, authority creep, and misuse during the pre-Season 3 phase.

## Critical Documents

Before making any changes, you **must** read and understand:

| Document | Purpose |
| :--- | :--- |
| [CORE_BOUNDARY.md](./CORE_BOUNDARY.md) | Defines what is and is not part of the Governance Core |
| [AUTHORITY_CLASSIFICATION.md](./AUTHORITY_CLASSIFICATION.md) | Classifies all components by authority level |
| [MISUSE_SIGNALS.md](./MISUSE_SIGNALS.md) | Log for observed misuse signals |

## Repository Structure

```
sovereign/
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

---

**Version:** 1.0.0
**Date:** January 29, 2026
**Status:** Pre-Season 3 (Observational Only)

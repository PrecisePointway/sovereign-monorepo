# Authority Classification

**This document explicitly classifies all components within the Sovereign monorepo by their authority level. No component may claim authority beyond its classification.**

---

## Classification Levels

| Level | Meaning |
| :--- | :--- |
| **GOVERNANCE CORE** | May contain governance logic, enforcement rules, or decision systems. Subject to quorum approval. |
| **APPLICATION** | Functional software with no governance authority. Cannot make or enforce decisions. |
| **EXPERIMENTAL** | Prototype or research code. Non-authoritative. May be deprecated without notice. |
| **DOCUMENTATION** | Narrative, planning, or reference material. Carries no decision weight. |

---

## Component Classifications

### GOVERNANCE CORE

| Path | Source Repository | Notes |
| :--- | :--- | :--- |
| `/infra/core/` | sovereign-infra | Season 2 core infrastructure |
| `/infra/safe-os/` | SAFE-OS | Sovereign, Assistive, Fail-closed Environment |
| `/apps/elite/core/` | sovereign-sanctuary-elite | Governance daemon and models only |

### APPLICATION (NO AUTHORITY)

| Path | Source Repository | Notes |
| :--- | :--- | :--- |
| `/apps/blade2ai/` | Blade2AI | AI-powered blade management |
| `/apps/web-stack/` | sovereign-web-stack | Hugo, FastAPI, WordPress stack |
| `/domains/agricoop/` | agricoop | Cooperative operating system |

### EXPERIMENTAL / NON-AUTHORITATIVE

| Path | Source Repository | Notes |
| :--- | :--- | :--- |
| `/agents/gesture-protocol/` | manus-gesture-protocol | Gesture-based control (prototype) |
| `/agents/sovereign-agent/` | sovereign-agent | Autonomous agent framework (prototype) |
| `/modules/registry/` | module-registry | Shared module registry |

### DOCUMENTATION ONLY

| Path | Source Repository | Notes |
| :--- | :--- | :--- |
| `/docs/protocol/` | sovereign-protocol-docs | Protocol documentation |
| `/docs/season2/` | season2-rise-of-partnership | Partnership documentation |
| `/docs/archive/` | Session artifacts | Historical artifacts, no authority |
| `/infra/deploy/` | sovereign-deploy | Deployment configs and docs |

---

## Enforcement

Until Season 3 Kernel v0 is deployed, **no component may enforce decisions**. All governance logic is observational only. Any attempt to activate enforcement must be logged in `MISUSE_SIGNALS.md`.

# Sovereign Governance Core Boundary

**WARNING: This document defines the explicit boundary of the Sovereign Governance Core. Nothing outside the directories listed below has authority, enforcement power, or decision weight.**

---

## Core Components

The following directories and their sub-contents constitute the **Sovereign Governance Core**:

- `/infra/core/` (from `sovereign-infra`)
- `/infra/safe-os/` (from `SAFE-OS`)
- `/apps/elite/` (governance components from `sovereign-sanctuary-elite`)

## Non-Core Components

All other directories and files within this monorepo are considered **non-core**. This includes, but is not limited to:

- `/docs/`
- `/apps/web-stack/`
- `/apps/blade2ai/`
- `/agents/`
- `/modules/`
- `/domains/`

## Authority & Misuse

- **Authority:** Only components within the **Sovereign Governance Core** can be considered for authoritative actions or decisions.
- **Misuse:** Citing, executing, or treating any non-core component as authoritative is a misuse of the system and will be logged.

---

**This boundary is non-negotiable and is enforced to prevent accidental activation and authority creep.**

# Misuse Signals Log

**This document serves as an immutable log of observed misuse signals. It is a critical early-warning system for governance failures.**

---

## Log Format

Each entry must follow this format:

```markdown
**Date:** YYYY-MM-DD HH:MM UTC
**Signal ID:** [UUID]
**Observer:** [Your Name/ID]

**Signal Type:**
- [ ] **Authority Creep:** Attempt to treat a non-core component as authoritative.
- [ ] **Premature Activation:** Request to enable enforcement or automated decision-making.
- [ ] **Policy Laundering:** Citing archived or non-authoritative documents as policy.
- [ ] **Process Bypass:** Attempt to merge code or make changes outside the established process.
- [ ] **Other:** (Specify)

**Description:**
A clear, objective description of the observed event. What happened? Who was involved? What was the context?

**Evidence:**
- Link to commit, PR, chat log, or other relevant artifacts.
- Quote the specific language used if applicable.

**Immediate Action Taken:**
- [ ] **None:** Observation only.
- [ ] **Clarification:** Reminded the individual of the core boundary/process.
- [ ] **Rejection:** Blocked a PR or action.
- [ ] **Escalation:** Notified the governance quorum.

**Follow-up Required:**
- [ ] None.
- [ ] Review process at next governance meeting.
- [ ] Update documentation to clarify.
- [ ] Other: (Specify)

---
```

## Log Entries

*(No entries yet.)*

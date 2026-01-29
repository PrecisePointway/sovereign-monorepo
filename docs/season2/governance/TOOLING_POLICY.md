# Tooling Policy — Season 2

**Version:** 1.0
**Date:** 27 January 2026
**Classification:** Internal Governance

---

### 1.0 PRINCIPLE

Each tool gets a single job. No tool gets to think it's the system.

The real system stays:
- **Local**
- **File-based**
- **Repo-based**
- **Portable**

Everything else is just a lens.

---

### 2.0 THE STACK (WHO DOES WHAT — NO OVERLAP)

| Tool | Role | Purpose |
|------|------|---------|
| **Notion** | Internal Truth & Operations | Living ops console, not brain replacement |
| **Figma** | Visual Story Only | Show, not decide |
| **WordPress** | Public Face | Shop window, nothing more |
| **SiteGround** | Hosting Only | Landlord, not partner |

---

### 3.0 NOTION — INTERNAL TRUTH & OPERATIONS

**Use it as a living ops console, not a brain replacement.**

**Yes for:**
- Master checklist (open source / Seedrs / grants)
- Status tracking (Not started / In progress / Done)
- One-page summaries you don't want to rewrite

**Hard Rules:**
- Notion is not canonical
- Nothing lives only in Notion
- If Notion vanished tomorrow, you still win

> Think: whiteboard that remembers things, not a source of truth.

---

### 4.0 FIGMA — VISUAL STORY ONLY

**Use it to show, not to decide.**

**Yes for:**
- Architecture diagrams
- System flow visuals
- Investor-friendly visuals
- Open-source diagrams

**Hard Rules:**
- No text-heavy docs
- No decisions made in Figma
- Export images → store locally / repo

> Think: diagram camera, not a design brain.

---

### 5.0 WORDPRESS — PUBLIC FACE

**This is your shop window, nothing more.**

**Yes for:**
- Public site
- Landing page
- "What this is / what it isn't"
- Links to open-source repo, contact, updates

**Hard Rules:**
- No business logic
- No workflows
- No governance hidden here
- Static pages preferred

> Think: poster on a wall, not infrastructure.

---

### 6.0 SITEGROUND — HOSTING ONLY

**Yes, with guardrails.**

**Yes for:**
- Hosting WordPress
- Email if you must (but don't build systems around it)
- Reliability and boring uptime

**Hard Rules:**
- No vendor lock-in content
- Keep full backups locally
- You can migrate away in a day if needed

> Think: landlord, not partner.

---

### 7.0 HOW THEY CONNECT

**They do not integrate deeply.**

```
Notion     → human coordination
Figma      → exported visuals
WordPress  → published output
SiteGround → dumb host
```

Your real system stays:
- local
- file-based
- repo-based
- portable

---

### 8.0 WHAT YOU ARE NOT DOING (ON PURPOSE)

| Prohibited | Reason |
|------------|--------|
| "All-in-one" platform | Creates dependency |
| Clever integrations | Hides state |
| Automation that hides state | Breaks auditability |
| SaaS dependency for truth | Violates sovereignty |

This keeps you:
- Calm
- Sovereign
- Able to stop at any time

---

### 9.0 BOTTOM LINE

| Tool | Function |
|------|----------|
| Notion | Organise |
| Figma | Explain |
| WordPress | Publish |
| SiteGround | Host |

**But none of them get to own the work.**

You already did the hard part. This stack just lets the world see it without touching it.

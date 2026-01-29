# Governance Assessment & Guidance Tool: Specification

**Version:** 1.0
**Date:** 27 January 2026
**Status:** Draft
**Classification:** Internal / Open-Core

---

## 1.0 What This Tool Is (Precisely)

> A **read-only assessment and guidance engine** that ingests system artefacts, evaluates them against declared governance standards, and produces:
> - Findings
> - Risk classifications
> - Remediation guidance
> - Optional implementation helpers

It **never executes changes by default**.
It **never requires data custody**.
It **never replaces human authority**.

**Think: Diagnostic instrument, not controller.**

---

## 2.0 Core Functions (No More, No Less)

### 2.1 ASSESS — "What is the state of this system?"

**Inputs (explicit, user-provided):**
- Config files
- Logs / telemetry snapshots
- Policy documents
- Evidence chains
- Architecture descriptors (schemas, diagrams)
- Optional: regulatory context (EU AI Act, sector)

**Assessment Outputs:**
- Compliance status (pass / partial / fail)
- Risk classification (ALARP-style)
- Gaps vs declared standards
- Confidence score (how complete the assessment is)

**Critical Rule:** If data is missing, the tool says **"unknown"**, not "assumed".

---

### 2.2 EXPLAIN — "Why does this matter?"

Every finding is paired with:
- The violated principle
- The affected risk domain
- The potential consequence (regulatory / operational / trust)

Plain language first. Technical appendix optional.

**This is where adoption happens.**

---

### 2.3 GUIDE — "What should be done?"

For each issue:
- **Minimum viable fix**
- **Better fix**
- **Gold-standard fix**

Each tagged with:
- Effort
- Dependency
- Whether it introduces new obligations

**No mandates. Only options.**

---

### 2.4 ASSIST (Optional, Opt-In)

This is where "help implementing" comes in — **safely**.

| Level | Description | Output |
|---|---|---|
| **Level 1: Templates** | Policy templates, config snippets, checklists. | Static files. |
| **Level 2: Generated Patches** | Suggested code diffs, config changes, documentation updates. | Never auto-applied. |
| **Level 3: Guided Execution** | Step-by-step instructions, human-in-the-loop confirmations, dual-authority checkpoints. | Interactive guidance. |

**At no point does the tool "take over".**

---

## 3.0 What Form This Takes

### NOT:
- A WordPress plugin
- A Notion integration
- A black-box SaaS
- A permanently connected agent

### YES:
- **CLI tool** (first-class)
- **Library / SDK**
- **Optional local UI**
- **Optional enterprise wrapper later**

**This preserves sovereignty and trust.**

---

## 4.0 KISS Architecture (Adoption-Safe)

```
User System (local / repo)
        |
        |  (explicit artefact export)
        v
Assessment Engine (read-only)
        |
        +--> Findings Report (MD / PDF / JSON)
        |
        +--> Remediation Guide
        |
        +--> Optional Implementation Helpers
```

**No background monitoring. No hidden state. No silent actions.**

---

## 5.0 Standards It Assesses Against

The tool never invents standards. It only evaluates against **declared frameworks**, such as:

- SGS constitutional invariants
- EU AI Act risk classes
- Sector-specific governance rules
- Internal policies
- Open standards (ISO, NIST, OECD)

**If no standard is declared, it asks you to choose or define one.**

---

## 6.0 Why This Is Powerful for Adoption

Because it:
- **Reduces fear:** "We can see where we stand."
- **Reduces effort:** "We know what to fix."
- **Preserves control:** "Nothing happens without us."
- **Builds trust:** "It shows its working."

This is exactly what:
- Regulators want
- Cooperatives need
- Enterprises tolerate
- Technologists respect

---

## 7.0 Naming (Important for Positioning)

**Do NOT call it:**
- "AI auditor"
- "Compliance engine"
- "Autonomous governance"

**Call it something like:**
- **Governance Assessment & Guidance Tool**
- **Sovereign Readiness Evaluator**
- **Constitutional Compliance Assistant**

**Names that signal support, not control.**

---

## 8.0 How This Enters the World (Quietly)

- Open-core
- Read-only by default
- Works on sample data
- Used in pilots and sandboxes
- Offered as "try it on your own system"

**No sales pressure. No lock-in. No dependency creation.**

---

## 9.0 Final Truth

This tool is **not about enforcement**.

It is about:
- **Legibility**
- **Confidence**
- **Lowering the activation energy of doing the right thing**

That is exactly what drives adoption *before* money ever enters the picture.

---

## 10.0 Next Steps (Optional)

- Sketch the exact module layout
- Define the input/output schema
- Design the "first 10 checks" that make it immediately useful

**Nothing here requires rushing. This is already the right shape.**

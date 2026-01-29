# Standalone Product Architecture: Principles for Non-Entanglement

**Version:** 1.0
**Date:** 27 January 2026
**Status:** Canonical
**Classification:** Architectural Doctrine

---

## 1.0 The Prime Directive: No Entanglement

Any new tool, feature, or capability built from this point forward (a "bolt-on") must exist as a **standalone product**. It cannot be a mere feature or plugin that depends on the core governance kernel or any other system to function.

> **Each product does one job. It does not know about the system. It does not try to become the system.**

This is not a guideline; it is a structural law. Violation of this principle constitutes architectural drift and must be rejected.

---

## 2.0 The Four Rules of Standalone Architecture

Every bolt-on product must adhere to these four rules without exception.

### Rule 1: It is a CLI Tool First

- **Primary Interface:** The product's primary and first-class interface must be a command-line interface (CLI).
- **Rationale:** A CLI enforces a clean separation of concerns. It takes explicit inputs and produces explicit outputs. It has no hidden state and cannot create deep, invisible integrations.
- **Secondary Interfaces:** Optional UIs (local web apps, etc.) are permissible, but they must be thin wrappers around the core CLI functionality. The product must be fully functional without the UI.

### Rule 2: It Communicates via Files and Standard Streams

- **Input:** The product must receive its inputs via command-line arguments, configuration files, or standard input (`stdin`).
- **Output:** The product must deliver its outputs via standard output (`stdout`), standard error (`stderr`), or by writing to files in specified directories.
- **Rationale:** This enforces a contract. The product does not reach into other systems to pull data, nor does it push data into them. It operates on what it is given and places its results in a predictable location. This prevents API-driven entanglement and dependency creep.

### Rule 3: It Has Zero Knowledge of the Core Kernel

- **No Direct Dependencies:** The product cannot import, link to, or otherwise directly depend on the code of the Sovereign Governance Kernel or any other bolt-on.
- **Shared Logic:** If functionality needs to be shared, it must be extracted into a standalone, versioned library that both the kernel and the bolt-on can depend on independently. The library itself becomes a standalone product.
- **Rationale:** This prevents the bolt-on from becoming a tightly coupled module of the core system. It ensures that the bolt-on can be developed, deployed, and even deprecated without affecting the kernel.

### Rule 4: It is Independently Viable

- **Standalone Value:** The product must provide tangible value on its own, without requiring the user to own or understand the entire Sovereign Governance ecosystem.
- **Example:** The `Governance Assessment & Guidance Tool` is valuable to anyone who wants to assess their system against a declared standard, even if they don't use our core kernel.
- **Rationale:** This ensures that each product has a clear purpose and a viable path to adoption on its own merits. It prevents the creation of "features" masquerading as products.

---

## 3.0 Architectural Metaphor: The Workshop, Not the Engine

Think of the Sovereign Governance Kernel as the engine block of a car. It is the core, immutable power source.

Bolt-on products are the tools on the workshop wall:

- A **torque wrench** (The Assessment Tool)
- A **diagnostic scanner** (A Log Analyzer)
- A **paint gun** (A Reporting Tool)

Each tool is picked up, used for its specific job, and then put back on the wall. The torque wrench does not need to know about the paint gun. The engine does not need to know about the wrench. The mechanic (the user) chooses the right tool for the job.

**We are not building a bigger, more complex engine. We are building a workshop of clean, reliable, single-purpose tools.**

---

## 4.0 Consequence of This Doctrine

- **No Vendor Lock-In:** Users can adopt one tool without adopting the entire ecosystem.
- **Resilience:** The failure or deprecation of one tool has no impact on the others.
- **Clarity:** The purpose of each product is clear and unambiguous.
- **Sovereignty:** The user remains in control, orchestrating the use of tools rather than being managed by an integrated system.

This is the only way to build bolt-ons that honor the core principles of the Sovereign Governance System. There is no other path.

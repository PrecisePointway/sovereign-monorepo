# Product Specification: Governance Assessment & Guidance Tool

**Version:** 1.0
**Date:** 27 January 2026
**Status:** Draft
**Codename:** The Assessor

---

## 1.0 One-Line Description

> A read-only CLI tool that ingests system artefacts, evaluates them against declared governance standards, and produces findings, risk classifications, and remediation guidance.

---

## 2.0 Adherence to Standalone Product Principles

This product strictly adheres to the `STANDALONE_PRODUCT_PRINCIPLES.md` doctrine.

| Principle | Implementation |
|---|---|
| **Rule 1: CLI Tool First** | The primary interface is a CLI. An optional local web UI will be a thin wrapper around the CLI. |
| **Rule 2: File-Based I/O** | The tool reads from specified files/directories and writes reports to a specified output directory. It does not connect to any APIs or databases. |
| **Rule 3: Zero Knowledge** | The tool has no dependency on the Sovereign Governance Kernel. It is a completely separate codebase. |
| **Rule 4: Independently Viable** | The tool is useful to any organization wishing to assess its systems against any declared standard, regardless of their use of our other products. |

---

## 3.0 Core Functionality

### 3.1 `assess` command

**Usage:**
```bash
assessor assess --input <path_to_artefacts> --output <path_to_reports> --standard <path_to_standard_file>
```

**Inputs:**
- `--input`: A directory containing the system artefacts to be assessed (e.g., config files, logs, policy documents).
- `--output`: A directory where the assessment reports will be written.
- `--standard`: A YAML or JSON file defining the governance standard to assess against. This file contains the specific checks to be performed.

**Process:**
1. The tool ingests the artefacts from the `--input` directory.
2. It reads the declared standard from the `--standard` file.
3. It executes a series of checks defined in the standard file against the artefacts.
4. It generates a set of findings.

**Outputs:**
- `findings.json`: A machine-readable JSON file containing the detailed assessment results.
- `report.md`: A human-readable Markdown report summarizing the findings, risk classifications, and remediation guidance.

### 3.2 `guide` command

**Usage:**
```bash
assessor guide --finding <finding_id> --level <1|2|3>
```

**Inputs:**
- `--finding`: The ID of a specific finding from the `findings.json` report.
- `--level`: The level of assistance requested (1: Template, 2: Patch, 3: Guided Execution).

**Process:**
- Based on the finding and the requested level, the tool generates the appropriate remediation assistance.

**Outputs:**
- For Level 1, it outputs a template file (e.g., `POLICY_TEMPLATE.md`).
- For Level 2, it outputs a patch file (e.g., `CONFIG_FIX.patch`).
- For Level 3, it initiates an interactive CLI session to guide the user through the remediation steps.

---

## 4.0 The Standard File (`standard.yaml`)

The power and flexibility of the Assessor come from the `standard.yaml` file. This file allows users to define their own governance standards.

**Example `standard.yaml`:**
```yaml
name: "SGS Core Invariants"
version: "1.0"
checks:
  - id: "AUTH-001"
    description: "Ensure dual authority is required for critical operations."
    artefact: "config.json"
    check_type: "json_path"
    params:
      path: "$.security.critical_operations.requires_dual_authority"
      expected_value: true
    remediation:
      - level: 1
        type: "template"
        description: "Template for a compliant security policy."
        path: "templates/dual_authority_policy.md"
      - level: 2
        type: "patch"
        description: "Patch to enable dual authority in the config file."
        patch: "..."
```

---

## 5.0 Market Positioning

- **Target Audience:** Developers, DevOps engineers, compliance officers, and security auditors.
- **Value Proposition:** "Assess your system's compliance with any standard, without vendor lock-in or data custody."
- **Distribution:** Open-core model. The CLI tool is free and open-source. Pre-built standard packs (e.g., for EU AI Act, ISO 27001) and the optional UI are commercial offerings.

---

## 6.0 What This Product Is NOT

- It is **not** a continuous monitoring platform.
- It is **not** an automated enforcement engine.
- It is **not** a SaaS product that requires you to upload your data to the cloud.

**It is a diagnostic instrument. You remain in control.**

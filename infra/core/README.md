# Sovereign Infrastructure - Season 2 Core

> *This system is not built to crown anyone. It is built to outlive its creator.*

---

## Overview

This repository contains the **Season 2 Core** of the Sovereign Infrastructure project. Season 2 represents the **free, open, and stable proof layer** that establishes trust and legitimacy before any monetisation occurs.

**Status:** Sealed and Frozen.

---

## Repository Structure

```
sovereign-infra/
├── .vscode/                 # VS Code configuration
├── .idea/                   # JetBrains IDE configuration
├── code/
│   └── gmail_local_agent.py # Local-compatible Gmail agent (Standard Google API)
├── governance/
│   ├── season_2_charter.md  # 1-Page North Star document
│   └── governance_build_checklist.md
├── presentations/
│   ├── governance_alignment/ # 11-slide stakeholder deck
│   └── executive_summary/    # 3-slide exec summary
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

---

## Getting Started

### Prerequisites

*   Python 3.11+
*   A Google Cloud project with the Gmail API enabled.
*   OAuth 2.0 credentials (`credentials.json`) from Google Cloud Console.

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/PrecisePointway/sovereign-infra.git
    cd sovereign-infra
    ```

2.  Create a virtual environment and install dependencies:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  Place your `credentials.json` file in the root directory.

4.  Run the Gmail Local Agent:
    ```bash
    python code/gmail_local_agent.py
    ```
    The first run will open a browser window for OAuth authorization.

---

## IDE Setup

### VS Code

Open the project folder in VS Code. Recommended extensions will be suggested automatically. Use the pre-configured launch configuration to run and debug the agent.

### JetBrains (PyCharm / IntelliJ)

Open the project folder in PyCharm. The run configuration `gmail_local_agent` is pre-configured and ready to use.

---

## Season Structure

| Season | Purpose | Status |
| :--- | :--- | :--- |
| **Season 2** | Free Core: Proof, trust, legitimacy. | **Sealed** |
| **Season 3** | Paid Bolt-Ons: Operationalisation, deployment, scale. | Pending Demand |

---

## License

This project is source-available. See the `governance/season_2_charter.md` for the operating principles.

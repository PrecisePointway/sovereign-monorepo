# The Sovereign Protocol: Year 1 Technical Execution Plan

This document provides a detailed breakdown of the technical milestones, deliverables, and acceptance criteria for **Year 1: The Foundation & The Conscience**. The overarching goal is to deliver an **Accountable MVP**—a system that is functional, auditable, honest, accessible, and demonstrably safe.

---

## Quarter 1: The Constitutional Engine

**Theme:** Establish the bedrock of truth. This quarter is focused on deploying the core data stack and ensuring every piece of data is ingested, transformed, and stored in a reliable and repeatable manner.

| Milestone | Technical Specification | Deliverable | Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **1.1: Infrastructure Deployment** | Deploy a production-grade Kubernetes cluster (e.g., AWS EKS) and a development environment using Docker Compose. Infrastructure as Code (IaC) will be managed via Terraform. | Fully version-controlled IaC repository (Terraform). Deployed dev and prod environments. | `terraform apply` successfully provisions all required resources. Dev environment is accessible to the engineering team. |
| **1.2: Core Data Stack** | Deploy PostgreSQL (for data warehousing), Airbyte (for ELT), dbt (for transformation), and Metabase (for BI) into the Kubernetes cluster. | Helm charts for each application. Running instances of all four core services. | All services are reachable via internal network endpoints. Health checks for all services are green. |
| **1.3: Initial Data Ingestion** | Configure Airbyte to connect to at least two critical data sources (e.g., primary financial account, core operational spreadsheet). Data syncs are scheduled to run hourly. | Two active, scheduled Airbyte connectors. Raw data tables populated in the Postgres data warehouse. | Raw tables in Postgres are updated within one hour of a change in the source system. Sync success rate is >98%. |
| **1.4: Foundational dbt Models** | Create a dbt project with staging models for the raw source data and initial transformation models for calculating core KPIs (e.g., Burn Rate, Runway). | A dbt project in a Git repository. At least two core KPI models. | `dbt run` and `dbt test` complete successfully. dbt-generated documentation is published and accessible. |

**End of Q1 State:** A functioning, end-to-end data pipeline exists. Data flows automatically from source systems into a data warehouse, is transformed, and is ready for visualization.

---

## Quarter 2: The Log & The Ledger

**Theme:** Make the system accountable. This quarter focuses on building the immutable audit trail for all governance actions, establishing the principle that every change is authorized and recorded.

| Milestone | Technical Specification | Deliverable | Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **2.1: Immutable Ledger Deployment** | Deploy Amazon QLDB as the immutable ledger for governance actions. Define the core journal schema (e.g., `action_id`, `timestamp`, `actor`, `action_type`, `details_hash`). | A provisioned QLDB instance. A document defining the journal schema. | The QLDB ledger is accessible via the AWS SDK. The schema is committed to the project's documentation repository. |
| **2.2: Governance Logger Service** | Create a dedicated microservice (`governance-logger`) with a single, secured API endpoint. This service is responsible for receiving governance action events and writing them to QLDB. | A containerized microservice deployed in the K8s cluster. OpenAPI specification for the logging endpoint. | The service can successfully write a well-formed event to QLDB. The endpoint returns a `202 Accepted` status upon receiving a valid event. |
| **2.3: Human Quorum Implementation** | Implement the M-of-N human quorum signing logic. This will be a separate service (`quorum-signer`) that exposes an API to propose a transaction and another to add a signature. A transaction is only marked `EXECUTABLE` after M signatures are collected. | A containerized `quorum-signer` microservice. A secure vault (HashiCorp Vault) for storing the private keys of the human operators. | A proposed transaction remains in a `PENDING` state with fewer than M signatures. A transaction moves to `EXECUTABLE` state after M signatures are verified. |
| **2.4: Initial Dashboard & Logging** | Create the first Sovereign Dashboard in Metabase, visualizing the core KPIs from the dbt models. Any administrative action taken within Metabase (e.g., changing a widget) must fire an event to the `governance-logger`. | A Metabase dashboard with at least two KPI widgets. A log entry in QLDB corresponding to the creation of the dashboard. | The dashboard accurately reflects the data in the dbt models. An immutable record of the dashboard's creation exists in the QLDB ledger. |

**End of Q2 State:** The system is now auditable. The first version of the dashboard is live, and any changes to its structure are logged immutably. The technical foundation for human-in-the-loop governance is in place.

---

## Quarter 3: The Balance Sheet & The Mandate

**Theme:** Make the system honest and accessible. This quarter is dedicated to enhancing the user interface to be transparent about uncertainty and inclusive by design.

| Milestone | Technical Specification | Deliverable | Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **3.1: Truth Balance Sheet - Backend** | Extend the dbt models to calculate a `confidence_score` for each KPI. The score is a function of source data freshness, known error rates (stored in a dbt seed file), and pipeline execution duration. The API serving the dashboard is updated to include this score. | Updated dbt models with confidence score logic. The API response for each KPI now includes a `value` and a `confidence_score` field. | The confidence score for a KPI drops if its underlying data source has not been updated recently. The API consistently serves the score. |
| **3.2: Truth Balance Sheet - Frontend** | The Metabase dashboard is customized. A JavaScript snippet reads the `confidence_score` for each KPI and dynamically applies a CSS class to gray out any value where the score is below 99.9%. | A custom Metabase frontend component. A visual change on the dashboard when data is stale. | A KPI with a confidence score of 99.8% is visibly grayed out and includes a tooltip explaining the reason for the low confidence. |
| **3.3: Clarity Mandate - Low-Stimulus UI** | Develop a separate, lightweight frontend application (e.g., using Vite + React) that provides a text-only, high-contrast view of the core KPIs. This app reads from a new, simplified API endpoint. | A deployed web application at a separate URL (e.g., `simple.sovereign.system`). A new API endpoint serving only essential data. | The low-stimulus UI displays the same core KPI values as the main dashboard but without any graphical elements. The UI passes WCAG 2.1 AA accessibility checks. |
| **3.4: Clarity Mandate - Cognitive Support** | Implement the simplified summary and cognitive cool-down features. A small, fine-tuned NLP model (e.g., T5-small) is deployed as a microservice to generate one-sentence summaries for any proposed governance action. The frontend tracks interaction velocity and triggers a cool-down modal if thresholds are breached. | A `summarizer` microservice. A frontend modal component for the cool-down protocol. | A complex governance proposal (e.g., "add new user with read-only access to financial data") is accompanied by a summary: "This action would let a new person see financial numbers." |

**End of Q3 State:** The system is now honest and inclusive. It visually communicates its own uncertainty and provides alternative interfaces for users who need or prefer them.

---

## Quarter 4: The Guardian Protocol

**Theme:** Give the system a conscience. This final quarter is dedicated to building the most critical ethical constraint: the automated veto for actions that could harm the vulnerable.

| Milestone | Technical Specification | Deliverable | Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **4.1: Harm Model Scaffolding** | Deploy a dedicated service (`guardian-protocol`) that acts as a policy engine. Initially, it will use a simple, static ruleset based on known harmful patterns (e.g., block any governance change that grants public access to a private data source). | A deployed `guardian-protocol` microservice with a policy endpoint. A Git repository containing the initial ruleset in a simple format (e.g., YAML). | The service correctly returns a `VETO` decision for a governance proposal that matches a rule in the static ruleset. |
| **4.2: Predictive Engine Integration (Spike)** | Conduct a technical spike to integrate a pre-trained predictive model. This involves setting up a Python environment with a GNN library (e.g., PyTorch Geometric) and loading a pre-trained model that can classify a proposed governance action as potentially harmful. | A research report detailing the performance of the pre-trained model on historical data. A functional, non-production prototype of the `guardian-protocol` service using the ML model. | The prototype correctly identifies at least one known historical 
governance failure mode from a test set. |
| **4.3: Governance Workflow Integration** | The `quorum-signer` service is modified. Before a transaction can be moved to the `EXECUTABLE` state, it must first be sent to the `guardian-protocol` service for approval. If the Guardian returns a `VETO`, the transaction is permanently moved to a `REJECTED` state and cannot be enacted. | Updated `quorum-signer` service. Sequence diagrams showing the updated governance workflow. | A governance proposal that receives a `VETO` from the Guardian cannot be signed or executed by the human quorum. The rejection is logged immutably in QLDB. |
| **4.4: Final Integration & System Seal** | All services are deployed to the production environment with final configurations. Kubernetes network policies are tightened to restrict all inter-service communication to the minimum required. All administrative access to the underlying infrastructure is placed behind a break-glass emergency protocol. | A "Year 1 System Seal" document, cryptographically signed by the founder, attesting that the system meets all Year 1 requirements. | A full end-to-end test passes: A change in a source system is reflected in the dashboard; a governance change is proposed, signed by the quorum, approved by the Guardian, and logged in QLDB; a harmful change is proposed and correctly vetoed. |

**End of Q4 State:** The **Accountable MVP** is live and sealed. It is a functional data and governance platform that is auditable by design, transparent about its own limitations, accessible to a wide range of users, and hard-coded with a non-negotiable ethical constraint to prevent harm. The foundation is complete. The conscience is active. The system is ready for Year 2.

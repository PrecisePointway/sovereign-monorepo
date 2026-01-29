# AGRICOOP — FARMER-FACING MVP SPECIFICATION

**Version:** 1.0  
**Date:** 2026-01-27  
**Target:** Phase 1 Pilot (2026-2027)  
**Alignment:** Sanctuary + H.U.G.

---

## EXECUTIVE SUMMARY

AgriCoop MVP delivers **three core tools** to a pilot cooperative:

1. **Coordination Hub** — Member management, voting, scheduling
2. **Contribution Ledger** — Evidence of deliveries and compliance
3. **Order Aggregator** — Consumer demand visibility

**No AI decisions. No trust scores. No optimization of humans.**

---

## TARGET USER

| User Type | Need |
|-----------|------|
| **Cooperative Manager** | Reduce admin, coordinate logistics |
| **Farmer Member** | Record contributions, see schedules |
| **Consumer** | Place orders, see provenance |

---

## MVP SCOPE

### In Scope (Phase 1)

| Feature | Description |
|---------|-------------|
| Member registry | Add/remove members, assign roles |
| Voting system | Create ballots, record votes, check quorum |
| Delivery logging | Record what was delivered, when, by whom |
| Compliance evidence | Upload certifications, inspection records |
| Order collection | Consumers place explicit orders |
| Demand dashboard | Cooperatives see aggregated demand |
| Provenance display | QR code links to contribution ledger |

### Out of Scope (Phase 1)

| Feature | Reason |
|---------|--------|
| AI recommendations | Violates "system never decides" |
| Trust/reputation scores | Violates "humans judge, system records" |
| Price optimization | Violates "no optimization of humans" |
| Predictive analytics | Not needed for MVP |
| Payment processing | Use existing systems |

---

## TECHNICAL ARCHITECTURE

### Stack (Sanctuary-Aligned)

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Frontend | HTMX + Alpine.js | No build step, low complexity |
| Backend | FastAPI (Python) | Native integration with Sanctuary |
| Database | PostgreSQL | Reliable, self-hosted |
| Ledger | Hash-chain (local) | Evidence integrity |
| Auth | Passkeys + backup codes | No passwords, no biometrics |
| Hosting | Self-hosted or VPS | Sovereign, no SaaS dependency |

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      AGRICOOP MVP                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Coordination│  │ Contribution│  │    Order    │         │
│  │     Hub     │  │   Ledger    │  │  Aggregator │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          │                                  │
│                  ┌───────▼───────┐                          │
│                  │   FastAPI     │                          │
│                  │   Backend     │                          │
│                  └───────┬───────┘                          │
│                          │                                  │
│         ┌────────────────┼────────────────┐                 │
│         │                │                │                 │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐         │
│  │  PostgreSQL │  │ Hash-Chain  │  │  S.A.F.E.-OS│         │
│  │  (Records)  │  │  (Evidence) │  │ (Governance)│         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## MODULE SPECIFICATIONS

### Module 1: Coordination Hub

**Purpose:** Member management and cooperative logistics

#### 1.1 Member Registry

```python
class Member:
    id: UUID
    name: str
    role: Enum["farmer", "manager", "observer"]
    public_key: str  # For signing
    joined_at: datetime
    status: Enum["active", "suspended", "withdrawn"]
```

**Operations:**
- `add_member(name, role)` — Manager only
- `suspend_member(id, reason)` — Requires vote
- `withdraw_member(id)` — Self-service

#### 1.2 Voting System

```python
class Ballot:
    id: UUID
    title: str
    options: List[str]
    quorum_required: float  # e.g., 0.51
    deadline: datetime
    status: Enum["open", "closed", "passed", "failed"]

class Vote:
    ballot_id: UUID
    member_id: UUID
    choice: str
    signature: str  # Signed with member key
    timestamp: datetime
```

**Operations:**
- `create_ballot(title, options, quorum, deadline)` — Manager only
- `cast_vote(ballot_id, choice)` — Any active member
- `close_ballot(ballot_id)` — Auto at deadline or manual

**Rules:**
- One vote per member per ballot
- Votes are signed and immutable
- Results are transparent to all members

#### 1.3 Scheduling

```python
class Schedule:
    id: UUID
    type: Enum["delivery", "pickup", "meeting", "inspection"]
    date: date
    time_window: Tuple[time, time]
    location: str
    assigned_members: List[UUID]
    status: Enum["scheduled", "completed", "cancelled"]
```

**Operations:**
- `create_schedule(type, date, time_window, location)`
- `assign_member(schedule_id, member_id)`
- `mark_complete(schedule_id, evidence_id)`

---

### Module 2: Contribution Ledger

**Purpose:** Evidence of deliveries and compliance

#### 2.1 Delivery Records

```python
class Delivery:
    id: UUID
    member_id: UUID
    date: datetime
    product: str
    quantity: float
    unit: str
    quality_grade: Optional[str]  # If inspected
    evidence_hash: str  # Photo, receipt, etc.
    recorded_by: UUID
    signature: str
```

**Operations:**
- `record_delivery(member_id, product, quantity, unit, evidence)`
- `query_deliveries(member_id, date_range)`
- `export_ledger(format)` — CSV, JSON, PDF

#### 2.2 Compliance Evidence

```python
class ComplianceRecord:
    id: UUID
    member_id: UUID
    type: Enum["organic_cert", "inspection", "training", "audit"]
    issued_by: str
    valid_from: date
    valid_until: date
    document_hash: str
    verified_by: Optional[UUID]
```

**Operations:**
- `upload_certification(member_id, type, document)`
- `verify_certification(record_id, verifier_id)`
- `check_compliance(member_id)` — Returns list of valid/expired certs

#### 2.3 Hash Chain

Every record is linked:

```
Record 1 → SHA256(Record1 + "GENESIS") → H1
Record 2 → SHA256(Record2 + H1) → H2
Record 3 → SHA256(Record3 + H2) → H3
```

**Properties:**
- Immutable
- Verifiable
- Tamper-evident
- Exportable for audit

---

### Module 3: Order Aggregator

**Purpose:** Consumer demand visibility

#### 3.1 Consumer Orders

```python
class Order:
    id: UUID
    consumer_id: UUID
    items: List[OrderItem]
    delivery_preference: Enum["pickup", "delivery"]
    status: Enum["pending", "confirmed", "fulfilled", "cancelled"]
    created_at: datetime

class OrderItem:
    product: str
    quantity: float
    unit: str
    max_price: Optional[float]  # Consumer's ceiling
```

**Operations:**
- `place_order(items, delivery_preference)`
- `confirm_order(order_id)` — After cooperative review
- `cancel_order(order_id)` — Before confirmation only

#### 3.2 Demand Dashboard

**For Cooperative Managers:**

```
┌─────────────────────────────────────────────────────────────┐
│                    DEMAND DASHBOARD                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Product        │ Total Demand │ Available │ Gap           │
│  ───────────────┼──────────────┼───────────┼───────────    │
│  Tomatoes       │ 500 kg       │ 450 kg    │ -50 kg        │
│  Potatoes       │ 300 kg       │ 400 kg    │ +100 kg       │
│  Eggs           │ 200 dozen    │ 180 dozen │ -20 dozen     │
│                                                             │
│  [Export CSV]  [Notify Members]  [Close Orders]            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**No recommendations. No optimization. Just visibility.**

#### 3.3 Provenance Display

**Consumer-facing QR code links to:**

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCT PROVENANCE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Product: Organic Tomatoes                                  │
│  Cooperative: Tenerife Valley Growers                       │
│  Farmer: [Name withheld — privacy]                          │
│  Harvested: 2026-01-25                                      │
│  Delivered: 2026-01-26                                      │
│  Certifications: Organic (valid), Food Safety (valid)       │
│                                                             │
│  Evidence Hash: a7b3c9d2...                                 │
│  Verify: [Link to ledger]                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## USER INTERFACE

### Design Principles

| Principle | Implementation |
|-----------|----------------|
| Low-tech friendly | Large buttons, simple language |
| Offline-capable | PWA with local storage |
| Multi-language | Spanish, English (Tenerife pilot) |
| Accessible | WCAG 2.1 AA compliance |
| No dark patterns | No nudges, no urgency tricks |

### Key Screens

1. **Dashboard** — Overview of schedules, pending votes, recent deliveries
2. **Members** — List, add, suspend (manager only)
3. **Voting** — Active ballots, cast vote, results
4. **Deliveries** — Log delivery, view history
5. **Compliance** — Upload cert, check status
6. **Orders** — View demand, confirm orders
7. **Settings** — Profile, keys, language

---

## DEPLOYMENT

### Requirements

| Resource | Minimum |
|----------|---------|
| Server | 2 vCPU, 4GB RAM, 50GB SSD |
| Database | PostgreSQL 15+ |
| SSL | Required (Let's Encrypt) |
| Backup | Daily, offsite |

### Installation

```bash
# Clone
git clone https://github.com/PrecisePointway/agricoop.git
cd agricoop

# Configure
cp .env.example .env
vim .env  # Set database, secrets

# Deploy
docker-compose up -d

# Initialize
python manage.py migrate
python manage.py createsuperuser
```

---

## PILOT PLAN

### Timeline

| Phase | Duration | Focus |
|-------|----------|-------|
| **Alpha** | 4 weeks | Core team testing |
| **Beta** | 8 weeks | 5-10 farmer pilot |
| **Launch** | Ongoing | Full cooperative |

### Success Metrics

| Metric | Target |
|--------|--------|
| Deliveries logged | 90%+ of actual deliveries |
| Votes cast | 70%+ participation |
| Orders fulfilled | 80%+ on time |
| User satisfaction | "Would recommend" > 80% |

### Feedback Loop

- Weekly check-ins with pilot farmers
- Monthly review with cooperative board
- Continuous iteration based on evidence

---

## SANCTUARY COMPLIANCE CHECKLIST

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| No AI decisions | System only displays, humans decide | ✓ |
| No trust scores | Contribution ledger, not reputation | ✓ |
| No optimization of humans | Logistics only | ✓ |
| Evidence-first | Hash-chain ledger | ✓ |
| Fail-closed | Requires explicit approval | ✓ |
| Data sovereignty | Self-hosted, exportable | ✓ |
| Explainable | All actions logged with reason | ✓ |

---

## NEXT STEPS

1. **Create Git repository** — `agricoop`
2. **Scaffold FastAPI project** — With S.A.F.E.-OS integration
3. **Build Module 1** — Coordination Hub
4. **Build Module 2** — Contribution Ledger
5. **Build Module 3** — Order Aggregator
6. **Deploy to pilot** — Tenerife cooperative

---

## CANONICAL CLOSURE

This MVP specification defines the scope and boundaries for AgriCoop Phase 1.

**The system serves farmers. Farmers remain sovereign.**

> **AgriCoop does not automate farming. It automates coordination, verification, and logistics so farmers can farm.**

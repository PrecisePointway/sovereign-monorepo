# Sovereign Sanctuary Elite - Deployment Guide

**Version:** 2.0.0
**Date:** 2026-01-25
**Author:** Manus AI for Architect

---

## 1. Prerequisites

Before deploying the Sovereign Sanctuary Elite system, ensure the following prerequisites are met:

### 1.1 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Disk | 20 GB | 50+ GB SSD |
| OS | Ubuntu 22.04 / Windows 11 | Ubuntu 22.04 LTS |
| Python | 3.10+ | 3.11+ |
| Node.js | 18+ | 22 LTS |

### 1.2 Network Requirements

- Tailscale installed and configured (for multi-node deployment)
- Outbound HTTPS access to OpenAI API
- SSH access between nodes (port 22)

### 1.3 Required Credentials

Create a `.env` file with the following:

```env
# Agent signing key (generate with: openssl rand -hex 32)
AGENT_SIGNING_KEY="your-64-character-hex-key"

# OpenAI API key
OPENAI_API_KEY="sk-..."

# Optional: Agent identity
AGENT_ID="agent-pr-reviewer-v2"
```

---

## 2. Installation

### 2.1 Clone Repository

```bash
git clone https://github.com/YOUR_ORG/sovereign-sanctuary-elite.git
cd sovereign-sanctuary-elite
```

### 2.2 Python Environment Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -e .[dev]
```

### 2.3 Node.js Environment Setup

```bash
# Install Node dependencies
pnpm install

# Build TypeScript
pnpm build
```

### 2.4 Configuration

Copy and customize the configuration:

```bash
cp config/swarm_config.example.json config/swarm_config.json
```

Edit `config/swarm_config.json` to match your node topology.

---

## 3. Single-Node Deployment

For development or single-machine deployments:

### 3.1 Start Self-Heal Monitor

```bash
# Start with default 60-second interval
sanctuary-heal

# Or with custom interval
sanctuary-heal --interval 30 --config config/swarm_config.json
```

### 3.2 Start Flight Control Daemon

```bash
# Start file watcher
sanctuary-flight --verbose
```

### 3.3 Verify Installation

```bash
# Check health endpoint
curl http://localhost:5001/health

# Run test suite
pytest
pnpm test
```

---

## 4. Multi-Node Deployment

For production deployments across multiple nodes:

### 4.1 Node Configuration

Update `config/swarm_config.json` with your node IPs:

```json
{
  "nodes": {
    "controller": {
      "ip": "100.94.217.80",
      "role": "controller",
      "port": 22
    },
    "pc1_blade": {
      "ip": "100.94.217.81",
      "role": "primary",
      "port": 22
    },
    "pc2_echo": {
      "ip": "100.94.217.82",
      "role": "compute",
      "port": 22
    }
  }
}
```

### 4.2 Deploy to Each Node

Use the push system to deploy:

```bash
python scripts/push_system.py --target all --method git
```

### 4.3 Start Services on Each Node

On each node, start the appropriate services:

**Controller Node:**
```bash
sanctuary-heal --interval 30
sanctuary-flight
```

**Compute Nodes:**
```bash
sanctuary-heal --interval 60
```

---

## 5. Systemd Service Installation (Linux)

### 5.1 Create Service File

```bash
sudo cp scripts/self_activation/sovereign-sanctuary.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 5.2 Enable and Start

```bash
sudo systemctl enable sovereign-sanctuary
sudo systemctl start sovereign-sanctuary
```

### 5.3 Check Status

```bash
sudo systemctl status sovereign-sanctuary
journalctl -u sovereign-sanctuary -f
```

---

## 6. Windows Service Installation

### 6.1 Install as Service

Run PowerShell as Administrator:

```powershell
.\scripts\self_activation\Sovereign-Service.ps1 -Install
```

### 6.2 Start Service

```powershell
Start-Service SovereignSanctuary
```

---

## 7. Verification Checklist

After deployment, verify the following:

| Check | Command | Expected Result |
|-------|---------|-----------------|
| Self-heal running | `ps aux \| grep self_heal` | Process active |
| Flight control running | `ps aux \| grep flight_control` | Process active |
| SITREP updated | `cat evidence/SITREP.md` | Recent timestamp |
| Nodes reachable | `ping 100.94.217.81` | Response received |
| Ledger writable | `echo "test" >> evidence/ledger.jsonl` | No error |

---

## 8. Troubleshooting

### 8.1 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "psutil not available" | Missing dependency | `pip install psutil` |
| "watchdog not installed" | Missing dependency | `pip install watchdog` |
| Node unreachable | Tailscale not connected | `tailscale up` |
| Signature verification failed | Wrong signing key | Check `.env` file |

### 8.2 Log Locations

- Self-heal logs: `logs/self_heal.log`
- Flight control: stdout (or redirect to file)
- Evidence ledger: `evidence/ledger.jsonl`
- Learn database: `evidence/learn_db.jsonl`

---

## 9. Backup and Recovery

### 9.1 Critical Files to Backup

```
evidence/
├── ledger.jsonl      # Audit trail (CRITICAL)
├── learn_db.jsonl    # Learning patterns
└── SITREP.md         # Status board

config/
└── swarm_config.json # Node configuration
```

### 9.2 Recovery Procedure

1. Stop all services
2. Restore `evidence/` directory from backup
3. Verify ledger integrity: `sha256sum evidence/ledger.jsonl`
4. Restart services

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 2.0.0 | 2026-01-25 | Manus AI | Initial deployment guide |

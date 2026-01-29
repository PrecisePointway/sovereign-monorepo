# Sovereign Agent

**ND/ADHD-Optimized Agentic Automation Framework**

A personal automation system designed specifically for neurodivergent operators. Reduces cognitive load, eliminates decision fatigue, and automates routine tasks while preserving human autonomy.

---

## Core Principles

1. **Zero Decision Fatigue** — System makes routine decisions automatically
2. **External Brain** — Never lose context, always know where you left off
3. **Body Doubling** — Ambient awareness without judgment
4. **Hyperfocus Protection** — Queue interruptions during deep work
5. **Transition Support** — Clear task boundaries, explicit "done" signals
6. **Overwhelm Prevention** — One task at a time, automatic intervention

---

## Quick Start

```bash
# Install
cd /home/ubuntu/sovereign_agent
chmod +x main.py

# Create alias
echo 'alias sa="python3 /home/ubuntu/sovereign_agent/main.py"' >> ~/.bashrc
source ~/.bashrc

# Start your day
sa start

# Enter focus mode
sa focus 90

# Quick capture a task
sa task "Review deployment"

# Complete current task
sa done

# Check status
sa status
```

---

## Components

### Core Modules

| Module | Purpose |
|--------|---------|
| `core/task_queue.py` | ND/ADHD-optimized task management |
| `agents/social_agent.py` | Automated social media posting |
| `agents/reminder_agent.py` | Gentle, non-judgmental reminders |
| `nd_support/cognitive_support.py` | Cognitive load monitoring |
| `integrations/system_hub.py` | Unified control hub |

### ND/ADHD Features

| Feature | Description |
|---------|-------------|
| One Task View | See only ONE task at a time |
| Context Preservation | Never lose where you left off |
| Micro-Actions | Smallest possible next step |
| Overwhelm Detection | Automatic intervention when overloaded |
| Focus Mode | Queue non-critical interruptions |
| Energy Matching | Match tasks to current energy level |
| Snooze Without Guilt | Snoozing is okay, no judgment |

---

## Commands

### Daily Routines

```bash
sa start          # Morning startup
sa end            # Evening shutdown
```

### Focus Management

```bash
sa focus          # Enter focus mode (90 min default)
sa focus 45       # Enter focus mode (45 min)
sa unfocus        # Exit focus mode
```

### Task Management

```bash
sa task "Do the thing"    # Quick capture
sa done                   # Complete current task
sa done abc123            # Complete specific task
```

### Social Media

```bash
sa post linkedin "New release!"
sa post twitter "Thread incoming"
```

### Monitoring

```bash
sa status         # Full system status
sa overwhelm      # Check for overwhelm
sa health         # Set up health protocol
```

---

## Integration with Existing Systems

### Manus Bridge (Gesture Commands)

```python
from integrations.system_hub import SovereignAgentHub

hub = SovereignAgentHub()

# Handle gesture from Manus Bridge
result = hub.handle_gesture("thumbs_up")  # Completes current task
result = hub.handle_gesture("fist")       # Enters focus mode
result = hub.handle_gesture("open_palm")  # Takes a break
```

### S.A.F.E.-OS (Governance)

The agent respects S.A.F.E.-OS governance rules:
- All notifications pass through Language Safety Gate
- Content policy enforced on social posts
- Audit trail maintained for all actions

### Health Protocol

```bash
sa health         # Set up all health reminders

# Or programmatically:
hub.log_health_event("peptides", "Morning dose complete")
```

---

## Cognitive Load Monitoring

The system tracks:
- Task switches
- Decisions made
- Time since break
- Incomplete tasks
- Context switches

When load exceeds thresholds:
1. **Elevated** — Gentle notice
2. **High** — Intervention suggested
3. **Overwhelmed** — Immediate intervention

Interventions are **non-judgmental** and **action-oriented**.

---

## Configuration

### Environment Variables

```bash
# Social Media (optional)
export LINKEDIN_ACCESS_TOKEN="..."
export TWITTER_API_KEY="..."
export TWITTER_API_SECRET="..."
export TWITTER_ACCESS_TOKEN="..."
export TWITTER_ACCESS_SECRET="..."
```

### Data Storage

Default: `/var/lib/sovereign_agent/`

```
sovereign_agent/
├── tasks.json
├── social.json
├── reminders.json
├── cognitive.json
└── hub_state.json
```

---

## Systemd Service

```ini
# /etc/systemd/system/sovereign-agent.service
[Unit]
Description=Sovereign Agent
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/sovereign_agent
ExecStart=/usr/bin/python3 main.py daemon
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

---

## Philosophy

This system is built on the understanding that:

1. **ND brains work differently** — not worse, differently
2. **External structure helps** — the system provides what the brain doesn't
3. **Shame doesn't help** — all feedback is non-judgmental
4. **Flexibility matters** — snooze, defer, reschedule without guilt
5. **One thing at a time** — reduces overwhelm, increases completion

The goal is **sovereignty over your own attention and time**.

---

## License

Part of Sovereign Sanctuary Systems.
Governed by the Sovereign Sanctuary Codex v1.0.

---

*"Tools that serve. No extraction. No manipulation."*

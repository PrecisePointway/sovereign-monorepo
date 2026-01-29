# **Manus Pro Gesture Protocol**

**Sovereign Elite OS — Gesture-Driven Command Interface**

---

## **Overview**

This package provides a complete gesture-to-command routing system for the Manus Pro motion capture gloves, enabling deterministic infrastructure control through physical gestures.

---

## **Directory Structure**

```
manus_gesture_protocol/
├── README.md                    # This file
├── gesture_protocol.yaml        # Gesture → command mapping
├── manus_bridge.py              # Core router (Python)
├── manus_bridge.service         # Systemd unit file
├── docs/
│   └── JARVIS_Architecture_Reference.md
└── scripts/
    ├── generate_snapshot.sh     # Evidence capture
    ├── airbyte_sync.py          # Data pipeline trigger
    ├── open_dashboard.sh        # Metabase launcher
    ├── slack_alert.py           # Compliance notification
    ├── controlled_shutdown.sh   # Node-safe shutdown
    ├── metabase_control.py      # Dashboard tab control
    ├── health_log.py            # Health protocol logging
    └── gesture_audit.py         # Audit trail generator
```

---

## **Quick Start**

### **1. Install Dependencies**

```bash
sudo pip3 install pyyaml requests
```

### **2. Deploy to Target Directory**

```bash
sudo mkdir -p /opt/sovereign-os
sudo cp -r * /opt/sovereign-os/
cd /opt/sovereign-os
```

### **3. Set Permissions**

```bash
chmod +x scripts/*.sh scripts/*.py
chmod +x manus_bridge.py
```

### **4. Create Log Directory**

```bash
sudo mkdir -p /var/log/manus_gesture
sudo chown $USER:$USER /var/log/manus_gesture
```

### **5. Configure Environment**

Create `/opt/sovereign-os/.env`:

```bash
# Airbyte
AIRBYTE_HOST=http://localhost:8000
AIRBYTE_CONNECTION_ID=your-connection-id

# Metabase
METABASE_HOST=http://localhost:3000
METABASE_DASHBOARD_IDS=1,2,3

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz

# Docker
DOCKER_COMPOSE_DIR=/opt/sovereign-os

# Snapshots
SNAPSHOT_DIR=/var/snapshots
```

### **6. Install Systemd Service**

```bash
sudo cp manus_bridge.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable manus_bridge
sudo systemctl start manus_bridge
```

### **7. Verify**

```bash
sudo systemctl status manus_bridge
journalctl -u manus_bridge -f
```

---

## **Gesture Command Map**

| Gesture | Action | Script |
|---------|--------|--------|
| `fist_hold` | Generate evidence snapshot | `generate_snapshot.sh` |
| `two_finger_swipe_up` | Trigger Airbyte sync | `airbyte_sync.py` |
| `open_palm_hold` | Open Metabase dashboard | `open_dashboard.sh` |
| `thumb_circle` | Send Slack P1 alert | `slack_alert.py` |
| `pinch_twist` | Controlled shutdown | `controlled_shutdown.sh` |
| `double_tap` | Switch dashboard tab / ACK | `metabase_control.py` |

---

## **Security Model**

- **Identity Enforcement:** All gestures rejected unless biometric hash verified
- **Fail-Closed:** On auth failure, input layer freezes (requires manual intervention)
- **Hash Chain:** All events logged with cryptographic linking
- **Session Timeout:** 30 minutes of inactivity requires re-authentication

---

## **Testing**

### **Test Mode (Simulated Gesture)**

```bash
python3 manus_bridge.py --config gesture_protocol.yaml --test --authorized-hashes "your-biometric-hash"
```

### **Manual Script Testing**

```bash
# Test snapshot
./scripts/generate_snapshot.sh

# Test health logging
python3 scripts/health_log.py vitals

# Test audit
python3 scripts/gesture_audit.py summary
```

---

## **Audit & Compliance**

### **Export Audit Trail**

```bash
python3 scripts/gesture_audit.py export
# Output: /var/log/manus_gesture/gesture_audit.csv
```

### **Verify Hash Chain Integrity**

```bash
python3 scripts/gesture_audit.py verify
```

### **View Recent Events**

```bash
python3 scripts/gesture_audit.py tail 20
```

---

## **Health Protocol Integration**

Log health events via gesture or CLI:

```bash
# Log morning peptides
python3 scripts/health_log.py peptides_am

# Log vitals check
python3 scripts/health_log.py vitals "BP 120/80, HR 65"

# View today's log
python3 scripts/health_log.py status
```

---

## **Logs**

| Log | Location |
|-----|----------|
| Bridge log | `/var/log/manus_gesture/manus_bridge.log` |
| Hash chain | `/var/log/manus_gesture/hash_chain.json` |
| Audit CSV | `/var/log/manus_gesture/gesture_audit.csv` |
| Health log | `/var/log/health_spring/health_log.csv` |
| Shutdown log | `/var/log/manus_gesture/shutdown.log` |

---

## **Architecture Reference**

See `docs/JARVIS_Architecture_Reference.md` for full system architecture mapping.

---

## **Version**

- **Protocol Version:** 1.0.0
- **Author:** Architect
- **Last Updated:** 2026-01-25

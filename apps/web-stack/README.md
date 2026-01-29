# **Sovereign Web Stack**

**Sovereign Infrastructure for Elite Operations**

Zero-Dependency. Deterministic. Auditable.

---

## **Overview**

Complete web infrastructure for Sovereign Sanctuary Systems with gesture-native integration via Manus Pro.

| Component | Description | Sovereignty |
|-----------|-------------|-------------|
| `wordpress-plugin/` | WordPress integration (transitional) | ⭐⭐⭐ |
| `hugo-site/` | Static site generator | ⭐⭐⭐⭐⭐ |
| `fastapi-app/` | Gesture-native application | ⭐⭐⭐⭐⭐ |
| `docs/` | Deployment documentation | — |

---

## **Quick Start**

### **Option 1: Full Sovereign Stack (Recommended)**

```bash
# Clone and deploy
cd /opt
git clone https://github.com/your-org/sovereign-web-stack.git
cd sovereign-web-stack/fastapi-app

# Configure
cp .env.example .env
vim .env  # Set your secrets

# Build Hugo site
cd ../hugo-site && hugo --minify

# Deploy
cd ../fastapi-app
docker-compose up -d
```

### **Option 2: WordPress Plugin Only**

```bash
# Copy plugin to WordPress
cp -r wordpress-plugin /var/www/html/wp-content/plugins/sovereign-elite-os

# Activate in WordPress admin
# Configure at Settings → Sovereign Elite OS
```

---

## **Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    SOVEREIGN WEB STACK                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   NGINX     │    │   FASTAPI   │    │   MANUS     │     │
│  │  (Static)   │◄──►│    (API)    │◄──►│   BRIDGE    │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                  │                  │             │
│         ▼                  ▼                  ▼             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │    HUGO     │    │  HASH CHAIN │    │   GESTURE   │     │
│  │   (Build)   │    │   (Audit)   │    │   EVENTS    │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## **Components**

### **FastAPI Application** (`fastapi-app/`)

Gesture-native web application with:

- Native WebSocket connection to Manus Bridge
- Hash-chained audit logging
- HTMX-powered interactive UI
- Content management API
- Real-time gesture event handling

**Key Files:**
- `main.py` — Application code
- `Dockerfile` — Container build
- `docker-compose.yml` — Full stack deployment
- `nginx.conf` — Reverse proxy configuration

### **Hugo Static Site** (`hugo-site/`)

Zero-attack-surface public website:

- Markdown content in Git
- Gesture-triggered rebuilds
- Build manifest with content hash
- Sovereign theme included

**Key Files:**
- `hugo.toml` — Site configuration
- `content/` — Markdown content
- `themes/sovereign-theme/` — Custom theme
- `scripts/gesture_build.sh` — Build automation

### **WordPress Plugin** (`wordpress-plugin/`)

Transitional integration for existing WordPress sites:

- REST API endpoints for gestures
- Hash-chained event logging
- Gesture-triggered publishing
- Content snapshots

**Key Files:**
- `sovereign-elite-os.php` — Plugin code
- `readme.txt` — WordPress readme

---

## **Gesture Integration**

### **Supported Gestures**

| Gesture | Action | Description |
|---------|--------|-------------|
| `two_finger_swipe_up` | `generate_snapshot` | Create system snapshot |
| `fist_hold` | `trigger_sync` | Trigger data sync |
| `open_palm_push` | `publish_content` | Publish pending content |
| `index_point_right` | `open_dashboard` | Open dashboard |
| `three_finger_tap` | `send_alert` | Send alert notification |

### **Webhook Payload**

```json
{
  "gesture_id": "two_finger_swipe_up",
  "action": "generate_snapshot",
  "confidence": 0.92,
  "timestamp": 1706284800.123,
  "biometric_hash": "sha256:abc123...",
  "device_mac": "AA:BB:CC:DD:EE:FF"
}
```

---

## **API Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System status |
| `/api/gesture` | POST | Receive gesture events |
| `/api/audit` | GET | View audit log |
| `/api/audit/verify` | GET | Verify hash chain integrity |
| `/api/snapshot` | POST | Create system snapshot |
| `/api/content` | GET | List content items |
| `/api/content` | POST | Create content item |
| `/ws` | WebSocket | Real-time updates |

---

## **Security**

### **Hash Chain Audit**

All events are logged to a cryptographic hash chain:

```
Event N → SHA256(Event + Hash(N-1) + Timestamp) → Hash N
```

Verify integrity:
```bash
curl http://localhost:8000/api/audit/verify
# {"valid": true, "length": 42, "status": "INTACT"}
```

### **Webhook Authentication**

HMAC-SHA256 signature verification:

```
X-Sovereign-Signature: HMAC(timestamp + "." + body, secret)
X-Sovereign-Timestamp: Unix timestamp
```

---

## **Deployment**

See [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for complete instructions.

### **Quick Commands**

```bash
# Start stack
docker-compose up -d

# View logs
docker-compose logs -f

# Rebuild Hugo
./hugo-site/scripts/gesture_build.sh deploy

# Verify audit chain
curl http://localhost:8000/api/audit/verify
```

---

## **License**

Proprietary — Sovereign Sanctuary Systems

---

## **Contact**

- **Domain:** sovereignsanctuarysystems.co.uk
- **Author:** Architect

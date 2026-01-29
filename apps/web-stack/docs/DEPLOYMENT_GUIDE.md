# **Sovereign Web Stack — Deployment Guide**

**Version:** 1.0.0
**Date:** 2026-01-26
**Author:** Architect

---

## **1. Overview**

This guide covers deployment of the complete Sovereign Web Stack for sovereignsanctuarysystems.co.uk:

| Component | Purpose | Sovereignty Score |
|-----------|---------|-------------------|
| **WordPress Plugin** | Transitional CMS integration | 5/10 |
| **Hugo Static Site** | Public content, zero attack surface | 9/10 |
| **FastAPI Application** | Gesture-native, full control | 10/10 |

**Recommended Path:** Deploy FastAPI + Hugo for maximum sovereignty, use WordPress plugin only if transitioning from existing WordPress installation.

---

## **2. Prerequisites**

### **2.1 Infrastructure**

- Linux server (Ubuntu 22.04+ recommended)
- Docker & Docker Compose
- Domain: sovereignsanctuarysystems.co.uk
- SSL certificate (Let's Encrypt or custom)

### **2.2 Software**

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Hugo (for static site builds)
sudo apt install hugo

# Install Python 3.11+ (for local development)
sudo apt install python3.11 python3.11-venv
```

### **2.3 DNS Configuration**

| Record | Type | Value |
|--------|------|-------|
| @ | A | Your server IP |
| www | CNAME | sovereignsanctuarysystems.co.uk |
| app | A | Your server IP (for FastAPI) |

---

## **3. Deployment Options**

### **Option A: Full Sovereign Stack (Recommended)**

FastAPI + Hugo + Nginx — Maximum sovereignty, gesture-native.

### **Option B: WordPress Transitional**

WordPress + Plugin — Use existing WordPress, add gesture integration.

### **Option C: Hybrid**

Hugo (public) + FastAPI (API/dashboard) + WordPress (blog/shop).

---

## **4. Option A: Full Sovereign Stack**

### **4.1 Clone Repository**

```bash
cd /opt
git clone https://github.com/your-org/sovereign-web-stack.git
cd sovereign-web-stack
```

### **4.2 Configure Environment**

```bash
# Create .env file
cat > fastapi-app/.env << 'EOF'
WEBHOOK_SECRET=your-secure-secret-here
MANUS_BRIDGE_URL=ws://manus-bridge:8765
LOG_DIR=/var/log/sovereign_app
EOF
```

### **4.3 Build Hugo Site**

```bash
cd hugo-site

# Build static site
hugo --minify

# Verify output
ls -la public/
```

### **4.4 Deploy with Docker Compose**

```bash
cd ../fastapi-app

# Build and start services
docker-compose up -d --build

# Verify services
docker-compose ps
docker-compose logs -f sovereign-app
```

### **4.5 Verify Deployment**

```bash
# Check API status
curl http://localhost:8000/api/status

# Check static site
curl http://localhost/

# Check health
curl http://localhost/health
```

### **4.6 SSL Configuration (Production)**

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d sovereignsanctuarysystems.co.uk -d www.sovereignsanctuarysystems.co.uk

# Auto-renewal
sudo systemctl enable certbot.timer
```

---

## **5. Option B: WordPress Plugin**

### **5.1 Install Plugin**

```bash
# Copy plugin to WordPress
cp -r wordpress-plugin /var/www/html/wp-content/plugins/sovereign-elite-os

# Set permissions
chown -R www-data:www-data /var/www/html/wp-content/plugins/sovereign-elite-os
```

### **5.2 Activate Plugin**

1. Log in to WordPress admin
2. Go to Plugins → Installed Plugins
3. Activate "Sovereign Elite OS Integration"

### **5.3 Configure Plugin**

1. Go to Settings → Sovereign Elite OS
2. Note the auto-generated Webhook Secret
3. Copy the Gesture Webhook URL
4. Configure Manus Bridge to send events to this URL

### **5.4 Test Integration**

```bash
# Test webhook endpoint
curl -X POST https://sovereignsanctuarysystems.co.uk/wp-json/sovereign/v1/status
```

---

## **6. Manus Bridge Integration**

### **6.1 Update gesture_protocol.yaml**

Add webhook targets for your deployment:

```yaml
# In gesture_protocol.yaml
webhooks:
  # FastAPI endpoint
  fastapi:
    url: "https://app.sovereignsanctuarysystems.co.uk/api/gesture"
    secret: "${WEBHOOK_SECRET}"
    
  # WordPress endpoint (if using)
  wordpress:
    url: "https://sovereignsanctuarysystems.co.uk/wp-json/sovereign/v1/gesture"
    secret: "${WP_WEBHOOK_SECRET}"
    
  # Hugo rebuild trigger
  hugo:
    url: "http://localhost:8080/hooks/hugo-rebuild"
    secret: "${HUGO_WEBHOOK_SECRET}"
```

### **6.2 Configure Manus Bridge**

```bash
# Update manus_bridge.py to send to webhooks
cd /opt/sovereign-os
vim manus_bridge.py

# Restart service
sudo systemctl restart manus_bridge
```

---

## **7. Hugo Gesture Webhook**

For gesture-triggered site rebuilds, set up a webhook listener:

### **7.1 Install Webhook**

```bash
sudo apt install webhook
```

### **7.2 Configure Webhook**

```bash
# /etc/webhook.conf
cat > /etc/webhook.conf << 'EOF'
[
  {
    "id": "hugo-rebuild",
    "execute-command": "/opt/sovereign-web-stack/hugo-site/scripts/gesture_build.sh",
    "command-working-directory": "/opt/sovereign-web-stack/hugo-site",
    "pass-arguments-to-command": [
      {
        "source": "string",
        "name": "deploy"
      }
    ],
    "trigger-rule": {
      "match": {
        "type": "value",
        "value": "your-webhook-secret",
        "parameter": {
          "source": "header",
          "name": "X-Webhook-Secret"
        }
      }
    }
  }
]
EOF
```

### **7.3 Start Webhook Service**

```bash
webhook -hooks /etc/webhook.conf -port 8080 -verbose
```

---

## **8. Monitoring & Maintenance**

### **8.1 Health Checks**

```bash
# FastAPI status
curl https://app.sovereignsanctuarysystems.co.uk/api/status

# Audit chain verification
curl https://app.sovereignsanctuarysystems.co.uk/api/audit/verify

# WordPress status (if using)
curl https://sovereignsanctuarysystems.co.uk/wp-json/sovereign/v1/status
```

### **8.2 Log Locations**

| Component | Log Path |
|-----------|----------|
| FastAPI | `/var/log/sovereign_app/app.log` |
| Nginx | `/var/log/nginx/access.log` |
| Manus Bridge | `/var/log/manus_gesture/bridge.log` |
| Docker | `docker-compose logs` |

### **8.3 Backup**

```bash
# Backup script
#!/bin/bash
BACKUP_DIR="/backup/sovereign/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# FastAPI data
docker cp sovereign-app:/var/log/sovereign_app "$BACKUP_DIR/logs"
docker cp sovereign-app:/app/content "$BACKUP_DIR/content"

# Hugo source
tar -czf "$BACKUP_DIR/hugo-site.tar.gz" /opt/sovereign-web-stack/hugo-site

# Hash chain (critical)
cp /var/log/sovereign_app/hash_chain.json "$BACKUP_DIR/"

echo "Backup complete: $BACKUP_DIR"
```

---

## **9. Migration from WordPress**

### **9.1 Export Content**

```bash
# Install WP-CLI
curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
chmod +x wp-cli.phar
sudo mv wp-cli.phar /usr/local/bin/wp

# Export posts to JSON
wp post list --format=json > wordpress_posts.json

# Export pages
wp post list --post_type=page --format=json > wordpress_pages.json
```

### **9.2 Convert to Hugo**

```python
#!/usr/bin/env python3
# convert_wp_to_hugo.py

import json
from pathlib import Path
from datetime import datetime

def convert_post(post, output_dir):
    slug = post['post_name']
    date = post['post_date'][:10]
    
    frontmatter = f"""---
title: "{post['post_title']}"
date: {date}
draft: false
---

"""
    
    content = frontmatter + post['post_content']
    
    output_path = output_dir / f"{slug}.md"
    output_path.write_text(content)
    print(f"Converted: {slug}")

# Load WordPress export
with open('wordpress_posts.json') as f:
    posts = json.load(f)

# Convert each post
output_dir = Path('hugo-site/content/posts')
output_dir.mkdir(parents=True, exist_ok=True)

for post in posts:
    convert_post(post, output_dir)
```

### **9.3 Verify Migration**

```bash
cd hugo-site
hugo server

# Open http://localhost:1313 and verify content
```

---

## **10. Security Checklist**

### **Pre-Deployment**

- [ ] Change all default secrets and passwords
- [ ] Configure firewall (UFW/iptables)
- [ ] Set up fail2ban
- [ ] Enable SSL/TLS
- [ ] Configure rate limiting

### **Post-Deployment**

- [ ] Verify hash chain integrity
- [ ] Test gesture authentication
- [ ] Review access logs
- [ ] Set up monitoring alerts
- [ ] Document recovery procedures

### **Ongoing**

- [ ] Weekly hash chain verification
- [ ] Monthly security updates
- [ ] Quarterly access review
- [ ] Annual penetration testing

---

## **11. Troubleshooting**

### **FastAPI Not Starting**

```bash
# Check logs
docker-compose logs sovereign-app

# Common issues:
# - Port 8000 already in use
# - Missing environment variables
# - Permission issues on log directory
```

### **Hugo Build Failing**

```bash
# Check Hugo version
hugo version

# Verbose build
hugo --verbose

# Common issues:
# - Missing theme
# - Invalid frontmatter
# - Template errors
```

### **Gesture Events Not Received**

```bash
# Check Manus Bridge connection
curl -X POST http://localhost:8000/api/gesture \
  -H "Content-Type: application/json" \
  -d '{"gesture_id":"test","action":"test","confidence":1.0,"timestamp":1234567890}'

# Check webhook secret matches
# Check network connectivity between services
```

---

## **12. Quick Reference**

### **Commands**

```bash
# Start stack
docker-compose up -d

# Stop stack
docker-compose down

# Rebuild Hugo
./scripts/gesture_build.sh deploy

# View logs
docker-compose logs -f

# Verify audit chain
curl http://localhost:8000/api/audit/verify

# Create snapshot
curl -X POST http://localhost:8000/api/snapshot
```

### **Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System status |
| `/api/gesture` | POST | Receive gesture events |
| `/api/audit` | GET | View audit log |
| `/api/audit/verify` | GET | Verify hash chain |
| `/api/snapshot` | POST | Create snapshot |
| `/api/content` | GET/POST | Content management |
| `/ws` | WebSocket | Real-time updates |

---

**End of Deployment Guide**

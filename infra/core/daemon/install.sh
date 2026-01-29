#!/bin/bash
# Sovereign Governance Daemon - Installation Script
# This script installs and configures the governance daemon for production use.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root"
    exit 1
fi

log_info "═══════════════════════════════════════════════════════════"
log_info "  Sovereign Governance Daemon Installation"
log_info "═══════════════════════════════════════════════════════════"

# Create sovereign user if not exists
if ! id "sovereign" &>/dev/null; then
    log_info "Creating sovereign user..."
    useradd --system --no-create-home --shell /bin/false sovereign
fi

# Create directories
log_info "Creating directories..."
mkdir -p /opt/sovereign/daemon
mkdir -p /var/lib/sovereign
mkdir -p /var/log/sovereign
mkdir -p /var/run/sovereign
mkdir -p /etc/sovereign

# Set ownership
chown -R sovereign:sovereign /var/lib/sovereign
chown -R sovereign:sovereign /var/log/sovereign
chown -R sovereign:sovereign /var/run/sovereign

# Copy daemon files
log_info "Installing daemon files..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR"/*.py /opt/sovereign/daemon/
chmod +x /opt/sovereign/daemon/governance_daemon.py
chmod +x /opt/sovereign/daemon/hug_protocol.py

# Install systemd service
log_info "Installing systemd service..."
cp "$SCRIPT_DIR/systemd/governance-daemon.service" /etc/systemd/system/
systemctl daemon-reload

# Create default constitution if not exists
if [[ ! -f /etc/sovereign/constitution.yaml ]]; then
    log_info "Creating default constitution..."
    cat > /etc/sovereign/constitution.yaml << 'EOF'
# Sovereign System Constitution
# =============================
# This file defines the constitutional rules that govern the system.
# Changes require board approval.

constitution_version: "1.0.0"
last_amended: "2026-01-28"

core_principles:
  - id: CP-001
    name: "Immutable Audit Trail"
    description: "All actions must be logged to the ledger with hash chain integrity"

  - id: CP-002
    name: "Human Oversight"
    description: "High-risk decisions require human approval"

  - id: CP-003
    name: "Constitutional Supremacy"
    description: "No agent or process may override the constitution"

  - id: CP-004
    name: "Deterministic Behavior"
    description: "Same inputs must produce same outputs in Phase 0"

  - id: CP-005
    name: "Graceful Degradation"
    description: "System must fail safely, never silently"

kill_switch:
  enabled: true
  authorized_triggers:
    - human_operator
    - governance_daemon
  requires_evidence: true
EOF
    chown sovereign:sovereign /etc/sovereign/constitution.yaml
fi

# Enable and start service
log_info "Enabling and starting service..."
systemctl enable governance-daemon.service
systemctl start governance-daemon.service

# Verify installation
log_info "Verifying installation..."
sleep 2
if systemctl is-active --quiet governance-daemon.service; then
    log_info "✅ Governance daemon is running"
else
    log_error "❌ Governance daemon failed to start"
    log_error "Check logs: journalctl -u governance-daemon.service"
    exit 1
fi

log_info "═══════════════════════════════════════════════════════════"
log_info "  Installation Complete"
log_info "═══════════════════════════════════════════════════════════"
log_info ""
log_info "Commands:"
log_info "  Status:  systemctl status governance-daemon"
log_info "  Logs:    journalctl -u governance-daemon -f"
log_info "  Stop:    systemctl stop governance-daemon"
log_info "  Restart: systemctl restart governance-daemon"
log_info ""
log_info "Evidence ledger: /var/lib/sovereign/governance_ledger.jsonl"
log_info "Constitution:    /etc/sovereign/constitution.yaml"

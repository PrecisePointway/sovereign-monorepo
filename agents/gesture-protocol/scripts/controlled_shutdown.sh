#!/bin/bash
# ============================================================================
# CONTROLLED SHUTDOWN — Node-Safe Service Termination
# ============================================================================
# Triggered by: pinch_twist gesture (REQUIRES CONFIRMATION)
# Purpose: Initiate controlled service shutdown across defined nodes
# ============================================================================

set -euo pipefail

SHUTDOWN_LOG="/var/log/manus_gesture/shutdown.log"
DOCKER_COMPOSE_DIR="${DOCKER_COMPOSE_DIR:-/opt/sovereign-os}"
SHUTDOWN_MODE="${1:-services}"  # services | full | reboot

log() {
    echo "[SHUTDOWN] $(date -Iseconds) | $1" | tee -a "${SHUTDOWN_LOG}"
}

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================

log "============================================"
log "CONTROLLED SHUTDOWN INITIATED"
log "Mode: ${SHUTDOWN_MODE}"
log "============================================"

# Ensure log directory exists
mkdir -p "$(dirname "${SHUTDOWN_LOG}")"

# ============================================================================
# SHUTDOWN SEQUENCE
# ============================================================================

case "${SHUTDOWN_MODE}" in
    services)
        # Stop Docker services only
        log "Stopping Docker services..."
        
        if [ -f "${DOCKER_COMPOSE_DIR}/docker-compose.yml" ]; then
            cd "${DOCKER_COMPOSE_DIR}"
            docker-compose down --timeout 30 2>&1 | tee -a "${SHUTDOWN_LOG}"
            log "Docker services stopped"
        else
            log "No docker-compose.yml found at ${DOCKER_COMPOSE_DIR}"
        fi
        
        log "Service shutdown complete"
        ;;
        
    full)
        # Full system shutdown
        log "FULL SYSTEM SHUTDOWN REQUESTED"
        log "Stopping Docker services..."
        
        if [ -f "${DOCKER_COMPOSE_DIR}/docker-compose.yml" ]; then
            cd "${DOCKER_COMPOSE_DIR}"
            docker-compose down --timeout 30 2>&1 | tee -a "${SHUTDOWN_LOG}"
        fi
        
        log "Syncing filesystems..."
        sync
        
        log "Initiating system halt..."
        # Uncomment for production:
        # sudo shutdown -h now
        log "SIMULATION: shutdown -h now (uncomment in production)"
        ;;
        
    reboot)
        # System reboot
        log "SYSTEM REBOOT REQUESTED"
        log "Stopping Docker services..."
        
        if [ -f "${DOCKER_COMPOSE_DIR}/docker-compose.yml" ]; then
            cd "${DOCKER_COMPOSE_DIR}"
            docker-compose down --timeout 30 2>&1 | tee -a "${SHUTDOWN_LOG}"
        fi
        
        log "Syncing filesystems..."
        sync
        
        log "Initiating system reboot..."
        # Uncomment for production:
        # sudo shutdown -r now
        log "SIMULATION: shutdown -r now (uncomment in production)"
        ;;
        
    *)
        log "ERROR: Unknown shutdown mode: ${SHUTDOWN_MODE}"
        log "Valid modes: services | full | reboot"
        exit 1
        ;;
esac

log "============================================"
log "SHUTDOWN SEQUENCE COMPLETE"
log "============================================"

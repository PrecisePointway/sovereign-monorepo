#!/bin/bash
# ============================================================================
# GENERATE SNAPSHOT — Evidence Capture with Hash Chain
# ============================================================================
# Triggered by: fist_hold gesture
# Purpose: Full system snapshot with cryptographic integrity
# ============================================================================

set -euo pipefail

SNAPSHOT_DIR="${SNAPSHOT_DIR:-/var/snapshots}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SNAPSHOT_NAME="snapshot_${TIMESTAMP}"
SNAPSHOT_PATH="${SNAPSHOT_DIR}/${SNAPSHOT_NAME}"

echo "[SNAPSHOT] ============================================"
echo "[SNAPSHOT] Starting evidence snapshot: ${SNAPSHOT_NAME}"
echo "[SNAPSHOT] Timestamp: $(date -Iseconds)"
echo "[SNAPSHOT] ============================================"

# Create snapshot directory
mkdir -p "${SNAPSHOT_PATH}"

# 1. Capture system state
echo "[SNAPSHOT] Capturing system state..."
uname -a > "${SNAPSHOT_PATH}/system_info.txt"
df -h > "${SNAPSHOT_PATH}/disk_usage.txt"
docker ps -a > "${SNAPSHOT_PATH}/docker_containers.txt" 2>/dev/null || echo "Docker not available" > "${SNAPSHOT_PATH}/docker_containers.txt"
ps aux > "${SNAPSHOT_PATH}/processes.txt"

# 2. Capture network state
echo "[SNAPSHOT] Capturing network state..."
ip addr > "${SNAPSHOT_PATH}/network_interfaces.txt"
ss -tulpn > "${SNAPSHOT_PATH}/open_ports.txt" 2>/dev/null || netstat -tulpn > "${SNAPSHOT_PATH}/open_ports.txt"

# 3. Capture logs (last 1000 lines of key logs)
echo "[SNAPSHOT] Capturing recent logs..."
journalctl -n 1000 --no-pager > "${SNAPSHOT_PATH}/journal_recent.txt" 2>/dev/null || echo "journalctl not available" > "${SNAPSHOT_PATH}/journal_recent.txt"

# 4. Generate manifest with hashes
echo "[SNAPSHOT] Generating file manifest..."
find "${SNAPSHOT_PATH}" -type f -exec sha256sum {} \; > "${SNAPSHOT_PATH}/manifest.sha256"

# 5. Create tarball
echo "[SNAPSHOT] Creating archive..."
tar -czf "${SNAPSHOT_PATH}.tar.gz" -C "${SNAPSHOT_DIR}" "${SNAPSHOT_NAME}"

# 6. Generate final hash
FINAL_HASH=$(sha256sum "${SNAPSHOT_PATH}.tar.gz" | awk '{print $1}')
echo "${FINAL_HASH}  ${SNAPSHOT_NAME}.tar.gz" >> "${SNAPSHOT_DIR}/hash_chain.log"

# 7. Cleanup uncompressed
rm -rf "${SNAPSHOT_PATH}"

echo "[SNAPSHOT] ============================================"
echo "[SNAPSHOT] Completed: ${SNAPSHOT_NAME}.tar.gz"
echo "[SNAPSHOT] Hash: ${FINAL_HASH}"
echo "[SNAPSHOT] ============================================"

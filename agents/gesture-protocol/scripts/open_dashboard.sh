#!/bin/bash
# ============================================================================
# OPEN DASHBOARD — Launch Metabase Executive View
# ============================================================================
# Triggered by: open_palm_hold gesture
# Purpose: Launch Metabase executive dashboard on secure endpoint
# ============================================================================

set -euo pipefail

METABASE_URL="${METABASE_URL:-http://localhost:3000}"
DASHBOARD_ID="${METABASE_DASHBOARD_ID:-1}"
FULL_URL="${METABASE_URL}/dashboard/${DASHBOARD_ID}"

echo "[DASHBOARD] ============================================"
echo "[DASHBOARD] Opening Metabase dashboard"
echo "[DASHBOARD] URL: ${FULL_URL}"
echo "[DASHBOARD] ============================================"

# Detect display environment
if [ -n "${DISPLAY:-}" ]; then
    # X11 environment
    if command -v xdg-open &> /dev/null; then
        xdg-open "${FULL_URL}"
    elif command -v firefox &> /dev/null; then
        firefox "${FULL_URL}" &
    elif command -v chromium &> /dev/null; then
        chromium "${FULL_URL}" &
    else
        echo "[DASHBOARD] No browser found. URL: ${FULL_URL}"
    fi
elif [ -n "${WAYLAND_DISPLAY:-}" ]; then
    # Wayland environment
    xdg-open "${FULL_URL}" 2>/dev/null || echo "[DASHBOARD] URL: ${FULL_URL}"
else
    # Headless — output URL for remote access
    echo "[DASHBOARD] Headless mode detected"
    echo "[DASHBOARD] Access dashboard at: ${FULL_URL}"
fi

echo "[DASHBOARD] ============================================"
echo "[DASHBOARD] Dashboard launch complete"
echo "[DASHBOARD] ============================================"

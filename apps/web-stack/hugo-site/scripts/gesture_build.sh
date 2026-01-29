#!/bin/bash
# =============================================================================
# SOVEREIGN ELITE OS — Hugo Gesture Build Script
# =============================================================================
# Triggered by Manus Bridge gesture events to rebuild and deploy static site.
#
# Usage:
#   ./scripts/gesture_build.sh [action]
#
# Actions:
#   build    - Build site only
#   deploy   - Build and deploy to server
#   preview  - Build and start local preview server
#
# Environment Variables:
#   HUGO_ENV          - Environment (production/staging/development)
#   DEPLOY_TARGET     - rsync target (user@host:/path)
#   DEPLOY_KEY        - SSH key path for deployment
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SITE_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="${SITE_DIR}/public"
LOG_FILE="/var/log/manus_gesture/hugo_build.log"

ACTION="${1:-build}"
HUGO_ENV="${HUGO_ENV:-production}"
DEPLOY_TARGET="${DEPLOY_TARGET:-}"
DEPLOY_KEY="${DEPLOY_KEY:-}"

# Logging
log() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] $1" | tee -a "$LOG_FILE"
}

# Generate build hash
generate_hash() {
    local hash
    hash=$(find "$SITE_DIR/content" -type f -exec sha256sum {} \; | sha256sum | cut -d' ' -f1)
    echo "$hash"
}

# Build site
build_site() {
    log "[BUILD] Starting Hugo build..."
    log "[BUILD] Environment: ${HUGO_ENV}"
    
    cd "$SITE_DIR"
    
    # Clean previous build
    rm -rf "$BUILD_DIR"
    
    # Build with Hugo
    hugo --minify --environment "$HUGO_ENV"
    
    # Generate build manifest
    local build_hash
    build_hash=$(generate_hash)
    local build_time
    build_time=$(date -Iseconds)
    
    cat > "${BUILD_DIR}/build-manifest.json" << EOF
{
    "version": "1.0.0",
    "build_time": "${build_time}",
    "content_hash": "${build_hash}",
    "environment": "${HUGO_ENV}",
    "triggered_by": "gesture_build"
}
EOF
    
    log "[BUILD] Complete. Hash: ${build_hash:0:16}..."
    echo "$build_hash"
}

# Deploy site
deploy_site() {
    if [[ -z "$DEPLOY_TARGET" ]]; then
        log "[DEPLOY] ERROR: DEPLOY_TARGET not set"
        exit 1
    fi
    
    log "[DEPLOY] Deploying to ${DEPLOY_TARGET}..."
    
    local rsync_opts="-avz --delete"
    
    if [[ -n "$DEPLOY_KEY" ]]; then
        rsync_opts="$rsync_opts -e 'ssh -i $DEPLOY_KEY'"
    fi
    
    eval rsync $rsync_opts "${BUILD_DIR}/" "${DEPLOY_TARGET}"
    
    log "[DEPLOY] Complete."
}

# Preview server
preview_site() {
    log "[PREVIEW] Starting preview server..."
    cd "$SITE_DIR"
    hugo server --bind 0.0.0.0 --port 1313 --disableFastRender
}

# Main
main() {
    log "============================================"
    log "Gesture Build Script - Action: ${ACTION}"
    log "============================================"
    
    case "$ACTION" in
        build)
            build_site
            ;;
        deploy)
            build_site
            deploy_site
            ;;
        preview)
            build_site
            preview_site
            ;;
        *)
            log "ERROR: Unknown action: ${ACTION}"
            echo "Usage: $0 [build|deploy|preview]"
            exit 1
            ;;
    esac
    
    log "============================================"
    log "Gesture Build Complete"
    log "============================================"
}

main "$@"

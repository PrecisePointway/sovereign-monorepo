# Sovereign Sanctuary Elite - Dockerfile
# Multi-stage build for minimal production image

# ═══════════════════════════════════════════════════════════════════
# Stage 1: Builder
# ═══════════════════════════════════════════════════════════════════
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY pyproject.toml .
RUN pip install --no-cache-dir build && \
    pip wheel --no-cache-dir --wheel-dir /wheels .

# ═══════════════════════════════════════════════════════════════════
# Stage 2: Production
# ═══════════════════════════════════════════════════════════════════
FROM python:3.11-slim as production

# Security: Run as non-root user
RUN useradd --create-home --shell /bin/bash sanctuary
WORKDIR /home/sanctuary/app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

# Copy application code
COPY --chown=sanctuary:sanctuary . .

# Create required directories
RUN mkdir -p runtime evidence RESTORE_POINTS EVIDENCE_SNAPSHOTS && \
    chown -R sanctuary:sanctuary .

# Switch to non-root user
USER sanctuary

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python tools/safety/safety_guardrail_check.py || exit 1

# Default command: Run safety check then daemon
CMD ["python", "-m", "core.daemon"]

# ═══════════════════════════════════════════════════════════════════
# Labels
# ═══════════════════════════════════════════════════════════════════
LABEL org.opencontainers.image.title="Sovereign Sanctuary Elite"
LABEL org.opencontainers.image.version="2.0.0"
LABEL org.opencontainers.image.description="Zero-drift automation with cryptographic traceability"

#!/usr/bin/env python3
"""
SOVEREIGN ELITE OS — FastAPI Application
=========================================
Gesture-native web application with full Manus Bridge integration.

FEATURES:
- Native WebSocket connection to Manus Bridge
- Hash-chained audit logging
- HTMX-powered interactive UI
- Content management API
- Gesture-triggered actions
- CONTENT POLICY ENFORCEMENT (anime/child imagery banned)

AUTHOR: Architect
VERSION: 1.1.0
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import subprocess
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

# Content Policy Enforcement
from content_policy import content_policy, check_upload, ViolationType, PolicyViolation

# =============================================================================
# CONFIGURATION
# =============================================================================

LOG_DIR = Path(os.getenv("LOG_DIR", "/var/log/sovereign_app"))
CONTENT_DIR = Path(os.getenv("CONTENT_DIR", "./content"))
STATIC_DIR = Path(os.getenv("STATIC_DIR", "./static"))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me-in-production")
MANUS_BRIDGE_URL = os.getenv("MANUS_BRIDGE_URL", "ws://localhost:8765")

# Ensure directories exist
LOG_DIR.mkdir(parents=True, exist_ok=True)
CONTENT_DIR.mkdir(parents=True, exist_ok=True)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "app.log"),
    ]
)
logger = logging.getLogger("sovereign")

# =============================================================================
# MODELS
# =============================================================================

class GestureEvent(BaseModel):
    gesture_id: str
    action: str
    confidence: float
    timestamp: float
    biometric_hash: Optional[str] = None
    device_mac: Optional[str] = None


class ContentItem(BaseModel):
    title: str
    content: str
    status: str = "draft"
    tags: list[str] = []


class SnapshotRequest(BaseModel):
    triggered_by: str = "api"


# =============================================================================
# HASH CHAIN
# =============================================================================

class HashChain:
    """Cryptographic hash chain for audit logging."""
    
    def __init__(self, path: Path):
        self.path = path
        self.chain: list[dict] = []
        self._load()
    
    def _load(self):
        if self.path.exists():
            try:
                self.chain = json.loads(self.path.read_text())
            except Exception:
                self.chain = []
    
    def _save(self):
        self.path.write_text(json.dumps(self.chain, indent=2))
    
    def append(self, event: dict) -> str:
        prev_hash = self.chain[-1]["hash"] if self.chain else "GENESIS"
        timestamp = datetime.utcnow().isoformat()
        
        payload = json.dumps(event, sort_keys=True) + prev_hash + timestamp
        event_hash = hashlib.sha256(payload.encode()).hexdigest()
        
        record = {
            "timestamp": timestamp,
            "event": event,
            "prev_hash": prev_hash,
            "hash": event_hash,
        }
        
        self.chain.append(record)
        self._save()
        
        return event_hash
    
    def verify(self) -> bool:
        for i, record in enumerate(self.chain):
            expected_prev = self.chain[i-1]["hash"] if i > 0 else "GENESIS"
            if record["prev_hash"] != expected_prev:
                return False
            
            payload = json.dumps(record["event"], sort_keys=True) + record["prev_hash"] + record["timestamp"]
            expected_hash = hashlib.sha256(payload.encode()).hexdigest()
            if record["hash"] != expected_hash:
                return False
        
        return True


# =============================================================================
# APPLICATION STATE
# =============================================================================

@dataclass
class AppState:
    hash_chain: HashChain = None
    content_items: dict[str, dict] = field(default_factory=dict)
    connected_clients: list[WebSocket] = field(default_factory=list)
    last_gesture: Optional[dict] = None
    startup_time: datetime = field(default_factory=datetime.utcnow)


state = AppState()


# =============================================================================
# LIFESPAN
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Sovereign Elite OS Application starting...")
    logger.info("Content Policy Enforcement: ENABLED")
    logger.info("Banned categories: ANIME, CHILD-RELATED IMAGERY")
    
    state.hash_chain = HashChain(LOG_DIR / "hash_chain.json")
    state.hash_chain.append({"event": "app_startup", "version": "1.1.0", "content_policy": "enabled"})
    logger.info(f"Hash chain loaded: {len(state.hash_chain.chain)} records")
    
    yield
    
    # Shutdown
    logger.info("Sovereign Elite OS Application shutting down...")
    state.hash_chain.append({"event": "app_shutdown"})


# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="Sovereign Elite OS",
    description="Gesture-native web application for Sovereign Sanctuary Systems",
    version="1.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# CONTENT POLICY MIDDLEWARE
# =============================================================================

class ContentPolicyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce content policy on all requests.
    
    ZERO TOLERANCE for:
    - Anime imagery
    - Child-related imagery
    
    Checks:
    - Query parameters for banned terms
    - Request paths for suspicious patterns
    """
    
    async def dispatch(self, request: Request, call_next):
        # Check query parameters
        for key, value in request.query_params.items():
            violation = content_policy.check_content_text(value, context=f"query:{key}")
            if violation:
                logger.critical(f"CONTENT POLICY VIOLATION in query: {violation.reason}")
                state.hash_chain.append({
                    "event": "content_policy_violation",
                    "type": violation.violation_type.value,
                    "context": f"query:{key}",
                    "blocked": True,
                })
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "Content policy violation",
                        "type": violation.violation_type.value,
                        "message": "This content is prohibited by platform policy."
                    }
                )
        
        # Check path for suspicious patterns
        violation = content_policy.check_content_text(request.url.path, context="path")
        if violation:
            logger.critical(f"CONTENT POLICY VIOLATION in path: {violation.reason}")
            state.hash_chain.append({
                "event": "content_policy_violation",
                "type": violation.violation_type.value,
                "context": "path",
                "blocked": True,
            })
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Content policy violation",
                    "type": violation.violation_type.value,
                    "message": "This content is prohibited by platform policy."
                }
            )
        
        response = await call_next(request)
        return response


app.add_middleware(ContentPolicyMiddleware)


# =============================================================================
# MIDDLEWARE — REQUEST LOGGING
# =============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = (time.time() - start_time) * 1000
    
    logger.info(f"{request.method} {request.url.path} - {response.status_code} ({duration:.2f}ms)")
    
    return response


# =============================================================================
# WEBHOOK VERIFICATION
# =============================================================================

def verify_webhook_signature(request: Request, body: bytes) -> bool:
    """Verify HMAC signature from Manus Bridge."""
    signature = request.headers.get("X-Sovereign-Signature")
    timestamp = request.headers.get("X-Sovereign-Timestamp")
    
    if not signature or not timestamp:
        return False
    
    try:
        if abs(time.time() - float(timestamp)) > 300:
            return False
    except ValueError:
        return False
    
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        f"{timestamp}.".encode() + body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)


# =============================================================================
# ROUTES — CONTENT POLICY
# =============================================================================

@app.get("/api/content-policy")
async def get_content_policy():
    """Get current content policy status."""
    return {
        "enabled": content_policy.config.enabled,
        "strict_mode": content_policy.config.strict_mode,
        "banned_categories": ["anime", "child_related_imagery"],
        "violations_logged": len(content_policy.violations),
        "policy_version": "1.0.0",
    }


@app.get("/api/content-policy/violations")
async def get_policy_violations():
    """Get recent content policy violations."""
    violations = content_policy.get_violations(limit=50)
    return {
        "count": len(violations),
        "violations": [
            {
                "timestamp": v.timestamp,
                "type": v.violation_type.value,
                "filename": v.filename,
                "reason": v.reason,
                "blocked": v.blocked,
            }
            for v in violations
        ],
        "stats": content_policy.get_violation_stats(),
    }


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload file with content policy enforcement.
    
    BLOCKED:
    - Anime imagery
    - Child-related imagery
    """
    # Read file content
    content = await file.read()
    
    # Check against content policy
    violation = check_upload(file.filename, content)
    
    if violation:
        logger.critical(f"UPLOAD BLOCKED: {violation.reason}")
        state.hash_chain.append({
            "event": "upload_blocked",
            "type": violation.violation_type.value,
            "filename": file.filename,
            "reason": violation.reason,
        })
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Content policy violation",
                "type": violation.violation_type.value,
                "message": "This file type/content is prohibited by platform policy.",
            }
        )
    
    # Save file
    file_hash = hashlib.sha256(content).hexdigest()
    save_path = CONTENT_DIR / f"{file_hash[:16]}_{file.filename}"
    save_path.write_bytes(content)
    
    # Log successful upload
    state.hash_chain.append({
        "event": "file_uploaded",
        "filename": file.filename,
        "hash": file_hash,
        "size": len(content),
    })
    
    logger.info(f"File uploaded: {file.filename} ({len(content)} bytes)")
    
    return {
        "status": "success",
        "filename": file.filename,
        "hash": file_hash,
        "size": len(content),
    }


# =============================================================================
# ROUTES — API
# =============================================================================

@app.get("/api/status")
async def get_status():
    """System status endpoint."""
    return {
        "status": "operational",
        "version": "1.1.0",
        "uptime_seconds": (datetime.utcnow() - state.startup_time).total_seconds(),
        "hash_chain_length": len(state.hash_chain.chain),
        "hash_chain_valid": state.hash_chain.verify(),
        "content_count": len(state.content_items),
        "connected_clients": len(state.connected_clients),
        "last_gesture": state.last_gesture,
        "content_policy": {
            "enabled": content_policy.config.enabled,
            "violations": len(content_policy.violations),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/api/gesture")
async def handle_gesture(event: GestureEvent, request: Request):
    """Handle gesture events from Manus Bridge."""
    # Log event
    event_hash = state.hash_chain.append({
        "type": "gesture",
        "gesture_id": event.gesture_id,
        "action": event.action,
        "confidence": event.confidence,
    })
    
    state.last_gesture = {
        "gesture_id": event.gesture_id,
        "action": event.action,
        "timestamp": datetime.utcnow().isoformat(),
        "hash": event_hash,
    }
    
    logger.info(f"Gesture received: {event.gesture_id} -> {event.action}")
    
    # Execute action
    result = await execute_gesture_action(event)
    
    # Broadcast to connected clients
    await broadcast_event({
        "type": "gesture",
        "data": state.last_gesture,
    })
    
    return {
        "status": "success",
        "event_hash": event_hash,
        "result": result,
    }


async def execute_gesture_action(event: GestureEvent) -> dict:
    """Execute the action associated with a gesture."""
    action_map = {
        "generate_snapshot": action_snapshot,
        "trigger_sync": action_sync,
        "publish_content": action_publish,
        "open_dashboard": action_dashboard,
        "send_alert": action_alert,
    }
    
    handler = action_map.get(event.action)
    if handler:
        return await handler(event)
    
    return {"status": "unknown_action", "action": event.action}


async def action_snapshot(event: GestureEvent) -> dict:
    """Generate system snapshot."""
    snapshot = {
        "timestamp": datetime.utcnow().isoformat(),
        "content_count": len(state.content_items),
        "hash_chain_length": len(state.hash_chain.chain),
        "content_policy_violations": len(content_policy.violations),
        "triggered_by": event.gesture_id,
    }
    
    snapshot_hash = hashlib.sha256(json.dumps(snapshot).encode()).hexdigest()
    
    snapshot_path = LOG_DIR / f"snapshot_{int(time.time())}.json"
    snapshot_path.write_text(json.dumps(snapshot, indent=2))
    
    logger.info(f"Snapshot created: {snapshot_hash[:16]}...")
    
    return {"status": "snapshot_created", "hash": snapshot_hash}


async def action_sync(event: GestureEvent) -> dict:
    """Trigger data sync."""
    logger.info("Sync triggered via gesture")
    return {"status": "sync_triggered"}


async def action_publish(event: GestureEvent) -> dict:
    """Publish pending content."""
    published = 0
    for item_id, item in state.content_items.items():
        if item.get("status") == "pending":
            item["status"] = "published"
            item["published_at"] = datetime.utcnow().isoformat()
            published += 1
    
    logger.info(f"Published {published} items via gesture")
    return {"status": "published", "count": published}


async def action_dashboard(event: GestureEvent) -> dict:
    """Open dashboard."""
    logger.info("Dashboard open requested via gesture")
    return {"status": "dashboard_requested"}


async def action_alert(event: GestureEvent) -> dict:
    """Send alert."""
    logger.warning("Alert triggered via gesture")
    return {"status": "alert_sent"}


@app.post("/api/content")
async def create_content(item: ContentItem):
    """Create new content item with policy check."""
    # Check title against content policy
    violation = content_policy.check_content_text(item.title, context="content_title")
    if violation:
        raise HTTPException(status_code=403, detail=f"Content policy violation: {violation.reason}")
    
    # Check content against content policy
    violation = content_policy.check_content_text(item.content, context="content_body")
    if violation:
        raise HTTPException(status_code=403, detail=f"Content policy violation: {violation.reason}")
    
    # Check tags
    for tag in item.tags:
        violation = content_policy.check_content_text(tag, context="content_tag")
        if violation:
            raise HTTPException(status_code=403, detail=f"Content policy violation in tag: {violation.reason}")
    
    item_id = hashlib.md5(f"{item.title}{time.time()}".encode()).hexdigest()[:12]
    
    state.content_items[item_id] = {
        "id": item_id,
        "title": item.title,
        "content": item.content,
        "status": item.status,
        "tags": item.tags,
        "created_at": datetime.utcnow().isoformat(),
    }
    
    state.hash_chain.append({
        "type": "content_created",
        "item_id": item_id,
        "title": item.title,
    })
    
    return {"status": "created", "id": item_id}


@app.get("/api/content")
async def list_content():
    """List all content items."""
    return {"items": list(state.content_items.values())}


@app.get("/api/content/{item_id}")
async def get_content(item_id: str):
    """Get specific content item."""
    if item_id not in state.content_items:
        raise HTTPException(status_code=404, detail="Content not found")
    return state.content_items[item_id]


@app.post("/api/snapshot")
async def create_snapshot(req: SnapshotRequest):
    """Create system snapshot."""
    result = await action_snapshot(GestureEvent(
        gesture_id="api_call",
        action="generate_snapshot",
        confidence=1.0,
        timestamp=time.time(),
    ))
    return result


@app.get("/api/audit")
async def get_audit_log():
    """Get audit log (hash chain)."""
    return {
        "length": len(state.hash_chain.chain),
        "valid": state.hash_chain.verify(),
        "events": state.hash_chain.chain[-50:],
    }


@app.get("/api/audit/verify")
async def verify_audit():
    """Verify hash chain integrity."""
    valid = state.hash_chain.verify()
    return {
        "valid": valid,
        "length": len(state.hash_chain.chain),
        "status": "INTACT" if valid else "CORRUPTED",
    }


# =============================================================================
# ROUTES — WEBSOCKET
# =============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    state.connected_clients.append(websocket)
    logger.info(f"WebSocket client connected. Total: {len(state.connected_clients)}")
    
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "ack", "data": data})
    except WebSocketDisconnect:
        state.connected_clients.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(state.connected_clients)}")


async def broadcast_event(event: dict):
    """Broadcast event to all connected WebSocket clients."""
    for client in state.connected_clients:
        try:
            await client.send_json(event)
        except Exception:
            pass


# =============================================================================
# ROUTES — UI (HTMX)
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with HTMX-powered UI."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sovereign Elite OS</title>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <style>
        :root {
            --bg: #0a0a0a;
            --bg-secondary: #111;
            --text: #e0e0e0;
            --text-dim: #888;
            --accent: #00ff88;
            --danger: #ff4444;
            --border: #333;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            padding: 2rem;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { color: var(--accent); margin-bottom: 0.5rem; }
        .tagline { color: var(--text-dim); margin-bottom: 2rem; }
        .policy-banner {
            background: var(--danger);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
            font-weight: bold;
        }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
        .card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
        }
        .card h2 { font-size: 1rem; color: var(--accent); margin-bottom: 1rem; }
        .status-row { display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--border); }
        .status-row:last-child { border-bottom: none; }
        .status-label { color: var(--text-dim); }
        .status-value { font-family: monospace; }
        .status-ok { color: var(--accent); }
        .status-warn { color: #ffaa00; }
        .status-danger { color: var(--danger); }
        .btn {
            background: var(--accent);
            color: var(--bg);
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 600;
            margin-top: 1rem;
        }
        .btn:hover { opacity: 0.9; }
    </style>
</head>
<body>
    <div class="container">
        <div class="policy-banner">
            CONTENT POLICY ACTIVE: Anime and child-related imagery strictly prohibited
        </div>
        
        <h1>Sovereign Elite OS</h1>
        <p class="tagline">Zero-Dependency. Deterministic. Auditable.</p>
        
        <div class="grid">
            <div class="card">
                <h2>System Status</h2>
                <div hx-get="/api/status" hx-trigger="load, every 5s" hx-swap="innerHTML">
                    Loading...
                </div>
            </div>
            
            <div class="card">
                <h2>Content Policy</h2>
                <div hx-get="/ui/policy-status" hx-trigger="load, every 10s" hx-swap="innerHTML">
                    Loading...
                </div>
            </div>
            
            <div class="card">
                <h2>Audit Chain</h2>
                <div hx-get="/ui/audit-summary" hx-trigger="load, every 10s" hx-swap="innerHTML">
                    Loading...
                </div>
                <button class="btn" hx-post="/api/snapshot" hx-swap="none">
                    Create Snapshot
                </button>
            </div>
            
            <div class="card">
                <h2>Recent Gestures</h2>
                <div id="gesture-log" hx-get="/ui/gesture-log" hx-trigger="load, every 3s" hx-swap="innerHTML">
                    Loading...
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""


@app.get("/ui/policy-status", response_class=HTMLResponse)
async def ui_policy_status():
    """HTMX partial for content policy status."""
    violations = len(content_policy.violations)
    status_class = "status-ok" if violations == 0 else "status-danger"
    
    return f"""
    <div class="status-row">
        <span class="status-label">Policy</span>
        <span class="status-value status-ok">ENFORCED</span>
    </div>
    <div class="status-row">
        <span class="status-label">Banned</span>
        <span class="status-value">Anime, Child imagery</span>
    </div>
    <div class="status-row">
        <span class="status-label">Violations</span>
        <span class="status-value {status_class}">{violations}</span>
    </div>
    """


@app.get("/ui/audit-summary", response_class=HTMLResponse)
async def ui_audit_summary():
    """HTMX partial for audit summary."""
    valid = state.hash_chain.verify()
    length = len(state.hash_chain.chain)
    
    status_class = "status-ok" if valid else "status-warn"
    status_text = "INTACT" if valid else "CORRUPTED"
    
    return f"""
    <div class="status-row">
        <span class="status-label">Chain Length</span>
        <span class="status-value">{length}</span>
    </div>
    <div class="status-row">
        <span class="status-label">Integrity</span>
        <span class="status-value {status_class}">{status_text}</span>
    </div>
    """


@app.get("/ui/gesture-log", response_class=HTMLResponse)
async def ui_gesture_log():
    """HTMX partial for gesture log."""
    events = [e for e in state.hash_chain.chain if e["event"].get("type") == "gesture"][-10:]
    
    if not events:
        return "<p style='color: var(--text-dim);'>No gesture events yet.</p>"
    
    html = ""
    for event in reversed(events):
        gesture = event["event"].get("gesture_id", "unknown")
        action = event["event"].get("action", "unknown")
        ts = event["timestamp"][:19]
        html += f"""
        <div style="padding: 0.5rem; border-bottom: 1px solid var(--border);">
            <span style="color: var(--text-dim);">{ts}</span><br>
            <strong>{gesture}</strong> → {action}
        </div>
        """
    
    return html


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

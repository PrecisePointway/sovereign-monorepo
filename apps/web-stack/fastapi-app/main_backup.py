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

AUTHOR: Architect
VERSION: 1.0.0
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

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

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
    state.hash_chain = HashChain(LOG_DIR / "hash_chain.json")
    state.hash_chain.append({"event": "app_startup", "version": "1.0.0"})
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
    version="1.0.0",
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

# Static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# =============================================================================
# MIDDLEWARE
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
    
    # Check timestamp freshness (5 minute window)
    try:
        if abs(time.time() - float(timestamp)) > 300:
            return False
    except ValueError:
        return False
    
    # Verify HMAC
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        f"{timestamp}.".encode() + body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)


# =============================================================================
# ROUTES — API
# =============================================================================

@app.get("/api/status")
async def get_status():
    """System status endpoint."""
    return {
        "status": "operational",
        "version": "1.0.0",
        "uptime_seconds": (datetime.utcnow() - state.startup_time).total_seconds(),
        "hash_chain_length": len(state.hash_chain.chain),
        "hash_chain_valid": state.hash_chain.verify(),
        "content_count": len(state.content_items),
        "connected_clients": len(state.connected_clients),
        "last_gesture": state.last_gesture,
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
        "triggered_by": event.gesture_id,
    }
    
    snapshot_hash = hashlib.sha256(json.dumps(snapshot).encode()).hexdigest()
    
    # Save snapshot
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
    """Open dashboard (notification only for web app)."""
    logger.info("Dashboard open requested via gesture")
    return {"status": "dashboard_requested"}


async def action_alert(event: GestureEvent) -> dict:
    """Send alert."""
    logger.warning("Alert triggered via gesture")
    return {"status": "alert_sent"}


@app.post("/api/content")
async def create_content(item: ContentItem):
    """Create new content item."""
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
        "events": state.hash_chain.chain[-50:],  # Last 50 events
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
            # Echo back for now
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
        .event-log {
            max-height: 300px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 0.85rem;
        }
        .event { padding: 0.5rem; border-bottom: 1px solid var(--border); }
        .event-time { color: var(--text-dim); }
        .htmx-indicator { opacity: 0; transition: opacity 200ms; }
        .htmx-request .htmx-indicator { opacity: 1; }
    </style>
</head>
<body>
    <div class="container">
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
                <div id="gesture-log" class="event-log" hx-get="/ui/gesture-log" hx-trigger="load, every 3s" hx-swap="innerHTML">
                    Loading...
                </div>
            </div>
            
            <div class="card">
                <h2>Content Items</h2>
                <div hx-get="/ui/content-list" hx-trigger="load, every 10s" hx-swap="innerHTML">
                    Loading...
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // WebSocket for real-time updates
        const ws = new WebSocket('ws://' + window.location.host + '/ws');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'gesture') {
                htmx.trigger('#gesture-log', 'refresh');
            }
        };
    </script>
</body>
</html>
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
        <div class="event">
            <span class="event-time">{ts}</span><br>
            <strong>{gesture}</strong> → {action}
        </div>
        """
    
    return html


@app.get("/ui/content-list", response_class=HTMLResponse)
async def ui_content_list():
    """HTMX partial for content list."""
    if not state.content_items:
        return "<p style='color: var(--text-dim);'>No content items.</p>"
    
    html = ""
    for item in list(state.content_items.values())[:5]:
        status = item.get("status", "draft")
        status_class = "status-ok" if status == "published" else ""
        html += f"""
        <div class="status-row">
            <span class="status-label">{item['title'][:30]}</span>
            <span class="status-value {status_class}">{status}</span>
        </div>
        """
    
    return html


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

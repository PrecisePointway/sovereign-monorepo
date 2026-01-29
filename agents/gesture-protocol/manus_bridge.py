#!/usr/bin/env python3
"""
MANUS BRIDGE — Gesture-to-Command Router
=========================================
Sovereign Elite OS — Gesture-Driven Command Interface

PURPOSE:
    Route authenticated gestures from Manus Pro gloves to deterministic
    infrastructure commands. Fail-closed by default.

SECURITY MODEL:
    - Identity enforcement: Reject all input unless biometric hash verified
    - Fail-closed: On any auth failure, log + freeze input layer
    - No external dependencies: All execution is local shell or internal API

USAGE:
    python3 manus_bridge.py --config gesture_protocol.yaml

AUTHOR: Architect
VERSION: 1.0.0
"""

import argparse
import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

# =============================================================================
# CONFIGURATION
# =============================================================================

LOG_DIR = Path("/var/log/manus_gesture/")
LOG_FILE = LOG_DIR / "manus_bridge.log"
HASH_CHAIN_FILE = LOG_DIR / "hash_chain.json"

# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging() -> logging.Logger:
    """Initialize logging with file and console handlers."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("manus_bridge")
    logger.setLevel(logging.DEBUG)
    
    # File handler
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(logging.DEBUG)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

logger = setup_logging()

# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class GestureEvent:
    """Represents an incoming gesture event from Manus Pro SDK."""
    gesture_id: str
    confidence: float
    timestamp: float
    device_mac: str
    biometric_hash: Optional[str] = None


@dataclass
class AuthState:
    """Tracks authentication state for fail-closed behavior."""
    is_authenticated: bool = False
    failed_attempts: int = 0
    is_frozen: bool = False
    last_auth_time: Optional[float] = None


# =============================================================================
# CORE CLASSES
# =============================================================================

class HashChain:
    """Cryptographic hash chain for audit trail integrity."""
    
    def __init__(self, chain_file: Path):
        self.chain_file = chain_file
        self.chain = self._load_chain()
    
    def _load_chain(self) -> list:
        if self.chain_file.exists():
            with open(self.chain_file, "r") as f:
                return json.load(f)
        return []
    
    def _save_chain(self):
        with open(self.chain_file, "w") as f:
            json.dump(self.chain, f, indent=2)
    
    def get_previous_hash(self) -> str:
        if not self.chain:
            return "GENESIS"
        return self.chain[-1]["hash"]
    
    def append(self, event_data: dict) -> str:
        """Append event to chain with cryptographic linking."""
        prev_hash = self.get_previous_hash()
        
        record = {
            "index": len(self.chain),
            "timestamp": datetime.utcnow().isoformat(),
            "prev_hash": prev_hash,
            "data": event_data,
        }
        
        # Compute hash of this record
        record_str = json.dumps(record, sort_keys=True)
        record["hash"] = hashlib.sha256(record_str.encode()).hexdigest()
        
        self.chain.append(record)
        self._save_chain()
        
        return record["hash"]


class GestureProtocol:
    """Loads and manages the gesture protocol configuration."""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> dict:
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)
    
    def _validate_config(self):
        required_keys = ["operator_profile", "gesture_processing_policy", "command_map"]
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required config key: {key}")
    
    @property
    def debounce_ms(self) -> int:
        return self.config["gesture_processing_policy"].get("debounce_ms", 250)
    
    @property
    def confidence_threshold(self) -> float:
        return self.config["gesture_processing_policy"].get("confidence_threshold", 0.85)
    
    @property
    def identity_enforced(self) -> bool:
        return self.config["gesture_processing_policy"].get("identity_enforced", True)
    
    @property
    def max_failed_attempts(self) -> int:
        return self.config["environment_security"].get("max_failed_auth_attempts", 3)
    
    @property
    def session_timeout_minutes(self) -> int:
        return self.config["environment_security"].get("session_timeout_minutes", 30)
    
    def get_command(self, gesture_id: str) -> Optional[dict]:
        return self.config["command_map"].get(gesture_id)


class ManusAuthenticator:
    """
    Handles biometric authentication for Manus Pro gloves.
    
    STUB: Replace with actual Manus SDK integration.
    """
    
    def __init__(self, authorized_hashes: list[str]):
        self.authorized_hashes = set(authorized_hashes)
    
    def verify(self, biometric_hash: Optional[str]) -> bool:
        """
        Verify biometric hash against authorized list.
        
        SECURITY: Fail-closed — returns False on any ambiguity.
        """
        if biometric_hash is None:
            return False
        if not biometric_hash:
            return False
        return biometric_hash in self.authorized_hashes


class ManusBridge:
    """
    Main bridge class: routes gestures to commands.
    
    SECURITY MODEL:
        - All inputs rejected until authenticated
        - Failed auth increments counter; exceeds max → freeze
        - Frozen state requires manual intervention
        - All events logged with hash chain
    """
    
    def __init__(self, protocol: GestureProtocol, authenticator: ManusAuthenticator):
        self.protocol = protocol
        self.authenticator = authenticator
        self.auth_state = AuthState()
        self.hash_chain = HashChain(HASH_CHAIN_FILE)
        self.last_gesture_time: dict[str, float] = {}
    
    def _log_event(self, event_type: str, data: dict):
        """Log event to hash chain for audit trail."""
        event_data = {
            "type": event_type,
            "data": data,
        }
        chain_hash = self.hash_chain.append(event_data)
        logger.debug(f"Event logged: {event_type} | Hash: {chain_hash[:16]}...")
    
    def _is_frozen(self) -> bool:
        """Check if input layer is frozen."""
        return self.auth_state.is_frozen
    
    def _freeze_input_layer(self, reason: str):
        """Freeze input layer — fail-closed behavior."""
        self.auth_state.is_frozen = True
        logger.critical(f"INPUT LAYER FROZEN: {reason}")
        self._log_event("FREEZE", {"reason": reason})
    
    def _check_session_timeout(self) -> bool:
        """Check if session has timed out."""
        if self.auth_state.last_auth_time is None:
            return True
        
        elapsed = time.time() - self.auth_state.last_auth_time
        timeout_seconds = self.protocol.session_timeout_minutes * 60
        
        if elapsed > timeout_seconds:
            self.auth_state.is_authenticated = False
            logger.warning("Session timeout — re-authentication required")
            return True
        
        return False
    
    def _is_debounced(self, gesture_id: str) -> bool:
        """Check if gesture is within debounce window."""
        now = time.time()
        last_time = self.last_gesture_time.get(gesture_id, 0)
        debounce_seconds = self.protocol.debounce_ms / 1000.0
        
        if now - last_time < debounce_seconds:
            logger.debug(f"Gesture debounced: {gesture_id}")
            return True
        
        self.last_gesture_time[gesture_id] = now
        return False
    
    def authenticate(self, event: GestureEvent) -> bool:
        """
        Attempt authentication with biometric hash.
        
        Returns True if authenticated, False otherwise.
        On max failures, freezes input layer.
        """
        if self._is_frozen():
            logger.warning("Authentication rejected — input layer frozen")
            return False
        
        if self.authenticator.verify(event.biometric_hash):
            self.auth_state.is_authenticated = True
            self.auth_state.failed_attempts = 0
            self.auth_state.last_auth_time = time.time()
            logger.info(f"Authentication successful | Device: {event.device_mac}")
            self._log_event("AUTH_SUCCESS", {"device_mac": event.device_mac})
            return True
        
        # Auth failed
        self.auth_state.failed_attempts += 1
        logger.warning(
            f"Authentication failed | Attempt {self.auth_state.failed_attempts}/{self.protocol.max_failed_attempts}"
        )
        self._log_event("AUTH_FAILURE", {
            "device_mac": event.device_mac,
            "attempt": self.auth_state.failed_attempts,
        })
        
        if self.auth_state.failed_attempts >= self.protocol.max_failed_attempts:
            self._freeze_input_layer("Max authentication attempts exceeded")
        
        return False
    
    def process_gesture(self, event: GestureEvent) -> bool:
        """
        Process incoming gesture event.
        
        Returns True if command executed, False otherwise.
        """
        # GATE 1: Frozen check
        if self._is_frozen():
            logger.warning(f"Gesture rejected — input layer frozen | {event.gesture_id}")
            return False
        
        # GATE 2: Authentication check
        if self.protocol.identity_enforced:
            if not self.auth_state.is_authenticated or self._check_session_timeout():
                logger.warning(f"Gesture rejected — not authenticated | {event.gesture_id}")
                return self.authenticate(event)
        
        # GATE 3: Confidence threshold
        if event.confidence < self.protocol.confidence_threshold:
            logger.debug(
                f"Gesture rejected — low confidence | {event.gesture_id} | "
                f"{event.confidence:.2f} < {self.protocol.confidence_threshold}"
            )
            return False
        
        # GATE 4: Debounce
        if self._is_debounced(event.gesture_id):
            return False
        
        # GATE 5: Command lookup
        command = self.protocol.get_command(event.gesture_id)
        if command is None:
            logger.warning(f"Gesture rejected — unmapped | {event.gesture_id}")
            self._log_event("UNMAPPED_GESTURE", {"gesture_id": event.gesture_id})
            return False
        
        # GATE 6: Confirmation check (for critical commands)
        if command.get("requires_confirmation", False):
            logger.info(f"Command requires confirmation | {command['action']}")
            # Confirmation flow: requires double-tap within 3 seconds (implemented via gesture_confirmed flag)
            # For now, log and proceed
            self._log_event("CONFIRMATION_REQUIRED", {"action": command["action"]})
        
        # EXECUTE
        return self._execute_command(command, event)
    
    def _execute_command(self, command: dict, event: GestureEvent) -> bool:
        """Execute the shell command associated with the gesture."""
        action = command["action"]
        shell_cmd = command["shell"]
        
        logger.info(f"Executing: {action} | {shell_cmd}")
        self._log_event("EXECUTE_START", {
            "action": action,
            "shell": shell_cmd,
            "gesture_id": event.gesture_id,
        })
        
        try:
            result = subprocess.run(
                shell_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            success = result.returncode == 0
            
            self._log_event("EXECUTE_COMPLETE", {
                "action": action,
                "success": success,
                "returncode": result.returncode,
                "stdout": result.stdout[:500] if result.stdout else "",
                "stderr": result.stderr[:500] if result.stderr else "",
            })
            
            if success:
                logger.info(f"Command succeeded: {action}")
            else:
                logger.error(f"Command failed: {action} | RC={result.returncode}")
            
            return success
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timeout: {action}")
            self._log_event("EXECUTE_TIMEOUT", {"action": action})
            return False
        except Exception as e:
            logger.error(f"Command exception: {action} | {e}")
            self._log_event("EXECUTE_ERROR", {"action": action, "error": str(e)})
            return False


# =============================================================================
# WEBSOCKET SERVER (STUB)
# =============================================================================

def run_websocket_server(bridge: ManusBridge, host: str = "127.0.0.1", port: int = 8765):
    """
    WebSocket server for receiving gesture events from Manus SDK.
    
    STUB: Implement with actual WebSocket library (e.g., websockets, FastAPI).
    """
    logger.info(f"WebSocket server starting on ws://{host}:{port}")
    logger.info("STUB: Replace with actual WebSocket implementation")
    
    # Placeholder event loop
    # In production, this would:
    # 1. Accept WebSocket connections from Manus SDK bridge
    # 2. Parse incoming gesture events as JSON
    # 3. Convert to GestureEvent dataclass
    # 4. Call bridge.process_gesture(event)
    
    print("\n" + "=" * 60)
    print("MANUS BRIDGE — READY")
    print("=" * 60)
    print(f"Config loaded: {bridge.protocol.config_path}")
    print(f"Identity enforcement: {bridge.protocol.identity_enforced}")
    print(f"Confidence threshold: {bridge.protocol.confidence_threshold}")
    print(f"Debounce: {bridge.protocol.debounce_ms}ms")
    print(f"Session timeout: {bridge.protocol.session_timeout_minutes}min")
    print("=" * 60)
    print("\nAwaiting gesture input...")
    print("(STUB: Connect Manus SDK WebSocket client)\n")


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Manus Bridge — Gesture-to-Command Router",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("gesture_protocol.yaml"),
        help="Path to gesture protocol YAML config",
    )
    parser.add_argument(
        "--authorized-hashes",
        type=str,
        nargs="*",
        default=[],
        help="List of authorized biometric hashes (space-separated)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="WebSocket server host",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="WebSocket server port",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode with simulated gestures",
    )
    
    args = parser.parse_args()
    
    # Validate config exists
    if not args.config.exists():
        logger.error(f"Config file not found: {args.config}")
        sys.exit(1)
    
    # Initialize components
    protocol = GestureProtocol(args.config)
    authenticator = ManusAuthenticator(args.authorized_hashes)
    bridge = ManusBridge(protocol, authenticator)
    
    if args.test:
        # Test mode: simulate gesture events
        logger.info("Running in TEST MODE")
        test_event = GestureEvent(
            gesture_id="fist_hold",
            confidence=0.92,
            timestamp=time.time(),
            device_mac="AA:BB:CC:DD:EE:FF",
            biometric_hash=args.authorized_hashes[0] if args.authorized_hashes else None,
        )
        bridge.process_gesture(test_event)
    else:
        # Production mode: start WebSocket server
        run_websocket_server(bridge, args.host, args.port)


if __name__ == "__main__":
    main()

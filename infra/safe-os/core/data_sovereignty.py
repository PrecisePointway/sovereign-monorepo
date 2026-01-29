#!/usr/bin/env python3
"""
DATA SOVEREIGNTY MODULE
Implements /forget_me and /my_data endpoints per Codex Articles 10-12.

This module provides:
- Atomic data erasure with cryptographic confirmation
- Transparent session data exposure
- Audit trail for all sovereignty operations

Part of S.A.F.E.-OS (Sovereign, Assistive, Fail-closed Environment)
"""

import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum


class DataCategory(Enum):
    """Categories of data per Article 10.1."""
    OPERATIONAL = "operational"      # Session-scoped task data
    SYSTEM_INTEGRITY = "system_integrity"  # Anonymized metrics
    USER_CONFIG = "user_config"      # User preferences


class BannedDataType(Enum):
    """Explicitly prohibited data types per Article 10.2."""
    BIOMETRIC = "biometric"
    BEHAVIORAL_PROFILE = "behavioral_profile"
    CROSS_SESSION_TRACKING = "cross_session_tracking"
    PSYCHOMETRIC = "psychometric"


@dataclass
class SessionData:
    """Represents all data held for a user session."""
    session_id: str
    user_id_hash: str
    created_at: str
    operational_data: Dict[str, Any] = field(default_factory=dict)
    user_config: Dict[str, Any] = field(default_factory=dict)
    audit_events: List[Dict] = field(default_factory=list)
    
    # Explicitly declare what is NOT held
    biometric_data: None = None
    behavioral_profile: None = None
    cross_session_links: None = None
    psychometric_data: None = None
    emotional_memory: None = None
    personality_memory: None = None


@dataclass
class ErasureConfirmation:
    """Cryptographic confirmation of data erasure."""
    user_id_hash: str
    timestamp: str
    erasure_scope: List[str]
    prev_hash: str
    proof_hash: str
    status: str = "ERASED"


class DataSovereigntyManager:
    """
    Manages data sovereignty operations per Codex Articles 10-12.
    
    Responsibilities:
    - Track what data is held per session
    - Enforce data minimization
    - Execute atomic erasure
    - Provide transparent data exposure
    - Maintain audit trail
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path("/var/lib/safe_os/sessions")
        self.audit_log: List[Dict] = []
        self.prev_hash = "GENESIS"
        self.sessions: Dict[str, SessionData] = {}
        
        # Banned metrics per Article 11.1
        self.banned_metrics = [
            "session_length",
            "time_in_app",
            "return_frequency",
            "attention_heatmap",
            "click_through_rate",
            "content_virality",
            "share_metrics",
            "persuasion_ab_test",
            "retention_sentiment",
        ]
    
    def create_session(self, user_id: str) -> SessionData:
        """Create a new session with minimal data."""
        user_id_hash = self._hash_user_id(user_id)
        session_id = self._generate_session_id()
        
        session = SessionData(
            session_id=session_id,
            user_id_hash=user_id_hash,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        
        self.sessions[session_id] = session
        
        self._log_event(
            "SESSION_CREATED",
            f"New session created",
            {"session_id": session_id}
        )
        
        return session
    
    def store_operational_data(self, session_id: str, key: str, value: Any) -> bool:
        """
        Store operational data for a session.
        
        Per Article 10.1: Only data explicitly provided by the user
        to execute a requested task.
        """
        if session_id not in self.sessions:
            return False
        
        # Validate against banned data types
        if self._is_banned_data(key, value):
            self._log_event(
                "BANNED_DATA_REJECTED",
                f"Attempted to store banned data type: {key}",
                {"session_id": session_id, "key": key}
            )
            return False
        
        self.sessions[session_id].operational_data[key] = value
        
        self._log_event(
            "OPERATIONAL_DATA_STORED",
            f"Data stored: {key}",
            {"session_id": session_id, "key": key}
        )
        
        return True
    
    def _is_banned_data(self, key: str, value: Any) -> bool:
        """Check if data matches banned categories."""
        banned_keywords = [
            "biometric", "facial", "voice_print", "gait",
            "clickstream", "attention", "emotional_inference",
            "social_graph", "personality", "beliefs", "intelligence",
            "vulnerability", "psychometric",
        ]
        
        key_lower = key.lower()
        return any(banned in key_lower for banned in banned_keywords)
    
    def forget_me(self, user_id: str) -> ErasureConfirmation:
        """
        Execute /forget_me endpoint per Article 10.3.
        
        Atomic process:
        1. Delete: All user-provided operational data and configs
        2. Anonymize: Strip identifiers from integrity logs
        3. Confirm: Generate cryptographic erasure proof
        """
        user_id_hash = self._hash_user_id(user_id)
        timestamp = datetime.now(timezone.utc).isoformat()
        erasure_scope = []
        
        # Step 1: Delete all user sessions
        sessions_to_delete = [
            sid for sid, session in self.sessions.items()
            if session.user_id_hash == user_id_hash
        ]
        
        for session_id in sessions_to_delete:
            session = self.sessions[session_id]
            
            # Record what's being deleted
            erasure_scope.append(f"session:{session_id}")
            erasure_scope.extend([
                f"operational:{k}" for k in session.operational_data.keys()
            ])
            erasure_scope.extend([
                f"config:{k}" for k in session.user_config.keys()
            ])
            
            # Delete session data
            del self.sessions[session_id]
        
        # Step 2: Delete any persisted data
        if self.data_dir.exists():
            user_data_path = self.data_dir / user_id_hash
            if user_data_path.exists():
                shutil.rmtree(user_data_path)
                erasure_scope.append(f"filesystem:{user_data_path}")
        
        # Step 3: Anonymize audit logs (replace user_id_hash with "ERASED")
        for event in self.audit_log:
            if event.get("data", {}).get("user_id_hash") == user_id_hash:
                event["data"]["user_id_hash"] = "ERASED"
        
        # Step 4: Generate cryptographic proof
        proof_string = f"ERASURE|{user_id_hash}|{timestamp}|{json.dumps(erasure_scope, sort_keys=True)}|{self.prev_hash}"
        proof_hash = hashlib.sha256(proof_string.encode()).hexdigest()
        
        confirmation = ErasureConfirmation(
            user_id_hash=user_id_hash,
            timestamp=timestamp,
            erasure_scope=erasure_scope,
            prev_hash=self.prev_hash,
            proof_hash=proof_hash,
        )
        
        # Log the erasure (with anonymized reference)
        self._log_event(
            "FORGET_ME_EXECUTED",
            "User data erased",
            {
                "proof_hash": proof_hash,
                "items_erased": len(erasure_scope),
            }
        )
        
        return confirmation
    
    def my_data(self, user_id: str) -> Dict:
        """
        Execute /my_data endpoint per Article 12.2.
        
        Returns a transparent, user-readable dump of all data
        currently held that is linked to their active session.
        """
        user_id_hash = self._hash_user_id(user_id)
        
        # Find all sessions for this user
        user_sessions = [
            session for session in self.sessions.values()
            if session.user_id_hash == user_id_hash
        ]
        
        # Build transparent response
        response = {
            "user_id_hash": user_id_hash,
            "query_timestamp": datetime.now(timezone.utc).isoformat(),
            "data_categories": {
                "operational_data": "Data provided by you to execute tasks",
                "user_config": "Your explicit preferences and settings",
                "system_integrity": "Anonymized metrics (not linked to you)",
            },
            "sessions": [],
            "explicitly_not_held": {
                "biometric_data": None,
                "behavioral_profile": None,
                "cross_session_tracking": None,
                "psychometric_data": None,
                "emotional_memory": None,
                "personality_memory": None,
                "long_term_profile": None,
            },
            "your_rights": {
                "forget_me": "Invoke /forget_me to erase all data",
                "data_portability": "All data shown here is exportable",
                "correction": "Contact support to correct any errors",
            },
        }
        
        for session in user_sessions:
            session_data = {
                "session_id": session.session_id,
                "created_at": session.created_at,
                "operational_data": session.operational_data,
                "user_config": session.user_config,
                "audit_events_count": len(session.audit_events),
            }
            response["sessions"].append(session_data)
        
        self._log_event(
            "MY_DATA_REQUESTED",
            "User requested data transparency",
            {"user_id_hash": user_id_hash}
        )
        
        return response
    
    def validate_metric(self, metric_name: str) -> bool:
        """
        Validate a metric against Article 11.1.
        
        Returns True if permitted, False if banned.
        """
        metric_lower = metric_name.lower().replace(" ", "_")
        
        for banned in self.banned_metrics:
            if banned in metric_lower:
                self._log_event(
                    "BANNED_METRIC_BLOCKED",
                    f"Attempted to track banned metric: {metric_name}",
                    {"metric": metric_name}
                )
                return False
        
        return True
    
    def _hash_user_id(self, user_id: str) -> str:
        """Hash user ID for storage (never store raw)."""
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        random_bytes = os.urandom(8).hex()
        return hashlib.sha256(f"{timestamp}{random_bytes}".encode()).hexdigest()[:16]
    
    def _log_event(self, event_type: str, reason: str, data: Dict = None):
        """Log an event to the audit trail."""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        event_str = f"{event_type}|{reason}|{timestamp}|{self.prev_hash}"
        if data:
            event_str += f"|{json.dumps(data, sort_keys=True)}"
        event_hash = hashlib.sha256(event_str.encode()).hexdigest()
        
        event = {
            "event_type": event_type,
            "reason": reason,
            "timestamp": timestamp,
            "prev_hash": self.prev_hash,
            "hash": event_hash,
            "data": data or {},
        }
        
        self.audit_log.append(event)
        self.prev_hash = event_hash


# =============================================================================
# FastAPI Integration
# =============================================================================

def create_fastapi_routes(app, manager: DataSovereigntyManager):
    """
    Create FastAPI routes for data sovereignty endpoints.
    
    Usage:
        from fastapi import FastAPI
        from data_sovereignty import DataSovereigntyManager, create_fastapi_routes
        
        app = FastAPI()
        manager = DataSovereigntyManager()
        create_fastapi_routes(app, manager)
    """
    from fastapi import HTTPException, Header
    from pydantic import BaseModel
    
    class ForgetMeResponse(BaseModel):
        status: str
        timestamp: str
        proof_hash: str
        items_erased: int
    
    @app.post("/forget_me", response_model=ForgetMeResponse)
    async def forget_me(x_user_id: str = Header(...)):
        """
        Invoke the right to be forgotten.
        
        Atomic process:
        1. Delete all user-provided operational data and configs
        2. Anonymize system integrity logs
        3. Return cryptographic erasure proof
        """
        confirmation = manager.forget_me(x_user_id)
        
        return ForgetMeResponse(
            status=confirmation.status,
            timestamp=confirmation.timestamp,
            proof_hash=confirmation.proof_hash,
            items_erased=len(confirmation.erasure_scope),
        )
    
    @app.get("/my_data")
    async def my_data(x_user_id: str = Header(...)):
        """
        Get all data currently held about you.
        
        Returns a transparent, user-readable dump of all data
        linked to your active session.
        """
        return manager.my_data(x_user_id)
    
    @app.get("/health")
    async def health():
        """System health check (permitted metric)."""
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    @app.get("/status")
    async def status():
        """System status (permitted metric)."""
        return {
            "active_sessions": len(manager.sessions),
            "audit_log_length": len(manager.audit_log),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


if __name__ == "__main__":
    # Test the module
    print("=" * 60)
    print("DATA SOVEREIGNTY MODULE — TEST SUITE")
    print("=" * 60)
    
    manager = DataSovereigntyManager()
    
    # Test session creation
    print("\n[Session Management]")
    session = manager.create_session("test_user_123")
    print(f"✓ Session created: {session.session_id}")
    
    # Test operational data storage
    print("\n[Data Storage]")
    result = manager.store_operational_data(session.session_id, "task_input", "Hello world")
    print(f"✓ Operational data stored: {result}")
    
    # Test banned data rejection
    result = manager.store_operational_data(session.session_id, "biometric_face_scan", "data")
    print(f"✓ Banned data rejected: {not result}")
    
    # Test /my_data
    print("\n[/my_data Endpoint]")
    my_data = manager.my_data("test_user_123")
    print(f"✓ Sessions found: {len(my_data['sessions'])}")
    print(f"✓ Explicitly not held: {list(my_data['explicitly_not_held'].keys())}")
    
    # Test /forget_me
    print("\n[/forget_me Endpoint]")
    confirmation = manager.forget_me("test_user_123")
    print(f"✓ Status: {confirmation.status}")
    print(f"✓ Proof hash: {confirmation.proof_hash[:32]}...")
    print(f"✓ Items erased: {len(confirmation.erasure_scope)}")
    
    # Verify erasure
    my_data_after = manager.my_data("test_user_123")
    print(f"✓ Sessions after erasure: {len(my_data_after['sessions'])}")
    
    # Test metric validation
    print("\n[Metric Validation]")
    print(f"✓ 'request_latency' permitted: {manager.validate_metric('request_latency')}")
    print(f"✓ 'session_length' banned: {not manager.validate_metric('session_length')}")
    print(f"✓ 'click_through_rate' banned: {not manager.validate_metric('click_through_rate')}")
    
    print("\n" + "=" * 60)
    print("DATA SOVEREIGNTY TESTS COMPLETE")
    print("=" * 60)

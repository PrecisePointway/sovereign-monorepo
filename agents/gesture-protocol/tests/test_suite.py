#!/usr/bin/env python3
"""
MANUS GESTURE PROTOCOL — Comprehensive Test Suite
==================================================
Tests all components of the Sovereign Elite OS gesture interface.

USAGE:
    python3 tests/test_suite.py
    python3 tests/test_suite.py --verbose
    python3 tests/test_suite.py --component manus_bridge

AUTHOR: Architect
VERSION: 1.0.0
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# =============================================================================
# TEST FRAMEWORK
# =============================================================================

@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    passed: bool
    duration_ms: float
    message: str = ""
    error: Optional[str] = None


class TestSuite:
    """Simple test suite runner."""
    
    def __init__(self, name: str, verbose: bool = False):
        self.name = name
        self.verbose = verbose
        self.results: list[TestResult] = []
    
    def test(self, name: str):
        """Decorator to register a test function."""
        def decorator(func: Callable):
            def wrapper():
                start = time.time()
                try:
                    result = func()
                    duration = (time.time() - start) * 1000
                    
                    if result is True or result is None:
                        self.results.append(TestResult(name, True, duration))
                        return True
                    else:
                        self.results.append(TestResult(name, False, duration, str(result)))
                        return False
                except Exception as e:
                    duration = (time.time() - start) * 1000
                    self.results.append(TestResult(name, False, duration, error=str(e)))
                    return False
            
            wrapper._test_name = name
            wrapper._test_func = func
            return wrapper
        return decorator
    
    def run_all(self, tests: list[Callable]) -> bool:
        """Run all registered tests."""
        print(f"\n{'=' * 60}")
        print(f"TEST SUITE: {self.name}")
        print(f"{'=' * 60}\n")
        
        for test_func in tests:
            name = getattr(test_func, '_test_name', test_func.__name__)
            if self.verbose:
                print(f"Running: {name}...", end=" ", flush=True)
            
            passed = test_func()
            
            if self.verbose:
                status = "✓ PASS" if passed else "✗ FAIL"
                print(status)
        
        return self.report()
    
    def report(self) -> bool:
        """Print test report and return overall success."""
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        total_time = sum(r.duration_ms for r in self.results)
        
        print(f"\n{'=' * 60}")
        print(f"RESULTS: {passed}/{len(self.results)} passed ({total_time:.2f}ms)")
        print(f"{'=' * 60}")
        
        if failed > 0:
            print("\nFailed tests:")
            for r in self.results:
                if not r.passed:
                    print(f"  ✗ {r.name}")
                    if r.message:
                        print(f"    Message: {r.message}")
                    if r.error:
                        print(f"    Error: {r.error}")
        
        return failed == 0


# =============================================================================
# MANUS BRIDGE TESTS
# =============================================================================

suite = TestSuite("Manus Gesture Protocol", verbose=True)


@suite.test("Import manus_bridge module")
def test_import_manus_bridge():
    from manus_bridge import (
        GestureProtocol, ManusAuthenticator, ManusBridge,
        HashChain, GestureEvent, AuthState
    )
    return True


@suite.test("Load gesture_protocol.yaml")
def test_load_protocol():
    from manus_bridge import GestureProtocol
    protocol = GestureProtocol(Path("gesture_protocol.yaml"))
    
    assert protocol.debounce_ms == 250, f"Expected debounce 250, got {protocol.debounce_ms}"
    assert protocol.confidence_threshold == 0.85
    assert protocol.identity_enforced == True
    assert len(protocol.config["command_map"]) == 6
    return True


@suite.test("Authenticator accepts valid hash")
def test_auth_valid():
    from manus_bridge import ManusAuthenticator
    auth = ManusAuthenticator(["valid-hash-123"])
    
    assert auth.verify("valid-hash-123") == True
    return True


@suite.test("Authenticator rejects invalid hash")
def test_auth_invalid():
    from manus_bridge import ManusAuthenticator
    auth = ManusAuthenticator(["valid-hash-123"])
    
    assert auth.verify("wrong-hash") == False
    assert auth.verify(None) == False
    assert auth.verify("") == False
    return True


@suite.test("Bridge initializes correctly")
def test_bridge_init():
    from manus_bridge import GestureProtocol, ManusAuthenticator, ManusBridge
    
    protocol = GestureProtocol(Path("gesture_protocol.yaml"))
    auth = ManusAuthenticator(["test-hash"])
    bridge = ManusBridge(protocol, auth)
    
    assert bridge.auth_state.is_frozen == False
    assert bridge.auth_state.is_authenticated == False
    assert bridge.auth_state.failed_attempts == 0
    return True


@suite.test("Bridge freezes after max auth failures")
def test_bridge_freeze():
    from manus_bridge import GestureProtocol, ManusAuthenticator, ManusBridge, GestureEvent
    
    protocol = GestureProtocol(Path("gesture_protocol.yaml"))
    auth = ManusAuthenticator(["valid-hash"])
    bridge = ManusBridge(protocol, auth)
    
    # Attempt 3 failed authentications
    for i in range(3):
        event = GestureEvent(
            gesture_id="test",
            confidence=0.9,
            timestamp=time.time(),
            device_mac="AA:BB:CC:DD:EE:FF",
            biometric_hash="wrong-hash"
        )
        bridge.authenticate(event)
    
    assert bridge.auth_state.is_frozen == True
    return True


@suite.test("Bridge rejects low confidence gestures")
def test_low_confidence():
    from manus_bridge import GestureProtocol, ManusAuthenticator, ManusBridge, GestureEvent
    
    protocol = GestureProtocol(Path("gesture_protocol.yaml"))
    auth = ManusAuthenticator(["valid-hash"])
    bridge = ManusBridge(protocol, auth)
    
    # Authenticate first
    auth_event = GestureEvent(
        gesture_id="test",
        confidence=0.9,
        timestamp=time.time(),
        device_mac="AA:BB:CC:DD:EE:FF",
        biometric_hash="valid-hash"
    )
    bridge.authenticate(auth_event)
    
    # Try low confidence gesture
    low_conf_event = GestureEvent(
        gesture_id="fist_hold",
        confidence=0.5,  # Below 0.85 threshold
        timestamp=time.time(),
        device_mac="AA:BB:CC:DD:EE:FF",
        biometric_hash="valid-hash"
    )
    result = bridge.process_gesture(low_conf_event)
    
    assert result == False
    return True


@suite.test("Bridge rejects unmapped gestures")
def test_unmapped_gesture():
    from manus_bridge import GestureProtocol, ManusAuthenticator, ManusBridge, GestureEvent
    
    protocol = GestureProtocol(Path("gesture_protocol.yaml"))
    auth = ManusAuthenticator(["valid-hash"])
    bridge = ManusBridge(protocol, auth)
    
    # Authenticate
    auth_event = GestureEvent(
        gesture_id="test",
        confidence=0.9,
        timestamp=time.time(),
        device_mac="AA:BB:CC:DD:EE:FF",
        biometric_hash="valid-hash"
    )
    bridge.authenticate(auth_event)
    
    # Try unmapped gesture
    unmapped_event = GestureEvent(
        gesture_id="unknown_gesture_xyz",
        confidence=0.95,
        timestamp=time.time(),
        device_mac="AA:BB:CC:DD:EE:FF",
        biometric_hash="valid-hash"
    )
    result = bridge.process_gesture(unmapped_event)
    
    assert result == False
    return True


@suite.test("Hash chain maintains integrity")
def test_hash_chain():
    from manus_bridge import HashChain
    
    test_file = Path("/tmp/test_hash_chain.json")
    if test_file.exists():
        test_file.unlink()
    
    chain = HashChain(test_file)
    
    hash1 = chain.append({"event": "test1"})
    hash2 = chain.append({"event": "test2"})
    hash3 = chain.append({"event": "test3"})
    
    assert len(chain.chain) == 3
    assert chain.chain[0]["prev_hash"] == "GENESIS"
    assert chain.chain[1]["prev_hash"] == chain.chain[0]["hash"]
    assert chain.chain[2]["prev_hash"] == chain.chain[1]["hash"]
    
    # Cleanup
    test_file.unlink()
    return True


# =============================================================================
# IRONCORE KERNEL TESTS
# =============================================================================

@suite.test("Import ironcore_kernel module")
def test_import_ironcore():
    from ironcore_kernel import (
        IronCoreKernel, SpeculativeInferenceEngine,
        RetrievalMemory, SupervisorRouter, ExecutivePersona
    )
    return True


@suite.test("IronCore Kernel initializes")
def test_ironcore_init():
    from ironcore_kernel import IronCoreKernel
    kernel = IronCoreKernel()
    
    assert kernel.l5_inference is not None
    assert kernel.l4_memory is not None
    assert kernel.l3_agents is not None
    assert kernel.l1_persona is not None
    return True


@suite.test("IronCore routes to OPS agent")
def test_ironcore_ops_routing():
    from ironcore_kernel import IronCoreKernel
    
    async def run_test():
        kernel = IronCoreKernel()
        result = await kernel.process("generate system snapshot")
        return result["routing"]["primary_agent"] == "OPS"
    
    return asyncio.run(run_test())


@suite.test("IronCore routes to SECURITY agent")
def test_ironcore_security_routing():
    from ironcore_kernel import IronCoreKernel
    
    async def run_test():
        kernel = IronCoreKernel()
        result = await kernel.process("check for security threats")
        return result["routing"]["primary_agent"] == "SECURITY"
    
    return asyncio.run(run_test())


@suite.test("IronCore memory stores and retrieves")
def test_ironcore_memory():
    from ironcore_kernel import RetrievalMemory
    
    memory = RetrievalMemory()
    memory.store_episodic("Test event about snapshots", "test")
    memory.store_episodic("Another event about security", "test")
    
    results = memory.retrieve_context("snapshot", limit=5)
    assert len(results) >= 1
    return True


@suite.test("IronCore persona adapts mode")
def test_ironcore_persona():
    from ironcore_kernel import ExecutivePersona, PersonaMode
    
    persona = ExecutivePersona()
    
    # High stress + urgent = focused command
    mode1 = persona.adapt_tone(user_stress=0.9, context_priority="urgent")
    assert mode1 == PersonaMode.FOCUSED_COMMAND
    
    # Security context = alert
    mode2 = persona.adapt_tone(context_priority="security")
    assert mode2 == PersonaMode.ALERT
    
    # Default = confident assistant
    mode3 = persona.adapt_tone()
    assert mode3 == PersonaMode.CONFIDENT_ASSISTANT
    
    return True


# =============================================================================
# SCRIPT TESTS
# =============================================================================

@suite.test("health_log.py syntax check")
def test_health_log_syntax():
    result = subprocess.run(
        ["python3", "-m", "py_compile", "scripts/health_log.py"],
        capture_output=True
    )
    return result.returncode == 0


@suite.test("gesture_audit.py syntax check")
def test_gesture_audit_syntax():
    result = subprocess.run(
        ["python3", "-m", "py_compile", "scripts/gesture_audit.py"],
        capture_output=True
    )
    return result.returncode == 0


@suite.test("metabase_control.py syntax check")
def test_metabase_control_syntax():
    result = subprocess.run(
        ["python3", "-m", "py_compile", "scripts/metabase_control.py"],
        capture_output=True
    )
    return result.returncode == 0


@suite.test("airbyte_sync.py syntax check")
def test_airbyte_sync_syntax():
    result = subprocess.run(
        ["python3", "-m", "py_compile", "scripts/airbyte_sync.py"],
        capture_output=True
    )
    return result.returncode == 0


@suite.test("slack_alert.py syntax check")
def test_slack_alert_syntax():
    result = subprocess.run(
        ["python3", "-m", "py_compile", "scripts/slack_alert.py"],
        capture_output=True
    )
    return result.returncode == 0


@suite.test("generate_snapshot.sh syntax check")
def test_snapshot_syntax():
    result = subprocess.run(
        ["bash", "-n", "scripts/generate_snapshot.sh"],
        capture_output=True
    )
    return result.returncode == 0


@suite.test("controlled_shutdown.sh syntax check")
def test_shutdown_syntax():
    result = subprocess.run(
        ["bash", "-n", "scripts/controlled_shutdown.sh"],
        capture_output=True
    )
    return result.returncode == 0


@suite.test("open_dashboard.sh syntax check")
def test_dashboard_syntax():
    result = subprocess.run(
        ["bash", "-n", "scripts/open_dashboard.sh"],
        capture_output=True
    )
    return result.returncode == 0


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

@suite.test("Health log creates CSV output")
def test_health_log_csv():
    result = subprocess.run(
        ["python3", "scripts/health_log.py", "custom", "Integration test"],
        capture_output=True,
        text=True
    )
    
    csv_path = Path("/var/log/health_spring/health_log.csv")
    return csv_path.exists() and result.returncode == 0


@suite.test("Gesture audit exports to CSV")
def test_gesture_audit_export():
    result = subprocess.run(
        ["python3", "scripts/gesture_audit.py", "export"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


@suite.test("Gesture audit verifies hash chain")
def test_gesture_audit_verify():
    result = subprocess.run(
        ["python3", "scripts/gesture_audit.py", "verify"],
        capture_output=True,
        text=True
    )
    return "VALID" in result.stdout or "No events" in result.stdout


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Manus Gesture Protocol Test Suite")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--component", "-c", help="Test specific component")
    args = parser.parse_args()
    
    suite.verbose = args.verbose or True
    
    # Collect all test functions
    tests = [
        # Manus Bridge
        test_import_manus_bridge,
        test_load_protocol,
        test_auth_valid,
        test_auth_invalid,
        test_bridge_init,
        test_bridge_freeze,
        test_low_confidence,
        test_unmapped_gesture,
        test_hash_chain,
        # IronCore Kernel
        test_import_ironcore,
        test_ironcore_init,
        test_ironcore_ops_routing,
        test_ironcore_security_routing,
        test_ironcore_memory,
        test_ironcore_persona,
        # Script syntax
        test_health_log_syntax,
        test_gesture_audit_syntax,
        test_metabase_control_syntax,
        test_airbyte_sync_syntax,
        test_slack_alert_syntax,
        test_snapshot_syntax,
        test_shutdown_syntax,
        test_dashboard_syntax,
        # Integration
        test_health_log_csv,
        test_gesture_audit_export,
        test_gesture_audit_verify,
    ]
    
    # Filter by component if specified
    if args.component:
        component = args.component.lower()
        tests = [t for t in tests if component in t.__name__.lower()]
    
    # Change to package directory
    os.chdir(Path(__file__).parent.parent)
    
    # Run tests
    success = suite.run_all(tests)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

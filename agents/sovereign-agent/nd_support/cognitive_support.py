#!/usr/bin/env python3
"""
Sovereign Agent - Cognitive Load Reduction
ND/ADHD Optimized: External brain, decision reduction, overwhelm prevention
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class CognitiveState(Enum):
    OPTIMAL = "optimal"         # Good to go
    ELEVATED = "elevated"       # Slightly high, monitor
    HIGH = "high"               # Intervention suggested
    OVERWHELMED = "overwhelmed" # Immediate intervention


class EnergyState(Enum):
    HIGH = "high"       # Deep work capable
    MEDIUM = "medium"   # Standard tasks
    LOW = "low"         # Routine only
    DEPLETED = "depleted"  # Rest needed


@dataclass
class CognitiveSnapshot:
    """Point-in-time cognitive state."""
    timestamp: str
    state: CognitiveState
    energy: EnergyState
    indicators: Dict[str, int]
    notes: str = ""


class CognitiveLoadMonitor:
    """
    Monitors cognitive load indicators and suggests interventions.
    
    ND/ADHD Features:
    - Tracks decision fatigue
    - Detects overwhelm early
    - Suggests appropriate interventions
    - Non-judgmental feedback
    """
    
    # Thresholds (configurable)
    THRESHOLDS = {
        "task_switches": {"elevated": 5, "high": 10, "overwhelmed": 15},
        "incomplete_tasks": {"elevated": 5, "high": 8, "overwhelmed": 12},
        "decisions_made": {"elevated": 15, "high": 25, "overwhelmed": 40},
        "minutes_since_break": {"elevated": 60, "high": 90, "overwhelmed": 120},
        "context_switches": {"elevated": 3, "high": 6, "overwhelmed": 10},
    }
    
    def __init__(self, storage_path: str = "/var/lib/sovereign_agent/cognitive.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Current session indicators
        self.indicators = {
            "task_switches": 0,
            "incomplete_tasks": 0,
            "decisions_made": 0,
            "minutes_since_break": 0,
            "context_switches": 0,
        }
        
        self.session_start = datetime.now()
        self.last_break = datetime.now()
        self.history: List[CognitiveSnapshot] = []
        
        self.load()
    
    # === Indicator Tracking ===
    
    def record_task_switch(self):
        """Record a task switch."""
        self.indicators["task_switches"] += 1
        self.indicators["context_switches"] += 1
        self._check_and_alert()
    
    def record_decision(self):
        """Record a decision made."""
        self.indicators["decisions_made"] += 1
        self._check_and_alert()
    
    def record_incomplete_task(self):
        """Record an incomplete task."""
        self.indicators["incomplete_tasks"] += 1
        self._check_and_alert()
    
    def record_task_complete(self):
        """Record a completed task (reduces load)."""
        self.indicators["incomplete_tasks"] = max(0, self.indicators["incomplete_tasks"] - 1)
    
    def record_break(self, minutes: int = 5):
        """Record a break taken."""
        self.last_break = datetime.now()
        self.indicators["minutes_since_break"] = 0
        # Breaks reduce other indicators slightly
        self.indicators["context_switches"] = max(0, self.indicators["context_switches"] - 2)
    
    def update_time_indicators(self):
        """Update time-based indicators."""
        self.indicators["minutes_since_break"] = int(
            (datetime.now() - self.last_break).total_seconds() / 60
        )
    
    # === State Assessment ===
    
    def get_state(self) -> Tuple[CognitiveState, Dict[str, Any]]:
        """
        Assess current cognitive state.
        Returns state and detailed breakdown.
        """
        self.update_time_indicators()
        
        # Check each indicator against thresholds
        indicator_states = {}
        worst_state = CognitiveState.OPTIMAL
        
        for indicator, value in self.indicators.items():
            thresholds = self.THRESHOLDS.get(indicator, {})
            
            if value >= thresholds.get("overwhelmed", float('inf')):
                state = CognitiveState.OVERWHELMED
            elif value >= thresholds.get("high", float('inf')):
                state = CognitiveState.HIGH
            elif value >= thresholds.get("elevated", float('inf')):
                state = CognitiveState.ELEVATED
            else:
                state = CognitiveState.OPTIMAL
            
            indicator_states[indicator] = {
                "value": value,
                "state": state.value,
                "threshold_elevated": thresholds.get("elevated"),
                "threshold_high": thresholds.get("high"),
            }
            
            # Track worst state
            if state.value > worst_state.value:
                worst_state = state
        
        return worst_state, indicator_states
    
    def _check_and_alert(self):
        """Check state and trigger alert if needed."""
        state, _ = self.get_state()
        
        if state in (CognitiveState.HIGH, CognitiveState.OVERWHELMED):
            self._snapshot()
    
    def _snapshot(self):
        """Take a cognitive snapshot for history."""
        state, indicators = self.get_state()
        snapshot = CognitiveSnapshot(
            timestamp=datetime.now().isoformat(),
            state=state,
            energy=self._estimate_energy(),
            indicators=self.indicators.copy()
        )
        self.history.append(snapshot)
        self.save()
    
    def _estimate_energy(self) -> EnergyState:
        """Estimate current energy level."""
        minutes_working = (datetime.now() - self.session_start).total_seconds() / 60
        
        if minutes_working < 60:
            return EnergyState.HIGH
        elif minutes_working < 180:
            return EnergyState.MEDIUM
        elif minutes_working < 300:
            return EnergyState.LOW
        else:
            return EnergyState.DEPLETED
    
    # === Interventions ===
    
    def get_intervention(self) -> Optional[Dict[str, Any]]:
        """
        Get appropriate intervention based on current state.
        Non-judgmental, action-oriented.
        """
        state, indicators = self.get_state()
        
        if state == CognitiveState.OPTIMAL:
            return None
        
        interventions = {
            CognitiveState.ELEVATED: {
                "level": "gentle",
                "title": "Cognitive Load Notice",
                "message": "Your cognitive load is slightly elevated. This is normal.\n\nConsider:\n• Taking a short break soon\n• Finishing current task before switching\n• Deferring non-urgent decisions",
                "actions": ["take_break", "defer_decisions", "dismiss"]
            },
            CognitiveState.HIGH: {
                "level": "moderate",
                "title": "High Cognitive Load",
                "message": "Your cognitive load is high. Time to lighten the load.\n\nRecommended:\n• Take a 10-minute break now\n• Pick ONE task to focus on\n• Defer all non-critical decisions\n\nYou're not failing - your brain just needs a reset.",
                "actions": ["take_break", "pick_one_task", "defer_all", "dismiss"]
            },
            CognitiveState.OVERWHELMED: {
                "level": "urgent",
                "title": "Overwhelm Detected",
                "message": "STOP. Take a breath.\n\nYour system is overloaded. This is not a failure - it's information.\n\nImmediate actions:\n1. Step away from screen (5 min)\n2. Drink water\n3. When you return, pick ONE small thing\n\nEverything else can wait.",
                "actions": ["emergency_break", "clear_queue", "pick_micro_task"]
            }
        }
        
        intervention = interventions.get(state)
        if intervention:
            intervention["state"] = state.value
            intervention["indicators"] = indicators
        
        return intervention
    
    def apply_intervention(self, action: str) -> Dict[str, Any]:
        """Apply a suggested intervention action."""
        
        actions = {
            "take_break": self._action_take_break,
            "defer_decisions": self._action_defer_decisions,
            "pick_one_task": self._action_pick_one,
            "defer_all": self._action_defer_all,
            "emergency_break": self._action_emergency_break,
            "clear_queue": self._action_clear_queue,
            "pick_micro_task": self._action_micro_task,
        }
        
        action_fn = actions.get(action)
        if action_fn:
            return action_fn()
        
        return {"success": False, "error": "Unknown action"}
    
    def _action_take_break(self) -> Dict[str, Any]:
        self.record_break(10)
        return {
            "success": True,
            "message": "Break recorded. Timer set for 10 minutes.\n\nStretch, hydrate, look at something far away.",
            "duration": 10
        }
    
    def _action_defer_decisions(self) -> Dict[str, Any]:
        return {
            "success": True,
            "message": "Decision deferral mode active.\n\nFor the next hour, all non-critical decisions will be queued for later.",
            "mode": "defer_decisions"
        }
    
    def _action_pick_one(self) -> Dict[str, Any]:
        return {
            "success": True,
            "message": "Single-task mode active.\n\nOnly your ONE chosen task will be visible.\n\nWhat's the most important thing right now?",
            "mode": "single_task"
        }
    
    def _action_defer_all(self) -> Dict[str, Any]:
        return {
            "success": True,
            "message": "All non-critical items deferred to tomorrow.\n\nYour queue is now clear except for critical items.",
            "deferred": True
        }
    
    def _action_emergency_break(self) -> Dict[str, Any]:
        self.record_break(15)
        # Reset some indicators
        self.indicators["context_switches"] = 0
        self.indicators["task_switches"] = max(0, self.indicators["task_switches"] - 5)
        self.save()
        return {
            "success": True,
            "message": "Emergency break initiated.\n\nStep away NOW. 15 minutes minimum.\n\nThe work will be here when you get back.",
            "duration": 15,
            "mandatory": True
        }
    
    def _action_clear_queue(self) -> Dict[str, Any]:
        self.indicators["incomplete_tasks"] = 0
        self.save()
        return {
            "success": True,
            "message": "Queue cleared.\n\nAll tasks moved to 'Someday'. Nothing is due today.\n\nStart fresh.",
            "cleared": True
        }
    
    def _action_micro_task(self) -> Dict[str, Any]:
        return {
            "success": True,
            "message": "Micro-task mode.\n\nWhat's ONE tiny thing you can do in 2 minutes?\n\nJust one. That's all.",
            "mode": "micro_task",
            "time_limit": 2
        }
    
    # === Session Management ===
    
    def start_session(self):
        """Start a new work session."""
        self.session_start = datetime.now()
        self.last_break = datetime.now()
        self.indicators = {k: 0 for k in self.indicators}
        self.save()
    
    def end_session(self) -> Dict[str, Any]:
        """End work session and get summary."""
        duration = (datetime.now() - self.session_start).total_seconds() / 60
        
        summary = {
            "duration_minutes": int(duration),
            "task_switches": self.indicators["task_switches"],
            "decisions_made": self.indicators["decisions_made"],
            "breaks_taken": len([h for h in self.history 
                                 if h.timestamp >= self.session_start.isoformat()]),
            "peak_state": max([h.state.value for h in self.history] or [CognitiveState.OPTIMAL.value])
        }
        
        self._snapshot()
        return summary
    
    # === Persistence ===
    
    def save(self):
        """Save state to disk."""
        data = {
            "indicators": self.indicators,
            "session_start": self.session_start.isoformat(),
            "last_break": self.last_break.isoformat(),
            "history": [
                {
                    "timestamp": h.timestamp,
                    "state": h.state.value,
                    "energy": h.energy.value,
                    "indicators": h.indicators,
                    "notes": h.notes
                }
                for h in self.history[-100:]  # Keep last 100
            ],
            "saved_at": datetime.now().isoformat()
        }
        self.storage_path.write_text(json.dumps(data, indent=2))
    
    def load(self):
        """Load state from disk."""
        if self.storage_path.exists():
            data = json.loads(self.storage_path.read_text())
            self.indicators = data.get("indicators", self.indicators)
            self.session_start = datetime.fromisoformat(data.get("session_start", datetime.now().isoformat()))
            self.last_break = datetime.fromisoformat(data.get("last_break", datetime.now().isoformat()))
            self.history = [
                CognitiveSnapshot(
                    timestamp=h["timestamp"],
                    state=CognitiveState(h["state"]),
                    energy=EnergyState(h["energy"]),
                    indicators=h["indicators"],
                    notes=h.get("notes", "")
                )
                for h in data.get("history", [])
            ]


class DecisionReducer:
    """
    Reduces decision fatigue by automating routine choices.
    
    ND/ADHD Features:
    - Pre-made decisions for common scenarios
    - Defaults that just work
    - One-tap actions
    """
    
    def __init__(self):
        # Pre-configured defaults
        self.defaults = {
            "snooze_duration": 15,  # minutes
            "break_duration": 10,   # minutes
            "focus_duration": 90,   # minutes
            "defer_to": "tomorrow",
            "priority_threshold": 2,  # Only show HIGH and above
            "energy_match": True,     # Match tasks to energy
        }
        
        # Pre-made decision rules
        self.rules = {
            "new_email": "inbox",           # Don't decide, just inbox
            "new_task": "inbox",            # Process later
            "unclear_priority": "medium",   # Default to medium
            "no_due_date": "someday",       # No pressure
            "interruption": "queue",        # Queue it
        }
    
    def decide(self, scenario: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make a decision automatically.
        Returns the decision and rationale.
        """
        rule = self.rules.get(scenario)
        
        if rule:
            return {
                "decision": rule,
                "automatic": True,
                "rationale": f"Auto-decided based on rule: {scenario} → {rule}",
                "override_available": True
            }
        
        return {
            "decision": None,
            "automatic": False,
            "rationale": "No automatic rule. Human decision needed.",
            "suggestions": self._get_suggestions(scenario, context)
        }
    
    def _get_suggestions(self, scenario: str, context: Dict[str, Any]) -> List[str]:
        """Get decision suggestions for unknown scenarios."""
        return [
            "Defer to tomorrow",
            "Do it now (2 min rule)",
            "Delegate",
            "Delete/ignore"
        ]


# === CLI Interface ===

if __name__ == "__main__":
    monitor = CognitiveLoadMonitor("/tmp/test_cognitive.json")
    
    print("=== Sovereign Agent - Cognitive Support ===")
    print("ND/ADHD Optimized: External brain, overwhelm prevention\n")
    
    # Simulate some activity
    print("Simulating work session...")
    monitor.start_session()
    
    for i in range(8):
        monitor.record_task_switch()
        monitor.record_decision()
    
    monitor.record_incomplete_task()
    monitor.record_incomplete_task()
    monitor.record_incomplete_task()
    
    # Check state
    state, indicators = monitor.get_state()
    print(f"\nCurrent State: {state.value.upper()}")
    print("\nIndicators:")
    for name, data in indicators.items():
        print(f"  {name}: {data['value']} ({data['state']})")
    
    # Get intervention
    intervention = monitor.get_intervention()
    if intervention:
        print(f"\n{intervention['title']}")
        print(intervention['message'])
    
    print("\n✓ Cognitive Support Test Complete")

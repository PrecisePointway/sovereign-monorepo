#!/usr/bin/env python3
"""
Sovereign Agent - Task Queue
ND/ADHD Optimized: One task at a time, context preservation, overwhelm prevention
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field, asdict
import uuid


class Priority(Enum):
    CRITICAL = 1    # Do now, interrupt allowed
    HIGH = 2        # Do today
    MEDIUM = 3      # Do this week
    LOW = 4         # Do eventually
    SOMEDAY = 5     # Maybe never


class EnergyLevel(Enum):
    HIGH = "high"       # Deep focus work
    MEDIUM = "medium"   # Standard tasks
    LOW = "low"         # Routine, low-effort


class TaskState(Enum):
    INBOX = "inbox"           # Uncategorized
    READY = "ready"           # Ready to work
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    WAITING = "waiting"       # Waiting on external
    DONE = "done"
    DEFERRED = "deferred"


@dataclass
class Task:
    """A single task with full context preservation."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    
    # Classification
    priority: Priority = Priority.MEDIUM
    energy_required: EnergyLevel = EnergyLevel.MEDIUM
    state: TaskState = TaskState.INBOX
    
    # Time
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    due_date: Optional[str] = None
    estimated_minutes: int = 30
    time_spent_minutes: int = 0
    
    # Context (ND/ADHD critical)
    context_notes: str = ""           # Where you left off
    next_action: str = ""             # Smallest next step
    blockers: List[str] = field(default_factory=list)
    
    # Relationships
    project: str = ""
    tags: List[str] = field(default_factory=list)
    parent_task: Optional[str] = None
    subtasks: List[str] = field(default_factory=list)
    
    # Metadata
    source: str = "manual"            # Where task came from
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['priority'] = self.priority.value
        d['energy_required'] = self.energy_required.value
        d['state'] = self.state.value
        return d
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Task':
        d['priority'] = Priority(d['priority'])
        d['energy_required'] = EnergyLevel(d['energy_required'])
        d['state'] = TaskState(d['state'])
        return cls(**d)
    
    def micro_action(self) -> str:
        """Return the smallest possible action to start."""
        if self.next_action:
            return self.next_action
        return f"Open/look at: {self.title}"


class TaskQueue:
    """
    ND/ADHD-Optimized Task Queue
    
    Features:
    - One task at a time view (optional)
    - Automatic prioritization
    - Context preservation on switch
    - Overwhelm detection
    - Energy-aware sorting
    """
    
    def __init__(self, storage_path: str = "/var/lib/sovereign_agent/tasks.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.tasks: Dict[str, Task] = {}
        self.current_task_id: Optional[str] = None
        self.load()
    
    # === CRUD Operations ===
    
    def add(self, title: str, **kwargs) -> Task:
        """Add a new task to the queue."""
        task = Task(title=title, **kwargs)
        self.tasks[task.id] = task
        self.save()
        return task
    
    def get(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def update(self, task_id: str, **kwargs) -> Optional[Task]:
        """Update a task's fields."""
        task = self.tasks.get(task_id)
        if not task:
            return None
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        self.save()
        return task
    
    def delete(self, task_id: str) -> bool:
        """Delete a task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.save()
            return True
        return False
    
    # === ND/ADHD Optimized Views ===
    
    def get_one_task(self, energy: Optional[EnergyLevel] = None) -> Optional[Task]:
        """
        Get exactly ONE task to work on.
        Reduces overwhelm by hiding the rest.
        """
        ready_tasks = [t for t in self.tasks.values() 
                       if t.state in (TaskState.READY, TaskState.IN_PROGRESS)]
        
        if not ready_tasks:
            return None
        
        # Filter by energy if specified
        if energy:
            energy_match = [t for t in ready_tasks if t.energy_required == energy]
            if energy_match:
                ready_tasks = energy_match
        
        # Sort by priority, then due date
        ready_tasks.sort(key=lambda t: (
            t.priority.value,
            t.due_date or "9999-99-99"
        ))
        
        return ready_tasks[0]
    
    def get_today(self) -> List[Task]:
        """Get tasks for today only."""
        today = datetime.now().date().isoformat()
        tomorrow = (datetime.now().date() + timedelta(days=1)).isoformat()
        
        return [t for t in self.tasks.values()
                if t.state in (TaskState.READY, TaskState.IN_PROGRESS)
                and (t.due_date is None or t.due_date < tomorrow)
                and t.priority.value <= Priority.HIGH.value]
    
    def get_by_energy(self, energy: EnergyLevel) -> List[Task]:
        """Get tasks matching current energy level."""
        return [t for t in self.tasks.values()
                if t.state == TaskState.READY
                and t.energy_required == energy]
    
    # === Context Preservation ===
    
    def start_task(self, task_id: str) -> Dict[str, Any]:
        """
        Start working on a task.
        Returns context if resuming.
        """
        task = self.tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}
        
        # Save context of current task if switching
        if self.current_task_id and self.current_task_id != task_id:
            self._pause_current()
        
        task.state = TaskState.IN_PROGRESS
        self.current_task_id = task_id
        self.save()
        
        # Return context for resumption
        return {
            "task": task.to_dict(),
            "context": task.context_notes,
            "next_action": task.micro_action(),
            "time_spent": task.time_spent_minutes,
            "message": f"Starting: {task.title}\n\nNext action: {task.micro_action()}"
        }
    
    def pause_task(self, task_id: str, context_notes: str = "", next_action: str = "") -> Task:
        """
        Pause a task with context preservation.
        Critical for ND/ADHD - never lose where you were.
        """
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        task.state = TaskState.READY
        if context_notes:
            task.context_notes = context_notes
        if next_action:
            task.next_action = next_action
        
        if self.current_task_id == task_id:
            self.current_task_id = None
        
        self.save()
        return task
    
    def complete_task(self, task_id: str) -> Task:
        """Mark a task as done. Celebration moment!"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        task.state = TaskState.DONE
        task.completed_at = datetime.now().isoformat()
        
        if self.current_task_id == task_id:
            self.current_task_id = None
        
        self.save()
        return task
    
    def _pause_current(self):
        """Internal: pause current task when switching."""
        if self.current_task_id:
            task = self.tasks.get(self.current_task_id)
            if task:
                task.state = TaskState.READY
    
    # === Overwhelm Prevention ===
    
    def check_overwhelm(self) -> Dict[str, Any]:
        """
        Check for overwhelm indicators.
        Returns intervention suggestions if needed.
        """
        active_tasks = [t for t in self.tasks.values() 
                        if t.state in (TaskState.READY, TaskState.IN_PROGRESS)]
        urgent_tasks = [t for t in active_tasks if t.priority.value <= 2]
        overdue_tasks = [t for t in active_tasks 
                         if t.due_date and t.due_date < datetime.now().date().isoformat()]
        
        signals = {
            "too_many_active": len(active_tasks) > 10,
            "too_many_urgent": len(urgent_tasks) > 3,
            "has_overdue": len(overdue_tasks) > 0,
            "no_clear_priority": len(urgent_tasks) == 0 and len(active_tasks) > 5,
        }
        
        overwhelmed = any(signals.values())
        
        return {
            "overwhelmed": overwhelmed,
            "signals": signals,
            "active_count": len(active_tasks),
            "urgent_count": len(urgent_tasks),
            "overdue_count": len(overdue_tasks),
            "intervention": self._get_intervention(signals) if overwhelmed else None
        }
    
    def _get_intervention(self, signals: Dict[str, bool]) -> str:
        """Generate intervention message for overwhelm."""
        messages = []
        
        if signals["too_many_active"]:
            messages.append("• Too many active tasks. Let's defer some to tomorrow.")
        if signals["too_many_urgent"]:
            messages.append("• Multiple urgent items. Pick ONE to focus on.")
        if signals["has_overdue"]:
            messages.append("• Overdue tasks detected. Reschedule or complete.")
        if signals["no_clear_priority"]:
            messages.append("• No clear priority. Let's identify the most important task.")
        
        return """
OVERWHELM DETECTED

Recommended actions:
1. STOP - Take 5 deep breaths
2. PICK ONE - Just one task, the most important
3. SHRINK IT - What's the smallest first step?
4. DEFER - Move non-urgent to tomorrow

Issues detected:
""" + "\n".join(messages)
    
    def auto_defer_non_urgent(self) -> int:
        """Automatically defer non-urgent tasks to reduce overwhelm."""
        deferred_count = 0
        tomorrow = (datetime.now().date() + timedelta(days=1)).isoformat()
        
        for task in self.tasks.values():
            if (task.state == TaskState.READY 
                and task.priority.value >= Priority.MEDIUM.value
                and (task.due_date is None or task.due_date > tomorrow)):
                task.state = TaskState.DEFERRED
                task.due_date = tomorrow
                deferred_count += 1
        
        self.save()
        return deferred_count
    
    # === Quick Capture ===
    
    def quick_add(self, text: str) -> Task:
        """
        Quick capture - just get it out of your head.
        Parsing and prioritization happens later.
        """
        task = Task(
            title=text,
            state=TaskState.INBOX,
            source="quick_capture"
        )
        self.tasks[task.id] = task
        self.save()
        return task
    
    def process_inbox(self) -> List[Task]:
        """Get all inbox items for processing."""
        return [t for t in self.tasks.values() if t.state == TaskState.INBOX]
    
    # === Persistence ===
    
    def save(self):
        """Save tasks to disk."""
        data = {
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
            "current_task_id": self.current_task_id,
            "saved_at": datetime.now().isoformat()
        }
        self.storage_path.write_text(json.dumps(data, indent=2))
    
    def load(self):
        """Load tasks from disk."""
        if self.storage_path.exists():
            data = json.loads(self.storage_path.read_text())
            self.tasks = {k: Task.from_dict(v) for k, v in data.get("tasks", {}).items()}
            self.current_task_id = data.get("current_task_id")
    
    # === Statistics ===
    
    def stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        by_state = {}
        for task in self.tasks.values():
            state = task.state.value
            by_state[state] = by_state.get(state, 0) + 1
        
        completed_today = len([t for t in self.tasks.values()
                               if t.state == TaskState.DONE
                               and t.completed_at
                               and t.completed_at.startswith(datetime.now().date().isoformat())])
        
        return {
            "total": len(self.tasks),
            "by_state": by_state,
            "completed_today": completed_today,
            "current_task": self.current_task_id
        }


# === CLI Interface ===

if __name__ == "__main__":
    import sys
    
    queue = TaskQueue("/tmp/test_tasks.json")
    
    # Demo
    print("=== Sovereign Agent Task Queue ===")
    print("ND/ADHD Optimized\n")
    
    # Add sample tasks
    queue.add("Review S.A.F.E.-OS deployment", priority=Priority.HIGH, energy_required=EnergyLevel.HIGH)
    queue.add("Post LinkedIn announcement", priority=Priority.MEDIUM, energy_required=EnergyLevel.LOW)
    queue.add("Submit Consulta Previa", priority=Priority.CRITICAL, energy_required=EnergyLevel.MEDIUM)
    
    # Get one task
    print("ONE TASK TO FOCUS ON:")
    task = queue.get_one_task()
    if task:
        print(f"  → {task.title}")
        print(f"    Priority: {task.priority.name}")
        print(f"    Next action: {task.micro_action()}")
    
    print("\n" + "="*40)
    
    # Check overwhelm
    status = queue.check_overwhelm()
    print(f"Overwhelm check: {'⚠️ OVERWHELMED' if status['overwhelmed'] else '✓ OK'}")
    print(f"Active tasks: {status['active_count']}")
    
    print("\n✓ Task Queue Test Complete")

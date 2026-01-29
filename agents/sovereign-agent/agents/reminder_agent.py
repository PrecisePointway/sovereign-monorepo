#!/usr/bin/env python3
"""
Sovereign Agent - Reminder & Notification System
ND/ADHD Optimized: Gentle nudges, no overwhelm, context-aware
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid


class ReminderType(Enum):
    TASK = "task"           # Task deadline
    HEALTH = "health"       # Health protocol
    BREAK = "break"         # Break reminder
    TRANSITION = "transition"  # Task transition
    CUSTOM = "custom"


class Urgency(Enum):
    GENTLE = "gentle"       # Can be ignored
    NORMAL = "normal"       # Should see
    IMPORTANT = "important" # Needs attention
    CRITICAL = "critical"   # Interrupt allowed


class DeliveryMethod(Enum):
    SILENT = "silent"       # Log only
    NOTIFICATION = "notification"  # System notification
    SOUND = "sound"         # With sound
    VOICE = "voice"         # Text-to-speech


@dataclass
class Reminder:
    """A single reminder with ND/ADHD-friendly options."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    message: str = ""
    
    # Type and urgency
    reminder_type: ReminderType = ReminderType.CUSTOM
    urgency: Urgency = Urgency.NORMAL
    
    # Timing
    trigger_time: str = ""  # ISO format
    repeat: Optional[str] = None  # cron-like or "daily", "hourly"
    snooze_count: int = 0
    max_snoozes: int = 3
    
    # Delivery
    delivery: DeliveryMethod = DeliveryMethod.NOTIFICATION
    
    # State
    triggered: bool = False
    dismissed: bool = False
    snoozed_until: Optional[str] = None
    
    # Context
    related_task_id: Optional[str] = None
    action_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['reminder_type'] = self.reminder_type.value
        d['urgency'] = self.urgency.value
        d['delivery'] = self.delivery.value
        return d
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Reminder':
        d['reminder_type'] = ReminderType(d['reminder_type'])
        d['urgency'] = Urgency(d['urgency'])
        d['delivery'] = DeliveryMethod(d['delivery'])
        return cls(**d)


class ReminderAgent:
    """
    ND/ADHD-Optimized Reminder System
    
    Features:
    - Gentle, non-judgmental reminders
    - Smart batching (no notification spam)
    - Context-aware timing
    - Snooze without guilt
    - Break reminders
    """
    
    def __init__(self, storage_path: str = "/var/lib/sovereign_agent/reminders.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.reminders: Dict[str, Reminder] = {}
        self.notification_queue: List[Reminder] = []
        self.focus_mode: bool = False
        self.load()
    
    # === Reminder Creation ===
    
    def create(self, title: str, trigger_time: str, **kwargs) -> Reminder:
        """Create a new reminder."""
        reminder = Reminder(
            title=title,
            trigger_time=trigger_time,
            **kwargs
        )
        self.reminders[reminder.id] = reminder
        self.save()
        return reminder
    
    def create_health_reminder(self, title: str, time: str, repeat: str = "daily") -> Reminder:
        """Create a health protocol reminder (gentle, repeating)."""
        return self.create(
            title=title,
            trigger_time=self._next_occurrence(time),
            reminder_type=ReminderType.HEALTH,
            urgency=Urgency.GENTLE,
            delivery=DeliveryMethod.NOTIFICATION,
            repeat=repeat,
            message=f"Time for: {title}\n\nNo pressure. Just a gentle nudge."
        )
    
    def create_break_reminder(self, minutes: int = 90) -> Reminder:
        """Create a break reminder."""
        trigger = (datetime.now() + timedelta(minutes=minutes)).isoformat()
        return self.create(
            title="Break Time",
            trigger_time=trigger,
            reminder_type=ReminderType.BREAK,
            urgency=Urgency.GENTLE,
            delivery=DeliveryMethod.NOTIFICATION,
            message="You've been working for a while.\n\nStretch, hydrate, look away from screen.\n\nYou're doing great."
        )
    
    def create_task_reminder(self, task_id: str, task_title: str, due_time: str) -> Reminder:
        """Create a task deadline reminder."""
        # Create multiple reminders: 1 day, 1 hour, 15 min before
        reminders = []
        
        due = datetime.fromisoformat(due_time)
        
        # 1 day before (if applicable)
        day_before = due - timedelta(days=1)
        if day_before > datetime.now():
            reminders.append(self.create(
                title=f"Due tomorrow: {task_title}",
                trigger_time=day_before.isoformat(),
                reminder_type=ReminderType.TASK,
                urgency=Urgency.NORMAL,
                related_task_id=task_id,
                message=f"'{task_title}' is due tomorrow.\n\nWant to start now while it's fresh?"
            ))
        
        # 1 hour before
        hour_before = due - timedelta(hours=1)
        if hour_before > datetime.now():
            reminders.append(self.create(
                title=f"Due in 1 hour: {task_title}",
                trigger_time=hour_before.isoformat(),
                reminder_type=ReminderType.TASK,
                urgency=Urgency.IMPORTANT,
                related_task_id=task_id,
                message=f"'{task_title}' is due in 1 hour.\n\nWhat's the smallest step you can take?"
            ))
        
        return reminders[-1] if reminders else None
    
    def _next_occurrence(self, time_str: str) -> str:
        """Get next occurrence of a time (today or tomorrow)."""
        today = datetime.now().date()
        target = datetime.strptime(f"{today} {time_str}", "%Y-%m-%d %H:%M")
        
        if target <= datetime.now():
            target += timedelta(days=1)
        
        return target.isoformat()
    
    # === Reminder Processing ===
    
    def get_due_reminders(self) -> List[Reminder]:
        """Get reminders that are due now."""
        now = datetime.now().isoformat()
        due = []
        
        for reminder in self.reminders.values():
            if reminder.dismissed:
                continue
            if reminder.triggered and not reminder.repeat:
                continue
            if reminder.snoozed_until and reminder.snoozed_until > now:
                continue
            if reminder.trigger_time <= now:
                due.append(reminder)
        
        return due
    
    def process_reminders(self) -> List[Dict[str, Any]]:
        """
        Process due reminders.
        Respects focus mode and batches appropriately.
        """
        due = self.get_due_reminders()
        results = []
        
        for reminder in due:
            # Check focus mode
            if self.focus_mode and reminder.urgency != Urgency.CRITICAL:
                self.notification_queue.append(reminder)
                continue
            
            # Deliver reminder
            result = self._deliver(reminder)
            results.append(result)
            
            # Mark as triggered
            reminder.triggered = True
            
            # Handle repeat
            if reminder.repeat:
                self._schedule_next(reminder)
        
        self.save()
        return results
    
    def _deliver(self, reminder: Reminder) -> Dict[str, Any]:
        """Deliver a reminder notification."""
        
        # Build notification
        notification = {
            "id": reminder.id,
            "title": reminder.title,
            "message": reminder.message,
            "urgency": reminder.urgency.value,
            "type": reminder.reminder_type.value,
            "actions": ["dismiss", "snooze"]
        }
        
        if reminder.related_task_id:
            notification["actions"].append("open_task")
        
        # In production, send to notification system
        # For now, return the notification data
        
        return {
            "delivered": True,
            "notification": notification,
            "delivery_method": reminder.delivery.value
        }
    
    def _schedule_next(self, reminder: Reminder):
        """Schedule next occurrence for repeating reminders."""
        if reminder.repeat == "daily":
            next_time = datetime.fromisoformat(reminder.trigger_time) + timedelta(days=1)
        elif reminder.repeat == "hourly":
            next_time = datetime.fromisoformat(reminder.trigger_time) + timedelta(hours=1)
        elif reminder.repeat == "weekly":
            next_time = datetime.fromisoformat(reminder.trigger_time) + timedelta(weeks=1)
        else:
            return
        
        reminder.trigger_time = next_time.isoformat()
        reminder.triggered = False
    
    # === User Actions ===
    
    def snooze(self, reminder_id: str, minutes: int = 15) -> Optional[Reminder]:
        """
        Snooze a reminder without guilt.
        ND/ADHD friendly: snoozing is okay!
        """
        reminder = self.reminders.get(reminder_id)
        if not reminder:
            return None
        
        if reminder.snooze_count >= reminder.max_snoozes:
            # Gentle message, not punitive
            reminder.message = f"{reminder.message}\n\n(This has been snoozed a few times. No judgment - just noting it.)"
        
        reminder.snooze_count += 1
        reminder.snoozed_until = (datetime.now() + timedelta(minutes=minutes)).isoformat()
        reminder.triggered = False
        
        self.save()
        return reminder
    
    def dismiss(self, reminder_id: str) -> Optional[Reminder]:
        """Dismiss a reminder."""
        reminder = self.reminders.get(reminder_id)
        if not reminder:
            return None
        
        reminder.dismissed = True
        self.save()
        return reminder
    
    def dismiss_all_gentle(self) -> int:
        """Dismiss all gentle reminders (overwhelm relief)."""
        count = 0
        for reminder in self.reminders.values():
            if reminder.urgency == Urgency.GENTLE and not reminder.dismissed:
                reminder.dismissed = True
                count += 1
        self.save()
        return count
    
    # === Focus Mode ===
    
    def enter_focus_mode(self, duration_minutes: int = 90):
        """
        Enter focus mode - queue non-critical notifications.
        Auto-schedules break reminder.
        """
        self.focus_mode = True
        self.create_break_reminder(duration_minutes)
        self.save()
        return {
            "focus_mode": True,
            "duration": duration_minutes,
            "break_scheduled": True,
            "message": f"Focus mode active for {duration_minutes} minutes.\n\nOnly critical notifications will interrupt."
        }
    
    def exit_focus_mode(self) -> Dict[str, Any]:
        """Exit focus mode and deliver queued notifications."""
        self.focus_mode = False
        
        queued_count = len(self.notification_queue)
        
        # Batch deliver queued notifications
        if self.notification_queue:
            # Group by type for cleaner delivery
            summary = f"While you were focused:\n\n"
            for reminder in self.notification_queue:
                summary += f"• {reminder.title}\n"
            
            self.notification_queue = []
        else:
            summary = "No notifications while you were focused."
        
        self.save()
        return {
            "focus_mode": False,
            "queued_delivered": queued_count,
            "summary": summary
        }
    
    # === Health Protocol Integration ===
    
    def setup_health_protocol(self) -> List[Reminder]:
        """
        Set up the full Health Spring Protocol reminders.
        One command, all reminders configured.
        """
        protocol = [
            ("Peptides: BPC-157 + TB-500", "07:30"),
            ("Hydration + Electrolytes", "08:00"),
            ("Breakfast: Protein + Healthy Fats", "09:00"),
            ("Lunch: Protein + Greens + Complex Carbs", "12:30"),
            ("Vitals Check-in", "16:00"),
            ("Dinner: Light Protein + Greens", "18:30"),
            ("Evening Peptides/Hormones", "22:00"),
            ("Wind-down + Day Log", "22:30"),
        ]
        
        created = []
        for title, time in protocol:
            reminder = self.create_health_reminder(title, time)
            created.append(reminder)
        
        return created
    
    # === Persistence ===
    
    def save(self):
        """Save reminders to disk."""
        data = {
            "reminders": {k: v.to_dict() for k, v in self.reminders.items()},
            "focus_mode": self.focus_mode,
            "notification_queue": [r.to_dict() for r in self.notification_queue],
            "saved_at": datetime.now().isoformat()
        }
        self.storage_path.write_text(json.dumps(data, indent=2))
    
    def load(self):
        """Load reminders from disk."""
        if self.storage_path.exists():
            data = json.loads(self.storage_path.read_text())
            self.reminders = {k: Reminder.from_dict(v) for k, v in data.get("reminders", {}).items()}
            self.focus_mode = data.get("focus_mode", False)
            self.notification_queue = [Reminder.from_dict(r) for r in data.get("notification_queue", [])]
    
    # === Statistics ===
    
    def stats(self) -> Dict[str, Any]:
        """Get reminder statistics."""
        active = [r for r in self.reminders.values() if not r.dismissed]
        
        return {
            "total_active": len(active),
            "by_type": {
                t.value: len([r for r in active if r.reminder_type == t])
                for t in ReminderType
            },
            "focus_mode": self.focus_mode,
            "queued": len(self.notification_queue)
        }


# === CLI Interface ===

if __name__ == "__main__":
    agent = ReminderAgent("/tmp/test_reminders.json")
    
    print("=== Sovereign Agent - Reminders ===")
    print("ND/ADHD Optimized: Gentle nudges, no guilt\n")
    
    # Set up health protocol
    print("Setting up Health Spring Protocol...")
    reminders = agent.setup_health_protocol()
    print(f"  Created {len(reminders)} health reminders")
    
    # Create a break reminder
    print("\nCreating break reminder...")
    agent.create_break_reminder(90)
    
    # Enter focus mode
    print("\nEntering focus mode...")
    result = agent.enter_focus_mode(90)
    print(f"  {result['message']}")
    
    # Stats
    print("\nReminder Stats:")
    stats = agent.stats()
    print(f"  Active reminders: {stats['total_active']}")
    print(f"  Health reminders: {stats['by_type']['health']}")
    print(f"  Focus mode: {stats['focus_mode']}")
    
    print("\n✓ Reminder Agent Test Complete")

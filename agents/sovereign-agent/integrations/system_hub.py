#!/usr/bin/env python3
"""
Sovereign Agent - System Integration Hub
Connects: Health Protocol, Manus Bridge, S.A.F.E.-OS, Social, Tasks
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, "/home/ubuntu/manus_gesture_protocol")
sys.path.insert(0, "/home/ubuntu/SAFE_OS")

from core.task_queue import TaskQueue, Task, Priority, EnergyLevel
from agents.social_agent import SocialAgent, Platform
from agents.reminder_agent import ReminderAgent
from nd_support.cognitive_support import CognitiveLoadMonitor


class SovereignAgentHub:
    """
    Central hub connecting all Sovereign systems.
    
    Integrations:
    - Task Queue (ND/ADHD optimized)
    - Social Media Agent
    - Reminder Agent
    - Cognitive Load Monitor
    - Health Protocol
    - Manus Bridge (gesture commands)
    - S.A.F.E.-OS (governance)
    """
    
    def __init__(self, base_path: str = "/var/lib/sovereign_agent"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize all subsystems
        self.tasks = TaskQueue(str(self.base_path / "tasks.json"))
        self.social = SocialAgent(str(self.base_path / "social.json"))
        self.reminders = ReminderAgent(str(self.base_path / "reminders.json"))
        self.cognitive = CognitiveLoadMonitor(str(self.base_path / "cognitive.json"))
        
        # Integration state
        self.state = {
            "initialized": datetime.now().isoformat(),
            "focus_mode": False,
            "current_task": None,
            "energy_level": "medium"
        }
        
        self._load_state()
    
    # === Unified Commands ===
    
    def start_day(self) -> Dict[str, Any]:
        """
        Morning startup routine.
        One command to initialize everything.
        """
        self.cognitive.start_session()
        
        # Get today's tasks
        today_tasks = self.tasks.get_today()
        
        # Get health reminders status
        health_reminders = [r for r in self.reminders.reminders.values() 
                           if r.reminder_type.value == "health"]
        
        # Get social queue
        social_queue = self.social.get_queue()
        
        # Check cognitive state
        cog_state, _ = self.cognitive.get_state()
        
        return {
            "greeting": self._get_greeting(),
            "tasks_today": len(today_tasks),
            "top_task": today_tasks[0].title if today_tasks else "No tasks scheduled",
            "health_reminders_active": len(health_reminders),
            "social_posts_scheduled": len(social_queue),
            "cognitive_state": cog_state.value,
            "message": self._morning_message(today_tasks)
        }
    
    def _get_greeting(self) -> str:
        hour = datetime.now().hour
        if hour < 12:
            return "Good morning"
        elif hour < 17:
            return "Good afternoon"
        else:
            return "Good evening"
    
    def _morning_message(self, tasks: List[Task]) -> str:
        if not tasks:
            return "No tasks scheduled for today. What would you like to focus on?"
        
        top = tasks[0]
        return f"""
{self._get_greeting()}.

Your top priority today: {top.title}

Next action: {top.micro_action()}

{len(tasks) - 1} other tasks are ready when you are.
No rush. One thing at a time.
"""
    
    def end_day(self) -> Dict[str, Any]:
        """
        Evening shutdown routine.
        Review, log, prepare for tomorrow.
        """
        # Get session summary
        session = self.cognitive.end_session()
        
        # Get completed tasks
        completed = [t for t in self.tasks.tasks.values() 
                     if t.state.value == "done"
                     and t.completed_at
                     and t.completed_at.startswith(datetime.now().date().isoformat())]
        
        # Get social posts made
        posted = [p for p in self.social.posts.values()
                  if p.status.value == "posted"
                  and p.posted_at
                  and p.posted_at.startswith(datetime.now().date().isoformat())]
        
        return {
            "session_duration": session["duration_minutes"],
            "tasks_completed": len(completed),
            "social_posts": len(posted),
            "cognitive_summary": session,
            "message": self._evening_message(completed, session)
        }
    
    def _evening_message(self, completed: List[Task], session: Dict) -> str:
        return f"""
Day complete.

Tasks finished: {len(completed)}
Time working: {session['duration_minutes']} minutes
Task switches: {session['task_switches']}

{"Well done. Rest now." if len(completed) > 0 else "Tomorrow is a new day. Rest now."}
"""
    
    # === Focus Mode ===
    
    def enter_focus(self, task_id: Optional[str] = None, minutes: int = 90) -> Dict[str, Any]:
        """
        Enter focus mode with optional task selection.
        """
        # Start focus in reminders
        self.reminders.enter_focus_mode(minutes)
        
        # Start task if specified
        if task_id:
            task_result = self.tasks.start_task(task_id)
            self.state["current_task"] = task_id
        else:
            # Get one task automatically
            task = self.tasks.get_one_task()
            if task:
                task_result = self.tasks.start_task(task.id)
                self.state["current_task"] = task.id
            else:
                task_result = {"message": "No tasks available"}
        
        self.state["focus_mode"] = True
        self._save_state()
        
        return {
            "focus_mode": True,
            "duration": minutes,
            "task": task_result,
            "message": f"Focus mode active for {minutes} minutes.\n\n{task_result.get('message', '')}"
        }
    
    def exit_focus(self, context_notes: str = "") -> Dict[str, Any]:
        """
        Exit focus mode, save context.
        """
        # Exit focus in reminders
        reminder_result = self.reminders.exit_focus_mode()
        
        # Pause current task with context
        if self.state["current_task"]:
            self.tasks.pause_task(self.state["current_task"], context_notes)
        
        self.state["focus_mode"] = False
        self.state["current_task"] = None
        self._save_state()
        
        return {
            "focus_mode": False,
            "notifications_queued": reminder_result["queued_delivered"],
            "context_saved": bool(context_notes),
            "message": reminder_result["summary"]
        }
    
    # === Quick Actions ===
    
    def quick_task(self, text: str) -> Task:
        """Quick capture a task."""
        task = self.tasks.quick_add(text)
        self.cognitive.record_decision()  # Minimal decision made
        return task
    
    def quick_post(self, platform: str, content: str) -> Dict[str, Any]:
        """Quick create and schedule a social post."""
        plat = Platform(platform.lower())
        post = self.social.create_post(plat, content)
        self.social.auto_schedule(post.id)
        return {
            "post_id": post.id,
            "scheduled": post.scheduled_time,
            "message": f"Post scheduled for {post.scheduled_time}"
        }
    
    def complete_task(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Complete current or specified task."""
        tid = task_id or self.state["current_task"]
        if not tid:
            return {"error": "No task specified or in progress"}
        
        task = self.tasks.complete_task(tid)
        self.cognitive.record_task_complete()
        
        if self.state["current_task"] == tid:
            self.state["current_task"] = None
            self._save_state()
        
        # Get next task suggestion
        next_task = self.tasks.get_one_task()
        
        return {
            "completed": task.title,
            "message": f"✓ Completed: {task.title}\n\nGreat work!",
            "next_suggestion": next_task.title if next_task else None
        }
    
    # === Health Protocol Integration ===
    
    def setup_health_protocol(self) -> Dict[str, Any]:
        """Set up full health protocol reminders."""
        reminders = self.reminders.setup_health_protocol()
        return {
            "reminders_created": len(reminders),
            "message": f"Health Spring Protocol configured.\n{len(reminders)} daily reminders set."
        }
    
    def log_health_event(self, event_type: str, notes: str = "") -> Dict[str, Any]:
        """Log a health protocol event."""
        # Import health logger if available
        try:
            sys.path.insert(0, "/home/ubuntu/manus_gesture_protocol/scripts")
            from health_log import HealthLogger
            
            logger = HealthLogger()
            entry = logger.log_event(event_type, notes)
            
            return {
                "logged": True,
                "event": event_type,
                "timestamp": entry["timestamp"],
                "message": f"Logged: {event_type}"
            }
        except ImportError:
            return {
                "logged": False,
                "error": "Health logger not available",
                "event": event_type
            }
    
    # === Gesture Integration ===
    
    def handle_gesture(self, gesture_name: str) -> Dict[str, Any]:
        """
        Handle a gesture command from Manus Bridge.
        Maps gestures to agent actions.
        """
        gesture_map = {
            "thumbs_up": self._gesture_complete_task,
            "open_palm": self._gesture_take_break,
            "fist": self._gesture_enter_focus,
            "peace_sign": self._gesture_exit_focus,
            "point_up": self._gesture_next_task,
            "wave": self._gesture_dismiss_notifications,
        }
        
        handler = gesture_map.get(gesture_name)
        if handler:
            return handler()
        
        return {"error": f"Unknown gesture: {gesture_name}"}
    
    def _gesture_complete_task(self) -> Dict[str, Any]:
        return self.complete_task()
    
    def _gesture_take_break(self) -> Dict[str, Any]:
        self.cognitive.record_break(10)
        return {"action": "break", "duration": 10, "message": "Break time. 10 minutes."}
    
    def _gesture_enter_focus(self) -> Dict[str, Any]:
        return self.enter_focus(minutes=90)
    
    def _gesture_exit_focus(self) -> Dict[str, Any]:
        return self.exit_focus()
    
    def _gesture_next_task(self) -> Dict[str, Any]:
        task = self.tasks.get_one_task()
        if task:
            return self.tasks.start_task(task.id)
        return {"message": "No more tasks"}
    
    def _gesture_dismiss_notifications(self) -> Dict[str, Any]:
        count = self.reminders.dismiss_all_gentle()
        return {"dismissed": count, "message": f"Dismissed {count} gentle reminders"}
    
    # === Status & Monitoring ===
    
    def status(self) -> Dict[str, Any]:
        """Get full system status."""
        cog_state, cog_indicators = self.cognitive.get_state()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "focus_mode": self.state["focus_mode"],
            "current_task": self.state["current_task"],
            "cognitive_state": cog_state.value,
            "tasks": self.tasks.stats(),
            "social": self.social.weekly_summary(),
            "reminders": self.reminders.stats(),
            "intervention_needed": cog_state.value in ("high", "overwhelmed")
        }
    
    def check_overwhelm(self) -> Dict[str, Any]:
        """Check for overwhelm and get intervention if needed."""
        intervention = self.cognitive.get_intervention()
        task_overwhelm = self.tasks.check_overwhelm()
        
        if intervention or task_overwhelm["overwhelmed"]:
            return {
                "overwhelmed": True,
                "cognitive_intervention": intervention,
                "task_intervention": task_overwhelm.get("intervention"),
                "message": "Overwhelm detected. See interventions."
            }
        
        return {
            "overwhelmed": False,
            "message": "All systems nominal."
        }
    
    # === Persistence ===
    
    def _save_state(self):
        state_file = self.base_path / "hub_state.json"
        state_file.write_text(json.dumps(self.state, indent=2))
    
    def _load_state(self):
        state_file = self.base_path / "hub_state.json"
        if state_file.exists():
            self.state.update(json.loads(state_file.read_text()))


# === CLI Interface ===

if __name__ == "__main__":
    hub = SovereignAgentHub("/tmp/test_hub")
    
    print("=== Sovereign Agent Hub ===")
    print("Unified control for all systems\n")
    
    # Start day
    print("Starting day...")
    result = hub.start_day()
    print(result["message"])
    
    # Quick task
    print("\nQuick capturing task...")
    task = hub.quick_task("Review S.A.F.E.-OS deployment")
    print(f"  Created: {task.title}")
    
    # Enter focus
    print("\nEntering focus mode...")
    focus = hub.enter_focus(minutes=45)
    print(f"  Focus: {focus['focus_mode']}")
    
    # Status
    print("\nSystem Status:")
    status = hub.status()
    print(f"  Cognitive: {status['cognitive_state']}")
    print(f"  Focus mode: {status['focus_mode']}")
    print(f"  Tasks: {status['tasks']['total']}")
    
    # Check overwhelm
    print("\nOverwhelm check:")
    overwhelm = hub.check_overwhelm()
    print(f"  {overwhelm['message']}")
    
    print("\n✓ Hub Integration Test Complete")

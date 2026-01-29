# ND/ADHD-OPTIMIZED AGENTIC ARCHITECTURE

**Version:** 1.0  
**Purpose:** Reduce cognitive load, eliminate decision fatigue, automate everything possible

---

## CORE PRINCIPLES FOR ND/ADHD SUPPORT

### 1. ZERO DECISION FATIGUE
- System makes routine decisions automatically
- Only surface decisions that truly require human input
- Default actions for everything

### 2. EXTERNAL BRAIN
- System remembers everything
- Proactive reminders before deadlines
- Context restoration on task switch

### 3. BODY DOUBLING (Digital)
- Ambient awareness of task progress
- Gentle accountability without judgment
- Progress visibility

### 4. HYPERFOCUS PROTECTION
- Block interruptions during deep work
- Queue non-urgent items
- Batch notifications

### 5. TRANSITION SUPPORT
- Clear task boundaries
- Explicit "done" signals
- Next action always visible

### 6. OVERWHELM PREVENTION
- One task visible at a time (optional)
- Break large tasks automatically
- "Just start" micro-actions

---

## ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                    SOVEREIGN AGENT                          │
│                  (ND/ADHD Optimized)                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   INTAKE    │  │   BRAIN     │  │   OUTPUT    │         │
│  │   AGENT     │  │   AGENT     │  │   AGENT     │         │
│  │             │  │             │  │             │         │
│  │ • Capture   │  │ • Decide    │  │ • Execute   │         │
│  │ • Classify  │  │ • Prioritize│  │ • Notify    │         │
│  │ • Queue     │  │ • Schedule  │  │ • Log       │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          │                                  │
│                    ┌─────▼─────┐                            │
│                    │   TASK    │                            │
│                    │   QUEUE   │                            │
│                    │           │                            │
│                    │ Priority  │                            │
│                    │ Context   │                            │
│                    │ Deadlines │                            │
│                    └───────────┘                            │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                    ND SUPPORT LAYER                         │
│                                                             │
│  • Cognitive Load Monitor    • Transition Helper            │
│  • Hyperfocus Guard          • Overwhelm Detector           │
│  • Body Double Mode          • Energy Tracker               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## AGENT DEFINITIONS

### 1. INTAKE AGENT
**Purpose:** Capture everything, classify automatically, never lose anything

| Trigger | Action |
|---------|--------|
| New email | Extract action items, add to queue |
| New message | Parse intent, route appropriately |
| Voice note | Transcribe, extract tasks |
| Calendar event | Create prep tasks, set reminders |
| Idea capture | Log with context, tag for review |

### 2. BRAIN AGENT
**Purpose:** Make decisions so you don't have to

| Function | Behavior |
|----------|----------|
| Prioritization | Eisenhower matrix, auto-sort |
| Scheduling | Time-block based on energy patterns |
| Batching | Group similar tasks |
| Delegation | Route to appropriate system/person |
| Deferral | Snooze with context preservation |

### 3. OUTPUT AGENT
**Purpose:** Execute tasks, notify completion, log everything

| Function | Behavior |
|----------|----------|
| Social posting | Auto-post from queue at optimal times |
| Email sending | Draft and send routine responses |
| File management | Auto-organize, backup, sync |
| Notifications | Batch, prioritize, deliver appropriately |
| Logging | Hash-chain audit trail |

---

## ND SUPPORT FEATURES

### A. COGNITIVE LOAD MONITOR

```python
class CognitiveLoadMonitor:
    """
    Tracks cognitive load indicators and adjusts system behavior.
    """
    
    indicators = {
        'task_switches': 0,      # High = overload
        'incomplete_tasks': 0,   # High = overwhelm
        'time_since_break': 0,   # High = fatigue
        'decision_count': 0,     # High = decision fatigue
    }
    
    def check_load(self):
        if self.indicators['incomplete_tasks'] > 5:
            return 'OVERWHELM_WARNING'
        if self.indicators['time_since_break'] > 90:  # minutes
            return 'BREAK_NEEDED'
        if self.indicators['decision_count'] > 20:
            return 'DECISION_FATIGUE'
        return 'OK'
```

### B. HYPERFOCUS GUARD

```python
class HyperfocusGuard:
    """
    Protects deep work, queues interruptions.
    """
    
    def __init__(self):
        self.mode = 'NORMAL'  # NORMAL, FOCUS, BREAK
        self.queue = []
        
    def enter_focus(self, duration_minutes=90):
        self.mode = 'FOCUS'
        # Block notifications
        # Queue incoming items
        # Set break reminder
        
    def handle_interrupt(self, item):
        if self.mode == 'FOCUS':
            if item.priority == 'CRITICAL':
                return 'ALLOW'
            else:
                self.queue.append(item)
                return 'QUEUED'
        return 'ALLOW'
```

### C. TRANSITION HELPER

```python
class TransitionHelper:
    """
    Supports task switching without losing context.
    """
    
    def save_context(self, task):
        return {
            'task_id': task.id,
            'state': task.current_state,
            'notes': task.scratch_notes,
            'next_action': task.next_action,
            'time_spent': task.time_spent,
            'timestamp': now()
        }
    
    def restore_context(self, task_id):
        context = self.load_context(task_id)
        return f"""
        RESUMING: {context['task_id']}
        
        WHERE YOU LEFT OFF:
        {context['state']}
        
        YOUR NOTES:
        {context['notes']}
        
        NEXT ACTION:
        {context['next_action']}
        """
```

### D. OVERWHELM DETECTOR

```python
class OverwhelmDetector:
    """
    Detects overwhelm and triggers intervention.
    """
    
    def check(self, task_queue):
        signals = {
            'too_many_tasks': len(task_queue) > 10,
            'too_many_urgent': sum(1 for t in task_queue if t.urgent) > 3,
            'no_progress': self.no_completions_in(hours=4),
            'rapid_switching': self.switches_per_hour > 10,
        }
        
        if any(signals.values()):
            return self.intervention(signals)
        return None
    
    def intervention(self, signals):
        return """
        OVERWHELM DETECTED
        
        Recommended actions:
        1. STOP - Take 5 minutes
        2. PICK ONE - Just one task
        3. SHRINK IT - What's the smallest step?
        4. DEFER - Move non-urgent to tomorrow
        
        Would you like me to auto-defer non-urgent tasks?
        """
```

---

## AUTOMATION TARGETS

### Social Media (Fully Automated)

| Task | Automation |
|------|------------|
| Content creation | Queue posts in advance |
| Posting | Auto-post at optimal times |
| Engagement | Notify of important interactions only |
| Analytics | Weekly summary, no daily noise |

### Health Protocol (Reminder-Based)

| Task | Automation |
|------|------------|
| Peptide reminders | Push notification + log prompt |
| Meal reminders | Gentle nudge, no judgment |
| Vitals check | One-tap logging |
| Day log | End-of-day prompt with pre-fill |

### Administrative (Decision-Free)

| Task | Automation |
|------|------------|
| Email triage | Auto-categorize, surface urgent only |
| File organization | Auto-sort by type/project |
| Backup | Automatic, silent |
| Updates | Auto-apply, notify only on failure |

### Development (Context-Preserving)

| Task | Automation |
|------|------------|
| Git commits | Auto-commit on save (optional) |
| Test runs | Auto-run on file change |
| Deployment | One-command deploy |
| Documentation | Auto-generate from code |

---

## NOTIFICATION PHILOSOPHY

### ALLOW IMMEDIATELY:
- Critical system failures
- Time-sensitive deadlines (< 1 hour)
- Explicit user requests

### BATCH (Every 2 hours):
- Email summaries
- Social media interactions
- Non-urgent updates

### DAILY DIGEST:
- Analytics
- Completed tasks
- Upcoming deadlines

### NEVER NOTIFY:
- Vanity metrics (likes, followers)
- Marketing emails
- Non-actionable information

---

## ENERGY-AWARE SCHEDULING

```python
class EnergyScheduler:
    """
    Schedules tasks based on energy patterns.
    """
    
    # Default patterns (customizable)
    energy_curve = {
        'morning': 'HIGH',      # 8-12: Deep work
        'early_afternoon': 'MEDIUM',  # 12-15: Meetings, admin
        'late_afternoon': 'LOW',      # 15-17: Light tasks
        'evening': 'VARIABLE',        # 17+: User preference
    }
    
    def schedule_task(self, task):
        if task.requires == 'DEEP_FOCUS':
            return self.find_slot('HIGH')
        elif task.requires == 'ROUTINE':
            return self.find_slot('LOW')
        else:
            return self.find_slot('MEDIUM')
```

---

## IMPLEMENTATION PRIORITY

| Phase | Components | Timeline |
|-------|------------|----------|
| 1 | Task Queue + Reminders | Immediate |
| 2 | Social Media Automation | Day 1 |
| 3 | Cognitive Load Monitor | Day 2 |
| 4 | Full Agent Integration | Day 3-5 |

---

**Document Status:** ARCHITECTURE COMPLETE

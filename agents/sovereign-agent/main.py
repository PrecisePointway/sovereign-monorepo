#!/usr/bin/env python3
"""
Sovereign Agent - Main Entry Point
ND/ADHD Optimized Agentic Automation Framework
"""

import sys
import argparse
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from integrations.system_hub import SovereignAgentHub


def main():
    parser = argparse.ArgumentParser(
        description="Sovereign Agent - ND/ADHD Optimized Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  start           Start your day (morning routine)
  end             End your day (evening routine)
  focus [mins]    Enter focus mode (default: 90 min)
  unfocus         Exit focus mode
  task <text>     Quick capture a task
  done [id]       Complete current or specified task
  status          Get system status
  overwhelm       Check for overwhelm
  health          Set up health protocol
  post <platform> <text>  Quick schedule a post

Examples:
  sovereign-agent start
  sovereign-agent focus 45
  sovereign-agent task "Review deployment"
  sovereign-agent done
  sovereign-agent post linkedin "New release!"
"""
    )
    
    parser.add_argument("command", nargs="?", default="status", help="Command to run")
    parser.add_argument("args", nargs="*", help="Command arguments")
    parser.add_argument("--path", default="/var/lib/sovereign_agent", help="Data path")
    
    args = parser.parse_args()
    
    # Initialize hub
    hub = SovereignAgentHub(args.path)
    
    # Route commands
    commands = {
        "start": lambda: hub.start_day(),
        "end": lambda: hub.end_day(),
        "focus": lambda: hub.enter_focus(minutes=int(args.args[0]) if args.args else 90),
        "unfocus": lambda: hub.exit_focus(),
        "task": lambda: hub.quick_task(" ".join(args.args)),
        "done": lambda: hub.complete_task(args.args[0] if args.args else None),
        "status": lambda: hub.status(),
        "overwhelm": lambda: hub.check_overwhelm(),
        "health": lambda: hub.setup_health_protocol(),
        "post": lambda: hub.quick_post(args.args[0], " ".join(args.args[1:])) if len(args.args) >= 2 else {"error": "Usage: post <platform> <text>"},
    }
    
    handler = commands.get(args.command)
    if handler:
        result = handler()
        
        # Pretty print result
        if isinstance(result, dict):
            if "message" in result:
                print(result["message"])
            else:
                import json
                print(json.dumps(result, indent=2, default=str))
        else:
            print(result)
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()


if __name__ == "__main__":
    main()

"""
Sovereign Sanctuary Elite Pack - Self-Run Activation Daemon
Deterministic execution with watchdog, health checks, and auto-recovery
"""

import os
import sys
import json
import time
import signal
import hashlib
import logging
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
import yaml

# Systemd watchdog support
try:
    import systemd.daemon as sd_daemon
    SYSTEMD_AVAILABLE = True
except ImportError:
    SYSTEMD_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

@dataclass
class DaemonConfig:
    """Daemon configuration"""
    mode: str = "production"  # production, development, test
    watchdog_enabled: bool = True
    watchdog_interval_sec: int = 60
    max_runtime_hours: int = 24
    health_check_interval_sec: int = 30
    auto_restart_on_failure: bool = True
    max_restart_attempts: int = 5
    log_level: str = "INFO"
    log_file: str = "/var/log/sovereign/sanctuary.log"
    state_file: str = "/var/lib/sovereign/daemon_state.json"
    pid_file: str = "/var/run/sovereign/sanctuary.pid"
    
    # Component activation
    enable_grant_pipeline: bool = True
    enable_runway_tracker: bool = True
    enable_decision_matrix: bool = True
    enable_daily_sprint: bool = True
    enable_airtable_sync: bool = True
    
    @classmethod
    def from_yaml(cls, path: str) -> 'DaemonConfig':
        """Load config from YAML file"""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data.get('daemon', {}))
    
    @classmethod
    def from_env(cls) -> 'DaemonConfig':
        """Load config from environment variables"""
        return cls(
            mode=os.environ.get('SANCTUARY_MODE', 'production'),
            watchdog_enabled=os.environ.get('WATCHDOG_ENABLED', 'true').lower() == 'true',
            log_level=os.environ.get('LOG_LEVEL', 'INFO')
        )


# ═══════════════════════════════════════════════════════════════════
# DAEMON STATE
# ═══════════════════════════════════════════════════════════════════

@dataclass
class DaemonState:
    """Persistent daemon state"""
    start_time: str = ""
    last_heartbeat: str = ""
    restart_count: int = 0
    components_active: List[str] = field(default_factory=list)
    last_error: str = ""
    state_hash: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_time": self.start_time,
            "last_heartbeat": self.last_heartbeat,
            "restart_count": self.restart_count,
            "components_active": self.components_active,
            "last_error": self.last_error,
            "state_hash": self.state_hash
        }
    
    def save(self, path: str) -> None:
        """Save state to file"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: str) -> 'DaemonState':
        """Load state from file"""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            return cls(**data)
        except FileNotFoundError:
            return cls()
    
    def update_heartbeat(self) -> None:
        """Update heartbeat timestamp"""
        self.last_heartbeat = datetime.utcnow().isoformat()
        self.state_hash = hashlib.sha256(
            json.dumps(self.to_dict(), sort_keys=True).encode()
        ).hexdigest()[:12]


# ═══════════════════════════════════════════════════════════════════
# COMPONENT REGISTRY
# ═══════════════════════════════════════════════════════════════════

class ComponentRegistry:
    """Registry of daemon components"""
    
    def __init__(self):
        self.components: Dict[str, Callable] = {}
        self.running: Dict[str, bool] = {}
        self.threads: Dict[str, threading.Thread] = {}
    
    def register(self, name: str, component: Callable) -> None:
        """Register a component"""
        self.components[name] = component
        self.running[name] = False
    
    def start(self, name: str) -> bool:
        """Start a component"""
        if name not in self.components:
            return False
        
        if self.running.get(name, False):
            return True  # Already running
        
        try:
            thread = threading.Thread(
                target=self.components[name],
                name=f"component-{name}",
                daemon=True
            )
            thread.start()
            self.threads[name] = thread
            self.running[name] = True
            return True
        except Exception as e:
            logging.error(f"Failed to start component {name}: {e}")
            return False
    
    def stop(self, name: str) -> bool:
        """Stop a component"""
        if name not in self.running:
            return False
        
        self.running[name] = False
        # Thread will exit on next iteration check
        return True
    
    def stop_all(self) -> None:
        """Stop all components"""
        for name in list(self.running.keys()):
            self.stop(name)
    
    def is_healthy(self, name: str) -> bool:
        """Check if component is healthy"""
        if name not in self.threads:
            return False
        return self.threads[name].is_alive()
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all components"""
        return {
            name: {
                "running": self.running.get(name, False),
                "healthy": self.is_healthy(name)
            }
            for name in self.components.keys()
        }


# ═══════════════════════════════════════════════════════════════════
# WATCHDOG
# ═══════════════════════════════════════════════════════════════════

class Watchdog:
    """
    Watchdog process for daemon health monitoring
    - Sends heartbeats to systemd
    - Monitors component health
    - Enforces max runtime
    - Triggers auto-recovery
    """
    
    def __init__(self, config: DaemonConfig, registry: ComponentRegistry, state: DaemonState):
        self.config = config
        self.registry = registry
        self.state = state
        self.running = False
        self.start_time = datetime.utcnow()
        self._thread: Optional[threading.Thread] = None
    
    def start(self) -> None:
        """Start watchdog thread"""
        self.running = True
        self._thread = threading.Thread(target=self._run, name="watchdog", daemon=True)
        self._thread.start()
        logging.info("Watchdog started")
    
    def stop(self) -> None:
        """Stop watchdog"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        logging.info("Watchdog stopped")
    
    def _run(self) -> None:
        """Watchdog main loop"""
        while self.running:
            try:
                # Update heartbeat
                self.state.update_heartbeat()
                self.state.save(self.config.state_file)
                
                # Notify systemd
                if SYSTEMD_AVAILABLE:
                    sd_daemon.notify("WATCHDOG=1")
                
                # Check runtime limit
                runtime = datetime.utcnow() - self.start_time
                if runtime > timedelta(hours=self.config.max_runtime_hours):
                    logging.warning(f"Max runtime exceeded ({self.config.max_runtime_hours}h)")
                    self._trigger_graceful_shutdown()
                    break
                
                # Check component health
                status = self.registry.get_status()
                unhealthy = [name for name, s in status.items() if not s["healthy"]]
                
                if unhealthy and self.config.auto_restart_on_failure:
                    for name in unhealthy:
                        logging.warning(f"Component {name} unhealthy, attempting restart")
                        self.registry.start(name)
                
                # Update active components
                self.state.components_active = [
                    name for name, s in status.items() if s["running"]
                ]
                
            except Exception as e:
                logging.error(f"Watchdog error: {e}")
                self.state.last_error = str(e)
            
            time.sleep(self.config.watchdog_interval_sec)
    
    def _trigger_graceful_shutdown(self) -> None:
        """Trigger graceful shutdown"""
        logging.info("Triggering graceful shutdown")
        os.kill(os.getpid(), signal.SIGTERM)


# ═══════════════════════════════════════════════════════════════════
# MAIN DAEMON
# ═══════════════════════════════════════════════════════════════════

class SanctuaryDaemon:
    """
    Main daemon process for Sovereign Sanctuary Elite Pack
    
    Features:
    - Systemd integration with watchdog
    - Component lifecycle management
    - Health monitoring and auto-recovery
    - Graceful shutdown handling
    - State persistence
    """
    
    def __init__(self, config: DaemonConfig):
        self.config = config
        self.state = DaemonState.load(config.state_file)
        self.registry = ComponentRegistry()
        self.watchdog: Optional[Watchdog] = None
        self.running = False
        
        # Setup logging
        self._setup_logging()
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigint)
    
    def _setup_logging(self) -> None:
        """Configure logging"""
        Path(self.config.log_file).parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            handlers=[
                logging.FileHandler(self.config.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _handle_sigterm(self, signum, frame) -> None:
        """Handle SIGTERM for graceful shutdown"""
        logging.info("Received SIGTERM, initiating graceful shutdown")
        self.stop()
    
    def _handle_sigint(self, signum, frame) -> None:
        """Handle SIGINT (Ctrl+C)"""
        logging.info("Received SIGINT, initiating graceful shutdown")
        self.stop()
    
    def _write_pid_file(self) -> None:
        """Write PID file"""
        Path(self.config.pid_file).parent.mkdir(parents=True, exist_ok=True)
        with open(self.config.pid_file, 'w') as f:
            f.write(str(os.getpid()))
    
    def _remove_pid_file(self) -> None:
        """Remove PID file"""
        try:
            os.remove(self.config.pid_file)
        except FileNotFoundError:
            pass
    
    def _register_components(self) -> None:
        """Register all daemon components"""
        
        # Import components (lazy to avoid circular imports)
        if self.config.enable_grant_pipeline:
            from automations.grant_pipeline import create_default_pipeline
            
            def grant_pipeline_loop():
                pipeline = create_default_pipeline()
                while self.registry.running.get("grant_pipeline", False):
                    # Generate daily sprint at configured time
                    sprint = pipeline.generate_daily_sprint()
                    logging.debug(f"Grant pipeline sprint: {sprint['summary']}")
                    time.sleep(3600)  # Check hourly
            
            self.registry.register("grant_pipeline", grant_pipeline_loop)
        
        if self.config.enable_runway_tracker:
            from automations.runway_tracker import create_default_runway
            
            def runway_tracker_loop():
                runway = create_default_runway()
                while self.registry.running.get("runway_tracker", False):
                    report = runway.generate_report()
                    alerts = runway.generate_alerts()
                    for alert in alerts:
                        logging.warning(f"Runway alert: {alert['message']}")
                    time.sleep(3600)
            
            self.registry.register("runway_tracker", runway_tracker_loop)
        
        if self.config.enable_decision_matrix:
            from automations.decision_matrix import DecisionMatrixEngine
            
            def decision_matrix_loop():
                engine = DecisionMatrixEngine()
                while self.registry.running.get("decision_matrix", False):
                    status = engine.get_status()
                    logging.debug(f"Decision matrix: {status['current_state']}")
                    time.sleep(300)  # Check every 5 minutes
            
            self.registry.register("decision_matrix", decision_matrix_loop)
        
        if self.config.enable_daily_sprint:
            from automations.daily_sprint import create_48h_execution_sprint
            
            def daily_sprint_loop():
                while self.registry.running.get("daily_sprint", False):
                    sprint = create_48h_execution_sprint()
                    logging.info(f"Daily sprint generated: {sprint.sprint_id}")
                    # Sleep until next day
                    time.sleep(86400)
            
            self.registry.register("daily_sprint", daily_sprint_loop)
    
    def start(self) -> None:
        """Start the daemon"""
        logging.info("═" * 60)
        logging.info("  SOVEREIGN SANCTUARY DAEMON STARTING")
        logging.info("═" * 60)
        
        self.running = True
        self._write_pid_file()
        
        # Update state
        self.state.start_time = datetime.utcnow().isoformat()
        self.state.restart_count += 1
        self.state.save(self.config.state_file)
        
        # Register components
        self._register_components()
        
        # Start components
        for name in self.registry.components.keys():
            if self.registry.start(name):
                logging.info(f"Started component: {name}")
            else:
                logging.error(f"Failed to start component: {name}")
        
        # Start watchdog
        if self.config.watchdog_enabled:
            self.watchdog = Watchdog(self.config, self.registry, self.state)
            self.watchdog.start()
        
        # Notify systemd ready
        if SYSTEMD_AVAILABLE:
            sd_daemon.notify("READY=1")
        
        logging.info("Daemon started successfully")
        
        # Main loop
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the daemon"""
        if not self.running:
            return
        
        logging.info("Stopping daemon...")
        self.running = False
        
        # Notify systemd stopping
        if SYSTEMD_AVAILABLE:
            sd_daemon.notify("STOPPING=1")
        
        # Stop watchdog
        if self.watchdog:
            self.watchdog.stop()
        
        # Stop all components
        self.registry.stop_all()
        
        # Save final state
        self.state.save(self.config.state_file)
        
        # Remove PID file
        self._remove_pid_file()
        
        logging.info("Daemon stopped")


# ═══════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sovereign Sanctuary Daemon")
    parser.add_argument("--config", "-c", help="Path to config file")
    parser.add_argument("--mode", choices=["production", "development", "test"], default="production")
    parser.add_argument("--foreground", "-f", action="store_true", help="Run in foreground")
    args = parser.parse_args()
    
    # Load config
    if args.config:
        config = DaemonConfig.from_yaml(args.config)
    else:
        config = DaemonConfig.from_env()
    
    config.mode = args.mode
    
    # Create and start daemon
    daemon = SanctuaryDaemon(config)
    daemon.start()


if __name__ == "__main__":
    main()

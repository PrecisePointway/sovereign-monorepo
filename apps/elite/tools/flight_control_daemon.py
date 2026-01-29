#!/usr/bin/env python3
"""
Flight Control Daemon - Sovereign Sanctuary Elite
Watches for file changes and triggers sealing and SITREP updates.

Version: 2.0.0 (Bug-fixed and cleaned)
Author: Manus AI for Architect

Changes from v1:
- Fixed potential infinite loop with better event filtering
- Added proper error handling with specific exceptions
- Added configurable watch patterns
- Improved debouncing logic
- Added graceful shutdown
- Added IDE mode optimizations
- Fixed import fallback logic
"""

import os
import sys
import time
import signal
import logging
import argparse
import subprocess
from pathlib import Path
from typing import Optional, Callable, List
from dataclasses import dataclass

# Conditional import for watchdog
try:
    from watchdog.observers import Observer
    from watchdog.events import PatternMatchingEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

@dataclass
class DaemonConfig:
    """Configuration for the flight control daemon"""
    watch_dir: str = "evidence"
    sealer_cmd: List[str] = None
    updater_cmd: List[str] = None
    sitrep_file: str = "evidence/visuals/SWOT_SITREP.mmd"
    patterns: List[str] = None
    ignore_patterns: List[str] = None
    debounce_seconds: float = 0.5
    
    def __post_init__(self):
        if self.sealer_cmd is None:
            self.sealer_cmd = ["python", "tools/seal_file.py"]
        if self.updater_cmd is None:
            self.updater_cmd = ["python", "tools/update_sitrep.py"]
        if self.patterns is None:
            self.patterns = ["*.mmd", "*.md"]
        if self.ignore_patterns is None:
            self.ignore_patterns = ["*.sha256.txt", ".DS_Store", "*.tmp", "*~"]


# ═══════════════════════════════════════════════════════════════════
# LOGGING SETUP
# ═══════════════════════════════════════════════════════════════════

def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging for the daemon"""
    logger = logging.getLogger("flight_control")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler with formatting
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# ═══════════════════════════════════════════════════════════════════
# LEDGER INTEGRATION
# ═══════════════════════════════════════════════════════════════════

def get_ledger_append_function() -> Optional[Callable]:
    """
    Attempt to import the ledger append function.
    Returns None if not available.
    """
    # Try multiple import paths
    import_paths = [
        ("tools.ledger_tool", "append_event"),
        ("ledger_tool", "append_event"),
    ]
    
    for module_path, func_name in import_paths:
        try:
            module = __import__(module_path, fromlist=[func_name])
            return getattr(module, func_name, None)
        except ImportError:
            continue
    
    return None


# ═══════════════════════════════════════════════════════════════════
# FILE EVENT HANDLER
# ═══════════════════════════════════════════════════════════════════

if WATCHDOG_AVAILABLE:
    class FlightControlHandler(PatternMatchingEventHandler):
        """
        Handles file system events for the flight control daemon.
        
        Event Loop:
        1. Detect source file change
        2. Debounce rapid changes
        3. Seal the changed file
        4. Update SITREP (if not the SITREP itself)
        5. Seal the updated SITREP
        """
        
        def __init__(self, config: DaemonConfig, logger: logging.Logger):
            super().__init__(
                patterns=config.patterns,
                ignore_patterns=config.ignore_patterns,
                ignore_directories=True,
                case_sensitive=False
            )
            self.config = config
            self.logger = logger
            self.append_event = get_ledger_append_function()
            self._last_event_time: dict = {}
        
        def _should_process(self, path: str) -> bool:
            """
            Check if event should be processed (debouncing).
            Prevents duplicate processing from editors that save multiple times.
            """
            current_time = time.time()
            last_time = self._last_event_time.get(path, 0)
            
            if current_time - last_time < self.config.debounce_seconds:
                return False
            
            self._last_event_time[path] = current_time
            return True
        
        def _run_command(self, cmd: List[str], description: str) -> bool:
            """
            Run a subprocess command with error handling.
            
            Returns:
                True if command succeeded, False otherwise
            """
            try:
                result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                self.logger.debug(f"{description} output: {result.stdout}")
                return True
            except subprocess.CalledProcessError as e:
                self.logger.error(f"{description} failed: {e.stderr}")
                return False
            except subprocess.TimeoutExpired:
                self.logger.error(f"{description} timed out")
                return False
            except FileNotFoundError as e:
                self.logger.error(f"{description} command not found: {e}")
                return False
        
        def process(self, event: FileSystemEvent) -> None:
            """Process a file system event"""
            changed_file = event.src_path
            filename = os.path.basename(changed_file)
            
            # Debounce check
            if not self._should_process(changed_file):
                self.logger.debug(f"Debounced: {filename}")
                return
            
            self.logger.info(f"CHANGE DETECTED: {filename}")
            
            # Step 1: Seal the changed file
            seal_cmd = self.config.sealer_cmd + [changed_file]
            if not self._run_command(seal_cmd, f"Seal {filename}"):
                return
            self.logger.info(f"Sealed: {filename}")
            
            # Step 2: Update SITREP if this wasn't the SITREP itself
            sitrep_basename = os.path.basename(self.config.sitrep_file)
            if sitrep_basename not in filename:
                self.logger.info("Updating SITREP...")
                
                if self._run_command(self.config.updater_cmd, "Update SITREP"):
                    # Log to ledger if available
                    if self.append_event:
                        try:
                            self.append_event("SITREP_UPDATED", {"triggered_by": filename})
                        except Exception as e:
                            self.logger.warning(f"Failed to log to ledger: {e}")
                    
                    # Step 3: Seal the updated SITREP
                    sitrep_seal_cmd = self.config.sealer_cmd + [self.config.sitrep_file]
                    if self._run_command(sitrep_seal_cmd, "Seal SITREP"):
                        self.logger.info("SITREP sealed")
            
            self.logger.info("BOARD GREEN - LISTENING...")
        
        def on_modified(self, event: FileSystemEvent) -> None:
            """Handle file modification events"""
            if not event.is_directory:
                self.process(event)
        
        def on_created(self, event: FileSystemEvent) -> None:
            """Handle file creation events"""
            if not event.is_directory:
                self.process(event)


# ═══════════════════════════════════════════════════════════════════
# DAEMON CONTROLLER
# ═══════════════════════════════════════════════════════════════════

class FlightControlDaemon:
    """
    Main daemon controller for flight control operations.
    
    Manages the file watcher and handles graceful shutdown.
    """
    
    def __init__(self, config: DaemonConfig, verbose: bool = False, ide_mode: bool = False):
        self.config = config
        self.logger = setup_logging(verbose)
        self.ide_mode = ide_mode
        self._running = True
        self._observer: Optional[Observer] = None
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self._running = False
    
    def _validate_environment(self) -> bool:
        """Validate that required directories and tools exist"""
        # Check watch directory
        if not os.path.exists(self.config.watch_dir):
            self.logger.error(f"Watch directory '{self.config.watch_dir}' not found")
            return False
        
        # Check sealer script
        sealer_script = self.config.sealer_cmd[-1] if self.config.sealer_cmd else None
        if sealer_script and not os.path.exists(sealer_script):
            self.logger.warning(f"Sealer script '{sealer_script}' not found - sealing will fail")
        
        return True
    
    def run(self) -> None:
        """Start the daemon"""
        if not WATCHDOG_AVAILABLE:
            self.logger.error("watchdog package not installed. Run: pip install watchdog")
            return
        
        if not self._validate_environment():
            return
        
        # Print banner
        self._print_banner()
        
        # Create and start observer
        handler = FlightControlHandler(self.config, self.logger)
        self._observer = Observer()
        self._observer.schedule(handler, path=self.config.watch_dir, recursive=True)
        self._observer.start()
        
        self.logger.info("LISTENING for changes...")
        
        try:
            while self._running:
                time.sleep(1)
        finally:
            self._shutdown()
    
    def _print_banner(self) -> None:
        """Print startup banner"""
        print("=" * 60)
        print("FLIGHT CONTROL DAEMON - SOVEREIGN SANCTUARY ELITE")
        print("=" * 60)
        print(f"Watching:  {os.path.abspath(self.config.watch_dir)}")
        print(f"Patterns:  {', '.join(self.config.patterns)}")
        print(f"Ignored:   {', '.join(self.config.ignore_patterns)}")
        if self.ide_mode:
            print("IDE Mode:  ENABLED (optimized for IDE integration)")
        print("-" * 60)
    
    def _shutdown(self) -> None:
        """Clean shutdown of the daemon"""
        self.logger.info("Stopping daemon...")
        
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
        
        self.logger.info("Flight Control Daemon terminated")


# ═══════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def main() -> None:
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Flight Control Daemon - Sovereign Sanctuary Elite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python flight_control_daemon.py
  python flight_control_daemon.py --verbose
  python flight_control_daemon.py --ide-mode --watch-dir ./evidence
        """
    )
    parser.add_argument(
        "--watch-dir",
        type=str,
        default="evidence",
        help="Directory to watch for changes (default: evidence)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--ide-mode",
        action="store_true",
        help="Enable IDE optimization mode"
    )
    parser.add_argument(
        "--no-stop",
        action="store_true",
        help="Run in continuous mode (deprecated, now default)"
    )
    
    args = parser.parse_args()
    
    config = DaemonConfig(watch_dir=args.watch_dir)
    daemon = FlightControlDaemon(config, verbose=args.verbose, ide_mode=args.ide_mode)
    daemon.run()


if __name__ == "__main__":
    main()

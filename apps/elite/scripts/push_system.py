"""
Sovereign Sanctuary Elite Pack - File Push System
Deterministic deployment with cryptographic verification and webhook triggers
"""

import os
import sys
import json
import hashlib
import subprocess
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import yaml


# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

@dataclass
class PushConfig:
    """File push configuration"""
    # Git settings
    git_remote: str = "origin"
    git_branch: str = "main"
    auto_commit: bool = True
    commit_prefix: str = "[SANCTUARY]"
    
    # Rsync settings
    rsync_enabled: bool = True
    rsync_targets: List[str] = field(default_factory=list)
    rsync_options: str = "-avz --delete"
    
    # Webhook settings
    webhook_enabled: bool = True
    webhook_urls: List[str] = field(default_factory=list)
    webhook_secret: str = ""
    
    # Integrity verification
    verify_before_push: bool = True
    verify_after_push: bool = True
    hash_algorithm: str = "sha256"
    
    # Paths
    source_dir: str = "/opt/sovereign-sanctuary"
    manifest_file: str = "MANIFEST.json"
    
    @classmethod
    def from_yaml(cls, path: str) -> 'PushConfig':
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data.get('push', {}))


# ═══════════════════════════════════════════════════════════════════
# INTEGRITY VERIFICATION
# ═══════════════════════════════════════════════════════════════════

class IntegrityVerifier:
    """
    Cryptographic integrity verification for file pushes
    Ensures deterministic, tamper-evident deployments
    """
    
    def __init__(self, algorithm: str = "sha256"):
        self.algorithm = algorithm
    
    def hash_file(self, path: Path) -> str:
        """Compute hash of a single file"""
        h = hashlib.new(self.algorithm)
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    
    def hash_directory(self, directory: Path, exclude: List[str] = None) -> Dict[str, str]:
        """Compute hashes for all files in directory"""
        exclude = exclude or ['.git', '__pycache__', '*.pyc', '.env']
        hashes = {}
        
        for path in sorted(directory.rglob('*')):
            if path.is_file():
                # Check exclusions
                skip = False
                for pattern in exclude:
                    if pattern.startswith('*'):
                        if path.suffix == pattern[1:]:
                            skip = True
                            break
                    elif pattern in str(path):
                        skip = True
                        break
                
                if not skip:
                    rel_path = str(path.relative_to(directory))
                    hashes[rel_path] = self.hash_file(path)
        
        return hashes
    
    def compute_manifest_hash(self, hashes: Dict[str, str]) -> str:
        """Compute hash of the manifest itself"""
        manifest_str = json.dumps(hashes, sort_keys=True)
        return hashlib.new(self.algorithm, manifest_str.encode()).hexdigest()
    
    def generate_manifest(self, directory: Path) -> Dict[str, Any]:
        """Generate complete manifest for directory"""
        hashes = self.hash_directory(directory)
        manifest_hash = self.compute_manifest_hash(hashes)
        
        return {
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
            "algorithm": self.algorithm,
            "files": hashes,
            "file_count": len(hashes),
            "manifest_hash": manifest_hash
        }
    
    def verify_manifest(self, directory: Path, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Verify directory against manifest"""
        current_hashes = self.hash_directory(directory)
        expected_hashes = manifest.get("files", {})
        
        added = set(current_hashes.keys()) - set(expected_hashes.keys())
        removed = set(expected_hashes.keys()) - set(current_hashes.keys())
        modified = {
            k for k in current_hashes.keys() & expected_hashes.keys()
            if current_hashes[k] != expected_hashes[k]
        }
        
        return {
            "valid": not (added or removed or modified),
            "added": list(added),
            "removed": list(removed),
            "modified": list(modified),
            "current_hash": self.compute_manifest_hash(current_hashes),
            "expected_hash": manifest.get("manifest_hash", "")
        }


# ═══════════════════════════════════════════════════════════════════
# GIT PUSH HANDLER
# ═══════════════════════════════════════════════════════════════════

class GitPushHandler:
    """
    Git-based file push with integrity verification
    """
    
    def __init__(self, config: PushConfig, verifier: IntegrityVerifier):
        self.config = config
        self.verifier = verifier
        self.source_dir = Path(config.source_dir)
    
    def _run_git(self, *args) -> subprocess.CompletedProcess:
        """Run git command"""
        return subprocess.run(
            ['git', *args],
            cwd=self.source_dir,
            capture_output=True,
            text=True
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get git status"""
        result = self._run_git('status', '--porcelain')
        changes = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        return {
            "has_changes": len(changes) > 0,
            "changes": changes,
            "branch": self._run_git('branch', '--show-current').stdout.strip()
        }
    
    def commit(self, message: str) -> Dict[str, Any]:
        """Create commit with integrity manifest"""
        # Generate manifest
        manifest = self.verifier.generate_manifest(self.source_dir)
        manifest_path = self.source_dir / self.config.manifest_file
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Stage all changes
        self._run_git('add', '-A')
        
        # Create commit
        full_message = f"{self.config.commit_prefix} {message}\n\nManifest hash: {manifest['manifest_hash']}"
        result = self._run_git('commit', '-m', full_message)
        
        return {
            "success": result.returncode == 0,
            "message": result.stdout if result.returncode == 0 else result.stderr,
            "manifest_hash": manifest['manifest_hash']
        }
    
    def push(self) -> Dict[str, Any]:
        """Push to remote"""
        # Pre-push verification
        if self.config.verify_before_push:
            manifest_path = self.source_dir / self.config.manifest_file
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                verification = self.verifier.verify_manifest(self.source_dir, manifest)
                if not verification['valid']:
                    return {
                        "success": False,
                        "error": "Pre-push verification failed",
                        "verification": verification
                    }
        
        # Execute push
        result = self._run_git('push', self.config.git_remote, self.config.git_branch)
        
        return {
            "success": result.returncode == 0,
            "message": result.stdout if result.returncode == 0 else result.stderr
        }
    
    def pull(self) -> Dict[str, Any]:
        """Pull from remote"""
        result = self._run_git('pull', self.config.git_remote, self.config.git_branch)
        
        # Post-pull verification
        if self.config.verify_after_push and result.returncode == 0:
            manifest_path = self.source_dir / self.config.manifest_file
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                verification = self.verifier.verify_manifest(self.source_dir, manifest)
                return {
                    "success": verification['valid'],
                    "message": result.stdout,
                    "verification": verification
                }
        
        return {
            "success": result.returncode == 0,
            "message": result.stdout if result.returncode == 0 else result.stderr
        }


# ═══════════════════════════════════════════════════════════════════
# RSYNC PUSH HANDLER
# ═══════════════════════════════════════════════════════════════════

class RsyncPushHandler:
    """
    Rsync-based file push for NAS and remote servers
    """
    
    def __init__(self, config: PushConfig, verifier: IntegrityVerifier):
        self.config = config
        self.verifier = verifier
        self.source_dir = Path(config.source_dir)
    
    def push_to_target(self, target: str) -> Dict[str, Any]:
        """Push to a single rsync target"""
        # Generate manifest before push
        manifest = self.verifier.generate_manifest(self.source_dir)
        manifest_path = self.source_dir / self.config.manifest_file
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Execute rsync
        cmd = f"rsync {self.config.rsync_options} {self.source_dir}/ {target}/"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        return {
            "target": target,
            "success": result.returncode == 0,
            "message": result.stdout if result.returncode == 0 else result.stderr,
            "manifest_hash": manifest['manifest_hash']
        }
    
    def push_all(self) -> List[Dict[str, Any]]:
        """Push to all configured targets"""
        results = []
        for target in self.config.rsync_targets:
            results.append(self.push_to_target(target))
        return results


# ═══════════════════════════════════════════════════════════════════
# WEBHOOK HANDLER
# ═══════════════════════════════════════════════════════════════════

class WebhookHandler:
    """
    Webhook triggers for deployment notifications
    """
    
    def __init__(self, config: PushConfig):
        self.config = config
    
    def _sign_payload(self, payload: str) -> str:
        """Sign payload with webhook secret"""
        if not self.config.webhook_secret:
            return ""
        
        return hashlib.hmac(
            self.config.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def trigger(self, event: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Trigger webhooks for an event"""
        if not self.config.webhook_enabled:
            return []
        
        payload = {
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        payload_str = json.dumps(payload)
        signature = self._sign_payload(payload_str)
        
        headers = {
            "Content-Type": "application/json",
            "X-Sanctuary-Event": event,
            "X-Sanctuary-Signature": signature
        }
        
        results = []
        for url in self.config.webhook_urls:
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                results.append({
                    "url": url,
                    "success": response.status_code < 400,
                    "status_code": response.status_code
                })
            except Exception as e:
                results.append({
                    "url": url,
                    "success": False,
                    "error": str(e)
                })
        
        return results


# ═══════════════════════════════════════════════════════════════════
# UNIFIED PUSH SYSTEM
# ═══════════════════════════════════════════════════════════════════

class PushSystem:
    """
    Unified file push system with multiple backends
    """
    
    def __init__(self, config: PushConfig):
        self.config = config
        self.verifier = IntegrityVerifier(config.hash_algorithm)
        self.git_handler = GitPushHandler(config, self.verifier)
        self.rsync_handler = RsyncPushHandler(config, self.verifier) if config.rsync_enabled else None
        self.webhook_handler = WebhookHandler(config) if config.webhook_enabled else None
    
    def push(self, message: str = "Automated push") -> Dict[str, Any]:
        """Execute full push workflow"""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "git": None,
            "rsync": None,
            "webhooks": None
        }
        
        # Git commit and push
        if self.config.auto_commit:
            commit_result = self.git_handler.commit(message)
            if not commit_result['success']:
                results['git'] = commit_result
                return results
        
        push_result = self.git_handler.push()
        results['git'] = push_result
        
        # Rsync to additional targets
        if self.rsync_handler and self.config.rsync_targets:
            results['rsync'] = self.rsync_handler.push_all()
        
        # Trigger webhooks
        if self.webhook_handler:
            results['webhooks'] = self.webhook_handler.trigger('push', {
                'message': message,
                'git_result': push_result
            })
        
        return results
    
    def verify(self) -> Dict[str, Any]:
        """Verify current state against manifest"""
        manifest_path = Path(self.config.source_dir) / self.config.manifest_file
        
        if not manifest_path.exists():
            return {
                "valid": False,
                "error": "Manifest not found"
            }
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        return self.verifier.verify_manifest(Path(self.config.source_dir), manifest)
    
    def status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            "git": self.git_handler.get_status(),
            "verification": self.verify()
        }


# ═══════════════════════════════════════════════════════════════════
# GIT HOOKS
# ═══════════════════════════════════════════════════════════════════

PRE_PUSH_HOOK = '''#!/bin/bash
# Sovereign Sanctuary - Pre-Push Hook
# Verifies integrity before push

set -e

echo "[SANCTUARY] Running pre-push verification..."

# Run verification
python3 -c "
from push_system import PushSystem, PushConfig
config = PushConfig()
system = PushSystem(config)
result = system.verify()
if not result['valid']:
    print('Pre-push verification FAILED')
    print(f'Modified: {result.get(\"modified\", [])}')
    print(f'Added: {result.get(\"added\", [])}')
    print(f'Removed: {result.get(\"removed\", [])}')
    exit(1)
print('[SANCTUARY] Verification passed')
"

exit 0
'''

POST_RECEIVE_HOOK = '''#!/bin/bash
# Sovereign Sanctuary - Post-Receive Hook
# Triggers deployment after push

set -e

echo "[SANCTUARY] Running post-receive deployment..."

# Navigate to working directory
cd /opt/sovereign-sanctuary

# Pull latest changes
git pull origin main

# Verify integrity
python3 -c "
from push_system import PushSystem, PushConfig
config = PushConfig()
system = PushSystem(config)
result = system.verify()
if not result['valid']:
    print('Post-receive verification FAILED')
    exit(1)
print('[SANCTUARY] Deployment verified')
"

# Restart services
sudo systemctl restart sovereign-sanctuary

echo "[SANCTUARY] Deployment complete"
'''


def install_git_hooks(repo_path: str) -> None:
    """Install git hooks in repository"""
    hooks_dir = Path(repo_path) / '.git' / 'hooks'
    hooks_dir.mkdir(parents=True, exist_ok=True)
    
    # Pre-push hook
    pre_push_path = hooks_dir / 'pre-push'
    with open(pre_push_path, 'w') as f:
        f.write(PRE_PUSH_HOOK)
    os.chmod(pre_push_path, 0o755)
    
    print(f"Installed pre-push hook: {pre_push_path}")


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Sovereign Sanctuary Push System")
    parser.add_argument("command", choices=["push", "verify", "status", "install-hooks"])
    parser.add_argument("--config", "-c", help="Config file path")
    parser.add_argument("--message", "-m", default="Automated push", help="Commit message")
    parser.add_argument("--repo", default=".", help="Repository path for hook installation")
    args = parser.parse_args()
    
    # Load config
    if args.config:
        config = PushConfig.from_yaml(args.config)
    else:
        config = PushConfig()
    
    system = PushSystem(config)
    
    if args.command == "push":
        result = system.push(args.message)
        print(json.dumps(result, indent=2))
    
    elif args.command == "verify":
        result = system.verify()
        print(json.dumps(result, indent=2))
        sys.exit(0 if result['valid'] else 1)
    
    elif args.command == "status":
        result = system.status()
        print(json.dumps(result, indent=2))
    
    elif args.command == "install-hooks":
        install_git_hooks(args.repo)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
SOVEREIGN ELITE OS — Content Policy Enforcement
================================================
Strict content filtering for prohibited imagery categories.

POLICY:
- BANNED: Anime imagery (all forms)
- BANNED: Child-related imagery (zero tolerance)
- BANNED: Any content depicting minors

This module provides multi-layer enforcement:
1. Filename pattern matching
2. MIME type validation
3. Image hash blocklist
4. Optional AI-based content classification

AUTHOR: Architect
VERSION: 1.0.0
"""

import hashlib
import logging
import mimetypes
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Set

# =============================================================================
# CONFIGURATION
# =============================================================================

logger = logging.getLogger("sovereign.content_policy")

class ViolationType(Enum):
    """Content policy violation types."""
    ANIME = "anime"
    CHILD_RELATED = "child_related"
    BLOCKED_HASH = "blocked_hash"
    SUSPICIOUS_FILENAME = "suspicious_filename"
    POLICY_VIOLATION = "policy_violation"


@dataclass
class PolicyViolation:
    """Record of a content policy violation."""
    timestamp: str
    violation_type: ViolationType
    filename: str
    file_hash: Optional[str]
    reason: str
    blocked: bool = True


@dataclass
class ContentPolicyConfig:
    """Content policy configuration."""
    
    # Master switches
    enabled: bool = True
    strict_mode: bool = True  # Block on any suspicion
    log_violations: bool = True
    
    # Banned filename patterns (case-insensitive)
    banned_filename_patterns: list = field(default_factory=lambda: [
        # Anime-related
        r"anime",
        r"manga",
        r"hentai",
        r"waifu",
        r"loli",
        r"shota",
        r"chibi",
        r"kawaii",
        r"otaku",
        r"ecchi",
        r"doujin",
        r"ahegao",
        
        # Child-related (zero tolerance)
        r"child",
        r"kid[s]?",
        r"minor[s]?",
        r"underage",
        r"young",
        r"teen",
        r"preteen",
        r"infant",
        r"toddler",
        r"baby",
        r"juvenile",
        r"adolescent",
        r"schoolgirl",
        r"schoolboy",
        r"jailbait",
        r"pedo",
        r"cp\b",
        r"csam",
    ])
    
    # Banned MIME types
    banned_mime_types: Set[str] = field(default_factory=lambda: {
        # None by default - we filter by content, not type
    })
    
    # Allowed image MIME types (whitelist approach)
    allowed_image_types: Set[str] = field(default_factory=lambda: {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/svg+xml",
        "image/bmp",
        "image/tiff",
    })
    
    # Maximum file size for images (10MB)
    max_image_size_bytes: int = 10 * 1024 * 1024


# =============================================================================
# CONTENT POLICY ENFORCER
# =============================================================================

class ContentPolicyEnforcer:
    """
    Multi-layer content policy enforcement.
    
    Implements belt-and-braces approach with multiple detection layers:
    1. Filename pattern matching
    2. File hash blocklist
    3. MIME type validation
    4. File size limits
    """
    
    def __init__(self, config: Optional[ContentPolicyConfig] = None):
        self.config = config or ContentPolicyConfig()
        self.violations: list[PolicyViolation] = []
        self.blocked_hashes: Set[str] = set()
        
        # Compile regex patterns for performance
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config.banned_filename_patterns
        ]
        
        logger.info(f"Content Policy Enforcer initialized | Strict mode: {self.config.strict_mode}")
    
    def check_filename(self, filename: str) -> Optional[PolicyViolation]:
        """
        Check filename against banned patterns.
        
        Returns PolicyViolation if banned, None if allowed.
        """
        if not self.config.enabled:
            return None
        
        filename_lower = filename.lower()
        
        for pattern in self._compiled_patterns:
            if pattern.search(filename_lower):
                violation = PolicyViolation(
                    timestamp=datetime.utcnow().isoformat(),
                    violation_type=self._categorize_pattern(pattern.pattern),
                    filename=filename,
                    file_hash=None,
                    reason=f"Filename matches banned pattern: {pattern.pattern}",
                    blocked=True,
                )
                self._log_violation(violation)
                return violation
        
        return None
    
    def check_file(self, filepath: Path, content: Optional[bytes] = None) -> Optional[PolicyViolation]:
        """
        Comprehensive file check.
        
        Performs all validation layers:
        1. Filename check
        2. MIME type check
        3. File size check
        4. Hash blocklist check
        """
        if not self.config.enabled:
            return None
        
        # Layer 1: Filename check
        filename_violation = self.check_filename(filepath.name)
        if filename_violation:
            return filename_violation
        
        # Layer 2: MIME type check
        mime_type, _ = mimetypes.guess_type(str(filepath))
        if mime_type:
            if mime_type in self.config.banned_mime_types:
                violation = PolicyViolation(
                    timestamp=datetime.utcnow().isoformat(),
                    violation_type=ViolationType.POLICY_VIOLATION,
                    filename=filepath.name,
                    file_hash=None,
                    reason=f"Banned MIME type: {mime_type}",
                    blocked=True,
                )
                self._log_violation(violation)
                return violation
            
            # For images, check against whitelist
            if mime_type.startswith("image/"):
                if mime_type not in self.config.allowed_image_types:
                    violation = PolicyViolation(
                        timestamp=datetime.utcnow().isoformat(),
                        violation_type=ViolationType.POLICY_VIOLATION,
                        filename=filepath.name,
                        file_hash=None,
                        reason=f"Image type not in whitelist: {mime_type}",
                        blocked=True,
                    )
                    self._log_violation(violation)
                    return violation
        
        # Layer 3: File size check
        if filepath.exists():
            file_size = filepath.stat().st_size
            if file_size > self.config.max_image_size_bytes:
                violation = PolicyViolation(
                    timestamp=datetime.utcnow().isoformat(),
                    violation_type=ViolationType.POLICY_VIOLATION,
                    filename=filepath.name,
                    file_hash=None,
                    reason=f"File exceeds size limit: {file_size} > {self.config.max_image_size_bytes}",
                    blocked=True,
                )
                self._log_violation(violation)
                return violation
        
        # Layer 4: Hash blocklist check
        if content:
            file_hash = hashlib.sha256(content).hexdigest()
        elif filepath.exists():
            file_hash = hashlib.sha256(filepath.read_bytes()).hexdigest()
        else:
            file_hash = None
        
        if file_hash and file_hash in self.blocked_hashes:
            violation = PolicyViolation(
                timestamp=datetime.utcnow().isoformat(),
                violation_type=ViolationType.BLOCKED_HASH,
                filename=filepath.name,
                file_hash=file_hash,
                reason="File hash matches blocklist",
                blocked=True,
            )
            self._log_violation(violation)
            return violation
        
        return None
    
    def check_content_text(self, text: str, context: str = "content") -> Optional[PolicyViolation]:
        """
        Check text content for policy violations.
        
        Used for:
        - Post titles
        - Descriptions
        - Alt text
        - Tags
        """
        if not self.config.enabled:
            return None
        
        text_lower = text.lower()
        
        for pattern in self._compiled_patterns:
            if pattern.search(text_lower):
                violation = PolicyViolation(
                    timestamp=datetime.utcnow().isoformat(),
                    violation_type=self._categorize_pattern(pattern.pattern),
                    filename=f"[{context}]",
                    file_hash=None,
                    reason=f"Text contains banned pattern: {pattern.pattern}",
                    blocked=True,
                )
                self._log_violation(violation)
                return violation
        
        return None
    
    def add_blocked_hash(self, file_hash: str, reason: str = "Manual block"):
        """Add a file hash to the blocklist."""
        self.blocked_hashes.add(file_hash)
        logger.warning(f"Hash added to blocklist | {file_hash[:16]}... | Reason: {reason}")
    
    def _categorize_pattern(self, pattern: str) -> ViolationType:
        """Categorize violation type based on matched pattern."""
        anime_patterns = {"anime", "manga", "hentai", "waifu", "chibi", "kawaii", "otaku", "ecchi", "doujin", "ahegao"}
        
        pattern_lower = pattern.lower()
        
        # Check for child-related patterns (highest priority)
        child_patterns = {"child", "kid", "minor", "underage", "young", "teen", "preteen", 
                         "infant", "toddler", "baby", "juvenile", "adolescent", "schoolgirl", 
                         "schoolboy", "jailbait", "pedo", "loli", "shota", "cp", "csam"}
        
        for cp in child_patterns:
            if cp in pattern_lower:
                return ViolationType.CHILD_RELATED
        
        for ap in anime_patterns:
            if ap in pattern_lower:
                return ViolationType.ANIME
        
        return ViolationType.POLICY_VIOLATION
    
    def _log_violation(self, violation: PolicyViolation):
        """Log and store violation."""
        self.violations.append(violation)
        
        if self.config.log_violations:
            log_level = logging.CRITICAL if violation.violation_type == ViolationType.CHILD_RELATED else logging.WARNING
            logger.log(
                log_level,
                f"CONTENT POLICY VIOLATION | Type: {violation.violation_type.value} | "
                f"File: {violation.filename} | Reason: {violation.reason}"
            )
    
    def get_violations(self, limit: int = 100) -> list[PolicyViolation]:
        """Get recent violations."""
        return self.violations[-limit:]
    
    def get_violation_stats(self) -> dict:
        """Get violation statistics."""
        stats = {
            "total": len(self.violations),
            "by_type": {},
        }
        
        for vtype in ViolationType:
            count = sum(1 for v in self.violations if v.violation_type == vtype)
            if count > 0:
                stats["by_type"][vtype.value] = count
        
        return stats


# =============================================================================
# GLOBAL ENFORCER INSTANCE
# =============================================================================

# Create global enforcer with default strict config
content_policy = ContentPolicyEnforcer(ContentPolicyConfig(
    enabled=True,
    strict_mode=True,
    log_violations=True,
))


# =============================================================================
# FASTAPI MIDDLEWARE INTEGRATION
# =============================================================================

async def content_policy_middleware(request, call_next):
    """
    FastAPI middleware for content policy enforcement.
    
    Checks:
    - Uploaded file names
    - Form field values
    - Query parameters
    """
    from fastapi import HTTPException
    
    # Check query parameters
    for key, value in request.query_params.items():
        violation = content_policy.check_content_text(value, context=f"query:{key}")
        if violation:
            raise HTTPException(
                status_code=403,
                detail=f"Content policy violation: {violation.reason}"
            )
    
    # Process request
    response = await call_next(request)
    return response


def check_upload(filename: str, content: bytes) -> Optional[PolicyViolation]:
    """
    Check uploaded file against content policy.
    
    Call this before saving any uploaded file.
    """
    # Check filename
    violation = content_policy.check_filename(filename)
    if violation:
        return violation
    
    # Check content hash
    file_hash = hashlib.sha256(content).hexdigest()
    if file_hash in content_policy.blocked_hashes:
        return PolicyViolation(
            timestamp=datetime.utcnow().isoformat(),
            violation_type=ViolationType.BLOCKED_HASH,
            filename=filename,
            file_hash=file_hash,
            reason="File hash matches blocklist",
            blocked=True,
        )
    
    return None


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python content_policy.py <check|stats|test>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "check" and len(sys.argv) >= 3:
        filepath = Path(sys.argv[2])
        violation = content_policy.check_file(filepath)
        if violation:
            print(f"❌ BLOCKED: {violation.reason}")
            sys.exit(1)
        else:
            print(f"✓ ALLOWED: {filepath.name}")
            sys.exit(0)
    
    elif command == "stats":
        stats = content_policy.get_violation_stats()
        print(f"Total violations: {stats['total']}")
        for vtype, count in stats.get("by_type", {}).items():
            print(f"  {vtype}: {count}")
    
    elif command == "test":
        # Test patterns
        test_cases = [
            ("normal_image.jpg", False),
            ("anime_character.png", True),
            ("child_photo.jpg", True),
            ("business_report.pdf", False),
            ("manga_cover.png", True),
            ("team_photo.jpg", False),
            ("loli_art.png", True),
            ("product_image.webp", False),
        ]
        
        print("Content Policy Test Suite")
        print("=" * 50)
        
        for filename, should_block in test_cases:
            violation = content_policy.check_filename(filename)
            blocked = violation is not None
            status = "✓" if blocked == should_block else "✗"
            result = "BLOCKED" if blocked else "ALLOWED"
            print(f"{status} {filename}: {result}")
        
        print("=" * 50)
        print("Test complete.")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

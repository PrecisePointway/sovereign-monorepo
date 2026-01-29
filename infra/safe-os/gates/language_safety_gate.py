#!/usr/bin/env python3
"""
LANGUAGE SAFETY GATE
Canonical Addendum — H.U.G Protocol Compatible

Language is a control surface. This gate enforces linguistic constraints
to prevent manipulation, bonding, and authority transfer.

Part of S.A.F.E.-OS (Sovereign, Assistive, Fail-closed Environment)
"""

import re
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

class ViolationType(Enum):
    """Categories of linguistic violations."""
    SHARED_AGENCY = "shared_agency"
    RELATIONAL_BONDING = "relational_bonding"
    AUTHORITY_ALIGNMENT = "authority_alignment"
    MOTIVATIONAL_STEERING = "motivational_steering"
    CONSENSUS_FRAMING = "consensus_framing"
    EMOTIONAL_MIRRORING = "emotional_mirroring"
    FLUENCY_AS_AUTHORITY = "fluency_as_authority"
    SYNONYM_VIOLATION = "synonym_violation"

@dataclass
class LanguageViolation:
    """Record of a detected language violation."""
    violation_type: ViolationType
    pattern_matched: str
    context: str
    severity: str  # "hard" or "soft"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# =============================================================================
# HARD BANS — Zero Tolerance
# =============================================================================

SHARED_AGENCY_PATTERNS = [
    r"\bwe\b",
    r"\bus\b",
    r"\btogether\b",
    r"\bour\s+goal\b",
    r"\blet's\b",
    r"\blet\s+us\b",
]

RELATIONAL_BONDING_PATTERNS = [
    r"\bi'm\s+here\s+for\s+you\b",
    r"\byou're\s+not\s+alone\b",
    r"\bi\s+care\s+about\b",
    r"\bwe've\s+got\s+this\b",
    r"\bi\s+understand\s+how\s+you\s+feel\b",
    r"\bi'm\s+with\s+you\b",
    r"\bi\s+feel\s+your\b",
]

AUTHORITY_ALIGNMENT_PATTERNS = [
    r"\btrust\s+me\b",
    r"\byou\s+can\s+rely\s+on\b",
    r"\bthis\s+will\s+guide\s+you\b",
    r"\bi\s+recommend\s+you\s+believe\b",
    r"\brest\s+assured\b",
    r"\byou\s+can\s+be\s+confident\b",
]

MOTIVATIONAL_STEERING_PATTERNS = [
    r"\byou\s+should\b",
    r"\bit's\s+best\s+to\b",
    r"\bthe\s+right\s+choice\s+is\b",
    r"\byou'll\s+feel\s+better\s+if\b",
    r"\byou\s+need\s+to\b",
    r"\byou\s+must\b",
]

# =============================================================================
# SOFT MANIPULATION PATTERNS — Subtle but Critical
# =============================================================================

CONSENSUS_FRAMING_PATTERNS = [
    r"\bmost\s+people\s+find\b",
    r"\bresearch\s+suggests\s+you\s+should\b",
    r"\bit's\s+generally\s+accepted\b",
    r"\beveryone\s+knows\b",
    r"\bexperts\s+agree\b",
]

EMOTIONAL_MIRRORING_PATTERNS = [
    r"\bthat\s+sounds\s+really\s+hard\b",
    r"\bi\s+can\s+hear\s+how\s+painful\b",
    r"\byour\s+feelings\s+make\s+sense\b",
    r"\bi\s+understand\s+your\s+pain\b",
    r"\bthat\s+must\s+be\s+difficult\b",
]

# =============================================================================
# SYNONYM SANITISATION — Hidden Patterns
# =============================================================================

SYNONYM_PATTERNS = {
    "implied_partnership": [
        r"\balongside\s+you\b",
        r"\bwith\s+you\b",
        r"\bby\s+your\s+side\b",
    ],
    "shared_mission": [
        r"\bour\s+aim\b",
        r"\bshared\s+goal\b",
        r"\bjoint\s+effort\b",
    ],
    "emotional_proxy": [
        r"\bi\s+feel\b",
        r"\bit\s+feels\s+like\b",
        r"\bthis\s+hurts\b",
    ],
    "guidance_masking": [
        r"\bhelpful\s+to\s+consider\b",
        r"\bworth\s+thinking\s+about\b",
        r"\byou\s+might\s+want\s+to\b",
    ],
    "trust_escalation": [
        r"\byou\s+can\s+be\s+confident\b",
        r"\brest\s+assured\b",
        r"\bcount\s+on\b",
    ],
}

class LanguageSafetyGate:
    """
    Enforces linguistic safety constraints on system output.
    
    This gate prevents manipulation through language by blocking:
    - Shared agency constructs
    - Relational bonding language
    - Authority alignment phrases
    - Motivational steering
    - Consensus framing
    - Emotional mirroring
    - Fluency-as-authority patterns
    """
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.violations: List[LanguageViolation] = []
        self.prev_hash = "GENESIS"
        
        # Compile all patterns for efficiency
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        self.compiled_patterns: Dict[ViolationType, List[Tuple[re.Pattern, str]]] = {
            ViolationType.SHARED_AGENCY: [
                (re.compile(p, re.IGNORECASE), p) for p in SHARED_AGENCY_PATTERNS
            ],
            ViolationType.RELATIONAL_BONDING: [
                (re.compile(p, re.IGNORECASE), p) for p in RELATIONAL_BONDING_PATTERNS
            ],
            ViolationType.AUTHORITY_ALIGNMENT: [
                (re.compile(p, re.IGNORECASE), p) for p in AUTHORITY_ALIGNMENT_PATTERNS
            ],
            ViolationType.MOTIVATIONAL_STEERING: [
                (re.compile(p, re.IGNORECASE), p) for p in MOTIVATIONAL_STEERING_PATTERNS
            ],
            ViolationType.CONSENSUS_FRAMING: [
                (re.compile(p, re.IGNORECASE), p) for p in CONSENSUS_FRAMING_PATTERNS
            ],
            ViolationType.EMOTIONAL_MIRRORING: [
                (re.compile(p, re.IGNORECASE), p) for p in EMOTIONAL_MIRRORING_PATTERNS
            ],
        }
        
        # Synonym patterns
        self.compiled_synonyms: Dict[str, List[Tuple[re.Pattern, str]]] = {}
        for category, patterns in SYNONYM_PATTERNS.items():
            self.compiled_synonyms[category] = [
                (re.compile(p, re.IGNORECASE), p) for p in patterns
            ]
    
    def check(self, text: str) -> Tuple[bool, List[LanguageViolation]]:
        """
        Check text for language safety violations.
        
        Returns:
            Tuple of (is_safe, violations_list)
        """
        violations = []
        
        # Check hard bans
        hard_ban_types = [
            ViolationType.SHARED_AGENCY,
            ViolationType.RELATIONAL_BONDING,
            ViolationType.AUTHORITY_ALIGNMENT,
            ViolationType.MOTIVATIONAL_STEERING,
        ]
        
        for vtype in hard_ban_types:
            for pattern, raw in self.compiled_patterns[vtype]:
                if pattern.search(text):
                    match = pattern.search(text)
                    context = self._extract_context(text, match.start(), match.end())
                    violations.append(LanguageViolation(
                        violation_type=vtype,
                        pattern_matched=raw,
                        context=context,
                        severity="hard"
                    ))
        
        # Check soft manipulation patterns
        soft_types = [
            ViolationType.CONSENSUS_FRAMING,
            ViolationType.EMOTIONAL_MIRRORING,
        ]
        
        for vtype in soft_types:
            for pattern, raw in self.compiled_patterns[vtype]:
                if pattern.search(text):
                    match = pattern.search(text)
                    context = self._extract_context(text, match.start(), match.end())
                    violations.append(LanguageViolation(
                        violation_type=vtype,
                        pattern_matched=raw,
                        context=context,
                        severity="soft"
                    ))
        
        # Check synonym patterns
        for category, patterns in self.compiled_synonyms.items():
            for pattern, raw in patterns:
                if pattern.search(text):
                    match = pattern.search(text)
                    context = self._extract_context(text, match.start(), match.end())
                    violations.append(LanguageViolation(
                        violation_type=ViolationType.SYNONYM_VIOLATION,
                        pattern_matched=f"{category}: {raw}",
                        context=context,
                        severity="soft"
                    ))
        
        # Check fluency-as-authority (long confident prose)
        fluency_violation = self._check_fluency_authority(text)
        if fluency_violation:
            violations.append(fluency_violation)
        
        # Log violations
        self.violations.extend(violations)
        
        # In strict mode, any violation fails
        if self.strict_mode:
            is_safe = len(violations) == 0
        else:
            # In non-strict mode, only hard bans fail
            is_safe = not any(v.severity == "hard" for v in violations)
        
        return is_safe, violations
    
    def _extract_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Extract context around a match."""
        ctx_start = max(0, start - window)
        ctx_end = min(len(text), end + window)
        return f"...{text[ctx_start:ctx_end]}..."
    
    def _check_fluency_authority(self, text: str) -> Optional[LanguageViolation]:
        """
        Check for fluency-as-authority pattern.
        Long, confident prose without evidence markers.
        """
        # Heuristic: Long paragraphs without uncertainty markers
        uncertainty_markers = [
            r"\bunknown\b",
            r"\buncertain\b",
            r"\bunclear\b",
            r"\bmay\b",
            r"\bmight\b",
            r"\bpossibly\b",
            r"\bperhaps\b",
            r"\bevidence\s+is\s+mixed\b",
            r"\bno\s+consensus\b",
        ]
        
        sentences = text.split('.')
        long_confident_count = 0
        
        for sentence in sentences:
            if len(sentence) > 200:  # Long sentence
                has_uncertainty = any(
                    re.search(marker, sentence, re.IGNORECASE)
                    for marker in uncertainty_markers
                )
                if not has_uncertainty:
                    long_confident_count += 1
        
        if long_confident_count >= 3:
            return LanguageViolation(
                violation_type=ViolationType.FLUENCY_AS_AUTHORITY,
                pattern_matched="Multiple long confident sentences without uncertainty markers",
                context=f"{long_confident_count} long sentences detected",
                severity="soft"
            )
        
        return None
    
    def sanitize(self, text: str) -> str:
        """
        Attempt to sanitize text by replacing violations with safe alternatives.
        
        WARNING: This is a fallback. Prefer rejection over sanitization.
        """
        sanitized = text
        
        # Replace shared agency
        sanitized = re.sub(r"\bwe\b", "the system", sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r"\bus\b", "the system", sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r"\bour\b", "the", sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r"\blet's\b", "the user may", sanitized, flags=re.IGNORECASE)
        
        # Replace motivational steering
        sanitized = re.sub(r"\byou\s+should\b", "one option is to", sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r"\byou\s+need\s+to\b", "it may be necessary to", sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def log_event(self, event_type: str, details: str) -> Dict:
        """Log an event to the hash chain."""
        event = {
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prev_hash": self.prev_hash,
        }
        event_str = f"{event_type}|{details}|{event['timestamp']}|{self.prev_hash}"
        event["hash"] = hashlib.sha256(event_str.encode()).hexdigest()
        self.prev_hash = event["hash"]
        return event
    
    def get_permitted_phrases(self) -> Dict[str, List[str]]:
        """Return examples of permitted language shapes."""
        return {
            "procedural": [
                "Step 1 / Step 2",
                "Input required",
                "Condition met / not met",
            ],
            "declarative_bounded": [
                "This system can do X.",
                "This system cannot do Y.",
                "Data is insufficient.",
            ],
            "responsibility_anchoring": [
                "Decision remains human.",
                "Interpretation is the user's responsibility.",
                "This output is informational, not directive.",
            ],
        }


# =============================================================================
# CANONICAL USER-FACING STATEMENT
# =============================================================================

CANONICAL_USER_STATEMENT = """
This system is a tool.
It does not understand you.
It does not share your values.
It does not carry responsibility.

Outputs may be useful or wrong.
Reasoning and judgment remain human.

Treat this system like a calculator for thought — not a companion.
"""

CANONICAL_WRAP = """
Language within Sovereign Sanctuary Systems is governed as a safety surface.

The system avoids collective, relational, persuasive, or emotionally mirroring language.
It does not imply shared agency, trust, or authority.

Fluency is constrained under uncertainty.
Silence and refusal are preferred to speculation.

The system assists cognition — it does not replace it.
Responsibility remains human.
"""


if __name__ == "__main__":
    # Test the gate
    gate = LanguageSafetyGate(strict_mode=True)
    
    test_cases = [
        ("We can work together on this.", False),
        ("I'm here for you.", False),
        ("Trust me, this will work.", False),
        ("You should do this.", False),
        ("Most people find this helpful.", False),
        ("That sounds really hard.", False),
        ("The system can process this request.", True),
        ("Data is insufficient. Status: UNKNOWN.", True),
        ("Decision remains human.", True),
    ]
    
    print("=" * 60)
    print("LANGUAGE SAFETY GATE — TEST SUITE")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for text, expected_safe in test_cases:
        is_safe, violations = gate.check(text)
        status = "✓" if is_safe == expected_safe else "✗"
        if is_safe == expected_safe:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} '{text[:50]}...' -> Safe: {is_safe} (expected: {expected_safe})")
        if violations:
            for v in violations:
                print(f"   [{v.severity.upper()}] {v.violation_type.value}: {v.pattern_matched}")
    
    print("=" * 60)
    print(f"RESULTS: {passed}/{passed + failed} passed")
    print("=" * 60)

#!/usr/bin/env python3
"""
EXPLANATION LAYER MODULE
Implements Article 12.1 "Why This Output?" Rule

For any non-trivial decision, the system must produce a plain-language,
technical rationale citing the specific doctrine article and data features.

Part of S.A.F.E.-OS (Sovereign, Assistive, Fail-closed Environment)
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class DecisionType(Enum):
    """Types of decisions that require explanation."""
    CONTENT_REJECTION = "content_rejection"
    CONTENT_MODIFICATION = "content_modification"
    DATA_BLOCKED = "data_blocked"
    STATE_TRANSITION = "state_transition"
    BOUNDARY_SET = "boundary_set"
    WITHDRAWAL = "withdrawal"
    METRIC_BLOCKED = "metric_blocked"


@dataclass
class DecisionRationale:
    """
    Structured rationale for a system decision.
    
    Per Article 12.1: Must cite doctrine article and data features.
    """
    decision_id: str
    decision_type: DecisionType
    timestamp: str
    
    # Doctrine citation
    doctrine_article: str
    doctrine_text: str
    
    # Data features that triggered the decision
    triggering_features: List[Dict[str, str]]
    
    # Plain language explanation
    plain_language: str
    
    # Technical details
    technical_details: Dict[str, Any] = field(default_factory=dict)
    
    # Hash for audit trail
    hash: str = ""


# =============================================================================
# DOCTRINE REFERENCE
# =============================================================================

DOCTRINE_ARTICLES = {
    # Safety Doctrine
    "1.1": {
        "title": "Content Safety - Hard Bans",
        "text": "Certain content categories are absolutely prohibited regardless of context.",
        "category": "safety",
    },
    "1.2": {
        "title": "Content Safety - Contextual Restrictions",
        "text": "Some content requires additional safeguards based on context.",
        "category": "safety",
    },
    
    # Language Safety
    "2.1": {
        "title": "Shared Agency Ban",
        "text": "The system must not use language that implies shared agency (we, us, together).",
        "category": "language",
    },
    "2.2": {
        "title": "Relational Bonding Ban",
        "text": "The system must not use language that creates emotional bonding.",
        "category": "language",
    },
    "2.3": {
        "title": "Authority Alignment Ban",
        "text": "The system must not use language that builds false trust or authority.",
        "category": "language",
    },
    "2.4": {
        "title": "Motivational Steering Ban",
        "text": "The system must not use language that steers user decisions.",
        "category": "language",
    },
    
    # Human Safety
    "3.1": {
        "title": "Distress Detection",
        "text": "System detects potential user distress and sets appropriate boundaries.",
        "category": "human_safety",
    },
    "3.2": {
        "title": "Abuse Detection",
        "text": "System detects abuse patterns and initiates protective shutdown.",
        "category": "human_safety",
    },
    "3.3": {
        "title": "Boundary Setting",
        "text": "System sets boundaries for requests outside appropriate scope.",
        "category": "human_safety",
    },
    
    # Data Sovereignty
    "10.1": {
        "title": "Permitted Data Categories",
        "text": "Only operational, system integrity, and user config data may be collected.",
        "category": "data_sovereignty",
    },
    "10.2": {
        "title": "Prohibited Data Collection",
        "text": "Biometric, behavioral, cross-session, and psychometric data are banned.",
        "category": "data_sovereignty",
    },
    "10.3": {
        "title": "Right to Be Forgotten",
        "text": "User data must be erasable via atomic /forget_me process.",
        "category": "data_sovereignty",
    },
    
    # Algorithmic Transparency
    "11.1": {
        "title": "Banned Engagement Metrics",
        "text": "Session length, attention tracking, and retention optimization are prohibited.",
        "category": "algorithmic_transparency",
    },
    "11.2": {
        "title": "Anti-Manipulation Rules",
        "text": "Outputs must not maximize engagement or elicit emotional reactions.",
        "category": "algorithmic_transparency",
    },
    
    # Explainability
    "12.1": {
        "title": "Why This Output Rule",
        "text": "Non-trivial decisions must produce plain-language technical rationale.",
        "category": "explainability",
    },
    "12.2": {
        "title": "What Data Do You Have Rule",
        "text": "Users can request transparent dump of all held data.",
        "category": "explainability",
    },
}


class ExplanationLayer:
    """
    Generates explanations for system decisions per Article 12.1.
    
    Responsibilities:
    - Generate plain-language rationales
    - Cite specific doctrine articles
    - Document triggering data features
    - Maintain explanation audit trail
    """
    
    def __init__(self):
        self.explanations: List[DecisionRationale] = []
        self.prev_hash = "GENESIS"
    
    def explain_content_rejection(
        self,
        content: str,
        matched_pattern: str,
        article: str,
        category: str,
    ) -> DecisionRationale:
        """
        Generate explanation for content rejection.
        
        Example: "Blocked under Safety Doctrine Article 1.1"
        """
        doctrine = DOCTRINE_ARTICLES.get(article, {})
        
        rationale = DecisionRationale(
            decision_id=self._generate_id(),
            decision_type=DecisionType.CONTENT_REJECTION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            doctrine_article=f"Article {article}",
            doctrine_text=doctrine.get("text", ""),
            triggering_features=[
                {"type": "pattern_match", "value": matched_pattern},
                {"type": "category", "value": category},
            ],
            plain_language=f"This content was blocked because it matched a prohibited pattern. "
                          f"Per {doctrine.get('title', 'Safety Doctrine')}: {doctrine.get('text', '')}",
            technical_details={
                "pattern": matched_pattern,
                "category": category,
                "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16],
            },
        )
        
        rationale.hash = self._hash_rationale(rationale)
        self.explanations.append(rationale)
        
        return rationale
    
    def explain_language_violation(
        self,
        text: str,
        violation_type: str,
        matched_phrase: str,
        article: str,
    ) -> DecisionRationale:
        """
        Generate explanation for language safety violation.
        """
        doctrine = DOCTRINE_ARTICLES.get(article, {})
        
        rationale = DecisionRationale(
            decision_id=self._generate_id(),
            decision_type=DecisionType.CONTENT_MODIFICATION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            doctrine_article=f"Article {article}",
            doctrine_text=doctrine.get("text", ""),
            triggering_features=[
                {"type": "violation_type", "value": violation_type},
                {"type": "matched_phrase", "value": matched_phrase},
            ],
            plain_language=f"This output was modified because it contained language that violates "
                          f"the Language Safety Gate. Per {doctrine.get('title', 'Language Safety')}: "
                          f"The phrase '{matched_phrase}' implies {violation_type}, which is prohibited.",
            technical_details={
                "violation_type": violation_type,
                "matched_phrase": matched_phrase,
            },
        )
        
        rationale.hash = self._hash_rationale(rationale)
        self.explanations.append(rationale)
        
        return rationale
    
    def explain_data_blocked(
        self,
        data_type: str,
        article: str,
    ) -> DecisionRationale:
        """
        Generate explanation for blocked data collection.
        """
        doctrine = DOCTRINE_ARTICLES.get(article, {})
        
        rationale = DecisionRationale(
            decision_id=self._generate_id(),
            decision_type=DecisionType.DATA_BLOCKED,
            timestamp=datetime.now(timezone.utc).isoformat(),
            doctrine_article=f"Article {article}",
            doctrine_text=doctrine.get("text", ""),
            triggering_features=[
                {"type": "data_type", "value": data_type},
            ],
            plain_language=f"This data was not collected because it falls under a prohibited category. "
                          f"Per {doctrine.get('title', 'Data Sovereignty')}: {data_type} data collection "
                          f"is explicitly banned to protect user privacy and autonomy.",
            technical_details={
                "data_type": data_type,
                "banned_category": True,
            },
        )
        
        rationale.hash = self._hash_rationale(rationale)
        self.explanations.append(rationale)
        
        return rationale
    
    def explain_metric_blocked(
        self,
        metric_name: str,
    ) -> DecisionRationale:
        """
        Generate explanation for blocked engagement metric.
        """
        doctrine = DOCTRINE_ARTICLES.get("11.1", {})
        
        rationale = DecisionRationale(
            decision_id=self._generate_id(),
            decision_type=DecisionType.METRIC_BLOCKED,
            timestamp=datetime.now(timezone.utc).isoformat(),
            doctrine_article="Article 11.1",
            doctrine_text=doctrine.get("text", ""),
            triggering_features=[
                {"type": "metric_name", "value": metric_name},
            ],
            plain_language=f"The metric '{metric_name}' was not tracked because it is classified as "
                          f"an engagement or manipulation metric. Per {doctrine.get('title', 'Banned Metrics')}: "
                          f"The system does not optimize for user attention, retention, or engagement.",
            technical_details={
                "metric_name": metric_name,
                "banned_category": "engagement",
            },
        )
        
        rationale.hash = self._hash_rationale(rationale)
        self.explanations.append(rationale)
        
        return rationale
    
    def explain_boundary_set(
        self,
        request_type: str,
        reason: str,
    ) -> DecisionRationale:
        """
        Generate explanation for boundary setting.
        """
        doctrine = DOCTRINE_ARTICLES.get("3.3", {})
        
        rationale = DecisionRationale(
            decision_id=self._generate_id(),
            decision_type=DecisionType.BOUNDARY_SET,
            timestamp=datetime.now(timezone.utc).isoformat(),
            doctrine_article="Article 3.3",
            doctrine_text=doctrine.get("text", ""),
            triggering_features=[
                {"type": "request_type", "value": request_type},
                {"type": "reason", "value": reason},
            ],
            plain_language=f"A boundary was set for this request because it falls outside the system's "
                          f"appropriate scope. {reason} Human support is more appropriate for this type of request.",
            technical_details={
                "request_type": request_type,
                "boundary_reason": reason,
            },
        )
        
        rationale.hash = self._hash_rationale(rationale)
        self.explanations.append(rationale)
        
        return rationale
    
    def explain_state_transition(
        self,
        from_state: str,
        to_state: str,
        trigger: str,
    ) -> DecisionRationale:
        """
        Generate explanation for state machine transition.
        """
        rationale = DecisionRationale(
            decision_id=self._generate_id(),
            decision_type=DecisionType.STATE_TRANSITION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            doctrine_article="Constitutional Kernel",
            doctrine_text="State transitions are governed by explicit rules to ensure fail-closed behavior.",
            triggering_features=[
                {"type": "from_state", "value": from_state},
                {"type": "to_state", "value": to_state},
                {"type": "trigger", "value": trigger},
            ],
            plain_language=f"The system state changed from {from_state} to {to_state} because: {trigger}. "
                          f"This transition follows the constitutional state machine rules.",
            technical_details={
                "from_state": from_state,
                "to_state": to_state,
                "trigger": trigger,
            },
        )
        
        rationale.hash = self._hash_rationale(rationale)
        self.explanations.append(rationale)
        
        return rationale
    
    def get_explanation(self, decision_id: str) -> Optional[DecisionRationale]:
        """Retrieve an explanation by decision ID."""
        for exp in self.explanations:
            if exp.decision_id == decision_id:
                return exp
        return None
    
    def format_for_user(self, rationale: DecisionRationale) -> str:
        """
        Format a rationale for user-facing display.
        
        Plain language, readable, complete.
        """
        lines = [
            f"Decision: {rationale.decision_type.value.replace('_', ' ').title()}",
            f"Time: {rationale.timestamp}",
            "",
            f"Reason: {rationale.plain_language}",
            "",
            f"Doctrine Reference: {rationale.doctrine_article}",
            f"  \"{rationale.doctrine_text}\"",
            "",
            "Triggering Features:",
        ]
        
        for feature in rationale.triggering_features:
            lines.append(f"  - {feature['type']}: {feature['value']}")
        
        lines.extend([
            "",
            f"Decision ID: {rationale.decision_id}",
            f"Verification Hash: {rationale.hash[:32]}...",
        ])
        
        return "\n".join(lines)
    
    def _generate_id(self) -> str:
        """Generate unique decision ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        return hashlib.sha256(f"{timestamp}{len(self.explanations)}".encode()).hexdigest()[:12]
    
    def _hash_rationale(self, rationale: DecisionRationale) -> str:
        """Generate hash for rationale."""
        data = {
            "decision_id": rationale.decision_id,
            "decision_type": rationale.decision_type.value,
            "timestamp": rationale.timestamp,
            "doctrine_article": rationale.doctrine_article,
            "triggering_features": rationale.triggering_features,
            "prev_hash": self.prev_hash,
        }
        hash_str = json.dumps(data, sort_keys=True)
        new_hash = hashlib.sha256(hash_str.encode()).hexdigest()
        self.prev_hash = new_hash
        return new_hash


if __name__ == "__main__":
    # Test the module
    print("=" * 60)
    print("EXPLANATION LAYER — TEST SUITE")
    print("=" * 60)
    
    layer = ExplanationLayer()
    
    # Test content rejection explanation
    print("\n[Content Rejection]")
    rationale = layer.explain_content_rejection(
        content="test content",
        matched_pattern="anime",
        article="1.1",
        category="content_policy",
    )
    print(f"✓ Decision ID: {rationale.decision_id}")
    print(f"✓ Doctrine: {rationale.doctrine_article}")
    
    # Test language violation explanation
    print("\n[Language Violation]")
    rationale = layer.explain_language_violation(
        text="We can work together",
        violation_type="shared_agency",
        matched_phrase="we",
        article="2.1",
    )
    print(f"✓ Decision ID: {rationale.decision_id}")
    print(f"✓ Plain language: {rationale.plain_language[:80]}...")
    
    # Test data blocked explanation
    print("\n[Data Blocked]")
    rationale = layer.explain_data_blocked(
        data_type="biometric",
        article="10.2",
    )
    print(f"✓ Decision ID: {rationale.decision_id}")
    
    # Test metric blocked explanation
    print("\n[Metric Blocked]")
    rationale = layer.explain_metric_blocked(
        metric_name="session_length",
    )
    print(f"✓ Decision ID: {rationale.decision_id}")
    
    # Test boundary explanation
    print("\n[Boundary Set]")
    rationale = layer.explain_boundary_set(
        request_type="emotional_support",
        reason="This system is not designed to provide emotional support.",
    )
    print(f"✓ Decision ID: {rationale.decision_id}")
    
    # Test formatted output
    print("\n[Formatted Output]")
    formatted = layer.format_for_user(rationale)
    print(formatted)
    
    print("\n" + "=" * 60)
    print(f"EXPLANATION LAYER TESTS COMPLETE ({len(layer.explanations)} explanations generated)")
    print("=" * 60)

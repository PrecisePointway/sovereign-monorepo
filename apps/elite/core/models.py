"""
Sovereign Sanctuary Elite Pack - Core Data Models
Zero-Drift Deterministic Data Structures
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any
import json
import hashlib


class GrantStatus(Enum):
    """Grant pipeline status states"""
    RESEARCH = "Research"
    DRAFTING = "Drafting"
    REVIEW = "Review"
    SUBMITTED = "Submitted"
    AWARDED = "Awarded"
    REJECTED = "Rejected"


class DecisionState(Enum):
    """Urbanismo decision matrix states"""
    PENDING = "PENDING"
    GREEN = "GREEN"      # HQ Approved
    AMBER = "AMBER"      # Conditions Required
    RED = "RED"          # Rural Prohibited


class SueloClassification(Enum):
    """Spanish land classification types"""
    RUSTICO_COMUN = "rústico común"
    COMUN = "común"
    PROTEGIDO = "protegido"
    URBANO = "urbano"
    UNKNOWN = "unknown"


@dataclass
class PropertyData:
    """Property meeting extraction data model"""
    referencia_catastral: str = ""  # 14-digit code
    suelo_classification: SueloClassification = SueloClassification.UNKNOWN
    monthly_opex_eur: float = 0.0
    cedula_habitabilidad: bool = False
    permit_issues: List[str] = field(default_factory=list)
    house_a_m2: float = 0.0
    house_b_m2: float = 0.0
    total_area_m2: float = 5900.0
    extraction_timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "referencia_catastral": self.referencia_catastral,
            "suelo_classification": self.suelo_classification.value,
            "monthly_opex_eur": self.monthly_opex_eur,
            "cedula_habitabilidad": self.cedula_habitabilidad,
            "permit_issues": self.permit_issues,
            "house_a_m2": self.house_a_m2,
            "house_b_m2": self.house_b_m2,
            "total_area_m2": self.total_area_m2,
            "extraction_timestamp": self.extraction_timestamp.isoformat()
        }
    
    def integrity_hash(self) -> str:
        """Generate cryptographic hash for data integrity verification"""
        data_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    def validate(self) -> List[str]:
        """Validate property data completeness"""
        errors = []
        if len(self.referencia_catastral) != 14:
            errors.append(f"Invalid Referencia Catastral length: {len(self.referencia_catastral)}/14")
        if self.suelo_classification == SueloClassification.UNKNOWN:
            errors.append("Suelo classification not set")
        if self.monthly_opex_eur <= 0:
            errors.append("Monthly OpEx not set")
        return errors


@dataclass
class Grant:
    """Grant pipeline entry"""
    id: str
    name: str
    funder: str
    amount_eur: float
    deadline: date
    status: GrantStatus
    owner: str
    priority: int = 1
    narrative_template: str = ""
    submission_url: str = ""
    notes: List[str] = field(default_factory=list)
    
    @property
    def days_until_deadline(self) -> int:
        return (self.deadline - date.today()).days
    
    @property
    def is_urgent(self) -> bool:
        return self.days_until_deadline <= 7
    
    @property
    def is_critical(self) -> bool:
        return self.days_until_deadline <= 3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "funder": self.funder,
            "amount_eur": self.amount_eur,
            "deadline": self.deadline.isoformat(),
            "status": self.status.value,
            "owner": self.owner,
            "priority": self.priority,
            "days_until_deadline": self.days_until_deadline,
            "is_urgent": self.is_urgent,
            "is_critical": self.is_critical
        }


@dataclass
class RunwayWeek:
    """Weekly runway projection"""
    week_label: str
    week_start: date
    cash_in: float
    cash_out: float
    is_projected: bool = False
    
    @property
    def net(self) -> float:
        return self.cash_in - self.cash_out
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "week": self.week_label,
            "week_start": self.week_start.isoformat(),
            "cash_in": self.cash_in,
            "cash_out": self.cash_out,
            "net": self.net,
            "is_projected": self.is_projected
        }


@dataclass
class RunwayTracker:
    """Financial runway tracking"""
    starting_balance: float
    weeks: List[RunwayWeek] = field(default_factory=list)
    critical_threshold: float = 10000.0
    
    def calculate_cumulative(self) -> List[Dict[str, Any]]:
        """Calculate cumulative runway with projections"""
        cumulative = self.starting_balance
        results = []
        for week in self.weeks:
            cumulative += week.net
            results.append({
                **week.to_dict(),
                "cumulative": cumulative,
                "is_critical": cumulative < self.critical_threshold
            })
        return results
    
    @property
    def weeks_of_runway(self) -> int:
        """Calculate weeks until critical threshold"""
        cumulative = self.starting_balance
        for i, week in enumerate(self.weeks):
            cumulative += week.net
            if cumulative < self.critical_threshold:
                return i
        return len(self.weeks)
    
    @property
    def runway_status(self) -> str:
        weeks = self.weeks_of_runway
        if weeks <= 2:
            return "🔴 CRITICAL"
        elif weeks <= 4:
            return "🟡 WARNING"
        return "🟢 HEALTHY"


@dataclass
class UrbanismoSubmission:
    """Urbanismo consulta tracking"""
    registro_number: str = ""
    submission_date: Optional[date] = None
    referencia_catastral: str = ""
    status: DecisionState = DecisionState.PENDING
    response_date: Optional[date] = None
    conditions: List[str] = field(default_factory=list)
    documents_submitted: List[str] = field(default_factory=list)
    
    @property
    def days_since_submission(self) -> Optional[int]:
        if self.submission_date:
            return (date.today() - self.submission_date).days
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "registro_number": self.registro_number,
            "submission_date": self.submission_date.isoformat() if self.submission_date else None,
            "referencia_catastral": self.referencia_catastral,
            "status": self.status.value,
            "response_date": self.response_date.isoformat() if self.response_date else None,
            "conditions": self.conditions,
            "days_since_submission": self.days_since_submission
        }


@dataclass
class ExecutionCheckpoint:
    """48-hour execution checkpoint tracking"""
    checkpoint_id: str
    description: str
    completed: bool = False
    completion_timestamp: Optional[datetime] = None
    evidence_hash: str = ""
    
    def mark_complete(self, evidence: str = "") -> None:
        self.completed = True
        self.completion_timestamp = datetime.now()
        if evidence:
            self.evidence_hash = hashlib.sha256(evidence.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "description": self.description,
            "completed": self.completed,
            "completion_timestamp": self.completion_timestamp.isoformat() if self.completion_timestamp else None,
            "evidence_hash": self.evidence_hash
        }


@dataclass
class SanctuaryState:
    """Master state container for Sovereign Sanctuary operations"""
    property_data: PropertyData = field(default_factory=PropertyData)
    grants: List[Grant] = field(default_factory=list)
    runway: RunwayTracker = field(default_factory=lambda: RunwayTracker(starting_balance=37000))
    urbanismo: UrbanismoSubmission = field(default_factory=UrbanismoSubmission)
    checkpoints: List[ExecutionCheckpoint] = field(default_factory=list)
    decision_state: DecisionState = DecisionState.PENDING
    last_updated: datetime = field(default_factory=datetime.now)
    
    def state_hash(self) -> str:
        """Generate cryptographic hash of entire state for integrity verification"""
        state_dict = {
            "property": self.property_data.to_dict(),
            "grants": [g.to_dict() for g in self.grants],
            "runway": self.runway.calculate_cumulative(),
            "urbanismo": self.urbanismo.to_dict(),
            "checkpoints": [c.to_dict() for c in self.checkpoints],
            "decision_state": self.decision_state.value
        }
        return hashlib.sha256(json.dumps(state_dict, sort_keys=True).encode()).hexdigest()[:16]
    
    def to_json(self, indent: int = 2) -> str:
        """Export state to JSON"""
        return json.dumps({
            "property": self.property_data.to_dict(),
            "grants": [g.to_dict() for g in self.grants],
            "runway": self.runway.calculate_cumulative(),
            "urbanismo": self.urbanismo.to_dict(),
            "checkpoints": [c.to_dict() for c in self.checkpoints],
            "decision_state": self.decision_state.value,
            "last_updated": self.last_updated.isoformat(),
            "state_hash": self.state_hash()
        }, indent=indent)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SanctuaryState':
        """Load state from JSON"""
        data = json.loads(json_str)
        # Implementation for full deserialization
        state = cls()
        # ... populate from data
        return state


# Victory Condition Checkpoints
DEFAULT_CHECKPOINTS = [
    ExecutionCheckpoint("REF_CAT", "Referencia Catastral extracted (14 digits)"),
    ExecutionCheckpoint("SUELO", "Suelo classification confirmed"),
    ExecutionCheckpoint("OPEX", "Monthly OpEx number captured"),
    ExecutionCheckpoint("CEDULA", "Cédula habitabilidad status confirmed"),
    ExecutionCheckpoint("AIRTABLE", "Airtable base live with grants + runway"),
    ExecutionCheckpoint("URBANISMO", "Urbanismo consulta filed with registro #"),
]

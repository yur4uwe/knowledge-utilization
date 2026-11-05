"""Domain and audit data models for SE07: Ontology Pitfalls, OntoClean, and Situation Templates."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DefectCategory(str, Enum):
    """Four mandatory pitfall categories defined in criterion C2."""

    LOGICAL = "logical"
    NAMING = "naming"
    DOCUMENTATION = "documentation"
    ONTOCLEAN = "ontoclean"


class SeverityLevel(str, Enum):
    """Severity levels for ontology pitfalls."""

    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


@dataclass
class OntologyDefect:
    """Formal representation of an ontological defect / pitfall."""

    id: str
    category: DefectCategory
    severity: SeverityLevel
    entity_name: str
    title: str
    description: str
    remediation: str
    oops_code: Optional[str] = None
    status: str = "detected"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category.value,
            "severity": self.severity.value,
            "entity_name": self.entity_name,
            "title": self.title,
            "description": self.description,
            "remediation": self.remediation,
            "oops_code": self.oops_code,
            "status": self.status,
        }


@dataclass
class AuditReport:
    """Result of an ontology audit session."""

    ontology_path: str
    version: str
    total_classes: int
    total_properties: int
    total_axioms: int
    defects: List[OntologyDefect] = field(default_factory=list)
    is_dl_consistent: bool = True

    @property
    def defect_count(self) -> int:
        return len(self.defects)

    @property
    def category_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {cat.value: 0 for cat in DefectCategory}
        for d in self.defects:
            counts[d.category.value] += 1
        return counts


@dataclass
class SituationTemplate:
    """Situation pattern tuple: State -> Event -> Condition -> New State -> Action."""

    id: str
    title: str
    initial_state_class: str
    event_class: str
    condition_expr: str
    new_state_class: str
    action_class: str
    iec_cim_mapping: str
    operational_narrative: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "initial_state": self.initial_state_class,
            "event": self.event_class,
            "condition": self.condition_expr,
            "new_state": self.new_state_class,
            "action": self.action_class,
            "iec_cim": self.iec_cim_mapping,
            "narrative": self.operational_narrative,
        }

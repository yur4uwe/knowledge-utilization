"""Data models for Concept Map evaluation according to Novak & Canas (2008)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Concept:
    """Represents a node (concept) in a concept map."""
    id: str
    label: str
    level: int  # 0 is top-most general concept, increasing downwards
    category: str
    is_example: bool = False
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Proposition:
    """Represents a labeled, directed proposition (Subject - Predicate -> Object)."""
    source_id: str
    target_id: str
    predicate: str
    is_cross_link: bool = False
    is_valid: bool = True
    comment: str = ""


@dataclass
class ConceptMap:
    """Represents a full concept map graph."""
    id: str
    title: str
    domain: str
    focus_question: str
    concepts: Dict[str, Concept]
    propositions: List[Proposition]
    source_type: str  # 'own', 'llm', 'peer', 'llm_corrected'

    def get_max_level(self) -> int:
        """Calculate maximum hierarchical depth in the map."""
        if not self.concepts:
            return 0
        return max(c.level for c in self.concepts.values())

    def get_cross_links_count(self) -> int:
        """Count valid cross-links."""
        return sum(1 for p in self.propositions if p.is_cross_link and p.is_valid)

    def get_valid_propositions_count(self) -> int:
        """Count valid, meaningful propositions."""
        return sum(1 for p in self.propositions if p.is_valid)

    def get_examples_count(self) -> int:
        """Count leaf/example concepts."""
        return sum(1 for c in self.concepts.values() if c.is_example)


@dataclass
class RubricScore:
    """Scoring along 5 normalized dimensions (0-10 scale)."""
    propositions: float  # Validity, semantic precision, absence of vague 'related-to'
    hierarchy: float     # Subsumption depth, generality-to-specificity ordering
    cross_links: float   # Integrative reconciliation between distinct branches
    examples: float      # Terminal concrete instances illustrating concepts
    focus_question: float # Degree to which the map directly answers the focus question

    @property
    def total(self) -> float:
        """Total composite score (0-50)."""
        return (
            self.propositions
            + self.hierarchy
            + self.cross_links
            + self.examples
            + self.focus_question
        )

    @property
    def mean(self) -> float:
        """Normalized average score (0-10)."""
        return self.total / 5.0

    def as_dict(self) -> Dict[str, float]:
        return {
            "propositions": self.propositions,
            "hierarchy": self.hierarchy,
            "cross_links": self.cross_links,
            "examples": self.examples,
            "focus_question": self.focus_question,
            "mean": round(self.mean, 2),
            "total": round(self.total, 2),
        }


@dataclass
class NovakCountMetrics:
    """Classic Novak & Gowin (1984) scoring formula metrics.

    Formula: Points = (Valid Propositions * 1) + (Hierarchy Levels * 5)
                      + (Cross-links * 10) + (Examples * 1)
    """
    valid_propositions: int
    hierarchy_levels: int
    cross_links: int
    examples: int

    @property
    def total_novak_points(self) -> int:
        return (
            (self.valid_propositions * 1)
            + (self.hierarchy_levels * 5)
            + (self.cross_links * 10)
            + (self.examples * 1)
        )

    def as_dict(self) -> Dict[str, int]:
        return {
            "valid_propositions": self.valid_propositions,
            "hierarchy_levels": self.hierarchy_levels,
            "cross_links": self.cross_links,
            "examples": self.examples,
            "total_novak_points": self.total_novak_points,
        }


@dataclass
class EvaluationRecord:
    """Comprehensive evaluation record for one map evaluated by one evaluator."""
    map_id: str
    map_title: str
    evaluator_name: str
    evaluator_role: str
    rubric: RubricScore
    novak_counts: NovakCountMetrics
    notes: str = ""


@dataclass
class InterRaterAgreement:
    """Statistical inter-rater agreement metrics between two evaluators for a map."""
    map_id: str
    evaluator_1: str
    evaluator_2: str
    criterion_diffs: Dict[str, float]  # criterion -> abs(score1 - score2)
    mae: float                         # Mean Absolute Error across criteria
    pearson_r: float                   # Pearson correlation coefficient
    spearman_rho: float                # Spearman rank correlation
    max_diff_criterion: str            # Criterion with highest divergence
    max_diff_value: float              # Max difference value
    max_diff_explanation: str          # Qualitative explanation for divergence


@dataclass
class CorrectionRecord:
    """Correction of an LLM map defect."""
    error_id: str
    original_source: str
    original_predicate: str
    original_target: str
    defect_type: str
    corrected_source: str
    corrected_predicate: str
    corrected_target: str
    rationale: str


@dataclass
class DefectPattern:
    """Catalog entry for typical LLM concept-mapping errors."""
    defect_id: str
    name: str
    category: str
    description: str
    manifestation: str
    impact: str
    detection_rule: str
    remediation: str

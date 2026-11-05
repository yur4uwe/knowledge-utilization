"""Automated pytest test suite for SE07: Ontology Pitfall Audit, OntoClean, and Situation Templates."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from src.se07.analyzer import OntologyAnalyzer
from src.se07.main import CORRECTED_ONTOLOGY, RAW_ONTOLOGY, run_pipeline
from src.se07.models import DefectCategory
from src.se07.situations import SITUATION_TEMPLATES, validate_situation_bindings


@pytest.fixture(scope="module")
def raw_audit():
    analyzer = OntologyAnalyzer(RAW_ONTOLOGY)
    return analyzer.run_full_audit()


@pytest.fixture(scope="module")
def corr_audit():
    analyzer = OntologyAnalyzer(CORRECTED_ONTOLOGY)
    return analyzer.run_full_audit()


@pytest.fixture(scope="module")
def corr_analyzer():
    return OntologyAnalyzer(CORRECTED_ONTOLOGY)


def test_c1_ontology_size_and_minimum_defects(raw_audit):
    """Verify Criterion C1: Analyzed ontology has >= 50 classes and >= 5 defects found."""
    assert raw_audit.total_classes >= 50, (
        f"Raw ontology must have >= 50 named classes, found {raw_audit.total_classes}"
    )
    assert raw_audit.defect_count >= 5, (
        f"Must identify >= 5 defects in the ontology, found {raw_audit.defect_count}"
    )


def test_c2_defects_categorization(raw_audit):
    """Verify Criterion C2: Defects are classified across all 4 mandatory categories."""
    categories_found = {d.category for d in raw_audit.defects}

    required_categories = {
        DefectCategory.LOGICAL,
        DefectCategory.NAMING,
        DefectCategory.DOCUMENTATION,
        DefectCategory.ONTOCLEAN,
    }

    assert required_categories.issubset(categories_found), (
        f"Missing categories: {required_categories - categories_found}"
    )

    # Check presence of specific core defects
    defect_ids = {d.id for d in raw_audit.defects}
    assert any("LOG-DISJ" in did for did in defect_ids), "Missing disjoint subsumption logical defect"
    assert any("LOG-CYCLE" in did for did in defect_ids), "Missing cycle logical defect"
    assert any("NAM-SNAKE" in did for did in defect_ids), "Missing naming style defect"
    assert any("ONT-RIGID" in did for did in defect_ids), "Missing OntoClean rigidity defect"


def test_c3_remediation_delta_and_reasoner_effect(raw_audit, corr_audit):
    """Verify Criterion C3: Remediation fixes >= 3 defects with proven effect on consistency."""
    resolved_count = raw_audit.defect_count - corr_audit.defect_count
    assert resolved_count >= 3, f"Expected >= 3 defects resolved, got {resolved_count}"

    # Verify DL consistency before and after
    assert raw_audit.is_dl_consistent is False, "Raw ontology should be marked inconsistent"
    assert corr_audit.is_dl_consistent is True, "Corrected ontology must be marked consistent"

    # Verify no critical logical or OntoClean defects remain
    assert corr_audit.category_counts["logical"] == 0
    assert corr_audit.category_counts["ontoclean"] == 0
    assert corr_audit.category_counts["naming"] == 0


def test_c4_situation_templates_bound_to_classes(corr_analyzer):
    """Verify Criterion C4: Exactly 5 situation templates are defined and strictly bound to classes."""
    assert len(SITUATION_TEMPLATES) == 5, f"Expected 5 situation templates, got {len(SITUATION_TEMPLATES)}"

    validation_results = validate_situation_bindings(corr_analyzer)
    for sid, ok, msg in validation_results:
        assert ok is True, f"Situation {sid} failed binding validation: {msg}"


def test_pipeline_execution():
    """Verify end-to-end pipeline execution and diagram generation."""
    res = run_pipeline()
    assert "raw_report" in res
    assert "corr_report" in res
    assert "seeded_catalog" in res
    assert len(res["seeded_catalog"]) >= 5
    assert "mermaid_chart" in res
    assert "flowchart LR" in res["mermaid_chart"]

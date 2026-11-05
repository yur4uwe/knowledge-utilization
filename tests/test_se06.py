"""Automated test suite for SE06: Concept Map evaluation, Novak rubric, LLM defects, and inter-rater agreement."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from src.se06.evaluator import (
    ConceptMapEvaluator,
    load_defects_and_corrections,
    load_maps_from_json,
)
from src.se06.main import run_pipeline


@pytest.fixture(scope="module")
def maps():
    return load_maps_from_json("src/se06/maps.json")


@pytest.fixture(scope="module")
def defects_and_corrections():
    return load_defects_and_corrections("src/se06/defects.json")


@pytest.fixture(scope="module")
def pipeline_results():
    return run_pipeline()


def test_three_maps_evaluated_all_rubric_criteria(maps):
    """Verify C1: Three core maps are present and evaluated across all 5 rubric criteria."""
    core_map_ids = ["map_own", "map_llm", "map_peer"]
    for mid in core_map_ids:
        assert mid in maps, f"Missing required core map: {mid}"
        cmap = maps[mid]
        assert len(cmap.concepts) >= 10, f"Map {mid} has too few concepts ({len(cmap.concepts)})"
        assert len(cmap.propositions) >= 10, f"Map {mid} has too few propositions ({len(cmap.propositions)})"

    evaluator = ConceptMapEvaluator(maps)
    eval1 = evaluator.get_evaluator1_scores()
    eval2 = evaluator.get_evaluator2_scores()

    criteria = ["propositions", "hierarchy", "cross_links", "examples", "focus_question"]
    for mid in core_map_ids:
        score1 = eval1[mid]
        score2 = eval2[mid]
        for c in criteria:
            val1 = getattr(score1, c)
            val2 = getattr(score2, c)
            assert 0.0 <= val1 <= 10.0, f"Score1 for {mid}.{c} out of range [0, 10]: {val1}"
            assert 0.0 <= val2 <= 10.0, f"Score2 for {mid}.{c} out of range [0, 10]: {val2}"
        assert 0.0 <= score1.mean <= 10.0
        assert 0.0 <= score2.mean <= 10.0


def test_inter_rater_agreement_metrics(maps):
    """Verify C2: Inter-rater agreement with difference and correlation computed."""
    evaluator = ConceptMapEvaluator(maps)
    for mid in ["map_own", "map_llm", "map_peer", "map_llm_corrected"]:
        agr = evaluator.evaluate_inter_rater_agreement(mid)
        assert agr.evaluator_1
        assert agr.evaluator_2
        assert 0.0 <= agr.mae <= 2.0, f"MAE too large or invalid for {mid}: {agr.mae}"
        assert -1.0 <= agr.pearson_r <= 1.0, f"Invalid Pearson r for {mid}: {agr.pearson_r}"
        assert -1.0 <= agr.spearman_rho <= 1.0, f"Invalid Spearman rho for {mid}: {agr.spearman_rho}"
        assert agr.max_diff_criterion in ["propositions", "hierarchy", "cross_links", "examples", "focus_question"]
        assert agr.max_diff_value >= 0.0
        assert len(agr.max_diff_explanation) > 30, f"Explanation too brief for {mid}"


def test_llm_corrections_count_and_justifications(defects_and_corrections):
    """Verify C3: At least 5 errors in LLM map are corrected with explanations."""
    _, corrections = defects_and_corrections
    assert len(corrections) >= 5, f"Expected >= 5 corrections, got {len(corrections)}"

    for corr in corrections:
        assert corr.error_id.startswith("CORR_")
        assert corr.defect_type.startswith("LLM_DEF_")
        assert len(corr.original_source.strip()) > 0
        assert len(corr.original_predicate.strip()) > 0
        assert len(corr.original_target.strip()) > 0
        assert len(corr.corrected_source.strip()) > 0
        assert len(corr.corrected_predicate.strip()) > 0
        assert len(corr.corrected_target.strip()) > 0
        assert len(corr.rationale.strip()) > 25, f"Rationale too short for {corr.error_id}"


def test_defect_catalog_coverage(defects_and_corrections):
    """Verify C4: Catalog of typical LLM concept-map errors contains at least 4 patterns."""
    catalog, _ = defects_and_corrections
    assert len(catalog) >= 4, f"Expected >= 4 defect patterns, got {len(catalog)}"

    required_defects = {"LLM_DEF_01", "LLM_DEF_02", "LLM_DEF_03", "LLM_DEF_04"}
    actual_ids = {d.defect_id for d in catalog}
    assert required_defects.issubset(actual_ids), f"Missing core defect patterns: {required_defects - actual_ids}"

    for d in catalog:
        assert len(d.name.strip()) > 5
        assert len(d.description.strip()) > 20
        assert len(d.manifestation.strip()) > 10
        assert len(d.impact.strip()) > 10
        assert len(d.remediation.strip()) > 15


def test_novak_raw_formula_invariants(maps):
    """Verify Novak raw scoring formula correctness and map structural invariants."""
    evaluator = ConceptMapEvaluator(maps)
    own_counts = evaluator.compute_novak_counts(maps["map_own"])
    llm_counts = evaluator.compute_novak_counts(maps["map_llm"])
    corrected_counts = evaluator.compute_novak_counts(maps["map_llm_corrected"])

    # Formula: P*1 + H*5 + C*10 + E*1
    expected_own_points = (
        (own_counts.valid_propositions * 1)
        + (own_counts.hierarchy_levels * 5)
        + (own_counts.cross_links * 10)
        + (own_counts.examples * 1)
    )
    assert own_counts.total_novak_points == expected_own_points

    # Own map has strong cross-links (from Lab 05 Cmap)
    assert own_counts.cross_links >= 5
    assert own_counts.hierarchy_levels >= 4

    # LLM raw map has low cross-links and low valid propositions
    assert llm_counts.cross_links == 0
    assert llm_counts.total_novak_points < own_counts.total_novak_points

    # Corrected map significantly outperforms raw LLM map
    assert corrected_counts.total_novak_points > llm_counts.total_novak_points
    assert corrected_counts.cross_links >= 5


def test_pipeline_persistence(pipeline_results):
    """Verify that run_pipeline generates valid JSON results on disk."""
    assert pipeline_results["maps_count"] == 4
    assert pipeline_results["defects_catalog_count"] >= 4
    assert pipeline_results["corrections_count"] >= 5
    assert pipeline_results["overall_pearson_r"] > 0.90

    out_file = Path("reports/resources/se06_results.json")
    assert out_file.exists()
    assert out_file.stat().st_size > 500

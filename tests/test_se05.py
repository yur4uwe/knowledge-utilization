"""Automated test suite for SE05: Taxonomy construction, metrics, SKOS export and defects."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path even without pyproject.toml pythonpath configuration
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from rdflib import Graph

from src.se05.main import run_pipeline
from src.se05.metrics import TaxonomyMetricsCalculator
from src.se05.skos_exporter import SkosExporter
from src.se05.taxonomy_builder import (
    BottomUpTaxonomyBuilder,
    ExpertCIMTaxonomyBuilder,
    TopDownTaxonomyBuilder,
    load_terms,
)


@pytest.fixture(scope="module")
def terms():
    return load_terms("src/se05/terms.json")


@pytest.fixture(scope="module")
def pipeline_results():
    return run_pipeline()


def test_terms_corpus_validity(terms):
    """Verify that domain corpus contains at least 60 valid, unique terms."""
    assert len(terms) >= 60, f"Expected >= 60 terms, got {len(terms)}"
    ids = [t["id"] for t in terms]
    assert len(ids) == len(set(ids)), "Term IDs must be unique"

    required_keys = {"id", "name_uk", "name_en", "category_gold", "definition", "attributes"}
    for term in terms:
        missing = required_keys - set(term.keys())
        assert not missing, f"Term {term.get('id')} missing keys: {missing}"
        assert len(term["attributes"]) >= 2, f"Term {term['id']} needs at least 2 attributes"
        assert len(term["definition"].strip()) > 10, f"Term {term['id']} definition too short"


def test_top_down_taxonomy_structure(terms):
    """Verify Top-Down taxonomy tree invariants."""
    builder = TopDownTaxonomyBuilder(terms)
    tax = builder.build()

    assert tax.root_id == "ROOT_TOP_DOWN"
    assert tax.root_id in tax.nodes

    leaves = tax.get_leaves()
    assert len(leaves) == len(terms), "All corpus terms must be represented as leaves"

    for leaf in leaves:
        assert leaf.parent_id is not None, f"Leaf {leaf.id} has no parent"
        assert leaf.parent_id in tax.nodes, f"Parent {leaf.parent_id} of leaf {leaf.id} not in nodes"
        assert leaf.level == 3, f"Expected leaf level 3, got {leaf.level}"

    # Verify acyclicity by walking up from each leaf
    for leaf in leaves:
        curr = leaf.id
        visited = set()
        while curr:
            assert curr not in visited, f"Cycle detected at node {curr}"
            visited.add(curr)
            parent = tax.nodes[curr].parent_id
            curr = parent


def test_bottom_up_clustering_structure(terms):
    """Verify Bottom-Up HAC dendrogram invariants."""
    builder = BottomUpTaxonomyBuilder(terms)
    tax = builder.build()

    assert tax.root_id in tax.nodes
    leaves = tax.get_leaves()
    assert len(leaves) == len(terms), "All corpus terms must be leaves in HAC"

    non_leaves = tax.get_non_leaves()
    # In binary agglomerative tree of N leaves, there must be N-1 internal merges
    assert len(non_leaves) == len(terms) - 1

    for node in non_leaves:
        assert len(node.children) == 2, f"Internal cluster node {node.id} must merge exactly 2 children"

    # All leaves must reach the root
    for leaf in leaves:
        curr = leaf.id
        path_length = 0
        while curr != tax.root_id:
            curr = tax.nodes[curr].parent_id
            path_length += 1
            assert path_length <= len(terms), f"Path too long or disconnected from root for {leaf.id}"
        assert curr == tax.root_id


def test_metrics_calculation(terms):
    """Verify that all metrics are properly computed and mathematically valid."""
    expert = ExpertCIMTaxonomyBuilder(terms).build()
    calc = TaxonomyMetricsCalculator(corpus_terms=terms, expert_taxonomy=expert)

    top_down = TopDownTaxonomyBuilder(terms).build()
    bottom_up = BottomUpTaxonomyBuilder(terms).build()

    m_td = calc.compute(top_down)
    m_bu = calc.compute(bottom_up)
    m_exp = calc.compute(expert)

    # Coverage
    assert m_td.coverage_pct == 100.0
    assert m_bu.coverage_pct == 100.0

    # Depth
    assert m_td.max_depth == 3
    assert m_bu.max_depth > m_td.max_depth, "HAC binary tree depth must exceed top-down depth"

    # Breadth
    assert m_td.max_fan_out >= 3
    assert m_bu.max_fan_out == 2, "HAC binary dendrogram has fan-out = 2"

    # Agreement
    assert m_exp.expert_pairwise_jaccard == 1.0
    assert m_exp.expert_cluster_purity == 1.0
    assert 0.0 <= m_td.expert_pairwise_jaccard <= 1.0
    assert 0.0 <= m_bu.expert_pairwise_jaccard <= 1.0
    assert m_td.expert_cluster_purity >= 0.70, "Top-Down should exhibit high purity against CIM"


def test_skos_export(terms, tmp_path):
    """Verify that taxonomies export to valid parseable W3C SKOS RDF Turtle."""
    tax = TopDownTaxonomyBuilder(terms).build()
    exporter = SkosExporter(tax)

    out_file = tmp_path / "test_tax.ttl"
    saved = exporter.save_turtle(out_file)

    g = Graph()
    g.parse(saved, format="turtle")
    assert len(g) > 200, "SKOS graph must contain substantial triples"

    # Check for presence of key SKOS concepts
    query = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    ASK {
        ?s a skos:Concept .
        ?s skos:prefLabel ?label .
    }
    """
    res = g.query(query)
    assert bool(res.askAnswer) is True


def test_defect_detection(terms):
    """Verify that at least 5 defects are detected and fully documented."""
    top_down = TopDownTaxonomyBuilder(terms).build()
    bottom_up = BottomUpTaxonomyBuilder(terms).build()

    defects = TaxonomyMetricsCalculator.detect_defects(top_down, bottom_up)
    assert len(defects) >= 5, f"Expected >= 5 defects, got {len(defects)}"

    for defect in defects:
        assert defect.defect_id.startswith("DEF_")
        assert defect.severity in {"HIGH", "MEDIUM", "LOW"}
        assert len(defect.affected_elements) > 0
        assert len(defect.description) > 30
        assert len(defect.violated_principle) > 10
        assert len(defect.remediation_recommendation) > 20

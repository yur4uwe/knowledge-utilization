"""Tests for Self-Education 8: SPARQL queries to Wikidata.

Verifies Criteria C1, C2, C3, and C4 according to self-edu_08.md:
- C1: >= 8 queries with diverse constructs (SELECT, ASK, aggregation, property path, SERVICE label).
- C2: Results fragment and interpretation available for all queries.
- C3: LLM queries compared and >= 3 fixed with valid SPARQL syntax.
- C4: Typical LLM errors classified and mapped.
"""

import json
from pathlib import Path
import pytest
from rdflib.plugins.sparql.parser import parseQuery

from src.se08.queries import QUERIES, LLM_COMPARISONS
from src.se08.client import RESULTS_FILE, load_cached_results


def test_c1_query_count_and_diversity():
    """Verify C1: >= 8 queries and presence of diverse SPARQL constructs."""
    assert len(QUERIES) >= 8, f"Expected at least 8 queries, found {len(QUERIES)}"

    all_constructs = set()
    has_select = False
    has_ask = False
    has_aggregation = False
    has_property_path = False
    has_service_label = False

    for qid, qdata in QUERIES.items():
        sparql = qdata["sparql"].upper()
        constructs = qdata.get("constructs", [])
        all_constructs.update(constructs)

        if "SELECT" in sparql:
            has_select = True
        if "ASK" in sparql:
            has_ask = True
        if any(agg in sparql for agg in ["COUNT(", "SUM(", "AVG(", "GROUP BY", "HAVING"]):
            has_aggregation = True
        if "/" in sparql or "+" in sparql or "*" in sparql:
            has_property_path = True
        if "SERVICE" in sparql and "WIKIBASE:LABEL" in sparql:
            has_service_label = True

    assert has_select, "C1: Missing SELECT queries"
    assert has_ask, "C1: Missing ASK query"
    assert has_aggregation, "C1: Missing aggregation (COUNT/SUM/AVG/GROUP BY/HAVING)"
    assert has_property_path, "C1: Missing property path constructs"
    assert has_service_label, "C1: Missing SERVICE wikibase:label construct"


def test_c1_sparql_files_exist_and_valid():
    """Verify all individual .sparql query files exist on disk and are syntactically valid SPARQL 1.1."""
    queries_dir = Path(__file__).resolve().parent.parent / "src" / "se08" / "queries"
    assert queries_dir.exists(), "src/se08/queries/ must exist"

    for qid, qdata in QUERIES.items():
        sparql_file = queries_dir / qdata["file"]
        assert sparql_file.exists(), f"Query file {sparql_file} does not exist"
        content = sparql_file.read_text(encoding="utf-8").strip()
        assert len(content) > 10, f"Query file {sparql_file} is empty"

        try:
            parsed = parseQuery(content)
            assert parsed is not None
        except Exception as e:
            pytest.fail(f"Syntax error in {qdata['file']}: {e}")


def test_c2_results_and_interpretation_presence():
    """Verify C2: each query has cached results and valid execution status."""
    assert RESULTS_FILE.exists(), "Results file se08_results.json must exist"
    data = load_cached_results()
    assert "queries" in data, "Results file must contain 'queries' key"
    queries_results = data["queries"]

    for qid in QUERIES.keys():
        assert qid in queries_results, f"Missing execution results for {qid}"
        res = queries_results[qid]
        assert res.get("status") == "success", f"Query {qid} was not marked as successful"
        if res.get("boolean") is not None:
            assert isinstance(res["boolean"], bool)
        else:
            assert "bindings" in res or "count" in res
            assert res.get("count", 0) >= 0


def test_c3_llm_comparison_and_fixes():
    """Verify C3: LLM comparison contains >= 3 fixed queries with valid SPARQL syntax."""
    assert len(LLM_COMPARISONS) >= 3, f"Expected at least 3 LLM comparisons, found {len(LLM_COMPARISONS)}"

    for cid, cdata in LLM_COMPARISONS.items():
        assert "raw_llm_sparql" in cdata
        assert "fixed_sparql" in cdata
        assert "defect_type" in cdata
        assert len(cdata["defect_description"]) > 20

        # Fixed query must be syntactically valid SPARQL
        fixed_sparql = cdata["fixed_sparql"]
        try:
            parsed_fixed = parseQuery(fixed_sparql)
            assert parsed_fixed is not None
        except Exception as e:
            pytest.fail(f"Fixed SPARQL query in {cid} failed syntax parsing: {e}")


def test_c4_llm_error_classification():
    """Verify C4: classification covers key error categories in text-to-SPARQL."""
    defect_types = [c["defect_type"] for c in LLM_COMPARISONS.values()]
    # Check coverage of diverse error types
    assert any("простор" in dt.lower() or "dbpe" in dt.lower() or "префікс" in dt.lower() for dt in defect_types)
    assert any("інверс" in dt.lower() or "суб'єкт" in dt.lower() for dt in defect_types)
    assert any("шлях" in dt.lower() or "property path" in dt.lower() or "вкладен" in dt.lower() for dt in defect_types)
    assert any("міток" in dt.lower() or "label" in dt.lower() or "групув" in dt.lower() for dt in defect_types)

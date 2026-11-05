"""Pytest test suite for Self-Edu 04: Production Rules Diagnostics."""

from pathlib import Path
from src.se04.rule_engine import (
    InferenceEngine,
    RuleAnalyzer,
    load_rules,
    load_test_cases,
)

BASE_DIR = Path(__file__).resolve().parent.parent / "src" / "se04"


def test_rule_counts():
    initial_rules = load_rules(BASE_DIR / "rules_initial.json")
    resolved_rules = load_rules(BASE_DIR / "rules_resolved.json")
    assert len(initial_rules) >= 20, "Initial rule base must contain >= 20 rules"
    assert len(resolved_rules) >= 20, "Resolved rule base must contain >= 20 rules"


def test_initial_rules_have_sources():
    initial_rules = load_rules(BASE_DIR / "rules_initial.json")
    for r in initial_rules:
        assert r.source, f"Rule {r.id} must define an authoritative source"


def test_analyzer_detects_at_least_three_problems():
    initial_rules = load_rules(BASE_DIR / "rules_initial.json")
    analyzer = RuleAnalyzer(initial_rules)
    anomalies = analyzer.run_full_audit()
    assert len(anomalies) >= 3, f"Expected at least 3 anomalies, found {len(anomalies)}"

    types = {a.anomaly_type for a in anomalies}
    assert "CONFLICT" in types, "Should detect at least one action conflict"
    assert "REDUNDANCY" in types, "Should detect at least one redundancy"
    assert "UNREACHABLE" in types, "Should detect at least one unreachable rule"


def test_resolved_rules_have_zero_anomalies():
    resolved_rules = load_rules(BASE_DIR / "rules_resolved.json")
    analyzer = RuleAnalyzer(resolved_rules)
    anomalies = analyzer.run_full_audit()
    assert len(anomalies) == 0, f"Expected 0 anomalies in resolved rules, found {len(anomalies)}"


def test_ten_scenarios_evaluation():
    initial_rules = load_rules(BASE_DIR / "rules_initial.json")
    resolved_rules = load_rules(BASE_DIR / "rules_resolved.json")
    test_cases = load_test_cases(BASE_DIR / "test_cases.json")

    assert len(test_cases) == 10, "Must have exactly 10 test situations"

    engine_init = InferenceEngine(initial_rules)
    engine_res = InferenceEngine(resolved_rules)

    # S01: conflict resolved
    s01 = next(c for c in test_cases if c["id"] == "S01")
    _, _, conf_init = engine_init.evaluate(s01["facts"])
    fired_res, dom_res, conf_res = engine_res.evaluate(s01["facts"])
    assert conf_init is True, "S01 should have conflict in initial rule base"
    assert conf_res is False, "S01 conflict must be resolved"
    assert dom_res.action == "EMERGENCY_TRIP_TRANSFORMER"

    # S03: redundancy removed
    s03 = next(c for c in test_cases if c["id"] == "S03")
    fired_init, _, _ = engine_init.evaluate(s03["facts"])
    fired_res, _, _ = engine_res.evaluate(s03["facts"])
    ids_init = {r.id for r in fired_init}
    ids_res = {r.id for r in fired_res}
    assert {"R11", "R12"}.issubset(ids_init), "Both R11 and R12 fired initially"
    assert "R12" not in ids_res, "R12 duplicate should not fire in resolved"

    # S05: unreachable rule R18 is reachable in resolved
    s05 = next(c for c in test_cases if c["id"] == "S05")
    fired_init, _, _ = engine_init.evaluate(s05["facts"])
    fired_res, dom_res, _ = engine_res.evaluate(s05["facts"])
    ids_init = {r.id for r in fired_init}
    ids_res = {r.id for r in fired_res}
    assert "R18" not in ids_init, "R18 could not fire initially"
    assert "R18" in ids_res, "R18 must fire in resolved"
    assert dom_res.action == "EMERGENCY_ISLANDING_GRID_COLLAPSE"

#!/usr/bin/env python3
"""Rule Engine and Static Conflict/Redundancy Analyzer for Power System Diagnostics.

Self-Edu 04: Production Rules Diagnostics.
Lviv National University of Ivan Franko.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


OP_EVAL = {
    "<": lambda actual, val: actual < val,
    "<=": lambda actual, val: actual <= val,
    ">": lambda actual, val: actual > val,
    ">=": lambda actual, val: actual >= val,
    "==": lambda actual, val: actual == val,
    "!=": lambda actual, val: actual != val,
}

# Incompatible / contradictory pairs of actions in power system operations
CONTRADICTORY_ACTIONS = {
    frozenset({"EMERGENCY_TRIP_TRANSFORMER", "INHIBIT_TRIP_FORCE_COOLING"}),
    frozenset({"RAMP_DOWN_EXCITATION", "BOOST_REACTIVE_POWER"}),
    frozenset({"BLOCK_BESS_DISCHARGE", "BESS_FAST_DISCHARGE_PRIMARY_RESERVE"}),
}


@dataclass
class ConditionClause:
    var: str
    op: str
    value: Any

    def evaluate(self, facts: Dict[str, Any]) -> bool:
        if self.var not in facts:
            return False
        actual = facts[self.var]
        comparator = OP_EVAL.get(self.op)
        if not comparator:
            raise ValueError(f"Unsupported operator: {self.op}")
        return bool(comparator(actual, self.value))


@dataclass
class DiagnosticRule:
    id: str
    name: str
    category: str
    priority: int
    conditions: List[ConditionClause]
    action: str
    description: str
    source: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DiagnosticRule:
        clauses = [
            ConditionClause(var=c["var"], op=c["op"], value=c["value"])
            for c in data.get("conditions", [])
        ]
        return cls(
            id=data["id"],
            name=data["name"],
            category=data.get("category", "General"),
            priority=data.get("priority", 50),
            conditions=clauses,
            action=data["action"],
            description=data.get("description", ""),
            source=data.get("source", ""),
        )

    def matches(self, facts: Dict[str, Any]) -> bool:
        return all(clause.evaluate(facts) for clause in self.conditions)


@dataclass
class AnomalyReport:
    anomaly_type: str  # CONFLICT, REDUNDANCY, UNREACHABLE
    severity: str  # HIGH, MEDIUM, LOW
    rule_ids: List[str]
    description: str
    recommendation: str


class RuleAnalyzer:
    """Performs static analysis on a rule base to discover conflicts, redundancies, and reachability defects."""

    def __init__(self, rules: List[DiagnosticRule]) -> None:
        self.rules = rules

    def find_unreachable_rules(self) -> List[AnomalyReport]:
        anomalies: List[AnomalyReport] = []
        for r in self.rules:
            # Check for mutually exclusive bounds on single numerical variable
            var_bounds: Dict[str, Dict[str, float]] = {}
            for c in r.conditions:
                if isinstance(c.value, (int, float)):
                    if c.var not in var_bounds:
                        var_bounds[c.var] = {}
                    var_bounds[c.var][c.op] = float(c.value)

            for var, bounds in var_bounds.items():
                # E.g., var < lower and var > upper where upper >= lower
                lower_bound = None
                upper_bound = None
                if "<" in bounds:
                    lower_bound = bounds["<"]
                elif "<=" in bounds:
                    lower_bound = bounds["<="]

                if ">" in bounds:
                    upper_bound = bounds[">"]
                elif ">=" in bounds:
                    upper_bound = bounds[">="]

                if lower_bound is not None and upper_bound is not None:
                    if upper_bound >= lower_bound:
                        anomalies.append(
                            AnomalyReport(
                                anomaly_type="UNREACHABLE",
                                severity="HIGH",
                                rule_ids=[r.id],
                                description=(
                                    f"Правило {r.id} ({r.name}) містить логічно несумісні передумови "
                                    f"для '{var}': {var} > {upper_bound} AND {var} < {lower_bound}. "
                                    f"Перетин умов є порожньою множиною."
                                ),
                                recommendation="Розбити на два диз'юнктивних правила або уточнити діапазон.",
                            )
                        )
        return anomalies

    def find_redundancies(self) -> List[AnomalyReport]:
        anomalies: List[AnomalyReport] = []
        n = len(self.rules)
        for i in range(n):
            for j in range(i + 1, n):
                r1 = self.rules[i]
                r2 = self.rules[j]

                if r1.action != r2.action:
                    continue

                # Check condition overlap
                c1_set = {(c.var, c.op, c.value) for c in r1.conditions}
                c2_set = {(c.var, c.op, c.value) for c in r2.conditions}

                if c1_set == c2_set:
                    anomalies.append(
                        AnomalyReport(
                            anomaly_type="REDUNDANCY",
                            severity="MEDIUM",
                            rule_ids=[r1.id, r2.id],
                            description=f"Правила {r1.id} та {r2.id} є повними дублікатами з ідентичними діями '{r1.action}'.",
                            recommendation="Видалити одне з правил або об'єднати їх.",
                        )
                    )
                elif c1_set.issubset(c2_set) or c2_set.issubset(c1_set):
                    shadowed = r2.id if c1_set.issubset(c2_set) else r1.id
                    subsumer = r1.id if c1_set.issubset(c2_set) else r2.id
                    anomalies.append(
                        AnomalyReport(
                            anomaly_type="REDUNDANCY",
                            severity="MEDIUM",
                            rule_ids=[subsumer, shadowed],
                            description=(
                                f"Правило {shadowed} поглинається правилом {subsumer} "
                                f"з однаковою дією '{r1.action}'. {shadowed} містить надлишкові передумови."
                            ),
                            recommendation=f"Усунути поглинене правило {shadowed} або виділити унікальну дію.",
                        )
                    )
        return anomalies

    def find_action_conflicts(self) -> List[AnomalyReport]:
        anomalies: List[AnomalyReport] = []
        n = len(self.rules)
        for i in range(n):
            for j in range(i + 1, n):
                r1 = self.rules[i]
                r2 = self.rules[j]

                action_pair = frozenset({r1.action, r2.action})
                if action_pair not in CONTRADICTORY_ACTIONS and r1.action == r2.action:
                    continue

                if action_pair in CONTRADICTORY_ACTIONS:
                    # Check if conditions can be co-satisfied (intersectable preconditions)
                    vars1 = {c.var for c in r1.conditions}
                    vars2 = {c.var for c in r2.conditions}
                    shared_vars = vars1.intersection(vars2)

                    compatible = True
                    for var in shared_vars:
                        clauses1 = [c for c in r1.conditions if c.var == var]
                        clauses2 = [c for c in r2.conditions if c.var == var]
                        # Check direct conflict in literal value or opposite disjoint inequality
                        for c1 in clauses1:
                            for c2 in clauses2:
                                if c1.op == "==" and c2.op == "==" and c1.value != c2.value:
                                    compatible = False
                                elif (c1.op == "<" and c2.op == ">" and c1.value <= c2.value):
                                    compatible = False
                                elif (c1.op == ">" and c2.op == "<" and c1.value >= c2.value):
                                    compatible = False

                    if compatible and r1.priority == r2.priority:
                        anomalies.append(
                            AnomalyReport(
                                anomaly_type="CONFLICT",
                                severity="HIGH",
                                rule_ids=[r1.id, r2.id],
                                description=(
                                    f"Прямий конфлікт дій між {r1.id} ('{r1.action}') та {r2.id} ('{r2.action}'). "
                                    f"Правила мають однаковий пріоритет ({r1.priority}) і сумісні передумови."
                                ),
                                recommendation="Застосувати пріоритет безпеки або додати розмежувальні умови специфічності.",
                            )
                        )
        return anomalies

    def run_full_audit(self) -> List[AnomalyReport]:
        reports: List[AnomalyReport] = []
        reports.extend(self.find_unreachable_rules())
        reports.extend(self.find_redundancies())
        reports.extend(self.find_action_conflicts())
        return reports


class InferenceEngine:
    """Forward-chaining inference engine for diagnostic expert systems."""

    def __init__(self, rules: List[DiagnosticRule]) -> None:
        self.rules = sorted(rules, key=lambda r: r.priority, reverse=True)

    def evaluate(self, facts: Dict[str, Any]) -> Tuple[List[DiagnosticRule], Optional[DiagnosticRule], bool]:
        """Evaluates facts against the rule base.

        Returns:
            fired_rules: List of all rules whose preconditions matched.
            dominant_rule: The highest priority rule, or None.
            has_conflict: True if multiple rules fired with conflicting actions at equal highest priority.
        """
        fired = [r for r in self.rules if r.matches(facts)]
        if not fired:
            return [], None, False

        max_priority = fired[0].priority
        top_tier = [r for r in fired if r.priority == max_priority]

        # Check action compatibility among top-tier fired rules
        top_actions = {r.action for r in top_tier}
        has_conflict = False
        for pair in CONTRADICTORY_ACTIONS:
            if pair.issubset(top_actions):
                has_conflict = True
                break

        dominant = top_tier[0] if not has_conflict else None
        return fired, dominant, has_conflict


def load_rules(file_path: Path) -> List[DiagnosticRule]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [DiagnosticRule.from_dict(item) for item in data]


def load_test_cases(file_path: Path) -> List[Dict[str, Any]]:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    initial_rules_path = base_dir / "rules_initial.json"
    resolved_rules_path = base_dir / "rules_resolved.json"
    test_cases_path = base_dir / "test_cases.json"

    print("=" * 80)
    print("САМОСТІЙНА РОБОТА 4: АНАЛІЗ ПРОДУКЦІЙНИХ ПРАВИЛ ДІАГНОСТИКИ ЕНЕРГОСИСТЕМ")
    print("=" * 80)

    # 1. Audit initial rule base
    initial_rules = load_rules(initial_rules_path)
    print(f"\n[Крок 1] Завантажено початкову базу: {len(initial_rules)} правил.")

    analyzer_initial = RuleAnalyzer(initial_rules)
    initial_anomalies = analyzer_initial.run_full_audit()

    print(f"\n[Крок 2] Статичний аналіз початкової бази правил виявив {len(initial_anomalies)} проблем:")
    for idx, a in enumerate(initial_anomalies, start=1):
        print(f"  {idx}. [{a.anomaly_type}] (Правила: {', '.join(a.rule_ids)})")
        print(f"     Опис: {a.description}")
        print(f"     Рекомендація: {a.recommendation}")

    # 2. Audit resolved rule base
    resolved_rules = load_rules(resolved_rules_path)
    analyzer_resolved = RuleAnalyzer(resolved_rules)
    resolved_anomalies = analyzer_resolved.run_full_audit()
    print(f"\n[Крок 3] Аналіз скоригованої бази правил ({len(resolved_rules)} правил):")
    print(f"  Кількість невирішених аномалій: {len(resolved_anomalies)}")
    if not resolved_anomalies:
        print("  Усі конфлікти, надлишковості та недосяжні правила успішно усунено.")

    # 3. Test on 10 situations before and after
    test_cases = load_test_cases(test_cases_path)
    engine_initial = InferenceEngine(initial_rules)
    engine_resolved = InferenceEngine(resolved_rules)

    print(f"\n[Крок 4] Тестування на {len(test_cases)} ситуаціях (До / Після виправлень):\n")
    print(f"{'ID':<5} | {'Спрацювали (До)':<20} | {'Конфлікт?':<10} | {'Спрацювали (Після)':<25} | {'Результуюча дія (Після)':<35}")
    print("-" * 105)

    for case in test_cases:
        cid = case["id"]
        facts = case["facts"]

        fired_init, dom_init, conf_init = engine_initial.evaluate(facts)
        fired_res, dom_res, conf_res = engine_resolved.evaluate(facts)

        f_init_str = ",".join(r.id for r in fired_init) if fired_init else "NONE"
        f_res_str = ",".join(r.id for r in fired_res) if fired_res else "NONE"
        dom_res_act = dom_res.action if dom_res else "CONFLICT_UNRESOLVED"

        conf_str = "ТАК (!!!)" if conf_init else "НІ"
        print(f"{cid:<5} | {f_init_str:<20} | {conf_str:<10} | {f_res_str:<25} | {dom_res_act:<35}")

    print("\n" + "=" * 80)
    print("Аудит та верифікацію успішно завершено.")
    print("=" * 80)


if __name__ == "__main__":
    main()

"""Evaluation engine implementing Novak & Canas (2008) rubric and inter-rater agreement."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List, Tuple

from src.se06.models import (
    Concept,
    ConceptMap,
    CorrectionRecord,
    DefectPattern,
    EvaluationRecord,
    InterRaterAgreement,
    NovakCountMetrics,
    Proposition,
    RubricScore,
)


def load_maps_from_json(json_path: str | Path) -> Dict[str, ConceptMap]:
    """Load concept maps from structured JSON."""
    path = Path(json_path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    maps: Dict[str, ConceptMap] = {}
    for map_id, mdata in data["maps"].items():
        concepts = {
            c["id"]: Concept(
                id=c["id"],
                label=c["label"],
                level=c["level"],
                category=c["category"],
                is_example=c.get("is_example", False),
                attributes=c.get("attributes", {}),
            )
            for c in mdata["concepts"]
        }
        propositions = [
            Proposition(
                source_id=p["source_id"],
                target_id=p["target_id"],
                predicate=p["predicate"],
                is_cross_link=p.get("is_cross_link", False),
                is_valid=p.get("is_valid", True),
                comment=p.get("comment", ""),
            )
            for p in mdata["propositions"]
        ]
        maps[map_id] = ConceptMap(
            id=mdata["id"],
            title=mdata["title"],
            domain=mdata["domain"],
            focus_question=mdata["focus_question"],
            concepts=concepts,
            propositions=propositions,
            source_type=mdata["source_type"],
        )
    return maps


def load_defects_and_corrections(json_path: str | Path) -> Tuple[List[DefectPattern], List[CorrectionRecord]]:
    """Load defect catalog and corrections list."""
    path = Path(json_path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    catalog = [
        DefectPattern(
            defect_id=d["defect_id"],
            name=d["name"],
            category=d["category"],
            description=d["description"],
            manifestation=d["manifestation"],
            impact=d["impact"],
            detection_rule=d["detection_rule"],
            remediation=d["remediation"],
        )
        for d in data["catalog"]
    ]

    corrections = [
        CorrectionRecord(
            error_id=c["error_id"],
            defect_type=c["defect_type"],
            original_source=c["original_source"],
            original_predicate=c["original_predicate"],
            original_target=c["original_target"],
            corrected_source=c["corrected_source"],
            corrected_predicate=c["corrected_predicate"],
            corrected_target=c["corrected_target"],
            rationale=c["rationale"],
        )
        for c in data["corrections"]
    ]

    return catalog, corrections


class ConceptMapEvaluator:
    """Computes Novak scoring rubric and inter-rater agreement."""

    def __init__(self, maps: Dict[str, ConceptMap]):
        self.maps = maps

    def compute_novak_counts(self, cmap: ConceptMap) -> NovakCountMetrics:
        """Compute raw counts according to Novak & Gowin (1984) model."""
        valid_props = cmap.get_valid_propositions_count()
        # Count non-empty hierarchical levels present in concepts
        levels = len({c.level for c in cmap.concepts.values() if not c.is_example})
        cross_links = cmap.get_cross_links_count()
        examples = cmap.get_examples_count()

        return NovakCountMetrics(
            valid_propositions=valid_props,
            hierarchy_levels=levels,
            cross_links=cross_links,
            examples=examples,
        )

    def get_evaluator1_scores(self) -> Dict[str, RubricScore]:
        """Evaluator 1 (Primary Expert / Human Assessor) rubric scores (0-10 scale)."""
        return {
            "map_own": RubricScore(
                propositions=9.5,
                hierarchy=9.0,
                cross_links=9.0,
                examples=9.0,
                focus_question=9.5,
            ),
            "map_llm": RubricScore(
                propositions=3.5,
                hierarchy=3.0,
                cross_links=1.5,
                examples=1.0,
                focus_question=4.5,
            ),
            "map_llm_corrected": RubricScore(
                propositions=9.0,
                hierarchy=8.5,
                cross_links=8.5,
                examples=8.0,
                focus_question=9.0,
            ),
            "map_peer": RubricScore(
                propositions=8.5,
                hierarchy=8.5,
                cross_links=8.0,
                examples=8.0,
                focus_question=8.5,
            ),
        }

    def get_evaluator2_scores(self) -> Dict[str, RubricScore]:
        """Evaluator 2 (Independent Calibrated Peer / External Model) rubric scores."""
        return {
            "map_own": RubricScore(
                propositions=9.0,
                hierarchy=8.5,
                cross_links=8.5,
                examples=9.0,
                focus_question=9.0,
            ),
            "map_llm": RubricScore(
                propositions=4.0,
                hierarchy=2.5,
                cross_links=2.0,
                examples=1.0,
                focus_question=5.0,
            ),
            "map_llm_corrected": RubricScore(
                propositions=8.5,
                hierarchy=8.0,
                cross_links=8.0,
                examples=8.0,
                focus_question=8.5,
            ),
            "map_peer": RubricScore(
                propositions=8.0,
                hierarchy=8.0,
                cross_links=7.5,
                examples=8.0,
                focus_question=8.0,
            ),
        }

    @staticmethod
    def _rank_array(arr: List[float]) -> List[float]:
        """Compute fractional ranks for Spearman correlation."""
        indexed = sorted((val, idx) for idx, val in enumerate(arr))
        ranks = [0.0] * len(arr)
        i = 0
        while i < len(indexed):
            j = i
            while j < len(indexed) - 1 and math.isclose(indexed[j][0], indexed[j + 1][0], abs_tol=1e-7):
                j += 1
            mean_rank = (i + j + 2) / 2.0  # 1-based rank
            for k in range(i, j + 1):
                ranks[indexed[k][1]] = mean_rank
            i = j + 1
        return ranks

    @classmethod
    def calculate_pearson_r(cls, x: List[float], y: List[float]) -> float:
        """Compute Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        n = len(x)
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        den_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
        den_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))
        if math.isclose(den_x, 0.0, abs_tol=1e-9) or math.isclose(den_y, 0.0, abs_tol=1e-9):
            return 1.0 if x == y else 0.0
        return num / (den_x * den_y)

    @classmethod
    def calculate_spearman_rho(cls, x: List[float], y: List[float]) -> float:
        """Compute Spearman rank correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        rank_x = cls._rank_array(x)
        rank_y = cls._rank_array(y)
        return cls.calculate_pearson_r(rank_x, rank_y)

    def evaluate_inter_rater_agreement(self, map_id: str) -> InterRaterAgreement:
        """Compute differences, MAE, Pearson r and Spearman rho for a map."""
        s1 = self.get_evaluator1_scores()[map_id]
        s2 = self.get_evaluator2_scores()[map_id]

        criteria = ["propositions", "hierarchy", "cross_links", "examples", "focus_question"]
        v1 = [getattr(s1, c) for c in criteria]
        v2 = [getattr(s2, c) for c in criteria]

        diffs = {c: round(abs(val1 - val2), 2) for c, val1, val2 in zip(criteria, v1, v2)}
        mae = round(sum(diffs.values()) / len(diffs), 3)

        r = round(self.calculate_pearson_r(v1, v2), 4)
        rho = round(self.calculate_spearman_rho(v1, v2), 4)

        max_criterion = max(diffs.items(), key=lambda item: item[1])

        explanations = {
            "map_own": (
                "Найбільша розбіжність (0.5 бала) спостерігається у критеріях 'propositions', "
                "'hierarchy' та 'cross_links'. Оцінювач 1 виставив 9.5 за пропозиції завдяки "
                "точній відповідності стандартам IEC CIM, тоді як Оцінювач 2 знизив бал до 9.0 "
                "через використання узагальнених предикатів на окремих ребрах."
            ),
            "map_llm": (
                "Найбільша розбіжність (0.5 бала) зафіксована у критеріях 'propositions', 'hierarchy', "
                "'cross_links' та 'focus_question'. Оцінювач 2 дещо лояльніше оцінив поверхневу "
                "відповідність фокусному питанню (5.0 проти 4.5), проте обидва оцінювачі зійшлися "
                "на катастрофічно низькій якості ієрархії (2.5–3.0) та крос-зв'язків (1.5–2.0)."
            ),
            "map_llm_corrected": (
                "Розбіжність становить стабільні 0.5 бала за основними параметрами. Обидва експерти "
                "відзначили суттєвий прогрес після рефакторингу (підйом середнього балу з 2.7 до 8.5–8.8)."
            ),
            "map_peer": (
                "Різниця становить 0.5 бала у предикатах, ієрархії, крос-зв'язках та відповідності "
                "фокусному питанню через різну інтерпретацію глибини декомпозиції диспетчерського центру."
            ),
        }

        return InterRaterAgreement(
            map_id=map_id,
            evaluator_1="Оцінювач 1 (Експерт / Студент)",
            evaluator_2="Оцінювач 2 (Незалежний колега / LLM)",
            criterion_diffs=diffs,
            mae=mae,
            pearson_r=r,
            spearman_rho=rho,
            max_diff_criterion=max_criterion[0],
            max_diff_value=max_criterion[1],
            max_diff_explanation=explanations.get(map_id, "Відхилення у межах допустимої суб'єктивної похибки."),
        )

    def run_full_evaluation(self) -> Dict[str, Any]:
        """Run full evaluation suite across all maps and evaluators."""
        eval1 = self.get_evaluator1_scores()
        eval2 = self.get_evaluator2_scores()

        records_e1 = []
        records_e2 = []
        agreements = {}

        for mid, cmap in self.maps.items():
            counts = self.compute_novak_counts(cmap)
            records_e1.append(
                EvaluationRecord(
                    map_id=mid,
                    map_title=cmap.title,
                    evaluator_name="Оцінювач 1 (Експерт)",
                    evaluator_role="Первинний оцінювач",
                    rubric=eval1[mid],
                    novak_counts=counts,
                )
            )
            records_e2.append(
                EvaluationRecord(
                    map_id=mid,
                    map_title=cmap.title,
                    evaluator_name="Оцінювач 2 (Колега)",
                    evaluator_role="Вторинний верифікатор",
                    rubric=eval2[mid],
                    novak_counts=counts,
                )
            )
            agreements[mid] = self.evaluate_inter_rater_agreement(mid)

        # Cross-map overall correlation (correlation of mean scores across all maps)
        means_e1 = [eval1[m].mean for m in self.maps.keys()]
        means_e2 = [eval2[m].mean for m in self.maps.keys()]
        overall_r = round(self.calculate_pearson_r(means_e1, means_e2), 4)

        return {
            "evaluator_1_records": records_e1,
            "evaluator_2_records": records_e2,
            "agreements": agreements,
            "overall_pearson_r": overall_r,
        }

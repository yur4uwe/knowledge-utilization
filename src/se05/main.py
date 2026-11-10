"""Main runner for SE05: builds taxonomies, calculates metrics, exports SKOS graphs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from typing import Any, Dict

from src.se05.metrics import TaxonomyMetricsCalculator
from src.se05.skos_exporter import SkosExporter
from src.se05.taxonomy_builder import (
    BottomUpTaxonomyBuilder,
    ExpertCIMTaxonomyBuilder,
    TopDownTaxonomyBuilder,
    load_terms,
)


def run_pipeline(
    terms_path: str = "src/se05/terms.json",
    output_dir: str = "reports/resources",
) -> Dict[str, Any]:
    terms = load_terms(terms_path)

    # 1. Build taxonomies
    td_builder = TopDownTaxonomyBuilder(terms)
    top_down_tax = td_builder.build()

    td_defective_builder = TopDownTaxonomyBuilder(terms, inject_sample_defects=True)
    top_down_defective = td_defective_builder.build()

    bu_builder = BottomUpTaxonomyBuilder(terms)
    bottom_up_tax = bu_builder.build()

    expert_builder = ExpertCIMTaxonomyBuilder(terms)
    expert_tax = expert_builder.build()

    # 2. Compute metrics
    calc = TaxonomyMetricsCalculator(corpus_terms=terms, expert_taxonomy=expert_tax)
    metrics_td = calc.compute(top_down_tax)
    metrics_td_defect = calc.compute(top_down_defective)
    metrics_bu = calc.compute(bottom_up_tax)
    metrics_expert = calc.compute(expert_tax)

    # 3. Detect defects
    defects = calc.detect_defects(top_down_tax, bottom_up_tax)

    # 4. Export SKOS RDF graphs
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    SkosExporter(top_down_tax).save_turtle(out_path / "se05_top_down.ttl")
    SkosExporter(bottom_up_tax).save_turtle(out_path / "se05_bottom_up.ttl")
    SkosExporter(expert_tax).save_turtle(out_path / "se05_expert_cim.ttl")

    results = {
        "metrics": {
            "top_down": metrics_td.to_dict(),
            "top_down_with_defects": metrics_td_defect.to_dict(),
            "bottom_up": metrics_bu.to_dict(),
            "expert_cim": metrics_expert.to_dict(),
        },
        "defects": [d.to_dict() for d in defects],
    }

    results_file = out_path / "se05_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return results


if __name__ == "__main__":
    res = run_pipeline()
    print("Execution complete. Metrics summary:")
    print(json.dumps(res["metrics"], ensure_ascii=False, indent=2))

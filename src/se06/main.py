"""CLI runner and pipeline orchestrator for SE06 Concept Map Evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from src.se06.evaluator import (
    ConceptMapEvaluator,
    load_defects_and_corrections,
    load_maps_from_json,
)


def generate_mermaid_radar_chart(e1_records: list) -> str:
    """Generate Mermaid graph representing comparative score profiles across maps."""
    lines = [
        "```mermaid",
        "caption: Порівняльний профіль оцінювання концептуальних карт за рубрикою Новака (Оцінювач 1, шкала 0–10)",
        "options: { width=85% }",
        "xychart-beta",
        '    title "Бали критеріїв оцінювання концептуальних карт"',
        '    x-axis ["Пропозиції", "Ієрархія", "Крос-зв\'язки", "Приклади", "Фокусне питання"]',
        '    y-axis "Бал (0-10)" 0 --> 10',
    ]

    for rec in e1_records:
        r = rec.rubric
        title_short = {
            "map_own": "Власна (CmapTools)",
            "map_llm": "LLM (вихідна)",
            "map_llm_corrected": "LLM (виправлена)",
            "map_peer": "Еталон / Колега",
        }.get(rec.map_id, rec.map_id)
        vals = f"[{r.propositions}, {r.hierarchy}, {r.cross_links}, {r.examples}, {r.focus_question}]"
        lines.append(f'    line "{title_short}" {vals}')

    lines.append("```")
    return "\n".join(lines)


def generate_corrected_map_mermaid() -> str:
    """Generate Mermaid diagram of the corrected LLM concept map."""
    return """```mermaid
caption: Семантична структура виправленої концептуальної карти LLM з типізованими предикатами та крос-зв'язками
options: { width=100% }
flowchart TD
    %% Levels and Domains
    subgraph S_ACTOR ["Рівень 0: Диспетчерське керування"]
        TSO["Диспетчерський центр ОСП<br/>(TSOControlCenter)"]
    end

    subgraph S_GEN ["Рівень 1: Генерація та навантаження"]
        PP["Електростанція<br/>(PowerPlant)"]
        VRE["Стохастична ВДЕ<br/>(VREGeneration)"]
        DEM["Вузол споживання<br/>(DemandNode)"]
        TURBO["Турбогенератор ТВВ-1000<br/>(Екземпляр)"]:::exampleNode
    end

    subgraph S_NET ["Рівень 2: Мережева інфраструктура"]
        SUB["Підстанція 750 кВ<br/>(Substation)"]
        LINE["Лінія передачі 750 кВ<br/>(TransmissionLine)"]
        TRANS["Силовий трансформатор<br/>(PowerTransformer)"]
    end

    subgraph S_PROC ["Рівень 2-3: Процеси, захисти та параметри"]
        FREQ["Частота мережі 50.00 Гц<br/>(GridFrequency)"]
        BAL["Балансування частоти<br/>(FrequencyBalancing)"]
        ACHR["Автоматика розвантаження АЧР<br/>(UFLS)"]
        PROT["Релейний захист РЗА<br/>(RelayProtection)"]
        DGA["Хроматографія DGA<br/>(DissolvedGasAnalysis)"]
        SHORT["Коротке замикання<br/>(ShortCircuit)"]
        CONG["Перевантаження лінії<br/>(LineCongestion)"]
        SIPRO["SIPROTEC 7SJ<br/>(Екземпляр)"]:::exampleNode
    end

    %% Topological & Power Flows
    PP -->|"supplies-power-to (FIX_01)"| SUB
    VRE -->|"supplies-power-to (FIX_01)"| SUB
    TRANS -->|"part-of"| SUB
    SUB -->|"connected-to"| LINE
    LINE -->|"transmits-to"| DEM
    PP -->|"instance-of"| TURBO

    %% Grid Disturbances & Protection
    LINE -->|"experiences"| SHORT
    SHORT -->|"triggers (t ≤ 80 ms) (FIX_02)"| PROT
    PROT -->|"protects (відключає)"| LINE
    PROT -->|"instance-of"| SIPRO

    %% Dispatch & SCADA Supervision
    TSO -->|"monitors (SCADA) (FIX_05)"| LINE
    LINE -->|"develops"| CONG
    CONG -->|"triggers-alarm-at (FIX_06)"| TSO

    %% Cross-Links (Integrative Reconciliation)
    VRE -.->|"causes (ΔP небаланс) (FIX_03)"| FREQ
    FREQ -->|"activates (|Δf| > 0.05 Гц)"| BAL
    BAL -.->|"regulates (графік P) (Крос)"| PP
    FREQ -.->|"triggers (f < 49.0 Гц) (FIX_04)"| ACHR
    ACHR -.->|"disconnects (чергу навантаження)"| DEM
    DGA -.->|"monitors (C2H2 в маслі) (FIX_07)"| TRANS

    classDef exampleNode fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,stroke-dasharray: 5 5;
```"""


def run_pipeline() -> Dict[str, Any]:
    """Execute complete SE06 evaluation pipeline and persist artifacts."""
    base_dir = Path(__file__).resolve().parent
    root_dir = base_dir.parent.parent

    maps_file = base_dir / "maps.json"
    defects_file = base_dir / "defects.json"

    maps = load_maps_from_json(maps_file)
    catalog, corrections = load_defects_and_corrections(defects_file)

    evaluator = ConceptMapEvaluator(maps)
    eval_results = evaluator.run_full_evaluation()

    # Prepare serialized summary for report and validation
    summary = {
        "maps_count": len(maps),
        "defects_catalog_count": len(catalog),
        "corrections_count": len(corrections),
        "overall_pearson_r": eval_results["overall_pearson_r"],
        "evaluator_1": [
            {
                "map_id": r.map_id,
                "title": r.map_title,
                "rubric": r.rubric.as_dict(),
                "novak_counts": r.novak_counts.as_dict(),
            }
            for r in eval_results["evaluator_1_records"]
        ],
        "evaluator_2": [
            {
                "map_id": r.map_id,
                "title": r.map_title,
                "rubric": r.rubric.as_dict(),
                "novak_counts": r.novak_counts.as_dict(),
            }
            for r in eval_results["evaluator_2_records"]
        ],
        "agreements": {
            mid: {
                "mae": agr.mae,
                "pearson_r": agr.pearson_r,
                "spearman_rho": agr.spearman_rho,
                "max_diff_criterion": agr.max_diff_criterion,
                "max_diff_value": agr.max_diff_value,
                "diffs": agr.criterion_diffs,
                "explanation": agr.max_diff_explanation,
            }
            for mid, agr in eval_results["agreements"].items()
        },
        "defects_catalog": [
            {
                "defect_id": d.defect_id,
                "name": d.name,
                "category": d.category,
                "description": d.description,
                "remediation": d.remediation,
            }
            for d in catalog
        ],
        "corrections": [
            {
                "error_id": c.error_id,
                "defect_type": c.defect_type,
                "before": f"[{c.original_source}] --{c.original_predicate}--> [{c.original_target}]",
                "after": f"[{c.corrected_source}] --{c.corrected_predicate}--> [{c.corrected_target}]",
                "rationale": c.rationale,
            }
            for c in corrections
        ],
    }

    # Persist results in reports/resources/se06_results.json
    res_dir = root_dir / "reports" / "resources"
    res_dir.mkdir(parents=True, exist_ok=True)
    out_file = res_dir / "se06_results.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return summary


def main() -> None:
    results = run_pipeline()
    print("=== SE06 Concept Map Evaluation Pipeline Complete ===")
    print(f"Maps evaluated: {results['maps_count']}")
    print(f"Defect patterns in catalog: {results['defects_catalog_count']}")
    print(f"Corrections implemented: {results['corrections_count']}")
    print(f"Overall Inter-Rater Pearson r: {results['overall_pearson_r']}")


if __name__ == "__main__":
    main()

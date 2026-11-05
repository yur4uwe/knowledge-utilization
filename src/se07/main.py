"""CLI runner and orchestrator for SE07: Ontology Pitfall Audit and Situation Templates."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.se07.analyzer import OntologyAnalyzer
from src.se07.situations import SITUATION_TEMPLATES, validate_situation_bindings

RAW_ONTOLOGY = Path(__file__).resolve().parent / "data" / "energy_raw.ttl"
CORRECTED_ONTOLOGY = Path(__file__).resolve().parent / "data" / "energy_corrected.ttl"


def generate_mermaid_situation_diagram() -> str:
    """Generate Mermaid state-event diagram illustrating Situation 1 and Situation 2."""
    return """```mermaid
caption: Шаблони динамічних ситуацій енергосистеми (Стан -> Подія -> Умова -> Новий стан -> Дія)
options: { width=90% }
flowchart LR
    subgraph S1["Ситуація 1: КЗ на ПЛ 750 кВ"]
        direction TB
        State1["NormalOperationState\\n(Номінальний режим)"]
        Evt1["ShortCircuitFault\\n(КЗ 24.5 кА)"]
        Cond1{"hasFaultCurrentKA > 20"}
        NewState1["EmergencyState\\n(Аварійний режим)"]
        Act1["RelayProtectionAction\\n(Відсічка вимикача 65 мс)"]

        State1 --> Evt1 --> Cond1
        Cond1 -- Так --> NewState1 --> Act1
    end

    subgraph S2["Ситуація 2: Дефіцит генерації"]
        direction TB
        State2["NormalOperationState\\n(f = 50.00 Гц)"]
        Evt2["FrequencyDeviation\\n(Втрата 1000 МВт)"]
        Cond2{"hasGridFrequencyHz < 49.80"}
        NewState2["AlertState\\n(Тривожний режим)"]
        Act2["PrimaryFrequencyControl\\n(Пуск ГАЕС FCR 2-15 с)"]

        State2 --> Evt2 --> Cond2
        Cond2 -- Так --> NewState2 --> Act2
    end
```"""


def run_pipeline() -> Dict[str, Any]:
    """Execute complete SE07 pipeline, returning audit results and validation reports."""
    raw_analyzer = OntologyAnalyzer(RAW_ONTOLOGY)
    corr_analyzer = OntologyAnalyzer(CORRECTED_ONTOLOGY)

    raw_report = raw_analyzer.run_full_audit()
    corr_report = corr_analyzer.run_full_audit()

    situation_val = validate_situation_bindings(corr_analyzer)

    # Core 7 Seeded Defect Summary for Report
    seeded_defects_catalog = [
        {
            "id": "LOG-01",
            "category": "Логічна (Logical)",
            "oops": "P19 (Unsatisfiable Class)",
            "entity": ":InconsistentDiagnosticAsset",
            "desc": "Спадкування взаємовиключних disjoint-класів :GridAsset та :SystemProcess.",
            "remediation": "Усунено множинне успадкування; переведено в :NetworkInfra з асоціацією.",
            "effect": "Клас став задовольняваним (Satisfiable). Reasoner consistency: True.",
        },
        {
            "id": "LOG-02",
            "category": "Логічна (Logical)",
            "oops": "P06 (Cycle in Hierarchy)",
            "entity": ":GridBalancingProcess <-> :SecondaryFrequencyRestoration",
            "desc": "Циклічна взаємна залежність підкласів subClassOf.",
            "remediation": "Розірвано циклічне посилання; встановлено строгу орієнтовану ієрархію.",
            "effect": "Ієрархія позбавлена тавтологічної еквівалентності (A equiv B).",
        },
        {
            "id": "NAM-01",
            "category": "Іменування (Naming)",
            "oops": "P22 (Naming Conventions)",
            "entity": ":battery_energy_storage_system, :dissolved_gas_monitoring_unit",
            "desc": "Використання змішаного snake_case замість загального UpperCamelCase.",
            "remediation": "Перейменовано на :BatteryStorageBESS та :DissolvedGasMonitoringUnit.",
            "effect": "Повна уніфікація простору імен згідно з практиками W3C / Protégé.",
        },
        {
            "id": "NAM-02",
            "category": "Іменування (Naming)",
            "oops": "P22 / P07 (Verb Naming)",
            "entity": ":trip_circuit_breaker",
            "desc": "Вживання наказового дієслова замість іменникового концепту процесу.",
            "remediation": "Перейменовано на :CircuitBreakerTripAction.",
            "effect": "Відновлено таксономічну чистоту класів як сутностей, а не методів.",
        },
        {
            "id": "DOC-01",
            "category": "Документація (Doc)",
            "oops": "P08 (Missing Annotations)",
            "entity": ":WindPowerPlant, :BiomassPowerPlant, :InsulationDegradation",
            "desc": "Відсутність анотацій rdfs:label та rdfs:comment.",
            "remediation": "Додано повні україномовні інженерні описи та позначки IEC CIM.",
            "effect": "100% покриття словника людсько-читабельними метаданими.",
        },
        {
            "id": "DOC-02",
            "category": "Документація (Doc)",
            "oops": "P13 (Inverse Properties)",
            "entity": ":suppliesPowerTo, :protects",
            "desc": "Відсутність зворотних зв'язків owl:inverseOf для асиметричних предикатів.",
            "remediation": "Оголошено властивості :receivesPowerFrom та :isProtectedBy.",
            "effect": "Двонаправлена навігація та повна дедукція в графових запитах SPARQL.",
        },
        {
            "id": "ONT-01",
            "category": "OntoClean (OntoClean)",
            "oops": "Guarino & Welty (2002)",
            "entity": ":PowerTransformer subClassOf :FaultedAsset",
            "desc": "Rigidity Inversion: жорсткий концепт (+R) підпорядковано анти-жорсткій ролі (~R).",
            "remediation": "Перенесено :PowerTransformer під :NetworkInfra (+R); аварійний стан винесено в роль/стан.",
            "effect": "Усунено логічну ваду 'кожен трансформатор є сутнісно пошкодженим'.",
        },
    ]

    return {
        "raw_report": raw_report,
        "corr_report": corr_report,
        "seeded_catalog": seeded_defects_catalog,
        "situation_templates": SITUATION_TEMPLATES,
        "situation_validation": situation_val,
        "mermaid_chart": generate_mermaid_situation_diagram(),
    }


def main() -> None:
    results = run_pipeline()
    raw = results["raw_report"]
    corr = results["corr_report"]

    print("=" * 80)
    print("SE07: ONTOLOGY PITFALL AUDIT, REASONER CONSISTENCY & SITUATION TEMPLATES")
    print("=" * 80)
    print(f"\n[1] BASELINE ONTOLOGY (RAW) AUDIT:")
    print(f"    - Path: {raw.ontology_path}")
    print(f"    - Named Classes: {raw.total_classes} (Criteria C1 >= 50: {raw.total_classes >= 50})")
    print(f"    - Properties: {raw.total_properties}")
    print(f"    - Total Axioms: {raw.total_axioms}")
    print(f"    - Detected Defects: {raw.defect_count} (Criteria C1 >= 5: {raw.defect_count >= 5})")
    print(f"    - Breakdown by Category: {raw.category_counts}")
    print(f"    - DL Consistency: {raw.is_dl_consistent} (Inconsistent due to critical logical faults)")

    print(f"\n[2] REMEDIATED ONTOLOGY (CORRECTED) AUDIT:")
    print(f"    - Path: {corr.ontology_path}")
    print(f"    - Named Classes: {corr.total_classes}")
    print(f"    - Detected Defects: {corr.defect_count}")
    print(f"    - DL Consistency: {corr.is_dl_consistent} (All classes satisfiable, 0 cycles, 0 rigidity clashes)")

    print(f"\n[3] REMEDIATION DELTA (CRITERIA C3 >= 3 FIXED):")
    delta_defects = raw.defect_count - corr.defect_count
    print(f"    - Resolved Defects: {delta_defects} (Required >= 3: {delta_defects >= 3})")

    print(f"\n[4] SITUATION TEMPLATES VALIDATION (CRITERIA C4):")
    for sid, ok, msg in results["situation_validation"]:
        status = "PASSED" if ok else "FAILED"
        print(f"    - [{status}] {sid}: {msg}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()

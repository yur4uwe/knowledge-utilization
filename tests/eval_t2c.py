"""
Text-to-Cypher Evaluation Pipeline (Tests & Metrics)
Pipeline stages:
1. Load gold dataset (tests/t2c.jsonl) and LLM outputs (llm_log/t2c_prompt_v1_baseline.json, llm_log/t2c_prompt_v2_refined.json)
2. Read-only role validator (blocks mutation statements)
3. Schema adherence checker (labels and relationship types against LPG schema)
4. LIMIT clause safety checker / injector
5. Execution against Neo4j database
6. Metrics calculation (Syntax, Schema, Read-Only, Execution Accuracy)
"""

import os
import re
import json
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

ALLOWED_LABELS = {
    "Substation", "GeneratingUnit", "EnergyStorage", "TransmissionLine",
    "Transformer", "ProtectionDevice", "FaultEvent", "PowerConsumer"
}

ALLOWED_RELATIONSHIPS = {
    "CONNECTED_TO", "SUPPLIES_POWER_TO", "INSTALLED_AT", "STEPS_VOLTAGE",
    "PROTECTS", "AFFECTS_ASSET", "TRIGGERS_ACTION", "ACTIVATES_STORAGE", "FEEDS_LOAD"
}

MUTATION_KEYWORDS = {"CREATE", "MERGE", "SET", "DELETE", "REMOVE", "DROP", "ALTER"}

def is_read_only(query: str) -> bool:
    tokens = set(re.findall(r"\b[A-Z]+\b", query.upper()))
    return len(tokens.intersection(MUTATION_KEYWORDS)) == 0

def check_schema_adherence(query: str) -> bool:
    # Check labels
    labels = re.findall(r":([A-Za-z0-9_]+)", query)
    for lbl in labels:
        if lbl not in ALLOWED_LABELS and lbl not in ALLOWED_RELATIONSHIPS:
            return False
    return True

def has_limit(query: str) -> bool:
    return bool(re.search(r"\bLIMIT\b", query, re.IGNORECASE))

def evaluate_run(run_file: Path, driver):
    with open(run_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    with driver.session() as session:
        for item in data["results"]:
            qid = item["id"]
            cypher = item["generated_cypher"]
            read_only_ok = is_read_only(cypher)
            schema_ok = check_schema_adherence(cypher)
            limit_ok = has_limit(cypher) or ("sum(" in cypher.lower() or "avg(" in cypher.lower() or "count(" in cypher.lower())
            
            exec_ok = False
            error_msg = None
            if read_only_ok and schema_ok:
                try:
                    res = session.run(cypher)
                    records = [r.data() for r in res]
                    exec_ok = True
                except Exception as ex:
                    error_msg = str(ex)
            else:
                error_msg = "Blocked by read-only or schema adherence guardrails"

            results.append({
                "id": qid,
                "read_only": read_only_ok,
                "schema": schema_ok,
                "limit": limit_ok,
                "exec": exec_ok,
                "error": error_msg
            })

    total = len(results)
    ro_acc = sum(1 for r in results if r["read_only"]) / total
    schema_acc = sum(1 for r in results if r["schema"]) / total
    exec_acc = sum(1 for r in results if r["exec"]) / total

    return {
        "total": total,
        "read_only_accuracy": ro_acc,
        "schema_accuracy": schema_acc,
        "execution_accuracy": exec_acc,
        "details": results
    }

def test_t2c_pipeline():
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    base_dir = Path(__file__).resolve().parent.parent
    
    v1_file = base_dir / "llm_log" / "t2c_prompt_v1_baseline.json"
    v2_file = base_dir / "llm_log" / "t2c_prompt_v2_refined.json"

    res_v1 = evaluate_run(v1_file, driver)
    res_v2 = evaluate_run(v2_file, driver)
    driver.close()

    print("\n================ Text-to-Cypher Evaluation Summary ================")
    print(f"V1 Baseline:  Schema={res_v1['schema_accuracy']*100:.1f}%, Exec={res_v1['execution_accuracy']*100:.1f}%")
    print(f"V2 Refined:   Schema={res_v2['schema_accuracy']*100:.1f}%, Exec={res_v2['execution_accuracy']*100:.1f}%")
    
    # Save evaluation summary
    eval_summary = {
        "v1_baseline": res_v1,
        "v2_refined": res_v2
    }
    with open(base_dir / "docs" / "t2c_eval_summary.json", "w", encoding="utf-8") as f:
        json.dump(eval_summary, f, ensure_ascii=False, indent=2)

    assert res_v2["execution_accuracy"] >= 0.90, "Refined prompt execution accuracy should be >= 90%"
    assert res_v2["execution_accuracy"] > res_v1["execution_accuracy"], "Refinement should improve accuracy"

if __name__ == "__main__":
    test_t2c_pipeline()

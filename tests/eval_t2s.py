#!/usr/bin/env python3
"""
Text-to-SPARQL Evaluation Pipeline
Pipeline stages:
1. Load gold dataset (tests/t2s.jsonl) and LLM outputs (llm_log/...)
2. SPARQL Syntax Parser (rdflib SPARQL parser)
3. Schema Adherence Checker (validates against vocabulary in data/kb.ttl)
4. Triplestore Execution with LIMIT against Fuseki endpoint
5. Metrics calculation (Syntax, Schema, Execution) before and after prompt refinement
"""

import json
import re
import sys
import requests
import rdflib
from rdflib.plugins.sparql.parser import parseQuery

FUSEKI_ENDPOINT = "http://localhost:3030/energy/sparql"
KB_FILE = "data/kb.ttl"
T2S_GOLD_FILE = "tests/t2s.jsonl"
LOG_V1 = "llm_log/t2s_prompt_v1_baseline.json"
LOG_V2 = "llm_log/t2s_prompt_v2_refined.json"

def extract_schema_vocabulary(ttl_path: str):
    g = rdflib.Graph()
    g.parse(ttl_path, format="turtle")
    base_ns = "http://www.semanticweb.org/ontologies/2026/energy-system#"
    vocab = set()
    for s, p, o in g:
        for term in (s, p, o):
            if isinstance(term, rdflib.URIRef) and str(term).startswith(base_ns):
                local_name = str(term)[len(base_ns):]
                vocab.add(local_name)
    return vocab

def check_syntax(query_str: str) -> bool:
    try:
        parseQuery(query_str)
        return True
    except Exception:
        return False

def check_schema_adherence(query_str: str, allowed_vocab: set) -> bool:
    # Find all tokens prefixed with ':' (e.g. :Substation, :hasRatedActivePowerMW)
    # Exclude standard prefixes like rdf:type or xsd:double
    tokens = re.findall(r'(?<![a-zA-Z0-9_]):([a-zA-Z0-9_]+)', query_str)
    for tok in tokens:
        if tok not in allowed_vocab:
            return False
    return True

def ensure_limit(query_str: str, limit_val: int = 50) -> str:
    if re.search(r'\bLIMIT\b', query_str, re.IGNORECASE) or re.search(r'\bASK\b', query_str, re.IGNORECASE):
        return query_str
    return query_str.rstrip() + f"\nLIMIT {limit_val}\n"

def execute_sparql(query_str: str, endpoint: str):
    query_with_limit = ensure_limit(query_str)
    try:
        resp = requests.post(
            endpoint,
            data={"query": query_with_limit},
            headers={"Accept": "application/sparql-results+json"},
            timeout=5
        )
        if resp.status_code != 200:
            return False, None
        data = resp.json()
        if "boolean" in data:
            return True, data["boolean"]
        bindings = data.get("results", {}).get("bindings", [])
        # Canonical representation of bindings for comparison
        normalized = []
        for b in bindings:
            row = {k: v.get("value") for k, v in b.items()}
            normalized.append(tuple(sorted(row.items())))
        return True, set(normalized)
    except Exception as e:
        return False, None

def evaluate_run(run_data, gold_data, allowed_vocab, endpoint):
    gold_map = {item["id"]: item for item in gold_data}
    total = len(run_data["results"])
    syntax_ok = 0
    schema_ok = 0
    exec_ok = 0
    detailed_results = []

    for item in run_data["results"]:
        qid = item["id"]
        raw_sparql = item["raw_output"]
        gold_sparql = gold_map[qid]["gold_sparql"]

        # Step 1: Syntax
        is_syn = check_syntax(raw_sparql)
        if is_syn:
            syntax_ok += 1

        # Step 2: Schema
        is_sch = is_syn and check_schema_adherence(raw_sparql, allowed_vocab)
        if is_sch:
            schema_ok += 1

        # Step 3: Execution
        is_exec = False
        if is_sch:
            ok_gold, res_gold = execute_sparql(gold_sparql, endpoint)
            ok_cand, res_cand = execute_sparql(raw_sparql, endpoint)
            if ok_gold and ok_cand and res_gold == res_cand:
                is_exec = True
                exec_ok += 1

        detailed_results.append({
            "id": qid,
            "question": item["question"],
            "syntax": is_syn,
            "schema": is_sch,
            "exec": is_exec,
            "raw_output": raw_sparql
        })

    metrics = {
        "total": total,
        "syntax_accuracy": (syntax_ok / total) * 100,
        "schema_accuracy": (schema_ok / total) * 100,
        "execution_accuracy": (exec_ok / total) * 100,
        "syntax_count": syntax_ok,
        "schema_count": schema_ok,
        "execution_count": exec_ok,
        "details": detailed_results
    }
    return metrics

def main():
    allowed_vocab = extract_schema_vocabulary(KB_FILE)
    print(f"Loaded schema vocabulary: {len(allowed_vocab)} unique local terms.")

    gold_data = []
    with open(T2S_GOLD_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                gold_data.append(json.loads(line))

    with open(LOG_V1, "r", encoding="utf-8") as f:
        v1_data = json.load(f)

    with open(LOG_V2, "r", encoding="utf-8") as f:
        v2_data = json.load(f)

    print("\n--- Running Evaluation: V1 Baseline ---")
    m1 = evaluate_run(v1_data, gold_data, allowed_vocab, FUSEKI_ENDPOINT)
    print(f"Syntax Correctness:  {m1['syntax_count']}/{m1['total']} ({m1['syntax_accuracy']:.1f}%)")
    print(f"Schema Adherence:    {m1['schema_count']}/{m1['total']} ({m1['schema_accuracy']:.1f}%)")
    print(f"Execution Accuracy:  {m1['execution_count']}/{m1['total']} ({m1['execution_accuracy']:.1f}%)")

    print("\n--- Running Evaluation: V2 Refined Prompt ---")
    m2 = evaluate_run(v2_data, gold_data, allowed_vocab, FUSEKI_ENDPOINT)
    print(f"Syntax Correctness:  {m2['syntax_count']}/{m2['total']} ({m2['syntax_accuracy']:.1f}%)")
    print(f"Schema Adherence:    {m2['schema_count']}/{m2['total']} ({m2['schema_accuracy']:.1f}%)")
    print(f"Execution Accuracy:  {m2['execution_count']}/{m2['total']} ({m2['execution_accuracy']:.1f}%)")

if __name__ == "__main__":
    main()

"""Script to execute all SPARQL queries against live Wikidata Query Service

and cache verified results into src/se08/data/se08_results.json.
"""

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.se08.client import WikidataClient, save_cached_results
from src.se08.queries import QUERIES, LLM_COMPARISONS


def fetch_all() -> None:
    """Execute all queries against live Wikidata endpoint and save results."""
    print("=" * 75)
    print("Self-Education 8: Fetching live data from Wikidata Query Service")
    print("Endpoint: https://query.wikidata.org/sparql")
    print("=" * 75)

    client = WikidataClient(timeout=30)
    results_payload = {
        "endpoint": "https://query.wikidata.org/sparql",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "queries": {},
        "llm_evaluations": {},
    }

    # 1. Execute Domain Competency Queries (CQ1 - CQ8)
    print("\n--- [1] Executing Domain Queries (CQ1 - CQ8) ---")
    for qid, qdata in QUERIES.items():
        title = qdata["title"]
        sparql = qdata["sparql"]
        print(f"-> {qid}: {title} ...", end=" ", flush=True)

        start = time.time()
        res = client.execute_query(sparql)
        elapsed = time.time() - start

        if "error" in res:
            print(f"[ERROR: {res['error']}] ({elapsed:.2f}s)")
            results_payload["queries"][qid] = {
                "file": qdata["file"],
                "query_name": title,
                "status": "error",
                "error": res["error"],
            }
        else:
            boolean = res.get("boolean")
            bindings = res.get("results", {}).get("bindings", [])
            count = len(bindings) if boolean is None else (1 if boolean else 0)
            status_text = f"OK, count={count}" if boolean is None else f"OK, boolean={boolean}"
            print(f"[{status_text}] ({elapsed:.2f}s)")

            results_payload["queries"][qid] = {
                "file": qdata["file"],
                "query_name": title,
                "status": "success",
                "elapsed_sec": round(elapsed, 3),
                "count": count,
                "boolean": boolean,
                "bindings": bindings,
            }

    # 2. Execute LLM Comparison Cases
    print("\n--- [2] Executing LLM Text-to-SPARQL Cases (Raw vs Fixed) ---")
    for cid, cdata in LLM_COMPARISONS.items():
        title = cdata["title"]
        print(f"-> {cid} [{title}]:")

        # Test Raw LLM query
        raw_res = client.execute_query(cdata["raw_llm_sparql"])
        raw_err = raw_res.get("error")
        raw_bindings = raw_res.get("results", {}).get("bindings", [])
        raw_bool = raw_res.get("boolean")
        raw_count = len(raw_bindings) if raw_bool is None else (1 if raw_bool else 0)

        # Test Fixed query
        fixed_res = client.execute_query(cdata["fixed_sparql"])
        fixed_err = fixed_res.get("error")
        fixed_bindings = fixed_res.get("results", {}).get("bindings", [])
        fixed_bool = fixed_res.get("boolean")
        fixed_count = len(fixed_bindings) if fixed_bool is None else (1 if fixed_bool else 0)

        print(f"   Raw LLM   : {'Error: ' + str(raw_err) if raw_err else f'count={raw_count}, bool={raw_bool}'}")
        print(f"   Fixed     : {'Error: ' + str(fixed_err) if fixed_err else f'count={fixed_count}, bool={fixed_bool}'}")

        results_payload["llm_evaluations"][cid] = {
            "title": title,
            "raw_execution": {
                "status": "error" if raw_err else "success",
                "count": raw_count,
                "boolean": raw_bool,
                "error": raw_err,
            },
            "fixed_execution": {
                "status": "error" if fixed_err else "success",
                "count": fixed_count,
                "boolean": fixed_bool,
                "error": fixed_err,
            },
        }

    save_cached_results(results_payload)
    print("\nAll results saved to src/se08/data/se08_results.json successfully.")


if __name__ == "__main__":
    fetch_all()

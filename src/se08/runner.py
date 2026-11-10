"""Execution runner for Self-Education 8 queries."""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.se08.client import WikidataClient, load_cached_results, save_cached_results
from src.se08.queries import QUERIES, LLM_COMPARISONS



def run_all(live: bool = False) -> None:
    """Run all queries or print cached verification data."""
    print("=" * 70)
    print("Самостійна робота 8: SPARQL до Wikidata (Управління енергосистемами)")
    print("=" * 70)

    if live:
        print("Виконання в режимі LIVE до https://query.wikidata.org/sparql ...")
        client = WikidataClient()
        data = load_cached_results()
        if "queries" not in data:
            data["queries"] = {}

        for qid, qdata in QUERIES.items():
            print(f"-> Виконання {qid}: {qdata['title']} ...", end=" ", flush=True)
            res = client.execute_query(qdata["sparql"])
            if "error" in res:
                print(f"[ПОМИЛКА: {res['error']}]")
            else:
                bindings = res.get("results", {}).get("bindings", [])
                boolean = res.get("boolean")
                count = len(bindings) if boolean is None else 1
                data["queries"][qid] = {
                    "query_name": qdata["title"],
                    "status": "success",
                    "count": count,
                    "bindings": bindings[:5] if boolean is None else None,
                    "boolean": boolean,
                }
                print(f"[OK, знайдено: {count} записів]")
        save_cached_results(data)
    else:
        print("Завантаження верифікованих результатів із reports/resources/se08_results.json:")
        data = load_cached_results()
        queries_res = data.get("queries", {})
        for qid, qdata in QUERIES.items():
            res = queries_res.get(qid, {})
            status = res.get("status", "unknown")
            count = res.get("count", res.get("boolean", "N/A"))
            print(f"- {qid}: {qdata['title']} | Конструкції: {', '.join(qdata['constructs'])} | Статус: {status} (Результатів: {count})")

    print("\nПорівняння з LLM Text-to-SPARQL (Виправлено >= 3 дефекти):")
    for cid, cdata in LLM_COMPARISONS.items():
        print(f"* {cid} [{cdata['title']}]:")
        print(f"  Дефект: {cdata['defect_type']}")


if __name__ == "__main__":
    is_live = "--live" in sys.argv
    run_all(live=is_live)

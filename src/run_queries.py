"""
Execute all Cypher queries (CQ1-CQ8 + Impact Analysis 1-2) against Neo4j and format results for docs/cypher_results.md
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

QUERIES_DIR = Path(__file__).resolve().parent.parent / "queries"

def main():
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    query_files = sorted(QUERIES_DIR.glob("q*.cypher"))
    results = {}

    with driver.session() as session:
        for qf in query_files:
            print(f"Executing {qf.name}...")
            with open(qf, "r", encoding="utf-8") as f:
                query_text = f.read().strip()
            
            # Execute
            res = session.run(query_text)
            records = [r.data() for r in res]
            results[qf.name] = {
                "file": qf.name,
                "query": query_text,
                "count": len(records),
                "records": records[:10]  # top 10
            }
            print(f" -> Returned {len(records)} records")

    driver.close()
    
    out_json = Path(__file__).resolve().parent.parent / "docs" / "cypher_execution_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Results dumped to {out_json}")

if __name__ == "__main__":
    main()

"""
Run Graph Data Science (GDS) algorithms:
1. Graph projection
2. PageRank (write to node property 'pagerank')
3. Louvain Community Detection (write to node property 'community')
4. Run PROFILE for 2 queries (one unoptimized and optimized) and capture plan metrics.
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

def main():
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    with driver.session() as session:
        # Check if projection already exists, drop if needed
        exists = session.run("CALL gds.graph.exists('powerGrid') YIELD exists RETURN exists").single()["exists"]
        if exists:
            print("Dropping existing GDS projection 'powerGrid'...")
            session.run("CALL gds.graph.drop('powerGrid')")

        print("[1] Creating GDS in-memory graph projection 'powerGrid'...")
        proj_res = session.run("""
            CALL gds.graph.project(
                'powerGrid',
                ['Substation', 'GeneratingUnit', 'EnergyStorage', 'TransmissionLine', 'PowerConsumer'],
                {
                    CONNECTED_TO: {orientation: 'UNDIRECTED'},
                    SUPPLIES_POWER_TO: {orientation: 'NATURAL'},
                    FEEDS_LOAD: {orientation: 'NATURAL'}
                }
            )
            YIELD graphName, nodeCount, relationshipCount
            RETURN graphName, nodeCount, relationshipCount
        """).single()
        print(f"Projected {proj_res['graphName']}: {proj_res['nodeCount']} nodes, {proj_res['relationshipCount']} rels")

        print("\n[2] Executing PageRank (write mode)...")
        pr_summary = session.run("""
            CALL gds.pageRank.write('powerGrid', {
                maxIterations: 20,
                dampingFactor: 0.85,
                writeProperty: 'pagerank'
            })
            YIELD nodePropertiesWritten, computeMillis
            RETURN nodePropertiesWritten, computeMillis
        """).single()
        print(f"PageRank finished: {pr_summary['nodePropertiesWritten']} nodes updated in {pr_summary['computeMillis']} ms")

        # Top 10 by PageRank
        top10_pr = session.run("""
            MATCH (n)
            WHERE n.pagerank IS NOT NULL
            RETURN n.id AS id, n.name AS name, labels(n)[0] AS type, n.pagerank AS pagerank
            ORDER BY pagerank DESC
            LIMIT 10
        """).data()
        print("\nTop 10 Nodes by PageRank:")
        for r in top10_pr:
            print(f"  {r['pagerank']:.4f} | {r['type']:<16} | {r['name']} ({r['id']})")

        print("\n[3] Executing Louvain Community Detection (write mode)...")
        louvain_summary = session.run("""
            CALL gds.louvain.write('powerGrid', {
                writeProperty: 'community'
            })
            YIELD communityCount, modularity, computeMillis
            RETURN communityCount, modularity, computeMillis
        """).single()
        print(f"Louvain finished: {louvain_summary['communityCount']} communities, modularity={louvain_summary['modularity']:.4f} in {louvain_summary['computeMillis']} ms")

        # Community distribution
        communities = session.run("""
            MATCH (n)
            WHERE n.community IS NOT NULL
            WITH n.community AS commId, count(n) AS memberCount, collect(n.name)[..5] AS sampleMembers
            RETURN commId, memberCount, sampleMembers
            ORDER BY memberCount DESC
        """).data()
        print(f"\nDiscovered {len(communities)} communities:")
        for c in communities[:5]:
            print(f"  Community {c['commId']}: {c['memberCount']} nodes, samples: {c['sampleMembers']}")

        print("\n[4] Profiling Queries: Unoptimized vs Optimized...")
        # Query 1: Unoptimized - full scan without label and Regex match
        profile_unopt = session.run("""
            PROFILE
            MATCH (a)-[:CONNECTED_TO*1..2]-(b)
            WHERE a.name =~ '.*Вінницька.*' AND b.name =~ '.*Київська.*'
            RETURN count(*) AS cnt
        """).consume().profile

        # Query 2: Optimized - labeled nodes with indexed property match
        profile_opt = session.run("""
            PROFILE
            MATCH (a:Substation {id: 'SS_Vinnytska_750'})-[:CONNECTED_TO*1..2]-(b:Substation {id: 'SS_Kyivska_750'})
            RETURN count(*) AS cnt
        """).consume().profile

        # Query 3: Profiling another query (Transformer status index lookup)
        profile_q2 = session.run("""
            PROFILE
            MATCH (t:Transformer)-[:INSTALLED_AT]->(s:Substation)
            WHERE t.status = 'ALARM'
            RETURN t.name, s.name
        """).consume().profile

        def sum_hits(p):
            return p.get("dbHits", 0) + sum(sum_hits(c) for c in p.get("children", []))

        hits_unopt = sum_hits(profile_unopt)
        hits_opt = sum_hits(profile_opt)
        hits_q2 = sum_hits(profile_q2)

        print(f"Unoptimized Query: total dbHits = {hits_unopt}")
        print(f"Optimized Query:   total dbHits = {hits_opt}")
        print(f"Query 2 (Transformer status index lookup): total dbHits = {hits_q2}")

        gds_data = {
            "top10_pagerank": top10_pr,
            "communities": communities,
            "unoptimized_profile": {
                "dbHits": hits_unopt,
                "rows": profile_unopt.get("rows"),
            },
            "optimized_profile": {
                "dbHits": hits_opt,
                "rows": profile_opt.get("rows"),
            },
            "transformer_profile": {
                "dbHits": hits_q2,
            }
        }

        with open(Path(__file__).resolve().parent.parent / "docs" / "gds_profile_data.json", "w", encoding="utf-8") as f:
            json.dump(gds_data, f, ensure_ascii=False, indent=2)

    driver.close()

if __name__ == "__main__":
    main()

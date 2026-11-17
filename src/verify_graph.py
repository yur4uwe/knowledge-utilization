"""
Verification and Health Check utility for Neo4j Knowledge Graph.
Checks database connectivity, GDS extension, graph statistics, constraints, indexes,
and node property integrity.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase, exceptions

load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

def main():
    print(f"Connecting to Neo4j at {URI} as user '{USER}'...")
    try:
        driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
        with driver.session() as session:
            # 1. Connectivity and GDS version
            server_info = session.run("CALL dbms.components() YIELD name, versions, edition RETURN name, versions[0] AS version, edition").single()
            print(f"[OK] Connected to {server_info['name']} {server_info['version']} ({server_info['edition']} Edition)")

            try:
                gds_ver = session.run("RETURN gds.version() AS ver").single()["ver"]
                print(f"[OK] Graph Data Science (GDS) extension active: v{gds_ver}")
            except Exception as e:
                print(f"[WARN] GDS extension not detected: {e}")

            # 2. Graph statistics
            node_cnt = session.run("MATCH (n) RETURN count(n) AS cnt").single()["cnt"]
            rel_cnt = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt").single()["cnt"]
            print(f"[STATS] Total Nodes: {node_cnt} (Threshold: >= 100)")
            print(f"[STATS] Total Relationships: {rel_cnt} (Threshold: >= 200)")

            # Breakdown by label
            labels_info = session.run("CALL db.labels() YIELD label RETURN label ORDER BY label").data()
            print("\n[LABELS]")
            for item in labels_info:
                lbl = item["label"]
                cnt = session.run(f"MATCH (n:`{lbl}`) RETURN count(n) AS cnt").single()["cnt"]
                print(f"  :{lbl:<20} -> {cnt} nodes")

            # Breakdown by relationship type
            rels_info = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType").data()
            print("\n[RELATIONSHIP TYPES]")
            for item in rels_info:
                rtype = item["relationshipType"]
                cnt = session.run(f"MATCH ()-[r:`{rtype}`]->() RETURN count(r) AS cnt").single()["cnt"]
                print(f"  :{rtype:<20} -> {cnt} relationships")

            # 3. Constraints and Indexes
            constraints = session.run("SHOW CONSTRAINTS").data()
            indexes = session.run("SHOW INDEXES").data()
            print(f"\n[SCHEMA] Active Constraints: {len(constraints)}")
            for c in constraints:
                print(f"  - {c.get('name')}: {c.get('type')} on {c.get('labelsOrTypes')}({c.get('properties')})")

            print(f"\n[SCHEMA] Active Indexes: {len(indexes)}")
            for idx in indexes:
                print(f"  - {idx.get('name')}: {idx.get('type')} on {idx.get('labelsOrTypes')}({idx.get('properties')})")

            # 4. GDS Written Properties Check
            pr_cnt = session.run("MATCH (n) WHERE n.pagerank IS NOT NULL RETURN count(n) AS cnt").single()["cnt"]
            comm_cnt = session.run("MATCH (n) WHERE n.community IS NOT NULL RETURN count(n) AS cnt").single()["cnt"]
            print(f"\n[GDS PROPERTIES]")
            print(f"  Nodes with 'pagerank' property:  {pr_cnt}")
            print(f"  Nodes with 'community' property: {comm_cnt}")

            # Verification assertions
            assert node_cnt >= 100, f"Node count ({node_cnt}) is less than required 100"
            assert rel_cnt >= 200, f"Relationship count ({rel_cnt}) is less than required 200"
            assert len(constraints) >= 2, f"Constraints ({len(constraints)}) less than required 2"
            assert len(indexes) >= 2, f"Indexes ({len(indexes)}) less than required 2"

            print("\n[SUCCESS] All health and schema checks passed!")

        driver.close()
    except exceptions.ServiceUnavailable as e:
        print(f"\n[ERROR] Could not connect to Neo4j database: {e}")
        print("Please ensure the Neo4j container is running: docker ps --filter 'name=neo4j-lab09'")
        sys.exit(1)

if __name__ == "__main__":
    main()

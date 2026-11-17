"""
Run database setup, constraints creation, data import, idempotency check, and constraint violation demo.
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

IMPORT_DIR = Path(__file__).resolve().parent.parent / "import"

def run_cypher_file(session, file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split statements by semicolon, ignoring empty lines and comments
    statements = []
    current = []
    for line in content.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("//"):
            continue
        current.append(line)
        if trimmed.endswith(";"):
            stmt = "\n".join(current).rstrip(";").strip()
            if stmt:
                statements.append(stmt)
            current = []
    if current:
        stmt = "\n".join(current).rstrip(";").strip()
        if stmt:
            statements.append(stmt)

    for stmt in statements:
        session.run(stmt)

def main():
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    with driver.session() as session:
        print("[1] Clearing database...")
        session.run("MATCH (n) DETACH DELETE n")

        print("[2] Creating constraints and indexes...")
        run_cypher_file(session, IMPORT_DIR / "01_constraints_and_indexes.cypher")

        print("[3] First import pass (Nodes)...")
        run_cypher_file(session, IMPORT_DIR / "02_load_nodes.cypher")

        print("[4] First import pass (Relationships)...")
        run_cypher_file(session, IMPORT_DIR / "03_load_relationships.cypher")

        nodes_pass1 = session.run("MATCH (n) RETURN count(n) AS cnt").single()["cnt"]
        rels_pass1 = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt").single()["cnt"]
        print(f"Pass 1: Nodes = {nodes_pass1}, Relationships = {rels_pass1}")

        print("[5] Second import pass (Testing Idempotency)...")
        run_cypher_file(session, IMPORT_DIR / "02_load_nodes.cypher")
        run_cypher_file(session, IMPORT_DIR / "03_load_relationships.cypher")

        nodes_pass2 = session.run("MATCH (n) RETURN count(n) AS cnt").single()["cnt"]
        rels_pass2 = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt").single()["cnt"]
        print(f"Pass 2: Nodes = {nodes_pass2}, Relationships = {rels_pass2}")

        assert nodes_pass1 == nodes_pass2, "Idempotency failed: Node counts differ!"
        assert rels_pass1 == rels_pass2, "Idempotency failed: Relationship counts differ!"
        print("Idempotency verified: counts match perfectly.")

        print("\n[6] Listing active constraints:")
        constraints = session.run("SHOW CONSTRAINTS").data()
        for c in constraints:
            print(f" - {c.get('name')}: {c.get('type')} on {c.get('labelsOrTypes')}({c.get('properties')})")

        print("\n[7] Listing active indexes:")
        indexes = session.run("SHOW INDEXES").data()
        for idx in indexes:
            print(f" - {idx.get('name')}: {idx.get('type')} on {idx.get('labelsOrTypes')}({idx.get('properties')})")

        print("\n[8] Testing constraint violation...")
        try:
            session.run("""
                CREATE (s:Substation {
                    id: 'Substation_Vinnytska_750kV',
                    name: 'Дублікат ПС Вінницька 750 кВ',
                    voltageKV: 750.0
                })
            """)
            print("ERROR: Constraint violation did not trigger!")
            sys.exit(1)
        except exceptions.ClientError as ex:
            print(f"Success! Constraint violation triggered as expected:\n  Code: {ex.code}\n  Message: {ex.message}")

    driver.close()

if __name__ == "__main__":
    main()

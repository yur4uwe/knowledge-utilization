# Knowledge Repositories and Knowledge Utilization (Domain Knowledge Hub)

## Domain Overview

- **Economy Sector:** Energy
- **Thematic Area:** Energy System Management
- **Aim:** Gathering data on energy resources and flows
- **Short Description:** Modeling energy systems for resource planning, balancing, and optimization.

---

## Repository Architecture and Workflow

This repository serves as the central **Domain Knowledge Hub**, accumulating knowledge engineering assets, data pipelines, and validation systems across assignments.

### Git Branching Model
- `main`: Stable mainline branch containing verified and merged Hub infrastructure and baseline assets.
- `labXX`: Assignment-specific branches (e.g. `lab08`, `lab09`) created from `main`. Specific lab deliverables and evaluation criteria are developed and validated within their respective branches before being merged into main.

Lab branch cannot be deleted as it represents the definitive version of the assignment.

### Standard Directory Structure

The repository follows a standardized layout expected by the evaluation rubrics:

- `data/`: Knowledge base artifacts (RDF/Turtle graphs, JSON-LD, external link datasets).
- `queries/`: Query specifications (SPARQL, Cypher).
- `shapes/`: Schema validation constraints (SHACL shapes).
- `docs/`: Technical logs, execution reports, and evaluation summaries.
- `tests/`: Automated validation suites, benchmark datasets, and evaluation test cases.
- `claims/`: Claims verification matrix (`claims.csv`) tracking extracted or generated statements across verification levels (V1–V4).
- `llm_log/`: Verifiable audit logs for GenAI interactions (model, temperature, seed, prompt, output, human decisions).

---

## Python Environment Management with `uv`

The project uses [`uv`](https://docs.astral.sh/uv/)

### Prerequisites
- Python `>= 3.12`
- `uv` installed (regrettably, via `curl -LsSf https://astral.sh/uv/install.sh | sh` or system package manager)

### Quickstart

1. **Clone the repository and enter the directory:**
```bash
git clone https://github.com/yur4uwe/knowledge-utilization kms
cd kms
```

2. **Synchronize environment and install dependencies:**
`uv` automatically manages the virtual environment in `.venv/` and installs all locked dependencies:
```bash
uv sync
```

3. **Run scripts and tools:**
Execute scripts directly inside the managed environment without manual activation:
```bash
uv run python <script_path.py>
uv run pytest
```

4. **Adding new dependencies:**
To add runtime or development dependencies:
```bash
# Add runtime package
uv add <package_name>

# Add development package
uv add --dev <package_name>
```

5. **Updating dependencies:**
```bash
uv lock --upgrade
uv sync
```

---

## Claims Management

CLI tool for managing claims in the `claims/claims.csv` file. Please refer to `claim.bash --help` for further documentation and usage.
Claims must ONLY be managed via the CLI tool.

---

## Environment and Secrets Management

Configuration parameters and API credentials must be managed via local environment variables.

1. **Set up local environment file:**
```bash
cp .env.example .env
```
2. **Configure local values in `.env`:**
   Populate necessary endpoints (e.g., SPARQL triplestore endpoints, database connections) and LLM API keys.

> **Security Notice:** `.env` is ignored by version control. Never commit API keys, passwords, or sensitive infrastructure credentials to the repository.

---

## LLM-as-an-Expert Protocol

When utilizing LLM assistants for drafts, schema design, or queries:
1. **Audit Logs:** Log all prompt/response sessions into `llm_log/` including model identifier, temperature, and random seed.
2. **Claims Verification:** Record candidate assertions in `claims/claims.csv` specifying:
   - Claim text and type (fact, rule, hypothesis).
   - Source provenance.
   - Verification level (V1: citation check, V2: schema/syntax execution, V3: expert review, V4: benchmark metric).
   - Validation status (`verified`, `rejected`, `pending`).

---

## Lab 09: Knowledge Graph in Neo4j (Execution Pipeline)

All pipeline stages are implemented as standalone Python scripts in `src/` and `tests/`:

### 1. Launch Neo4j 5.x Container (Docker / Rancher Desktop)
```bash
docker run -d --name neo4j-lab09 \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  -e NEO4J_PLUGINS='["graph-data-science", "apoc"]' \
  -e NEO4J_dbms_security_procedures_unrestricted=gds.*,apoc.* \
  -e NEO4J_dbms_security_procedures_allowlist=gds.*,apoc.* \
  -e NEO4J_server_directories_import=/import \
  -v $(pwd)/data:/import:ro \
  neo4j:5
```

### 2. Pipeline Scripts in Repository
| Script Path | Description | Output Artifacts |
| :--- | :--- | :--- |
| `src/generate_graph_data.py` | Extracts all 26 entities from `data/kb.ttl` and supplements with Ukrainian grid topology | `data/nodes.csv`, `data/relationships.csv` |
| `src/run_import.py` | Applies constraints & indexes, imports data idempotently via `MERGE`, tests violation | Database state, constraint validation test |
| `src/run_queries.py` | Executes all 10 Cypher queries (CQ1–CQ8 + 2 Impact Analysis queries) | `docs/cypher_execution_results.json` |
| `src/run_gds.py` | Runs GDS PageRank & Louvain, writes properties to nodes, profiles queries | `docs/gds_profile_data.json` |
| `src/verify_graph.py` | Health check utility: verifies connection, counts, constraints, indexes, GDS properties | CLI verification report |
| `tests/eval_t2c.py` | Evaluates Text-to-Cypher pipeline with read-only, schema, and limit guardrails | `docs/t2c_eval_summary.json` |

### 3. Execution Commands
```bash
# Generate normalized CSV datasets from ontology:
uv run python src/generate_graph_data.py

# Import into Neo4j and verify constraints & idempotency:
uv run python src/run_import.py

# Execute analytical Cypher queries to competency questions:
uv run python src/run_queries.py

# Execute Graph Data Science algorithms (PageRank, Louvain) & profiling:
uv run python src/run_gds.py

# Run health check and graph integrity verification:
uv run python src/verify_graph.py

# Run Text-to-Cypher test suite:
uv run pytest tests/eval_t2c.py -v
```


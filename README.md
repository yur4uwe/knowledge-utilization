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

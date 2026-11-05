"""Wikidata SPARQL Client for executing and verifying queries."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import requests

WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"
DEFAULT_USER_AGENT = "DomainKnowledgeHub-SE08/1.0 (yur4uwe@gmail.com; educational research) Python/requests"
RESULTS_FILE = Path(__file__).resolve().parent.parent.parent / "reports" / "resources" / "se08_results.json"

logger = logging.getLogger(__name__)


class WikidataClient:
    """SPARQL client communicating with Wikidata Query Service."""

    def __init__(
        self,
        endpoint_url: str = WIKIDATA_SPARQL_URL,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: int = 30,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.user_agent = user_agent
        self.timeout = timeout

    def execute_query(self, sparql: str) -> Dict[str, Any]:
        """Execute a SPARQL query against Wikidata endpoint."""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/sparql-results+json",
        }
        params = {"query": sparql, "format": "json"}
        try:
            response = requests.get(
                self.endpoint_url,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e), "status_code": getattr(e.response, "status_code", None)}


def load_cached_results() -> Dict[str, Any]:
    """Load cached query results from JSON file."""
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cached_results(data: Dict[str, Any]) -> None:
    """Save query results to JSON cache."""
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

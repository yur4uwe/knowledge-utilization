"""W3C SKOS RDF serialization module using RDFLib.

Serializes BaseTaxonomy instances into RDF graphs conforming to the SKOS data model:
- skos:ConceptScheme
- skos:Concept
- skos:broader / skos:narrower
- skos:topConceptOf / skos:hasTopConcept
- skos:prefLabel
- skos:definition
"""

from __future__ import annotations

from pathlib import Path
from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import RDFS, SKOS

from src.se05.taxonomy_builder import BaseTaxonomy


class SkosExporter:
    """Exports a BaseTaxonomy to a SKOS RDF graph."""

    def __init__(self, taxonomy: BaseTaxonomy, base_uri: str = "http://example.org/energy/taxonomy#"):
        self.taxonomy = taxonomy
        self.base_uri = base_uri
        self.ns = Namespace(base_uri)

    def export_graph(self) -> Graph:
        g = Graph()
        g.bind("skos", SKOS)
        g.bind("rdfs", RDFS)
        g.bind("energy", self.ns)

        scheme_uri = self.ns[self.taxonomy.root_id]
        g.add((scheme_uri, RDF.type, SKOS.ConceptScheme))
        g.add((scheme_uri, RDFS.label, Literal(self.taxonomy.name, lang="uk")))

        root_node = self.taxonomy.get_node(self.taxonomy.root_id)
        if root_node:
            for top_child_id in root_node.children:
                top_uri = self.ns[top_child_id]
                g.add((scheme_uri, SKOS.hasTopConcept, top_uri))

        for node_id, node in self.taxonomy.nodes.items():
            node_uri = self.ns[node_id]
            g.add((node_uri, RDF.type, SKOS.Concept))
            g.add((node_uri, SKOS.prefLabel, Literal(node.name, lang="uk")))

            if node.metadata.get("name_en"):
                g.add((node_uri, SKOS.prefLabel, Literal(node.metadata["name_en"], lang="en")))

            if node.definition:
                g.add((node_uri, SKOS.definition, Literal(node.definition, lang="uk")))

            if node.parent_id and node.parent_id in self.taxonomy.nodes:
                parent_uri = self.ns[node.parent_id]
                g.add((node_uri, SKOS.broader, parent_uri))
                g.add((parent_uri, SKOS.narrower, node_uri))

            if node.parent_id == self.taxonomy.root_id:
                g.add((node_uri, SKOS.topConceptOf, scheme_uri))

        return g

    def save_turtle(self, destination: Path | str) -> str:
        """Serialize and save RDF graph in Turtle syntax."""
        g = self.export_graph()
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        g.serialize(destination=str(path), format="turtle")
        return str(path)

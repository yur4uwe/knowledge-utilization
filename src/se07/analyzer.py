"""Ontology Pitfall and OntoClean static analyzer using RDFLib."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

import rdflib
from rdflib.namespace import OWL, RDF, RDFS

from src.se07.models import (
    AuditReport,
    DefectCategory,
    OntologyDefect,
    SeverityLevel,
)

# OntoClean Rigidity Metadata Mapping for Power Systems Domain
# +R: Rigid kinds (essential to instance identity across all possible worlds)
# ~R: Anti-rigid roles / states (contingent, instance can stop having it without ceasing to exist)
RIGIDITY_KIND_MAP = {
    "GridAsset": "+R",
    "GenerationUnit": "+R",
    "NuclearPowerPlant": "+R",
    "ThermalPowerPlant": "+R",
    "HydroPowerPlant": "+R",
    "WindPowerPlant": "+R",
    "SolarPowerPlant": "+R",
    "BiomassPowerPlant": "+R",
    "NetworkInfra": "+R",
    "TransmissionLine": "+R",
    "OverheadLine": "+R",
    "UndergroundCable": "+R",
    "Substation": "+R",
    "PowerTransformer": "+R",
    "CircuitBreaker": "+R",
    "Busbar": "+R",
    "EnergyStorage": "+R",
    "BatteryStorageBESS": "+R",
    "PumpedStorageHydro": "+R",
    "EnergyConsumer": "+R",
    "IndustrialConsumer": "+R",
    "ResidentialConsumer": "+R",
    "CommercialConsumer": "+R",
    "SystemActor": "+R",
    "TransmissionSystemOperator": "+R",
    "DistributionSystemOperator": "+R",
    "ControlCenterDispatcher": "+R",
    "BalanceResponsibleParty": "+R",
}

RIGIDITY_ROLE_MAP = {
    "FaultedAsset": "~R",
    "ReserveAsset": "~R",
    "CurtailableLoad": "~R",
    "IsolatedNode": "~R",
}


class OntologyAnalyzer:
    """Analyzer implementing OOPS! checks, OntoClean rigidity validation, and DL satisfiability rules."""

    def __init__(self, ontology_path: str | Path):
        self.path = Path(ontology_path)
        self.graph = rdflib.Graph()
        self.graph.parse(str(self.path), format="turtle")
        self.ns = "http://www.semanticweb.org/ontologies/2026/energy-system#"

    def _local_name(self, uri: rdflib.URIRef | rdflib.Node) -> str:
        s = str(uri)
        if "#" in s:
            return s.split("#")[-1]
        return s.rstrip("/").split("/")[-1]

    def get_named_classes(self) -> List[rdflib.URIRef]:
        """Return all explicit named owl:Class nodes in the ontology."""
        classes = set()
        for s in self.graph.subjects(RDF.type, OWL.Class):
            if isinstance(s, rdflib.URIRef):
                classes.add(s)
        return sorted(list(classes), key=lambda x: str(x))

    def get_properties(self) -> List[rdflib.URIRef]:
        """Return all object and datatype properties."""
        props = set()
        for p_type in (OWL.ObjectProperty, OWL.DatatypeProperty):
            for s in self.graph.subjects(RDF.type, p_type):
                if isinstance(s, rdflib.URIRef):
                    props.add(s)
        return sorted(list(props), key=lambda x: str(x))

    def detect_disjoint_subsumption_conflicts(self) -> List[OntologyDefect]:
        """Check for classes subclassing multiple mutually disjoint parent classes (LOGICAL)."""
        defects = []
        # Find all disjoint sets
        disjoint_sets: List[Set[str]] = []
        for all_disjoint in self.graph.subjects(RDF.type, OWL.AllDisjointClasses):
            members_node = self.graph.value(all_disjoint, OWL.members)
            if members_node:
                members = set()
                for item in self.graph.items(members_node):
                    members.add(self._local_name(item))
                if members:
                    disjoint_sets.append(members)

        # Check explicit owl:disjointWith
        for s, _, o in self.graph.triples((None, OWL.disjointWith, None)):
            disjoint_sets.append({self._local_name(s), self._local_name(o)})

        # For every class, find all ancestors
        for cls in self.get_named_classes():
            cls_name = self._local_name(cls)
            parents = set(self._local_name(p) for p in self.graph.objects(cls, RDFS.subClassOf) if isinstance(p, rdflib.URIRef))
            for dset in disjoint_sets:
                intersect = parents.intersection(dset)
                if len(intersect) > 1:
                    defects.append(
                        OntologyDefect(
                            id=f"LOG-DISJ-{cls_name}",
                            category=DefectCategory.LOGICAL,
                            severity=SeverityLevel.CRITICAL,
                            entity_name=cls_name,
                            title="Unsatisfiable Class (Contradictory Disjoint Subsumption)",
                            description=(
                                f"Клас {cls_name} успадковує взаємовиключні класи {sorted(list(intersect))}, "
                                f"оголошені disjoint у базі знань. Клас є логічно суперечливим (equiv owl:Nothing)."
                            ),
                            remediation="Усунути множинне успадкування несумісних категорій або замінити на асоціативне відношення.",
                            oops_code="P19",
                            status="detected",
                        )
                    )
        return defects

    def detect_subclass_cycles(self) -> List[OntologyDefect]:
        """Check for cycles in the rdfs:subClassOf hierarchy (LOGICAL / OOPS! P06)."""
        defects = []
        subclass_graph: Dict[str, Set[str]] = {}
        for s, _, o in self.graph.triples((None, RDFS.subClassOf, None)):
            if isinstance(s, rdflib.URIRef) and isinstance(o, rdflib.URIRef):
                s_name = self._local_name(s)
                o_name = self._local_name(o)
                subclass_graph.setdefault(s_name, set()).add(o_name)

        # Direct 2-node cycles: A subClassOf B and B subClassOf A
        checked_pairs = set()
        for a, parents in subclass_graph.items():
            for b in parents:
                if b in subclass_graph and a in subclass_graph[b] and a != b:
                    pair = tuple(sorted([a, b]))
                    if pair not in checked_pairs:
                        checked_pairs.add(pair)
                        defects.append(
                            OntologyDefect(
                                id=f"LOG-CYCLE-{pair[0]}-{pair[1]}",
                                category=DefectCategory.LOGICAL,
                                severity=SeverityLevel.CRITICAL,
                                entity_name=f"{pair[0]} <-> {pair[1]}",
                                title="Cyclic Subclass Relationship",
                                description=(
                                    f"Виявлено циклічну ієрархію між класами {pair[0]} та {pair[1]}: "
                                    f"кожне поняття декларується прямим підкласом іншого (OOPS! P06)."
                                ),
                                remediation="Розірвати зворотне посилання subClassOf; зберегти лише прямий ієрархічний зв'язок.",
                                oops_code="P06",
                                status="detected",
                            )
                        )
        return defects

    def detect_naming_pitfalls(self) -> List[OntologyDefect]:
        """Check for inconsistent naming conventions (snake_case, verb names) (NAMING / OOPS! P22)."""
        defects = []
        for cls in self.get_named_classes():
            cls_name = self._local_name(cls)
            # Check for snake_case
            if "_" in cls_name and not cls_name.startswith("_"):
                defects.append(
                    OntologyDefect(
                        id=f"NAM-SNAKE-{cls_name}",
                        category=DefectCategory.NAMING,
                        severity=SeverityLevel.MAJOR,
                        entity_name=cls_name,
                        title="Inconsistent Naming Convention (snake_case used)",
                        description=(
                            f"Ідентифікатор класу :{cls_name} використовує стиль snake_case замість загальноприйнятого UpperCamelCase (OOPS! P22)."
                        ),
                        remediation="Перейменувати ідентифікатор у стандартний стиль UpperCamelCase (наприклад, :BatteryStorageBESS).",
                        oops_code="P22",
                        status="detected",
                    )
                )
            # Check for imperative verb phrases
            if cls_name.startswith("trip_") or cls_name.startswith("execute_"):
                defects.append(
                    OntologyDefect(
                        id=f"NAM-VERB-{cls_name}",
                        category=DefectCategory.NAMING,
                        severity=SeverityLevel.MAJOR,
                        entity_name=cls_name,
                        title="Imperative Verb Formulation for Concept Class",
                        description=(
                            f"Клас :{cls_name} названо наказовим дієсловом, що порушує онтологічну конвенцію "
                            "моделювання концептів іменниковими категоріями."
                        ),
                        remediation="Перейменувати на іменникову дію, наприклад :CircuitBreakerTripAction.",
                        oops_code="P22",
                        status="detected",
                    )
                )
        return defects

    def detect_documentation_pitfalls(self) -> List[OntologyDefect]:
        """Check for missing rdfs:comment, rdfs:label, or missing inverseOf (DOCUMENTATION / OOPS! P08, P13)."""
        defects = []
        # Missing annotations on classes
        for cls in self.get_named_classes():
            cls_name = self._local_name(cls)
            labels = list(self.graph.objects(cls, RDFS.label))
            comments = list(self.graph.objects(cls, RDFS.comment))

            if not labels:
                defects.append(
                    OntologyDefect(
                        id=f"DOC-NOLBL-{cls_name}",
                        category=DefectCategory.DOCUMENTATION,
                        severity=SeverityLevel.MINOR,
                        entity_name=cls_name,
                        title="Missing Human-Readable Label (rdfs:label)",
                        description=f"Клас :{cls_name} не містить жодної анотації rdfs:label (OOPS! P08).",
                        remediation="Додати локалізований ярлик rdfs:label@uk.",
                        oops_code="P08",
                        status="detected",
                    )
                )
            if not comments:
                defects.append(
                    OntologyDefect(
                        id=f"DOC-NOCOMM-{cls_name}",
                        category=DefectCategory.DOCUMENTATION,
                        severity=SeverityLevel.MINOR,
                        entity_name=cls_name,
                        title="Missing Ontological Documentation (rdfs:comment)",
                        description=f"Клас :{cls_name} не має описової анотації rdfs:comment (OOPS! P08).",
                        remediation="Додати інженерне визначення поняття в rdfs:comment@uk.",
                        oops_code="P08",
                        status="detected",
                    )
                )

        # Missing annotations on datatype properties
        for prop in self.graph.subjects(RDF.type, OWL.DatatypeProperty):
            if isinstance(prop, rdflib.URIRef):
                p_name = self._local_name(prop)
                comments = list(self.graph.objects(prop, RDFS.comment))
                if not comments:
                    defects.append(
                        OntologyDefect(
                            id=f"DOC-NODTCOMM-{p_name}",
                            category=DefectCategory.DOCUMENTATION,
                            severity=SeverityLevel.MINOR,
                            entity_name=p_name,
                            title="Missing Documentation on Datatype Property",
                            description=f"Властивість даних :{p_name} не містить анотації rdfs:comment (OOPS! P08).",
                            remediation="Додати коментар із зазначенням одиниць вимірювання та фізичного змісту.",
                            oops_code="P08",
                            status="detected",
                        )
                    )

        # Missing inverse object properties (OOPS! P13)
        asymmetric_props = [":suppliesPowerTo", ":protects"]
        for prop_str in asymmetric_props:
            prop_uri = rdflib.URIRef(f"{self.ns}{prop_str.lstrip(':')}")
            if (prop_uri, RDF.type, OWL.ObjectProperty) in self.graph:
                inverses = list(self.graph.objects(prop_uri, OWL.inverseOf))
                inv_subjects = list(self.graph.subjects(OWL.inverseOf, prop_uri))
                if not inverses and not inv_subjects:
                    defects.append(
                        OntologyDefect(
                            id=f"DOC-NOINV-{self._local_name(prop_uri)}",
                            category=DefectCategory.DOCUMENTATION,
                            severity=SeverityLevel.MAJOR,
                            entity_name=self._local_name(prop_uri),
                            title="Inverse Relationship Not Declared",
                            description=(
                                f"Об'єктна властивість :{self._local_name(prop_uri)} не має парного "
                                "експліцитного оголошення owl:inverseOf (OOPS! P13)."
                            ),
                            remediation="Оголосити відповідне зворотне відношення (наприклад, :isProtectedBy для :protects).",
                            oops_code="P13",
                            status="detected",
                        )
                    )
        return defects

    def detect_ontoclean_pitfalls(self) -> List[OntologyDefect]:
        """Check for OntoClean rigidity violations (+R subsumed by ~R) (ONTOCLEAN)."""
        defects = []
        for s, _, o in self.graph.triples((None, RDFS.subClassOf, None)):
            if isinstance(s, rdflib.URIRef) and isinstance(o, rdflib.URIRef):
                sub_name = self._local_name(s)
                sup_name = self._local_name(o)

                sub_rigidity = RIGIDITY_KIND_MAP.get(sub_name)
                sup_rigidity = RIGIDITY_ROLE_MAP.get(sup_name)

                # OntoClean Rigidity Constraint: +R cannot be a subclass of ~R
                if sub_rigidity == "+R" and sup_rigidity == "~R":
                    defects.append(
                        OntologyDefect(
                            id=f"ONT-RIGID-{sub_name}-{sup_name}",
                            category=DefectCategory.ONTOCLEAN,
                            severity=SeverityLevel.CRITICAL,
                            entity_name=f"{sub_name} subClassOf {sup_name}",
                            title="OntoClean Rigidity Inversion Violation (+R subClassOf ~R)",
                            description=(
                                f"Істотна жорстка сутність (Rigid Kind +R) '{sub_name}' підпорядкована "
                                f"анти-жорсткій ролі (Anti-rigid Role ~R) '{sup_name}'. За методологією Guarino & Welty (2002), "
                                "жорсткий концепт не може бути підкласом анти-жорсткого: це приписує ролеву ознаку як обов'язкову сутність."
                            ),
                            remediation=(
                                f"Перенести '{sub_name}' під рідний жорсткий батьківський клас (наприклад, :NetworkInfra), "
                                f"а роль '{sup_name}' моделювати через динамічне відношення або ситуаційний стан."
                            ),
                            oops_code="OntoClean-Rigidity",
                            status="detected",
                        )
                    )
        return defects

    def run_full_audit(self) -> AuditReport:
        """Run all pitfall detectors and compile an audit report."""
        named_classes = self.get_named_classes()
        properties = self.get_properties()
        axioms_count = len(self.graph)

        all_defects: List[OntologyDefect] = []
        all_defects.extend(self.detect_disjoint_subsumption_conflicts())
        all_defects.extend(self.detect_subclass_cycles())
        all_defects.extend(self.detect_naming_pitfalls())
        all_defects.extend(self.detect_documentation_pitfalls())
        all_defects.extend(self.detect_ontoclean_pitfalls())

        # Determine logical consistency
        is_consistent = not any(
            d.category == DefectCategory.LOGICAL and d.severity == SeverityLevel.CRITICAL
            for d in all_defects
        )

        version = str(self.graph.value(rdflib.URIRef(self.ns.rstrip("#")), OWL.versionInfo) or "unknown")

        return AuditReport(
            ontology_path=str(self.path),
            version=version,
            total_classes=len(named_classes),
            total_properties=len(properties),
            total_axioms=axioms_count,
            defects=all_defects,
            is_dl_consistent=is_consistent,
        )

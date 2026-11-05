"""Taxonomy construction module using Top-Down and Bottom-Up methods.

Includes:
- TaxonomyNode data structure
- TopDownTaxonomyBuilder (deductive classification)
- BottomUpTaxonomyBuilder (hierarchical agglomerative clustering)
- ExpertCIMTaxonomyBuilder (IEC 61970 CIM gold standard)
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class TaxonomyNode:
    """Represents a concept or category in a taxonomy tree."""

    id: str
    name: str
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    level: int = 0
    is_leaf: bool = False
    attributes: List[str] = field(default_factory=list)
    category_type: str = "category"  # "root", "category", "subcategory", "term"
    definition: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to serializable dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "children": self.children,
            "level": self.level,
            "is_leaf": self.is_leaf,
            "attributes": self.attributes,
            "category_type": self.category_type,
            "definition": self.definition,
            "metadata": self.metadata,
        }


class BaseTaxonomy:
    """Base class holding a graph of taxonomy nodes."""

    def __init__(self, name: str, root_id: str):
        self.name = name
        self.root_id = root_id
        self.nodes: Dict[str, TaxonomyNode] = {}

    def add_node(self, node: TaxonomyNode) -> None:
        """Add node to taxonomy, keeping parent-child links synchronized."""
        self.nodes[node.id] = node
        if node.parent_id and node.parent_id in self.nodes:
            parent = self.nodes[node.parent_id]
            if node.id not in parent.children:
                parent.children.append(node.id)

    def get_node(self, node_id: str) -> Optional[TaxonomyNode]:
        return self.nodes.get(node_id)

    def get_leaves(self) -> List[TaxonomyNode]:
        return [node for node in self.nodes.values() if node.is_leaf]

    def get_non_leaves(self) -> List[TaxonomyNode]:
        return [node for node in self.nodes.values() if not node.is_leaf]

    def compute_levels(self) -> None:
        """Recompute levels starting from root_id."""
        if self.root_id not in self.nodes:
            return

        def _assign_level(current_id: str, current_level: int):
            node = self.nodes[current_id]
            node.level = current_level
            for child_id in node.children:
                if child_id in self.nodes:
                    _assign_level(child_id, current_level + 1)

        _assign_level(self.root_id, 0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "root_id": self.root_id,
            "total_nodes": len(self.nodes),
            "leaf_count": len(self.get_leaves()),
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
        }


def load_terms(json_path: Path | str) -> List[Dict[str, Any]]:
    """Load term corpus from JSON file."""
    path = Path(json_path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class TopDownTaxonomyBuilder:
    """Constructs taxonomy deductively from general domain principles to specific terms."""

    def __init__(self, terms: List[Dict[str, Any]], inject_sample_defects: bool = False):
        self.terms = terms
        self.inject_sample_defects = inject_sample_defects

    def build(self) -> BaseTaxonomy:
        tax = BaseTaxonomy(
            name="TopDown_EnergySystem_Taxonomy",
            root_id="ROOT_TOP_DOWN",
        )

        # 0. Root
        root = TaxonomyNode(
            id="ROOT_TOP_DOWN",
            name="Управління енергетичними системами (Top-Down)",
            parent_id=None,
            level=0,
            category_type="root",
            definition="Верхній рівень предметної області управління електроенергетичними системами.",
        )
        tax.add_node(root)

        # 1. Level 1 Categories (Principle of Division: Functional Domain Areas)
        categories = [
            ("CAT_EQUIPMENT", "Фізичне обладнання підстанцій та мереж", [
                ("SUBCAT_TRANSFORMERS", "Трансформаторне устаткування"),
                ("SUBCAT_SWITCHING", "Комутаційне та вимикальне обладнання"),
                ("SUBCAT_LINES", "Лінії електропередачі та шини"),
                ("SUBCAT_COMPENSATION", "Пристрої компенсації реактивної потужності"),
                ("SUBCAT_INSTRUMENTATION", "Вимірювальні трансформатори та первинні датчики"),
            ]),
            ("CAT_GENERATION_STORAGE", "Активи генерації та накопичення", [
                ("SUBCAT_THERMAL_NUCLEAR", "Теплова та ядерна синхронна генерація"),
                ("SUBCAT_HYDRO", "Гідроенергетичні агрегати та ГАЕС"),
                ("SUBCAT_RENEWABLES", "Відновлювані джерела енергії (ВДЕ)"),
                ("SUBCAT_STORAGE", "Системи накопичення електроенергії"),
            ]),
            ("CAT_PROTECTION_AUTOMATION", "Релейний захист та протиаварійна автоматика", [
                ("SUBCAT_UNIT_PROTECTION", "Захисти основного обладнання"),
                ("SUBCAT_NETWORK_PROTECTION", "Ступеневі та мережеві захисти ліній"),
                ("SUBCAT_FREQUENCY_AUTOMATION", "Автоматика частотного розвантаження"),
                ("SUBCAT_RESTORATION", "Автоматика відновлення та перемикань"),
            ]),
            ("CAT_REGIME_PARAMETERS", "Режимні параметри та змінні стану", [
                ("SUBCAT_ELECTRICAL_VARS", "Електричні величини та фазові кути"),
                ("SUBCAT_OPERATIONAL_LIMITS", "Експлуатаційні та теплові обмеження"),
            ]),
            ("CAT_MARKET_BALANCING", "Балансуючі резерви та ринкові операції", [
                ("SUBCAT_ANCILLARY_RESERVES", "Допоміжні резерви підтримки та відновлення"),
                ("SUBCAT_DISPATCH_ACTIONS", "Диспетчерські дії та редиспатчинг"),
            ]),
            ("CAT_ANALYTICAL_EMS", "Аналітичні функції SCADA та EMS", [
                ("SUBCAT_STATE_SECURITY", "Оцінювання стану та аналіз стійкості N-1"),
                ("SUBCAT_OPTIMIZATION", "Оптимізація потокорозподілу"),
            ]),
            ("CAT_GRID_INCIDENTS", "Аварійні режими та збурення в мережі", [
                ("SUBCAT_FAULTS", "Короткі замикання та обриви фаз"),
                ("SUBCAT_INSTABILITY", "Динамічна нестійкість та системні аварії"),
                ("SUBCAT_DEGRADATION", "Діагностика деградації ізоляції"),
            ]),
        ]

        for cat_id, cat_name, subcats in categories:
            cat_node = TaxonomyNode(
                id=cat_id,
                name=cat_name,
                parent_id="ROOT_TOP_DOWN",
                level=1,
                category_type="category",
            )
            tax.add_node(cat_node)

            for subcat_id, subcat_name in subcats:
                subcat_node = TaxonomyNode(
                    id=subcat_id,
                    name=subcat_name,
                    parent_id=cat_id,
                    level=2,
                    category_type="subcategory",
                )
                tax.add_node(subcat_node)

        # Mapping of Term IDs to Top-Down subcategories
        term_mapping: Dict[str, str] = {
            # Equipment
            "TERM_01": "SUBCAT_TRANSFORMERS",
            "TERM_02": "SUBCAT_TRANSFORMERS",
            "TERM_03": "SUBCAT_TRANSFORMERS",
            "TERM_04": "SUBCAT_SWITCHING",
            "TERM_05": "SUBCAT_SWITCHING",
            "TERM_06": "SUBCAT_SWITCHING",
            "TERM_07": "SUBCAT_SWITCHING",
            "TERM_08": "SUBCAT_LINES",
            "TERM_09": "SUBCAT_LINES",
            "TERM_10": "SUBCAT_LINES",
            "TERM_16": "SUBCAT_LINES",
            "TERM_11": "SUBCAT_COMPENSATION",
            "TERM_12": "SUBCAT_COMPENSATION",
            "TERM_13": "SUBCAT_COMPENSATION",
            "TERM_14": "SUBCAT_COMPENSATION",
            "TERM_15": "SUBCAT_COMPENSATION",
            "TERM_17": "SUBCAT_INSTRUMENTATION",
            "TERM_18": "SUBCAT_INSTRUMENTATION",
            "TERM_19": "SUBCAT_INSTRUMENTATION",
            "TERM_20": "SUBCAT_INSTRUMENTATION",
            "TERM_21": "SUBCAT_INSTRUMENTATION",
            "TERM_22": "SUBCAT_INSTRUMENTATION",
            "TERM_23": "SUBCAT_INSTRUMENTATION",
            # Generation & Storage
            "TERM_24": "SUBCAT_THERMAL_NUCLEAR",
            "TERM_25": "SUBCAT_THERMAL_NUCLEAR",
            "TERM_26": "SUBCAT_THERMAL_NUCLEAR",
            "TERM_27": "SUBCAT_HYDRO",
            "TERM_28": "SUBCAT_HYDRO",
            "TERM_29": "SUBCAT_RENEWABLES",
            "TERM_30": "SUBCAT_RENEWABLES",
            "TERM_31": "SUBCAT_STORAGE",
            # Protection & Automation
            "TERM_32": "SUBCAT_UNIT_PROTECTION",
            "TERM_34": "SUBCAT_UNIT_PROTECTION",
            "TERM_33": "SUBCAT_NETWORK_PROTECTION",
            "TERM_35": "SUBCAT_NETWORK_PROTECTION",
            "TERM_41": "SUBCAT_NETWORK_PROTECTION",
            "TERM_36": "SUBCAT_FREQUENCY_AUTOMATION",
            "TERM_37": "SUBCAT_FREQUENCY_AUTOMATION",
            "TERM_38": "SUBCAT_FREQUENCY_AUTOMATION",
            "TERM_39": "SUBCAT_RESTORATION",
            "TERM_40": "SUBCAT_RESTORATION",
            # Regime parameters
            "TERM_42": "SUBCAT_ELECTRICAL_VARS",
            "TERM_43": "SUBCAT_ELECTRICAL_VARS",
            "TERM_44": "SUBCAT_ELECTRICAL_VARS",
            "TERM_45": "SUBCAT_ELECTRICAL_VARS",
            "TERM_46": "SUBCAT_ELECTRICAL_VARS",
            "TERM_47": "SUBCAT_OPERATIONAL_LIMITS",
            "TERM_48": "SUBCAT_OPERATIONAL_LIMITS",
            # Market & Balancing
            "TERM_49": "SUBCAT_ANCILLARY_RESERVES",
            "TERM_50": "SUBCAT_ANCILLARY_RESERVES",
            "TERM_51": "SUBCAT_ANCILLARY_RESERVES",
            "TERM_52": "SUBCAT_ANCILLARY_RESERVES",
            "TERM_53": "SUBCAT_DISPATCH_ACTIONS",
            # Analytical EMS
            "TERM_54": "SUBCAT_STATE_SECURITY",
            "TERM_55": "SUBCAT_STATE_SECURITY",
            "TERM_56": "SUBCAT_OPTIMIZATION",
            # Grid Incidents
            "TERM_57": "SUBCAT_FAULTS",
            "TERM_58": "SUBCAT_FAULTS",
            "TERM_64": "SUBCAT_FAULTS",
            "TERM_59": "SUBCAT_INSTABILITY",
            "TERM_60": "SUBCAT_INSTABILITY",
            "TERM_61": "SUBCAT_INSTABILITY",
            "TERM_62": "SUBCAT_INSTABILITY",
            "TERM_63": "SUBCAT_DEGRADATION",
        }

        # If sample defects are explicitly requested for comparative defect studies:
        if self.inject_sample_defects:
            # Defect 1: is-a vs part-of (attach Buchholz relay directly under Power Transformer)
            term_mapping["TERM_19"] = "SUBCAT_TRANSFORMERS"
            # Defect 3: Create uninformative 'Other' bucket and put BESS and FACTS there
            other_cat = TaxonomyNode(
                id="SUBCAT_OTHER",
                name="Інше некласифіковане обладнання",
                parent_id="CAT_EQUIPMENT",
                level=2,
                category_type="subcategory",
            )
            tax.add_node(other_cat)
            term_mapping["TERM_13"] = "SUBCAT_OTHER"
            term_mapping["TERM_31"] = "SUBCAT_OTHER"

        for term in self.terms:
            t_id = term["id"]
            parent_id = term_mapping.get(t_id, "SUBCAT_OTHER" if self.inject_sample_defects else "SUBCAT_LINES")
            leaf_node = TaxonomyNode(
                id=t_id,
                name=term["name_uk"],
                parent_id=parent_id,
                level=3,
                is_leaf=True,
                attributes=term.get("attributes", []),
                category_type="term",
                definition=term.get("definition", ""),
                metadata={"name_en": term.get("name_en", ""), "category_gold": term.get("category_gold", "")},
            )
            tax.add_node(leaf_node)

        tax.compute_levels()
        return tax


class BottomUpTaxonomyBuilder:
    """Constructs taxonomy inductively using Hierarchical Agglomerative Clustering (HAC)."""

    def __init__(self, terms: List[Dict[str, Any]], distance_threshold: float = 0.5):
        self.terms = terms
        self.distance_threshold = distance_threshold

    @staticmethod
    def _extract_feature_set(term: Dict[str, Any]) -> Set[str]:
        """Extract combined features: attributes + normalized definition tokens."""
        features = set(term.get("attributes", []))
        tokens = re.findall(r"\b[a-zA-Zа-яА-ЯіІїЇєЄґҐ0-9_-]{3,}\b", term.get("definition", "").lower())
        features.update(tokens)
        return features

    @classmethod
    def jaccard_distance(cls, set_a: Set[str], set_b: Set[str]) -> float:
        """Calculate Jaccard distance between two feature sets."""
        if not set_a and not set_b:
            return 0.0
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        if union == 0:
            return 1.0
        return 1.0 - (intersection / union)

    def build(self) -> BaseTaxonomy:
        tax = BaseTaxonomy(
            name="BottomUp_EnergySystem_Taxonomy",
            root_id="ROOT_BOTTOM_UP",
        )

        # 1. Initialize clusters: each term is an individual leaf cluster
        clusters: Dict[str, Dict[str, Any]] = {}
        term_nodes: Dict[str, TaxonomyNode] = {}

        for term in self.terms:
            t_id = term["id"]
            feat = self._extract_feature_set(term)
            node = TaxonomyNode(
                id=t_id,
                name=term["name_uk"],
                parent_id=None,
                level=0,
                is_leaf=True,
                attributes=term.get("attributes", []),
                category_type="term",
                definition=term.get("definition", ""),
                metadata={"name_en": term.get("name_en", ""), "category_gold": term.get("category_gold", "")},
            )
            term_nodes[t_id] = node
            tax.add_node(node)

            clusters[t_id] = {
                "id": t_id,
                "node_ids": [t_id],
                "feature_set": feat,
                "name": term["name_uk"],
            }

        # 2. Iterative Agglomerative Hierarchical Clustering
        cluster_counter = 1
        active_cluster_ids = list(clusters.keys())

        while len(active_cluster_ids) > 1:
            best_dist = float("inf")
            best_pair: Optional[Tuple[str, str]] = None

            for i in range(len(active_cluster_ids)):
                cid_a = active_cluster_ids[i]
                set_a = clusters[cid_a]["feature_set"]
                for j in range(i + 1, len(active_cluster_ids)):
                    cid_b = active_cluster_ids[j]
                    set_b = clusters[cid_b]["feature_set"]
                    dist = self.jaccard_distance(set_a, set_b)
                    if dist < best_dist:
                        best_dist = dist
                        best_pair = (cid_a, cid_b)

            if best_pair is None:
                break

            cid_a, cid_b = best_pair
            new_cid = f"CLUST_{cluster_counter:02d}"
            cluster_counter += 1

            # Determine dominant label from intersection or union of attributes
            union_features = clusters[cid_a]["feature_set"].union(clusters[cid_b]["feature_set"])
            inter_features = clusters[cid_a]["feature_set"].intersection(clusters[cid_b]["feature_set"])
            common_attrs = [f for f in inter_features if not f.startswith("0") and len(f) > 3]

            if common_attrs:
                label_suffix = f"({', '.join(sorted(common_attrs)[:2])})"
            else:
                label_suffix = f"(d={best_dist:.2f})"

            new_cluster_name = f"Кластер {new_cid} {label_suffix}"

            parent_node = TaxonomyNode(
                id=new_cid,
                name=new_cluster_name,
                parent_id=None,
                children=[cid_a, cid_b],
                level=0,
                is_leaf=False,
                category_type="category",
                metadata={"distance": best_dist, "merged": [cid_a, cid_b]},
            )
            tax.add_node(parent_node)

            # Update children's parent pointers
            tax.nodes[cid_a].parent_id = new_cid
            tax.nodes[cid_b].parent_id = new_cid

            # Register new cluster
            clusters[new_cid] = {
                "id": new_cid,
                "node_ids": clusters[cid_a]["node_ids"] + clusters[cid_b]["node_ids"],
                "feature_set": union_features,
                "name": new_cluster_name,
            }

            active_cluster_ids.remove(cid_a)
            active_cluster_ids.remove(cid_b)
            active_cluster_ids.append(new_cid)

        # Root of bottom-up is the last remaining cluster
        if active_cluster_ids:
            final_root_id = active_cluster_ids[0]
            tax.root_id = final_root_id
            tax.nodes[final_root_id].name = "Управління енергетичними системами (Bottom-Up HAC)"
            tax.nodes[final_root_id].category_type = "root"

        tax.compute_levels()
        return tax


class ExpertCIMTaxonomyBuilder:
    """Constructs the gold standard benchmark hierarchy based on IEC 61970 CIM."""

    def __init__(self, terms: List[Dict[str, Any]]):
        self.terms = terms

    def build(self) -> BaseTaxonomy:
        tax = BaseTaxonomy(
            name="IEC61970_CIM_Benchmark_Taxonomy",
            root_id="ROOT_IEC61970_CIM",
        )

        root = TaxonomyNode(
            id="ROOT_IEC61970_CIM",
            name="IEC 61970 Common Information Model (CIM)",
            parent_id=None,
            level=0,
            category_type="root",
        )
        tax.add_node(root)

        for term in self.terms:
            t_id = term["id"]
            cat_gold = term.get("category_gold", "IEC61970::General")
            parts = cat_gold.split("::")

            # Create package node (e.g. IEC61970::Wires)
            package_id = f"CIM_PKG_{parts[1]}" if len(parts) > 1 else "CIM_PKG_General"
            package_name = f"CIM Package: {parts[1]}" if len(parts) > 1 else "CIM Package: General"

            if package_id not in tax.nodes:
                pkg_node = TaxonomyNode(
                    id=package_id,
                    name=package_name,
                    parent_id="ROOT_IEC61970_CIM",
                    level=1,
                    category_type="category",
                )
                tax.add_node(pkg_node)

            # Create class node (e.g. IEC61970::Wires::Transformer)
            class_id = f"CIM_CLS_{'_'.join(parts[1:])}"
            class_name = f"CIM Class: {parts[-1]}"

            if class_id not in tax.nodes:
                cls_node = TaxonomyNode(
                    id=class_id,
                    name=class_name,
                    parent_id=package_id,
                    level=2,
                    category_type="subcategory",
                )
                tax.add_node(cls_node)

            # Add leaf term
            leaf_node = TaxonomyNode(
                id=t_id,
                name=term["name_uk"],
                parent_id=class_id,
                level=3,
                is_leaf=True,
                attributes=term.get("attributes", []),
                category_type="term",
                definition=term.get("definition", ""),
                metadata={"name_en": term.get("name_en", "")},
            )
            tax.add_node(leaf_node)

        tax.compute_levels()
        return tax

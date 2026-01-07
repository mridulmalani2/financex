#!/usr/bin/env python3
"""
Financial Lineage Graph - Production V1.0
==========================================
Graph-based financial provenance tracking.

ARCHITECTURE:
  Nodes = Financial facts (cells, concepts, values)
  Edges = Transformations (extraction, mapping, aggregation, calculation)

DESIGN PRINCIPLES:
1. Immutable nodes - once created, never modified
2. Versioned edges - can be superseded by analyst brain
3. Conditional edges - multiple paths, only one active
4. Full provenance - every value traceable to source

Graph Structure:
  SourceCellNode -> ExtractedNode -> MappedNode -> AggregatedNode -> CalculatedNode
       |               |                |               |                |
     Excel           messy          normalized        pivoted          DCF/LBO
"""

import json
import uuid
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from collections import defaultdict
import heapq


# =============================================================================
# NODE TYPES
# =============================================================================

class NodeType(Enum):
    """Types of nodes in the lineage graph."""
    SOURCE_CELL = "source_cell"           # Excel cell
    EXTRACTED = "extracted"                # messy_input.csv row
    MAPPED = "mapped"                      # normalized_financials.csv row
    AGGREGATED = "aggregated"              # Pivoted value (concept+period)
    CALCULATED = "calculated"              # Derived value (formula)


@dataclass
class FinancialNode:
    """
    A node in the financial lineage graph.
    Represents a single financial fact at a specific stage.
    """
    node_id: str                          # Unique identifier
    node_type: NodeType

    # Core data
    concept: Optional[str] = None         # XBRL concept (if known)
    label: Optional[str] = None           # Display label
    value: Any = None                     # The actual value
    period: Optional[str] = None          # Time period

    # Source information
    sheet_name: Optional[str] = None
    cell_ref: Optional[str] = None
    row_index: Optional[int] = None
    col_index: Optional[int] = None

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    session_id: str = ""

    # Status
    is_active: bool = True                # False if superseded

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "concept": self.concept,
            "label": self.label,
            "value": self.value,
            "period": self.period,
            "sheet_name": self.sheet_name,
            "cell_ref": self.cell_ref,
            "row_index": self.row_index,
            "col_index": self.col_index,
            "created_at": self.created_at,
            "session_id": self.session_id,
            "is_active": self.is_active
        }


# =============================================================================
# EDGE TYPES
# =============================================================================

class EdgeType(Enum):
    """Types of edges (transformations) in the graph."""
    EXTRACTION = "extraction"             # Excel -> Extracted
    MAPPING = "mapping"                   # Label -> Concept
    AGGREGATION = "aggregation"           # Many -> One
    CALCULATION = "calculation"           # Formula
    SUPERSEDED = "superseded"             # Replaced by analyst brain


class MappingSource(Enum):
    """Source of a mapping decision."""
    ANALYST_BRAIN = "analyst_brain"       # Tier 0
    ALIAS = "alias"                       # Tier 1
    EXACT_LABEL = "exact_label"           # Tier 2
    KEYWORD = "keyword"                   # Tier 3
    HIERARCHY = "hierarchy"               # Tier 4 (safe mode)
    UNMAPPED = "unmapped"                 # Failed


class AggregationStrategy(Enum):
    """Strategy used for aggregation."""
    TOTAL_LINE_USED = "total_line_used"         # Detected total, used it
    COMPONENT_SUM = "component_sum"             # Summed components
    MAX_VALUE = "max_value"                     # Multiple totals, used max
    SINGLE_VALUE = "single_value"               # Only one value present


@dataclass
class FinancialEdge:
    """
    An edge in the financial lineage graph.
    Represents a transformation from source node(s) to target node.
    """
    edge_id: str                          # Unique identifier
    edge_type: EdgeType

    # Graph structure
    source_node_ids: List[str]            # Can be many-to-one
    target_node_id: str

    # Transformation metadata
    method: str                           # Human-readable method
    confidence: float = 1.0               # 0.0 to 1.0
    source: Optional[MappingSource] = None

    # Conditional edges (for hierarchy-aware aggregation)
    is_active: bool = True                # False if path not taken
    condition: Optional[str] = None       # Why this path was/wasn't taken

    # Aggregation details (if applicable)
    aggregation_strategy: Optional[AggregationStrategy] = None
    excluded_source_ids: List[str] = field(default_factory=list)  # Excluded to prevent double-counting

    # Formula details (if applicable)
    formula: Optional[str] = None
    formula_inputs: Dict[str, float] = field(default_factory=dict)

    # Alternatives (for audit trail)
    alternatives_considered: List[Dict] = field(default_factory=list)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str = "system"
    session_id: str = ""

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "edge_id": self.edge_id,
            "edge_type": self.edge_type.value,
            "source_node_ids": self.source_node_ids,
            "target_node_id": self.target_node_id,
            "method": self.method,
            "confidence": self.confidence,
            "source": self.source.value if self.source else None,
            "is_active": self.is_active,
            "condition": self.condition,
            "aggregation_strategy": self.aggregation_strategy.value if self.aggregation_strategy else None,
            "excluded_source_ids": self.excluded_source_ids,
            "formula": self.formula,
            "formula_inputs": self.formula_inputs,
            "alternatives_considered": self.alternatives_considered,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "session_id": self.session_id
        }


# =============================================================================
# GRAPH STRUCTURE
# =============================================================================

class FinancialLineageGraph:
    """
    In-memory graph database for financial lineage.

    Supports:
    - Many-to-one (aggregation)
    - One-to-many (splitting)
    - Conditional edges (hierarchy-aware resolution)
    - Graph traversal (forward/backward)
    - Path finding (how did we get here?)
    """

    def __init__(self, session_id: str, source_file: str):
        self.session_id = session_id
        self.source_file = source_file
        self.created_at = datetime.utcnow().isoformat()

        # Core storage
        self.nodes: Dict[str, FinancialNode] = {}
        self.edges: Dict[str, FinancialEdge] = {}

        # Adjacency lists for fast traversal
        self._outgoing: Dict[str, Set[str]] = defaultdict(set)  # node_id -> edge_ids
        self._incoming: Dict[str, Set[str]] = defaultdict(set)  # node_id -> edge_ids

        # Indexes for fast queries
        self._by_type: Dict[NodeType, Set[str]] = defaultdict(set)
        self._by_concept: Dict[str, Set[str]] = defaultdict(set)
        self._by_period: Dict[str, Set[str]] = defaultdict(set)
        self._by_cell: Dict[Tuple[str, int, int], str] = {}  # (sheet, row, col) -> node_id

        # Metadata
        self.metadata = {
            "session_id": session_id,
            "source_file": source_file,
            "created_at": self.created_at,
            "total_nodes": 0,
            "total_edges": 0,
            "active_edges": 0
        }

    # =========================================================================
    # CRUD OPERATIONS
    # =========================================================================

    def add_node(self, node: FinancialNode) -> str:
        """Add a node to the graph."""
        node_id = node.node_id
        self.nodes[node_id] = node

        # Update indexes
        self._by_type[node.node_type].add(node_id)
        if node.concept:
            self._by_concept[node.concept].add(node_id)
        if node.period:
            self._by_period[node.period].add(node_id)
        if node.sheet_name and node.row_index is not None and node.col_index is not None:
            key = (node.sheet_name, node.row_index, node.col_index)
            self._by_cell[key] = node_id

        self.metadata["total_nodes"] = len(self.nodes)
        return node_id

    def add_edge(self, edge: FinancialEdge) -> str:
        """Add an edge to the graph."""
        edge_id = edge.edge_id
        self.edges[edge_id] = edge

        # Update adjacency lists
        for source_id in edge.source_node_ids:
            self._outgoing[source_id].add(edge_id)
        self._incoming[edge.target_node_id].add(edge_id)

        # Update metadata
        self.metadata["total_edges"] = len(self.edges)
        if edge.is_active:
            self.metadata["active_edges"] = sum(1 for e in self.edges.values() if e.is_active)

        return edge_id

    def get_node(self, node_id: str) -> Optional[FinancialNode]:
        """Get node by ID."""
        return self.nodes.get(node_id)

    def get_edge(self, edge_id: str) -> Optional[FinancialEdge]:
        """Get edge by ID."""
        return self.edges.get(edge_id)

    def deactivate_edge(self, edge_id: str, reason: str = ""):
        """
        Mark an edge as inactive (path not taken).
        Used for conditional edges in hierarchy-aware aggregation.
        """
        edge = self.edges.get(edge_id)
        if edge:
            edge.is_active = False
            edge.condition = reason
            self.metadata["active_edges"] = sum(1 for e in self.edges.values() if e.is_active)

    def supersede_edge(self, old_edge_id: str, new_edge_id: str, reason: str = "analyst_brain_override"):
        """
        Mark an edge as superseded by a new edge.
        Used when analyst brain overrides system mapping.
        """
        old_edge = self.edges.get(old_edge_id)
        new_edge = self.edges.get(new_edge_id)

        if old_edge and new_edge:
            old_edge.is_active = False
            old_edge.condition = f"Superseded by {new_edge_id}: {reason}"

            # Create superseded edge
            superseded = FinancialEdge(
                edge_id=f"superseded_{uuid.uuid4().hex[:8]}",
                edge_type=EdgeType.SUPERSEDED,
                source_node_ids=[old_edge_id],
                target_node_id=new_edge_id,
                method="superseded",
                condition=reason,
                session_id=self.session_id
            )
            self.add_edge(superseded)

    # =========================================================================
    # GRAPH TRAVERSAL
    # =========================================================================

    def get_outgoing_edges(self, node_id: str, active_only: bool = True) -> List[FinancialEdge]:
        """Get all edges leaving a node."""
        edge_ids = self._outgoing.get(node_id, set())
        edges = [self.edges[eid] for eid in edge_ids if eid in self.edges]
        if active_only:
            edges = [e for e in edges if e.is_active]
        return edges

    def get_incoming_edges(self, node_id: str, active_only: bool = True) -> List[FinancialEdge]:
        """Get all edges entering a node."""
        edge_ids = self._incoming.get(node_id, set())
        edges = [self.edges[eid] for eid in edge_ids if eid in self.edges]
        if active_only:
            edges = [e for e in edges if e.is_active]
        return edges

    def get_children(self, node_id: str, active_only: bool = True) -> List[FinancialNode]:
        """Get all child nodes (nodes this node flows to)."""
        edges = self.get_outgoing_edges(node_id, active_only)
        children = []
        for edge in edges:
            target = self.nodes.get(edge.target_node_id)
            if target:
                children.append(target)
        return children

    def get_parents(self, node_id: str, active_only: bool = True) -> List[FinancialNode]:
        """Get all parent nodes (nodes that flow into this one)."""
        edges = self.get_incoming_edges(node_id, active_only)
        parents = []
        for edge in edges:
            for source_id in edge.source_node_ids:
                source = self.nodes.get(source_id)
                if source:
                    parents.append(source)
        return parents

    def trace_forward(self, node_id: str, max_depth: int = 100, active_only: bool = True) -> List[FinancialNode]:
        """
        Trace forward from a node to find all descendants.
        Returns nodes in breadth-first order.
        """
        visited = set()
        queue = [(node_id, 0)]
        result = []

        while queue:
            current_id, depth = queue.pop(0)

            if current_id in visited or depth > max_depth:
                continue

            visited.add(current_id)
            node = self.nodes.get(current_id)
            if node:
                result.append(node)

            # Add children to queue
            for child in self.get_children(current_id, active_only):
                if child.node_id not in visited:
                    queue.append((child.node_id, depth + 1))

        return result

    def trace_backward(self, node_id: str, max_depth: int = 100, active_only: bool = True) -> List[FinancialNode]:
        """
        Trace backward from a node to find all ancestors.
        Returns nodes in reverse order (closest ancestors first).
        """
        visited = set()
        queue = [(node_id, 0)]
        result = []

        while queue:
            current_id, depth = queue.pop(0)

            if current_id in visited or depth > max_depth:
                continue

            visited.add(current_id)
            node = self.nodes.get(current_id)
            if node:
                result.append(node)

            # Add parents to queue
            for parent in self.get_parents(current_id, active_only):
                if parent.node_id not in visited:
                    queue.append((parent.node_id, depth + 1))

        return result

    def find_path(self, source_id: str, target_id: str, active_only: bool = True) -> Optional[List[Tuple[FinancialNode, FinancialEdge]]]:
        """
        Find shortest path from source to target.
        Returns list of (node, edge) pairs, or None if no path exists.

        Uses Dijkstra's algorithm with confidence as edge weight.
        """
        # Priority queue: (negative_confidence, node_id, path)
        pq = [(0.0, source_id, [])]
        visited = set()

        while pq:
            neg_conf, current_id, path = heapq.heappop(pq)

            if current_id in visited:
                continue

            visited.add(current_id)

            # Found target
            if current_id == target_id:
                return path

            # Explore neighbors
            for edge in self.get_outgoing_edges(current_id, active_only):
                if edge.target_node_id not in visited:
                    node = self.nodes.get(current_id)
                    new_path = path + [(node, edge)]
                    # Use negative confidence as priority (higher confidence = lower priority value)
                    priority = neg_conf - edge.confidence
                    heapq.heappush(pq, (priority, edge.target_node_id, new_path))

        return None  # No path found

    # =========================================================================
    # QUERIES
    # =========================================================================

    def query_nodes_by_type(self, node_type: NodeType) -> List[FinancialNode]:
        """Get all nodes of a specific type."""
        node_ids = self._by_type.get(node_type, set())
        return [self.nodes[nid] for nid in node_ids if nid in self.nodes]

    def query_nodes_by_concept(self, concept: str, period: Optional[str] = None) -> List[FinancialNode]:
        """Get all nodes for a concept, optionally filtered by period."""
        node_ids = self._by_concept.get(concept, set())

        if period:
            period_ids = self._by_period.get(period, set())
            node_ids = node_ids & period_ids

        return [self.nodes[nid] for nid in node_ids if nid in self.nodes]

    def query_node_by_cell(self, sheet: str, row: int, col: int) -> Optional[FinancialNode]:
        """Get node for a specific Excel cell."""
        key = (sheet, row, col)
        node_id = self._by_cell.get(key)
        return self.nodes.get(node_id) if node_id else None

    def query_aggregations_with_conflicts(self) -> List[Tuple[FinancialNode, List[FinancialEdge]]]:
        """
        Find all aggregations where conflicts were detected.
        Returns list of (target_node, [inactive_edges]) pairs.
        """
        results = []

        for node in self.query_nodes_by_type(NodeType.AGGREGATED):
            incoming = self.get_incoming_edges(node.node_id, active_only=False)
            inactive = [e for e in incoming if not e.is_active and e.edge_type == EdgeType.AGGREGATION]

            if inactive:
                results.append((node, inactive))

        return results

    def query_analyst_brain_overrides(self) -> List[Tuple[FinancialNode, FinancialEdge]]:
        """Find all mappings that used analyst brain."""
        results = []

        for edge in self.edges.values():
            if edge.source == MappingSource.ANALYST_BRAIN and edge.is_active:
                target = self.nodes.get(edge.target_node_id)
                if target:
                    results.append((target, edge))

        return results

    def query_low_confidence_mappings(self, threshold: float = 0.7) -> List[Tuple[FinancialNode, FinancialEdge]]:
        """Find mappings with confidence below threshold."""
        results = []

        for edge in self.edges.values():
            if edge.edge_type == EdgeType.MAPPING and edge.confidence < threshold and edge.is_active:
                target = self.nodes.get(edge.target_node_id)
                if target:
                    results.append((target, edge))

        return results

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def to_dict(self) -> Dict:
        """Serialize entire graph to dictionary."""
        return {
            "metadata": self.metadata,
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "edges": {eid: edge.to_dict() for eid, edge in self.edges.items()}
        }

    def to_json(self, filepath: str):
        """Export graph to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_dict(cls, data: Dict) -> 'FinancialLineageGraph':
        """Deserialize graph from dictionary."""
        metadata = data["metadata"]
        graph = cls(metadata["session_id"], metadata["source_file"])

        # Load nodes
        for node_data in data["nodes"].values():
            node = FinancialNode(
                node_id=node_data["node_id"],
                node_type=NodeType(node_data["node_type"]),
                concept=node_data.get("concept"),
                label=node_data.get("label"),
                value=node_data.get("value"),
                period=node_data.get("period"),
                sheet_name=node_data.get("sheet_name"),
                cell_ref=node_data.get("cell_ref"),
                row_index=node_data.get("row_index"),
                col_index=node_data.get("col_index"),
                created_at=node_data["created_at"],
                session_id=node_data["session_id"],
                is_active=node_data["is_active"]
            )
            graph.add_node(node)

        # Load edges
        for edge_data in data["edges"].values():
            edge = FinancialEdge(
                edge_id=edge_data["edge_id"],
                edge_type=EdgeType(edge_data["edge_type"]),
                source_node_ids=edge_data["source_node_ids"],
                target_node_id=edge_data["target_node_id"],
                method=edge_data["method"],
                confidence=edge_data["confidence"],
                source=MappingSource(edge_data["source"]) if edge_data.get("source") else None,
                is_active=edge_data["is_active"],
                condition=edge_data.get("condition"),
                aggregation_strategy=AggregationStrategy(edge_data["aggregation_strategy"]) if edge_data.get("aggregation_strategy") else None,
                excluded_source_ids=edge_data.get("excluded_source_ids", []),
                formula=edge_data.get("formula"),
                formula_inputs=edge_data.get("formula_inputs", {}),
                alternatives_considered=edge_data.get("alternatives_considered", []),
                created_at=edge_data["created_at"],
                created_by=edge_data["created_by"],
                session_id=edge_data["session_id"]
            )
            graph.add_edge(edge)

        return graph

    @classmethod
    def from_json(cls, filepath: str) -> 'FinancialLineageGraph':
        """Load graph from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

    # =========================================================================
    # GRAPH STATISTICS
    # =========================================================================

    def get_statistics(self) -> Dict:
        """Get graph statistics for reporting."""
        stats = {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "active_edges": sum(1 for e in self.edges.values() if e.is_active),
            "inactive_edges": sum(1 for e in self.edges.values() if not e.is_active),
            "nodes_by_type": {
                nt.value: len(self._by_type[nt])
                for nt in NodeType
            },
            "edges_by_type": defaultdict(int),
            "mapping_sources": defaultdict(int),
            "aggregation_strategies": defaultdict(int),
            "avg_confidence": 0.0
        }

        # Edge statistics
        confidence_sum = 0.0
        confidence_count = 0

        for edge in self.edges.values():
            stats["edges_by_type"][edge.edge_type.value] += 1

            if edge.source:
                stats["mapping_sources"][edge.source.value] += 1

            if edge.aggregation_strategy:
                stats["aggregation_strategies"][edge.aggregation_strategy.value] += 1

            if edge.is_active:
                confidence_sum += edge.confidence
                confidence_count += 1

        if confidence_count > 0:
            stats["avg_confidence"] = confidence_sum / confidence_count

        return dict(stats)


# =============================================================================
# GRAPH BUILDER (Integration Helper)
# =============================================================================

class LineageGraphBuilder:
    """
    Helper class to build lineage graph during pipeline execution.
    Simplifies integration with existing FinanceX pipeline.
    """

    def __init__(self, session_id: str, source_file: str):
        self.graph = FinancialLineageGraph(session_id, source_file)
        self._node_counter = 0
        self._edge_counter = 0

    def _generate_node_id(self, prefix: str) -> str:
        """Generate unique node ID."""
        self._node_counter += 1
        return f"{self.graph.session_id}:{prefix}:{self._node_counter:08d}"

    def _generate_edge_id(self, prefix: str) -> str:
        """Generate unique edge ID."""
        self._edge_counter += 1
        return f"{self.graph.session_id}:{prefix}:{self._edge_counter:08d}"

    def add_source_cell(self, sheet: str, row: int, col: int, cell_ref: str,
                       value: Any, label: Optional[str] = None) -> str:
        """Add a source Excel cell node."""
        node = FinancialNode(
            node_id=self._generate_node_id("cell"),
            node_type=NodeType.SOURCE_CELL,
            label=label,
            value=value,
            sheet_name=sheet,
            cell_ref=cell_ref,
            row_index=row,
            col_index=col,
            session_id=self.graph.session_id
        )
        return self.graph.add_node(node)

    def add_extraction(self, source_cell_id: str, extracted_label: str,
                      extracted_value: Any, period: str) -> Tuple[str, str]:
        """Add extraction node and edge."""
        # Create extracted node
        node = FinancialNode(
            node_id=self._generate_node_id("extracted"),
            node_type=NodeType.EXTRACTED,
            label=extracted_label,
            value=extracted_value,
            period=period,
            session_id=self.graph.session_id
        )
        node_id = self.graph.add_node(node)

        # Create extraction edge
        edge = FinancialEdge(
            edge_id=self._generate_edge_id("extract"),
            edge_type=EdgeType.EXTRACTION,
            source_node_ids=[source_cell_id],
            target_node_id=node_id,
            method="excel_extraction",
            confidence=1.0,
            session_id=self.graph.session_id
        )
        edge_id = self.graph.add_edge(edge)

        return node_id, edge_id

    def add_mapping(self, extracted_node_id: str, concept: str,
                   mapping_method: str, mapping_source: MappingSource,
                   confidence: float, alternatives: List[Dict] = None) -> Tuple[str, str]:
        """Add mapping node and edge."""
        # Create mapped node
        extracted = self.graph.get_node(extracted_node_id)
        node = FinancialNode(
            node_id=self._generate_node_id("mapped"),
            node_type=NodeType.MAPPED,
            concept=concept,
            label=extracted.label if extracted else None,
            value=extracted.value if extracted else None,
            period=extracted.period if extracted else None,
            session_id=self.graph.session_id
        )
        node_id = self.graph.add_node(node)

        # Create mapping edge
        edge = FinancialEdge(
            edge_id=self._generate_edge_id("map"),
            edge_type=EdgeType.MAPPING,
            source_node_ids=[extracted_node_id],
            target_node_id=node_id,
            method=mapping_method,
            confidence=confidence,
            source=mapping_source,
            alternatives_considered=alternatives or [],
            session_id=self.graph.session_id
        )
        edge_id = self.graph.add_edge(edge)

        return node_id, edge_id

    def add_aggregation(self, mapped_node_ids: List[str], concept: str,
                       period: str, final_value: float, strategy: AggregationStrategy,
                       excluded_ids: List[str] = None, condition: str = "") -> Tuple[str, str]:
        """Add aggregation node and edge (many-to-one)."""
        # Create aggregated node
        node = FinancialNode(
            node_id=self._generate_node_id("agg"),
            node_type=NodeType.AGGREGATED,
            concept=concept,
            value=final_value,
            period=period,
            session_id=self.graph.session_id
        )
        node_id = self.graph.add_node(node)

        # Create aggregation edge
        edge = FinancialEdge(
            edge_id=self._generate_edge_id("agg"),
            edge_type=EdgeType.AGGREGATION,
            source_node_ids=mapped_node_ids,
            target_node_id=node_id,
            method=f"aggregation_{strategy.value}",
            confidence=1.0,
            aggregation_strategy=strategy,
            excluded_source_ids=excluded_ids or [],
            condition=condition,
            session_id=self.graph.session_id
        )
        edge_id = self.graph.add_edge(edge)

        return node_id, edge_id

    def add_calculation(self, source_node_ids: List[str], result_label: str,
                       formula: str, inputs: Dict[str, float], result_value: float,
                       period: str) -> Tuple[str, str]:
        """Add calculation node and edge."""
        # Create calculated node
        node = FinancialNode(
            node_id=self._generate_node_id("calc"),
            node_type=NodeType.CALCULATED,
            label=result_label,
            value=result_value,
            period=period,
            session_id=self.graph.session_id
        )
        node_id = self.graph.add_node(node)

        # Create calculation edge
        edge = FinancialEdge(
            edge_id=self._generate_edge_id("calc"),
            edge_type=EdgeType.CALCULATION,
            source_node_ids=source_node_ids,
            target_node_id=node_id,
            method="formula",
            confidence=1.0,
            formula=formula,
            formula_inputs=inputs,
            session_id=self.graph.session_id
        )
        edge_id = self.graph.add_edge(edge)

        return node_id, edge_id


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Example: Build a simple lineage graph
    builder = LineageGraphBuilder("session_123", "apple_10k.xlsx")

    # 1. Source cells
    cell1_id = builder.add_source_cell("Income Statement", 5, 2, "C6", 100000, "Total Net Sales")
    cell2_id = builder.add_source_cell("Income Statement", 6, 2, "C7", 60000, "Product Sales")
    cell3_id = builder.add_source_cell("Income Statement", 7, 2, "C8", 40000, "Service Sales")

    # 2. Extraction
    ext1_id, _ = builder.add_extraction(cell1_id, "Total Net Sales", 100000, "2023")
    ext2_id, _ = builder.add_extraction(cell2_id, "Product Sales", 60000, "2023")
    ext3_id, _ = builder.add_extraction(cell3_id, "Service Sales", 40000, "2023")

    # 3. Mapping
    map1_id, _ = builder.add_mapping(ext1_id, "us-gaap_Revenues", "Alias Match",
                                     MappingSource.ALIAS, 1.0)
    map2_id, _ = builder.add_mapping(ext2_id, "us-gaap_Revenues", "Keyword Match",
                                     MappingSource.KEYWORD, 0.8)
    map3_id, _ = builder.add_mapping(ext3_id, "us-gaap_Revenues", "Keyword Match",
                                     MappingSource.KEYWORD, 0.8)

    # 4. Aggregation (hierarchy-aware: use total, not sum of components)
    agg_id, agg_edge_id = builder.add_aggregation(
        [map1_id, map2_id, map3_id],
        "us-gaap_Revenues",
        "2023",
        100000,
        AggregationStrategy.TOTAL_LINE_USED,
        excluded_ids=[map2_id, map3_id],
        condition="Total line detected, components excluded to prevent double-counting"
    )

    # 5. Query the graph
    graph = builder.graph

    print("=== Graph Statistics ===")
    stats = graph.get_statistics()
    print(f"Total nodes: {stats['total_nodes']}")
    print(f"Total edges: {stats['total_edges']}")
    print(f"Active edges: {stats['active_edges']}")
    print()

    print("=== Trace backward from aggregated Revenue ===")
    ancestors = graph.trace_backward(agg_id)
    for node in ancestors:
        print(f"  {node.node_type.value}: {node.label or node.concept} = {node.value}")
    print()

    print("=== Find path from source cell to aggregated value ===")
    path = graph.find_path(cell1_id, agg_id)
    if path:
        for node, edge in path:
            print(f"  {node.node_type.value} --[{edge.method}]--> ", end="")
        print(f"{graph.get_node(path[-1][1].target_node_id).node_type.value}")
    print()

    print("=== Aggregations with conflicts ===")
    conflicts = graph.query_aggregations_with_conflicts()
    print(f"Found {len(conflicts)} aggregations with conflicts")
    print()

    # Export graph
    graph.to_json("lineage_graph_example.json")
    print("Graph exported to lineage_graph_example.json")

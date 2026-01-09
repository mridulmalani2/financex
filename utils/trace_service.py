#!/usr/bin/env python3
"""
Trace Service - Production Traceability API
============================================
Provides high-level APIs for retrieving financial value traces,
dependency graphs, and transformation histories.

This is the main interface between the lineage graph and the UI.
"""

import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from utils.lineage_graph import (
    FinancialLineageGraph,
    FinancialNode,
    FinancialEdge,
    NodeType,
    EdgeType,
    MappingSource,
    AggregationStrategy
)


# =============================================================================
# TRACE DATA MODELS (UI-Ready)
# =============================================================================

@dataclass
class SourceInfo:
    """Source information for a value."""
    origin: str  # "excel_upload", "user_override", "system_derived"
    cell_ref: Optional[str] = None
    sheet_name: Optional[str] = None
    row: Optional[int] = None
    col: Optional[int] = None
    file_name: Optional[str] = None
    raw_value: Any = None

    # Taxonomy info
    concept: Optional[str] = None
    standard_label: Optional[str] = None
    taxonomy: Optional[str] = None  # "US_GAAP", "IFRS"

    # Mapping details
    mapping_rule_id: Optional[str] = None
    mapping_rule_name: Optional[str] = None
    mapping_tier: Optional[str] = None  # "Analyst Brain", "Alias", "Exact Match", etc.
    was_user_edited: bool = False

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TransformationStep:
    """A single transformation step."""
    step_number: int
    operation: str  # "extraction", "mapping", "aggregation", "calculation"
    formula: Optional[str] = None
    inputs: Dict[str, Any] = None
    output: Any = None
    confidence: float = 1.0
    reasoning: Optional[str] = None  # Why this transformation was applied

    def to_dict(self) -> Dict:
        result = asdict(self)
        if self.inputs is None:
            result['inputs'] = {}
        return result


@dataclass
class DecisionPath:
    """Decision path showing why a mapping was chosen."""
    chosen_mapping: str
    mapping_source: str  # "analyst_brain", "alias", "exact_label", etc.
    confidence: float
    alternatives: List[Dict[str, Any]]  # Alternative mappings that were considered
    reasoning: str  # Human-readable explanation
    analyst_override: bool = False

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DependencyNode:
    """A node in the dependency graph."""
    node_id: str
    node_type: str
    label: Optional[str]
    value: Any
    concept: Optional[str]
    period: Optional[str]
    is_active: bool
    confidence: float

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DependencyEdge:
    """An edge in the dependency graph."""
    edge_id: str
    source_id: str
    target_id: str
    edge_type: str
    method: str
    confidence: float
    is_active: bool
    formula: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class LineageTrace:
    """Complete lineage trace for a value (UI-ready)."""
    value_id: str
    final_value: Any
    label: Optional[str]
    concept: Optional[str]
    period: Optional[str]

    # Trace components
    source: SourceInfo
    transformations: List[TransformationStep]
    decision_path: Optional[DecisionPath]

    # Dependencies
    upstream_dependencies: List[str]  # Node IDs
    downstream_dependencies: List[str]  # Node IDs

    # Analyst Brain
    analyst_corrections: List[Dict[str, Any]]  # History of corrections

    # Metadata
    created_at: str
    session_id: str
    is_local_only: bool = True  # Always True - data is local

    def to_dict(self) -> Dict:
        return {
            "value_id": self.value_id,
            "final_value": self.final_value,
            "label": self.label,
            "concept": self.concept,
            "period": self.period,
            "source": self.source.to_dict(),
            "transformations": [t.to_dict() for t in self.transformations],
            "decision_path": self.decision_path.to_dict() if self.decision_path else None,
            "upstream_dependencies": self.upstream_dependencies,
            "downstream_dependencies": self.downstream_dependencies,
            "analyst_corrections": self.analyst_corrections,
            "is_local_only": self.is_local_only,
            "created_at": self.created_at,
            "session_id": self.session_id
        }


# =============================================================================
# TRACE SERVICE
# =============================================================================

class TraceService:
    """
    High-level service for trace retrieval and analysis.

    This is the main interface between the lineage graph and the UI.
    Provides rich, UI-ready trace objects.
    """

    def __init__(self, lineage_graph: FinancialLineageGraph, brain_manager=None):
        """
        Initialize trace service.

        Args:
            lineage_graph: The financial lineage graph
            brain_manager: Optional Analyst Brain manager for correction history
        """
        self.graph = lineage_graph
        self.brain_manager = brain_manager

    # =========================================================================
    # MAIN TRACE RETRIEVAL
    # =========================================================================

    def get_trace(self, node_id: str) -> Optional[LineageTrace]:
        """
        Get complete trace for a node.

        This is the main entry point for UI trace retrieval.
        Returns a rich LineageTrace object with all details.
        """
        node = self.graph.get_node(node_id)
        if not node:
            return None

        # Get source info
        source = self._build_source_info(node_id)

        # Get transformation history
        transformations = self._build_transformation_history(node_id)

        # Get decision path (if mapped)
        decision_path = self._build_decision_path(node_id)

        # Get dependencies
        upstream_deps = [n.node_id for n in self.graph.get_parents(node_id, active_only=True)]
        downstream_deps = [n.node_id for n in self.graph.get_children(node_id, active_only=True)]

        # Get analyst corrections
        analyst_corrections = self._get_analyst_corrections(node)

        return LineageTrace(
            value_id=node_id,
            final_value=node.value,
            label=node.label,
            concept=node.concept,
            period=node.period,
            source=source,
            transformations=transformations,
            decision_path=decision_path,
            upstream_dependencies=upstream_deps,
            downstream_dependencies=downstream_deps,
            analyst_corrections=analyst_corrections,
            is_local_only=True,
            created_at=node.created_at,
            session_id=node.session_id
        )

    def get_trace_by_concept_period(self, concept: str, period: str) -> Optional[LineageTrace]:
        """Get trace for a specific concept and period."""
        nodes = self.graph.query_nodes_by_concept(concept, period)

        # Get the most recent aggregated or calculated node
        for node_type in [NodeType.CALCULATED, NodeType.AGGREGATED]:
            for node in nodes:
                if node.node_type == node_type and node.is_active:
                    return self.get_trace(node.node_id)

        # Fallback to any active node
        for node in nodes:
            if node.is_active:
                return self.get_trace(node.node_id)

        return None

    # =========================================================================
    # DEPENDENCY GRAPH
    # =========================================================================

    def get_dependency_graph(self, node_id: str, max_depth: int = 5, direction: str = "both") -> Dict[str, Any]:
        """
        Get dependency graph for visualization.

        Args:
            node_id: Starting node
            max_depth: Maximum depth to traverse
            direction: "upstream", "downstream", or "both"

        Returns:
            Dict with 'nodes' and 'edges' lists for graph visualization
        """
        nodes_dict = {}
        edges_list = []

        # Collect nodes based on direction
        if direction in ["upstream", "both"]:
            ancestors = self.graph.trace_backward(node_id, max_depth=max_depth)
            for node in ancestors:
                nodes_dict[node.node_id] = self._node_to_dependency_node(node)

        if direction in ["downstream", "both"]:
            descendants = self.graph.trace_forward(node_id, max_depth=max_depth)
            for node in descendants:
                nodes_dict[node.node_id] = self._node_to_dependency_node(node)

        # Collect edges between collected nodes
        for nid in nodes_dict.keys():
            for edge in self.graph.get_incoming_edges(nid, active_only=True):
                # Only include edge if both source and target are in our node set
                all_sources_included = all(sid in nodes_dict for sid in edge.source_node_ids)
                if all_sources_included:
                    edges_list.append(self._edge_to_dependency_edge(edge))

        return {
            "nodes": [n.to_dict() for n in nodes_dict.values()],
            "edges": [e.to_dict() for e in edges_list],
            "root_node_id": node_id
        }

    def get_reverse_dependencies(self, node_id: str) -> List[str]:
        """Get all nodes that depend on this node (downstream)."""
        descendants = self.graph.trace_forward(node_id, max_depth=100)
        return [n.node_id for n in descendants if n.node_id != node_id]

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _build_source_info(self, node_id: str) -> SourceInfo:
        """Build source information by tracing back to origin."""
        node = self.graph.get_node(node_id)
        if not node:
            return SourceInfo(origin="unknown")

        # Trace back to find source cell
        ancestors = self.graph.trace_backward(node_id, max_depth=100)

        source_cell = None
        extracted = None
        mapped = None

        for ancestor in ancestors:
            if ancestor.node_type == NodeType.SOURCE_CELL:
                source_cell = ancestor
            elif ancestor.node_type == NodeType.EXTRACTED:
                extracted = ancestor
            elif ancestor.node_type == NodeType.MAPPED:
                mapped = ancestor

        # Determine origin
        origin = "system_derived"
        was_user_edited = False

        if source_cell:
            origin = "excel_upload"

        # Check for analyst brain override
        mapping_edge = None
        for edge in self.graph.get_incoming_edges(node_id, active_only=True):
            if edge.edge_type == EdgeType.MAPPING:
                mapping_edge = edge
                if edge.source == MappingSource.ANALYST_BRAIN:
                    was_user_edited = True
                    origin = "user_override"
                break

        return SourceInfo(
            origin=origin,
            cell_ref=source_cell.cell_ref if source_cell else None,
            sheet_name=source_cell.sheet_name if source_cell else None,
            row=source_cell.row_index if source_cell else None,
            col=source_cell.col_index if source_cell else None,
            file_name=self.graph.source_file,
            raw_value=source_cell.value if source_cell else None,
            concept=mapped.concept if mapped else node.concept,
            standard_label=node.label,
            taxonomy="US_GAAP",  # TODO: Get from concept
            mapping_rule_id=mapping_edge.edge_id if mapping_edge else None,
            mapping_rule_name=mapping_edge.method if mapping_edge else None,
            mapping_tier=mapping_edge.source.value if (mapping_edge and mapping_edge.source) else None,
            was_user_edited=was_user_edited
        )

    def _build_transformation_history(self, node_id: str) -> List[TransformationStep]:
        """Build step-by-step transformation history."""
        transformations = []

        # Find path from source to this node
        ancestors = self.graph.trace_backward(node_id, max_depth=100)

        # Find source cell
        source_id = None
        for ancestor in ancestors:
            if ancestor.node_type == NodeType.SOURCE_CELL:
                source_id = ancestor.node_id
                break

        if not source_id:
            return transformations

        # Find path
        path = self.graph.find_path(source_id, node_id, active_only=True)
        if not path:
            return transformations

        # Build transformations from path
        step_num = 1
        for node, edge in path:
            transformation = self._edge_to_transformation_step(edge, step_num)
            if transformation:
                transformations.append(transformation)
                step_num += 1

        return transformations

    def _edge_to_transformation_step(self, edge: FinancialEdge, step_num: int) -> Optional[TransformationStep]:
        """Convert edge to transformation step."""
        operation_map = {
            EdgeType.EXTRACTION: "extraction",
            EdgeType.MAPPING: "mapping",
            EdgeType.AGGREGATION: "aggregation",
            EdgeType.CALCULATION: "calculation"
        }

        operation = operation_map.get(edge.edge_type, "unknown")

        # Get inputs
        inputs = {}
        for source_id in edge.source_node_ids:
            source_node = self.graph.get_node(source_id)
            if source_node:
                key = source_node.label or source_node.concept or source_id
                inputs[key] = source_node.value

        # Get output
        target_node = self.graph.get_node(edge.target_node_id)
        output = target_node.value if target_node else None

        # Build reasoning
        reasoning = self._build_reasoning(edge)

        return TransformationStep(
            step_number=step_num,
            operation=operation,
            formula=edge.formula,
            inputs=inputs or edge.formula_inputs,
            output=output,
            confidence=edge.confidence,
            reasoning=reasoning
        )

    def _build_reasoning(self, edge: FinancialEdge) -> str:
        """Build human-readable reasoning for an edge."""
        if edge.edge_type == EdgeType.EXTRACTION:
            return "Extracted from Excel file"

        elif edge.edge_type == EdgeType.MAPPING:
            if edge.source == MappingSource.ANALYST_BRAIN:
                return f"Mapped via Analyst Brain (Tier 0) - User override"
            elif edge.source == MappingSource.ALIAS:
                return f"Mapped via Alias (Tier 1) - Exact match in aliases.csv"
            elif edge.source == MappingSource.EXACT_LABEL:
                return f"Mapped via Exact Label (Tier 2) - Found in taxonomy database"
            elif edge.source == MappingSource.KEYWORD:
                return f"Mapped via Keyword (Tier 3) - Fuzzy match on keywords"
            elif edge.source == MappingSource.HIERARCHY:
                return f"Mapped via Hierarchy (Tier 4) - Safe mode fallback"
            else:
                return f"Mapped via {edge.method}"

        elif edge.edge_type == EdgeType.AGGREGATION:
            if edge.aggregation_strategy == AggregationStrategy.TOTAL_LINE_USED:
                excluded_count = len(edge.excluded_source_ids)
                return f"Detected total line, used it directly. Excluded {excluded_count} component(s) to prevent double-counting"
            elif edge.aggregation_strategy == AggregationStrategy.COMPONENT_SUM:
                return f"Summed {len(edge.source_node_ids)} component values"
            elif edge.aggregation_strategy == AggregationStrategy.MAX_VALUE:
                return f"Multiple totals found, used maximum value"
            elif edge.aggregation_strategy == AggregationStrategy.SINGLE_VALUE:
                return "Single value for this concept and period"
            else:
                return f"Aggregated via {edge.aggregation_strategy}"

        elif edge.edge_type == EdgeType.CALCULATION:
            return f"Calculated using formula: {edge.formula or 'custom calculation'}"

        return edge.condition or edge.method

    def _build_decision_path(self, node_id: str) -> Optional[DecisionPath]:
        """Build decision path for mapping decisions."""
        # Find mapping edge
        mapping_edge = None
        for edge in self.graph.get_incoming_edges(node_id, active_only=True):
            if edge.edge_type == EdgeType.MAPPING:
                mapping_edge = edge
                break

        if not mapping_edge:
            # Check ancestors
            ancestors = self.graph.trace_backward(node_id, max_depth=10)
            for ancestor in ancestors:
                for edge in self.graph.get_incoming_edges(ancestor.node_id, active_only=True):
                    if edge.edge_type == EdgeType.MAPPING:
                        mapping_edge = edge
                        break
                if mapping_edge:
                    break

        if not mapping_edge:
            return None

        target = self.graph.get_node(mapping_edge.target_node_id)

        return DecisionPath(
            chosen_mapping=target.concept if target else "unknown",
            mapping_source=mapping_edge.source.value if mapping_edge.source else "unknown",
            confidence=mapping_edge.confidence,
            alternatives=mapping_edge.alternatives_considered,
            reasoning=self._build_reasoning(mapping_edge),
            analyst_override=(mapping_edge.source == MappingSource.ANALYST_BRAIN)
        )

    def _get_analyst_corrections(self, node: FinancialNode) -> List[Dict[str, Any]]:
        """Get analyst correction history from Brain Manager."""
        corrections = []

        if not self.brain_manager:
            return corrections

        # Check if this node's label has correction history
        if node.label:
            mapping = self.brain_manager.get_mapping(node.label)
            if mapping:
                corrections.append({
                    "source_label": node.label,
                    "target_concept": mapping.get("target_element_id"),
                    "created_at": mapping.get("created_at"),
                    "created_by": mapping.get("created_by"),
                    "notes": mapping.get("notes", "")
                })

        return corrections

    def _node_to_dependency_node(self, node: FinancialNode) -> DependencyNode:
        """Convert FinancialNode to DependencyNode (UI-friendly)."""
        return DependencyNode(
            node_id=node.node_id,
            node_type=node.node_type.value,
            label=node.label,
            value=node.value,
            concept=node.concept,
            period=node.period,
            is_active=node.is_active,
            confidence=node.confidence
        )

    def _edge_to_dependency_edge(self, edge: FinancialEdge) -> DependencyEdge:
        """Convert FinancialEdge to DependencyEdge (UI-friendly)."""
        # Create one edge per source (for visualization)
        # If multiple sources, this will be called multiple times
        source_id = edge.source_node_ids[0] if edge.source_node_ids else ""

        return DependencyEdge(
            edge_id=edge.edge_id,
            source_id=source_id,
            target_id=edge.target_node_id,
            edge_type=edge.edge_type.value,
            method=edge.method,
            confidence=edge.confidence,
            is_active=edge.is_active,
            formula=edge.formula
        )

    # =========================================================================
    # SEARCH & QUERY
    # =========================================================================

    def search_traces_by_label(self, label: str) -> List[LineageTrace]:
        """Search for traces by label (fuzzy match)."""
        traces = []

        for node in self.graph.nodes.values():
            if node.label and label.lower() in node.label.lower():
                trace = self.get_trace(node.node_id)
                if trace:
                    traces.append(trace)

        return traces

    def get_all_low_confidence_traces(self, threshold: float = 0.7) -> List[LineageTrace]:
        """Get all traces with confidence below threshold."""
        traces = []

        low_conf_mappings = self.graph.query_low_confidence_mappings(threshold)
        for node, edge in low_conf_mappings:
            trace = self.get_trace(node.node_id)
            if trace:
                traces.append(trace)

        return traces

    def get_analyst_brain_traces(self) -> List[LineageTrace]:
        """Get all traces that used analyst brain."""
        traces = []

        brain_overrides = self.graph.query_analyst_brain_overrides()
        for node, edge in brain_overrides:
            trace = self.get_trace(node.node_id)
            if trace:
                traces.append(trace)

        return traces


# =============================================================================
# INTERACTION TRACKER
# =============================================================================

class InteractionTracker:
    """
    Tracks user interactions with traces for debugging and reproducibility.

    NOT analytics - this is for:
    - Reproducibility (what did the analyst look at?)
    - Debuggability (what path did they take?)
    - Explainability (what influenced their decision?)
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.interactions = []
        self.started_at = datetime.utcnow().isoformat()

    def track_click(self, node_id: str, label: Optional[str], value: Any):
        """Track when user clicks on a value."""
        self.interactions.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "click",
            "node_id": node_id,
            "label": label,
            "value": value
        })

    def track_trace_view(self, node_id: str, trace_depth: int):
        """Track when user views a trace."""
        self.interactions.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "view_trace",
            "node_id": node_id,
            "trace_depth": trace_depth
        })

    def track_dependency_exploration(self, from_node_id: str, to_node_id: str, direction: str):
        """Track when user explores dependencies."""
        self.interactions.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "explore_dependency",
            "from_node_id": from_node_id,
            "to_node_id": to_node_id,
            "direction": direction
        })

    def export_log(self, filepath: str):
        """Export interaction log for reproducibility."""
        log = {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "ended_at": datetime.utcnow().isoformat(),
            "total_interactions": len(self.interactions),
            "interactions": self.interactions
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(log, f, indent=2)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of interactions."""
        action_counts = {}
        for interaction in self.interactions:
            action = interaction["action"]
            action_counts[action] = action_counts.get(action, 0) + 1

        return {
            "session_id": self.session_id,
            "total_interactions": len(self.interactions),
            "action_counts": action_counts,
            "started_at": self.started_at
        }

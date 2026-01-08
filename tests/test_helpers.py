#!/usr/bin/env python3
"""
Test Helper Classes
===================
Simplified wrappers for testing purposes.
"""

import sys
import os
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.lineage_graph import (
    FinancialLineageGraph,
    LineageGraphBuilder,
    FinancialNode,
    FinancialEdge,
    NodeType,
    EdgeType,
    MappingSource,
    AggregationStrategy,
)


class LineageGraph:
    """Simplified wrapper for FinancialLineageGraph for testing."""

    def __init__(self):
        """Initialize with default session and source file."""
        self.session_id = str(uuid.uuid4())
        self.source_file = "test.xlsx"
        self.builder = LineageGraphBuilder(self.session_id, self.source_file)
        self.graph = self.builder.graph

    def add_node(self, node_type: NodeType, data: dict) -> str:
        """Add a node with simplified interface."""
        node_id = f"{self.session_id}:{node_type.value}:{uuid.uuid4().hex[:8]}"

        node = FinancialNode(
            node_id=node_id,
            node_type=node_type,
            concept=data.get('concept'),
            label=data.get('label'),
            value=data.get('value'),
            period=data.get('period'),
            sheet_name=data.get('sheet_name'),
            cell_ref=data.get('cell_ref'),
            row_index=data.get('row_index'),
            col_index=data.get('col_index'),
            confidence=data.get('confidence', 1.0),
            session_id=self.session_id
        )

        self.graph.add_node(node)
        return node_id

    def add_edge(self, edge_type: EdgeType, source_node_ids: list, target_node_id: str,
                 method: str, confidence: float = 1.0, **kwargs) -> str:
        """Add an edge with simplified interface."""
        edge_id = f"{self.session_id}:{edge_type.value}:{uuid.uuid4().hex[:8]}"

        edge = FinancialEdge(
            edge_id=edge_id,
            edge_type=edge_type,
            source_node_ids=source_node_ids,
            target_node_id=target_node_id,
            method=method,
            confidence=confidence,
            source=kwargs.get('source'),
            aggregation_strategy=kwargs.get('aggregation_strategy'),
            formula=kwargs.get('formula'),
            session_id=self.session_id
        )

        self.graph.add_edge(edge)
        return edge_id

    def get_node(self, node_id: str) -> FinancialNode:
        """Get a node by ID."""
        return self.graph.get_node(node_id)

    def get_edge(self, edge_id: str) -> FinancialEdge:
        """Get an edge by ID."""
        return self.graph.get_edge(edge_id)

    def trace_backward(self, node_id: str) -> list:
        """Trace backward from a node."""
        return self.graph.trace_backward(node_id)

    def trace_forward(self, node_id: str) -> list:
        """Trace forward from a node."""
        return self.graph.trace_forward(node_id)

    def find_path(self, source_id: str, target_id: str):
        """Find path between two nodes."""
        result = self.graph.find_path(source_id, target_id)
        if result is None:
            return None
        # Convert to list of nodes
        return [node for node, edge in result] + [self.graph.get_node(result[-1][1].target_node_id)]

    def query_nodes_by_type(self, node_type: NodeType):
        """Query nodes by type."""
        return self.graph.query_nodes_by_type(node_type)

    def query_all_nodes(self):
        """Query all nodes."""
        return self.graph.nodes.values()

    def get_all_edges(self):
        """Get all edges."""
        return self.graph.edges

    def get_incoming_edges(self, node_id: str):
        """Get incoming edges for a node."""
        return self.graph.get_incoming_edges(node_id)

    def to_json(self) -> str:
        """Export to JSON string."""
        import json
        data = self.graph.to_dict()
        return json.dumps(data, indent=2)

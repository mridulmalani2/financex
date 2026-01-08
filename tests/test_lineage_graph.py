#!/usr/bin/env python3
"""
Unit Tests for Lineage Graph - Production V1.0
===============================================
Comprehensive test suite for lineage graph operations.

Target: >95% code coverage

Test Categories:
1. Graph completeness (C1.1-C1.5)
2. Edge integrity (C2.1-C2.5)
3. Query correctness (C3.1-C3.3)
4. Node creation and management
5. Edge creation and validation
"""

import unittest
import sys
import os
import json
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.lineage_graph import (
    NodeType,
    EdgeType,
    MappingSource,
    AggregationStrategy,
)
from test_helpers import LineageGraph


class TestGraphCompleteness(unittest.TestCase):
    """Test graph completeness guarantees (C1.1-C1.5)."""

    def setUp(self):
        """Create a sample lineage graph for testing."""
        self.graph = LineageGraph()

        # Create SOURCE_CELL node
        self.source_id = self.graph.add_node(
            node_type=NodeType.SOURCE_CELL,
            data={
                "sheet_name": "Income Statement",
                "cell_ref": "A1",
                "value": "Revenue",
                "label": "Revenue"
            }
        )

        # Create EXTRACTED node
        self.extracted_id = self.graph.add_node(
            node_type=NodeType.EXTRACTED,
            data={
                "label": "Revenue",
                "value": 1000000
            }
        )

        # Link SOURCE_CELL -> EXTRACTED
        self.graph.add_edge(
            edge_type=EdgeType.EXTRACTION,
            source_node_ids=[self.source_id],
            target_node_id=self.extracted_id,
            method="Excel cell extraction",
            confidence=1.0
        )

        # Create MAPPED node
        self.mapped_id = self.graph.add_node(
            node_type=NodeType.MAPPED,
            data={
                "concept": "us-gaap:Revenues",
                "label": "Revenue",
                "value": 1000000
            }
        )

        # Link EXTRACTED -> MAPPED
        self.graph.add_edge(
            edge_type=EdgeType.MAPPING,
            source_node_ids=[self.extracted_id],
            target_node_id=self.mapped_id,
            method="Exact label match",
            confidence=0.90,
            source=MappingSource.EXACT_LABEL
        )

    def test_all_extracted_nodes_have_source_cells(self):
        """C1.1: Every EXTRACTED node has ≥1 SOURCE_CELL ancestor."""
        extracted_nodes = self.graph.query_nodes_by_type(NodeType.EXTRACTED)
        for node in extracted_nodes:
            ancestors = self.graph.trace_backward(node.node_id)
            source_cells = [n for n in ancestors if n.node_type == NodeType.SOURCE_CELL]
            self.assertGreater(len(source_cells), 0,
                             f"EXTRACTED node {node.node_id} has no SOURCE_CELL ancestor")

    def test_all_mapped_nodes_have_extracted_ancestors(self):
        """C1.2: Every MAPPED node has ≥1 EXTRACTED ancestor."""
        mapped_nodes = self.graph.query_nodes_by_type(NodeType.MAPPED)
        for node in mapped_nodes:
            ancestors = self.graph.trace_backward(node.node_id)
            extracted = [n for n in ancestors if n.node_type == NodeType.EXTRACTED]
            self.assertGreater(len(extracted), 0,
                             f"MAPPED node {node.node_id} has no EXTRACTED ancestor")

    def test_aggregated_nodes_have_mapped_ancestors(self):
        """C1.3: Every AGGREGATED node has ≥1 MAPPED ancestor."""
        # Create AGGREGATED node for testing
        agg_id = self.graph.add_node(
            node_type=NodeType.AGGREGATED,
            data={
                "concept": "us-gaap:Revenues",
                "period": "2024-Q1",
                "value": 1000000
            }
        )

        self.graph.add_edge(
            edge_type=EdgeType.AGGREGATION,
            source_node_ids=[self.mapped_id],
            target_node_id=agg_id,
            method="Single value aggregation",
            confidence=0.90,
            aggregation_strategy=AggregationStrategy.SINGLE_VALUE
        )

        aggregated_nodes = self.graph.query_nodes_by_type(NodeType.AGGREGATED)
        for node in aggregated_nodes:
            ancestors = self.graph.trace_backward(node.node_id)
            mapped = [n for n in ancestors if n.node_type == NodeType.MAPPED]
            self.assertGreater(len(mapped), 0,
                             f"AGGREGATED node {node.node_id} has no MAPPED ancestor")

    def test_calculated_nodes_have_required_ancestors(self):
        """C1.4: Every CALCULATED node has ≥1 AGGREGATED or CALCULATED ancestor."""
        # Create AGGREGATED node
        agg_id = self.graph.add_node(
            node_type=NodeType.AGGREGATED,
            data={
                "concept": "us-gaap:Revenues",
                "period": "2024-Q1",
                "value": 1000000
            }
        )

        self.graph.add_edge(
            edge_type=EdgeType.AGGREGATION,
            source_node_ids=[self.mapped_id],
            target_node_id=agg_id,
            method="Single value aggregation",
            confidence=0.90
        )

        # Create CALCULATED node
        calc_id = self.graph.add_node(
            node_type=NodeType.CALCULATED,
            data={
                "concept": "Revenue_Growth",
                "value": 0.05,
                "formula": "(Current - Previous) / Previous"
            }
        )

        self.graph.add_edge(
            edge_type=EdgeType.CALCULATION,
            source_node_ids=[agg_id],
            target_node_id=calc_id,
            method="Growth rate calculation",
            confidence=0.90,
            formula="(Current - Previous) / Previous"
        )

        calculated_nodes = self.graph.query_nodes_by_type(NodeType.CALCULATED)
        for node in calculated_nodes:
            ancestors = self.graph.trace_backward(node.node_id)
            valid_ancestors = [n for n in ancestors
                             if n.node_type in [NodeType.AGGREGATED, NodeType.CALCULATED]]
            self.assertGreater(len(valid_ancestors), 0,
                             f"CALCULATED node {node.node_id} has no valid ancestors")

    def test_no_orphan_nodes(self):
        """C1.5: Zero orphan nodes (nodes with no ancestors except SOURCE_CELL)."""
        all_nodes = self.graph.query_all_nodes()
        for node in all_nodes:
            if node.node_type == NodeType.SOURCE_CELL:
                continue  # SOURCE_CELL nodes are roots, can have no ancestors

            ancestors = self.graph.trace_backward(node.node_id)
            self.assertGreater(len(ancestors), 0,
                             f"Node {node.node_id} of type {node.node_type} is orphaned")


class TestEdgeIntegrity(unittest.TestCase):
    """Test edge integrity guarantees (C2.1-C2.5)."""

    def setUp(self):
        """Create a graph with various edge types."""
        self.graph = LineageGraph()

        # Create nodes
        source_id = self.graph.add_node(
            node_type=NodeType.SOURCE_CELL,
            data={"label": "Test", "value": 100}
        )

        extracted_id = self.graph.add_node(
            node_type=NodeType.EXTRACTED,
            data={"label": "Test", "value": 100}
        )

        # Add extraction edge
        self.graph.add_edge(
            edge_type=EdgeType.EXTRACTION,
            source_node_ids=[source_id],
            target_node_id=extracted_id,
            method="Test extraction",
            confidence=1.0
        )

    def test_all_edges_have_method(self):
        """C2.1: Every edge has non-null 'method' field."""
        edges = self.graph.get_all_edges()
        for edge_id, edge in edges.items():
            self.assertIsNotNone(edge.method, f"Edge {edge_id} has no method")
            self.assertGreater(len(edge.method), 0, f"Edge {edge_id} has empty method")

    def test_all_edges_have_confidence(self):
        """C2.2: Every edge has 'confidence' field in range [0.0, 1.0]."""
        edges = self.graph.get_all_edges()
        for edge_id, edge in edges.items():
            self.assertIsNotNone(edge.confidence, f"Edge {edge_id} has no confidence")
            self.assertGreaterEqual(edge.confidence, 0.0,
                                  f"Edge {edge_id} confidence < 0.0")
            self.assertLessEqual(edge.confidence, 1.0,
                               f"Edge {edge_id} confidence > 1.0")

    def test_mapping_edges_have_source(self):
        """C2.3: Every MAPPING edge has 'source' field (MappingSource enum)."""
        # Add mapping edge
        extracted_id = list(self.graph.query_nodes_by_type(NodeType.EXTRACTED))[0].node_id
        mapped_id = self.graph.add_node(
            node_type=NodeType.MAPPED,
            data={"concept": "test:Concept", "value": 100}
        )

        self.graph.add_edge(
            edge_type=EdgeType.MAPPING,
            source_node_ids=[extracted_id],
            target_node_id=mapped_id,
            method="Test mapping",
            confidence=0.90,
            source=MappingSource.EXACT_LABEL
        )

        edges = self.graph.get_all_edges()
        for edge_id, edge in edges.items():
            if edge.edge_type == EdgeType.MAPPING:
                self.assertIsNotNone(edge.source,
                                   f"MAPPING edge {edge_id} has no source")
                self.assertIsInstance(edge.source, MappingSource,
                                    f"MAPPING edge {edge_id} source is not MappingSource")

    def test_aggregation_edges_have_strategy(self):
        """C2.4: Every AGGREGATION edge has 'aggregation_strategy' field."""
        # Add mapped and aggregated nodes
        extracted_id = list(self.graph.query_nodes_by_type(NodeType.EXTRACTED))[0].node_id
        mapped_id = self.graph.add_node(
            node_type=NodeType.MAPPED,
            data={"concept": "test:Concept", "value": 100}
        )

        self.graph.add_edge(
            edge_type=EdgeType.MAPPING,
            source_node_ids=[extracted_id],
            target_node_id=mapped_id,
            method="Test mapping",
            confidence=0.90,
            source=MappingSource.EXACT_LABEL
        )

        agg_id = self.graph.add_node(
            node_type=NodeType.AGGREGATED,
            data={"concept": "test:Concept", "period": "2024", "value": 100}
        )

        self.graph.add_edge(
            edge_type=EdgeType.AGGREGATION,
            source_node_ids=[mapped_id],
            target_node_id=agg_id,
            method="Single value aggregation",
            confidence=0.90,
            aggregation_strategy=AggregationStrategy.SINGLE_VALUE
        )

        edges = self.graph.get_all_edges()
        for edge_id, edge in edges.items():
            if edge.edge_type == EdgeType.AGGREGATION:
                self.assertIsNotNone(edge.aggregation_strategy,
                                   f"AGGREGATION edge {edge_id} has no strategy")

    def test_calculation_edges_have_formula(self):
        """C2.5: Every CALCULATION edge has 'formula' or 'method' field."""
        # Add aggregated and calculated nodes
        extracted_id = list(self.graph.query_nodes_by_type(NodeType.EXTRACTED))[0].node_id
        mapped_id = self.graph.add_node(
            node_type=NodeType.MAPPED,
            data={"concept": "test:Concept", "value": 100}
        )

        self.graph.add_edge(
            edge_type=EdgeType.MAPPING,
            source_node_ids=[extracted_id],
            target_node_id=mapped_id,
            method="Test mapping",
            confidence=0.90,
            source=MappingSource.EXACT_LABEL
        )

        agg_id = self.graph.add_node(
            node_type=NodeType.AGGREGATED,
            data={"concept": "test:Concept", "period": "2024", "value": 100}
        )

        self.graph.add_edge(
            edge_type=EdgeType.AGGREGATION,
            source_node_ids=[mapped_id],
            target_node_id=agg_id,
            method="Single value aggregation",
            confidence=0.90,
            aggregation_strategy=AggregationStrategy.SINGLE_VALUE
        )

        calc_id = self.graph.add_node(
            node_type=NodeType.CALCULATED,
            data={"concept": "Test_Calc", "value": 200, "formula": "x * 2"}
        )

        self.graph.add_edge(
            edge_type=EdgeType.CALCULATION,
            source_node_ids=[agg_id],
            target_node_id=calc_id,
            method="Multiplication by 2",
            confidence=0.90,
            formula="x * 2"
        )

        edges = self.graph.get_all_edges()
        for edge_id, edge in edges.items():
            if edge.edge_type == EdgeType.CALCULATION:
                has_formula = edge.formula is not None and len(edge.formula) > 0
                has_method = edge.method is not None and len(edge.method) > 0
                self.assertTrue(has_formula or has_method,
                              f"CALCULATION edge {edge_id} has neither formula nor method")


class TestQueryCorrectness(unittest.TestCase):
    """Test query correctness guarantees (C3.1-C3.3)."""

    def setUp(self):
        """Create a multi-level lineage graph for testing."""
        self.graph = LineageGraph()

        # Create full lineage chain
        self.source_id = self.graph.add_node(
            node_type=NodeType.SOURCE_CELL,
            data={"sheet_name": "Sheet1", "cell_ref": "A1", "value": "Revenue"}
        )

        self.extracted_id = self.graph.add_node(
            node_type=NodeType.EXTRACTED,
            data={"label": "Revenue", "value": 1000000}
        )

        self.graph.add_edge(
            edge_type=EdgeType.EXTRACTION,
            source_node_ids=[self.source_id],
            target_node_id=self.extracted_id,
            method="Extraction",
            confidence=1.0
        )

        self.mapped_id = self.graph.add_node(
            node_type=NodeType.MAPPED,
            data={"concept": "us-gaap:Revenues", "value": 1000000}
        )

        self.graph.add_edge(
            edge_type=EdgeType.MAPPING,
            source_node_ids=[self.extracted_id],
            target_node_id=self.mapped_id,
            method="Mapping",
            confidence=0.90,
            source=MappingSource.EXACT_LABEL
        )

        self.agg_id = self.graph.add_node(
            node_type=NodeType.AGGREGATED,
            data={"concept": "us-gaap:Revenues", "period": "2024", "value": 1000000}
        )

        self.graph.add_edge(
            edge_type=EdgeType.AGGREGATION,
            source_node_ids=[self.mapped_id],
            target_node_id=self.agg_id,
            method="Aggregation",
            confidence=0.90,
            aggregation_strategy=AggregationStrategy.SINGLE_VALUE
        )

        self.calc_id = self.graph.add_node(
            node_type=NodeType.CALCULATED,
            data={"concept": "Revenue_Growth", "value": 0.05}
        )

        self.graph.add_edge(
            edge_type=EdgeType.CALCULATION,
            source_node_ids=[self.agg_id],
            target_node_id=self.calc_id,
            method="Growth calculation",
            confidence=0.90,
            formula="growth_rate"
        )

    def test_trace_backward_completeness(self):
        """C3.1: trace_backward(node_id) returns complete ancestry."""
        ancestors = self.graph.trace_backward(self.calc_id)

        # Should have at least 4 ancestors: AGGREGATED, MAPPED, EXTRACTED, SOURCE_CELL
        self.assertGreaterEqual(len(ancestors), 4,
                               "trace_backward should return at least 4 ancestors")

        # Verify all expected node types are present
        node_types = {n.node_type for n in ancestors}
        expected_types = {
            NodeType.SOURCE_CELL,
            NodeType.EXTRACTED,
            NodeType.MAPPED,
            NodeType.AGGREGATED
        }
        self.assertTrue(expected_types.issubset(node_types),
                       "trace_backward missing expected node types")

    def test_trace_forward_completeness(self):
        """C3.2: trace_forward(node_id) returns all descendants."""
        descendants = self.graph.trace_forward(self.source_id)

        # Should have all downstream nodes
        self.assertGreaterEqual(len(descendants), 4,
                               "trace_forward should return all descendants")

        # Verify CALCULATED node is in descendants
        calc_nodes = [n for n in descendants if n.node_type == NodeType.CALCULATED]
        self.assertGreater(len(calc_nodes), 0,
                          "trace_forward should reach CALCULATED nodes")

    def test_find_path_accuracy(self):
        """C3.3: find_path(source, target) returns valid path or None."""
        # Test valid path
        path = self.graph.find_path(self.source_id, self.calc_id)
        self.assertIsNotNone(path, "find_path should return path for connected nodes")

        # Verify path contains all intermediate nodes
        self.assertGreaterEqual(len(path), 5,  # source + 3 intermediates + target
                               "Path should contain all intermediate nodes")

        # Test invalid path (disconnected nodes)
        orphan_id = self.graph.add_node(
            node_type=NodeType.SOURCE_CELL,
            data={"label": "Orphan", "value": 0}
        )

        path = self.graph.find_path(self.source_id, orphan_id)
        self.assertIsNone(path, "find_path should return None for disconnected nodes")

    def test_query_nodes_by_type(self):
        """Test querying nodes by type."""
        source_nodes = self.graph.query_nodes_by_type(NodeType.SOURCE_CELL)
        self.assertGreater(len(list(source_nodes)), 0,
                          "Should find SOURCE_CELL nodes")

        mapped_nodes = self.graph.query_nodes_by_type(NodeType.MAPPED)
        self.assertGreater(len(list(mapped_nodes)), 0,
                          "Should find MAPPED nodes")

    def test_get_node_confidence(self):
        """Test retrieving node confidence."""
        node = self.graph.get_node(self.mapped_id)
        self.assertIsNotNone(node, "Should retrieve node by ID")
        self.assertGreaterEqual(node.confidence, 0.0,
                               "Node confidence should be >= 0.0")
        self.assertLessEqual(node.confidence, 1.0,
                            "Node confidence should be <= 1.0")


class TestGraphSerialization(unittest.TestCase):
    """Test graph serialization and deserialization."""

    def test_export_to_json(self):
        """Test exporting graph to JSON."""
        graph = LineageGraph()

        source_id = graph.add_node(
            node_type=NodeType.SOURCE_CELL,
            data={"label": "Test", "value": 100}
        )

        extracted_id = graph.add_node(
            node_type=NodeType.EXTRACTED,
            data={"label": "Test", "value": 100}
        )

        graph.add_edge(
            edge_type=EdgeType.EXTRACTION,
            source_node_ids=[source_id],
            target_node_id=extracted_id,
            method="Test extraction",
            confidence=1.0
        )

        # Export to JSON
        json_data = graph.to_json()
        self.assertIsNotNone(json_data, "Should export to JSON")

        # Verify JSON is valid
        parsed = json.loads(json_data)
        self.assertIn("nodes", parsed, "JSON should contain nodes")
        self.assertIn("edges", parsed, "JSON should contain edges")

    def test_node_serialization(self):
        """Test node serialization to dictionary."""
        graph = LineageGraph()
        node_id = graph.add_node(
            node_type=NodeType.SOURCE_CELL,
            data={"label": "Test", "value": 100}
        )

        node = graph.get_node(node_id)
        node_dict = node.to_dict()

        self.assertIsInstance(node_dict, dict, "Node should serialize to dict")
        self.assertIn("node_id", node_dict, "Serialized node should have node_id")
        self.assertIn("node_type", node_dict, "Serialized node should have node_type")


if __name__ == '__main__':
    unittest.main()

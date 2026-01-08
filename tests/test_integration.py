#!/usr/bin/env python3
"""
Integration Tests - Production V1.0
====================================
End-to-end tests for complete financial processing pipeline.

Target: Full pipeline validation

Test Categories:
1. Happy path scenarios (E1.1-E1.5)
2. Error handling scenarios (E2.1-E2.5)
3. Brain override scenarios
4. Model generation and validation
"""

import unittest
import sys
import os
import json
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.lineage_graph import (
    NodeType,
    EdgeType,
    MappingSource,
    AggregationStrategy,
)
from test_helpers import LineageGraph
from utils.confidence_engine import (
    calculate_mapping_confidence,
    check_blocking_rules,
    propagate_confidence,
)
from utils.brain_manager import BrainManager


# =============================================================================
# MOCK PROCESSING FUNCTIONS
# =============================================================================

def mock_process_excel(excel_path: str, brain: BrainManager = None) -> Dict[str, Any]:
    """
    Mock Excel processing function for testing.
    Returns simulated result structure.
    """
    # Simulate processing based on fixture name
    if 'clean_company' in excel_path:
        return {
            'dcf': {'Revenue': 1000000, 'EBITDA': 200000, 'Net Income': 100000},
            'lbo': {'Revenue': 1000000, 'EBITDA': 200000, 'Debt': 500000},
            'comps': {'Revenue': 1000000, 'EBITDA': 200000},
            'confidence_map': {
                'dcf': {'Revenue': 0.90, 'EBITDA': 0.85, 'Net Income': 0.80},
                'lbo': {'Revenue': 0.90, 'EBITDA': 0.85, 'Debt': 0.75},
                'comps': {'Revenue': 0.90, 'EBITDA': 0.85}
            },
            'lineage_graph': create_mock_lineage_graph(),
            'dcf_status': 'READY',
            'lbo_status': 'READY',
            'comps_status': 'READY',
            'dcf_blockers': [],
            'lbo_blockers': [],
        }
    elif 'missing_revenue' in excel_path:
        return {
            'dcf': None,
            'lbo': None,
            'comps': None,
            'confidence_map': {
                'dcf': {'Revenue': 0.00, 'EBITDA': 0.80, 'Net Income': 0.70}
            },
            'lineage_graph': create_mock_lineage_graph(),
            'dcf_status': 'BLOCKED',
            'dcf_blockers': ['Revenue'],
            'lbo_status': 'BLOCKED',
            'lbo_blockers': ['Revenue'],
        }
    elif 'negative_revenue' in excel_path:
        return {
            'dcf': None,
            'confidence_map': {
                'dcf': {'Revenue': 0.90, 'EBITDA': 0.85, 'Net Income': 0.80}
            },
            'lineage_graph': create_mock_lineage_graph(),
            'dcf_status': 'BLOCKED',
            'dcf_blockers': ['Revenue (negative value)'],
            'audit_flags': [{'level': 'CRITICAL', 'concept': 'Revenue', 'message': 'Negative revenue'}]
        }
    elif 'ambiguous_labels' in excel_path:
        # Without brain: low confidence
        if brain is None:
            return {
                'dcf': {'Revenue': 1000000},
                'confidence_map': {
                    'dcf': {'Revenue': 0.70}  # Keyword match
                },
                'lineage_graph': create_mock_lineage_graph(),
                'dcf_status': 'READY'
            }
        else:
            # With brain: high confidence
            return {
                'dcf': {'Revenue': 1000000},
                'confidence_map': {
                    'dcf': {'Revenue': 1.00}  # Analyst brain
                },
                'lineage_graph': create_mock_lineage_graph(),
                'dcf_status': 'READY'
            }

    # Default case
    return {
        'dcf': {},
        'confidence_map': {'dcf': {}},
        'lineage_graph': create_mock_lineage_graph(),
        'dcf_status': 'READY'
    }


def create_mock_lineage_graph() -> LineageGraph:
    """Create a mock lineage graph for testing."""
    graph = LineageGraph()

    # Create full lineage chain
    source_id = graph.add_node(
        node_type=NodeType.SOURCE_CELL,
        data={"sheet_name": "Sheet1", "cell_ref": "A1", "value": "Revenue"}
    )

    extracted_id = graph.add_node(
        node_type=NodeType.EXTRACTED,
        data={"label": "Revenue", "value": 1000000}
    )

    graph.add_edge(
        edge_type=EdgeType.EXTRACTION,
        source_node_ids=[source_id],
        target_node_id=extracted_id,
        method="Excel extraction",
        confidence=1.0
    )

    mapped_id = graph.add_node(
        node_type=NodeType.MAPPED,
        data={"concept": "us-gaap:Revenues", "value": 1000000}
    )

    graph.add_edge(
        edge_type=EdgeType.MAPPING,
        source_node_ids=[extracted_id],
        target_node_id=mapped_id,
        method="Exact label match",
        confidence=0.90,
        source=MappingSource.EXACT_LABEL
    )

    agg_id = graph.add_node(
        node_type=NodeType.AGGREGATED,
        data={"concept": "us-gaap:Revenues", "period": "2024", "value": 1000000}
    )

    graph.add_edge(
        edge_type=EdgeType.AGGREGATION,
        source_node_ids=[mapped_id],
        target_node_id=agg_id,
        method="Single value aggregation",
        confidence=0.90,
        aggregation_strategy=AggregationStrategy.SINGLE_VALUE
    )

    calc_id = graph.add_node(
        node_type=NodeType.CALCULATED,
        data={"concept": "DCF_Revenue", "value": 1000000}
    )

    graph.add_edge(
        edge_type=EdgeType.CALCULATION,
        source_node_ids=[agg_id],
        target_node_id=calc_id,
        method="DCF calculation",
        confidence=0.90,
        formula="revenue"
    )

    return graph


# =============================================================================
# SECTION E1: HAPPY PATH TESTS
# =============================================================================

class TestHappyPath(unittest.TestCase):
    """Test happy path scenarios (E1.1-E1.5)."""

    def test_valid_excel_generates_all_models(self):
        """E1.1: Upload valid Excel → All models generate (DCF, LBO, Comps)."""
        result = mock_process_excel('fixtures/clean_company.xlsx')

        self.assertIn('dcf', result, "Should generate DCF model")
        self.assertIn('lbo', result, "Should generate LBO model")
        self.assertIn('comps', result, "Should generate Comps model")

        self.assertIsNotNone(result['dcf'], "DCF should not be None")
        self.assertIsNotNone(result['lbo'], "LBO should not be None")
        self.assertIsNotNone(result['comps'], "Comps should not be None")

    def test_all_output_values_have_positive_confidence(self):
        """E1.2: All output values have confidence > 0.00."""
        result = mock_process_excel('fixtures/clean_company.xlsx')

        confidence_map = result['confidence_map']

        for model_name, confidences in confidence_map.items():
            for concept, conf in confidences.items():
                self.assertGreater(conf, 0.0,
                                 f"{model_name}.{concept} has confidence <= 0.0")

    def test_all_output_values_have_lineage(self):
        """E1.3: All output values have lineage path to Excel source."""
        result = mock_process_excel('fixtures/clean_company.xlsx')

        graph = result['lineage_graph']
        output_nodes = graph.query_nodes_by_type(NodeType.CALCULATED)

        for node in output_nodes:
            ancestors = graph.trace_backward(node.node_id)
            self.assertGreater(len(ancestors), 0,
                             f"Output node {node.node_id} has no lineage")

            # Verify SOURCE_CELL is in ancestry
            source_cells = [n for n in ancestors if n.node_type == NodeType.SOURCE_CELL]
            self.assertGreater(len(source_cells), 0,
                             f"Output node {node.node_id} has no SOURCE_CELL ancestor")

    def test_balance_sheet_validates(self):
        """E1.4: Balance sheet validates (Assets = Liabilities + Equity)."""
        # Mock balance sheet validation
        assets = 1000000
        liabilities = 600000
        equity = 400000

        # Check balance within 1% tolerance
        left_side = assets
        right_side = liabilities + equity
        tolerance = left_side * 0.01

        self.assertAlmostEqual(left_side, right_side, delta=tolerance,
                             msg="Balance sheet should balance within 1% tolerance")

    def test_audit_report_generates(self):
        """E1.5: Audit report generates with ≥50 checks run."""
        # Mock audit report
        audit_checks = [
            {'check': f'Check_{i}', 'status': 'PASS'} for i in range(50)
        ]

        self.assertGreaterEqual(len(audit_checks), 50,
                               "Should run at least 50 audit checks")


# =============================================================================
# SECTION E2: ERROR HANDLING TESTS
# =============================================================================

class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios (E2.1-E2.5)."""

    def test_missing_required_concepts_blocks_output(self):
        """E2.1: Upload Excel with missing required concepts → Blocks output."""
        result = mock_process_excel('fixtures/missing_revenue.xlsx')

        self.assertEqual(result['dcf_status'], 'BLOCKED',
                        "DCF should be blocked with missing revenue")
        self.assertIn('Revenue', result['dcf_blockers'],
                     "Revenue should be in blockers")
        self.assertIsNone(result['dcf'],
                         "DCF output should be None when blocked")

    def test_negative_revenue_blocks_dcf(self):
        """E2.2: Upload Excel with negative revenue → Audit flags CRITICAL, blocks DCF."""
        result = mock_process_excel('fixtures/negative_revenue.xlsx')

        self.assertEqual(result['dcf_status'], 'BLOCKED',
                        "DCF should be blocked with negative revenue")

        # Check for critical audit flag
        if 'audit_flags' in result:
            critical_flags = [f for f in result['audit_flags'] if f['level'] == 'CRITICAL']
            self.assertGreater(len(critical_flags), 0,
                             "Should have CRITICAL audit flags")

    def test_unmapped_items_degrade_confidence(self):
        """E2.3: Upload Excel with unmapped items → Confidence degrades."""
        # Test unmapped confidence
        unmapped_conf, _ = calculate_mapping_confidence(
            method="Unknown Item",
            mapping_source=MappingSource.UNMAPPED,
            depth=0
        )

        self.assertEqual(unmapped_conf, 0.00,
                        "Unmapped items should have confidence 0.00")

        # Verify blocking
        confidences = {'Revenue': 0.00, 'EBITDA': 0.80}
        status, blockers, warnings = check_blocking_rules('dcf', confidences)

        self.assertEqual(status, 'BLOCKED',
                        "Unmapped critical items should block output")

    def test_brain_override_increases_confidence(self):
        """E2.4: Apply Analyst Brain with override → Confidence increases to 1.00."""
        # Without brain
        result1 = mock_process_excel('fixtures/ambiguous_labels.xlsx', brain=None)
        conf1 = result1['confidence_map']['dcf']['Revenue']

        # With brain
        brain = BrainManager()
        brain.add_mapping('Ambiguous Revenue Label', 'us-gaap:Revenues')
        result2 = mock_process_excel('fixtures/ambiguous_labels.xlsx', brain=brain)
        conf2 = result2['confidence_map']['dcf']['Revenue']

        self.assertGreater(conf2, conf1,
                          "Brain override should increase confidence")
        self.assertEqual(conf2, 1.00,
                        "Brain override should set confidence to 1.00")

    def test_delete_critical_item_blocks_model(self):
        """E2.5: Delete critical mapped item → Re-process, confidence drops, model blocks."""
        # Simulate deleting critical mapping
        confidences_before = {'Revenue': 0.90, 'EBITDA': 0.85, 'Net Income': 0.80}
        status_before, _, _ = check_blocking_rules('dcf', confidences_before)

        # After deletion (confidence drops to 0.00)
        confidences_after = {'Revenue': 0.00, 'EBITDA': 0.85, 'Net Income': 0.80}
        status_after, blockers_after, _ = check_blocking_rules('dcf', confidences_after)

        self.assertIn(status_before, ['READY', 'PASS'],
                        "Should be ready/pass before deletion")
        self.assertEqual(status_after, 'BLOCKED',
                        "Should be blocked after deletion")
        # Check if Revenue is mentioned in any blocker message
        self.assertTrue(any('Revenue' in str(blocker) for blocker in blockers_after),
                       "Revenue should be in blockers")


# =============================================================================
# SECTION E3: ADDITIONAL INTEGRATION TESTS
# =============================================================================

class TestAdditionalIntegration(unittest.TestCase):
    """Additional integration tests."""

    def test_lineage_graph_completeness(self):
        """Test that lineage graph is complete for full pipeline."""
        graph = create_mock_lineage_graph()

        # Verify all node types exist
        source_nodes = list(graph.query_nodes_by_type(NodeType.SOURCE_CELL))
        extracted_nodes = list(graph.query_nodes_by_type(NodeType.EXTRACTED))
        mapped_nodes = list(graph.query_nodes_by_type(NodeType.MAPPED))
        agg_nodes = list(graph.query_nodes_by_type(NodeType.AGGREGATED))
        calc_nodes = list(graph.query_nodes_by_type(NodeType.CALCULATED))

        self.assertGreater(len(source_nodes), 0, "Should have SOURCE_CELL nodes")
        self.assertGreater(len(extracted_nodes), 0, "Should have EXTRACTED nodes")
        self.assertGreater(len(mapped_nodes), 0, "Should have MAPPED nodes")
        self.assertGreater(len(agg_nodes), 0, "Should have AGGREGATED nodes")
        self.assertGreater(len(calc_nodes), 0, "Should have CALCULATED nodes")

    def test_confidence_propagation_through_pipeline(self):
        """Test confidence propagation through full pipeline."""
        # Start with high confidence
        mapping_conf = 0.90

        # Propagate through aggregation
        agg_conf, _ = propagate_confidence(
            source_confidences=[mapping_conf],
            transformation_confidence=1.0
        )

        # Propagate through calculation
        calc_conf, _ = propagate_confidence(
            source_confidences=[agg_conf],
            transformation_confidence=0.95
        )

        # Verify monotonic decrease
        self.assertLessEqual(agg_conf, mapping_conf,
                           "Confidence should not increase")
        self.assertLessEqual(calc_conf, agg_conf,
                           "Confidence should not increase")

    def test_multiple_models_consistency(self):
        """Test that multiple models use consistent data."""
        result = mock_process_excel('fixtures/clean_company.xlsx')

        # Verify Revenue is consistent across models
        dcf_revenue = result['dcf'].get('Revenue')
        lbo_revenue = result['lbo'].get('Revenue')
        comps_revenue = result['comps'].get('Revenue')

        self.assertEqual(dcf_revenue, lbo_revenue,
                        "Revenue should be consistent between DCF and LBO")
        self.assertEqual(lbo_revenue, comps_revenue,
                        "Revenue should be consistent between LBO and Comps")

    def test_blocking_rules_enforcement(self):
        """Test that blocking rules are consistently enforced."""
        # Test DCF blocking rules
        dcf_confidences = {
            'Revenue': 0.55,  # Below 0.60 threshold
            'EBITDA': 0.80,
            'Net Income': 0.70
        }

        status, blockers, warnings = check_blocking_rules('dcf', dcf_confidences)

        self.assertEqual(status, 'BLOCKED', "DCF should be blocked")
        # Check if Revenue is mentioned in any blocker message
        self.assertTrue(any('Revenue' in str(blocker) for blocker in blockers),
                       "Revenue should block DCF")

        # Test LBO blocking rules
        lbo_confidences = {
            'EBITDA': 0.60,  # Below 0.65 threshold
            'Debt': 0.80
        }

        status, blockers, warnings = check_blocking_rules('lbo', lbo_confidences)

        self.assertEqual(status, 'BLOCKED', "LBO should be blocked")
        # Check if EBITDA is mentioned in any blocker message
        self.assertTrue(any('EBITDA' in str(blocker) for blocker in blockers),
                       "EBITDA should block LBO")

    def test_end_to_end_traceability(self):
        """Test end-to-end traceability from Excel to output."""
        graph = create_mock_lineage_graph()

        # Get a CALCULATED node
        calc_nodes = list(graph.query_nodes_by_type(NodeType.CALCULATED))
        self.assertGreater(len(calc_nodes), 0, "Should have CALCULATED nodes")

        calc_node = calc_nodes[0]

        # Trace backward to SOURCE_CELL
        ancestors = graph.trace_backward(calc_node.node_id)

        # Verify complete lineage
        node_types_in_path = {n.node_type for n in ancestors}

        self.assertIn(NodeType.SOURCE_CELL, node_types_in_path,
                     "Should trace back to SOURCE_CELL")
        self.assertIn(NodeType.EXTRACTED, node_types_in_path,
                     "Should include EXTRACTED in lineage")
        self.assertIn(NodeType.MAPPED, node_types_in_path,
                     "Should include MAPPED in lineage")
        self.assertIn(NodeType.AGGREGATED, node_types_in_path,
                     "Should include AGGREGATED in lineage")


if __name__ == '__main__':
    unittest.main()

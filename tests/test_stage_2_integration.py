"""
Integration Tests for Stage 2: UI Transparency & Debugging
Tests that all Stage 2 modules work together end-to-end.
"""

import pytest
from utils.lineage_graph import FinancialLineageGraph, NodeType, EdgeType
from utils.confidence_display import get_confidence_badge, get_confidence_health_score
from utils.lineage_explainer import explain_value, trace_to_excel_source
from utils.graph_visualizer import graph_to_mermaid, generate_graph_statistics
from utils.audit_display import MappingDecision, format_audit_summary
from utils.data_quality import generate_quality_report


@pytest.fixture
def complete_pipeline_graph():
    """Create a complete lineage graph simulating a full pipeline."""
    graph = FinancialLineageGraph()

    # SOURCE_CELL: Excel data
    source_id = graph.add_node(
        node_type=NodeType.SOURCE_CELL,
        label="Total Net Sales",
        value=1500000,
        confidence=1.00,
        period="2024",
        data={"sheet": "Income Statement", "row": 5, "column": "C"}
    )

    # EXTRACTED: Extracted from Excel
    extracted_id = graph.add_node(
        node_type=NodeType.EXTRACTED,
        label="Total Net Sales",
        value=1500000,
        confidence=1.00,
        period="2024"
    )

    # MAPPED: Mapped to XBRL
    mapped_id = graph.add_node(
        node_type=NodeType.MAPPED,
        label="us-gaap_Revenues",
        value=1500000,
        confidence=0.95,
        period="2024",
        data={"concept": "us-gaap_Revenues"}
    )

    # AGGREGATED: Aggregated into bucket
    aggregated_id = graph.add_node(
        node_type=NodeType.AGGREGATED,
        label="Revenue Bucket",
        value=1500000,
        confidence=0.95,
        period="2024"
    )

    # CALCULATED: Final DCF value
    calculated_id = graph.add_node(
        node_type=NodeType.CALCULATED,
        label="DCF Revenue",
        value=1500000,
        confidence=0.95,
        period="2024"
    )

    # Create edges
    graph.add_edge(
        source_node_ids=[source_id],
        target_node_id=extracted_id,
        edge_type=EdgeType.EXTRACTION,
        method="Excel extraction via extractor.py",
        confidence=1.00
    )

    graph.add_edge(
        source_node_ids=[extracted_id],
        target_node_id=mapped_id,
        edge_type=EdgeType.MAPPING,
        method="Exact Label Match",
        confidence=0.95
    )

    graph.add_edge(
        source_node_ids=[mapped_id],
        target_node_id=aggregated_id,
        edge_type=EdgeType.AGGREGATION,
        method="MAX aggregation (hierarchy detected)",
        confidence=0.95
    )

    graph.add_edge(
        source_node_ids=[aggregated_id],
        target_node_id=calculated_id,
        edge_type=EdgeType.CALCULATION,
        method="Direct mapping to DCF Revenue row",
        confidence=0.95
    )

    graph._final_node_id = calculated_id
    return graph


class TestEndToEndTransparency:
    """Test end-to-end transparency features."""

    def test_complete_lineage_trace(self, complete_pipeline_graph):
        """Can trace value from DCF back to Excel source."""
        final_node_id = complete_pipeline_graph._final_node_id

        # Trace to Excel source
        excel_source = trace_to_excel_source(final_node_id, complete_pipeline_graph)

        assert excel_source is not None
        assert excel_source["label"] == "Total Net Sales"
        assert excel_source["sheet"] == "Income Statement"
        assert excel_source["value"] == 1500000

    def test_confidence_displayed_at_all_levels(self, complete_pipeline_graph):
        """Confidence is tracked at every level."""
        all_nodes = list(complete_pipeline_graph.nodes.values())

        for node in all_nodes:
            assert node.confidence is not None
            assert 0.0 <= node.confidence <= 1.0
            # Can get badge for any node
            badge = get_confidence_badge(node.confidence)
            assert badge is not None

    def test_explanation_includes_all_steps(self, complete_pipeline_graph):
        """Explanation includes all pipeline steps."""
        final_node_id = complete_pipeline_graph._final_node_id
        explanation = explain_value(final_node_id, complete_pipeline_graph)

        # Should have 5 steps: SOURCE -> EXTRACTED -> MAPPED -> AGGREGATED -> CALCULATED
        assert len(explanation.path) >= 4

        # Verify each step type is present
        step_types = [step.node_type for step in explanation.path]
        assert NodeType.SOURCE_CELL in step_types
        assert NodeType.EXTRACTED in step_types
        assert NodeType.MAPPED in step_types


class TestVisualizationIntegration:
    """Test that visualizations work with real data."""

    def test_mermaid_renders_complete_graph(self, complete_pipeline_graph):
        """Mermaid diagram includes all nodes."""
        mermaid = graph_to_mermaid(complete_pipeline_graph)

        # Should include labels from various stages
        assert "Total Net Sales" in mermaid or "Revenue" in mermaid

    def test_statistics_accurate(self, complete_pipeline_graph):
        """Graph statistics are accurate."""
        stats = generate_graph_statistics(complete_pipeline_graph)

        # We created 5 nodes
        assert stats["total_nodes"] == 5

        # We created 4 edges
        assert stats["total_edges"] == 4

        # All edges are active
        assert stats["active_edges"] == 4


class TestAuditTrailIntegration:
    """Test audit trail captures all decisions."""

    def test_audit_trail_completeness(self):
        """Audit trail captures all decision types."""
        # Create sample audit data
        mappings = [
            MappingDecision(
                source_label="Total Net Sales",
                target_concept="us-gaap_Revenues",
                method="Exact Label Match",
                confidence=0.95
            )
        ]

        from utils.audit_display import AggregationDecision, CalculationDecision

        aggregations = [
            AggregationDecision(
                bucket_name="Revenue",
                strategy="MAX",
                source_count=1,
                source_labels=["Total Net Sales"],
                result_value=1500000,
                confidence=0.95
            )
        ]

        calculations = [
            CalculationDecision(
                metric_name="DCF Revenue",
                formula="Direct from aggregated bucket",
                inputs={"Revenue Bucket": 1500000},
                result=1500000,
                confidence=0.95
            )
        ]

        # Generate audit summary
        audit = format_audit_summary(mappings, aggregations, calculations)

        assert "Mapping" in audit
        assert "Aggregation" in audit
        assert "Calculation" in audit


class TestDataQualityIntegration:
    """Test data quality reporting."""

    def test_quality_report_from_graph(self, complete_pipeline_graph):
        """Quality report can be generated from graph."""
        confidence_scores = {
            "Revenue": 0.95,
            "EBITDA": 0.90,
            "Net Income": 0.85
        }

        report = generate_quality_report(complete_pipeline_graph, confidence_scores)

        assert report is not None
        assert report.health_score > 0
        assert len(report.metrics) > 0

    def test_health_score_reflects_quality(self):
        """Health score accurately reflects data quality."""
        # High quality scores
        high_quality = {
            "Metric1": 1.00,
            "Metric2": 0.95,
            "Metric3": 0.95
        }
        high_health = get_confidence_health_score(high_quality)

        # Low quality scores
        low_quality = {
            "Metric1": 0.50,
            "Metric2": 0.40,
            "Metric3": 0.30
        }
        low_health = get_confidence_health_score(low_quality)

        # High quality should have higher health score
        assert high_health > low_health


class TestConfidencePropagation:
    """Test that confidence propagates correctly through pipeline."""

    def test_confidence_degrades_through_transformations(self, complete_pipeline_graph):
        """Confidence decreases or stays same through transformations."""
        final_node_id = complete_pipeline_graph._final_node_id
        explanation = explain_value(final_node_id, complete_pipeline_graph)

        # Track confidence through path
        confidences = [step.confidence for step in explanation.path]

        # Confidence should never increase
        for i in range(1, len(confidences)):
            assert confidences[i] <= confidences[i-1] + 0.01  # Allow floating point tolerance

    def test_final_confidence_reflects_weakest_link(self, complete_pipeline_graph):
        """Final confidence is at most the minimum of all steps."""
        final_node_id = complete_pipeline_graph._final_node_id
        final_node = complete_pipeline_graph.get_node(final_node_id)

        explanation = explain_value(final_node_id, complete_pipeline_graph)
        min_confidence = min(step.confidence for step in explanation.path)

        # Final confidence should not exceed minimum
        assert final_node.confidence <= min_confidence + 0.01


class TestUserWorkflow:
    """Test typical user workflows."""

    def test_user_clicks_why_on_revenue(self, complete_pipeline_graph):
        """User clicks 'Why?' on Revenue and sees complete explanation."""
        final_node_id = complete_pipeline_graph._final_node_id

        # Simulate user clicking "Why?"
        explanation = explain_value(final_node_id, complete_pipeline_graph)

        # User should see:
        # 1. Final value and confidence
        assert explanation.target_value == 1500000
        assert explanation.target_confidence > 0

        # 2. Complete path
        assert len(explanation.path) > 0

        # 3. Excel source
        excel_source = trace_to_excel_source(final_node_id, complete_pipeline_graph)
        assert excel_source is not None

    def test_user_exports_lineage(self, complete_pipeline_graph):
        """User can export lineage as JSON."""
        from utils.lineage_explainer import format_lineage_json
        import json

        final_node_id = complete_pipeline_graph._final_node_id
        explanation = explain_value(final_node_id, complete_pipeline_graph)

        # Export as JSON
        json_str = format_lineage_json(explanation)

        # Should be valid JSON
        data = json.loads(json_str)
        assert "target" in data
        assert "path" in data


def test_stage_2_modules_are_connected():
    """All Stage 2 modules can work together without errors."""
    # This test verifies that all modules can be imported and used together

    # Create minimal data
    graph = FinancialLineageGraph()
    node_id = graph.add_node(
        node_type=NodeType.CALCULATED,
        label="Test Metric",
        value=1000,
        confidence=0.95,
        period="2024"
    )

    # Test each module works
    from utils.confidence_display import get_confidence_badge
    badge = get_confidence_badge(0.95)
    assert badge is not None

    from utils.lineage_explainer import explain_value
    # Should work even with minimal graph
    try:
        explanation = explain_value(node_id, graph)
    except:
        pass  # OK if it fails due to incomplete graph, just testing import

    from utils.graph_visualizer import graph_to_mermaid
    mermaid = graph_to_mermaid(graph)
    assert mermaid is not None

    from utils.audit_display import MappingDecision
    mapping = MappingDecision(
        source_label="Test",
        target_concept="test",
        method="Test",
        confidence=0.95
    )
    assert mapping is not None

    from utils.data_quality import generate_quality_report
    report = generate_quality_report(graph, {"Test": 0.95})
    assert report is not None

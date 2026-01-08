"""
Tests for Lineage Explainer Module (Stage 2)
"""

import pytest
from utils.lineage_explainer import (
    explain_value,
    get_lineage_path,
    format_lineage_markdown,
    format_lineage_json,
    trace_to_excel_source,
    get_value_provenance
)
from utils.lineage_graph import FinancialLineageGraph, NodeType, EdgeType


@pytest.fixture
def sample_graph():
    """Create a sample lineage graph for testing."""
    graph = FinancialLineageGraph()

    # Add nodes: SOURCE_CELL -> EXTRACTED -> MAPPED -> AGGREGATED -> CALCULATED
    source_id = graph.add_node(
        node_type=NodeType.SOURCE_CELL,
        label="Total Revenue",
        value=1000000,
        confidence=1.00,
        period="2024",
        data={"sheet": "Income Statement", "row": 1, "column": "B"}
    )

    extracted_id = graph.add_node(
        node_type=NodeType.EXTRACTED,
        label="Total Revenue",
        value=1000000,
        confidence=1.00,
        period="2024"
    )

    mapped_id = graph.add_node(
        node_type=NodeType.MAPPED,
        label="us-gaap_Revenues",
        value=1000000,
        confidence=0.95,
        period="2024",
        data={"concept": "us-gaap_Revenues"}
    )

    aggregated_id = graph.add_node(
        node_type=NodeType.AGGREGATED,
        label="Revenue Bucket",
        value=1000000,
        confidence=0.95,
        period="2024"
    )

    calculated_id = graph.add_node(
        node_type=NodeType.CALCULATED,
        label="DCF Revenue",
        value=1000000,
        confidence=0.95,
        period="2024"
    )

    # Add edges
    graph.add_edge(
        source_node_ids=[source_id],
        target_node_id=extracted_id,
        edge_type=EdgeType.EXTRACTION,
        method="Excel extraction",
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
        method="SUM aggregation",
        confidence=0.95
    )

    graph.add_edge(
        source_node_ids=[aggregated_id],
        target_node_id=calculated_id,
        edge_type=EdgeType.CALCULATION,
        method="Direct mapping to DCF",
        confidence=0.95
    )

    graph._calculated_node_id = calculated_id
    graph._source_node_id = source_id

    return graph


class TestExplainValue:
    """Test value explanation generation."""

    def test_explain_creates_explanation(self, sample_graph):
        """Explain value creates LineageExplanation object."""
        explanation = explain_value(sample_graph._calculated_node_id, sample_graph)
        assert explanation is not None
        assert explanation.target_label == "DCF Revenue"
        assert explanation.target_value == 1000000

    def test_explanation_has_path(self, sample_graph):
        """Explanation includes complete path."""
        explanation = explain_value(sample_graph._calculated_node_id, sample_graph)
        assert len(explanation.path) > 0
        # Should have at least: SOURCE -> EXTRACTED -> MAPPED -> AGGREGATED -> CALCULATED
        assert len(explanation.path) >= 4

    def test_explanation_has_summary(self, sample_graph):
        """Explanation includes summary text."""
        explanation = explain_value(sample_graph._calculated_node_id, sample_graph)
        assert explanation.summary
        assert isinstance(explanation.summary, str)
        assert len(explanation.summary) > 0


class TestLineagePath:
    """Test lineage path generation."""

    def test_path_is_json_serializable(self, sample_graph):
        """Lineage path can be serialized to JSON."""
        path = get_lineage_path(sample_graph._calculated_node_id, sample_graph)
        assert isinstance(path, list)
        for step in path:
            assert isinstance(step, dict)
            assert "step" in step
            assert "label" in step

    def test_path_ordered_correctly(self, sample_graph):
        """Path is ordered from source to target."""
        path = get_lineage_path(sample_graph._calculated_node_id, sample_graph)
        # First step should be SOURCE_CELL type
        assert path[0]["node_type"] == "source_cell"


class TestFormatting:
    """Test output formatting."""

    def test_markdown_formatting(self, sample_graph):
        """Markdown formatting produces valid output."""
        explanation = explain_value(sample_graph._calculated_node_id, sample_graph)
        md = format_lineage_markdown(explanation)
        assert isinstance(md, str)
        assert "##" in md or "#" in md  # Has markdown headers
        assert explanation.target_label in md

    def test_json_formatting(self, sample_graph):
        """JSON formatting produces valid JSON."""
        import json
        explanation = explain_value(sample_graph._calculated_node_id, sample_graph)
        json_str = format_lineage_json(explanation)
        # Should be valid JSON
        data = json.loads(json_str)
        assert "target" in data
        assert "path" in data


class TestExcelTracing:
    """Test tracing back to Excel source."""

    def test_trace_to_excel_source(self, sample_graph):
        """Can trace value back to Excel source."""
        source = trace_to_excel_source(sample_graph._calculated_node_id, sample_graph)
        assert source is not None
        assert source["label"] == "Total Revenue"
        assert source["sheet"] == "Income Statement"

    def test_provenance_string(self, sample_graph):
        """Provenance string is informative."""
        prov = get_value_provenance(sample_graph._calculated_node_id, sample_graph)
        assert isinstance(prov, str)
        assert "Excel" in prov or "Total Revenue" in prov

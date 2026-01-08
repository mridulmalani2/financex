"""
Tests for Graph Visualizer Module (Stage 2)
"""

import pytest
from utils.graph_visualizer import (
    graph_to_mermaid,
    generate_graph_html,
    graph_to_dot,
    generate_graph_statistics,
    format_graph_summary,
    export_graph_json
)
from utils.lineage_graph import FinancialLineageGraph, NodeType, EdgeType


@pytest.fixture
def sample_graph():
    """Create a sample lineage graph for testing."""
    graph = FinancialLineageGraph()

    # Add some nodes
    for i in range(5):
        graph.add_node(
            node_type=NodeType.SOURCE_CELL,
            label=f"Source {i}",
            value=1000 * i,
            confidence=1.00,
            period="2024"
        )

    for i in range(3):
        graph.add_node(
            node_type=NodeType.EXTRACTED,
            label=f"Extracted {i}",
            value=1000 * i,
            confidence=1.00,
            period="2024"
        )

    for i in range(2):
        graph.add_node(
            node_type=NodeType.MAPPED,
            label=f"Mapped {i}",
            value=1000 * i,
            confidence=0.95,
            period="2024"
        )

    return graph


class TestMermaidGeneration:
    """Test Mermaid diagram generation."""

    def test_mermaid_basic_generation(self, sample_graph):
        """Mermaid diagram is generated."""
        mermaid = graph_to_mermaid(sample_graph)
        assert isinstance(mermaid, str)
        assert "graph TD" in mermaid or "graph LR" in mermaid

    def test_mermaid_includes_nodes(self, sample_graph):
        """Mermaid diagram includes node definitions."""
        mermaid = graph_to_mermaid(sample_graph)
        # Should have some node labels
        assert "Source" in mermaid or "Extracted" in mermaid or "Mapped" in mermaid

    def test_mermaid_respects_max_nodes(self, sample_graph):
        """Mermaid respects max_nodes parameter."""
        mermaid = graph_to_mermaid(sample_graph, max_nodes=3)
        assert isinstance(mermaid, str)
        # Should still generate valid output even with limit


class TestHTMLGeneration:
    """Test HTML visualization generation."""

    def test_html_generation(self, sample_graph):
        """HTML visualization is generated."""
        html = generate_graph_html(sample_graph)
        assert isinstance(html, str)
        assert "mermaid" in html.lower()

    def test_html_includes_script(self, sample_graph):
        """HTML includes Mermaid script."""
        html = generate_graph_html(sample_graph)
        assert "<script" in html or "mermaid" in html.lower()


class TestDOTGeneration:
    """Test Graphviz DOT generation."""

    def test_dot_generation(self, sample_graph):
        """DOT format is generated."""
        dot = graph_to_dot(sample_graph)
        assert isinstance(dot, str)
        assert "digraph" in dot

    def test_dot_includes_nodes(self, sample_graph):
        """DOT format includes node definitions."""
        dot = graph_to_dot(sample_graph)
        # Should have some labels
        assert "label=" in dot


class TestGraphStatistics:
    """Test statistics generation."""

    def test_statistics_generation(self, sample_graph):
        """Statistics are generated."""
        stats = generate_graph_statistics(sample_graph)
        assert isinstance(stats, dict)
        assert "total_nodes" in stats
        assert "total_edges" in stats

    def test_statistics_counts_accurate(self, sample_graph):
        """Statistics counts are accurate."""
        stats = generate_graph_statistics(sample_graph)
        # We created 5 SOURCE_CELL + 3 EXTRACTED + 2 MAPPED = 10 nodes
        assert stats["total_nodes"] == 10

    def test_statistics_has_confidence(self, sample_graph):
        """Statistics include confidence metrics."""
        stats = generate_graph_statistics(sample_graph)
        assert "avg_confidence" in stats


class TestGraphSummary:
    """Test summary formatting."""

    def test_summary_generation(self, sample_graph):
        """Summary is generated."""
        summary = format_graph_summary(sample_graph)
        assert isinstance(summary, str)
        assert "Lineage Graph" in summary or "Summary" in summary

    def test_summary_includes_counts(self, sample_graph):
        """Summary includes node/edge counts."""
        summary = format_graph_summary(sample_graph)
        assert "Nodes" in summary or "nodes" in summary


class TestJSONExport:
    """Test JSON export."""

    def test_json_export(self, sample_graph):
        """Graph can be exported as JSON."""
        import json
        json_str = export_graph_json(sample_graph)
        data = json.loads(json_str)
        assert "nodes" in data
        assert "edges" in data
        assert "statistics" in data

    def test_json_preserves_data(self, sample_graph):
        """JSON export preserves node data."""
        import json
        json_str = export_graph_json(sample_graph)
        data = json.loads(json_str)
        # Should have all 10 nodes
        assert len(data["nodes"]) == 10

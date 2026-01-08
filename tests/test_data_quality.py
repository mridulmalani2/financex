"""
Tests for Data Quality Module (Stage 2)
"""

import pytest
from utils.data_quality import (
    calculate_mapping_coverage,
    calculate_avg_confidence,
    calculate_model_confidence,
    identify_low_confidence_areas,
    generate_quality_report,
    format_quality_dashboard,
    get_quality_score_breakdown
)
from utils.lineage_graph import FinancialLineageGraph, NodeType


@pytest.fixture
def sample_graph():
    """Create a sample lineage graph."""
    graph = FinancialLineageGraph()

    # Add 10 EXTRACTED nodes
    for i in range(10):
        graph.add_node(
            node_type=NodeType.EXTRACTED,
            label=f"Extracted {i}",
            value=1000 * i,
            confidence=1.00,
            period="2024"
        )

    # Add 8 MAPPED nodes (80% mapping coverage)
    for i in range(8):
        graph.add_node(
            node_type=NodeType.MAPPED,
            label=f"Mapped {i}",
            value=1000 * i,
            confidence=0.90,
            period="2024"
        )

    return graph


@pytest.fixture
def sample_confidence_scores():
    """Create sample confidence scores."""
    return {
        "Revenue": 0.95,
        "EBITDA": 0.90,
        "Net Income": 0.85,
        "Depreciation": 0.65,
        "Unknown Metric": 0.00
    }


class TestMappingCoverage:
    """Test mapping coverage calculation."""

    def test_coverage_calculation(self, sample_graph):
        """Coverage is calculated correctly."""
        coverage = calculate_mapping_coverage(sample_graph)
        # 8 mapped out of 10 extracted = 0.80
        assert abs(coverage - 0.80) < 0.01

    def test_coverage_range(self, sample_graph):
        """Coverage is between 0 and 1."""
        coverage = calculate_mapping_coverage(sample_graph)
        assert 0.0 <= coverage <= 1.0

    def test_empty_graph_coverage(self):
        """Empty graph has 0 coverage."""
        graph = FinancialLineageGraph()
        coverage = calculate_mapping_coverage(graph)
        assert coverage == 0.0


class TestConfidenceCalculation:
    """Test confidence calculations."""

    def test_avg_confidence(self, sample_graph):
        """Average confidence is calculated."""
        avg = calculate_avg_confidence(sample_graph)
        assert 0.0 <= avg <= 1.0

    def test_avg_confidence_by_type(self, sample_graph):
        """Average confidence can be filtered by type."""
        avg = calculate_avg_confidence(sample_graph, node_type=NodeType.MAPPED)
        # All mapped nodes have 0.90 confidence
        assert abs(avg - 0.90) < 0.01

    def test_model_confidence(self, sample_confidence_scores):
        """Model confidence is calculated."""
        conf = calculate_model_confidence("dcf", sample_confidence_scores)
        assert 0.0 <= conf <= 1.0


class TestLowConfidenceIdentification:
    """Test identification of low confidence areas."""

    def test_identify_low_confidence(self, sample_confidence_scores):
        """Low confidence areas are identified."""
        low_areas = identify_low_confidence_areas(sample_confidence_scores, threshold=0.70)
        # Should find "Depreciation" (0.65) and "Unknown Metric" (0.00)
        assert len(low_areas) >= 2

    def test_low_confidence_sorted(self, sample_confidence_scores):
        """Low confidence areas are sorted by severity."""
        low_areas = identify_low_confidence_areas(sample_confidence_scores, threshold=0.70)
        # First item should be lowest confidence or highest severity
        assert low_areas[0]["confidence"] <= low_areas[-1]["confidence"] or \
               low_areas[0]["severity"] in ["critical", "warning"]

    def test_low_confidence_has_recommendations(self, sample_confidence_scores):
        """Low confidence areas have recommendations."""
        low_areas = identify_low_confidence_areas(sample_confidence_scores, threshold=0.70)
        for area in low_areas:
            assert "recommendation" in area
            assert len(area["recommendation"]) > 0


class TestQualityReport:
    """Test quality report generation."""

    def test_report_generation(self, sample_graph, sample_confidence_scores):
        """Quality report is generated."""
        report = generate_quality_report(sample_graph, sample_confidence_scores)
        assert report is not None
        assert report.health_score >= 0
        assert report.health_score <= 100

    def test_report_has_metrics(self, sample_graph, sample_confidence_scores):
        """Quality report includes metrics."""
        report = generate_quality_report(sample_graph, sample_confidence_scores)
        assert len(report.metrics) > 0

    def test_report_has_recommendations(self, sample_graph, sample_confidence_scores):
        """Quality report includes recommendations."""
        report = generate_quality_report(sample_graph, sample_confidence_scores)
        assert len(report.recommendations) > 0

    def test_report_identifies_issues(self, sample_graph, sample_confidence_scores):
        """Quality report identifies issues."""
        report = generate_quality_report(sample_graph, sample_confidence_scores)
        # Should identify "Unknown Metric" with 0.00 confidence
        assert len(report.issues) > 0


class TestDashboardFormatting:
    """Test dashboard formatting."""

    def test_dashboard_generation(self, sample_graph, sample_confidence_scores):
        """Dashboard is formatted."""
        report = generate_quality_report(sample_graph, sample_confidence_scores)
        dashboard = format_quality_dashboard(report)
        assert isinstance(dashboard, str)
        assert "Quality Dashboard" in dashboard or "Health" in dashboard

    def test_dashboard_includes_health_score(self, sample_graph, sample_confidence_scores):
        """Dashboard includes health score."""
        report = generate_quality_report(sample_graph, sample_confidence_scores)
        dashboard = format_quality_dashboard(report)
        assert str(report.health_score) in dashboard


class TestQualityBreakdown:
    """Test quality score breakdown."""

    def test_breakdown_generation(self, sample_confidence_scores):
        """Breakdown is generated."""
        breakdown = get_quality_score_breakdown(sample_confidence_scores)
        assert isinstance(breakdown, dict)
        assert "total" in breakdown

    def test_breakdown_counts_accurate(self, sample_confidence_scores):
        """Breakdown counts are accurate."""
        breakdown = get_quality_score_breakdown(sample_confidence_scores)
        # Total should equal number of scores
        assert breakdown["total"] == len(sample_confidence_scores)

    def test_breakdown_categories(self, sample_confidence_scores):
        """Breakdown has all categories."""
        breakdown = get_quality_score_breakdown(sample_confidence_scores)
        assert "perfect" in breakdown
        assert "high" in breakdown
        assert "good" in breakdown
        assert "medium" in breakdown
        assert "low" in breakdown

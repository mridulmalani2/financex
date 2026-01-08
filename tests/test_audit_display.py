"""
Tests for Audit Display Module (Stage 2)
"""

import pytest
from utils.audit_display import (
    MappingDecision,
    AggregationDecision,
    CalculationDecision,
    format_audit_summary,
    format_mapping_audit,
    format_aggregation_audit,
    format_calculation_audit,
    generate_mapping_coverage_report,
    export_audit_trail_json
)


@pytest.fixture
def sample_mappings():
    """Create sample mapping decisions."""
    return [
        MappingDecision(
            source_label="Total Revenue",
            target_concept="us-gaap_Revenues",
            method="Exact Label Match",
            confidence=0.95
        ),
        MappingDecision(
            source_label="COGS",
            target_concept="us-gaap_CostOfRevenue",
            method="Alias",
            confidence=0.95
        ),
        MappingDecision(
            source_label="Unknown Item",
            target_concept="UNMAPPED",
            method="None",
            confidence=0.00
        )
    ]


@pytest.fixture
def sample_aggregations():
    """Create sample aggregation decisions."""
    return [
        AggregationDecision(
            bucket_name="Revenue",
            strategy="MAX",
            source_count=3,
            source_labels=["Total Revenue", "Net Sales", "Revenue"],
            result_value=1000000,
            confidence=0.95
        )
    ]


@pytest.fixture
def sample_calculations():
    """Create sample calculation decisions."""
    return [
        CalculationDecision(
            metric_name="Gross Profit",
            formula="Revenue - COGS",
            inputs={"Revenue": 1000000, "COGS": 600000},
            result=400000,
            confidence=0.95
        )
    ]


class TestMappingAudit:
    """Test mapping audit formatting."""

    def test_mapping_audit_generation(self, sample_mappings):
        """Mapping audit is generated."""
        audit = format_mapping_audit(sample_mappings)
        assert isinstance(audit, str)
        assert len(audit) > 0

    def test_mapping_audit_includes_all_items(self, sample_mappings):
        """Mapping audit includes all mappings."""
        audit = format_mapping_audit(sample_mappings)
        assert "Total Revenue" in audit
        assert "COGS" in audit

    def test_mapping_audit_shows_unmapped(self, sample_mappings):
        """Mapping audit shows unmapped items."""
        audit = format_mapping_audit(sample_mappings)
        assert "Unknown Item" in audit or "Unmapped" in audit


class TestAggregationAudit:
    """Test aggregation audit formatting."""

    def test_aggregation_audit_generation(self, sample_aggregations):
        """Aggregation audit is generated."""
        audit = format_aggregation_audit(sample_aggregations)
        assert isinstance(audit, str)
        assert "Revenue" in audit

    def test_aggregation_audit_shows_strategy(self, sample_aggregations):
        """Aggregation audit shows strategy."""
        audit = format_aggregation_audit(sample_aggregations)
        assert "MAX" in audit or "Strategy" in audit


class TestCalculationAudit:
    """Test calculation audit formatting."""

    def test_calculation_audit_generation(self, sample_calculations):
        """Calculation audit is generated."""
        audit = format_calculation_audit(sample_calculations)
        assert isinstance(audit, str)
        assert "Gross Profit" in audit

    def test_calculation_audit_shows_formula(self, sample_calculations):
        """Calculation audit shows formula."""
        audit = format_calculation_audit(sample_calculations)
        assert "Revenue - COGS" in audit or "Formula" in audit


class TestAuditSummary:
    """Test comprehensive audit summary."""

    def test_summary_generation(self, sample_mappings, sample_aggregations, sample_calculations):
        """Audit summary is generated."""
        summary = format_audit_summary(sample_mappings, sample_aggregations, sample_calculations)
        assert isinstance(summary, str)
        assert "Audit Trail" in summary or "Summary" in summary

    def test_summary_includes_all_sections(self, sample_mappings, sample_aggregations, sample_calculations):
        """Summary includes all decision types."""
        summary = format_audit_summary(sample_mappings, sample_aggregations, sample_calculations)
        # Should mention mappings, aggregations, calculations
        assert "Mapping" in summary or "mapping" in summary
        assert "Aggregation" in summary or "aggregation" in summary
        assert "Calculation" in summary or "calculation" in summary


class TestCoverageReport:
    """Test mapping coverage report."""

    def test_coverage_report_generation(self, sample_mappings):
        """Coverage report is generated."""
        report = generate_mapping_coverage_report(
            total_items=3,
            mapped_items=2,
            mappings=sample_mappings
        )
        assert isinstance(report, str)
        assert "Coverage" in report

    def test_coverage_shows_percentage(self, sample_mappings):
        """Coverage report shows percentage."""
        report = generate_mapping_coverage_report(
            total_items=3,
            mapped_items=2,
            mappings=sample_mappings
        )
        # 2/3 = 66.7%
        assert "66" in report or "67" in report


class TestJSONExport:
    """Test JSON export."""

    def test_json_export(self, sample_mappings, sample_aggregations, sample_calculations):
        """Audit trail can be exported as JSON."""
        data = export_audit_trail_json(sample_mappings, sample_aggregations, sample_calculations)
        assert isinstance(data, dict)
        assert "mappings" in data
        assert "aggregations" in data
        assert "calculations" in data

    def test_json_preserves_data(self, sample_mappings):
        """JSON export preserves mapping data."""
        data = export_audit_trail_json(sample_mappings, [], [])
        assert len(data["mappings"]) == 3

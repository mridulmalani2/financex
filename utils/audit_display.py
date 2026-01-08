"""
Audit Display Module
Formats audit trail information for UI display.

Part of Stage 2: UI Transparency & Debugging
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from utils.confidence_display import get_confidence_badge, get_confidence_emoji


class AuditCategory(Enum):
    """Categories of audit entries."""
    MAPPING = "mapping"
    AGGREGATION = "aggregation"
    CALCULATION = "calculation"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"


@dataclass
class MappingDecision:
    """Represents a single mapping decision."""
    source_label: str
    target_concept: str
    method: str
    confidence: float
    taxonomy: str = "US-GAAP"
    notes: Optional[str] = None


@dataclass
class AggregationDecision:
    """Represents an aggregation decision."""
    bucket_name: str
    strategy: str
    source_count: int
    source_labels: List[str]
    result_value: Optional[float] = None
    confidence: float = 1.0
    notes: Optional[str] = None


@dataclass
class CalculationDecision:
    """Represents a calculation decision."""
    metric_name: str
    formula: str
    inputs: Dict[str, Any]
    result: Optional[float] = None
    confidence: float = 1.0
    notes: Optional[str] = None


def format_audit_summary(
    mappings: List[MappingDecision],
    aggregations: List[AggregationDecision],
    calculations: List[CalculationDecision]
) -> str:
    """
    Generate comprehensive audit summary.

    Args:
        mappings: List of mapping decisions
        aggregations: List of aggregation decisions
        calculations: List of calculation decisions

    Returns:
        Markdown-formatted audit summary
    """
    md = "# 📋 Audit Trail - Processing Summary\n\n"

    # Overall stats
    total_decisions = len(mappings) + len(aggregations) + len(calculations)
    md += f"**Total Decisions:** {total_decisions}\n"
    md += f"- Mappings: {len(mappings)}\n"
    md += f"- Aggregations: {len(aggregations)}\n"
    md += f"- Calculations: {len(calculations)}\n\n"

    # Mapping decisions
    if mappings:
        md += "## Mapping Decisions\n\n"
        md += format_mapping_audit(mappings)
        md += "\n"

    # Aggregation strategies
    if aggregations:
        md += "## Aggregation Strategies\n\n"
        md += format_aggregation_audit(aggregations)
        md += "\n"

    # Calculation formulas
    if calculations:
        md += "## Calculation Formulas\n\n"
        md += format_calculation_audit(calculations)
        md += "\n"

    return md


def format_mapping_audit(mappings: List[MappingDecision]) -> str:
    """
    Format mapping decisions as table.

    Args:
        mappings: List of mapping decisions

    Returns:
        Markdown table
    """
    if not mappings:
        return "No mapping decisions recorded."

    # Group by success/failure
    successful = [m for m in mappings if m.target_concept and m.target_concept != "UNMAPPED"]
    unmapped = [m for m in mappings if not m.target_concept or m.target_concept == "UNMAPPED"]

    md = f"**Summary:** {len(successful)}/{len(mappings)} labels mapped successfully\n\n"

    # Successful mappings
    if successful:
        md += "### ✅ Successful Mappings\n\n"
        md += "| Source Label | Target Concept | Method | Confidence |\n"
        md += "|--------------|----------------|--------|------------|\n"

        for m in sorted(successful, key=lambda x: x.confidence, reverse=True):
            badge = get_confidence_badge(m.confidence)
            # Truncate long labels
            label = m.source_label[:40] + "..." if len(m.source_label) > 40 else m.source_label
            concept = m.target_concept[:40] + "..." if len(m.target_concept) > 40 else m.target_concept
            md += f"| {label} | `{concept}` | {m.method} | {badge} |\n"

        md += "\n"

    # Unmapped items
    if unmapped:
        md += "### ❌ Unmapped Items\n\n"
        md += "These items could not be mapped to standard concepts:\n\n"

        for m in unmapped:
            md += f"- **{m.source_label}**"
            if m.notes:
                md += f" - {m.notes}"
            md += "\n"

        md += "\n"

    # Breakdown by method
    md += "### Mapping Method Breakdown\n\n"

    method_counts = {}
    for m in successful:
        method_counts[m.method] = method_counts.get(m.method, 0) + 1

    for method, count in sorted(method_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(successful)) * 100
        md += f"- **{method}:** {count} ({pct:.1f}%)\n"

    return md


def format_aggregation_audit(aggregations: List[AggregationDecision]) -> str:
    """
    Format aggregation decisions.

    Args:
        aggregations: List of aggregation decisions

    Returns:
        Markdown formatted text
    """
    if not aggregations:
        return "No aggregation decisions recorded."

    md = f"**Total Buckets Aggregated:** {len(aggregations)}\n\n"

    for agg in aggregations:
        emoji = get_confidence_emoji(agg.confidence)
        md += f"### {emoji} {agg.bucket_name}\n\n"
        md += f"- **Strategy:** {agg.strategy}\n"
        md += f"- **Source Count:** {agg.source_count}\n"

        if agg.result_value is not None:
            md += f"- **Result:** {agg.result_value:,.0f}\n"

        md += f"- **Confidence:** {get_confidence_badge(agg.confidence)}\n"

        if agg.source_labels:
            md += f"\n**Source Labels:**\n"
            for label in agg.source_labels[:5]:  # Limit to 5 for brevity
                md += f"  - {label}\n"

            if len(agg.source_labels) > 5:
                md += f"  - ... and {len(agg.source_labels) - 5} more\n"

        if agg.notes:
            md += f"\n*Note: {agg.notes}*\n"

        md += "\n"

    return md


def format_calculation_audit(calculations: List[CalculationDecision]) -> str:
    """
    Format calculation decisions.

    Args:
        calculations: List of calculation decisions

    Returns:
        Markdown formatted text
    """
    if not calculations:
        return "No calculation decisions recorded."

    md = f"**Total Calculations:** {len(calculations)}\n\n"

    for calc in calculations:
        emoji = get_confidence_emoji(calc.confidence)
        md += f"### {emoji} {calc.metric_name}\n\n"
        md += f"**Formula:** `{calc.formula}`\n\n"

        if calc.inputs:
            md += "**Inputs:**\n"
            for key, value in calc.inputs.items():
                if isinstance(value, (int, float)):
                    md += f"  - {key} = {value:,.0f}\n"
                else:
                    md += f"  - {key} = {value}\n"

        if calc.result is not None:
            md += f"\n**Result:** {calc.result:,.0f}\n"

        md += f"\n**Confidence:** {get_confidence_badge(calc.confidence)}\n"

        if calc.notes:
            md += f"\n*Note: {calc.notes}*\n"

        md += "\n"

    return md


def generate_mapping_coverage_report(
    total_items: int,
    mapped_items: int,
    mappings: List[MappingDecision]
) -> str:
    """
    Generate mapping coverage report.

    Args:
        total_items: Total number of source items
        mapped_items: Number successfully mapped
        mappings: List of mapping decisions

    Returns:
        Markdown report
    """
    coverage_pct = (mapped_items / total_items * 100) if total_items > 0 else 0

    md = "## 📊 Mapping Coverage Report\n\n"

    # Coverage indicator
    if coverage_pct >= 95:
        emoji = "🟢"
        status = "Excellent"
    elif coverage_pct >= 85:
        emoji = "🟡"
        status = "Good"
    elif coverage_pct >= 70:
        emoji = "🟠"
        status = "Fair"
    else:
        emoji = "🔴"
        status = "Poor"

    md += f"### {emoji} Coverage: {coverage_pct:.1f}% ({status})\n\n"
    md += f"- **Mapped:** {mapped_items}/{total_items} items\n"
    md += f"- **Unmapped:** {total_items - mapped_items}/{total_items} items\n\n"

    # Confidence distribution
    if mappings:
        successful = [m for m in mappings if m.target_concept and m.target_concept != "UNMAPPED"]

        if successful:
            avg_conf = sum(m.confidence for m in successful) / len(successful)
            md += f"### Average Confidence: {get_confidence_badge(avg_conf)}\n\n"

            # Confidence buckets
            perfect = sum(1 for m in successful if m.confidence >= 1.0)
            high = sum(1 for m in successful if 0.90 <= m.confidence < 1.0)
            good = sum(1 for m in successful if 0.70 <= m.confidence < 0.90)
            medium = sum(1 for m in successful if 0.40 <= m.confidence < 0.70)
            low = sum(1 for m in successful if m.confidence < 0.40)

            md += "**Confidence Distribution:**\n"
            md += f"- 🟢 Perfect (1.00): {perfect}\n"
            md += f"- 🟢 High (0.90-0.99): {high}\n"
            md += f"- 🟡 Good (0.70-0.89): {good}\n"
            md += f"- 🟠 Medium (0.40-0.69): {medium}\n"
            md += f"- 🔴 Low (0.00-0.39): {low}\n"

    return md


def generate_audit_recommendations(
    mappings: List[MappingDecision],
    aggregations: List[AggregationDecision]
) -> str:
    """
    Generate recommendations based on audit findings.

    Args:
        mappings: List of mapping decisions
        aggregations: List of aggregation decisions

    Returns:
        Markdown recommendations
    """
    md = "## 💡 Recommendations\n\n"

    recommendations = []

    # Check for unmapped items
    unmapped = [m for m in mappings if not m.target_concept or m.target_concept == "UNMAPPED"]
    if unmapped:
        recommendations.append(
            f"**Add {len(unmapped)} custom mappings to Analyst Brain** to improve coverage"
        )

    # Check for low confidence mappings
    low_conf = [m for m in mappings if m.target_concept and 0 < m.confidence < 0.70]
    if low_conf:
        recommendations.append(
            f"**Review {len(low_conf)} low-confidence mappings** - consider adding to Analyst Brain"
        )

    # Check for keyword-only mappings
    keyword_mappings = [m for m in mappings if m.method == "Keyword Match"]
    if keyword_mappings and len(keyword_mappings) > 5:
        recommendations.append(
            f"**Verify {len(keyword_mappings)} keyword-based mappings** - ensure accuracy"
        )

    # Check for aggregations with low confidence
    low_conf_agg = [a for a in aggregations if a.confidence < 0.70]
    if low_conf_agg:
        recommendations.append(
            f"**Review {len(low_conf_agg)} aggregations with low confidence** - verify source data"
        )

    # Output recommendations
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            md += f"{i}. {rec}\n"
    else:
        md += "✅ No issues found - data quality is excellent!\n"

    md += "\n"

    return md


def export_audit_trail_json(
    mappings: List[MappingDecision],
    aggregations: List[AggregationDecision],
    calculations: List[CalculationDecision]
) -> Dict[str, Any]:
    """
    Export audit trail as JSON-serializable dict.

    Args:
        mappings: List of mapping decisions
        aggregations: List of aggregation decisions
        calculations: List of calculation decisions

    Returns:
        Dict with audit trail data
    """
    return {
        "mappings": [
            {
                "source_label": m.source_label,
                "target_concept": m.target_concept,
                "method": m.method,
                "confidence": m.confidence,
                "taxonomy": m.taxonomy,
                "notes": m.notes
            }
            for m in mappings
        ],
        "aggregations": [
            {
                "bucket_name": a.bucket_name,
                "strategy": a.strategy,
                "source_count": a.source_count,
                "source_labels": a.source_labels,
                "result_value": a.result_value,
                "confidence": a.confidence,
                "notes": a.notes
            }
            for a in aggregations
        ],
        "calculations": [
            {
                "metric_name": c.metric_name,
                "formula": c.formula,
                "inputs": c.inputs,
                "result": c.result,
                "confidence": c.confidence,
                "notes": c.notes
            }
            for c in calculations
        ],
        "summary": {
            "total_decisions": len(mappings) + len(aggregations) + len(calculations),
            "mapping_count": len(mappings),
            "aggregation_count": len(aggregations),
            "calculation_count": len(calculations)
        }
    }


def create_quick_audit_summary(
    mapped_count: int,
    total_count: int,
    avg_confidence: float
) -> str:
    """
    Create a one-line audit summary.

    Args:
        mapped_count: Number of successfully mapped items
        total_count: Total number of items
        avg_confidence: Average confidence score

    Returns:
        One-line summary string
    """
    coverage = (mapped_count / total_count * 100) if total_count > 0 else 0
    emoji = get_confidence_emoji(avg_confidence)

    return (
        f"{emoji} Mapped {mapped_count}/{total_count} items ({coverage:.1f}%) "
        f"with avg confidence {avg_confidence:.2f}"
    )

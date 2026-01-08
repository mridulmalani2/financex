"""
Data Quality Module
Calculates data quality metrics and provides actionable recommendations.

Part of Stage 2: UI Transparency & Debugging
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from utils.lineage_graph import FinancialLineageGraph, NodeType
from utils.confidence_display import (
    get_confidence_emoji,
    get_confidence_badge,
    get_confidence_health_score
)


@dataclass
class QualityMetric:
    """Represents a quality metric."""
    name: str
    value: float
    status: str  # "excellent", "good", "fair", "poor"
    emoji: str
    notes: Optional[str] = None


@dataclass
class QualityIssue:
    """Represents a data quality issue."""
    severity: str  # "critical", "warning", "info"
    metric_name: str
    issue_description: str
    current_value: float
    recommendation: str
    impact: str  # "high", "medium", "low"


@dataclass
class DataQualityReport:
    """Complete data quality report."""
    health_score: int  # 0-100
    metrics: List[QualityMetric]
    issues: List[QualityIssue]
    recommendations: List[str]
    summary: str


def calculate_mapping_coverage(graph: FinancialLineageGraph) -> float:
    """
    Calculate percentage of source items that were successfully mapped.

    Args:
        graph: Lineage graph

    Returns:
        Coverage percentage (0.0 to 1.0)
    """
    # Count EXTRACTED nodes (all source items)
    extracted_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.EXTRACTED]

    if not extracted_nodes:
        return 0.0

    # Count MAPPED nodes (successfully mapped items)
    mapped_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.MAPPED]

    return len(mapped_nodes) / len(extracted_nodes)


def calculate_avg_confidence(
    graph: FinancialLineageGraph,
    node_type: Optional[NodeType] = None
) -> float:
    """
    Calculate average confidence score across nodes.

    Args:
        graph: Lineage graph
        node_type: Optional node type to filter by

    Returns:
        Average confidence (0.0 to 1.0)
    """
    nodes = list(graph.nodes.values())

    if node_type:
        nodes = [n for n in nodes if n.node_type == node_type]

    if not nodes:
        return 0.0

    confidences = [n.confidence for n in nodes if n.confidence is not None]

    if not confidences:
        return 0.0

    return sum(confidences) / len(confidences)


def calculate_model_confidence(
    model_name: str,
    confidence_scores: Dict[str, float]
) -> float:
    """
    Calculate average confidence for a specific model.

    Args:
        model_name: Model name ("dcf", "lbo", "comps")
        confidence_scores: Dict mapping metric names to confidence scores

    Returns:
        Average confidence for model
    """
    if not confidence_scores:
        return 0.0

    # Filter metrics relevant to this model
    model_metrics = {
        "dcf": ["Revenue", "EBITDA", "EBIT", "Net Income", "FCF", "NOPAT", "NWC", "CapEx"],
        "lbo": ["EBITDA", "Debt", "Net Debt", "Leverage Ratio", "Interest Coverage"],
        "comps": ["Revenue", "EBITDA", "EBIT", "Net Income", "Margins", "EPS"]
    }

    relevant_metrics = model_metrics.get(model_name.lower(), [])

    if not relevant_metrics:
        # If no specific metrics defined, use all
        return sum(confidence_scores.values()) / len(confidence_scores)

    # Calculate average for relevant metrics
    relevant_scores = []
    for metric in relevant_metrics:
        # Try exact match first
        if metric in confidence_scores:
            relevant_scores.append(confidence_scores[metric])
        else:
            # Try partial match
            for key, value in confidence_scores.items():
                if metric.lower() in key.lower():
                    relevant_scores.append(value)
                    break

    if not relevant_scores:
        return 0.0

    return sum(relevant_scores) / len(relevant_scores)


def identify_low_confidence_areas(
    confidence_scores: Dict[str, float],
    threshold: float = 0.70
) -> List[Dict[str, Any]]:
    """
    Identify metrics with low confidence scores.

    Args:
        confidence_scores: Dict mapping metric names to confidence scores
        threshold: Confidence threshold (default 0.70)

    Returns:
        List of low-confidence metrics with recommendations
    """
    low_conf_areas = []

    for metric, score in confidence_scores.items():
        if score < threshold:
            # Determine severity
            if score < 0.40:
                severity = "critical"
                impact = "high"
            elif score < 0.60:
                severity = "warning"
                impact = "medium"
            else:
                severity = "info"
                impact = "low"

            # Generate recommendation
            if score == 0.0:
                recommendation = f"'{metric}' is unmapped - verify source data or add custom mapping"
            elif score < 0.70:
                recommendation = f"'{metric}' has low confidence - consider adding to Analyst Brain"
            else:
                recommendation = f"'{metric}' confidence is acceptable but could be improved"

            low_conf_areas.append({
                "metric": metric,
                "confidence": score,
                "severity": severity,
                "impact": impact,
                "recommendation": recommendation
            })

    # Sort by severity and confidence (lowest first)
    low_conf_areas.sort(key=lambda x: (
        {"critical": 0, "warning": 1, "info": 2}[x["severity"]],
        x["confidence"]
    ))

    return low_conf_areas


def generate_quality_report(
    graph: FinancialLineageGraph,
    confidence_scores: Dict[str, float],
    model_scores: Optional[Dict[str, float]] = None
) -> DataQualityReport:
    """
    Generate comprehensive data quality report.

    Args:
        graph: Lineage graph
        confidence_scores: Dict of confidence scores
        model_scores: Optional dict of per-model average confidences

    Returns:
        DataQualityReport object
    """
    # Calculate metrics
    mapping_coverage = calculate_mapping_coverage(graph)
    avg_confidence = calculate_avg_confidence(graph, node_type=NodeType.MAPPED)
    health_score = get_confidence_health_score(confidence_scores)

    # Create quality metrics
    metrics = []

    # Mapping coverage metric
    if mapping_coverage >= 0.95:
        status, emoji = "excellent", "🟢"
    elif mapping_coverage >= 0.85:
        status, emoji = "good", "🟡"
    elif mapping_coverage >= 0.70:
        status, emoji = "fair", "🟠"
    else:
        status, emoji = "poor", "🔴"

    metrics.append(QualityMetric(
        name="Mapping Coverage",
        value=mapping_coverage * 100,
        status=status,
        emoji=emoji,
        notes=f"{mapping_coverage*100:.1f}% of source items mapped"
    ))

    # Average confidence metric
    if avg_confidence >= 0.90:
        status, emoji = "excellent", "🟢"
    elif avg_confidence >= 0.70:
        status, emoji = "good", "🟡"
    elif avg_confidence >= 0.50:
        status, emoji = "fair", "🟠"
    else:
        status, emoji = "poor", "🔴"

    metrics.append(QualityMetric(
        name="Average Confidence",
        value=avg_confidence * 100,
        status=status,
        emoji=emoji,
        notes=f"{avg_confidence:.2f} average confidence"
    ))

    # Model-specific metrics
    if model_scores:
        for model_name, score in model_scores.items():
            if score >= 0.90:
                status, emoji = "excellent", "🟢"
            elif score >= 0.70:
                status, emoji = "good", "🟡"
            else:
                status, emoji = "fair", "🟠"

            metrics.append(QualityMetric(
                name=f"{model_name.upper()} Model Confidence",
                value=score * 100,
                status=status,
                emoji=emoji,
                notes=f"{score:.2f} confidence for {model_name.upper()}"
            ))

    # Identify issues
    issues = []
    low_conf_areas = identify_low_confidence_areas(confidence_scores)

    for area in low_conf_areas[:10]:  # Top 10 issues
        issues.append(QualityIssue(
            severity=area["severity"],
            metric_name=area["metric"],
            issue_description=f"Low confidence score ({area['confidence']:.2f})",
            current_value=area["confidence"],
            recommendation=area["recommendation"],
            impact=area["impact"]
        ))

    # Generate recommendations
    recommendations = []

    if mapping_coverage < 0.95:
        unmapped_count = int((1 - mapping_coverage) * len(confidence_scores))
        recommendations.append(
            f"Add {unmapped_count} custom mappings to Analyst Brain to improve coverage to 95%+"
        )

    low_conf_count = len([s for s in confidence_scores.values() if 0 < s < 0.70])
    if low_conf_count > 0:
        recommendations.append(
            f"Review {low_conf_count} low-confidence mappings and add to Analyst Brain"
        )

    if avg_confidence < 0.80:
        recommendations.append(
            "Overall confidence is below optimal - focus on improving keyword-based mappings"
        )

    if not recommendations:
        recommendations.append("✅ Data quality is excellent - no immediate actions needed!")

    # Generate summary
    if health_score >= 90:
        health_status = "Excellent"
        emoji = "🟢"
    elif health_score >= 75:
        health_status = "Good"
        emoji = "🟡"
    elif health_score >= 60:
        health_status = "Fair"
        emoji = "🟠"
    else:
        health_status = "Poor"
        emoji = "🔴"

    summary = (
        f"{emoji} Overall Health: {health_score}/100 ({health_status})\n"
        f"Mapping Coverage: {mapping_coverage*100:.1f}%\n"
        f"Average Confidence: {avg_confidence:.2f}"
    )

    return DataQualityReport(
        health_score=health_score,
        metrics=metrics,
        issues=issues,
        recommendations=recommendations,
        summary=summary
    )


def format_quality_dashboard(report: DataQualityReport) -> str:
    """
    Format quality report as dashboard.

    Args:
        report: DataQualityReport object

    Returns:
        Markdown dashboard
    """
    md = "# 📊 Data Quality Dashboard\n\n"

    # Overall health
    if report.health_score >= 90:
        emoji = "🟢"
    elif report.health_score >= 75:
        emoji = "🟡"
    else:
        emoji = "🔴"

    md += f"## {emoji} Overall Health: {report.health_score}/100\n\n"

    # Metrics
    md += "## Quality Metrics\n\n"

    for metric in report.metrics:
        md += f"### {metric.emoji} {metric.name}: {metric.value:.1f}%\n"
        if metric.notes:
            md += f"_{metric.notes}_\n"
        md += "\n"

    # Issues
    if report.issues:
        md += "## ⚠️ Issues Detected\n\n"

        critical = [i for i in report.issues if i.severity == "critical"]
        warnings = [i for i in report.issues if i.severity == "warning"]
        info = [i for i in report.issues if i.severity == "info"]

        if critical:
            md += "### 🔴 Critical Issues\n\n"
            for issue in critical:
                md += f"- **{issue.metric_name}**: {issue.issue_description}\n"
                md += f"  - Current: {get_confidence_badge(issue.current_value)}\n"
                md += f"  - Recommendation: {issue.recommendation}\n\n"

        if warnings:
            md += "### 🟡 Warnings\n\n"
            for issue in warnings:
                md += f"- **{issue.metric_name}**: {issue.issue_description}\n"
                md += f"  - Recommendation: {issue.recommendation}\n\n"

        if info:
            md += "### 🔵 Informational\n\n"
            for issue in info[:5]:  # Limit to 5
                md += f"- **{issue.metric_name}**: {issue.issue_description}\n\n"

    # Recommendations
    md += "## 💡 Recommendations\n\n"

    for i, rec in enumerate(report.recommendations, 1):
        md += f"{i}. {rec}\n"

    return md


def calculate_improvement_impact(
    current_scores: Dict[str, float],
    improvements: Dict[str, float]
) -> Dict[str, Any]:
    """
    Calculate impact of potential improvements.

    Args:
        current_scores: Current confidence scores
        improvements: Dict of metric -> new confidence score

    Returns:
        Dict with impact analysis
    """
    current_avg = sum(current_scores.values()) / len(current_scores)
    current_health = get_confidence_health_score(current_scores)

    # Apply improvements
    new_scores = current_scores.copy()
    new_scores.update(improvements)

    new_avg = sum(new_scores.values()) / len(new_scores)
    new_health = get_confidence_health_score(new_scores)

    return {
        "current_avg_confidence": current_avg,
        "new_avg_confidence": new_avg,
        "confidence_improvement": new_avg - current_avg,
        "current_health": current_health,
        "new_health": new_health,
        "health_improvement": new_health - current_health,
        "metrics_improved": len(improvements),
        "percentage_improvement": ((new_avg - current_avg) / current_avg * 100) if current_avg > 0 else 0
    }


def get_quality_score_breakdown(
    confidence_scores: Dict[str, float]
) -> Dict[str, int]:
    """
    Get breakdown of confidence scores by category.

    Args:
        confidence_scores: Dict of confidence scores

    Returns:
        Dict with count in each category
    """
    return {
        "perfect": sum(1 for s in confidence_scores.values() if s >= 1.0),
        "high": sum(1 for s in confidence_scores.values() if 0.90 <= s < 1.0),
        "good": sum(1 for s in confidence_scores.values() if 0.70 <= s < 0.90),
        "medium": sum(1 for s in confidence_scores.values() if 0.40 <= s < 0.70),
        "low": sum(1 for s in confidence_scores.values() if s < 0.40),
        "total": len(confidence_scores)
    }


def prioritize_fixes(
    low_confidence_areas: List[Dict[str, Any]],
    max_fixes: int = 5
) -> List[Dict[str, Any]]:
    """
    Prioritize which low-confidence areas to fix first.

    Args:
        low_confidence_areas: List of low-confidence metrics
        max_fixes: Maximum number of fixes to recommend

    Returns:
        Prioritized list of fixes
    """
    # Sort by impact (critical first) and confidence (lowest first)
    sorted_areas = sorted(
        low_confidence_areas,
        key=lambda x: (
            {"critical": 0, "warning": 1, "info": 2}[x["severity"]],
            x["confidence"]
        )
    )

    return sorted_areas[:max_fixes]

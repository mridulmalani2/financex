"""
Lineage Explainer Module
Provides "Why This Number?" functionality by explaining value lineage.

Part of Stage 2: UI Transparency & Debugging
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from utils.lineage_graph import (
    FinancialLineageGraph,
    NodeType,
    EdgeType,
    FinancialNode,
    FinancialEdge
)
from utils.confidence_display import get_confidence_badge, get_confidence_emoji
import json


@dataclass
class LineageStep:
    """Represents one step in a lineage path."""
    step_number: int
    node_id: str
    node_type: NodeType
    label: str
    value: Optional[float]
    confidence: float
    transformation: str
    method: str
    details: Dict[str, Any]


@dataclass
class LineageExplanation:
    """Complete explanation of a value's lineage."""
    target_node_id: str
    target_label: str
    target_value: Optional[float]
    target_confidence: float
    path: List[LineageStep]
    alternatives: List[Dict[str, Any]]
    summary: str


def explain_value(
    node_id: str,
    graph: FinancialLineageGraph,
    include_alternatives: bool = True
) -> LineageExplanation:
    """
    Generate complete explanation for how a value was calculated.

    Args:
        node_id: Target node to explain
        graph: Lineage graph containing the node
        include_alternatives: Include alternative paths considered

    Returns:
        LineageExplanation object with complete lineage
    """
    # Get target node
    target_node = graph.get_node(node_id)
    if not target_node:
        raise ValueError(f"Node {node_id} not found in graph")

    # Trace backward to source
    ancestors = graph.trace_backward(node_id)

    # Build lineage path
    path = _build_lineage_path(node_id, ancestors, graph)

    # Find alternatives
    alternatives = []
    if include_alternatives:
        alternatives = _find_alternatives(node_id, graph)

    # Generate summary
    summary = _generate_summary(target_node, path, graph)

    return LineageExplanation(
        target_node_id=node_id,
        target_label=target_node.label,
        target_value=target_node.value,
        target_confidence=target_node.confidence,
        path=path,
        alternatives=alternatives,
        summary=summary
    )


def _build_lineage_path(
    node_id: str,
    ancestors: List[FinancialNode],
    graph: FinancialLineageGraph
) -> List[LineageStep]:
    """Build step-by-step lineage path from ancestors."""
    # Sort ancestors by depth (SOURCE_CELL first, CALCULATED last)
    type_order = {
        NodeType.SOURCE_CELL: 0,
        NodeType.EXTRACTED: 1,
        NodeType.MAPPED: 2,
        NodeType.AGGREGATED: 3,
        NodeType.CALCULATED: 4
    }

    sorted_ancestors = sorted(ancestors, key=lambda n: type_order.get(n.node_type, 99))

    # Build path
    path = []
    for i, node in enumerate(sorted_ancestors, 1):
        # Get incoming edge to understand transformation
        incoming_edges = graph.get_incoming_edges(node.node_id)

        transformation = "Initial"
        method = "Source data"

        if incoming_edges:
            edge = graph.get_edge(incoming_edges[0])
            transformation = edge.edge_type.value if edge.edge_type else "Unknown"
            method = edge.method or "Unknown"

        # Extract details
        details = {
            "node_type": node.node_type.value if node.node_type else "unknown",
            "period": node.period,
            "concept": node.data.get("concept") if node.data else None,
            "source": node.data.get("source") if node.data else None,
        }

        step = LineageStep(
            step_number=i,
            node_id=node.node_id,
            node_type=node.node_type,
            label=node.label,
            value=node.value,
            confidence=node.confidence,
            transformation=transformation,
            method=method,
            details=details
        )

        path.append(step)

    return path


def _find_alternatives(node_id: str, graph: FinancialLineageGraph) -> List[Dict[str, Any]]:
    """Find alternative paths or values that were considered but not used."""
    alternatives = []

    # Get edges involving this node
    all_edges = graph.edges.values()

    # Look for inactive edges (alternatives)
    for edge in all_edges:
        if edge.target_node_id == node_id and not edge.is_active:
            # This is an alternative that was not taken
            source_nodes = [graph.get_node(sid) for sid in edge.source_node_ids]

            alternatives.append({
                "reason": edge.data.get("inactive_reason", "Alternative not selected"),
                "method": edge.method,
                "confidence": edge.confidence,
                "sources": [
                    {
                        "label": node.label,
                        "value": node.value
                    }
                    for node in source_nodes if node
                ]
            })

    return alternatives


def _generate_summary(
    target_node: FinancialNode,
    path: List[LineageStep],
    graph: FinancialLineageGraph
) -> str:
    """Generate human-readable summary of lineage."""
    if not path:
        return "No lineage information available."

    # Get source step (first)
    source_step = path[0]

    # Get final transformation
    final_step = path[-1] if len(path) > 1 else source_step

    summary = f"**{target_node.label}** = **{target_node.value:,.0f}** "
    summary += f"({get_confidence_badge(target_node.confidence)})\n\n"

    if len(path) == 1:
        summary += f"This value comes directly from the source data: "
        summary += f"'{source_step.label}'"
    else:
        summary += f"This value originated from Excel cell '{source_step.label}' "
        summary += f"and went through {len(path) - 1} transformation(s):\n\n"

        for step in path[1:]:
            emoji = get_confidence_emoji(step.confidence)
            summary += f"{step.step_number}. {emoji} **{step.transformation}**: {step.method}\n"

    return summary


def get_lineage_path(node_id: str, graph: FinancialLineageGraph) -> List[Dict[str, Any]]:
    """
    Get lineage path as list of dicts (JSON-serializable).

    Args:
        node_id: Target node
        graph: Lineage graph

    Returns:
        List of path steps as dicts
    """
    explanation = explain_value(node_id, graph, include_alternatives=False)

    path = []
    for step in explanation.path:
        path.append({
            "step": step.step_number,
            "node_id": step.node_id,
            "node_type": step.node_type.value if step.node_type else "unknown",
            "label": step.label,
            "value": step.value,
            "confidence": step.confidence,
            "transformation": step.transformation,
            "method": step.method,
            "details": step.details
        })

    return path


def format_lineage_markdown(explanation: LineageExplanation) -> str:
    """
    Format lineage explanation as Markdown.

    Args:
        explanation: LineageExplanation object

    Returns:
        Markdown-formatted string
    """
    md = f"# 🔍 Why is {explanation.target_label} = "

    if explanation.target_value is not None:
        md += f"{explanation.target_value:,.0f}?\n\n"
    else:
        md += "this value?\n\n"

    # Summary
    md += explanation.summary + "\n\n"

    # Detailed path
    md += "## 📊 Detailed Lineage Path\n\n"

    for step in explanation.path:
        emoji = get_confidence_emoji(step.confidence)
        md += f"### Step {step.step_number}: {step.transformation}\n\n"
        md += f"- **Label:** {step.label}\n"

        if step.value is not None:
            md += f"- **Value:** {step.value:,.0f}\n"

        md += f"- **Confidence:** {emoji} {step.confidence:.2f}\n"
        md += f"- **Method:** {step.method}\n"

        if step.details.get("concept"):
            md += f"- **XBRL Concept:** `{step.details['concept']}`\n"

        md += "\n"

    # Confidence breakdown
    md += "## 🎯 Confidence Breakdown\n\n"
    md += "| Step | Transformation | Confidence |\n"
    md += "|------|----------------|------------|\n"

    for step in explanation.path:
        badge = get_confidence_badge(step.confidence)
        md += f"| {step.step_number} | {step.transformation} | {badge} |\n"

    md += f"\n**Final Confidence:** {get_confidence_badge(explanation.target_confidence)}\n\n"

    # Alternatives
    if explanation.alternatives:
        md += "## ⚠️ Alternatives Considered\n\n"
        md += f"{len(explanation.alternatives)} alternative(s) were considered:\n\n"

        for i, alt in enumerate(explanation.alternatives, 1):
            md += f"{i}. **{alt['method']}** (Confidence: {alt['confidence']:.2f})\n"
            md += f"   - Reason not used: {alt['reason']}\n"

    return md


def format_lineage_json(explanation: LineageExplanation) -> str:
    """
    Format lineage explanation as JSON.

    Args:
        explanation: LineageExplanation object

    Returns:
        JSON string
    """
    data = {
        "target": {
            "node_id": explanation.target_node_id,
            "label": explanation.target_label,
            "value": explanation.target_value,
            "confidence": explanation.target_confidence
        },
        "path": [
            {
                "step": step.step_number,
                "node_id": step.node_id,
                "node_type": step.node_type.value if step.node_type else "unknown",
                "label": step.label,
                "value": step.value,
                "confidence": step.confidence,
                "transformation": step.transformation,
                "method": step.method,
                "details": step.details
            }
            for step in explanation.path
        ],
        "alternatives": explanation.alternatives,
        "summary": explanation.summary
    }

    return json.dumps(data, indent=2)


def trace_to_excel_source(node_id: str, graph: FinancialLineageGraph) -> Optional[Dict[str, Any]]:
    """
    Trace a value back to its original Excel source cell.

    Args:
        node_id: Target node
        graph: Lineage graph

    Returns:
        Dict with Excel source information, or None if not found
    """
    ancestors = graph.trace_backward(node_id)

    # Find SOURCE_CELL nodes
    source_cells = [n for n in ancestors if n.node_type == NodeType.SOURCE_CELL]

    if not source_cells:
        return None

    # Use first source cell (there may be multiple for aggregations)
    source = source_cells[0]

    return {
        "node_id": source.node_id,
        "label": source.label,
        "value": source.value,
        "sheet": source.data.get("sheet") if source.data else None,
        "row": source.data.get("row") if source.data else None,
        "column": source.data.get("column") if source.data else None,
        "period": source.period,
        "raw_value": source.data.get("raw_value") if source.data else None,
    }


def get_value_provenance(node_id: str, graph: FinancialLineageGraph) -> str:
    """
    Get one-line provenance statement for a value.

    Args:
        node_id: Target node
        graph: Lineage graph

    Returns:
        One-line provenance string
    """
    excel_source = trace_to_excel_source(node_id, graph)

    if not excel_source:
        return "Source unknown"

    sheet = excel_source.get("sheet", "Unknown")
    label = excel_source.get("label", "Unknown")
    period = excel_source.get("period", "Unknown")

    return f"From Excel: '{label}' ({sheet}, {period})"


def compare_lineages(node_id_1: str, node_id_2: str, graph: FinancialLineageGraph) -> str:
    """
    Compare lineages of two values.

    Args:
        node_id_1: First node
        node_id_2: Second node
        graph: Lineage graph

    Returns:
        Comparison text (Markdown)
    """
    exp1 = explain_value(node_id_1, graph, include_alternatives=False)
    exp2 = explain_value(node_id_2, graph, include_alternatives=False)

    md = "# Lineage Comparison\n\n"
    md += "## Value 1\n"
    md += f"**{exp1.target_label}** = {exp1.target_value:,.0f} "
    md += f"({get_confidence_badge(exp1.target_confidence)})\n"
    md += f"- Steps: {len(exp1.path)}\n"
    md += f"- Source: {get_value_provenance(node_id_1, graph)}\n\n"

    md += "## Value 2\n"
    md += f"**{exp2.target_label}** = {exp2.target_value:,.0f} "
    md += f"({get_confidence_badge(exp2.target_confidence)})\n"
    md += f"- Steps: {len(exp2.path)}\n"
    md += f"- Source: {get_value_provenance(node_id_2, graph)}\n\n"

    # Check for common ancestry
    ancestors1 = set(step.node_id for step in exp1.path)
    ancestors2 = set(step.node_id for step in exp2.path)
    common = ancestors1 & ancestors2

    if common:
        md += f"## Common Ancestors\n"
        md += f"These values share {len(common)} common ancestor node(s).\n"
    else:
        md += f"## No Common Ancestors\n"
        md += f"These values have completely independent lineages.\n"

    return md

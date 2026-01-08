"""
Graph Visualizer Module
Generates visual representations of lineage graphs.

Part of Stage 2: UI Transparency & Debugging
"""

from typing import Dict, List, Optional, Set
from utils.lineage_graph import (
    FinancialLineageGraph,
    NodeType,
    EdgeType,
    FinancialNode,
    FinancialEdge
)
from utils.confidence_display import get_confidence_color, get_confidence_emoji
import json


def graph_to_mermaid(
    graph: FinancialLineageGraph,
    max_nodes: int = 50,
    include_inactive: bool = False
) -> str:
    """
    Convert lineage graph to Mermaid diagram syntax.

    Args:
        graph: Lineage graph to visualize
        max_nodes: Maximum number of nodes to include
        include_inactive: Include inactive edges

    Returns:
        Mermaid diagram string
    """
    mermaid = "graph TD\n"

    # Get nodes to include (limit for performance)
    nodes = list(graph.nodes.values())[:max_nodes]

    # Node styling by type
    node_styles = {
        NodeType.SOURCE_CELL: ("([", "])"),  # Stadium shape
        NodeType.EXTRACTED: ("[", "]"),      # Rectangle
        NodeType.MAPPED: ("{", "}"),         # Rhombus
        NodeType.AGGREGATED: ("[(", ")]"),   # Cylindrical
        NodeType.CALCULATED: ("((", "))"),   # Circle
    }

    # Add nodes
    for node in nodes:
        # Shorten label for readability
        label = node.label[:30] + "..." if len(node.label) > 30 else node.label

        # Add confidence emoji
        emoji = get_confidence_emoji(node.confidence)

        # Get node shape
        start, end = node_styles.get(node.node_type, ("[", "]"))

        # Create node definition
        node_def = f"    {node.node_id}{start}\"{emoji} {label}\"{end}\n"
        mermaid += node_def

    # Add edges
    node_ids = set(n.node_id for n in nodes)

    for edge in graph.edges.values():
        if not include_inactive and not edge.is_active:
            continue

        # Only include edges between visible nodes
        if edge.target_node_id not in node_ids:
            continue

        valid_sources = [sid for sid in edge.source_node_ids if sid in node_ids]
        if not valid_sources:
            continue

        # Add edges from each source to target
        for source_id in valid_sources:
            # Edge label (transformation method)
            edge_label = edge.method[:20] if edge.method else ""

            # Edge style based on confidence
            style = "-->" if edge.is_active else "-.->"

            edge_def = f"    {source_id} {style}|{edge_label}| {edge.target_node_id}\n"
            mermaid += edge_def

    # Add styling
    mermaid += "\n    classDef sourceCell fill:#e3f2fd,stroke:#1976d2\n"
    mermaid += "    classDef extracted fill:#f3e5f5,stroke:#7b1fa2\n"
    mermaid += "    classDef mapped fill:#fff3e0,stroke:#f57c00\n"
    mermaid += "    classDef aggregated fill:#e8f5e9,stroke:#388e3c\n"
    mermaid += "    classDef calculated fill:#fce4ec,stroke:#c2185b\n"

    # Apply classes to nodes
    for node_type, class_name in [
        (NodeType.SOURCE_CELL, "sourceCell"),
        (NodeType.EXTRACTED, "extracted"),
        (NodeType.MAPPED, "mapped"),
        (NodeType.AGGREGATED, "aggregated"),
        (NodeType.CALCULATED, "calculated"),
    ]:
        type_nodes = [n.node_id for n in nodes if n.node_type == node_type]
        if type_nodes:
            mermaid += f"    class {','.join(type_nodes)} {class_name}\n"

    return mermaid


def generate_graph_html(
    graph: FinancialLineageGraph,
    max_nodes: int = 50,
    width: int = 800,
    height: int = 600
) -> str:
    """
    Generate interactive HTML visualization of graph.

    Args:
        graph: Lineage graph to visualize
        max_nodes: Maximum number of nodes
        width: Width in pixels
        height: Height in pixels

    Returns:
        HTML string with embedded Mermaid diagram
    """
    mermaid_code = graph_to_mermaid(graph, max_nodes=max_nodes)

    html = f"""
    <div class="mermaid-container" style="width: {width}px; height: {height}px; overflow: auto;">
        <div class="mermaid">
            {mermaid_code}
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
    """

    return html


def graph_to_dot(graph: FinancialLineageGraph, max_nodes: int = 50) -> str:
    """
    Convert lineage graph to Graphviz DOT format.

    Args:
        graph: Lineage graph to visualize
        max_nodes: Maximum number of nodes

    Returns:
        DOT format string
    """
    dot = "digraph LineageGraph {\n"
    dot += "    rankdir=TB;\n"
    dot += "    node [style=filled];\n\n"

    # Node colors by type
    node_colors = {
        NodeType.SOURCE_CELL: "#e3f2fd",
        NodeType.EXTRACTED: "#f3e5f5",
        NodeType.MAPPED: "#fff3e0",
        NodeType.AGGREGATED: "#e8f5e9",
        NodeType.CALCULATED: "#fce4ec",
    }

    # Get nodes
    nodes = list(graph.nodes.values())[:max_nodes]

    # Add nodes
    for node in nodes:
        label = node.label[:30] + "..." if len(node.label) > 30 else node.label
        emoji = get_confidence_emoji(node.confidence)
        color = node_colors.get(node.node_type, "#ffffff")

        dot += f'    "{node.node_id}" [label="{emoji} {label}", fillcolor="{color}"];\n'

    dot += "\n"

    # Add edges
    node_ids = set(n.node_id for n in nodes)

    for edge in graph.edges.values():
        if not edge.is_active:
            continue

        if edge.target_node_id not in node_ids:
            continue

        for source_id in edge.source_node_ids:
            if source_id in node_ids:
                label = edge.method[:20] if edge.method else ""
                dot += f'    "{source_id}" -> "{edge.target_node_id}" [label="{label}"];\n'

    dot += "}\n"

    return dot


def generate_subgraph_for_node(
    node_id: str,
    graph: FinancialLineageGraph,
    depth: int = 3,
    direction: str = "backward"
) -> str:
    """
    Generate Mermaid diagram for a specific node and its ancestors/descendants.

    Args:
        node_id: Focus node
        graph: Lineage graph
        depth: How many levels to traverse
        direction: "backward" (ancestors) or "forward" (descendants)

    Returns:
        Mermaid diagram string
    """
    # Get relevant nodes
    if direction == "backward":
        relevant_nodes = graph.trace_backward(node_id, max_depth=depth)
    else:
        relevant_nodes = graph.trace_forward(node_id, max_depth=depth)

    # Create subgraph
    subgraph = FinancialLineageGraph()

    for node in relevant_nodes:
        subgraph.add_node(
            node_id=node.node_id,
            node_type=node.node_type,
            label=node.label,
            value=node.value,
            confidence=node.confidence,
            period=node.period,
            data=node.data
        )

    # Add relevant edges
    for edge in graph.edges.values():
        if edge.target_node_id in subgraph.nodes:
            subgraph.add_edge(
                edge_id=edge.edge_id,
                source_node_ids=edge.source_node_ids,
                target_node_id=edge.target_node_id,
                edge_type=edge.edge_type,
                method=edge.method,
                confidence=edge.confidence,
                is_active=edge.is_active,
                data=edge.data
            )

    return graph_to_mermaid(subgraph, max_nodes=100)


def generate_graph_statistics(graph: FinancialLineageGraph) -> Dict[str, any]:
    """
    Generate statistics about the graph.

    Args:
        graph: Lineage graph

    Returns:
        Dict with statistics
    """
    nodes = list(graph.nodes.values())
    edges = list(graph.edges.values())

    # Count by node type
    node_type_counts = {}
    for node_type in NodeType:
        count = sum(1 for n in nodes if n.node_type == node_type)
        node_type_counts[node_type.value] = count

    # Count by edge type
    edge_type_counts = {}
    for edge_type in EdgeType:
        count = sum(1 for e in edges if e.edge_type == edge_type)
        edge_type_counts[edge_type.value] = count

    # Confidence stats
    confidences = [n.confidence for n in nodes if n.confidence is not None]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    # Depth analysis (longest path)
    max_depth = 0
    for node in nodes:
        if node.node_type == NodeType.CALCULATED:
            ancestors = graph.trace_backward(node.node_id)
            depth = len(ancestors)
            max_depth = max(max_depth, depth)

    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "active_edges": sum(1 for e in edges if e.is_active),
        "inactive_edges": sum(1 for e in edges if not e.is_active),
        "node_type_counts": node_type_counts,
        "edge_type_counts": edge_type_counts,
        "avg_confidence": avg_confidence,
        "max_depth": max_depth,
    }


def format_graph_summary(graph: FinancialLineageGraph) -> str:
    """
    Generate human-readable summary of graph.

    Args:
        graph: Lineage graph

    Returns:
        Markdown summary
    """
    stats = generate_graph_statistics(graph)

    md = "# Lineage Graph Summary\n\n"
    md += f"**Total Nodes:** {stats['total_nodes']}\n"
    md += f"**Total Edges:** {stats['total_edges']} ({stats['active_edges']} active)\n"
    md += f"**Average Confidence:** {stats['avg_confidence']:.2f}\n"
    md += f"**Maximum Depth:** {stats['max_depth']}\n\n"

    md += "## Node Distribution\n\n"
    for node_type, count in stats['node_type_counts'].items():
        if count > 0:
            md += f"- **{node_type}:** {count}\n"

    md += "\n## Edge Distribution\n\n"
    for edge_type, count in stats['edge_type_counts'].items():
        if count > 0:
            md += f"- **{edge_type}:** {count}\n"

    return md


def export_graph_json(graph: FinancialLineageGraph, pretty: bool = True) -> str:
    """
    Export graph as JSON.

    Args:
        graph: Lineage graph
        pretty: Use indentation

    Returns:
        JSON string
    """
    data = {
        "nodes": [
            {
                "node_id": node.node_id,
                "node_type": node.node_type.value if node.node_type else None,
                "label": node.label,
                "value": node.value,
                "confidence": node.confidence,
                "period": node.period,
                "data": node.data
            }
            for node in graph.nodes.values()
        ],
        "edges": [
            {
                "edge_id": edge.edge_id,
                "source_node_ids": edge.source_node_ids,
                "target_node_id": edge.target_node_id,
                "edge_type": edge.edge_type.value if edge.edge_type else None,
                "method": edge.method,
                "confidence": edge.confidence,
                "is_active": edge.is_active,
                "data": edge.data
            }
            for edge in graph.edges.values()
        ],
        "statistics": generate_graph_statistics(graph)
    }

    return json.dumps(data, indent=2 if pretty else None)


def generate_node_detail_card(node_id: str, graph: FinancialLineageGraph) -> str:
    """
    Generate detailed information card for a node.

    Args:
        node_id: Node to describe
        graph: Lineage graph

    Returns:
        Markdown card
    """
    node = graph.get_node(node_id)
    if not node:
        return f"Node {node_id} not found."

    emoji = get_confidence_emoji(node.confidence)

    md = f"## {emoji} {node.label}\n\n"
    md += f"**Node ID:** `{node.node_id}`\n"
    md += f"**Type:** {node.node_type.value if node.node_type else 'Unknown'}\n"

    if node.value is not None:
        md += f"**Value:** {node.value:,.0f}\n"

    md += f"**Confidence:** {node.confidence:.2f}\n"

    if node.period:
        md += f"**Period:** {node.period}\n"

    # Incoming edges
    incoming = graph.get_incoming_edges(node_id)
    if incoming:
        md += f"\n**Incoming Edges:** {len(incoming)}\n"
        for edge_id in incoming:
            edge = graph.get_edge(edge_id)
            if edge:
                md += f"- {edge.method} (Confidence: {edge.confidence:.2f})\n"

    # Outgoing edges
    outgoing = graph.get_outgoing_edges(node_id)
    if outgoing:
        md += f"\n**Outgoing Edges:** {len(outgoing)}\n"
        for edge_id in outgoing:
            edge = graph.get_edge(edge_id)
            if edge:
                md += f"- {edge.method}\n"

    # Additional data
    if node.data:
        md += f"\n**Additional Data:**\n"
        for key, value in node.data.items():
            md += f"- {key}: {value}\n"

    return md


def find_critical_path(graph: FinancialLineageGraph) -> List[str]:
    """
    Find the critical path (longest path from source to calculated).

    Args:
        graph: Lineage graph

    Returns:
        List of node IDs in critical path
    """
    max_path = []
    max_length = 0

    # Find all calculated nodes
    calculated_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.CALCULATED]

    for node in calculated_nodes:
        ancestors = graph.trace_backward(node.node_id)
        if len(ancestors) > max_length:
            max_length = len(ancestors)
            max_path = [n.node_id for n in ancestors]

    return max_path


def highlight_low_confidence_paths(
    graph: FinancialLineageGraph,
    threshold: float = 0.70
) -> List[str]:
    """
    Identify nodes with low confidence.

    Args:
        graph: Lineage graph
        threshold: Confidence threshold

    Returns:
        List of node IDs with low confidence
    """
    low_confidence_nodes = []

    for node in graph.nodes.values():
        if node.confidence < threshold:
            low_confidence_nodes.append(node.node_id)

    return low_confidence_nodes

#!/usr/bin/env python3
"""
Trace UI Components for Streamlit
==================================
Production-grade UI components for displaying financial value traces,
dependency graphs, and transformation histories.

Designed for investment banking analysts - finance-first, not dev-first.
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List
from utils.trace_service import TraceService, LineageTrace, InteractionTracker


# =============================================================================
# STYLING
# =============================================================================

TRACE_PANEL_CSS = """
<style>
.trace-panel {
    background: linear-gradient(135deg, rgba(30, 33, 48, 0.95), rgba(38, 42, 60, 0.95));
    border-left: 4px solid #4A90E2;
    padding: 1.5rem;
    border-radius: 8px;
    margin: 1rem 0;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.trace-section {
    margin: 1rem 0;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
}

.trace-section-title {
    color: #4A90E2;
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
}

.trace-section-title::before {
    content: "▸";
    margin-right: 0.5rem;
}

.source-info {
    background: linear-gradient(135deg, rgba(74, 144, 226, 0.1), rgba(74, 144, 226, 0.05));
    padding: 1rem;
    border-left: 3px solid #4A90E2;
    border-radius: 4px;
}

.transformation-step {
    background: rgba(255, 255, 255, 0.03);
    padding: 0.75rem;
    margin: 0.5rem 0;
    border-left: 2px solid #888;
    border-radius: 4px;
}

.transformation-step.mapping {
    border-left-color: #50C878;
}

.transformation-step.aggregation {
    border-left-color: #FFD700;
}

.transformation-step.calculation {
    border-left-color: #FF6B6B;
}

.confidence-badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: 600;
}

.confidence-high {
    background: rgba(80, 200, 120, 0.2);
    color: #50C878;
}

.confidence-medium {
    background: rgba(255, 215, 0, 0.2);
    color: #FFD700;
}

.confidence-low {
    background: rgba(255, 107, 107, 0.2);
    color: #FF6B6B;
}

.analyst-override {
    background: linear-gradient(135deg, rgba(147, 51, 234, 0.15), rgba(147, 51, 234, 0.05));
    border-left: 3px solid #9333EA;
    padding: 0.75rem;
    border-radius: 4px;
    margin: 0.5rem 0;
}

.clickable-number {
    cursor: pointer;
    text-decoration: underline;
    text-decoration-style: dotted;
    text-decoration-color: #4A90E2;
    transition: all 0.2s;
}

.clickable-number:hover {
    color: #4A90E2;
    text-decoration-style: solid;
}

.dependency-node {
    background: rgba(74, 144, 226, 0.1);
    padding: 0.5rem 0.75rem;
    border-radius: 6px;
    margin: 0.25rem;
    display: inline-block;
    cursor: pointer;
    transition: all 0.2s;
}

.dependency-node:hover {
    background: rgba(74, 144, 226, 0.2);
    transform: translateY(-2px);
}

.local-only-badge {
    background: rgba(147, 51, 234, 0.15);
    color: #9333EA;
    padding: 0.25rem 0.5rem;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 600;
    display: inline-block;
}
</style>
"""


# =============================================================================
# TRACE INSPECTOR PANEL
# =============================================================================

def display_trace_inspector(trace: LineageTrace, trace_service: TraceService,
                           interaction_tracker: Optional[InteractionTracker] = None):
    """
    Display comprehensive trace inspector panel.

    This is the MAIN UI component for traceability.

    Args:
        trace: LineageTrace object to display
        trace_service: TraceService for recursive exploration
        interaction_tracker: Optional tracker for user interactions
    """
    # Inject CSS
    st.markdown(TRACE_PANEL_CSS, unsafe_allow_html=True)

    # Track view
    if interaction_tracker:
        interaction_tracker.track_trace_view(trace.value_id, len(trace.transformations))

    # Header
    st.markdown(f"""
    <div class="trace-panel">
        <h2 style="color: #4A90E2; margin: 0;">🔍 Value Trace Inspector</h2>
        <p style="color: #888; margin: 0.5rem 0 0 0;">
            Complete provenance and transformation history
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Value Summary
    st.markdown("### 📊 Value Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Final Value", f"{trace.final_value:,.2f}" if isinstance(trace.final_value, (int, float)) else str(trace.final_value))

    with col2:
        st.metric("Label", trace.label or "N/A")

    with col3:
        st.metric("Period", trace.period or "N/A")

    # Local-Only Badge
    if trace.is_local_only:
        st.markdown("""
        <span class="local-only-badge">🔒 LOCAL ONLY - Data stays on your machine</span>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Source Information
    _display_source_section(trace.source)

    # Transformations
    _display_transformations_section(trace.transformations)

    # Decision Path
    if trace.decision_path:
        _display_decision_path_section(trace.decision_path)

    # Dependencies
    _display_dependencies_section(
        trace.value_id,
        trace.upstream_dependencies,
        trace.downstream_dependencies,
        trace_service,
        interaction_tracker
    )

    # Analyst Corrections
    if trace.analyst_corrections:
        _display_analyst_corrections_section(trace.analyst_corrections)


def _display_source_section(source):
    """Display source information section."""
    st.markdown("### 📍 Source")

    origin_icons = {
        "excel_upload": "📊",
        "user_override": "👤",
        "system_derived": "⚙️"
    }

    icon = origin_icons.get(source.origin, "❓")

    st.markdown(f"""
    <div class="source-info">
        <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;">
            {icon} {source.origin.replace('_', ' ').title()}
        </div>
    """, unsafe_allow_html=True)

    if source.cell_ref:
        st.markdown(f"**Excel Cell**: `{source.sheet_name}!{source.cell_ref}`")

    if source.raw_value is not None:
        st.markdown(f"**Raw Value**: `{source.raw_value:,.2f}` " if isinstance(source.raw_value, (int, float)) else f"**Raw Value**: `{source.raw_value}`")

    if source.concept:
        st.markdown(f"**Taxonomy Concept**: `{source.concept}`")

    if source.mapping_tier:
        st.markdown(f"**Mapping Tier**: {source.mapping_tier}")

    if source.was_user_edited:
        st.markdown("**🎯 User Override**: This value was manually edited by analyst")

    st.markdown("</div>", unsafe_allow_html=True)


def _display_transformations_section(transformations: List):
    """Display transformation history section."""
    st.markdown("### 🔄 Transformation History")

    if not transformations:
        st.info("No transformations applied - value used directly from source")
        return

    for step in transformations:
        # Determine CSS class based on operation
        css_class = step.operation

        # Confidence badge
        conf_class = _get_confidence_class(step.confidence)

        st.markdown(f"""
        <div class="transformation-step {css_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>Step {step.step_number}: {step.operation.title()}</strong>
                </div>
                <div>
                    <span class="confidence-badge {conf_class}">
                        {step.confidence:.0%} confidence
                    </span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if step.formula:
            st.markdown(f"**Formula**: `{step.formula}`")

        if step.inputs:
            st.markdown("**Inputs**:")
            for key, value in step.inputs.items():
                if isinstance(value, (int, float)):
                    st.markdown(f"  - `{key}` = {value:,.2f}")
                else:
                    st.markdown(f"  - `{key}` = {value}")

        if step.output is not None:
            if isinstance(step.output, (int, float)):
                st.markdown(f"**Output**: `{step.output:,.2f}`")
            else:
                st.markdown(f"**Output**: `{step.output}`")

        if step.reasoning:
            st.markdown(f"**Reasoning**: _{step.reasoning}_")

        st.markdown("</div>", unsafe_allow_html=True)


def _display_decision_path_section(decision_path):
    """Display decision path section (why this mapping was chosen)."""
    st.markdown("### 🎯 Decision Path")

    conf_class = _get_confidence_class(decision_path.confidence)

    st.markdown(f"""
    <div class="trace-section">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <div>
                <strong>Chosen Mapping</strong>: <code>{decision_path.chosen_mapping}</code>
            </div>
            <div>
                <span class="confidence-badge {conf_class}">
                    {decision_path.confidence:.0%} confidence
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"**Source**: {decision_path.mapping_source}")
    st.markdown(f"**Reasoning**: _{decision_path.reasoning}_")

    if decision_path.analyst_override:
        st.markdown("""
        <div class="analyst-override">
            🎯 <strong>Analyst Override</strong>: This mapping was manually set by the user via Analyst Brain
        </div>
        """, unsafe_allow_html=True)

    # Show alternatives
    if decision_path.alternatives:
        with st.expander(f"📋 View {len(decision_path.alternatives)} Alternative Mappings"):
            for idx, alt in enumerate(decision_path.alternatives, 1):
                st.markdown(f"**Alternative {idx}**:")
                st.json(alt)

    st.markdown("</div>", unsafe_allow_html=True)


def _display_dependencies_section(node_id: str, upstream: List[str], downstream: List[str],
                                  trace_service: TraceService,
                                  interaction_tracker: Optional[InteractionTracker] = None):
    """Display dependencies section with recursive exploration."""
    st.markdown("### 🔗 Dependencies")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**⬆️ Upstream** ({len(upstream)} dependencies)")

        if upstream:
            for dep_id in upstream[:10]:  # Show first 10
                node = trace_service.graph.get_node(dep_id)
                if node:
                    label = node.label or node.concept or dep_id[:8]

                    # Make clickable
                    if st.button(f"🔍 {label}", key=f"upstream_{dep_id}"):
                        if interaction_tracker:
                            interaction_tracker.track_dependency_exploration(node_id, dep_id, "upstream")

                        # Fetch and display trace
                        dep_trace = trace_service.get_trace(dep_id)
                        if dep_trace:
                            st.session_state['current_trace'] = dep_trace
                            st.rerun()

            if len(upstream) > 10:
                st.info(f"+{len(upstream) - 10} more upstream dependencies")

    with col2:
        st.markdown(f"**⬇️ Downstream** ({len(downstream)} dependencies)")

        if downstream:
            for dep_id in downstream[:10]:  # Show first 10
                node = trace_service.graph.get_node(dep_id)
                if node:
                    label = node.label or node.concept or dep_id[:8]

                    # Make clickable
                    if st.button(f"🔍 {label}", key=f"downstream_{dep_id}"):
                        if interaction_tracker:
                            interaction_tracker.track_dependency_exploration(node_id, dep_id, "downstream")

                        # Fetch and display trace
                        dep_trace = trace_service.get_trace(dep_id)
                        if dep_trace:
                            st.session_state['current_trace'] = dep_trace
                            st.rerun()

            if len(downstream) > 10:
                st.info(f"+{len(downstream) - 10} more downstream dependencies")


def _display_analyst_corrections_section(corrections: List[Dict]):
    """Display analyst brain corrections history."""
    st.markdown("### 🧠 Analyst Brain History")

    st.markdown("""
    <div class="analyst-override">
        <strong>🔒 Local Only</strong>: All analyst corrections are stored locally in your Analyst Brain JSON file.
        This data never leaves your machine.
    </div>
    """, unsafe_allow_html=True)

    for correction in corrections:
        with st.expander(f"Correction: {correction.get('source_label', 'Unknown')}"):
            st.markdown(f"**Target Concept**: `{correction.get('target_concept', 'N/A')}`")
            st.markdown(f"**Created**: {correction.get('created_at', 'Unknown')}")
            st.markdown(f"**Created By**: {correction.get('created_by', 'Unknown')}")

            if correction.get('notes'):
                st.markdown(f"**Notes**: {correction['notes']}")


def _get_confidence_class(confidence: float) -> str:
    """Get CSS class for confidence badge."""
    if confidence >= 0.85:
        return "confidence-high"
    elif confidence >= 0.65:
        return "confidence-medium"
    else:
        return "confidence-low"


# =============================================================================
# CLICKABLE NUMBER COMPONENT
# =============================================================================

def clickable_number(value: Any, node_id: str, trace_service: TraceService,
                    interaction_tracker: Optional[InteractionTracker] = None,
                    label: Optional[str] = None) -> bool:
    """
    Display a clickable number that opens trace inspector.

    Args:
        value: The numeric value to display
        node_id: Node ID for trace lookup
        trace_service: TraceService instance
        interaction_tracker: Optional interaction tracker
        label: Optional label for the value

    Returns:
        True if clicked, False otherwise
    """
    # Format value
    if isinstance(value, (int, float)):
        display_value = f"{value:,.2f}"
    else:
        display_value = str(value)

    # Create button
    button_label = f"🔍 {label}: {display_value}" if label else f"🔍 {display_value}"

    clicked = st.button(button_label, key=f"clickable_{node_id}")

    if clicked:
        # Track interaction
        if interaction_tracker:
            interaction_tracker.track_click(node_id, label, value)

        # Fetch trace
        trace = trace_service.get_trace(node_id)

        if trace:
            # Store in session state
            st.session_state['current_trace'] = trace
            st.session_state['trace_panel_open'] = True

            return True

    return False


# =============================================================================
# DEPENDENCY GRAPH VISUALIZATION
# =============================================================================

def display_dependency_graph(node_id: str, trace_service: TraceService,
                            direction: str = "both", max_depth: int = 3):
    """
    Display interactive dependency graph visualization.

    Args:
        node_id: Starting node ID
        trace_service: TraceService instance
        direction: "upstream", "downstream", or "both"
        max_depth: Maximum depth to traverse
    """
    st.markdown("### 🕸️ Dependency Graph")

    # Get graph data
    graph_data = trace_service.get_dependency_graph(node_id, max_depth=max_depth, direction=direction)

    nodes = graph_data['nodes']
    edges = graph_data['edges']

    st.info(f"Graph contains {len(nodes)} nodes and {len(edges)} edges")

    # Display as hierarchical tree (simple text-based for now)
    # For production, you'd integrate with D3.js or Plotly

    # Group nodes by type
    nodes_by_type = {}
    for node in nodes:
        node_type = node['node_type']
        if node_type not in nodes_by_type:
            nodes_by_type[node_type] = []
        nodes_by_type[node_type].append(node)

    # Display by type
    for node_type, type_nodes in nodes_by_type.items():
        with st.expander(f"{node_type.upper()} ({len(type_nodes)} nodes)"):
            for node in type_nodes[:20]:  # Limit to 20 per type
                label = node['label'] or node['concept'] or node['node_id'][:8]
                value = node['value']

                if isinstance(value, (int, float)):
                    st.markdown(f"- **{label}**: {value:,.2f}")
                else:
                    st.markdown(f"- **{label}**: {value}")


# =============================================================================
# TRACE SEARCH
# =============================================================================

def display_trace_search(trace_service: TraceService):
    """Display trace search interface."""
    st.markdown("### 🔎 Search Traces")

    search_query = st.text_input("Search by label", placeholder="e.g., Revenue, EBITDA, Total Assets")

    if search_query:
        traces = trace_service.search_traces_by_label(search_query)

        st.info(f"Found {len(traces)} traces matching '{search_query}'")

        for trace in traces[:10]:  # Show first 10
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                st.markdown(f"**{trace.label}**")

            with col2:
                if isinstance(trace.final_value, (int, float)):
                    st.markdown(f"{trace.final_value:,.2f}")
                else:
                    st.markdown(str(trace.final_value))

            with col3:
                if st.button("View", key=f"search_{trace.value_id}"):
                    st.session_state['current_trace'] = trace
                    st.rerun()


# =============================================================================
# LOW CONFIDENCE TRACES
# =============================================================================

def display_low_confidence_traces(trace_service: TraceService, threshold: float = 0.7):
    """Display all traces with low confidence mappings."""
    st.markdown("### ⚠️ Low Confidence Traces")

    traces = trace_service.get_all_low_confidence_traces(threshold=threshold)

    if not traces:
        st.success("No low confidence traces found! All mappings are above threshold.")
        return

    st.warning(f"Found {len(traces)} traces with confidence below {threshold:.0%}")

    for trace in traces:
        with st.expander(f"⚠️ {trace.label} - {trace.period}"):
            # Show decision path if available
            if trace.decision_path:
                st.markdown(f"**Confidence**: {trace.decision_path.confidence:.0%}")
                st.markdown(f"**Reasoning**: {trace.decision_path.reasoning}")

            if st.button("View Full Trace", key=f"low_conf_{trace.value_id}"):
                st.session_state['current_trace'] = trace
                st.rerun()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_value(value: Any) -> str:
    """Format value for display."""
    if isinstance(value, (int, float)):
        return f"{value:,.2f}"
    elif isinstance(value, str):
        return value
    else:
        return str(value)

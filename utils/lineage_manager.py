#!/usr/bin/env python3
"""
Lineage Manager - Build Lineage Graph from Pipeline Outputs
============================================================
Reconstructs the complete lineage graph from existing pipeline CSVs
without modifying core pipeline code.

This is a NON-INVASIVE approach that:
1. Reads messy_input.csv (extraction output)
2. Reads normalized_financials.csv (mapping output)
3. Reads DCF/LBO/Comps CSVs (modeling output)
4. Builds a complete lineage graph
5. Enables traceability without code changes
"""

import os
import pandas as pd
import uuid
from typing import Dict, List, Optional, Any, Tuple
from utils.lineage_graph import (
    FinancialLineageGraph,
    LineageGraphBuilder,
    NodeType,
    MappingSource,
    AggregationStrategy
)
from utils.trace_service import TraceService, InteractionTracker


class LineageManager:
    """
    Manages lineage graph construction and persistence.

    Builds lineage graph from pipeline outputs without modifying
    existing extraction/mapping/modeling code.
    """

    def __init__(self, session_id: str, source_file: str, brain_manager=None):
        """
        Initialize lineage manager.

        Args:
            session_id: Session UUID
            source_file: Original Excel file path
            brain_manager: Optional BrainManager instance
        """
        self.session_id = session_id
        self.source_file = source_file
        self.brain_manager = brain_manager

        # Create graph builder
        self.builder = LineageGraphBuilder(session_id, source_file)

        # Node ID caches for lookup
        self._extracted_nodes: Dict[Tuple[str, str, str], str] = {}  # (label, amount, period) -> node_id
        self._mapped_nodes: Dict[Tuple[str, str, str], str] = {}  # (concept, amount, period) -> node_id
        self._aggregated_nodes: Dict[Tuple[str, str], str] = {}  # (concept, period) -> node_id
        self._calculated_nodes: Dict[Tuple[str, str], str] = {}  # (label, period) -> node_id

    # =========================================================================
    # BUILD LINEAGE FROM CSV FILES
    # =========================================================================

    def build_from_pipeline_outputs(self,
                                   messy_input_path: str,
                                   normalized_path: str,
                                   dcf_path: Optional[str] = None,
                                   lbo_path: Optional[str] = None,
                                   comps_path: Optional[str] = None) -> FinancialLineageGraph:
        """
        Build complete lineage graph from pipeline CSV outputs.

        Args:
            messy_input_path: Path to messy_input.csv
            normalized_path: Path to normalized_financials.csv
            dcf_path: Path to DCF_Historical_Setup.csv
            lbo_path: Path to LBO_Credit_Stats.csv
            comps_path: Path to Comps_Trading_Metrics.csv

        Returns:
            Complete FinancialLineageGraph
        """
        print("\n" + "=" * 70)
        print("BUILDING LINEAGE GRAPH")
        print("=" * 70)

        # Stage 1: Process extraction output
        if os.path.exists(messy_input_path):
            print("Processing extraction data...")
            self._process_extraction(messy_input_path)

        # Stage 2: Process mapping output
        if os.path.exists(normalized_path):
            print("Processing mapping data...")
            self._process_mapping(normalized_path)

        # Stage 3: Process aggregation (inferred from normalized data)
        if os.path.exists(normalized_path):
            print("Processing aggregation data...")
            self._process_aggregation(normalized_path)

        # Stage 4: Process calculations
        if dcf_path and os.path.exists(dcf_path):
            print("Processing DCF calculations...")
            self._process_dcf_calculations(dcf_path)

        if lbo_path and os.path.exists(lbo_path):
            print("Processing LBO calculations...")
            self._process_lbo_calculations(lbo_path)

        if comps_path and os.path.exists(comps_path):
            print("Processing Comps calculations...")
            self._process_comps_calculations(comps_path)

        # Print statistics
        stats = self.builder.graph.get_statistics()
        print(f"\nLineage Graph Statistics:")
        print(f"  Total Nodes: {stats['total_nodes']}")
        print(f"  Total Edges: {stats['total_edges']}")
        print(f"  Active Edges: {stats['active_edges']}")
        print(f"  Avg Confidence: {stats['avg_confidence']:.2f}")

        return self.builder.graph

    def _process_extraction(self, csv_path: str):
        """Process messy_input.csv to create extraction nodes."""
        df = pd.read_csv(csv_path)

        for idx, row in df.iterrows():
            label = row.get("Line Item", "")
            amount = row.get("Amount", 0)
            note = row.get("Note", "")

            # Parse note: "Income Statement | 2023"
            parts = note.split(" | ")
            sheet_name = parts[0] if len(parts) > 0 else "Unknown"
            period = parts[1] if len(parts) > 1 else "Unknown"

            # Create source cell node (we don't have exact cell refs, so use row index)
            cell_id = self.builder.add_source_cell(
                sheet=sheet_name,
                row=idx,
                col=1,  # Assume column 1 for amounts
                cell_ref=f"Row{idx}",
                value=amount,
                label=label
            )

            # Create extraction node
            extracted_id, _ = self.builder.add_extraction(
                source_cell_id=cell_id,
                extracted_label=label,
                extracted_value=amount,
                period=period
            )

            # Cache for later lookup
            cache_key = (label, str(amount), period)
            self._extracted_nodes[cache_key] = extracted_id

    def _process_mapping(self, csv_path: str):
        """Process normalized_financials.csv to create mapping nodes."""
        df = pd.read_csv(csv_path)

        for idx, row in df.iterrows():
            source_label = row.get("Source_Label", "")
            source_amount = row.get("Source_Amount", 0)
            period = self._extract_period(row)
            concept = row.get("Canonical_Concept", "")
            map_method = row.get("Map_Method", "")
            status = row.get("Status", "")

            if status != "VALID" or not concept:
                continue

            # Find extracted node
            cache_key = (source_label, str(source_amount), period)
            extracted_id = self._extracted_nodes.get(cache_key)

            if not extracted_id:
                # If not found, create a synthetic extracted node
                extracted_id = self.builder._generate_node_id("extracted")
                self._extracted_nodes[cache_key] = extracted_id

            # Determine mapping source and confidence
            mapping_source, confidence = self._infer_mapping_source(map_method)

            # Create mapping node
            mapped_id, _ = self.builder.add_mapping(
                extracted_node_id=extracted_id,
                concept=concept,
                mapping_method=map_method,
                mapping_source=mapping_source,
                confidence=confidence,
                alternatives=[]
            )

            # Cache for aggregation lookup
            map_cache_key = (concept, str(source_amount), period)
            self._mapped_nodes[map_cache_key] = mapped_id

    def _process_aggregation(self, csv_path: str):
        """
        Infer aggregation from normalized data.

        Groups by (concept, period) and creates aggregation nodes.
        """
        df = pd.read_csv(csv_path)

        # Filter valid mappings only
        df = df[df['Status'] == 'VALID'].copy()

        # Extract period
        df['Period'] = df.apply(self._extract_period, axis=1)

        # Group by concept and period
        grouped = df.groupby(['Canonical_Concept', 'Period'])

        for (concept, period), group in grouped:
            if len(group) == 0:
                continue

            # Get all mapped node IDs for this group
            mapped_ids = []
            for _, row in group.iterrows():
                source_label = row.get("Source_Label", "")
                source_amount = row.get("Source_Amount", 0)
                map_cache_key = (concept, str(source_amount), period)
                mapped_id = self._mapped_nodes.get(map_cache_key)
                if mapped_id:
                    mapped_ids.append(mapped_id)

            if not mapped_ids:
                continue

            # Determine aggregation strategy
            strategy, excluded_ids = self._infer_aggregation_strategy(group)

            # Calculate final value (sum of non-excluded)
            final_value = group['Source_Amount'].sum()

            # If total line was used, use its value
            if strategy == AggregationStrategy.TOTAL_LINE_USED and len(group) > 0:
                # Find total line (heuristic: contains "total" in label)
                total_rows = group[group['Source_Label'].str.contains('total', case=False, na=False)]
                if len(total_rows) > 0:
                    final_value = total_rows.iloc[0]['Source_Amount']

            # Create aggregation node
            agg_id, _ = self.builder.add_aggregation(
                mapped_node_ids=mapped_ids,
                concept=concept,
                period=period,
                final_value=final_value,
                strategy=strategy,
                excluded_ids=excluded_ids,
                condition=self._build_aggregation_condition(strategy, len(mapped_ids), len(excluded_ids))
            )

            # Cache for calculation lookup
            self._aggregated_nodes[(concept, period)] = agg_id

    def _process_dcf_calculations(self, csv_path: str):
        """Process DCF calculations to create calculation nodes."""
        df = pd.read_csv(csv_path)

        # Process each row (each row is a period)
        for idx, row in df.iterrows():
            period = row.get("Period", str(idx))

            # Revenue
            if 'Revenue' in row and pd.notna(row['Revenue']):
                self._create_calculation_if_new(
                    label="Revenue",
                    period=period,
                    value=row['Revenue'],
                    source_concepts=["us-gaap_Revenues"],
                    formula="Aggregated Revenue"
                )

            # Gross Profit = Revenue - COGS
            if 'Gross_Profit' in row and pd.notna(row['Gross_Profit']):
                self._create_calculation_if_new(
                    label="Gross Profit",
                    period=period,
                    value=row['Gross_Profit'],
                    source_concepts=["us-gaap_Revenues", "us-gaap_CostOfRevenue"],
                    formula="Revenue - COGS"
                )

            # EBITDA = Gross Profit - OpEx
            if 'EBITDA' in row and pd.notna(row['EBITDA']):
                self._create_calculation_if_new(
                    label="EBITDA",
                    period=period,
                    value=row['EBITDA'],
                    source_concepts=["us-gaap_Revenues", "us-gaap_CostOfRevenue", "us-gaap_OperatingExpenses"],
                    formula="Revenue - COGS - OpEx"
                )

            # EBIT = EBITDA - D&A
            if 'EBIT' in row and pd.notna(row['EBIT']):
                self._create_calculation_if_new(
                    label="EBIT",
                    period=period,
                    value=row['EBIT'],
                    source_concepts=["us-gaap_Revenues", "us-gaap_CostOfRevenue", "us-gaap_OperatingExpenses", "us-gaap_DepreciationAndAmortization"],
                    formula="EBITDA - D&A"
                )

            # NOPAT = EBIT * (1 - tax rate)
            if 'NOPAT' in row and pd.notna(row['NOPAT']):
                self._create_calculation_if_new(
                    label="NOPAT",
                    period=period,
                    value=row['NOPAT'],
                    source_concepts=["us-gaap_Revenues", "us-gaap_IncomeTaxExpenseBenefit"],
                    formula="EBIT * (1 - Tax Rate)"
                )

            # UFCF = NOPAT - NWC - CapEx
            if 'Unlevered_FCF' in row and pd.notna(row['Unlevered_FCF']):
                self._create_calculation_if_new(
                    label="Unlevered Free Cash Flow",
                    period=period,
                    value=row['Unlevered_FCF'],
                    source_concepts=["us-gaap_Revenues", "us-gaap_CapitalExpenditures", "us-gaap_IncreaseDecreaseInWorkingCapital"],
                    formula="NOPAT - Change in NWC - CapEx"
                )

    def _process_lbo_calculations(self, csv_path: str):
        """Process LBO calculations."""
        df = pd.read_csv(csv_path)

        for idx, row in df.iterrows():
            period = row.get("Period", str(idx))

            # Adjusted EBITDA
            if 'Adjusted_EBITDA' in row and pd.notna(row['Adjusted_EBITDA']):
                self._create_calculation_if_new(
                    label="Adjusted EBITDA",
                    period=period,
                    value=row['Adjusted_EBITDA'],
                    source_concepts=["us-gaap_Revenues", "us-gaap_RestructuringCharges", "us-gaap_StockBasedCompensation"],
                    formula="EBITDA + Restructuring + Stock Comp + Other Addbacks"
                )

            # Total Debt
            if 'Total_Debt' in row and pd.notna(row['Total_Debt']):
                self._create_calculation_if_new(
                    label="Total Debt",
                    period=period,
                    value=row['Total_Debt'],
                    source_concepts=["us-gaap_ShortTermDebt", "us-gaap_LongTermDebt"],
                    formula="Short-term Debt + Long-term Debt + Capital Leases"
                )

            # Net Debt
            if 'Net_Debt' in row and pd.notna(row['Net_Debt']):
                self._create_calculation_if_new(
                    label="Net Debt",
                    period=period,
                    value=row['Net_Debt'],
                    source_concepts=["us-gaap_ShortTermDebt", "us-gaap_LongTermDebt", "us-gaap_Cash"],
                    formula="Total Debt - Cash"
                )

            # Leverage Ratio
            if 'Leverage_Ratio' in row and pd.notna(row['Leverage_Ratio']):
                self._create_calculation_if_new(
                    label="Leverage Ratio",
                    period=period,
                    value=row['Leverage_Ratio'],
                    source_concepts=["us-gaap_ShortTermDebt", "us-gaap_LongTermDebt", "us-gaap_Revenues"],
                    formula="Net Debt / Adjusted EBITDA"
                )

    def _process_comps_calculations(self, csv_path: str):
        """Process Comps calculations."""
        df = pd.read_csv(csv_path)

        for idx, row in df.iterrows():
            period = row.get("Period", str(idx))

            # EBITDA Margin
            if 'EBITDA_Margin_Pct' in row and pd.notna(row['EBITDA_Margin_Pct']):
                self._create_calculation_if_new(
                    label="EBITDA Margin %",
                    period=period,
                    value=row['EBITDA_Margin_Pct'],
                    source_concepts=["us-gaap_Revenues"],
                    formula="(EBITDA / Revenue) * 100"
                )

            # Net Margin
            if 'Net_Margin_Pct' in row and pd.notna(row['Net_Margin_Pct']):
                self._create_calculation_if_new(
                    label="Net Margin %",
                    period=period,
                    value=row['Net_Margin_Pct'],
                    source_concepts=["us-gaap_Revenues", "us-gaap_NetIncomeLoss"],
                    formula="(Net Income / Revenue) * 100"
                )

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _extract_period(self, row) -> str:
        """Extract period from row (handles various column names)."""
        period_candidates = ["Period_Date", "Period", "Date", "Note"]
        for col in period_candidates:
            if col in row and pd.notna(row[col]):
                val = str(row[col])
                # Extract year if present
                if " | " in val:
                    return val.split(" | ")[-1]
                return val
        return "Unknown"

    def _infer_mapping_source(self, map_method: str) -> Tuple[MappingSource, float]:
        """Infer mapping source and confidence from method string."""
        method_lower = map_method.lower() if map_method else ""

        if "brain" in method_lower or "user" in method_lower:
            return MappingSource.ANALYST_BRAIN, 1.0
        elif "alias" in method_lower:
            return MappingSource.ALIAS, 0.95
        elif "exact" in method_lower or "label" in method_lower:
            return MappingSource.EXACT_LABEL, 0.90
        elif "keyword" in method_lower or "fuzzy" in method_lower:
            return MappingSource.KEYWORD, 0.75
        elif "hierarchy" in method_lower or "safe" in method_lower:
            return MappingSource.HIERARCHY, 0.65
        else:
            return MappingSource.KEYWORD, 0.70

    def _infer_aggregation_strategy(self, group: pd.DataFrame) -> Tuple[AggregationStrategy, List[str]]:
        """Infer aggregation strategy from grouped data."""
        if len(group) == 1:
            return AggregationStrategy.SINGLE_VALUE, []

        # Check if any label contains "total"
        total_rows = group[group['Source_Label'].str.contains('total', case=False, na=False)]

        if len(total_rows) > 0:
            # Find component rows (non-total rows)
            component_rows = group[~group['Source_Label'].str.contains('total', case=False, na=False)]
            excluded_ids = []  # We don't have node IDs yet, so return empty list

            return AggregationStrategy.TOTAL_LINE_USED, excluded_ids

        # If multiple values without total, sum components
        return AggregationStrategy.COMPONENT_SUM, []

    def _build_aggregation_condition(self, strategy: AggregationStrategy,
                                     total_count: int, excluded_count: int) -> str:
        """Build human-readable condition for aggregation."""
        if strategy == AggregationStrategy.SINGLE_VALUE:
            return "Single value for this concept and period"
        elif strategy == AggregationStrategy.TOTAL_LINE_USED:
            return f"Detected total line, used it directly. Excluded {excluded_count} components to prevent double-counting"
        elif strategy == AggregationStrategy.COMPONENT_SUM:
            return f"Summed {total_count} component values"
        elif strategy == AggregationStrategy.MAX_VALUE:
            return f"Multiple totals found, used maximum value"
        return "Aggregated"

    def _create_calculation_if_new(self, label: str, period: str, value: Any,
                                   source_concepts: List[str], formula: str):
        """Create a calculation node if it doesn't already exist."""
        cache_key = (label, period)

        if cache_key in self._calculated_nodes:
            return  # Already created

        # Find source aggregated nodes
        source_node_ids = []
        inputs = {}

        for concept in source_concepts:
            agg_key = (concept, period)
            if agg_key in self._aggregated_nodes:
                source_id = self._aggregated_nodes[agg_key]
                source_node_ids.append(source_id)

                # Get value from node
                node = self.builder.graph.get_node(source_id)
                if node:
                    inputs[concept] = node.value

        # If no source nodes found, skip
        if not source_node_ids:
            return

        # Create calculation node
        calc_id, _ = self.builder.add_calculation(
            source_node_ids=source_node_ids,
            result_label=label,
            formula=formula,
            inputs=inputs,
            result_value=value,
            period=period
        )

        self._calculated_nodes[cache_key] = calc_id

    # =========================================================================
    # PERSISTENCE
    # =========================================================================

    def save_graph(self, output_dir: str):
        """Save lineage graph to JSON file."""
        output_path = os.path.join(output_dir, "lineage_graph.json")
        self.builder.graph.to_json(output_path)
        print(f"\nLineage graph saved to: {output_path}")
        return output_path

    def load_graph(self, filepath: str) -> FinancialLineageGraph:
        """Load lineage graph from JSON file."""
        return FinancialLineageGraph.from_json(filepath)

    # =========================================================================
    # TRACE SERVICE INTEGRATION
    # =========================================================================

    def get_trace_service(self) -> TraceService:
        """Get TraceService instance for this lineage graph."""
        return TraceService(self.builder.graph, self.brain_manager)

    def get_interaction_tracker(self) -> InteractionTracker:
        """Get InteractionTracker for this session."""
        return InteractionTracker(self.session_id)


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def build_lineage_from_session(session_dir: str, source_file: str,
                               session_id: Optional[str] = None,
                               brain_manager=None) -> Tuple[FinancialLineageGraph, TraceService]:
    """
    Build lineage graph from a session directory.

    Args:
        session_dir: Path to session directory (contains CSVs)
        source_file: Original Excel file name
        session_id: Optional session UUID (generated if not provided)
        brain_manager: Optional BrainManager instance

    Returns:
        (FinancialLineageGraph, TraceService) tuple
    """
    if not session_id:
        session_id = str(uuid.uuid4())

    manager = LineageManager(session_id, source_file, brain_manager)

    # Build paths
    messy_input = os.path.join(session_dir, "messy_input.csv")
    normalized = os.path.join(session_dir, "normalized_financials.csv")
    dcf = os.path.join(session_dir, "final_ib_models", "DCF_Historical_Setup.csv")
    lbo = os.path.join(session_dir, "final_ib_models", "LBO_Credit_Stats.csv")
    comps = os.path.join(session_dir, "final_ib_models", "Comps_Trading_Metrics.csv")

    # Build graph
    graph = manager.build_from_pipeline_outputs(
        messy_input_path=messy_input,
        normalized_path=normalized,
        dcf_path=dcf if os.path.exists(dcf) else None,
        lbo_path=lbo if os.path.exists(lbo) else None,
        comps_path=comps if os.path.exists(comps) else None
    )

    # Save graph
    manager.save_graph(session_dir)

    # Get trace service
    trace_service = manager.get_trace_service()

    return graph, trace_service

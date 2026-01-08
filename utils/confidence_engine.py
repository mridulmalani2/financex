#!/usr/bin/env python3
"""
Confidence Propagation Engine - Production V1.0
================================================
Investment banking-grade confidence scoring and propagation system.

Every financial output carries a deterministic confidence score (0.0 to 1.0)
that quantifies the reliability of underlying data and transformations.

DESIGN PRINCIPLES:
1. Rule-based (not ML) - fully deterministic and explainable
2. Confidence degrades through transformations, never improves
3. Hard blocking rules prevent unreliable models from being delivered
4. Conservative thresholds - better to block than deliver bad data

CONFIDENCE SCORING RULES:
- Analyst Brain: 1.00 (highest trust)
- Explicit Alias: 0.95 (manually curated)
- Exact Label: 0.90 (official taxonomy)
- Keyword Match: 0.70 (fuzzy match)
- Hierarchy Fallback: 0.50-0.70 (depends on depth)
- Unmapped: 0.00 (excluded from models)

PROPAGATION RULES:
- Forward propagation: target = MIN(sources) × transformation
- Multi-input: target = MIN(all inputs) × transformation
- Conditional edges: only active path counts
- Minimum floor: 0.00, Maximum cap: source confidence

Author: FinanceX Engineering
Date: 2026-01-07
Status: Production Ready
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import sys
import os

# Import lineage graph types
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.lineage_graph import MappingSource, AggregationStrategy


# =============================================================================
# CONFIDENCE CALCULATION - MAPPING
# =============================================================================

def calculate_mapping_confidence(
    method: str,
    mapping_source: Optional[MappingSource] = None,
    depth: int = 0
) -> Tuple[float, str]:
    """
    Calculate confidence for a mapping operation.

    Args:
        method: Mapping method description (e.g., "Analyst Brain", "Exact Label Match")
        mapping_source: MappingSource enum value (if available)
        depth: Hierarchy depth for fallback (only used for hierarchy fallback)

    Returns:
        Tuple of (confidence_score, explanation)

    Confidence Tiers:
        Tier 0: Analyst Brain (User Override) → 1.00
        Tier 1: Explicit Alias → 0.95
        Tier 2: Exact Label Match → 0.90
        Tier 3: Keyword Match → 0.70
        Tier 4: Hierarchy Fallback → 0.70 - (depth × 0.05), min 0.50
        Tier 5: Unmapped → 0.00
    """
    # Use MappingSource if provided (preferred)
    if mapping_source:
        if mapping_source == MappingSource.ANALYST_BRAIN:
            return (1.00, "Analyst Brain - highest trust (user override)")
        elif mapping_source == MappingSource.ALIAS:
            return (0.95, "Explicit Alias - manually curated mapping")
        elif mapping_source == MappingSource.EXACT_LABEL:
            return (0.90, "Exact Label Match - official XBRL taxonomy")
        elif mapping_source == MappingSource.KEYWORD:
            return (0.70, "Keyword Match - fuzzy matching")
        elif mapping_source == MappingSource.HIERARCHY:
            confidence = max(0.50, 0.70 - (depth * 0.05))
            return (confidence, f"Hierarchy Fallback (depth={depth}) - walked up presentation tree")
        elif mapping_source == MappingSource.UNMAPPED:
            return (0.00, "Unmapped - failed to find matching concept")

    # Fallback to method string parsing (for backward compatibility)
    method_lower = method.lower()

    if "brain" in method_lower or "user memory" in method_lower:
        return (1.00, "Analyst Brain - highest trust (user override)")
    elif "alias" in method_lower:
        return (0.95, "Explicit Alias - manually curated mapping")
    elif "exact" in method_lower or "standard label" in method_lower:
        return (0.90, "Exact Label Match - official XBRL taxonomy")
    elif "keyword" in method_lower or "partial" in method_lower:
        return (0.70, "Keyword Match - fuzzy matching")
    elif "safe parent" in method_lower or "hierarchy" in method_lower or "fallback" in method_lower:
        # Try to extract depth from method string
        if "depth=" in method_lower:
            try:
                depth_str = method_lower.split("depth=")[1].split(")")[0].strip()
                depth = int(depth_str)
            except (ValueError, IndexError):
                depth = 1
        confidence = max(0.50, 0.70 - (depth * 0.05))
        return (confidence, f"Hierarchy Fallback (depth={depth}) - walked up presentation tree")
    elif "unmapped" in method_lower or not method:
        return (0.00, "Unmapped - failed to find matching concept")

    # Default: unknown method, assign medium-low confidence
    return (0.60, f"Unknown mapping method: {method}")


# =============================================================================
# CONFIDENCE CALCULATION - AGGREGATION
# =============================================================================

def calculate_aggregation_confidence(
    strategy: AggregationStrategy,
    has_conflicts: bool = False
) -> Tuple[float, str]:
    """
    Calculate confidence for an aggregation operation.

    Args:
        strategy: AggregationStrategy enum value
        has_conflicts: Whether double-counting conflicts were detected

    Returns:
        Tuple of (confidence_score, explanation)

    Confidence by Strategy:
        TOTAL_LINE_USED: 0.95 (most reliable - uses reported total)
        COMPONENT_SUM: 0.85 (high confidence - validated sum)
        SINGLE_VALUE: 0.90 (no aggregation ambiguity)
        MAX_VALUE: 0.60 (ambiguous - unclear which total is correct)

    Double-Counting Penalty:
        If conflicts detected but NOT prevented: -0.20 penalty
    """
    base_confidence = 0.60
    explanation = "Unknown aggregation strategy"

    if strategy == AggregationStrategy.TOTAL_LINE_USED:
        base_confidence = 0.95
        explanation = "Total Line Used - detected and used explicit total from source data"
    elif strategy == AggregationStrategy.COMPONENT_SUM:
        base_confidence = 0.85
        explanation = "Component Sum - summed granular components (double-counting prevented)"
    elif strategy == AggregationStrategy.SINGLE_VALUE:
        base_confidence = 0.90
        explanation = "Single Value - only one value present, no aggregation ambiguity"
    elif strategy == AggregationStrategy.MAX_VALUE:
        base_confidence = 0.60
        explanation = "Max Value - multiple totals found, used maximum (ambiguous)"

    # Apply penalty if conflicts were detected but not resolved
    if has_conflicts and strategy != AggregationStrategy.TOTAL_LINE_USED:
        base_confidence = max(0.00, base_confidence - 0.20)
        explanation += " [WARNING: potential double-counting detected]"

    return (base_confidence, explanation)


# =============================================================================
# CONFIDENCE CALCULATION - ITERATIVE RECOVERY
# =============================================================================

def calculate_recovery_confidence(attempt_num: int) -> Tuple[float, str]:
    """
    Calculate confidence based on iterative recovery attempt number.

    Args:
        attempt_num: Which recovery attempt succeeded (1, 2, 3, ...)

    Returns:
        Tuple of (confidence_score, explanation)

    Confidence by Attempt:
        Attempt 1 (Strict): 0.95 - used official IB rules concept sets
        Attempt 2 (Relaxed): 0.70 - required fallback to fuzzy matching
        Attempt 3 (Desperate): 0.40 - last resort, high uncertainty
        Failed (all attempts): 0.00 - critical bucket remains zero

    Rationale:
        If strict rules fail, data quality or mapping is questionable.
        Desperate recovery is unreliable for investment decisions.
    """
    if attempt_num == 1:
        return (0.95, "Strict Recovery (Attempt 1) - used official IB rules")
    elif attempt_num == 2:
        return (0.70, "Relaxed Recovery (Attempt 2) - required fuzzy matching")
    elif attempt_num == 3:
        return (0.40, "Desperate Recovery (Attempt 3) - last resort, high uncertainty")
    elif attempt_num == 0 or attempt_num > 3:
        return (0.00, "Recovery Failed - all attempts exhausted")
    else:
        # Shouldn't happen, but handle gracefully
        return (0.50, f"Unknown recovery attempt: {attempt_num}")


# =============================================================================
# CONFIDENCE CALCULATION - FORMULA COMPLEXITY
# =============================================================================

class FormulaType(Enum):
    """Types of formulas with different complexity factors."""
    SIMPLE_ARITHMETIC = "simple_arithmetic"      # A + B, A - B
    MULTIPLICATION = "multiplication"            # A × B, A / B
    GROWTH_RATE = "growth_rate"                  # (New - Old) / Old
    WACC = "wacc"                                # Weighted avg cost of capital
    TERMINAL_VALUE = "terminal_value"            # Perpetuity calculation
    IRR = "irr"                                  # Internal rate of return


def get_formula_complexity_factor(formula_type: FormulaType) -> Tuple[float, str]:
    """
    Get complexity factor for formula calculations.

    Args:
        formula_type: Type of formula being calculated

    Returns:
        Tuple of (complexity_factor, explanation)

    Complexity Factors:
        Simple arithmetic (+, -): 1.00
        Multiplication/Division: 0.98
        Growth rate: 0.95
        WACC: 0.90 (multiple inputs, sensitive)
        Terminal value: 0.85 (perpetuity assumption risk)
        IRR: 0.80 (iterative solver, sensitive)
    """
    if formula_type == FormulaType.SIMPLE_ARITHMETIC:
        return (1.00, "Simple arithmetic - no degradation")
    elif formula_type == FormulaType.MULTIPLICATION:
        return (0.98, "Multiplication/Division - minimal degradation")
    elif formula_type == FormulaType.GROWTH_RATE:
        return (0.95, "Growth rate calculation - standard")
    elif formula_type == FormulaType.WACC:
        return (0.90, "WACC calculation - multiple inputs, sensitive to errors")
    elif formula_type == FormulaType.TERMINAL_VALUE:
        return (0.85, "Terminal value - perpetuity assumption risk")
    elif formula_type == FormulaType.IRR:
        return (0.80, "IRR - iterative solver, sensitive to inputs")
    else:
        return (0.95, "Unknown formula type - default degradation")


def infer_formula_type(formula: str) -> FormulaType:
    """
    Infer formula type from formula string.

    Args:
        formula: Formula string (e.g., "A + B", "WACC = ...")

    Returns:
        FormulaType enum value
    """
    formula_lower = formula.lower()

    if "irr" in formula_lower or "internal rate" in formula_lower:
        return FormulaType.IRR
    elif "wacc" in formula_lower or "cost of capital" in formula_lower:
        return FormulaType.WACC
    elif "terminal" in formula_lower or "perpetuity" in formula_lower:
        return FormulaType.TERMINAL_VALUE
    elif "growth" in formula_lower or "cagr" in formula_lower:
        return FormulaType.GROWTH_RATE
    elif "*" in formula or "/" in formula or "×" in formula or "÷" in formula:
        return FormulaType.MULTIPLICATION
    else:
        return FormulaType.SIMPLE_ARITHMETIC


# =============================================================================
# CONFIDENCE PROPAGATION
# =============================================================================

def propagate_confidence(
    source_confidences: List[float],
    transformation_confidence: float,
    formula: Optional[str] = None
) -> Tuple[float, str]:
    """
    Propagate confidence through a transformation.

    Args:
        source_confidences: Confidence scores of input nodes
        transformation_confidence: Confidence of the transformation itself
        formula: Optional formula string for complexity analysis

    Returns:
        Tuple of (target_confidence, explanation)

    Propagation Rules:
        1. Target = MIN(source_confidences) × transformation_confidence
        2. If formula provided, apply complexity factor
        3. Floor at 0.00, cap at source minimum

    Rationale:
        Chain is only as strong as weakest link. Multiplying captures degradation.
    """
    if not source_confidences:
        return (0.00, "No source data - cannot calculate confidence")

    # Remove any None values and ensure all are floats
    valid_sources = [float(c) for c in source_confidences if c is not None]

    if not valid_sources:
        return (0.00, "No valid source confidences")

    # Find minimum source confidence (weakest link)
    min_source = min(valid_sources)

    # Apply transformation confidence
    target_confidence = min_source * transformation_confidence

    # Apply formula complexity factor if formula provided
    complexity_factor = 1.0
    complexity_note = ""
    if formula:
        formula_type = infer_formula_type(formula)
        complexity_factor, complexity_note = get_formula_complexity_factor(formula_type)
        target_confidence *= complexity_factor

    # Enforce bounds [0.0, min_source]
    target_confidence = max(0.00, min(target_confidence, min_source))

    # Build explanation
    explanation = f"Propagated from {len(valid_sources)} source(s): "
    explanation += f"MIN({', '.join(f'{c:.2f}' for c in valid_sources)}) = {min_source:.2f}"
    explanation += f" × transform({transformation_confidence:.2f})"
    if complexity_factor != 1.0:
        explanation += f" × complexity({complexity_factor:.2f})"
    explanation += f" = {target_confidence:.3f}"

    if complexity_note:
        explanation += f" [{complexity_note}]"

    return (target_confidence, explanation)


# =============================================================================
# BLOCKING RULES (INVESTMENT BANKING STANDARDS)
# =============================================================================

@dataclass
class BlockingThresholds:
    """Blocking thresholds for a specific model type and metric."""
    metric_name: str
    block_below: float      # Critical blocker (model refused)
    warn_below: float       # Warning (model with disclaimer)
    pass_above: float       # Pass (model delivered)

    def check(self, confidence: float) -> Tuple[str, str]:
        """
        Check confidence against thresholds.

        Returns:
            Tuple of (status, reason)
            Status: "BLOCKED", "WARNING", or "PASS"
        """
        if confidence < self.block_below:
            return ("BLOCKED",
                    f"{self.metric_name} confidence ({confidence:.2f}) below minimum threshold ({self.block_below:.2f})")
        elif confidence < self.warn_below:
            return ("WARNING",
                    f"{self.metric_name} confidence ({confidence:.2f}) below recommended threshold ({self.warn_below:.2f})")
        else:
            return ("PASS", "")


# DCF Model Thresholds
DCF_THRESHOLDS = {
    "Revenue": BlockingThresholds("Revenue", 0.60, 0.75, 0.75),
    "EBITDA": BlockingThresholds("EBITDA", 0.60, 0.75, 0.75),
    "Net Income": BlockingThresholds("Net Income", 0.50, 0.60, 0.60),
    "WACC": BlockingThresholds("WACC", 0.70, 0.80, 0.80),
    "Capex": BlockingThresholds("Capex", 0.50, 0.60, 0.60),
    "Working Capital": BlockingThresholds("Working Capital", 0.50, 0.60, 0.60),
}

# LBO Model Thresholds
LBO_THRESHOLDS = {
    "EBITDA": BlockingThresholds("EBITDA", 0.65, 0.75, 0.75),
    "Debt": BlockingThresholds("Debt", 0.70, 0.80, 0.80),
    "Interest Expense": BlockingThresholds("Interest Expense", 0.70, 0.80, 0.80),
    "Exit EBITDA": BlockingThresholds("Exit EBITDA", 0.60, 0.70, 0.70),
    "IRR": BlockingThresholds("IRR", 0.50, 0.65, 0.65),
    "Cash Flow": BlockingThresholds("Cash Flow", 0.60, 0.75, 0.75),
}

# Comps Analysis Thresholds
COMPS_THRESHOLDS = {
    "Revenue": BlockingThresholds("Revenue", 0.60, 0.75, 0.75),
    "EBITDA": BlockingThresholds("EBITDA", 0.60, 0.75, 0.75),
    "Market Cap": BlockingThresholds("Market Cap", 0.80, 0.85, 0.85),
    "Enterprise Value": BlockingThresholds("Enterprise Value", 0.75, 0.80, 0.80),
}


def check_blocking_rules(
    model_type: str,
    critical_inputs: Dict[str, float]
) -> Tuple[str, List[str], List[str]]:
    """
    Check if model should be blocked based on confidence thresholds.

    Args:
        model_type: "DCF", "LBO", or "COMPS"
        critical_inputs: Dict mapping metric names to confidence scores
                        e.g., {"Revenue": 0.82, "EBITDA": 0.75}

    Returns:
        Tuple of (overall_status, blocking_reasons, warning_reasons)
        overall_status: "BLOCKED", "WARNING", or "PASS"
        blocking_reasons: List of critical blockers
        warning_reasons: List of warnings

    Blocking Logic:
        - If ANY metric is BLOCKED → overall status = BLOCKED
        - Else if ANY metric has WARNING → overall status = WARNING
        - Else → overall status = PASS
        - CRITICAL: Any confidence = 0.00 → IMMEDIATE BLOCK
    """
    # Select thresholds based on model type
    if model_type.upper() == "DCF":
        thresholds = DCF_THRESHOLDS
    elif model_type.upper() == "LBO":
        thresholds = LBO_THRESHOLDS
    elif model_type.upper() in ["COMPS", "COMPARABLES"]:
        thresholds = COMPS_THRESHOLDS
    else:
        return ("BLOCKED", [f"Unknown model type: {model_type}"], [])

    blocking_reasons = []
    warning_reasons = []

    # Check each critical input
    for metric_name, confidence in critical_inputs.items():
        # CRITICAL: Confidence = 0.00 → IMMEDIATE BLOCK
        if confidence == 0.00:
            blocking_reasons.append(
                f"{metric_name} has zero confidence (missing or invalid data) - CRITICAL BLOCKER"
            )
            continue

        # Get threshold for this metric (if defined)
        threshold = thresholds.get(metric_name)
        if not threshold:
            # No threshold defined - log warning but don't block
            warning_reasons.append(f"{metric_name} has no defined threshold (confidence: {confidence:.2f})")
            continue

        # Check threshold
        status, reason = threshold.check(confidence)

        if status == "BLOCKED":
            blocking_reasons.append(reason)
        elif status == "WARNING":
            warning_reasons.append(reason)
        # PASS - no action needed

    # Determine overall status
    if blocking_reasons:
        overall_status = "BLOCKED"
    elif warning_reasons:
        overall_status = "WARNING"
    else:
        overall_status = "PASS"

    return (overall_status, blocking_reasons, warning_reasons)


# =============================================================================
# CONFIDENCE REPORTING
# =============================================================================

@dataclass
class ModelOutput:
    """Container for model output with confidence metadata."""
    model_type: str                              # "DCF", "LBO", "COMPS"
    overall_confidence: float                     # MIN of critical inputs
    critical_inputs: Dict[str, float]            # {"Revenue": 0.82, ...}
    blocking_status: str                         # "PASS", "WARNING", "BLOCKED"
    blocking_reasons: List[str] = field(default_factory=list)
    warning_reasons: List[str] = field(default_factory=list)
    low_confidence_items: List[Dict[str, Any]] = field(default_factory=list)


def generate_confidence_report(model_output: ModelOutput) -> str:
    """
    Generate human-readable confidence report for a model.

    Args:
        model_output: ModelOutput instance with confidence metadata

    Returns:
        Formatted confidence report string
    """
    report_lines = []

    # Header
    report_lines.append("=" * 70)
    report_lines.append(f"{model_output.model_type} MODEL CONFIDENCE REPORT")
    report_lines.append("=" * 70)
    report_lines.append("")

    # Overall status
    status_symbol = {
        "PASS": "✓",
        "WARNING": "⚠",
        "BLOCKED": "✗"
    }.get(model_output.blocking_status, "?")

    report_lines.append(f"Overall Status: {status_symbol} {model_output.blocking_status}")
    report_lines.append(f"Overall Confidence: {model_output.overall_confidence:.2f}")
    report_lines.append("")

    # Critical inputs
    report_lines.append("Critical Inputs:")
    report_lines.append("-" * 70)
    for metric, confidence in sorted(model_output.critical_inputs.items()):
        symbol = "✓" if confidence >= 0.75 else ("⚠" if confidence >= 0.60 else "✗")
        report_lines.append(f"  {metric:20s}: {confidence:.2f} {symbol}")
    report_lines.append("")

    # Blocking reasons (if any)
    if model_output.blocking_reasons:
        report_lines.append("CRITICAL BLOCKERS:")
        report_lines.append("-" * 70)
        for reason in model_output.blocking_reasons:
            report_lines.append(f"  ✗ {reason}")
        report_lines.append("")
        report_lines.append("ACTION REQUIRED: Fix blocking issues before model can be generated.")
        report_lines.append("")

    # Warnings (if any)
    if model_output.warning_reasons:
        report_lines.append("WARNINGS:")
        report_lines.append("-" * 70)
        for reason in model_output.warning_reasons:
            report_lines.append(f"  ⚠ {reason}")
        report_lines.append("")
        if model_output.blocking_status == "WARNING":
            report_lines.append("RECOMMENDATION: Review flagged items before client delivery.")
        report_lines.append("")

    # Low confidence items
    if model_output.low_confidence_items:
        report_lines.append("Low Confidence Items (Review Recommended):")
        report_lines.append("-" * 70)
        for item in model_output.low_confidence_items[:10]:  # Limit to top 10
            name = item.get("name", "Unknown")
            conf = item.get("confidence", 0.0)
            reason = item.get("reason", "No explanation")
            report_lines.append(f"  {name}: {conf:.2f} - {reason}")

        if len(model_output.low_confidence_items) > 10:
            report_lines.append(f"  ... and {len(model_output.low_confidence_items) - 10} more")
        report_lines.append("")

    # Footer
    if model_output.blocking_status == "PASS":
        report_lines.append("✓ Model suitable for delivery.")
    elif model_output.blocking_status == "WARNING":
        report_lines.append("⚠ Model generated with warnings - verify before delivery.")
    else:
        report_lines.append("✗ Model BLOCKED - cannot generate until issues resolved.")

    report_lines.append("=" * 70)

    return "\n".join(report_lines)


def generate_confidence_breakdown(
    node_value: Any,
    node_confidence: float,
    confidence_components: Dict[str, float]
) -> str:
    """
    Generate detailed confidence breakdown for a single node.

    Args:
        node_value: The value of the node
        node_confidence: Final confidence score
        confidence_components: Dict of component confidences
                              e.g., {"mapping": 0.90, "aggregation": 0.85}

    Returns:
        Formatted breakdown string
    """
    lines = []
    lines.append(f"Value: {node_value}")
    lines.append(f"Confidence: {node_confidence:.3f}")
    lines.append("")
    lines.append("Breakdown:")

    for component, conf in confidence_components.items():
        lines.append(f"  ├─ {component}: {conf:.3f}")

    # Show calculation
    if len(confidence_components) > 1:
        product = 1.0
        calc_parts = []
        for comp, conf in confidence_components.items():
            product *= conf
            calc_parts.append(f"{conf:.3f}")
        lines.append(f"  └─ Final: {' × '.join(calc_parts)} = {product:.3f}")

    return "\n".join(lines)


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("Confidence Engine - Production V1.0")
    print("=" * 70)
    print()

    # Example 1: Mapping confidence
    print("Example 1: Mapping Confidence")
    print("-" * 70)
    conf, expl = calculate_mapping_confidence("Analyst Brain", MappingSource.ANALYST_BRAIN)
    print(f"Analyst Brain: {conf:.2f} - {expl}")

    conf, expl = calculate_mapping_confidence("Keyword Match", MappingSource.KEYWORD)
    print(f"Keyword Match: {conf:.2f} - {expl}")

    conf, expl = calculate_mapping_confidence("Hierarchy Fallback", MappingSource.HIERARCHY, depth=3)
    print(f"Hierarchy (depth=3): {conf:.2f} - {expl}")
    print()

    # Example 2: Aggregation confidence
    print("Example 2: Aggregation Confidence")
    print("-" * 70)
    conf, expl = calculate_aggregation_confidence(AggregationStrategy.TOTAL_LINE_USED)
    print(f"Total Line Used: {conf:.2f} - {expl}")

    conf, expl = calculate_aggregation_confidence(AggregationStrategy.MAX_VALUE, has_conflicts=True)
    print(f"Max Value (conflicts): {conf:.2f} - {expl}")
    print()

    # Example 3: Confidence propagation
    print("Example 3: Confidence Propagation")
    print("-" * 70)
    sources = [0.90, 0.85, 0.80]
    transform = 0.85
    conf, expl = propagate_confidence(sources, transform)
    print(f"Propagation: {conf:.3f}")
    print(f"Explanation: {expl}")
    print()

    # Example 4: Blocking rules
    print("Example 4: DCF Blocking Rules")
    print("-" * 70)
    critical_inputs = {
        "Revenue": 0.82,
        "EBITDA": 0.78,
        "Net Income": 0.75,
        "WACC": 0.80,
        "Capex": 0.55
    }

    status, blocks, warns = check_blocking_rules("DCF", critical_inputs)
    print(f"Status: {status}")
    if blocks:
        print("Blockers:")
        for b in blocks:
            print(f"  - {b}")
    if warns:
        print("Warnings:")
        for w in warns:
            print(f"  - {w}")
    print()

    # Example 5: Confidence report
    print("Example 5: Model Confidence Report")
    print("-" * 70)
    model = ModelOutput(
        model_type="DCF",
        overall_confidence=0.75,
        critical_inputs=critical_inputs,
        blocking_status=status,
        blocking_reasons=blocks,
        warning_reasons=warns,
        low_confidence_items=[
            {"name": "Capex (2024)", "confidence": 0.55, "reason": "Keyword match - verify accuracy"}
        ]
    )

    print(generate_confidence_report(model))

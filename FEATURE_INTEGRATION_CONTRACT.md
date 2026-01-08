# FinanceX Feature Integration Contract
## Production V1.0 - Investment Banking Grade

**Status**: MANDATORY for all new features
**Enforcement**: Code review blocker
**Rationale**: Financial systems require absolute traceability and determinism

---

## Table of Contents

1. [Core Invariants](#core-invariants)
2. [Integration Requirements](#integration-requirements)
3. [Required Tests](#required-tests)
4. [Forbidden Patterns](#forbidden-patterns)
5. [Anti-Speculation Rules](#anti-speculation-rules)
6. [Case Study: Why CLI Features Fail](#case-study-why-cli-features-fail)
7. [Enforcement Mechanisms](#enforcement-mechanisms)

---

## Core Invariants

These invariants MUST be maintained by every feature. Violation = REJECT.

### Invariant 1: Complete Lineage Tracking
**Rule**: Every financial value MUST be traceable to its ultimate source (Excel cell, user input, or calculation).

**Implementation Requirements**:
- All data transformations create nodes in `FinancialLineageGraph`
- All transformations create edges with `EdgeType` specification
- Graph must be serializable and deserializable without loss

**Test**:
```python
def test_lineage_complete(self):
    """Every output value must trace back to source."""
    # Pick any final output value
    output_node = graph.query_nodes_by_type(NodeType.CALCULATED)[0]

    # Trace backward to source
    ancestors = graph.trace_backward(output_node.node_id)

    # Must find at least one SOURCE_CELL node
    source_cells = [n for n in ancestors if n.node_type == NodeType.SOURCE_CELL]
    assert len(source_cells) > 0, "No source found - lineage broken"
```

### Invariant 2: Audit Trail Completeness
**Rule**: Every transformation MUST be auditable with method, inputs, and reasoning.

**Implementation Requirements**:
- All mapping decisions recorded in `FinancialEdge.method`
- All aggregations record `AggregationStrategy`
- All calculations record `formula` and `formula_inputs`
- Alternative paths recorded in `alternatives_considered`

**Test**:
```python
def test_audit_trail_complete(self):
    """Every edge must have explanation."""
    for edge in graph.edges.values():
        assert edge.method != "", f"Edge {edge.edge_id} missing method"
        if edge.edge_type == EdgeType.AGGREGATION:
            assert edge.aggregation_strategy is not None
        if edge.edge_type == EdgeType.CALCULATION:
            assert edge.formula is not None
```

### Invariant 3: Confidence Propagation
**Rule**: Every value MUST carry a confidence score that propagates correctly.

**Implementation Requirements**:
- All nodes have `confidence` field (0.0 to 1.0)
- All edges have `confidence` and `confidence_source`
- Confidence propagates via `MIN(sources) × transformation`
- Confidence breakdown must be traceable

**Test**:
```python
def test_confidence_propagation(self):
    """Confidence must degrade or maintain, never improve."""
    for edge in graph.edges.values():
        if not edge.is_active:
            continue

        # Get source confidences
        source_confs = [graph.get_node(sid).confidence
                       for sid in edge.source_node_ids]

        # Get target confidence
        target = graph.get_node(edge.target_node_id)

        # Target confidence must not exceed minimum source
        assert target.confidence <= min(source_confs) + 0.01  # floating point tolerance
```

### Invariant 4: No Hidden State
**Rule**: All state MUST be in the lineage graph or explicit data structures. No global variables, no caches without invalidation.

**Implementation Requirements**:
- Use `FinancialLineageGraph` for all financial data
- Use `session_id` for scoping temporary state
- Any caching must have explicit TTL and invalidation
- No mutable class variables

**Test**:
```python
def test_no_hidden_state(self):
    """Running same operation twice must produce identical results."""
    # Run pipeline twice with same input
    result1 = run_pipeline(input_file, session_id="test1")
    result2 = run_pipeline(input_file, session_id="test2")

    # Results must be identical
    assert result1.equals(result2), "Non-deterministic behavior detected"
```

### Invariant 5: Determinism
**Rule**: Same input MUST always produce same output. No randomness, no timestamps in calculations.

**Implementation Requirements**:
- No `random`, no `uuid` in calculations
- Timestamps only for metadata (`created_at`), never for logic
- Sorting must have deterministic tiebreakers
- Dictionary iteration order must not affect output

**Test**:
```python
def test_determinism(self):
    """Same input = same output, always."""
    results = []
    for i in range(3):
        result = calculate_dcf(input_data)
        results.append(result.to_dict())

    # All results must be identical
    assert results[0] == results[1] == results[2]
```

---

## Integration Requirements

### Checklist for New Features

Before submitting PR, answer YES to ALL:

#### Lineage Integration
- [ ] Does feature create nodes for all intermediate values?
- [ ] Does feature create edges for all transformations?
- [ ] Are all `EdgeType`, `NodeType` enums used correctly?
- [ ] Can user trace any output back to Excel source?
- [ ] Is graph serializable after feature runs?

#### Audit Integration
- [ ] Does feature log all decisions to audit trail?
- [ ] Are all alternative paths recorded (even if not taken)?
- [ ] Can auditor understand why each choice was made?
- [ ] Are source labels preserved for human review?
- [ ] Does feature add entries to `engine.audit_log`?

#### Confidence Integration
- [ ] Does feature calculate confidence for all outputs?
- [ ] Does feature propagate confidence from inputs?
- [ ] Are confidence breakdowns traceable?
- [ ] Does feature check blocking thresholds before output?
- [ ] Does low confidence trigger warnings?

#### State Management
- [ ] Is all state in graph or explicit structs?
- [ ] Are temporary states scoped to `session_id`?
- [ ] Can feature run in parallel sessions without conflicts?
- [ ] Is cleanup explicit (no leaked resources)?

#### Determinism
- [ ] Does feature produce same output for same input?
- [ ] Are there any random or time-dependent calculations?
- [ ] Is sorting deterministic?
- [ ] Are floating-point operations stable?

---

## Required Tests

Every new feature MUST include these test categories:

### 1. Unit Tests (>95% coverage)
```python
class TestNewFeature(unittest.TestCase):
    def test_basic_functionality(self):
        """Feature works for happy path."""
        pass

    def test_edge_cases(self):
        """Feature handles edge cases correctly."""
        pass

    def test_error_handling(self):
        """Feature fails gracefully with clear errors."""
        pass
```

### 2. Lineage Tests
```python
class TestNewFeatureLineage(unittest.TestCase):
    def test_creates_nodes(self):
        """Feature creates appropriate nodes."""
        graph = run_feature_with_graph()
        assert len(graph.nodes) > 0

    def test_creates_edges(self):
        """Feature creates edges linking nodes."""
        graph = run_feature_with_graph()
        assert len(graph.edges) > 0

    def test_traceable_to_source(self):
        """All outputs trace back to source."""
        graph = run_feature_with_graph()
        for node in graph.query_nodes_by_type(NodeType.CALCULATED):
            ancestors = graph.trace_backward(node.node_id)
            sources = [n for n in ancestors if n.node_type == NodeType.SOURCE_CELL]
            assert len(sources) > 0
```

### 3. Confidence Tests
```python
class TestNewFeatureConfidence(unittest.TestCase):
    def test_confidence_assigned(self):
        """All outputs have confidence scores."""
        result = run_feature()
        assert result.confidence > 0.0

    def test_confidence_propagates(self):
        """Confidence degrades correctly."""
        result = run_feature_with_low_input_confidence()
        assert result.confidence < input_confidence

    def test_blocking_rules(self):
        """Low confidence triggers blocks."""
        with self.assertRaises(ModelValidationError):
            run_feature_with_zero_confidence()
```

### 4. Integration Tests
```python
class TestNewFeatureIntegration(unittest.TestCase):
    def test_end_to_end(self):
        """Feature works in full pipeline."""
        result = run_full_pipeline_with_feature()
        assert result is not None

    def test_backwards_compatibility(self):
        """Feature doesn't break existing functionality."""
        old_result = run_pipeline_without_feature()
        new_result = run_pipeline_with_feature()
        assert old_result.core_metrics.equals(new_result.core_metrics)
```

### 5. Determinism Tests
```python
class TestNewFeatureDeterminism(unittest.TestCase):
    def test_repeated_runs(self):
        """Same input = same output."""
        results = [run_feature() for _ in range(5)]
        assert all(r == results[0] for r in results)

    def test_parallel_sessions(self):
        """Parallel runs don't interfere."""
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(run_feature, session_id=f"s{i}")
                      for i in range(4)]
            results = [f.result() for f in futures]

        # All results should be identical
        assert all(r == results[0] for r in results)
```

---

## Forbidden Patterns

These patterns are PROHIBITED. Code review MUST reject:

### ❌ FORBIDDEN: Inferred Financial Meaning
```python
# BAD: Guessing what "Sales" means
if "sales" in label.lower():
    return "us-gaap_Revenues"  # WRONG - not traceable
```

**Why**: Financial labels are ambiguous. "Sales" could mean:
- Revenue
- Cost of Sales
- Sales & Marketing expense
- Asset sales

**Correct Approach**: Use explicit mapping with confidence scoring:
```python
# GOOD: Explicit mapping with low confidence
mapping = mapper.map_input(label)
if mapping["found"]:
    return {
        "concept": mapping["concept_id"],
        "confidence": mapping["confidence"],  # e.g., 0.70 for keyword match
        "method": mapping["method"]
    }
else:
    return {
        "concept": None,
        "confidence": 0.00,
        "method": "Unmapped"
    }
```

### ❌ FORBIDDEN: Imputing Missing Values
```python
# BAD: Filling gaps with assumptions
if capex == 0:
    capex = revenue * 0.05  # WRONG - arbitrary assumption
```

**Why**: Investment bankers need to know when data is missing. Silently filling gaps hides data quality issues.

**Correct Approach**: Mark as missing with zero confidence:
```python
# GOOD: Explicit handling of missing data
capex = self._sum_bucket(CAPEX_IDS)
if capex.sum() == 0:
    logger.warning("Capex not found in source data")
    # Don't impute - use zero with confidence = 0.00
    self.confidence_scores["Capex"] = 0.00
```

### ❌ FORBIDDEN: Hidden State in Global Variables
```python
# BAD: Global cache without invalidation
_MAPPING_CACHE = {}

def map_label(label):
    if label in _MAPPING_CACHE:
        return _MAPPING_CACHE[label]  # WRONG - no session scoping
```

**Why**: Global state breaks parallel processing and makes testing impossible.

**Correct Approach**: Scope state to session or pass explicitly:
```python
# GOOD: Session-scoped state
class Mapper:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self._cache: Dict[str, dict] = {}  # Instance variable

    def map_label(self, label):
        if label in self._cache:
            return self._cache[label]
        # ...
```

### ❌ FORBIDDEN: Calculations Without Lineage
```python
# BAD: Calculation that doesn't create edges
def calculate_ebitda(revenue, cogs, opex):
    return revenue - cogs - opex  # WRONG - no audit trail
```

**Why**: Auditors need to see how every number was calculated.

**Correct Approach**: Create edges for all calculations:
```python
# GOOD: Calculation with lineage tracking
def calculate_ebitda(graph_builder, revenue_node_id, cogs_node_id, opex_node_id):
    revenue_node = graph.get_node(revenue_node_id)
    cogs_node = graph.get_node(cogs_node_id)
    opex_node = graph.get_node(opex_node_id)

    ebitda_value = revenue_node.value - cogs_node.value - opex_node.value

    # Create node and edge with full provenance
    node_id, edge_id = graph_builder.add_calculation(
        source_node_ids=[revenue_node_id, cogs_node_id, opex_node_id],
        result_label="EBITDA",
        formula="Revenue - COGS - OpEx",
        inputs={"Revenue": revenue_node.value, "COGS": cogs_node.value, "OpEx": opex_node.value},
        result_value=ebitda_value,
        period=revenue_node.period
    )

    return node_id
```

### ❌ FORBIDDEN: Silent Failures
```python
# BAD: Swallowing errors
try:
    revenue = get_revenue()
except Exception:
    revenue = 0  # WRONG - hides problems
```

**Why**: Silent failures in financial systems lead to incorrect valuations.

**Correct Approach**: Fail loudly or log explicitly:
```python
# GOOD: Explicit error handling
try:
    revenue = get_revenue()
except MappingError as e:
    logger.error(f"Revenue mapping failed: {e}")
    revenue = 0
    self.confidence_scores["Revenue"] = 0.00
    self.audit_log.append(AuditEntry(
        metric="Revenue",
        value=0,
        method="Failed",
        concepts_used=[],
        validation_status="ERROR",
        notes=str(e)
    ))
```

### ❌ FORBIDDEN: Non-Deterministic Operations
```python
# BAD: Random or time-based logic
confidence = 0.7 + random.random() * 0.3  # WRONG
threshold = get_current_market_sentiment()  # WRONG
```

**Why**: Financial models must be reproducible for audits.

**Correct Approach**: Use only deterministic inputs:
```python
# GOOD: Deterministic confidence calculation
confidence = calculate_mapping_confidence(
    method=mapping_method,
    mapping_source=MappingSource.KEYWORD,
    depth=0
)  # Always returns same value for same inputs
```

---

## Anti-Speculation Rules

### Rule 1: No Inferred Financial Meaning
**Constraint**: Financial concepts must be explicitly mapped, never inferred.

**Enforceable Check**:
```python
def enforce_no_inference(code_path: str):
    """Scan code for inference patterns."""
    banned_patterns = [
        r"if .* in label.*return.*us-gaap",  # Inferred mapping
        r".*assume.*",                        # Assumption comments
        r".*probably.*",                      # Speculation
        r".*guess.*",                         # Guessing
    ]

    with open(code_path) as f:
        code = f.read()
        for pattern in banned_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                raise ValueError(f"Inference pattern detected: {pattern}")
```

### Rule 2: No Value Imputation Without Mathematical Proof
**Constraint**: Missing values stay missing unless derivable from accounting identities.

**Allowed**:
```python
# ALLOWED: Mathematically implied
assets = liabilities + equity  # Accounting identity
```

**Forbidden**:
```python
# FORBIDDEN: Statistical imputation
if missing(capex):
    capex = revenue * industry_avg_capex_ratio  # NO!
```

**Enforceable Check**:
```python
def enforce_no_imputation(func_name: str, source_code: str):
    """Ensure imputation is only for mathematical identities."""
    if "impute" in func_name or "fill" in func_name:
        # Must have proof annotation
        if "@mathematically_derived" not in source_code:
            raise ValueError("Imputation without mathematical proof")
```

### Rule 3: No Values Without Traceable Sources
**Constraint**: Every value must trace to Excel cell, user input, or calculation.

**Enforceable Check**:
```python
def enforce_traceable_sources(graph: FinancialLineageGraph):
    """Verify all values have sources."""
    for node in graph.nodes.values():
        if node.node_type in [NodeType.AGGREGATED, NodeType.CALCULATED]:
            # Must have incoming edges
            incoming = graph.get_incoming_edges(node.node_id)
            if len(incoming) == 0:
                raise ValueError(f"Node {node.node_id} has no source")

            # Must trace to source cells
            ancestors = graph.trace_backward(node.node_id)
            sources = [n for n in ancestors if n.node_type == NodeType.SOURCE_CELL]
            if len(sources) == 0:
                raise ValueError(f"Node {node.node_id} not traceable to source")
```

### Rule 4: Confidence Must Degrade or Maintain
**Constraint**: Transformations can only reduce confidence, never increase it.

**Enforceable Check**:
```python
def enforce_confidence_monotonicity(graph: FinancialLineageGraph):
    """Confidence can only degrade through transformations."""
    for edge in graph.edges.values():
        if not edge.is_active:
            continue

        source_confs = [graph.get_node(sid).confidence
                       for sid in edge.source_node_ids]
        target_conf = graph.get_node(edge.target_node_id).confidence

        min_source = min(source_confs)
        if target_conf > min_source + 0.01:  # floating point tolerance
            raise ValueError(
                f"Edge {edge.edge_id} increases confidence: "
                f"{min_source:.3f} -> {target_conf:.3f}"
            )
```

### Rule 5: No Magic Numbers
**Constraint**: All numerical constants must be named and justified.

**Forbidden**:
```python
# BAD: Magic number
if confidence < 0.65:  # Why 0.65?
    block_model()
```

**Correct**:
```python
# GOOD: Named constant with justification
DCF_EBITDA_CONFIDENCE_THRESHOLD = 0.65
# Rationale: Investment banks require 65% confidence minimum for
# LBO debt sizing calculations per standard credit committee guidelines

if confidence < DCF_EBITDA_CONFIDENCE_THRESHOLD:
    block_model()
```

---

## Case Study: Why CLI Features Fail

### Example: Hypothetical "Interactive CLI" Feature

**Proposed Feature**: Add interactive CLI that asks user questions to refine mappings.

**Why It Would Fail**:

#### ❌ Violation 1: No Lineage Tracking
```python
# Hypothetical bad code
def interactive_mapper():
    label = input("Enter label: ")
    concept = input("Enter concept: ")
    # Directly returns without creating graph nodes
    return concept  # WRONG - no audit trail
```

**Problem**: User inputs not recorded in lineage graph. Future auditors can't see why mapping was chosen.

#### ❌ Violation 2: Non-Deterministic
```python
# Hypothetical bad code
def run_pipeline():
    if is_interactive_mode():
        mapping = ask_user()  # Different every time
    else:
        mapping = auto_map()
    return mapping
```

**Problem**: Same input file produces different output depending on user interaction. Violates determinism invariant.

#### ❌ Violation 3: Hidden State in User Session
```python
# Hypothetical bad code
USER_RESPONSES = {}  # Global state

def interactive_mapper(label):
    if label in USER_RESPONSES:
        return USER_RESPONSES[label]  # Not in graph
```

**Problem**: State stored in global variable, not in lineage graph. Not serializable, not auditable.

### Correct Approach: Analyst Brain

The **existing Analyst Brain feature** solves this correctly:

✅ **Lineage Tracked**:
```python
# From mapper.py
if brain_mapping:
    return {
        "element_id": brain_mapping,
        "method": "Analyst Brain (User Memory)",
        "confidence": 1.00,  # Highest trust
        "mapping_source": MappingSource.ANALYST_BRAIN
    }
```

✅ **Deterministic**:
- User decisions stored in JSON file (`brain.json`)
- Same file + same input = same output
- Portable across sessions

✅ **Auditable**:
- All decisions in `brain.json` with timestamps
- Full history of user overrides
- Can replay decisions

✅ **Confidence Integration**:
- Analyst Brain mappings get confidence = 1.00
- Propagates through calculation chain
- Documented in confidence framework

**Lesson**: Interactive features must persist decisions in auditable, deterministic storage (Analyst Brain JSON), not ephemeral user input.

---

## Enforcement Mechanisms

### Pre-Commit Checks

Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash

# Run lineage integration tests
python -m pytest tests/test_*_lineage.py -v
if [ $? -ne 0 ]; then
    echo "❌ Lineage tests failed"
    exit 1
fi

# Run confidence tests
python -m pytest tests/test_confidence_*.py -v
if [ $? -ne 0 ]; then
    echo "❌ Confidence tests failed"
    exit 1
fi

# Check for forbidden patterns
python scripts/enforce_no_speculation.py
if [ $? -ne 0 ]; then
    echo "❌ Speculation patterns detected"
    exit 1
fi

echo "✅ All integration checks passed"
```

### Code Review Checklist

Reviewer must verify:

- [ ] Feature has lineage integration tests
- [ ] Feature has confidence propagation tests
- [ ] Feature has determinism tests
- [ ] No forbidden patterns present
- [ ] All values traceable to source
- [ ] Audit trail complete
- [ ] Documentation updated

### Automated Linting

Create `scripts/enforce_no_speculation.py`:
```python
#!/usr/bin/env python3
"""Enforce anti-speculation rules in code."""

import re
import sys
from pathlib import Path

FORBIDDEN_PATTERNS = {
    r"\bguess\b": "No guessing allowed in financial code",
    r"\bassume\b": "No assumptions without mathematical proof",
    r"\bprobably\b": "No probabilistic language in deterministic code",
    r"\brandom\b": "No randomness in financial calculations",
    r"if.*in.*label.*return.*us-gaap": "No inferred financial meaning",
}

def check_file(filepath: Path) -> List[str]:
    """Check file for forbidden patterns."""
    violations = []

    with open(filepath) as f:
        for line_num, line in enumerate(f, 1):
            for pattern, message in FORBIDDEN_PATTERNS.items():
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(
                        f"{filepath}:{line_num} - {message}\n  {line.strip()}"
                    )

    return violations

if __name__ == "__main__":
    violations = []
    for py_file in Path(".").rglob("*.py"):
        if "tests/" in str(py_file):
            continue  # Skip test files
        violations.extend(check_file(py_file))

    if violations:
        print("❌ SPECULATION VIOLATIONS FOUND:")
        for v in violations:
            print(v)
        sys.exit(1)
    else:
        print("✅ No speculation violations")
        sys.exit(0)
```

---

## Summary

### The Contract in One Sentence

**"Every financial value must be traceable to source, carry a confidence score, be auditable, and be deterministically reproducible."**

### Acceptance Criteria for New Features

1. ✅ All lineage integration tests pass
2. ✅ All confidence integration tests pass
3. ✅ All determinism tests pass
4. ✅ No forbidden patterns in code
5. ✅ Anti-speculation rules enforced
6. ✅ Code review checklist complete

### When in Doubt

**Ask**: "If an auditor reviewed this code 5 years from now, could they understand exactly how this value was calculated?"

If the answer is **NO**, the feature violates the contract.

---

**Document Version**: 1.0
**Author**: FinanceX Engineering
**Date**: 2026-01-08
**Status**: MANDATORY - All features must comply

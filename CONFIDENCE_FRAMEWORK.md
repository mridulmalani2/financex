# FinanceX Confidence Propagation Framework
# Production V1.0 - Investment Banking Grade

## Executive Summary

Every financial output in FinanceX carries a **deterministic confidence score** (0.0 to 1.0) that quantifies the reliability of the underlying data and transformations. This framework is **rule-based** (not ML-based), fully **explainable**, and enforces **hard blocking rules** to prevent delivery of unreliable models to investment bankers.

**Key Principle:** Confidence degrades through transformations, never disappears. A final output's confidence is the minimum confidence of its input chain.

---

## 1. Confidence Scoring Rules (Deterministic)

### 1.1 Mapping Confidence (Tier-Based)

Confidence assigned based on the mapping resolution tier used:

| Tier | Method | Confidence | Rationale |
|------|--------|-----------|-----------|
| 0 | **Analyst Brain (User Override)** | 1.00 | Human expert judgment - highest trust |
| 1 | **Explicit Alias** | 0.95 | Manually curated mappings in aliases.csv |
| 2 | **Exact Label Match** | 0.90 | Official XBRL taxonomy standard label |
| 3 | **Keyword Match** | 0.70 | Fuzzy match (e.g., "Product Revenue" → us-gaap_Revenues) |
| 4 | **Hierarchy Fallback (Safe Parent)** | 0.50 - 0.70 | Walked up presentation tree (penalized by depth) |
| 5 | **Unmapped** | 0.00 | Failed to map - data excluded from models |

**Hierarchy Fallback Penalty:**
```
confidence = 0.70 - (depth * 0.05)
Examples:
  depth=1 → 0.65
  depth=2 → 0.60
  depth=3 → 0.55
  depth=4 → 0.50 (capped at minimum)
```

**Rationale:** Each step up the hierarchy increases abstraction and potential for semantic mismatch.

---

### 1.2 Aggregation Confidence

Confidence assigned based on aggregation strategy:

| Strategy | Confidence | Condition | Rationale |
|----------|-----------|-----------|-----------|
| **TOTAL_LINE_USED** | 0.95 | Detected explicit total line in source data | Most reliable - uses reported total |
| **COMPONENT_SUM** | 0.85 | Summed granular components (prevented double-counting) | High confidence - validated sum |
| **SINGLE_VALUE** | 0.90 | Only one value present for concept+period | No aggregation ambiguity |
| **MAX_VALUE** | 0.60 | Multiple totals found, used maximum | Ambiguous - unclear which total is correct |

**Double-Counting Detection Bonus:**
- If double-counting prevented (hierarchy-aware): +0.00 (already factored into base)
- If potential double-counting detected but NOT prevented: -0.20 penalty

---

### 1.3 Iterative Recovery Confidence

Confidence assigned based on which attempt succeeded:

| Attempt | Strategy | Confidence | Rationale |
|---------|----------|-----------|-----------|
| 1 | **Strict (IB Rules Exact Match)** | 0.95 | Used official IB rules concept sets |
| 2 | **Relaxed (Fuzzy Match)** | 0.70 | Required fallback to fuzzy matching |
| 3 | **Desperate (Keyword + Threshold)** | 0.40 | Last resort - high uncertainty |
| - | **All Attempts Failed** | 0.00 | Critical bucket remains zero |

**Rationale:** If strict rules fail, the data quality or mapping is questionable. Desperate recovery is unreliable.

---

### 1.4 Calculation Confidence

For derived values (formulas in DCF/LBO models):

**Formula Confidence = MIN(input_confidences) × formula_complexity_factor**

**Formula Complexity Factors:**
- Simple arithmetic (A + B, A - B): 1.00
- Multiplication/Division (A × B, A / B): 0.98
- Growth rate calculation: 0.95
- WACC calculation: 0.90 (multiple inputs, sensitive to errors)
- Terminal value calculation: 0.85 (perpetuity assumption risk)
- IRR calculation: 0.80 (iterative solver, sensitive to inputs)

**Division by Zero or Invalid Math:** confidence = 0.00

---

### 1.5 Analyst Override Impact

When analyst brain overrides a mapping:

**Original Confidence:** Based on original method (e.g., 0.70 keyword match)
**Override Confidence:** 1.00 (analyst brain)
**Active Edge:** Override edge (confidence = 1.00)
**Inactive Edge:** Original edge (confidence = 0.70, is_active = False)

**Net Effect:** Confidence increases to 1.00 for overridden paths.

---

## 2. Confidence Propagation Rules

### 2.1 Forward Propagation (Sequential Transformations)

When a node is created from one or more source nodes:

**Rule:** Target confidence = MIN(source confidences) × transformation confidence

```
Example: Revenue Calculation
  Source Node (Mapped Revenue): confidence = 0.90
  Aggregation Strategy (COMPONENT_SUM): confidence = 0.85
  Target Node (Aggregated Revenue): confidence = 0.90 × 0.85 = 0.765
```

**Rationale:** A chain is only as strong as its weakest link. Multiplying captures degradation.

---

### 2.2 Multi-Input Propagation (Many-to-One)

For aggregations or calculations with multiple inputs:

**Rule:** Target confidence = MIN(all source confidences) × transformation confidence

```
Example: EBITDA Calculation
  Net Income: confidence = 0.85
  Interest: confidence = 0.90
  Tax: confidence = 0.80
  D&A: confidence = 0.70
  Formula Complexity: 1.00 (simple addition)

  EBITDA confidence = MIN(0.85, 0.90, 0.80, 0.70) × 1.00 = 0.70
```

**Rationale:** The least reliable input dominates the output's reliability.

---

### 2.3 Conditional Edges (Alternative Paths)

When multiple paths exist (e.g., hierarchy-aware aggregation):

**Rule:** Only the active path contributes to confidence. Inactive paths stored for audit but not propagated.

```
Example: Revenue Aggregation
  Path A (Total Line Used): confidence = 0.95, is_active = True
  Path B (Component Sum): confidence = 0.85, is_active = False

  Effective confidence = 0.95 (only active path counts)
```

---

### 2.4 Confidence Degradation Limits

**Minimum Floor:** Confidence never drops below 0.00 (invalid/missing data)
**Maximum Cap:** Confidence cannot exceed source confidence (transformations never improve confidence)
**Degradation Rate:** Each transformation step applies 0.85 to 1.00 multiplier (5-15% loss typical)

**Expected Confidence by Stage:**

| Stage | Typical Range | Example |
|-------|--------------|---------|
| Source Cell (Excel) | 1.00 | Extracted accurately |
| Mapped Concept | 0.70 - 1.00 | Depends on mapping tier |
| Aggregated Value | 0.60 - 0.95 | Depends on strategy |
| Calculated Output (DCF) | 0.50 - 0.90 | Depends on input chain |
| Deep Calculation (LBO IRR) | 0.40 - 0.85 | Long dependency chain |

---

## 3. Hard Blocking Rules (Investment Banking Standards)

### 3.1 DCF Model Generation - BLOCKING THRESHOLDS

**CRITICAL BLOCKER (Model Refused):**
- Revenue confidence < 0.60
- EBITDA confidence < 0.60
- Net Income confidence < 0.50
- WACC confidence < 0.70
- Any critical input = 0.00 confidence (missing/invalid)

**WARNING (Model Generated with Disclaimer):**
- Revenue confidence 0.60 - 0.75
- EBITDA confidence 0.60 - 0.75
- Capex confidence < 0.60
- Working capital confidence < 0.60

**PASS (Model Delivered):**
- Revenue confidence ≥ 0.75
- EBITDA confidence ≥ 0.75
- All critical inputs ≥ 0.60

**Rationale:** DCF valuation is garbage-in/garbage-out. If revenue or profitability is uncertain, the entire valuation is unreliable. Bankers cannot present a DCF with 40% confidence revenue.

---

### 3.2 LBO Model Generation - BLOCKING THRESHOLDS

**CRITICAL BLOCKER (Model Refused):**
- EBITDA confidence < 0.65 (debt sizing depends on it)
- Debt confidence < 0.70 (capital structure is critical)
- Interest expense confidence < 0.70 (impacts returns)
- Exit EBITDA confidence < 0.60
- IRR confidence < 0.50 (too many compounding errors)

**WARNING (Model Generated with IRR Flagged as Unreliable):**
- EBITDA confidence 0.65 - 0.75
- IRR confidence 0.50 - 0.65
- Cash flow confidence 0.60 - 0.75
- Debt schedule confidence 0.60 - 0.75

**PASS (Model Delivered):**
- EBITDA confidence ≥ 0.75
- Debt confidence ≥ 0.75
- IRR confidence ≥ 0.65
- All cash flow inputs ≥ 0.70

**Rationale:** LBO models are highly leveraged - small errors in EBITDA compound through debt covenants, cash sweeps, and IRR calculations. A 0.40 confidence IRR is meaningless to a private equity investor.

---

### 3.3 Comps Analysis - BLOCKING THRESHOLDS

**CRITICAL BLOCKER (Comps Refused):**
- Revenue confidence < 0.60
- EBITDA confidence < 0.60
- Market cap confidence < 0.80 (must be accurate for multiples)
- Enterprise value confidence < 0.75
- < 3 comparable companies with confidence ≥ 0.70

**WARNING (Peer Flagged in Output):**
- Individual peer revenue confidence 0.60 - 0.75
- Individual peer EBITDA confidence 0.60 - 0.75
- Partial data (missing metrics flagged explicitly)

**PASS (Comps Delivered):**
- Revenue confidence ≥ 0.75
- EBITDA confidence ≥ 0.75
- Market cap confidence ≥ 0.85
- ≥ 3 peers with all metrics ≥ 0.70

**Rationale:** Comps trading multiples are relative - one bad data point skews the entire peer group. Missing or low-confidence metrics must be explicitly flagged, not silently substituted.

---

### 3.4 Audit Warning Escalation

**INFO (Logged Only):**
- Confidence 0.75 - 0.90
- "Standard mapping confidence - review recommended"

**WARNING (Displayed to User):**
- Confidence 0.60 - 0.75
- "Medium confidence - verify source data accuracy"
- Listed in audit report with details

**CRITICAL (Blocks Model Output):**
- Confidence < 0.60
- "Low confidence - insufficient for investment decision"
- Model generation terminated with explanation

**FATAL (System Error):**
- Confidence = 0.00
- "Missing or invalid data - cannot proceed"
- User must fix source data or add analyst brain override

---

## 4. Confidence Explanation System

Every confidence score must be explainable. Users can query:

### 4.1 Confidence Breakdown (By Node)

```
Revenue (2023): $1,250.0M
Confidence: 0.765

Breakdown:
  ├─ Mapping: 0.90 (Exact Label Match - us-gaap_Revenues)
  ├─ Aggregation: 0.85 (Component Sum - 3 revenue streams)
  └─ Final: 0.90 × 0.85 = 0.765
```

### 4.2 Confidence Trace (Full Lineage)

```
DCF Enterprise Value: $5,240M
Confidence: 0.68

Trace:
  ├─ Terminal Value: 0.68
  │   ├─ Exit EBITDA: 0.75 (Aggregation: Component Sum)
  │   │   ├─ EBITDA Projection: 0.80 (Formula: Growth Rate)
  │   │   │   └─ Historical EBITDA: 0.85 (Mapping: Exact Label)
  │   │   └─ Growth Rate: 0.95 (Assumption: Analyst Input)
  │   └─ Exit Multiple: 0.90 (Assumption: Analyst Input)
  └─ Discount Rate (WACC): 0.80 (Calculation: Multi-input)
      ├─ Cost of Equity: 0.85
      ├─ Cost of Debt: 0.90
      └─ Weights: 0.95
```

### 4.3 Confidence Report (Model-Level)

```
DCF Model Confidence Summary
============================
Overall Model Confidence: 0.71 (PASS - Above 0.60 threshold)

Critical Inputs:
  Revenue:        0.82 ✓ (PASS)
  EBITDA:         0.78 ✓ (PASS)
  Net Income:     0.75 ✓ (PASS)
  WACC:           0.80 ✓ (PASS)
  Terminal Value: 0.68 ⚠ (WARNING - Review exit assumptions)

Lowest Confidence Items:
  1. Capex (2024): 0.55 ⚠ (Keyword Match - verify accuracy)
  2. Tax Rate: 0.60 ⚠ (Desperate Recovery - check 10-K)
  3. Working Capital: 0.62 ⚠ (Component Sum with missing data)

Recommendation: Model suitable for initial discussion. Review flagged items before client delivery.
```

---

## 5. Implementation Specification

### 5.1 Data Structure Updates

**FinancialEdge (Already Exists in lineage_graph.py):**
```python
@dataclass
class FinancialEdge:
    confidence: float = 1.0  # 0.0 to 1.0
    confidence_source: str = ""  # Explanation (e.g., "Exact Label Match")
    confidence_breakdown: Dict[str, float] = field(default_factory=dict)
    # Example: {"mapping": 0.90, "aggregation": 0.85, "final": 0.765}
```

**FinancialNode (Update):**
```python
@dataclass
class FinancialNode:
    confidence: float = 1.0  # Inherited from incoming edge(s)
    confidence_explanation: str = ""  # Human-readable
```

**ModelOutput (New - for DCF/LBO/Comps):**
```python
@dataclass
class ModelOutput:
    model_type: str  # "DCF", "LBO", "COMPS"
    overall_confidence: float  # MIN of critical inputs
    critical_inputs: Dict[str, float]  # {"Revenue": 0.82, ...}
    blocking_status: str  # "PASS", "WARNING", "BLOCKED"
    blocking_reason: Optional[str]  # If blocked
    low_confidence_items: List[Dict]  # Flagged items
```

---

### 5.2 Confidence Calculation Functions

**Location:** `utils/confidence_engine.py` (new file)

**Core Functions:**

```python
def calculate_mapping_confidence(method: str, depth: int = 0) -> float:
    """Calculate confidence for a mapping operation."""

def calculate_aggregation_confidence(strategy: AggregationStrategy,
                                     has_conflicts: bool) -> float:
    """Calculate confidence for an aggregation operation."""

def calculate_recovery_confidence(attempt_num: int) -> float:
    """Calculate confidence based on iterative recovery attempt."""

def propagate_confidence(source_confidences: List[float],
                        transformation_confidence: float) -> float:
    """Propagate confidence through a transformation."""

def check_blocking_rules(model_type: str,
                        critical_inputs: Dict[str, float]) -> Tuple[str, str]:
    """Check if model should be blocked based on confidence thresholds.
    Returns: (status, reason)
    """

def generate_confidence_report(model_output: ModelOutput) -> str:
    """Generate human-readable confidence report."""
```

---

### 5.3 Integration Points

**Mapper (mapper/mapper.py):**
- Line 393-400: When Analyst Brain mapping found → confidence = 1.00
- Line 403-412: When Exact Label match → confidence = 0.90
- Line 415-424: When Keyword match → confidence = 0.70
- Line 433-444: When Hierarchy fallback → confidence = 0.70 - (depth × 0.05)
- Line 447-454: When Unmapped → confidence = 0.00

**Modeler (modeler/engine.py):**
- Line 184-191: Track attempt number for recovery confidence
- Aggregation functions: Apply aggregation confidence based on strategy
- Calculation functions: Propagate confidence through formulas

**Lineage Graph (utils/lineage_graph.py):**
- Line 139: FinancialEdge.confidence already exists ✓
- Add confidence_breakdown dict for detailed tracking
- Add confidence query methods

**Output Generation:**
- Before generating DCF/LBO/Comps CSVs, run blocking rules
- If BLOCKED: Raise ModelValidationError with explanation
- If WARNING: Generate model + append disclaimer rows
- If PASS: Generate model with confidence metadata file

---

## 6. Blocking Rule Examples (Conservative & Realistic)

### Example 1: DCF Blocked - Low Revenue Confidence

**Scenario:**
- Company uses custom revenue labels not in XBRL taxonomy
- Mapper falls back to Keyword Match (confidence = 0.70)
- Aggregation uses MAX_VALUE (multiple totals found, confidence = 0.60)
- Final revenue confidence = 0.70 × 0.60 = 0.42

**Decision:** BLOCKED
**Reason:** "Revenue confidence (0.42) below minimum threshold (0.60). Cannot generate reliable DCF valuation."
**Action Required:** User must add Analyst Brain mapping for revenue or verify source data.

---

### Example 2: LBO IRR Flagged as Unreliable

**Scenario:**
- EBITDA confidence = 0.78 (PASS)
- Debt confidence = 0.85 (PASS)
- Interest expense confidence = 0.65 (WARNING - Desperate Recovery used)
- Exit EBITDA confidence = 0.72 (PASS)
- IRR calculation: MIN(0.78, 0.85, 0.65, 0.72) × 0.80 = 0.52

**Decision:** WARNING (Model generated but IRR flagged)
**Reason:** "IRR confidence (0.52) below reliable threshold (0.65). Interest expense required Desperate Recovery."
**Output:** LBO model generated with disclaimer row:
```
"*** WARNING: IRR (23.4%) has confidence score 0.52 - verify interest expense accuracy before investment decision ***"
```

---

### Example 3: Comps Peer Excluded - Missing Data

**Scenario:**
- Peer Company A: Revenue confidence = 0.85, EBITDA confidence = 0.30 (Unmapped)
- Threshold: EBITDA confidence must be ≥ 0.60

**Decision:** WARNING (Peer included with explicit flag)
**Reason:** "Peer EBITDA confidence (0.30) below threshold. Metrics incomplete."
**Output:**
```
comps_raw_financials.csv:
Company A, Revenue, 1250.0, 0.85, "Mapped"
Company A, EBITDA, ---, 0.00, "MISSING - could not map EBITDA label"

comps_valuation_multiples.csv:
Company A, EV/Revenue, 2.5x, 0.85, "Calculated"
Company A, EV/EBITDA, ---, 0.00, "Cannot calculate - EBITDA missing"
```

---

### Example 4: Audit Warning Escalation

**Scenario:**
- Capex mapped via Hierarchy Fallback (depth=3) → confidence = 0.55
- Threshold: WARNING at 0.60 - 0.75

**Decision:** WARNING (logged and reported)
**Audit Report:**
```
MEDIUM CONFIDENCE WARNING
=========================
Item: Capex (2023)
Confidence: 0.55
Mapping Method: Hierarchy Fallback (depth=3)
Source Label: "Capital Investments - Property"
Mapped Concept: us-gaap_PaymentsToAcquirePropertyPlantAndEquipment

Recommendation: Verify that "Capital Investments - Property" represents total Capex, not a subset.
Consider adding explicit alias or Analyst Brain mapping.

Impact: DCF free cash flow calculation depends on this value.
```

---

## 7. Confidence vs. Accuracy (Important Distinction)

**Confidence ≠ Accuracy**

- **Confidence:** Our certainty that the mapping/transformation is correct
- **Accuracy:** Whether the underlying data is factually correct

**Example:**
- Analyst Brain mapping: confidence = 1.00 (we're certain this is what the analyst wants)
- But if analyst makes a mistake, accuracy could be 0%

**Implication:** Confidence scores measure **mapping reliability**, not **data quality**. Users must still verify source data accuracy.

---

## 8. Regulatory Compliance & Audit Trail

### 8.1 SOX Compliance

For public company financial reporting:
- All confidence scores logged with timestamps
- Full lineage graph persisted (immutable audit trail)
- Blocking decisions logged with rationale
- Analyst overrides require user identity + reason

### 8.2 Investment Bank Internal Audit

Standard questions auditors ask:
1. "How do you know this revenue number is correct?" → Show lineage trace
2. "What if the mapping is wrong?" → Show confidence score + alternatives considered
3. "Why did you use this aggregation method?" → Show hierarchy-aware logic
4. "What data was excluded?" → Show unmapped items report with 0.00 confidence

**FinanceX Answer:** Complete confidence framework provides deterministic, explainable answers to all audit questions.

---

## 9. Future Enhancements (Out of Scope for V1.0)

### 9.1 User Confidence Overrides
Allow analysts to manually adjust confidence scores with justification:
```
Analyst: "I verified this with the 10-K footnote. Override confidence to 1.00."
System: Logs override + reason, updates active edge
```

### 9.2 Confidence-Based Scenario Analysis
Generate optimistic/pessimistic scenarios by filtering nodes:
- Optimistic: Only use nodes with confidence ≥ 0.80
- Pessimistic: Use all nodes (include low-confidence data)

### 9.3 Time-Decay Confidence
For cached mappings, confidence degrades over time:
```
confidence = base_confidence × (1 - time_decay_factor)
Example: 3-month-old alias → 0.95 × 0.98 = 0.931
```

---

## 10. Testing & Validation

### 10.1 Unit Tests Required

**Test Suite:** `tests/test_confidence_engine.py`

Test cases:
1. Mapping confidence calculation (all tiers)
2. Aggregation confidence calculation (all strategies)
3. Recovery confidence calculation (all attempts)
4. Confidence propagation (simple, multi-input, chains)
5. Blocking rules (DCF, LBO, Comps - all thresholds)
6. Confidence explanation generation
7. Edge cases (confidence = 0.00, confidence = 1.00, mixed)

### 10.2 Integration Tests

**Test Suite:** `tests/test_confidence_integration.py`

End-to-end scenarios:
1. Clean data (all Exact Label matches) → High confidence model
2. Messy data (Keyword matches) → Medium confidence model + warnings
3. Terrible data (Hierarchy fallbacks) → Model blocked
4. Analyst Brain rescue → Confidence restored to 1.00

### 10.3 Validation Criteria

**PASS Criteria:**
- All confidence scores deterministic (same input → same output)
- All confidence scores explainable (can trace to source)
- Blocking rules prevent obviously bad models
- No silent failures (confidence = 0.00 is explicit)

---

## 11. Deployment Checklist

- [ ] Implement `utils/confidence_engine.py` with core functions
- [ ] Update `mapper/mapper.py` to assign confidence scores
- [ ] Update `modeler/engine.py` to propagate confidence through calculations
- [ ] Update `utils/lineage_graph.py` to store confidence_breakdown
- [ ] Implement blocking rules in model output generation
- [ ] Generate confidence reports for all models (DCF/LBO/Comps)
- [ ] Add confidence metadata to CSV outputs (new column or separate file)
- [ ] Write unit tests (>95% coverage for confidence_engine.py)
- [ ] Write integration tests (end-to-end scenarios)
- [ ] Update ARCHITECTURE_DETAILED.md with confidence framework
- [ ] Train users on confidence interpretation

---

## Appendix A: Confidence Score Reference Card

Quick reference for developers:

| Source | Confidence | Code Location |
|--------|-----------|---------------|
| Analyst Brain | 1.00 | mapper.py:393 |
| Explicit Alias | 0.95 | mapper.py:403 |
| Exact Label | 0.90 | mapper.py:403 |
| Keyword Match | 0.70 | mapper.py:415 |
| Hierarchy (depth=1) | 0.65 | mapper.py:433 |
| Hierarchy (depth=2) | 0.60 | mapper.py:433 |
| Hierarchy (depth=3+) | 0.50 | mapper.py:433 |
| Unmapped | 0.00 | mapper.py:447 |

| Aggregation | Confidence | Code Location |
|-------------|-----------|---------------|
| Total Line Used | 0.95 | engine.py (aggregation) |
| Component Sum | 0.85 | engine.py (aggregation) |
| Single Value | 0.90 | engine.py (aggregation) |
| Max Value | 0.60 | engine.py (aggregation) |

| Recovery Attempt | Confidence | Code Location |
|-----------------|-----------|---------------|
| Strict (Attempt 1) | 0.95 | engine.py:184 |
| Relaxed (Attempt 2) | 0.70 | engine.py:184 |
| Desperate (Attempt 3) | 0.40 | engine.py:184 |
| Failed | 0.00 | engine.py:184 |

---

## Appendix B: Blocking Threshold Summary

Quick reference for operators:

| Model | Metric | BLOCK | WARN | PASS |
|-------|--------|-------|------|------|
| DCF | Revenue | < 0.60 | 0.60-0.75 | ≥ 0.75 |
| DCF | EBITDA | < 0.60 | 0.60-0.75 | ≥ 0.75 |
| DCF | WACC | < 0.70 | 0.70-0.80 | ≥ 0.80 |
| LBO | EBITDA | < 0.65 | 0.65-0.75 | ≥ 0.75 |
| LBO | Debt | < 0.70 | 0.70-0.80 | ≥ 0.80 |
| LBO | IRR | < 0.50 | 0.50-0.65 | ≥ 0.65 |
| Comps | Revenue | < 0.60 | 0.60-0.75 | ≥ 0.75 |
| Comps | EBITDA | < 0.60 | 0.60-0.75 | ≥ 0.75 |
| Comps | Market Cap | < 0.80 | 0.80-0.85 | ≥ 0.85 |

**CRITICAL:** Any metric with confidence = 0.00 → IMMEDIATE BLOCK (missing data)

---

**END OF FRAMEWORK**

**Document Version:** 1.0
**Author:** FinanceX Engineering
**Date:** 2026-01-07
**Status:** Design Complete - Ready for Implementation

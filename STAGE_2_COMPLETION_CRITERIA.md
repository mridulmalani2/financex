# Stage 2: UI Transparency & Debugging - Completion Criteria
**Version:** 1.0
**Date:** 2026-01-08
**Status:** Definition Phase

---

## Completion Definition

**Stage 2 is COMPLETE when ALL 40 criteria below pass.**

Any single failure = Stage 2 is NOT COMPLETE.

This is **binary**: Either 40/40 pass, or Stage 2 is incomplete.

---

## Prerequisites

**Stage 2 can only begin after Stage 1 is COMPLETE.**

Verify Stage 1:
```bash
python3 verify_stage_1_complete.py
# Must return: "✅ STAGE 1 COMPLETE - ALL 50 CRITERIA PASSED"
```

---

## Overview

Stage 2 exposes the infrastructure built in Stage 1 (confidence scores, lineage graph, audit trail) to end users through transparent, debuggable UI components.

**Core Philosophy:**
- **Transparency**: Users can see exactly how every number was calculated
- **Debuggability**: Users can trace any value back to its source
- **Actionability**: Users can identify and fix data quality issues
- **Trust**: Confidence scores guide decision-making

---

## Section A: Confidence Visualization (8 Criteria)

Users must be able to see and understand confidence scores throughout the UI.

### A1. Confidence Display Infrastructure
- [ ] **A1.1** `utils/confidence_display.py` exists with confidence color mapping functions
- [ ] **A1.2** Function `get_confidence_color(score: float) -> str` returns appropriate color
- [ ] **A1.3** Function `get_confidence_badge(score: float) -> str` returns HTML/Markdown badge
- [ ] **A1.4** Function `format_confidence_tooltip(score: float, breakdown: dict) -> str` generates tooltip

### A2. UI Integration
- [ ] **A2.1** All financial values in app.py display confidence badges/colors
- [ ] **A2.2** DCF model display shows confidence for Revenue, EBITDA, Net Income, FCF
- [ ] **A2.3** LBO model display shows confidence for EBITDA, Debt, Leverage Ratio
- [ ] **A2.4** Comps model display shows confidence for Revenue, EBITDA, Margins, EPS

**Verification:**
```bash
pytest tests/test_confidence_display.py::test_confidence_visualization -v
```

**Color Scheme:**
- 1.00 (Analyst Brain): 🟢 Green
- 0.90-0.99 (Exact/Alias): 🟢 Green
- 0.70-0.89 (Keyword): 🟡 Yellow
- 0.40-0.69 (Partial): 🟠 Orange
- 0.00-0.39 (Low/Unmapped): 🔴 Red

---

## Section B: "Why This Number?" Modal (10 Criteria)

Users must be able to click any financial value and see complete lineage.

### B1. Backend Infrastructure
- [ ] **B1.1** `utils/lineage_explainer.py` exists with lineage query functions
- [ ] **B1.2** Function `explain_value(node_id: str, graph: LineageGraph) -> dict` returns explanation
- [ ] **B1.3** Function `get_lineage_path(node_id: str, graph: LineageGraph) -> List[dict]` returns path
- [ ] **B1.4** Function `format_lineage_markdown(path: List[dict]) -> str` generates markdown

### B2. UI Modal Component
- [ ] **B2.1** Modal displays when user clicks "🔍 Why?" button next to any metric
- [ ] **B2.2** Modal shows complete path from Excel source to final value
- [ ] **B2.3** Modal shows all intermediate transformations (mapping, aggregation, calculation)
- [ ] **B2.4** Modal shows confidence score at each step
- [ ] **B2.5** Modal shows alternative paths that were considered but not taken
- [ ] **B2.6** Modal has "Export Lineage" button to download as JSON

**Verification:**
```bash
pytest tests/test_lineage_explainer.py::test_why_this_number_modal -v
```

**Modal Structure:**
```
🔍 Why is Revenue = $1,500,000 (Confidence: 0.95)?

📊 Lineage Path:
  1. Excel Source → "Total Net Sales" ($1,500,000) [Income Statement, 2024]
  2. Mapping → us-gaap_Revenues (Confidence: 0.95, Method: Exact Label Match)
  3. Aggregation → Revenue bucket (Strategy: MAX of duplicates)
  4. Calculation → DCF Revenue row (Formula: Direct mapping)

🎯 Confidence Breakdown:
  - Source Data: 1.00 (Extracted from Excel)
  - Mapping: 0.95 (Exact Label Match)
  - Aggregation: 0.95 (MIN propagation)
  - Final: 0.95

⚠️ Alternatives Considered:
  - "Sales Revenue" also mapped to us-gaap_Revenues (not used - hierarchy detected)

[📥 Export Lineage JSON]  [✖️ Close]
```

---

## Section C: Interactive Lineage Graph Explorer (8 Criteria)

Users must be able to visualize the complete data flow.

### C1. Visualization Backend
- [ ] **C1.1** `utils/graph_visualizer.py` exists with graph rendering functions
- [ ] **C1.2** Function `generate_graph_html(graph: LineageGraph) -> str` creates interactive HTML
- [ ] **C1.3** Function `graph_to_mermaid(graph: LineageGraph) -> str` generates Mermaid diagram
- [ ] **C1.4** Graph visualization shows all node types with distinct icons/colors

### C2. UI Integration
- [ ] **C2.1** "Lineage Graph" tab exists in main UI
- [ ] **C2.2** Graph displays all nodes: SOURCE_CELL → EXTRACTED → MAPPED → AGGREGATED → CALCULATED
- [ ] **C2.3** Graph edges show transformation methods on hover
- [ ] **C2.4** Clicking a node shows detailed information in sidebar

**Verification:**
```bash
pytest tests/test_graph_visualizer.py::test_graph_rendering -v
```

**Visual Requirements:**
- Nodes: Different colors/shapes for each NodeType
- Edges: Labeled with transformation method
- Interactive: Click to see details, zoom, pan
- Export: Download as PNG, SVG, or Mermaid

---

## Section D: Enhanced Audit Trail Display (6 Criteria)

Users must see comprehensive audit information for all models.

### D1. Audit Display Module
- [ ] **D1.1** `utils/audit_display.py` exists with audit formatting functions
- [ ] **D1.2** Function `format_audit_summary(audit_log: List[AuditEntry]) -> str` generates summary
- [ ] **D1.3** Function `format_mapping_audit(mappings: List[dict]) -> str` shows mapping decisions

### D2. UI Integration
- [ ] **D2.1** "Audit Trail" tab shows all mapping decisions with methods
- [ ] **D2.2** Audit trail shows all aggregation strategies used
- [ ] **D2.3** Audit trail shows all calculation formulas

**Verification:**
```bash
pytest tests/test_audit_display.py::test_audit_formatting -v
```

**Audit Trail Structure:**
```
📋 Audit Trail - Processing Summary

Mapping Decisions (43 items):
  ✅ "Total Revenue" → us-gaap_Revenues (Exact Label Match, Confidence: 0.95)
  ✅ "COGS" → us-gaap_CostOfRevenue (Alias, Confidence: 0.95)
  🟡 "Admin Expenses" → us-gaap_GeneralAndAdministrativeExpense (Keyword, Confidence: 0.70)
  ❌ "Custom Metric XYZ" → Unmapped (Confidence: 0.00)

Aggregation Strategies (12 buckets):
  📊 Revenue: MAX (detected hierarchy - used total line)
  📊 COGS: SUM (no duplicates detected)
  📊 SG&A: SUM (3 components aggregated)

Calculation Formulas (25 metrics):
  🧮 Gross Profit = Revenue - COGS
  🧮 EBITDA = Gross Profit - SG&A - R&D - Other OpEx
  🧮 NOPAT = EBIT × (1 - Tax Rate)
```

---

## Section E: Data Quality Dashboard (8 Criteria)

Users must see aggregate data quality metrics.

### E1. Dashboard Backend
- [ ] **E1.1** `utils/data_quality.py` exists with quality calculation functions
- [ ] **E1.2** Function `calculate_mapping_coverage(graph: LineageGraph) -> float` returns %
- [ ] **E1.3** Function `calculate_avg_confidence(graph: LineageGraph) -> float` returns average
- [ ] **E1.4** Function `identify_low_confidence_areas(graph: LineageGraph) -> List[dict]` finds issues

### E2. Dashboard UI
- [ ] **E2.1** "Data Quality" tab displays overall health score (0-100)
- [ ] **E2.2** Dashboard shows mapping coverage % (valid/total)
- [ ] **E2.3** Dashboard shows average confidence by model (DCF, LBO, Comps)
- [ ] **E2.4** Dashboard lists top 5 low-confidence metrics with recommendations

**Verification:**
```bash
pytest tests/test_data_quality.py::test_quality_metrics -v
```

**Dashboard Structure:**
```
📊 Data Quality Dashboard

Overall Health: 92/100 🟢 Excellent

Mapping Coverage:
  ✅ Mapped: 43/45 items (95.6%)
  ❌ Unmapped: 2/45 items (4.4%)

Average Confidence by Model:
  📈 DCF: 0.87 (Good) 🟡
  💰 LBO: 0.91 (Excellent) 🟢
  📊 Comps: 0.84 (Good) 🟡

⚠️ Low Confidence Areas:
  1. Depreciation & Amortization: 0.65 (Keyword match - consider adding to Analyst Brain)
  2. Interest Expense: 0.70 (Partial match - verify mapping)
  3. Preferred Stock: 0.00 (Unmapped - not found in source data)

💡 Recommendations:
  - Add 3 custom mappings to Analyst Brain to reach 98% confidence
  - Verify "Interest Expense" mapping (currently using keyword match)
  - Source data missing "Preferred Stock" - confirm with data provider
```

---

## Section F: Integration Tests (10 Criteria)

All Stage 2 features must work together end-to-end.

### F1. Confidence Display Integration
- [ ] **F1.1** Upload valid Excel → All models display with confidence colors
- [ ] **F1.2** Low confidence values show in orange/red, high confidence in green
- [ ] **F1.3** Hovering over confidence badge shows tooltip with breakdown

### F2. Modal Integration
- [ ] **F2.1** Click "Why?" on any metric → Modal opens with complete lineage
- [ ] **F2.2** Modal shows Excel source cell location
- [ ] **F2.3** Export lineage JSON → Valid JSON downloads

### F3. Graph Explorer Integration
- [ ] **F3.1** Lineage Graph tab renders without errors
- [ ] **F3.2** Graph shows complete flow from Excel to final models
- [ ] **F3.3** Clicking graph node displays details

### F4. End-to-End Transparency
- [ ] **F4.1** User can trace ANY value from UI back to Excel source cell

**Verification:**
```bash
pytest tests/test_stage_2_integration.py -v
```

---

## Verification Script

**File:** `verify_stage_2_complete.py`

```python
#!/usr/bin/env python3
"""
Stage 2 Completion Verification Script
Runs all 40 criteria checks and produces binary COMPLETE/INCOMPLETE result.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_artifacts():
    """Section A-E: Verify all mandatory files exist."""
    print("\n[A-E] Checking Stage 2 Artifacts...")
    files = [
        ('utils/confidence_display.py', 100),
        ('utils/lineage_explainer.py', 150),
        ('utils/graph_visualizer.py', 200),
        ('utils/audit_display.py', 100),
        ('utils/data_quality.py', 150),
        ('tests/test_confidence_display.py', 0),
        ('tests/test_lineage_explainer.py', 0),
        ('tests/test_graph_visualizer.py', 0),
        ('tests/test_audit_display.py', 0),
        ('tests/test_data_quality.py', 0),
        ('tests/test_stage_2_integration.py', 0),
    ]

    passed = 0
    failed = 0

    for filepath, min_lines in files:
        if not os.path.exists(filepath):
            print(f"  ❌ {filepath} does not exist")
            failed += 1
        elif min_lines > 0:
            with open(filepath) as f:
                lines = len(f.readlines())
            if lines >= min_lines:
                print(f"  ✅ {filepath} ({lines} lines)")
                passed += 1
            else:
                print(f"  ❌ {filepath} has {lines} lines, need {min_lines}")
                failed += 1
        else:
            print(f"  ✅ {filepath}")
            passed += 1

    return passed, failed

def run_tests(test_file):
    """Run pytest on specified test file."""
    cmd = ['pytest', test_file, '-v', '--tb=short']
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Parse pytest output for pass/fail counts
    output = result.stdout + result.stderr
    lines = output.split('\n')

    passed = 0
    failed = 0

    for line in lines:
        if ' PASSED' in line:
            passed += 1
        elif ' FAILED' in line or ' ERROR' in line:
            failed += 1

    return passed, failed, output

def main():
    print("="*70)
    print("STAGE 2: UI TRANSPARENCY & DEBUGGING - COMPLETION VERIFICATION")
    print("="*70)

    # Verify Stage 1 is complete first
    print("\n[Prerequisite] Verifying Stage 1 is complete...")
    result = subprocess.run(['python3', 'verify_stage_1_complete.py'],
                          capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Stage 1 must be complete before Stage 2")
        print("Run: python3 verify_stage_1_complete.py")
        return 1
    print("✅ Stage 1 verified complete")

    total_passed = 0
    total_failed = 0

    # Section A-E: Artifacts
    passed, failed = check_artifacts()
    total_passed += passed
    total_failed += failed
    print(f"  Sections A-E: {passed} passed, {failed} failed")

    # Section A: Confidence Display Tests
    if os.path.exists('tests/test_confidence_display.py'):
        print("\n[A] Running Confidence Display Tests...")
        passed, failed, output = run_tests('tests/test_confidence_display.py')
        total_passed += passed
        total_failed += failed
        print(f"  Section A: {passed} passed, {failed} failed")
        if failed > 0:
            print(f"\n  Failed tests:\n{output}")
    else:
        print("\n[A] ⚠️  Skipping - test_confidence_display.py not found")
        total_failed += 4

    # Section B: Lineage Explainer Tests
    if os.path.exists('tests/test_lineage_explainer.py'):
        print("\n[B] Running Lineage Explainer Tests...")
        passed, failed, output = run_tests('tests/test_lineage_explainer.py')
        total_passed += passed
        total_failed += failed
        print(f"  Section B: {passed} passed, {failed} failed")
        if failed > 0:
            print(f"\n  Failed tests:\n{output}")
    else:
        print("\n[B] ⚠️  Skipping - test_lineage_explainer.py not found")
        total_failed += 6

    # Section C: Graph Visualizer Tests
    if os.path.exists('tests/test_graph_visualizer.py'):
        print("\n[C] Running Graph Visualizer Tests...")
        passed, failed, output = run_tests('tests/test_graph_visualizer.py')
        total_passed += passed
        total_failed += failed
        print(f"  Section C: {passed} passed, {failed} failed")
        if failed > 0:
            print(f"\n  Failed tests:\n{output}")
    else:
        print("\n[C] ⚠️  Skipping - test_graph_visualizer.py not found")
        total_failed += 4

    # Section D: Audit Display Tests
    if os.path.exists('tests/test_audit_display.py'):
        print("\n[D] Running Audit Display Tests...")
        passed, failed, output = run_tests('tests/test_audit_display.py')
        total_passed += passed
        total_failed += failed
        print(f"  Section D: {passed} passed, {failed} failed")
        if failed > 0:
            print(f"\n  Failed tests:\n{output}")
    else:
        print("\n[D] ⚠️  Skipping - test_audit_display.py not found")
        total_failed += 3

    # Section E: Data Quality Tests
    if os.path.exists('tests/test_data_quality.py'):
        print("\n[E] Running Data Quality Tests...")
        passed, failed, output = run_tests('tests/test_data_quality.py')
        total_passed += passed
        total_failed += failed
        print(f"  Section E: {passed} passed, {failed} failed")
        if failed > 0:
            print(f"\n  Failed tests:\n{output}")
    else:
        print("\n[E] ⚠️  Skipping - test_data_quality.py not found")
        total_failed += 4

    # Section F: Integration Tests
    if os.path.exists('tests/test_stage_2_integration.py'):
        print("\n[F] Running Stage 2 Integration Tests...")
        passed, failed, output = run_tests('tests/test_stage_2_integration.py')
        total_passed += passed
        total_failed += failed
        print(f"  Section F: {passed} passed, {failed} failed")
        if failed > 0:
            print(f"\n  Failed tests:\n{output}")
    else:
        print("\n[F] ⚠️  Skipping - test_stage_2_integration.py not found")
        total_failed += 10

    # Final Result
    print("\n" + "="*70)
    print("FINAL RESULT")
    print("="*70)
    print(f"Total Passed: {total_passed}/40")
    print(f"Total Failed: {total_failed}/40")

    if total_failed == 0 and total_passed >= 40:
        print("\n🎉 ✅ STAGE 2 COMPLETE - ALL 40 CRITERIA PASSED")
        print("\nYou may proceed to Stage 3 (if defined).")
        return 0
    else:
        print("\n❌ STAGE 2 INCOMPLETE")
        print(f"\nRemaining failures: {total_failed}")
        print("Fix all failures before proceeding.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

---

## What This Ensures

### ✅ Transparency
- Every value shows confidence score
- Every value traceable to source
- All decisions visible and auditable

### ✅ Debuggability
- Users can see exactly how numbers were calculated
- Alternative paths shown for comparison
- Complete audit trail available

### ✅ Actionability
- Data quality dashboard identifies issues
- Recommendations provided for improvement
- Users can prioritize fixes by impact

### ✅ Trust
- Confidence scores guide decision-making
- Low confidence values clearly marked
- Users understand data quality

---

## Enforcement

**No work proceeds beyond Stage 2 until:**

1. `verify_stage_2_complete.py` returns exit code 0
2. All 40/40 criteria pass
3. Verification script output is committed to repo as `STAGE_2_VERIFICATION_REPORT.txt`

**To commit Stage 2 as complete:**
```bash
# Run verification
python3 verify_stage_2_complete.py > STAGE_2_VERIFICATION_REPORT.txt

# Check exit code
if [ $? -eq 0 ]; then
    echo "Stage 2 verification passed"
    git add STAGE_2_VERIFICATION_REPORT.txt
    git commit -m "Certify Stage 2 UI Transparency & Debugging as COMPLETE"
else
    echo "Stage 2 verification failed - do not proceed"
    exit 1
fi
```

---

## Summary

**Stage 2 is COMPLETE** means:

1. ✅ All 11 mandatory files exist with required content
2. ✅ Confidence visualization works throughout UI
3. ✅ "Why This Number?" modal traces any value to source
4. ✅ Interactive lineage graph explorer functional
5. ✅ Enhanced audit trail displays all decisions
6. ✅ Data quality dashboard provides actionable insights
7. ✅ All 40+ integration tests pass
8. ✅ `verify_stage_2_complete.py` exits with code 0

**Stage 2 is INCOMPLETE** if even ONE criterion fails.

**Binary. Testable. Builds on Stage 1.**

---

**End of Stage 2 Completion Criteria**

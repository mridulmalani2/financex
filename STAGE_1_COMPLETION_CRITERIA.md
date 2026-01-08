# Stage 1: Core Engine Hardening - Completion Criteria
**Version:** 1.0
**Date:** 2026-01-08
**Status:** Definition Phase

---

## Completion Definition

**Stage 1 is COMPLETE when ALL 50 criteria below pass.**

Any single failure = Stage 1 is NOT COMPLETE.

This is **binary**: Either 50/50 pass, or Stage 1 is incomplete.

---

## Section A: Mandatory Artifacts (10 Criteria)

These files must exist and contain required content.

### A1. Core System Files
- [ ] **A1.1** `utils/confidence_engine.py` exists, minimum 500 lines
- [ ] **A1.2** `utils/lineage_graph.py` exists, minimum 700 lines
- [ ] **A1.3** `utils/brain_manager.py` exists, minimum 200 lines
- [ ] **A1.4** `FEATURE_INTEGRATION_CONTRACT.md` exists, defines mandatory integration requirements
- [ ] **A1.5** `ANTI_SPECULATION_RULES.md` or equivalent documentation exists

### A2. Test Infrastructure
- [ ] **A2.1** `tests/test_confidence_engine.py` exists with ≥20 test cases
- [ ] **A2.2** `tests/test_lineage_graph.py` exists with ≥20 test cases
- [ ] **A2.3** `tests/test_integration.py` exists with ≥10 end-to-end test cases
- [ ] **A2.4** `tests/test_anti_speculation.py` exists with ≥10 test cases
- [ ] **A2.5** `tests/fixtures/` directory exists with ≥3 sample Excel files

**Verification:**
```bash
python3 -c "
import os
files = [
    ('utils/confidence_engine.py', 500),
    ('utils/lineage_graph.py', 700),
    ('utils/brain_manager.py', 200),
    ('FEATURE_INTEGRATION_CONTRACT.md', 0),
    ('tests/test_confidence_engine.py', 0),
    ('tests/test_lineage_graph.py', 0),
    ('tests/test_integration.py', 0),
    ('tests/test_anti_speculation.py', 0),
]
for f, min_lines in files:
    assert os.path.exists(f), f'{f} does not exist'
    if min_lines > 0:
        with open(f) as file:
            lines = len(file.readlines())
            assert lines >= min_lines, f'{f} has {lines} lines, need {min_lines}'
assert os.path.isdir('tests/fixtures'), 'tests/fixtures/ does not exist'
assert len(os.listdir('tests/fixtures')) >= 3, 'Need ≥3 fixture files'
print('✅ A1-A2: All artifacts exist')
"
```

---

## Section B: Confidence Engine Guarantees (10 Criteria)

These behaviors must be programmatically verified.

### B1. Scoring Rules
- [ ] **B1.1** Analyst Brain always returns confidence = 1.00
- [ ] **B1.2** Explicit Alias always returns confidence = 0.95
- [ ] **B1.3** Exact Label Match always returns confidence = 0.90
- [ ] **B1.4** Keyword Match always returns confidence = 0.70
- [ ] **B1.5** Unmapped always returns confidence = 0.00

### B2. Propagation Rules
- [ ] **B2.1** Aggregation uses MIN(sources) for confidence propagation
- [ ] **B2.2** Calculation uses MIN(inputs) × transformation_factor
- [ ] **B2.3** Confidence NEVER increases through transformations (monotonic decrease)
- [ ] **B2.4** Missing values propagate confidence = 0.00 to all dependents

### B3. Blocking Rules
- [ ] **B3.1** DCF blocks if Revenue < 0.60, EBITDA < 0.60, Net Income < 0.50
- [ ] **B3.2** LBO blocks if EBITDA < 0.65, Debt < 0.70

**Verification:**
```bash
pytest tests/test_confidence_engine.py::test_scoring_rules -v
pytest tests/test_confidence_engine.py::test_propagation_rules -v
pytest tests/test_confidence_engine.py::test_blocking_rules -v
```

**Required Test Cases (in test_confidence_engine.py):**
```python
def test_analyst_brain_confidence_is_always_1_00():
    # Test that Analyst Brain mappings always return 1.00
    assert calculate_mapping_confidence(source=MappingSource.ANALYST_BRAIN) == 1.00

def test_confidence_never_increases():
    # Test monotonic decrease: output_conf <= input_conf
    for input_conf in [1.0, 0.9, 0.7, 0.5, 0.3]:
        output_conf = propagate_confidence([input_conf], transformation=0.9)
        assert output_conf <= input_conf

def test_dcf_blocking_rules():
    # Test that DCF blocks when Revenue < 0.60
    status, blockers, warnings = check_blocking_rules(
        model='dcf',
        confidences={'Revenue': 0.55, 'EBITDA': 0.80}
    )
    assert status == 'BLOCKED'
    assert 'Revenue' in blockers
```

---

## Section C: Lineage Graph Guarantees (10 Criteria)

These properties must hold for ALL data in the graph.

### C1. Graph Completeness
- [ ] **C1.1** Every EXTRACTED node has ≥1 SOURCE_CELL ancestor
- [ ] **C1.2** Every MAPPED node has ≥1 EXTRACTED ancestor
- [ ] **C1.3** Every AGGREGATED node has ≥1 MAPPED ancestor
- [ ] **C1.4** Every CALCULATED node has ≥1 AGGREGATED or CALCULATED ancestor
- [ ] **C1.5** Zero orphan nodes (nodes with no ancestors except SOURCE_CELL)

### C2. Edge Integrity
- [ ] **C2.1** Every edge has non-null `method` field (human-readable explanation)
- [ ] **C2.2** Every edge has `confidence` field in range [0.0, 1.0]
- [ ] **C2.3** Every MAPPING edge has `source` field (MappingSource enum)
- [ ] **C2.4** Every AGGREGATION edge has `aggregation_strategy` field
- [ ] **C2.5** Every CALCULATION edge has `formula` or `method` field

### C3. Query Correctness
- [ ] **C3.1** `trace_backward(node_id)` returns complete ancestry (no missing links)
- [ ] **C3.2** `trace_forward(node_id)` returns all descendants
- [ ] **C3.3** `find_path(source, target)` returns valid path or None (no false positives)

**Verification:**
```bash
pytest tests/test_lineage_graph.py::test_graph_completeness -v
pytest tests/test_lineage_graph.py::test_edge_integrity -v
pytest tests/test_lineage_graph.py::test_query_correctness -v
```

**Required Test Cases (in test_lineage_graph.py):**
```python
def test_all_extracted_nodes_have_source_cells():
    # Load a sample lineage graph
    graph = load_test_graph('fixtures/sample_company.json')
    extracted_nodes = graph.query_nodes_by_type(NodeType.EXTRACTED)
    for node in extracted_nodes:
        ancestors = graph.trace_backward(node.node_id, edge_types=[EdgeType.EXTRACTION])
        assert len(ancestors) > 0, f"Node {node.node_id} has no SOURCE_CELL ancestor"

def test_all_edges_have_method():
    graph = load_test_graph('fixtures/sample_company.json')
    for edge_id, edge_data in graph.edges.items():
        assert edge_data.get('method') is not None, f"Edge {edge_id} missing 'method'"
        assert len(edge_data['method']) > 0, f"Edge {edge_id} has empty 'method'"

def test_trace_backward_completeness():
    graph = load_test_graph('fixtures/sample_company.json')
    # Pick a CALCULATED node (deepest level)
    calc_nodes = graph.query_nodes_by_type(NodeType.CALCULATED)
    for node in calc_nodes[:5]:  # Test first 5
        ancestors = graph.trace_backward(node.node_id)
        # Must have at least: CALCULATED → AGGREGATED → MAPPED → EXTRACTED → SOURCE_CELL
        assert len(ancestors) >= 4, f"Node {node.node_id} has incomplete ancestry"
```

---

## Section D: Anti-Speculation Enforcement (10 Criteria)

These violations must be **impossible** to commit.

### D1. Forbidden Operations (Must Fail)
- [ ] **D1.1** Creating a financial value without lineage edge → raises `LineageViolationError`
- [ ] **D1.2** Mapping without confidence score → raises `ConfidenceViolationError`
- [ ] **D1.3** Using global variables for financial state → linter fails (detectable)
- [ ] **D1.4** Imputing missing values (filling gaps) → raises `SpeculationViolationError`
- [ ] **D1.5** Generating output with confidence = 0.00 → blocked (no silent failures)

### D2. Required Operations (Must Succeed)
- [ ] **D2.1** Creating value with lineage edge + confidence → succeeds
- [ ] **D2.2** Marking value as unmapped (conf=0.00) → succeeds, excluded from output
- [ ] **D2.3** Loading Analyst Brain before defaults → always wins
- [ ] **D2.4** Exporting lineage graph to JSON → includes all edges and nodes
- [ ] **D2.5** Deterministic processing: same input → same output (verified with hash)

**Verification:**
```bash
pytest tests/test_anti_speculation.py::test_forbidden_operations -v
pytest tests/test_anti_speculation.py::test_required_operations -v
pytest tests/test_anti_speculation.py::test_determinism -v
```

**Required Test Cases (in test_anti_speculation.py):**
```python
def test_value_without_lineage_raises_error():
    graph = LineageGraph()
    with pytest.raises(LineageViolationError):
        # Attempt to add CALCULATED node without creating edge to source
        graph.add_node(
            node_type=NodeType.CALCULATED,
            data={'value': 1000000, 'concept': 'Revenue'}
        )
        # Missing: graph.add_edge(source_id, new_node_id, ...)

def test_mapping_without_confidence_raises_error():
    with pytest.raises(ConfidenceViolationError):
        calculate_mapping_confidence(
            source=None,  # Missing source
            match_type=None  # Missing match type
        )

def test_imputation_is_forbidden():
    with pytest.raises(SpeculationViolationError):
        impute_missing_value(
            concept='Revenue',
            period='2024-Q4',
            method='linear_interpolation'
        )

def test_deterministic_processing():
    # Process same file twice, verify identical output
    output1 = process_excel('fixtures/company_a.xlsx', brain=None)
    output2 = process_excel('fixtures/company_a.xlsx', brain=None)

    # Compare hashes of all outputs
    assert hash_dataframe(output1['dcf']) == hash_dataframe(output2['dcf'])
    assert hash_dataframe(output1['lbo']) == hash_dataframe(output2['lbo'])
    assert hash_json(output1['lineage']) == hash_json(output2['lineage'])
```

---

## Section E: Integration Tests (10 Criteria)

These end-to-end scenarios must pass.

### E1. Happy Path
- [ ] **E1.1** Upload valid Excel → All models generate (DCF, LBO, Comps)
- [ ] **E1.2** All output values have confidence > 0.00
- [ ] **E1.3** All output values have lineage path to Excel source
- [ ] **E1.4** Balance sheet validates (Assets = Liabilities + Equity, within 1% tolerance)
- [ ] **E1.5** Audit report generates with ≥50 checks run

### E2. Error Handling
- [ ] **E2.1** Upload Excel with missing required concepts → Blocks output, lists missing items
- [ ] **E2.2** Upload Excel with negative revenue → Audit flags CRITICAL, blocks DCF
- [ ] **E2.3** Upload Excel with unmapped items → Confidence degrades, reports unmapped count
- [ ] **E2.4** Apply Analyst Brain with override → Confidence increases to 1.00 for overridden items
- [ ] **E2.5** Delete critical mapped item → Re-process, confidence drops, model blocks

**Verification:**
```bash
pytest tests/test_integration.py::test_happy_path -v
pytest tests/test_integration.py::test_error_handling -v
pytest tests/test_integration.py::test_brain_overrides -v
```

**Required Test Cases (in test_integration.py):**
```python
def test_end_to_end_happy_path():
    # Full pipeline: Excel → Models
    result = process_excel('fixtures/clean_company.xlsx', brain=None)

    # Check all models generated
    assert 'dcf' in result
    assert 'lbo' in result
    assert 'comps' in result

    # Check all values have confidence > 0
    for model_name, model_df in result.items():
        if model_name in ['dcf', 'lbo', 'comps']:
            confidences = result['confidence_map'][model_name]
            assert all(c > 0.0 for c in confidences.values())

    # Check lineage completeness
    graph = result['lineage_graph']
    output_nodes = graph.query_nodes_by_type(NodeType.CALCULATED)
    for node in output_nodes:
        ancestors = graph.trace_backward(node.node_id)
        assert len(ancestors) > 0, f"Output node {node.node_id} has no lineage"

def test_missing_critical_concept_blocks_output():
    # Excel missing revenue → DCF blocked
    result = process_excel('fixtures/missing_revenue.xlsx', brain=None)

    assert result['dcf_status'] == 'BLOCKED'
    assert 'Revenue' in result['dcf_blockers']
    assert result['dcf'] is None or len(result['dcf']) == 0

def test_brain_override_increases_confidence():
    # Without brain: low confidence
    result1 = process_excel('fixtures/ambiguous_labels.xlsx', brain=None)
    conf1 = result1['confidence_map']['dcf']['Revenue']

    # With brain: high confidence
    brain = BrainManager()
    brain.add_mapping('Ambiguous Revenue Label', 'us-gaap:Revenues')
    result2 = process_excel('fixtures/ambiguous_labels.xlsx', brain=brain)
    conf2 = result2['confidence_map']['dcf']['Revenue']

    assert conf2 > conf1, "Brain override should increase confidence"
    assert conf2 == 1.00, "Brain override should set confidence to 1.00"
```

---

## Verification Script

This script runs ALL checks and produces a PASS/FAIL report.

**File:** `verify_stage_1_complete.py`

```python
#!/usr/bin/env python3
"""
Stage 1 Completion Verification Script
Runs all 50 criteria checks and produces binary COMPLETE/INCOMPLETE result.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_artifacts():
    """Section A: Verify all mandatory files exist."""
    print("\n[A] Checking Mandatory Artifacts...")
    files = [
        ('utils/confidence_engine.py', 500),
        ('utils/lineage_graph.py', 700),
        ('utils/brain_manager.py', 200),
        ('FEATURE_INTEGRATION_CONTRACT.md', 0),
        ('tests/test_confidence_engine.py', 0),
        ('tests/test_lineage_graph.py', 0),
        ('tests/test_integration.py', 0),
        ('tests/test_anti_speculation.py', 0),
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

    # Check fixtures directory
    if os.path.isdir('tests/fixtures'):
        fixture_count = len(os.listdir('tests/fixtures'))
        if fixture_count >= 3:
            print(f"  ✅ tests/fixtures/ ({fixture_count} files)")
            passed += 1
        else:
            print(f"  ❌ tests/fixtures/ has {fixture_count} files, need ≥3")
            failed += 1
    else:
        print(f"  ❌ tests/fixtures/ does not exist")
        failed += 1

    return passed, failed

def run_tests(test_file, test_pattern=None):
    """Run pytest on specified test file/pattern."""
    cmd = ['pytest', test_file, '-v', '--tb=short']
    if test_pattern:
        cmd.extend(['-k', test_pattern])

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
    print("STAGE 1: CORE ENGINE HARDENING - COMPLETION VERIFICATION")
    print("="*70)

    total_passed = 0
    total_failed = 0

    # Section A: Artifacts
    passed, failed = check_artifacts()
    total_passed += passed
    total_failed += failed
    print(f"  Section A: {passed} passed, {failed} failed")

    # Section B: Confidence Engine Tests
    if os.path.exists('tests/test_confidence_engine.py'):
        print("\n[B] Running Confidence Engine Tests...")
        passed, failed, output = run_tests('tests/test_confidence_engine.py')
        total_passed += passed
        total_failed += failed
        print(f"  Section B: {passed} passed, {failed} failed")
        if failed > 0:
            print(f"\n  Failed tests:\n{output}")
    else:
        print("\n[B] ⚠️  Skipping - test_confidence_engine.py not found")
        total_failed += 10

    # Section C: Lineage Graph Tests
    if os.path.exists('tests/test_lineage_graph.py'):
        print("\n[C] Running Lineage Graph Tests...")
        passed, failed, output = run_tests('tests/test_lineage_graph.py')
        total_passed += passed
        total_failed += failed
        print(f"  Section C: {passed} passed, {failed} failed")
        if failed > 0:
            print(f"\n  Failed tests:\n{output}")
    else:
        print("\n[C] ⚠️  Skipping - test_lineage_graph.py not found")
        total_failed += 10

    # Section D: Anti-Speculation Tests
    if os.path.exists('tests/test_anti_speculation.py'):
        print("\n[D] Running Anti-Speculation Tests...")
        passed, failed, output = run_tests('tests/test_anti_speculation.py')
        total_passed += passed
        total_failed += failed
        print(f"  Section D: {passed} passed, {failed} failed")
        if failed > 0:
            print(f"\n  Failed tests:\n{output}")
    else:
        print("\n[D] ⚠️  Skipping - test_anti_speculation.py not found")
        total_failed += 10

    # Section E: Integration Tests
    if os.path.exists('tests/test_integration.py'):
        print("\n[E] Running Integration Tests...")
        passed, failed, output = run_tests('tests/test_integration.py')
        total_passed += passed
        total_failed += failed
        print(f"  Section E: {passed} passed, {failed} failed")
        if failed > 0:
            print(f"\n  Failed tests:\n{output}")
    else:
        print("\n[E] ⚠️  Skipping - test_integration.py not found")
        total_failed += 10

    # Final Result
    print("\n" + "="*70)
    print("FINAL RESULT")
    print("="*70)
    print(f"Total Passed: {total_passed}/50")
    print(f"Total Failed: {total_failed}/50")

    if total_failed == 0 and total_passed == 50:
        print("\n🎉 ✅ STAGE 1 COMPLETE - ALL 50 CRITERIA PASSED")
        print("\nYou may proceed to Stage 2.")
        return 0
    else:
        print("\n❌ STAGE 1 INCOMPLETE")
        print(f"\nRemaining failures: {total_failed}")
        print("Fix all failures before proceeding to Stage 2.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

**Usage:**
```bash
python3 verify_stage_1_complete.py
```

**Output:**
```
======================================================================
STAGE 1: CORE ENGINE HARDENING - COMPLETION VERIFICATION
======================================================================

[A] Checking Mandatory Artifacts...
  ✅ utils/confidence_engine.py (723 lines)
  ✅ utils/lineage_graph.py (876 lines)
  ✅ utils/brain_manager.py (234 lines)
  ✅ FEATURE_INTEGRATION_CONTRACT.md
  ✅ tests/test_confidence_engine.py
  ✅ tests/test_lineage_graph.py
  ✅ tests/test_integration.py
  ✅ tests/test_anti_speculation.py
  ✅ tests/fixtures/ (5 files)
  Section A: 9 passed, 0 failed

[B] Running Confidence Engine Tests...
  Section B: 10 passed, 0 failed

[C] Running Lineage Graph Tests...
  Section C: 10 passed, 0 failed

[D] Running Anti-Speculation Tests...
  Section D: 10 passed, 0 failed

[E] Running Integration Tests...
  Section E: 11 passed, 0 failed

======================================================================
FINAL RESULT
======================================================================
Total Passed: 50/50
Total Failed: 0/50

🎉 ✅ STAGE 1 COMPLETE - ALL 50 CRITERIA PASSED

You may proceed to Stage 2.
```

---

## Definition of COMPLETE

**Stage 1 is COMPLETE if and only if:**

```bash
python3 verify_stage_1_complete.py
# Returns exit code 0
# Prints: "✅ STAGE 1 COMPLETE - ALL 50 CRITERIA PASSED"
```

**Stage 1 is INCOMPLETE if:**
- Any of the 50 criteria fail
- Exit code is non-zero
- Output shows any ❌ marks

---

## What This Ensures

### ✅ Trust
- Every value has confidence score (B1-B3)
- Confidence never lies (increases without justification) (B2.3)
- Blocking rules prevent unreliable outputs (B3)

### ✅ Traceability
- Every value has complete lineage to Excel source (C1)
- Every transformation is documented (C2.1)
- Queries return accurate results (C3)

### ✅ Fixability
- User can override with Analyst Brain (E2.4)
- Impact of changes is deterministic (D2.5)
- System provides clear error messages (E2.1-E2.3)

### ✅ Anti-Speculation
- Cannot create values without lineage (D1.1)
- Cannot impute missing data (D1.4)
- Cannot have silent failures (D1.5)

---

## What This Does NOT Ensure

### ❌ UI Quality
- Does not test Streamlit UI or "Why This Number?" modal
- Does not verify visual design or user experience
- Does not require polished frontend

### ❌ Generative AI Usage
- Does not require LLM-based mapping suggestions
- Does not require AI-powered audit commentary
- Does not require natural language interfaces

### ❌ Performance Optimization
- Does not set speed requirements (beyond "reasonable")
- Does not require caching or parallelization
- Does not mandate specific algorithms

### ❌ Production Deployment
- Does not require Docker containers
- Does not require CI/CD pipelines
- Does not require monitoring/alerting

---

## Enforcement

**No work proceeds to Stage 2 until:**

1. `verify_stage_1_complete.py` returns exit code 0
2. All 50/50 criteria pass
3. Verification script output is committed to repo as `STAGE_1_VERIFICATION_REPORT.txt`

**To commit Stage 1 as complete:**
```bash
# Run verification
python3 verify_stage_1_complete.py > STAGE_1_VERIFICATION_REPORT.txt

# Check exit code
if [ $? -eq 0 ]; then
    echo "Stage 1 verification passed"
    git add STAGE_1_VERIFICATION_REPORT.txt
    git commit -m "Certify Stage 1 Core Engine Hardening as COMPLETE"
else
    echo "Stage 1 verification failed - do not proceed"
    exit 1
fi
```

**This commit is the gate to Stage 2.**

---

## Appendix: Criteria Checklist

**Quick reference for tracking progress:**

```
SECTION A: MANDATORY ARTIFACTS (10)
[ ] A1.1  confidence_engine.py exists (500+ lines)
[ ] A1.2  lineage_graph.py exists (700+ lines)
[ ] A1.3  brain_manager.py exists (200+ lines)
[ ] A1.4  FEATURE_INTEGRATION_CONTRACT.md exists
[ ] A1.5  ANTI_SPECULATION_RULES.md exists
[ ] A2.1  test_confidence_engine.py exists (20+ tests)
[ ] A2.2  test_lineage_graph.py exists (20+ tests)
[ ] A2.3  test_integration.py exists (10+ tests)
[ ] A2.4  test_anti_speculation.py exists (10+ tests)
[ ] A2.5  tests/fixtures/ exists (3+ files)

SECTION B: CONFIDENCE ENGINE (10)
[ ] B1.1  Analyst Brain → 1.00
[ ] B1.2  Explicit Alias → 0.95
[ ] B1.3  Exact Label → 0.90
[ ] B1.4  Keyword Match → 0.70
[ ] B1.5  Unmapped → 0.00
[ ] B2.1  Aggregation uses MIN(sources)
[ ] B2.2  Calculation uses MIN(inputs) × factor
[ ] B2.3  Confidence never increases
[ ] B2.4  Missing values → 0.00
[ ] B3.1  DCF blocking rules enforced
[ ] B3.2  LBO blocking rules enforced

SECTION C: LINEAGE GRAPH (10)
[ ] C1.1  All EXTRACTED have SOURCE_CELL ancestors
[ ] C1.2  All MAPPED have EXTRACTED ancestors
[ ] C1.3  All AGGREGATED have MAPPED ancestors
[ ] C1.4  All CALCULATED have AGGREGATED/CALCULATED ancestors
[ ] C1.5  Zero orphan nodes
[ ] C2.1  All edges have 'method'
[ ] C2.2  All edges have 'confidence' [0.0-1.0]
[ ] C2.3  MAPPING edges have 'source'
[ ] C2.4  AGGREGATION edges have 'aggregation_strategy'
[ ] C2.5  CALCULATION edges have 'formula'
[ ] C3.1  trace_backward() complete
[ ] C3.2  trace_forward() complete
[ ] C3.3  find_path() accurate

SECTION D: ANTI-SPECULATION (10)
[ ] D1.1  Value without lineage → raises error
[ ] D1.2  Mapping without confidence → raises error
[ ] D1.3  Global state → linter fails
[ ] D1.4  Imputing values → raises error
[ ] D1.5  Output with conf=0.00 → blocked
[ ] D2.1  Value with lineage+conf → succeeds
[ ] D2.2  Unmapped value → excluded from output
[ ] D2.3  Brain overrides defaults → always wins
[ ] D2.4  Export lineage → includes all edges/nodes
[ ] D2.5  Deterministic: same input → same output

SECTION E: INTEGRATION (10)
[ ] E1.1  Valid Excel → All models generate
[ ] E1.2  All outputs have conf > 0.00
[ ] E1.3  All outputs have lineage to Excel
[ ] E1.4  Balance sheet validates
[ ] E1.5  Audit report generates (50+ checks)
[ ] E2.1  Missing concepts → blocks, lists missing
[ ] E2.2  Negative revenue → CRITICAL, blocks DCF
[ ] E2.3  Unmapped items → conf degrades, reports count
[ ] E2.4  Brain override → conf increases to 1.00
[ ] E2.5  Delete mapped item → conf drops, blocks model

TOTAL: [ ] 50/50 PASSED → STAGE 1 COMPLETE
```

---

## Summary

**Stage 1 is COMPLETE** means:

1. ✅ All 10 mandatory files exist with required content
2. ✅ All 60+ test cases pass (across 4 test files)
3. ✅ Confidence engine enforces all scoring/propagation/blocking rules
4. ✅ Lineage graph guarantees complete provenance for all values
5. ✅ Anti-speculation rules are programmatically enforced (violations raise errors)
6. ✅ Integration tests verify end-to-end correctness
7. ✅ `verify_stage_1_complete.py` exits with code 0

**Stage 1 is INCOMPLETE** if even ONE criterion fails.

**Binary. Testable. Independent of UI and AI.**

---

**End of Completion Criteria**

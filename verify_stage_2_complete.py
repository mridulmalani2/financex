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
    env = os.environ.copy()
    env['PYTHONPATH'] = '/home/user/financex:' + env.get('PYTHONPATH', '')
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)

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

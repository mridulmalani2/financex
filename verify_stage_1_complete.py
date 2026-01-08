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
        fixture_count = len([f for f in os.listdir('tests/fixtures') if not f.startswith('.')])
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
            print(f"\n  Failed tests output:")
            for line in output.split('\n'):
                if 'FAILED' in line or 'ERROR' in line:
                    print(f"    {line}")
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
            print(f"\n  Failed tests output:")
            for line in output.split('\n'):
                if 'FAILED' in line or 'ERROR' in line:
                    print(f"    {line}")
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
            print(f"\n  Failed tests output:")
            for line in output.split('\n'):
                if 'FAILED' in line or 'ERROR' in line:
                    print(f"    {line}")
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
            print(f"\n  Failed tests output:")
            for line in output.split('\n'):
                if 'FAILED' in line or 'ERROR' in line:
                    print(f"    {line}")
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

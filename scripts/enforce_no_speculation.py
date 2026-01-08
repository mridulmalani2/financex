#!/usr/bin/env python3
"""
Enforce Anti-Speculation Rules - Production V1.0
================================================
Automated linting to prevent speculative logic in financial code.

This script scans Python files for patterns that violate FinanceX invariants:
- No inferred financial meaning
- No guessing missing values
- No probabilistic language in deterministic code
- No randomness in calculations

Exit Codes:
  0 - No violations found
  1 - Violations found (blocks commit)
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class Violation:
    """Represents a single violation of anti-speculation rules."""
    filepath: Path
    line_num: int
    pattern_name: str
    message: str
    line_content: str
    severity: str  # "ERROR", "WARNING"


# Forbidden patterns with explanations
FORBIDDEN_PATTERNS = {
    # Speculation language
    r"\bguess(?:ing|ed)?\b": {
        "message": "No guessing allowed in financial code - use explicit mapping with confidence scores",
        "severity": "ERROR"
    },
    r"\bassume(?:s|d)?\b": {
        "message": "No assumptions without mathematical proof - document accounting identities only",
        "severity": "ERROR"
    },
    r"\bprobably\b": {
        "message": "No probabilistic language in deterministic code",
        "severity": "ERROR"
    },
    r"\bmaybe\b": {
        "message": "No uncertainty in financial logic - be explicit",
        "severity": "WARNING"
    },

    # Inference patterns
    r'if\s+["\']?\w*sales?\w*["\']?\s+in\s+\w+\.lower\(\).*return\s+["\']us-gaap_': {
        "message": "No inferred financial meaning - use explicit mapper with confidence scoring",
        "severity": "ERROR"
    },
    r'if\s+["\']?\w*revenue\w*["\']?\s+in\s+\w+\.lower\(\).*return\s+["\']us-gaap_': {
        "message": "No inferred financial meaning - use explicit mapper with confidence scoring",
        "severity": "ERROR"
    },

    # Imputation without proof
    r"\bimpute\b": {
        "message": "Value imputation requires @mathematically_derived decorator and proof",
        "severity": "ERROR"
    },
    r"\bfill(?:na|_missing)\b": {
        "message": "Filling missing values requires mathematical justification",
        "severity": "ERROR"
    },
    r"=\s*\w+\s*\*\s*0\.\d+\s*#.*default": {
        "message": "Default multipliers are speculation - missing data should remain missing",
        "severity": "WARNING"
    },

    # Randomness
    r"\brandom\.": {
        "message": "No randomness in financial calculations - violates determinism invariant",
        "severity": "ERROR"
    },
    r"\bnp\.random\.": {
        "message": "No randomness in financial calculations - violates determinism invariant",
        "severity": "ERROR"
    },

    # Hidden state
    r"^[A-Z_]+\s*=\s*\{\}": {
        "message": "Global dictionary state - use instance variables or session-scoped state",
        "severity": "ERROR"
    },
    r"^[A-Z_]+\s*=\s*\[\]": {
        "message": "Global list state - use instance variables or session-scoped state",
        "severity": "ERROR"
    },

    # Silent failures
    r"except.*:\s*pass": {
        "message": "Silent exception handling - financial errors must be logged explicitly",
        "severity": "ERROR"
    },
    r"except.*:\s*return\s+0": {
        "message": "Silent error returning zero - use explicit confidence = 0.00 and log error",
        "severity": "WARNING"
    },
}

# Patterns that are allowed with proper annotations
ALLOWED_WITH_ANNOTATION = {
    r"\bimpute\b": "@mathematically_derived",
    r"\bassume\b": "@accounting_identity",
}

# Safe patterns that look like violations but are actually OK
SAFE_PATTERNS = [
    # fillna(0) for display formatting (ratios, percentages)
    r"\.fillna\(0\)\.round\(",
    r"\)\.fillna\(0\)$",  # End of line fillna for display
    # "assume" in comments about what we DON'T do
    r"#.*doesn't assume",
    r"#.*no assumption",
    r"-.*doesn't assume",  # Docstring bullets
    r"without.*guessing",  # Docstring bullets about NOT guessing
    r"without file-path guessing",  # Specific docstring patterns
    # Using "maybe" in error messages or logging
    r"logger\.\w+\(.*maybe",
    r"print\(.*maybe",
]

# Directories to skip
SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "venv",
    "env",
    ".venv",
}

# Files to skip
SKIP_FILES = {
    "enforce_no_speculation.py",  # This file itself
    "test_",  # Test files (pattern)
}


def should_skip_file(filepath: Path) -> bool:
    """Check if file should be skipped."""
    # Skip if in excluded directory
    for skip_dir in SKIP_DIRS:
        if skip_dir in filepath.parts:
            return True

    # Skip test files
    if filepath.name.startswith("test_"):
        return True

    # Skip specific files
    for skip_file in SKIP_FILES:
        if filepath.name == skip_file:
            return True

    return False


def check_file(filepath: Path) -> List[Violation]:
    """Check a single file for forbidden patterns."""
    violations = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except (UnicodeDecodeError, PermissionError):
        # Skip binary files or files we can't read
        return violations

    # Read entire file for context checking
    full_content = ''.join(lines)

    for line_num, line in enumerate(lines, 1):
        # Skip comments and docstrings (simple heuristic)
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        if stripped.startswith('"""') or stripped.startswith("'''"):
            continue

        # Check each forbidden pattern
        for pattern, rule in FORBIDDEN_PATTERNS.items():
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                # Check if this is a safe pattern (false positive)
                is_safe = False
                for safe_pattern in SAFE_PATTERNS:
                    if re.search(safe_pattern, line):
                        is_safe = True
                        break

                if is_safe:
                    continue

                # Check if pattern is allowed with annotation
                if pattern in ALLOWED_WITH_ANNOTATION:
                    required_annotation = ALLOWED_WITH_ANNOTATION[pattern]
                    # Look for annotation in previous 5 lines
                    start_line = max(0, line_num - 5)
                    context = ''.join(lines[start_line:line_num])
                    if required_annotation in context:
                        # Pattern is allowed with proper annotation
                        continue

                violations.append(Violation(
                    filepath=filepath,
                    line_num=line_num,
                    pattern_name=pattern,
                    message=rule["message"],
                    line_content=line.strip(),
                    severity=rule["severity"]
                ))

    return violations


def scan_codebase(root_dir: Path = Path(".")) -> Tuple[List[Violation], List[Violation]]:
    """
    Scan entire codebase for violations.

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []

    # Find all Python files
    for py_file in root_dir.rglob("*.py"):
        if should_skip_file(py_file):
            continue

        violations = check_file(py_file)

        for violation in violations:
            if violation.severity == "ERROR":
                errors.append(violation)
            else:
                warnings.append(violation)

    return errors, warnings


def format_violation(v: Violation) -> str:
    """Format violation for display."""
    return (
        f"\n{v.severity}: {v.filepath}:{v.line_num}\n"
        f"  Pattern: {v.pattern_name}\n"
        f"  Issue: {v.message}\n"
        f"  Code: {v.line_content}\n"
    )


def main():
    """Main enforcement function."""
    print("=" * 70)
    print("FINANCEX ANTI-SPECULATION ENFORCEMENT")
    print("=" * 70)
    print("Scanning for patterns that violate financial invariants...\n")

    # Scan codebase
    errors, warnings = scan_codebase()

    # Report warnings
    if warnings:
        print(f"⚠️  {len(warnings)} WARNINGS found:")
        print("=" * 70)
        for w in warnings:
            print(format_violation(w))
        print()

    # Report errors
    if errors:
        print(f"❌ {len(errors)} ERRORS found:")
        print("=" * 70)
        for e in errors:
            print(format_violation(e))

        print("=" * 70)
        print("VIOLATIONS DETECTED - Commit blocked")
        print("=" * 70)
        print("\nFix violations or add proper annotations:")
        print("  - @mathematically_derived for imputation from accounting identities")
        print("  - @accounting_identity for documented accounting equations")
        print("\nSee FEATURE_INTEGRATION_CONTRACT.md for guidance.")
        return 1

    # Success
    print("✅ No speculation violations found")
    print(f"   Checked Python files in codebase")
    if warnings:
        print(f"   {len(warnings)} warnings (non-blocking)")
    print("\nAll anti-speculation rules enforced successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

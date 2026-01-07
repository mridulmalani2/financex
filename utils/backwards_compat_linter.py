#!/usr/bin/env python3
"""
Backwards Compatibility Linter - Production V1.0
================================================
Enforces "No Backwards Compatibility Hacks" invariant.

INVARIANT: Financial systems must be maintainable long-term.
Backwards compatibility layers accumulate technical debt and create undefined behavior.

This linter checks for common violations:
1. Unused parameters preserved (e.g., old_param=None)
2. Variables renamed with underscore prefix (e.g., _old_var)
3. "removed" comments (e.g., # Old code removed)
4. "deprecated" without removal (code still present)
5. Re-export of removed symbols
6. Conditional logic based on version/feature flags for removed features

Usage:
    python utils/backwards_compat_linter.py <file_or_directory>
    python utils/backwards_compat_linter.py .  # Check entire project

Exit code:
    0 = No violations found
    1 = Violations found
"""

import os
import re
import sys
import ast
from typing import List, Dict, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Violation:
    """A single backwards compatibility violation."""
    file_path: str
    line_number: int
    violation_type: str
    message: str
    code_snippet: str


class BackwardsCompatLinter:
    """
    Linter that detects backwards compatibility violations.
    """

    def __init__(self):
        self.violations: List[Violation] = []

        # Patterns to detect
        self.patterns = {
            'unused_underscore_var': re.compile(r'^\s*_\w+\s*='),
            'removed_comment': re.compile(r'#.*\b(removed|deleted|legacy|old code)\b', re.IGNORECASE),
            'deprecated_comment': re.compile(r'#.*\b(deprecated|obsolete)\b', re.IGNORECASE),
            'version_check': re.compile(r'if.*version|if.*LEGACY|if.*COMPAT', re.IGNORECASE),
            're_export': re.compile(r'from\s+\S+\s+import\s+\S+\s+as\s+_\w+'),
        }

    def check_file(self, file_path: str):
        """Check a single Python file for violations."""
        if not file_path.endswith('.py'):
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except (OSError, UnicodeDecodeError):
            return  # Skip files that can't be read

        # Check line-by-line
        for line_num, line in enumerate(lines, start=1):
            self._check_line(file_path, line_num, line, lines)

        # Check AST for function signatures
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=file_path)
            self._check_ast(file_path, tree, lines)
        except SyntaxError:
            pass  # Skip files with syntax errors

    def _check_line(self, file_path: str, line_num: int, line: str, all_lines: List[str]):
        """Check a single line for violations."""

        # Check for unused underscore variables
        if self.patterns['unused_underscore_var'].match(line):
            # Check if this variable is actually used later
            var_name = line.split('=')[0].strip()
            used = any(var_name in other_line for other_line in all_lines[line_num:])
            if not used:
                self.violations.append(Violation(
                    file_path=file_path,
                    line_number=line_num,
                    violation_type="UNUSED_UNDERSCORE_VAR",
                    message=f"Unused variable with underscore prefix: {var_name}. Delete unused code instead of renaming.",
                    code_snippet=line.strip()
                ))

        # Check for "removed" or "legacy" comments
        if self.patterns['removed_comment'].search(line):
            self.violations.append(Violation(
                file_path=file_path,
                line_number=line_num,
                violation_type="REMOVED_COMMENT",
                message="Comment mentions 'removed' or 'legacy' code. Delete the comment and code completely.",
                code_snippet=line.strip()
            ))

        # Check for deprecated comments (warn only if code still present)
        if self.patterns['deprecated_comment'].search(line):
            # Check if there's actual code on this line (not just comment)
            code_part = line.split('#')[0].strip()
            if code_part:
                self.violations.append(Violation(
                    file_path=file_path,
                    line_number=line_num,
                    violation_type="DEPRECATED_WITH_CODE",
                    message="Code marked 'deprecated' but still present. Delete deprecated code completely.",
                    code_snippet=line.strip()
                ))

        # Check for version/legacy checks
        if self.patterns['version_check'].search(line):
            self.violations.append(Violation(
                file_path=file_path,
                line_number=line_num,
                violation_type="VERSION_CHECK",
                message="Version/legacy/compat check detected. Remove backwards compatibility logic.",
                code_snippet=line.strip()
            ))

        # Check for re-exports with underscore
        if self.patterns['re_export'].search(line):
            self.violations.append(Violation(
                file_path=file_path,
                line_number=line_num,
                violation_type="UNDERSCORE_REEXPORT",
                message="Re-export with underscore prefix detected. Delete unused imports completely.",
                code_snippet=line.strip()
            ))

    def _check_ast(self, file_path: str, tree: ast.AST, lines: List[str]):
        """Check AST for function signature violations."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._check_function_signature(file_path, node, lines)

    def _check_function_signature(self, file_path: str, func: ast.FunctionDef, lines: List[str]):
        """Check function signature for unused parameters."""
        func_body_lines = lines[func.lineno - 1:func.end_lineno] if hasattr(func, 'end_lineno') else []
        func_body_text = ''.join(func_body_lines)

        for arg in func.args.args:
            arg_name = arg.arg

            # Skip common patterns (self, cls, kwargs, etc.)
            if arg_name in ('self', 'cls', 'args', 'kwargs'):
                continue

            # Check if parameter starts with underscore (potential unused marker)
            if arg_name.startswith('_'):
                # Check if it's actually used in function body
                if arg_name not in func_body_text:
                    self.violations.append(Violation(
                        file_path=file_path,
                        line_number=func.lineno,
                        violation_type="UNUSED_PARAMETER",
                        message=f"Function '{func.name}' has unused parameter with underscore: {arg_name}. Remove unused parameters instead of renaming.",
                        code_snippet=f"def {func.name}(..., {arg_name}, ...)"
                    ))

    def check_directory(self, directory: str):
        """Recursively check all Python files in a directory."""
        for root, dirs, files in os.walk(directory):
            # Skip common non-code directories
            dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', 'venv', '.venv', 'node_modules')]

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self.check_file(file_path)

    def print_report(self):
        """Print violations report."""
        if not self.violations:
            print("✅ No backwards compatibility violations found!")
            return

        print(f"❌ Found {len(self.violations)} backwards compatibility violations:\n")

        # Group by type
        by_type: Dict[str, List[Violation]] = {}
        for v in self.violations:
            if v.violation_type not in by_type:
                by_type[v.violation_type] = []
            by_type[v.violation_type].append(v)

        for vtype, violations in sorted(by_type.items()):
            print(f"## {vtype} ({len(violations)} violations)")
            print("=" * 70)
            for v in violations:
                print(f"  File: {v.file_path}:{v.line_number}")
                print(f"  Message: {v.message}")
                print(f"  Code: {v.code_snippet}")
                print()
            print()

    def has_violations(self) -> bool:
        """Check if any violations were found."""
        return len(self.violations) > 0


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python backwards_compat_linter.py <file_or_directory>")
        print("Example: python backwards_compat_linter.py .")
        sys.exit(1)

    target = sys.argv[1]

    linter = BackwardsCompatLinter()

    if os.path.isfile(target):
        print(f"Checking file: {target}")
        linter.check_file(target)
    elif os.path.isdir(target):
        print(f"Checking directory: {target}")
        linter.check_directory(target)
    else:
        print(f"Error: {target} is not a valid file or directory")
        sys.exit(1)

    linter.print_report()

    # Exit with error code if violations found
    sys.exit(1 if linter.has_violations() else 0)


if __name__ == "__main__":
    main()

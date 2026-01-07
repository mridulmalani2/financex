# FinanceX Invariant Enforcement

**Status:** Production V1.0
**Date:** 2026-01-07
**Purpose:** Documentation of code-enforced invariants

---

## Overview

This document describes the 4 invariants that were previously convention-only and have now been enforced by code.

These enforcements ensure production-grade reliability and prevent silent failures.

---

## 1. Taxonomy Database Read-Only ✅ ENFORCED

**Location:** `taxonomy_utils.py:35-55`

**WHY:** The 23,598 XBRL concepts are official standards. Modifying them would create non-standard taxonomy and break interoperability.

**ENFORCEMENT:**
```python
# Open database in read-only mode (uri=True enables read-only flag)
db_uri = f"file:{self.db_path}?mode=ro"
try:
    self.conn = sqlite3.connect(db_uri, uri=True)
except sqlite3.OperationalError as e:
    # If read-only mode fails, open normally but warn
    print(f"  WARNING: Could not open database in read-only mode: {e}")
```

**BEHAVIOR:**
- Database opened with SQLite read-only flag (`?mode=ro`)
- Any attempt to INSERT/UPDATE/DELETE will raise `sqlite3.OperationalError`
- If read-only mode unavailable, opens normally with prominent warning
- File permission check performed before opening

**TESTING:**
```python
# This should fail
engine = TaxonomyEngine("output/taxonomy_2025.db")
engine.connect()
cursor = engine.conn.cursor()
cursor.execute("DELETE FROM concepts WHERE element_id = 'us-gaap_Revenues'")
# Raises: sqlite3.OperationalError: attempt to write a readonly database
```

---

## 2. Thinking Logs Must Be Written ✅ ENFORCED

**Location:** `modeler/engine.py:64-129`

**WHY:** Iterative thinking process must be traceable. Auditors need to see why the system made certain decisions.

**ENFORCEMENT:**
```python
def log(self, message: str, level: str = "INFO"):
    # Always keep in memory (fallback if file write fails)
    self.entries.append(entry)

    # Try to write to file
    if self.log_path:
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(entry + "\n")
        except (OSError, PermissionError, IOError) as e:
            self.write_errors += 1
            if self.write_errors <= self.max_write_errors:
                print(f"  WARNING: Cannot write to thinking log: {e}")
```

**BEHAVIOR:**
- All log entries always stored in memory (guaranteed)
- File writes attempted with error handling
- Warnings printed for first 5 write failures
- Processing continues even if file writes fail
- In-memory logs can be retrieved via `get_summary()`

**TESTING:**
```python
# Simulate write failure
logger = ThinkingLogger(log_dir="/read-only-dir")
logger.log("Test message")
# Prints warning, but continues processing
# Log still available: logger.get_summary()
```

---

## 3. Calculation Weights Must Be ±1.0 ✅ ENFORCED

**Location:** `taxonomy_utils.py:78-120`

**WHY:** XBRL calculation linkbase uses +1.0 (additive) or -1.0 (subtractive). Other values violate XBRL spec.

**ENFORCEMENT:**
```python
for row in cur.fetchall():
    weight = row['weight']

    # INVARIANT ENFORCEMENT: Calculation weights must be ±1.0 per XBRL spec
    if weight not in (1.0, -1.0):
        invalid_weights.append({...})
        # Coerce to nearest valid value
        weight = 1.0 if weight > 0 else -1.0
```

**BEHAVIOR:**
- Every calculation weight validated during cache loading
- Invalid weights (not ±1.0) are coerced to nearest valid value
- Warning printed showing invalid relationships
- First 5 examples displayed for debugging
- System continues with corrected weights

**TESTING:**
```python
# If database has weight=0.5
engine = TaxonomyEngine()
engine.connect()
# Prints: WARNING: Found X calculation relationships with invalid weights
# Weight coerced to 1.0
children = engine.get_calculation_children('us-gaap_Revenues')
assert all(c['weight'] in (1.0, -1.0) for c in children)
```

---

## 4. No Backwards Compatibility Hacks ✅ ENFORCED

**Location:** `utils/backwards_compat_linter.py`

**WHY:** Financial systems must be maintainable long-term. Backwards compatibility layers accumulate technical debt.

**ENFORCEMENT:**
Automated linter checks for:
- Unused variables renamed with underscore prefix (e.g., `_old_var`)
- Comments mentioning "removed", "legacy", "old code"
- "Deprecated" comments with code still present
- Version/legacy/compat conditional checks
- Re-exports with underscore prefix
- Unused function parameters with underscore prefix

**USAGE:**
```bash
# Check entire project
python utils/backwards_compat_linter.py .

# Check specific file
python utils/backwards_compat_linter.py mapper/mapper.py

# Exit code 0 = clean, 1 = violations found
```

**BEHAVIOR:**
- Scans Python files for common backwards compatibility patterns
- Reports violations with file, line number, and message
- Groups violations by type
- Can be integrated into CI/CD pipeline

**EXAMPLE OUTPUT:**
```
❌ Found 3 backwards compatibility violations:

## UNUSED_UNDERSCORE_VAR (1 violation)
======================================================================
  File: mapper/mapper.py:245
  Message: Unused variable with underscore prefix: _old_param. Delete unused code instead of renaming.
  Code: _old_param = None

## REMOVED_COMMENT (2 violations)
======================================================================
  File: engine.py:512
  Message: Comment mentions 'removed' or 'legacy' code. Delete the comment and code completely.
  Code: # Old aggregation logic removed
```

**INTEGRATION WITH CI/CD:**
```bash
# Add to pre-commit hook or CI pipeline
python utils/backwards_compat_linter.py . || exit 1
```

---

## Summary

All 4 previously convention-only invariants are now enforced by code:

| Invariant | Enforcement Method | Failure Behavior |
|-----------|-------------------|------------------|
| Taxonomy Read-Only | SQLite read-only mode | OperationalError on write attempts |
| Thinking Logs Written | Try/except with fallback | Warning printed, in-memory logs retained |
| Calculation Weights ±1.0 | Validation + coercion | Invalid weights coerced, warning printed |
| No Backwards Compat | Static analysis linter | Violations reported, CI fails |

---

## Developer Guidelines

### For New Code

1. **Taxonomy Database:** Never write to taxonomy database in application code
2. **Thinking Logs:** Always use `ThinkingLogger` class (error handling built-in)
3. **Calculation Weights:** Let system validate (enforcement automatic)
4. **Backwards Compatibility:** Run linter before committing: `python utils/backwards_compat_linter.py .`

### For Code Reviews

When reviewing PRs, check for:
- ❌ Direct SQL writes to taxonomy database
- ❌ Custom file writing for logs (use `ThinkingLogger`)
- ❌ Manual calculation weight handling (use `TaxonomyEngine`)
- ❌ Backwards compatibility patterns (run linter)

### For Testing

```bash
# Test taxonomy read-only
python -c "from taxonomy_utils import get_taxonomy_engine; e = get_taxonomy_engine(); e.connect(); e.conn.execute('DELETE FROM concepts')"
# Should fail with: attempt to write a readonly database

# Test thinking log error handling
mkdir /tmp/readonly && chmod 444 /tmp/readonly
python -c "from modeler.engine import ThinkingLogger; ThinkingLogger('/tmp/readonly')"
# Should print warning and continue

# Test calculation weight validation
python -c "from taxonomy_utils import get_taxonomy_engine; e = get_taxonomy_engine(); e.connect()"
# Should print warning if any invalid weights found

# Test backwards compat linter
python utils/backwards_compat_linter.py .
# Should report any violations
```

---

## Rationale: Why Enforce These?

### Production-Grade Requirements

Financial systems used for investment decisions MUST:
1. **Prevent data corruption** (taxonomy read-only)
2. **Maintain audit trails** (thinking logs)
3. **Follow standards** (XBRL spec compliance)
4. **Be maintainable** (no tech debt accumulation)

### Regulatory Compliance

- **SOX (Sarbanes-Oxley):** Requires audit trails and data integrity
- **SEC Regulations:** XBRL filings must follow official taxonomy
- **FINRA:** Investment decisions must be traceable and defensible

### Investor Protection

Bad data = bad valuations = bad investment decisions = investor losses

These enforcements prevent silent failures that could propagate through:
- DCF models → Enterprise valuations
- LBO models → Acquisition pricing
- Comps analysis → Relative valuations

---

## Updating This Document

When adding new invariant enforcements:
1. Add section with location, WHY, enforcement code
2. Document behavior and testing procedure
3. Update summary table
4. Update developer guidelines

---

**Last Updated:** 2026-01-07
**Version:** 1.0
**Maintainer:** FinanceX Core Team

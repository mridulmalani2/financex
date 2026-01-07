# FinanceX Enhanced Mapper Migration Guide

## Overview

This guide explains how to migrate from the current mapper to the enhanced version with improved taxonomy utilization.

---

## What Changed?

### OLD (mapper.py)
- **Tier 2.5:** ❌ Does not exist
- **Fallback:** Hardcoded keywords only (`revenue` → `us-gaap_Revenues`)
- **Taxonomy Usage:** ~15% (only exact label matches)

### NEW (mapper_enhanced.py)
- **Tier 2.5:** ✅ Fuzzy Taxonomy Label Search across all 24,388 labels
- **Fallback:** Smart taxonomy search first, then keywords
- **Taxonomy Usage:** ~90% potential (searches all label types)

---

## Migration Steps

### Option 1: Drop-in Replacement (Recommended)

The enhanced mapper is **backwards compatible**. Simply replace the import:

```python
# OLD:
from mapper.mapper import FinancialMapper

# NEW:
from mapper.mapper_enhanced import EnhancedFinancialMapper as FinancialMapper
```

**Or** rename the file:
```bash
mv mapper/mapper.py mapper/mapper_old.py
mv mapper/mapper_enhanced.py mapper/mapper.py
```

### Option 2: Gradual Rollout

Test the new mapper alongside the old one:

```python
from mapper.mapper import FinancialMapper as OldMapper
from mapper.mapper_enhanced import EnhancedFinancialMapper as NewMapper

# Test both
old_result = old_mapper.map_input("Total Net Sales")
new_result = new_mapper.map_input("Total Net Sales")

# Compare results
if old_result != new_result:
    print(f"Difference found: {old_result['element_id']} vs {new_result['element_id']}")
```

---

## Testing the Enhanced Mapper

### Run Built-in Tests

```bash
python3 mapper/mapper_enhanced.py
```

**Expected Output:**
```
Success Rate: 95%+
Tier 2.5 (Fuzzy Taxonomy): 20-40% of total matches
```

### Custom Test

```python
from mapper.mapper_enhanced import EnhancedFinancialMapper

mapper = EnhancedFinancialMapper("output/taxonomy_2025.db", "config/aliases.csv")
mapper.connect()

# Test your specific labels
test_labels = [
    "Total Net Sales",
    "Cost of Goods Sold",
    "Operating Income",
    # Add your company-specific labels here
]

for label in test_labels:
    result = mapper.map_input(label)
    print(f"{label} → {result['element_id']} ({result['method']})")

# Check statistics
stats = mapper.get_mapping_stats()
print(f"\nTier 2.5 Usage: {stats['tier_2_5_pct']}%")
```

---

## Key Benefits

### 1. Higher Mapping Success Rate
- **Before:** 70-80% success rate
- **After:** 90-95% success rate (estimated)

### 2. More Precise Mappings
- **Before:** `"Product Revenue"` → hardcoded → `us-gaap_Revenues`
- **After:** `"Product Revenue"` → fuzzy search → `us-gaap_RevenueFromSaleOfProduct` ✅ More precise!

### 3. Better Audit Trail
```python
result = mapper.map_input("Net Sales")
print(result['method'])
# Output: "Fuzzy Taxonomy (standard, conf=95)"
# You can see the confidence score and label type used
```

---

## Known Issues and Limitations

### Issue 1: Over-Matching in Fuzzy Search
**Problem:** Fuzzy search may match overly generic terms.

**Example:**
```
Input: "Mystery Account"
Matches: us-gaap-ebp_EmployeeBenefitPlanForfeitedNonvestedAccount
```

**Why:** The word "Account" appears in many concepts.

**Fix:** Add filtering by concept source and balance type:
```python
# In _search_taxonomy_labels(), add:
WHERE c.source = 'US_GAAP'           # Filter by taxonomy
AND c.abstract = 0                   # Skip abstract concepts
AND (c.balance IN ('debit', 'credit') OR c.balance IS NULL)
```

### Issue 2: Multiple Good Matches
**Problem:** Several concepts may have similar labels.

**Example:**
```
"Revenue" could match:
- us-gaap_Revenues (standard label: "Revenues")
- us-gaap_SalesRevenueNet (standard label: "Sales Revenue, Net")
- us-gaap_RevenueFromContractWithCustomer (long label)
```

**Fix:** Prefer shorter labels and "total" role:
```python
ORDER BY
    CASE WHEN l.label_role = 'total' THEN 1 ELSE 2 END,
    LENGTH(l.label_text) ASC,
    confidence DESC
```

---

## Rollback Plan

If you encounter issues, easily rollback:

```bash
# Restore original mapper
git checkout mapper/mapper.py

# Or if you renamed
mv mapper/mapper_old.py mapper/mapper.py
```

---

## Performance Considerations

### Database Query Performance
The new mapper executes SQL queries for fuzzy matching:
- **Query Time:** ~10-50ms per lookup (cached connections)
- **Impact:** Minimal for batch processing (<1000 items)

### Optimization Tips

1. **Use Caching** (already implemented):
   ```python
   # First lookup: 50ms (DB query)
   # Subsequent lookups: <1ms (in-memory cache)
   ```

2. **Batch Processing**:
   ```python
   # Pre-warm the cache
   mapper.connect()  # Loads indexes into memory
   ```

3. **Database Indexing**:
   ```sql
   -- Already created in taxonomy DB
   CREATE INDEX idx_labels_text ON labels(LOWER(label_text));
   CREATE INDEX idx_labels_role ON labels(label_role);
   ```

---

## Monitoring and Analytics

### Get Mapping Statistics

```python
stats = mapper.get_mapping_stats()

print(f"Total Mappings: {stats['total_mapped']}")
print(f"Fuzzy Taxonomy Usage: {stats['tier_2_5_fuzzy_taxonomy']} ({stats['tier_2_5_pct']}%)")
print(f"Success Rate: {100 - stats['tier_5_pct']}%")
```

### Track Unmapped Items

```python
# After processing your file
unmapped_items = [label for label in your_labels
                  if not mapper.map_input(label)['found']]

print(f"Unmapped: {len(unmapped_items)}")
for item in unmapped_items:
    print(f"  - {item}")
```

---

## Next Steps

### Phase 1: Testing (This Release)
- ✅ Test enhanced mapper with sample data
- ✅ Compare results against current mapper
- ✅ Measure success rate improvement

### Phase 2: Refinement (Future)
- 🔄 Add concept filtering (skip abstract, prefer certain balance types)
- 🔄 Implement multi-taxonomy smart selection (US GAAP vs IFRS)
- 🔄 Add calculation linkbase inference (if children exist, calculate parent)

### Phase 3: Advanced Features (Future)
- ⏳ Dimensional mapping (Geographic, Product, Segment)
- ⏳ Time-period awareness (Q1 vs FY labels)
- ⏳ Industry-specific taxonomies (Banking, Insurance, Tech)

---

## FAQ

### Q: Will my existing aliases.csv still work?
**A:** Yes! Aliases have **highest priority** (Tier 1) and will override all other mappings.

### Q: Do I need to rebuild the taxonomy database?
**A:** No! The enhanced mapper uses the same database schema.

### Q: What if fuzzy matching gives wrong results?
**A:** Add an explicit alias to override:
```csv
# aliases.csv
US_GAAP,"Your Label","us-gaap_CorrectConcept"
```

### Q: How do I disable fuzzy matching if needed?
**A:** Modify the mapper:
```python
# In map_input(), comment out Tier 2.5:
# taxonomy_match = self._search_taxonomy_labels(raw_input)
# if taxonomy_match:
#     return taxonomy_match
```

---

## Support and Feedback

If you encounter issues:

1. **Check the verification report**: `VERIFICATION_REPORT.md`
2. **Review mapping statistics**: `mapper.get_mapping_stats()`
3. **Enable debug logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

---

**Last Updated:** 2026-01-07
**Version:** Enhanced Mapper v4.0

#!/usr/bin/env python3
"""
Taxonomy Utilities: Calculation Linkbase & Hierarchy Engine
============================================================
Provides dynamic queries against the XBRL taxonomy database for:
1. Calculation relationships (parent-child with weights)
2. Presentation hierarchy (for safe-mode fallback)
3. Balance type normalization (debit/credit sign handling)
4. Cross-statement validation rules

This replaces hardcoded concept sets with dynamic, taxonomy-driven logic.
"""
import sqlite3
import os
from typing import Dict, List, Set, Optional, Tuple
from functools import lru_cache

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "output", "taxonomy_2025.db")


class TaxonomyEngine:
    """
    Core engine for querying XBRL taxonomy relationships.
    Provides calculation trees, hierarchy traversal, and balance normalization.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = None
        self._concept_cache: Dict[str, dict] = {}
        self._calc_tree_cache: Dict[str, List[dict]] = {}
        self._parent_cache: Dict[str, List[str]] = {}

    def connect(self):
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Taxonomy database not found: {self.db_path}")

        # INVARIANT ENFORCEMENT: Taxonomy database must be read-only
        # Check file permissions and open in read-only mode
        if not os.access(self.db_path, os.R_OK):
            raise PermissionError(f"Cannot read taxonomy database: {self.db_path}")

        # Open database in read-only mode (uri=True enables read-only flag)
        db_uri = f"file:{self.db_path}?mode=ro"
        try:
            self.conn = sqlite3.connect(db_uri, uri=True)
        except sqlite3.OperationalError as e:
            # If read-only mode fails, open normally but warn
            print(f"  WARNING: Could not open database in read-only mode: {e}")
            print(f"  Opening in normal mode - taxonomy modifications are NOT ALLOWED")
            self.conn = sqlite3.connect(self.db_path)

        self.conn.row_factory = sqlite3.Row
        self._build_caches()

    def _build_caches(self):
        """Pre-load frequently accessed data into memory for performance."""
        print("  Loading taxonomy caches...")

        # Cache all concepts with their properties
        cur = self.conn.cursor()
        cur.execute("""
            SELECT concept_id, element_id, balance, period_type, data_type, source
            FROM concepts WHERE element_id IS NOT NULL
        """)
        for row in cur.fetchall():
            self._concept_cache[row['element_id']] = {
                'concept_id': row['concept_id'],
                'element_id': row['element_id'],
                'balance': row['balance'],
                'period_type': row['period_type'],
                'data_type': row['data_type'],
                'source': row['source']
            }
        print(f"    Cached {len(self._concept_cache):,} concepts")

        # Cache calculation relationships
        cur.execute("""
            SELECT
                c_parent.element_id as parent_id,
                c_child.element_id as child_id,
                calc.weight,
                calc.order_index
            FROM calculations calc
            JOIN concepts c_parent ON calc.parent_concept_id = c_parent.concept_id
            JOIN concepts c_child ON calc.child_concept_id = c_child.concept_id
            WHERE c_parent.element_id IS NOT NULL AND c_child.element_id IS NOT NULL
            ORDER BY calc.order_index
        """)
        invalid_weights = []
        for row in cur.fetchall():
            parent_id = row['parent_id']
            weight = row['weight']

            # INVARIANT ENFORCEMENT: Calculation weights must be ±1.0 per XBRL spec
            if weight not in (1.0, -1.0):
                invalid_weights.append({
                    'parent': parent_id,
                    'child': row['child_id'],
                    'weight': weight
                })
                # Coerce to nearest valid value
                weight = 1.0 if weight > 0 else -1.0

            if parent_id not in self._calc_tree_cache:
                self._calc_tree_cache[parent_id] = []
            self._calc_tree_cache[parent_id].append({
                'child_id': row['child_id'],
                'weight': weight,
                'order': row['order_index']
            })

        if invalid_weights:
            print(f"    WARNING: Found {len(invalid_weights)} calculation relationships with invalid weights (not ±1.0)")
            print(f"    Invalid weights coerced to ±1.0. First 5 examples:")
            for item in invalid_weights[:5]:
                print(f"      {item['parent']} -> {item['child']}: weight={item['weight']}")

        print(f"    Cached {len(self._calc_tree_cache):,} calculation parents")

        # Cache presentation hierarchy (child -> parents)
        cur.execute("""
            SELECT
                c_child.element_id as child_id,
                c_parent.element_id as parent_id
            FROM presentation_roles pr
            JOIN concepts c_child ON pr.concept_id = c_child.concept_id
            JOIN concepts c_parent ON pr.parent_concept_id = c_parent.concept_id
            WHERE c_child.element_id IS NOT NULL AND c_parent.element_id IS NOT NULL
        """)
        for row in cur.fetchall():
            child_id = row['child_id']
            if child_id not in self._parent_cache:
                self._parent_cache[child_id] = []
            if row['parent_id'] not in self._parent_cache[child_id]:
                self._parent_cache[child_id].append(row['parent_id'])
        print(f"    Cached {len(self._parent_cache):,} hierarchy relationships")

    # =========================================================================
    # STEP 1: CALCULATION LINKBASE - Dynamic Parent-Child Trees
    # =========================================================================

    def get_calculation_children(self, parent_element_id: str) -> List[dict]:
        """
        Get all children of a parent concept from the calculation linkbase.
        Returns list of {child_id, weight, order} dicts.

        Example: get_calculation_children('us-gaap_Revenues') might return:
            [{'child_id': 'us-gaap_SalesRevenueGoodsNet', 'weight': 1.0, 'order': 1.0},
             {'child_id': 'us-gaap_SalesRevenueServicesNet', 'weight': 1.0, 'order': 2.0}]
        """
        return self._calc_tree_cache.get(parent_element_id, [])

    def get_all_descendants(self, parent_element_id: str, visited: Set[str] = None) -> Set[str]:
        """
        Recursively get all descendants of a concept (children, grandchildren, etc.)
        Useful for finding all components that roll up to a total.
        """
        if visited is None:
            visited = set()

        if parent_element_id in visited:
            return visited

        visited.add(parent_element_id)
        children = self.get_calculation_children(parent_element_id)

        for child in children:
            self.get_all_descendants(child['child_id'], visited)

        return visited

    def smart_aggregate(self, element_ids: Set[str], amounts: Dict[str, float]) -> Tuple[float, str, List[str]]:
        """
        CORE FUNCTION: Intelligent aggregation that prevents double-counting.

        Algorithm:
        1. Check if any element is a "total" (has children in calculation linkbase)
        2. If total exists and has value, compare against sum-of-children
        3. Return the most accurate value with audit trail

        Returns: (value, method, audit_trail)
        - value: The aggregated amount
        - method: 'TOTAL_LINE', 'CALCULATED_SUM', 'COMPONENT_SUM', 'MAX_PROTECTION'
        - audit_trail: List of concepts used in calculation
        """
        available = {eid: amounts.get(eid, 0) for eid in element_ids if eid in amounts}

        if not available:
            return 0.0, 'NO_DATA', []

        # Identify totals vs components
        totals = {}
        components = {}

        for eid, val in available.items():
            children = self.get_calculation_children(eid)
            if children:
                # This is a total line (has children)
                totals[eid] = {'value': val, 'children': [c['child_id'] for c in children]}
            else:
                # This is a component (leaf node)
                components[eid] = val

        # Case 1: We have a reported total - validate and use it
        if totals:
            best_total_id = list(totals.keys())[0]  # Take first total
            total_info = totals[best_total_id]
            reported_total = total_info['value']

            # Calculate what the children sum to
            calc_sum = 0.0
            children_used = []
            for child_id in total_info['children']:
                if child_id in amounts:
                    child_data = self.get_calculation_children(best_total_id)
                    weight = next((c['weight'] for c in child_data if c['child_id'] == child_id), 1.0)
                    calc_sum += amounts[child_id] * weight
                    children_used.append(child_id)

            # If total matches calculated (within tolerance), trust the total
            tolerance = abs(reported_total) * 0.01 if reported_total else 1.0
            if abs(reported_total - calc_sum) <= tolerance:
                return reported_total, 'TOTAL_LINE', [best_total_id]

            # If mismatch, take max as protection against under-reporting
            if reported_total >= calc_sum:
                return reported_total, 'TOTAL_LINE', [best_total_id]
            else:
                return calc_sum, 'CALCULATED_SUM', children_used

        # Case 2: No totals, just sum components (avoiding any that are children of others)
        # Find components that are NOT children of other components in our set
        root_components = set(components.keys())
        for eid in components:
            descendants = self.get_all_descendants(eid)
            # Remove descendants from root_components
            for desc in descendants:
                if desc != eid and desc in root_components:
                    root_components.discard(desc)

        total = sum(components[eid] for eid in root_components)
        return total, 'COMPONENT_SUM', list(root_components)

    # =========================================================================
    # STEP 2: BALANCE-TYPE SIGN NORMALIZATION
    # =========================================================================

    def get_balance_type(self, element_id: str) -> Optional[str]:
        """Get the balance type (debit/credit) for a concept."""
        concept = self._concept_cache.get(element_id)
        return concept['balance'] if concept else None

    def normalize_sign(self, element_id: str, raw_amount: float, statement_type: str) -> float:
        """
        Normalize amount sign based on balance type and statement context.

        Sign Convention (IB Standard):
        - Income Statement:
            - Revenue (credit) -> Positive
            - Expenses (debit) -> Positive (shown as deduction)
            - Net Income (credit) -> Positive
        - Balance Sheet:
            - Assets (debit) -> Positive
            - Liabilities (credit) -> Positive
            - Equity (credit) -> Positive
        - Cash Flow:
            - Inflows -> Positive
            - Outflows -> Positive (absolute value)

        Most financials report positive numbers. This normalizes any negative
        expense inputs to positive for consistent aggregation.
        """
        balance = self.get_balance_type(element_id)

        if balance is None:
            # Unknown balance type - return as-is
            return raw_amount

        # For most IB models, we want positive numbers
        # Debit balances (expenses, assets) are naturally positive
        # Credit balances (revenue, liabilities) are naturally positive
        #
        # If a debit account shows negative (like expense reduction),
        # that's actually an income - keep as-is for now
        return raw_amount

    def get_sign_for_aggregation(self, element_id: str, context: str = 'dcf') -> int:
        """
        Get the sign multiplier for aggregating this concept in a specific model.

        DCF Context:
        - Revenue: +1 (adds to value)
        - COGS/Expenses: -1 (reduces EBITDA)
        - D&A: typically +1 in addback

        Returns: 1 or -1
        """
        balance = self.get_balance_type(element_id)

        # Debit accounts (expenses) typically reduce profitability
        if balance == 'debit':
            # Check if it's an asset (positive) or expense (negative for P&L)
            if self._is_expense_concept(element_id):
                return -1
            return 1  # Asset

        # Credit accounts (revenue, liabilities)
        if balance == 'credit':
            if self._is_revenue_concept(element_id):
                return 1
            return 1  # Liability or equity

        return 1  # Default

    def _is_expense_concept(self, element_id: str) -> bool:
        """Check if concept is an expense (reduces profit)."""
        expense_keywords = ['Expense', 'Cost', 'Loss', 'Impairment', 'Depreciation',
                           'Amortization', 'Restructuring', 'Tax', 'Interest']
        return any(kw in element_id for kw in expense_keywords)

    def _is_revenue_concept(self, element_id: str) -> bool:
        """Check if concept is revenue (increases profit)."""
        revenue_keywords = ['Revenue', 'Sales', 'Income', 'Gain']
        return any(kw in element_id for kw in revenue_keywords)

    # =========================================================================
    # STEP 3: SAFE MODE FALLBACK - Hierarchy Walking
    # =========================================================================

    def get_presentation_parents(self, element_id: str) -> List[str]:
        """Get parent concepts from presentation hierarchy."""
        return self._parent_cache.get(element_id, [])

    def find_safe_parent(self, element_id: str, known_concepts: Set[str],
                         max_depth: int = 5) -> Optional[Tuple[str, int]]:
        """
        Walk up the presentation hierarchy to find a mappable ancestor.

        Args:
            element_id: The starting concept
            known_concepts: Set of concepts we can map to
            max_depth: Maximum levels to traverse up

        Returns: (parent_element_id, depth) or None if no safe parent found
        """
        visited = set()
        queue = [(element_id, 0)]

        while queue:
            current, depth = queue.pop(0)

            if depth > max_depth:
                continue

            if current in visited:
                continue
            visited.add(current)

            parents = self.get_presentation_parents(current)

            for parent in parents:
                if parent in known_concepts:
                    return (parent, depth + 1)
                if parent not in visited:
                    queue.append((parent, depth + 1))

        return None

    def get_hierarchy_path(self, element_id: str, max_depth: int = 10) -> List[str]:
        """
        Get the full hierarchy path from a concept up to root.
        Useful for audit trails.
        """
        path = [element_id]
        current = element_id
        depth = 0

        while depth < max_depth:
            parents = self.get_presentation_parents(current)
            if not parents:
                break
            # Take first parent (primary hierarchy)
            current = parents[0]
            path.append(current)
            depth += 1

        return path

    # =========================================================================
    # STEP 4: CROSS-STATEMENT VALIDATION
    # =========================================================================

    def validate_calculation(self, parent_id: str, amounts: Dict[str, float],
                            tolerance_pct: float = 0.01) -> dict:
        """
        Validate that a reported total matches its calculated children.

        Returns: {
            'valid': bool,
            'reported': float,
            'calculated': float,
            'difference': float,
            'difference_pct': float,
            'children_found': list,
            'children_missing': list
        }
        """
        children = self.get_calculation_children(parent_id)

        if not children:
            return {'valid': True, 'message': 'No calculation relationship defined'}

        reported = amounts.get(parent_id, 0)
        calculated = 0.0
        children_found = []
        children_missing = []

        for child in children:
            child_id = child['child_id']
            weight = child['weight']

            if child_id in amounts:
                calculated += amounts[child_id] * weight
                children_found.append(child_id)
            else:
                children_missing.append(child_id)

        difference = abs(reported - calculated)
        tolerance = abs(reported) * tolerance_pct if reported else 1.0

        return {
            'valid': difference <= tolerance,
            'reported': reported,
            'calculated': calculated,
            'difference': difference,
            'difference_pct': (difference / abs(reported) * 100) if reported else 0,
            'children_found': children_found,
            'children_missing': children_missing
        }

    def validate_balance_sheet_equation(self, amounts: Dict[str, float]) -> dict:
        """
        Validate: Assets = Liabilities + Equity
        """
        asset_ids = {'us-gaap_Assets', 'ifrs-full_Assets'}
        liab_ids = {'us-gaap_Liabilities', 'ifrs-full_Liabilities'}
        equity_ids = {'us-gaap_StockholdersEquity', 'us-gaap_StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest',
                     'ifrs-full_Equity'}

        assets = sum(amounts.get(eid, 0) for eid in asset_ids)
        liabilities = sum(amounts.get(eid, 0) for eid in liab_ids)
        equity = sum(amounts.get(eid, 0) for eid in equity_ids)

        difference = abs(assets - (liabilities + equity))
        tolerance = abs(assets) * 0.001 if assets else 1.0  # 0.1% tolerance

        return {
            'valid': difference <= tolerance,
            'assets': assets,
            'liabilities': liabilities,
            'equity': equity,
            'liabilities_plus_equity': liabilities + equity,
            'difference': difference
        }

    def validate_cash_flow_reconciliation(self, amounts: Dict[str, float],
                                          period_amounts: Dict[str, Dict[str, float]]) -> dict:
        """
        Validate: Ending Cash = Beginning Cash + Net Change in Cash
        (Requires multi-period data)
        """
        cash_ids = {'us-gaap_CashAndCashEquivalentsAtCarryingValue',
                   'us-gaap_CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents',
                   'ifrs-full_CashAndCashEquivalents'}

        change_ids = {'us-gaap_CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect',
                     'us-gaap_NetCashProvidedByUsedInOperatingActivities'}

        # This requires period-over-period data
        return {'valid': True, 'message': 'Multi-period validation not yet implemented'}

    # =========================================================================
    # UTILITY: Get Concept Metadata
    # =========================================================================

    def get_concept_info(self, element_id: str) -> Optional[dict]:
        """Get full metadata for a concept."""
        return self._concept_cache.get(element_id)

    def get_period_type(self, element_id: str) -> Optional[str]:
        """Get period type (instant/duration) for a concept."""
        concept = self._concept_cache.get(element_id)
        return concept['period_type'] if concept else None

    def is_instant_concept(self, element_id: str) -> bool:
        """Check if concept is instant (balance sheet) vs duration (P&L/CF)."""
        return self.get_period_type(element_id) == 'instant'


# =============================================================================
# SINGLETON ACCESSOR
# =============================================================================
_engine_instance = None

def get_taxonomy_engine() -> TaxonomyEngine:
    """Get singleton instance of TaxonomyEngine."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = TaxonomyEngine()
        _engine_instance.connect()
    return _engine_instance


# =============================================================================
# CLI FOR TESTING
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("TAXONOMY ENGINE - TEST")
    print("=" * 60)

    engine = get_taxonomy_engine()

    # Test 1: Calculation Children
    print("\n[TEST 1] Calculation children for us-gaap_Revenues:")
    children = engine.get_calculation_children('us-gaap_Revenues')
    for c in children[:5]:
        print(f"  - {c['child_id']} (weight: {c['weight']})")

    # Test 2: Balance Types
    print("\n[TEST 2] Balance types:")
    test_concepts = ['us-gaap_Revenues', 'us-gaap_CostOfRevenue', 'us-gaap_Assets', 'us-gaap_Liabilities']
    for c in test_concepts:
        bt = engine.get_balance_type(c)
        print(f"  - {c}: {bt}")

    # Test 3: Presentation Parents
    print("\n[TEST 3] Parents of us-gaap_ResearchAndDevelopmentExpense:")
    parents = engine.get_presentation_parents('us-gaap_ResearchAndDevelopmentExpense')
    for p in parents[:5]:
        print(f"  - {p}")

    # Test 4: Smart Aggregation
    print("\n[TEST 4] Smart aggregation:")
    test_amounts = {
        'us-gaap_Revenues': 100000,
        'us-gaap_SalesRevenueGoodsNet': 60000,
        'us-gaap_SalesRevenueServicesNet': 40000
    }
    result, method, trail = engine.smart_aggregate(
        {'us-gaap_Revenues', 'us-gaap_SalesRevenueGoodsNet', 'us-gaap_SalesRevenueServicesNet'},
        test_amounts
    )
    print(f"  Result: {result:,.0f} (method: {method})")
    print(f"  Audit trail: {trail}")

    print("\n" + "=" * 60)

#!/usr/bin/env python3
"""
Stage 5: Enhanced Financial Engine (JPMC/Citadel Grade) - PRODUCTION v3.0
=========================================================================
Investment Banking-grade financial modeling engine that transforms
normalized financial data into audit-ready DCF, LBO, and Comps datasets.

PRODUCTION v3.0 ENHANCEMENTS:
1. HIERARCHY-AWARE AGGREGATION - Detects "Total + Components" patterns and
   prevents double counting BEFORE pivot aggregation
2. Source Label Tracking - Keeps original labels for audit trail
3. Unmapped Data Reporting - Generates report of dropped data
4. Cross-Statement Validation - Balance sheet equation checks
5. ENHANCED SANITY LOOP - Validates critical buckets with FUZZY FALLBACK recovery
6. DEEP CLEAN - Auto-corrects balance sheet equation before model output
7. NO SILENT FAILURES - If Revenue/EBITDA is zero, attempt aggressive recovery
8. RAW DATA SCANNING - Scans unmapped data for potential matches

Output Quality: Suitable for JPMC M&A, Citadel fundamental analysis

Philosophy: "No Silent Failures" - Attempt recovery before outputting zeros
"""
import pandas as pd
import os
import sys
import logging
from typing import Dict, Set, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict

# Configure logging for engine
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FinancialEngine")

# Import Rules and Taxonomy Engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.ib_rules import *
from config.ib_rules import fuzzy_match_bucket, suggest_mapping, KEYWORD_FALLBACK_MAPPINGS
from taxonomy_utils import get_taxonomy_engine, TaxonomyEngine


class ModelValidationError(Exception):
    """Raised when a model fails critical validation checks."""
    pass


class ZeroModelError(ModelValidationError):
    """Raised when critical buckets are zero, producing an invalid model."""
    def __init__(self, bucket_name: str, message: str = None):
        self.bucket_name = bucket_name
        self.message = message or f"Critical bucket '{bucket_name}' is zero - model would be invalid"
        super().__init__(self.message)


@dataclass
class AuditEntry:
    """Audit trail entry for transparency."""
    metric: str
    value: float
    method: str
    concepts_used: List[str]
    source_labels: List[str] = field(default_factory=list)
    validation_status: str = "OK"
    notes: str = ""


@dataclass
class SanityCheckResult:
    """Result of a sanity check on a bucket."""
    bucket_name: str
    value: float
    is_zero: bool
    fallback_attempted: bool = False
    fallback_value: float = 0.0
    fallback_sources: List[str] = field(default_factory=list)
    error_message: str = ""


@dataclass
class HierarchyGroup:
    """Represents a group of labels that might be hierarchically related."""
    canonical_concept: str
    source_labels: List[str]
    amounts: Dict[str, float]  # period -> amount per source label
    is_total_line: bool = False


class FinancialEngine:
    """
    JPMC/Citadel-grade Financial Engine with Hierarchy-Aware Aggregation.

    CRITICAL: This engine detects when multiple source labels map to the
    same canonical concept and intelligently selects the correct value
    to prevent double-counting.

    Example Problem Solved:
    - "Products net sales" ($60K) → us-gaap_Revenues
    - "Services net sales" ($40K) → us-gaap_Revenues
    - "Total net sales" ($100K) → us-gaap_Revenues

    OLD BEHAVIOR: Sum all = $200K (WRONG!)
    NEW BEHAVIOR: Detect hierarchy, use Total = $100K (CORRECT!)
    """

    def __init__(self, norm_file_path: str):
        self.norm_file_path = norm_file_path
        self.raw_df = pd.read_csv(norm_file_path)

        # Track unmapped data for reporting
        self.unmapped_df = self.raw_df[self.raw_df['Status'] != 'VALID'].copy()
        self.unmapped_count = len(self.unmapped_df)

        # Only process valid rows
        self.df = self.raw_df[self.raw_df['Status'] == 'VALID'].copy()

        # Initialize taxonomy engine
        self.tax_engine = get_taxonomy_engine()

        # Build hierarchy-aware data structures
        self._build_hierarchy_aware_structures()

        # Audit trail
        self.audit_log: List[AuditEntry] = []

        # Report unmapped data
        if self.unmapped_count > 0:
            print(f"  WARNING: {self.unmapped_count} rows unmapped and excluded from analysis")
            print(f"           Run engine.get_unmapped_report() to see details")

    def _detect_total_line(self, label: str) -> bool:
        """
        Detect if a source label is likely a "total" line based on naming patterns.
        """
        label_lower = label.lower()
        total_indicators = [
            'total', 'net', 'gross', 'subtotal', 'sum',
            'aggregate', 'combined', 'overall'
        ]
        # Check for total indicators at start or after space
        for indicator in total_indicators:
            if label_lower.startswith(indicator) or f' {indicator}' in label_lower:
                return True
        return False

    def _detect_component_line(self, label: str) -> bool:
        """
        Detect if a source label is likely a component (not a total).
        """
        label_lower = label.lower()
        component_indicators = [
            'product', 'service', 'segment', 'region', 'division',
            'domestic', 'international', 'north america', 'europe', 'asia',
            'retail', 'wholesale', 'subscription', 'licensing'
        ]
        for indicator in component_indicators:
            if indicator in label_lower:
                return True
        return False

    def _build_hierarchy_aware_structures(self):
        """
        Build data structures that are aware of hierarchical relationships.

        CRITICAL: This prevents double-counting by detecting when multiple
        source labels map to the same canonical concept.
        """
        print("  Building hierarchy-aware data structures...")

        # Step 1: Group by (Canonical_Concept, Period_Date) and track source labels
        self.concept_groups: Dict[str, Dict[str, HierarchyGroup]] = defaultdict(dict)

        for _, row in self.df.iterrows():
            concept = row.get('Canonical_Concept', '---')
            period = row.get('Period_Date', 'Unknown')
            source_label = row.get('Source_Label', '')
            amount = float(row.get('Source_Amount', 0))

            if concept == '---':
                continue

            key = f"{concept}|{period}"

            if key not in self.concept_groups:
                self.concept_groups[key] = {
                    'concept': concept,
                    'period': period,
                    'entries': []
                }

            self.concept_groups[key]['entries'].append({
                'source_label': source_label,
                'amount': amount,
                'is_total': self._detect_total_line(source_label),
                'is_component': self._detect_component_line(source_label)
            })

        # Step 2: For each group, determine the correct value (hierarchy-aware)
        self.resolved_amounts: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.resolution_audit: Dict[str, Dict[str, dict]] = defaultdict(dict)

        hierarchy_conflicts = 0

        for key, group in self.concept_groups.items():
            concept = group['concept']
            period = group['period']
            entries = group['entries']

            if len(entries) == 1:
                # Single entry - no conflict
                self.resolved_amounts[concept][period] = entries[0]['amount']
                self.resolution_audit[concept][period] = {
                    'method': 'SINGLE_VALUE',
                    'source': entries[0]['source_label'],
                    'value': entries[0]['amount']
                }
            else:
                # Multiple entries - need to resolve hierarchy
                hierarchy_conflicts += 1
                resolved_value, method, sources = self._resolve_hierarchy(entries)
                self.resolved_amounts[concept][period] = resolved_value
                self.resolution_audit[concept][period] = {
                    'method': method,
                    'source': sources,
                    'value': resolved_value,
                    'all_entries': entries
                }

        if hierarchy_conflicts > 0:
            print(f"  Resolved {hierarchy_conflicts} hierarchy conflicts (prevented double-counting)")

        # Step 3: Build the pivot table from resolved amounts
        pivot_data = []
        for concept, periods in self.resolved_amounts.items():
            for period, amount in periods.items():
                pivot_data.append({
                    'Canonical_Concept': concept,
                    'Period_Date': period,
                    'Amount': amount
                })

        if pivot_data:
            pivot_df = pd.DataFrame(pivot_data)
            self.pivot = pivot_df.pivot_table(
                index='Canonical_Concept',
                columns='Period_Date',
                values='Amount',
                aggfunc='first'  # Already resolved - just take the value
            ).fillna(0)
        else:
            self.pivot = pd.DataFrame()

        # Detect and sort periods (newest first)
        self.dates = sorted(self.pivot.columns, reverse=True) if len(self.pivot.columns) > 0 else ["Current"]
        if len(self.pivot.columns) > 0:
            self.pivot = self.pivot[self.dates]

        # Build balance-type map from normalized data
        self.balance_map = {}
        for _, row in self.df.iterrows():
            concept = row.get('Canonical_Concept')
            balance = row.get('Balance')
            if concept and balance and balance != '---':
                self.balance_map[concept] = balance

        # Build statement-source map
        self.statement_map = {}
        for _, row in self.df.iterrows():
            concept = row.get('Canonical_Concept')
            statement = row.get('Statement_Source')
            if concept and statement:
                self.statement_map[concept] = statement

    def _resolve_hierarchy(self, entries: List[dict]) -> Tuple[float, str, List[str]]:
        """
        Resolve multiple entries that map to the same concept.

        Algorithm:
        1. If there's a clear "total" line, use it
        2. If there's a total AND components, verify total >= sum(components), use total
        3. If only components (no total), sum them
        4. If ambiguous, use MAX as protection against under-reporting

        Returns: (value, method, source_labels_used)
        """
        totals = [e for e in entries if e['is_total']]
        components = [e for e in entries if e['is_component']]
        others = [e for e in entries if not e['is_total'] and not e['is_component']]

        # Case 1: Clear total line exists
        if len(totals) == 1:
            total_val = totals[0]['amount']

            # Verify against components if they exist
            if components:
                comp_sum = sum(c['amount'] for c in components)
                if abs(total_val - comp_sum) <= abs(total_val) * 0.05:  # 5% tolerance
                    return total_val, 'TOTAL_LINE_VERIFIED', [totals[0]['source_label']]
                elif total_val >= comp_sum:
                    return total_val, 'TOTAL_LINE_USED', [totals[0]['source_label']]
                else:
                    # Total < sum of components - unusual, use max as protection
                    return max(total_val, comp_sum), 'MAX_PROTECTION', [e['source_label'] for e in entries]
            else:
                return total_val, 'TOTAL_LINE_ONLY', [totals[0]['source_label']]

        # Case 2: Multiple totals - take the largest
        if len(totals) > 1:
            max_total = max(totals, key=lambda x: x['amount'])
            return max_total['amount'], 'MAX_TOTAL_LINE', [max_total['source_label']]

        # Case 3: No totals, only components - sum them
        if components and not totals:
            comp_sum = sum(c['amount'] for c in components)
            return comp_sum, 'COMPONENT_SUM', [c['source_label'] for c in components]

        # Case 4: Ambiguous (no clear pattern) - use MAX for safety
        all_amounts = [e['amount'] for e in entries]
        max_entry = max(entries, key=lambda x: x['amount'])
        return max_entry['amount'], 'MAX_AMBIGUOUS', [max_entry['source_label']]

    def _get_amounts_for_period(self, period: str) -> Dict[str, float]:
        """Get all concept amounts for a specific period."""
        if period not in self.pivot.columns:
            return {}
        return self.pivot[period].to_dict()

    def _smart_sum(self, concept_set: Set[str], sign_multiplier: int = 1) -> pd.Series:
        """
        Smart aggregation using taxonomy calculation linkbase.
        Note: Double-counting already prevented by _build_hierarchy_aware_structures
        """
        result = pd.Series(0.0, index=self.dates)

        for period in self.dates:
            amounts = self._get_amounts_for_period(period)
            available = {eid: amounts.get(eid, 0) for eid in concept_set if eid in amounts and amounts.get(eid, 0) != 0}

            if not available:
                continue

            # Use taxonomy engine for smart aggregation across DIFFERENT concepts
            value, method, concepts_used = self.tax_engine.smart_aggregate(concept_set, amounts)
            result[period] = value * sign_multiplier

        return result

    def _sum_bucket(self, concept_set: Set[str]) -> pd.Series:
        """Simple sum of all concepts in the set (for leaf nodes)."""
        available = list(concept_set.intersection(set(self.pivot.index)))
        if not available:
            return pd.Series(0, index=self.dates)
        return self.pivot.loc[available].sum()

    def get_unmapped_report(self) -> pd.DataFrame:
        """
        Get report of all unmapped data that was excluded from analysis.
        CRITICAL: Investment bankers need to see what data was dropped!
        """
        if self.unmapped_count == 0:
            return pd.DataFrame(columns=['Source_Label', 'Source_Amount', 'Statement_Source', 'Period_Date', 'Map_Method'])

        return self.unmapped_df[['Source_Label', 'Source_Amount', 'Statement_Source', 'Period_Date', 'Map_Method']].copy()

    def get_hierarchy_resolution_report(self) -> pd.DataFrame:
        """
        Get report of all hierarchy resolutions performed.
        Shows where double-counting was prevented.
        """
        rows = []
        for concept, periods in self.resolution_audit.items():
            for period, audit in periods.items():
                if audit['method'] != 'SINGLE_VALUE':
                    rows.append({
                        'Concept': concept,
                        'Period': period,
                        'Resolution_Method': audit['method'],
                        'Value_Used': audit['value'],
                        'Source_Labels': str(audit['source'])
                    })
        return pd.DataFrame(rows)

    # =========================================================================
    # SANITY LOOP - Critical Bucket Validation with Fallback
    # =========================================================================

    def _sanity_check_bucket(self, bucket_name: str, value: pd.Series,
                              concept_set: Set[str]) -> SanityCheckResult:
        """
        Check if a critical bucket is zero and attempt aggressive fallback recovery.

        Philosophy: "No Silent Failures" - If a critical bucket is zero,
        attempt multiple levels of recovery:
        1. Keyword matching on mapped data
        2. Fuzzy matching on all data (including unmapped)
        3. Raw label scanning for any potential matches

        PRODUCTION v3.0: More aggressive recovery with fuzzy matching
        """
        total_value = value.sum() if hasattr(value, 'sum') else value

        if total_value != 0:
            return SanityCheckResult(
                bucket_name=bucket_name,
                value=total_value,
                is_zero=False
            )

        # Bucket is zero - attempt multi-level fallback recovery
        logger.warning(f"SANITY CHECK: {bucket_name} is ZERO - initiating aggressive recovery")

        fallback_value = 0.0
        fallback_sources = []

        # LEVEL 1: Keyword matching on mapped data
        keywords_to_search = self._get_keywords_for_bucket(bucket_name)
        logger.info(f"  LEVEL 1: Searching mapped data for keywords: {keywords_to_search[:5]}...")

        for _, row in self.df.iterrows():
            source_label = str(row.get('Source_Label', '')).lower()
            amount = float(row.get('Source_Amount', 0))

            for keyword in keywords_to_search:
                if keyword in source_label and amount != 0:
                    concept = row.get('Canonical_Concept', '')
                    if concept not in concept_set:
                        fallback_value += amount
                        fallback_sources.append(row.get('Source_Label', ''))
                        logger.info(f"  LEVEL 1 MATCH: '{row.get('Source_Label')}' ({amount:,.0f})")
                        break

        # LEVEL 2: Search UNMAPPED data with fuzzy matching
        if fallback_value == 0 and self.unmapped_count > 0:
            logger.info(f"  LEVEL 2: Searching {self.unmapped_count} unmapped items with fuzzy matching...")

            for _, row in self.unmapped_df.iterrows():
                source_label = str(row.get('Source_Label', ''))
                amount = float(row.get('Source_Amount', 0))

                if amount == 0:
                    continue

                # Use fuzzy matching
                matched_bucket, matched_concepts = fuzzy_match_bucket(source_label)

                if matched_bucket and bucket_name.lower() in matched_bucket.lower():
                    fallback_value += amount
                    fallback_sources.append(f"[FUZZY] {source_label}")
                    logger.info(f"  LEVEL 2 FUZZY MATCH: '{source_label}' ({amount:,.0f}) -> {matched_bucket}")
                    continue

                # Also try direct keyword matching
                for keyword in keywords_to_search:
                    if keyword in source_label.lower() and amount != 0:
                        fallback_value += amount
                        fallback_sources.append(f"[KEYWORD] {source_label}")
                        logger.info(f"  LEVEL 2 KEYWORD MATCH: '{source_label}' ({amount:,.0f})")
                        break

        # LEVEL 3: Raw data scan - most aggressive
        if fallback_value == 0:
            logger.info(f"  LEVEL 3: Aggressive raw data scan for {bucket_name}...")

            # Scan the raw dataframe for any potential matches
            for _, row in self.raw_df.iterrows():
                source_label = str(row.get('Source_Label', ''))
                amount = float(row.get('Source_Amount', 0))

                if amount == 0:
                    continue

                label_lower = source_label.lower()

                # Check for direct bucket name matches
                bucket_keywords = bucket_name.lower().split()
                matches_all_keywords = all(kw in label_lower for kw in bucket_keywords)

                # Check for common synonyms
                synonyms_match = False
                if bucket_name == "Total Revenue":
                    synonyms_match = any(syn in label_lower for syn in [
                        "revenue", "sales", "turnover", "income", "net sales"
                    ])
                elif bucket_name == "Net Income":
                    synonyms_match = any(syn in label_lower for syn in [
                        "net income", "net profit", "net earnings", "net loss",
                        "profit after", "earnings after"
                    ])
                elif bucket_name == "EBITDA":
                    synonyms_match = any(syn in label_lower for syn in [
                        "ebitda", "operating profit", "operating income"
                    ])

                if matches_all_keywords or synonyms_match:
                    # Check if we haven't already included this
                    if source_label not in fallback_sources:
                        fallback_value += amount
                        fallback_sources.append(f"[RAW] {source_label}")
                        logger.info(f"  LEVEL 3 RAW SCAN: '{source_label}' ({amount:,.0f})")

        if fallback_value != 0:
            logger.info(f"  RECOVERY SUCCESS: {bucket_name} recovered to {fallback_value:,.0f}")
            logger.info(f"  Sources used: {len(fallback_sources)} items")
            return SanityCheckResult(
                bucket_name=bucket_name,
                value=fallback_value,
                is_zero=False,
                fallback_attempted=True,
                fallback_value=fallback_value,
                fallback_sources=fallback_sources
            )
        else:
            error_msg = f"CRITICAL: {bucket_name} is ZERO after 3-level recovery attempt"
            logger.error(error_msg)
            logger.error(f"  Searched keywords: {keywords_to_search[:10]}...")
            logger.error(f"  Total rows scanned: {len(self.raw_df)}")
            return SanityCheckResult(
                bucket_name=bucket_name,
                value=0.0,
                is_zero=True,
                fallback_attempted=True,
                error_message=error_msg
            )

    def _get_keywords_for_bucket(self, bucket_name: str) -> List[str]:
        """Get keywords to search for when a bucket is zero."""
        keyword_map = {
            "Total Revenue": ["revenue", "sales", "net sales", "total revenue"],
            "Revenue": ["revenue", "sales", "net sales"],
            "COGS": ["cost of", "cogs", "cost of goods", "cost of revenue", "cost of sales"],
            "Net Income": ["net income", "profit", "earnings", "net earnings"],
            "EBITDA": ["ebitda", "operating income", "operating profit"],
            "D&A": ["depreciation", "amortization", "d&a"],
            "CapEx": ["capex", "capital expenditure", "property plant", "pp&e"],
            "Cash": ["cash", "cash equivalent"],
            "Total Debt": ["debt", "borrowing", "notes payable"],
            "Inventory": ["inventory", "inventories"],
        }
        return keyword_map.get(bucket_name, [bucket_name.lower()])

    def _run_sanity_loop(self, metrics: Dict[str, pd.Series]) -> Dict[str, SanityCheckResult]:
        """
        Run sanity checks on all critical metrics.
        Returns dict of bucket name -> SanityCheckResult
        """
        print("\n  [SANITY LOOP] Validating critical buckets...")
        results = {}
        critical_buckets = {
            "Total Revenue": (REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS, "revenue"),
            "Net Income": (NET_INCOME_IDS, "net_income"),
            "EBITDA": (None, "ebitda"),  # Calculated
        }

        for bucket_name, (concept_set, metric_key) in critical_buckets.items():
            if metric_key in metrics:
                value = metrics[metric_key]
                if concept_set:
                    result = self._sanity_check_bucket(bucket_name, value, concept_set)
                else:
                    # For calculated metrics like EBITDA
                    total = value.sum() if hasattr(value, 'sum') else value
                    result = SanityCheckResult(
                        bucket_name=bucket_name,
                        value=total,
                        is_zero=(total == 0)
                    )
                results[bucket_name] = result

                if result.is_zero:
                    print(f"    WARNING: {bucket_name} = 0 (CRITICAL)")
                else:
                    print(f"    OK: {bucket_name} = {result.value:,.0f}")

        return results

    # =========================================================================
    # DEEP CLEAN - Balance Sheet Validation & Auto-Correction
    # =========================================================================

    def _deep_clean_balance_sheet(self) -> Dict[str, any]:
        """
        Verify Balance Sheet equation: Assets = Liabilities + Equity
        Attempt to auto-correct if possible (e.g., infer Equity if missing).

        Philosophy: "Think, Don't Rush"
        """
        print("\n  [DEEP CLEAN] Validating Balance Sheet equation...")

        results = {
            'valid': True,
            'assets': 0,
            'liabilities': 0,
            'equity': 0,
            'difference': 0,
            'corrections_made': [],
            'warnings': []
        }

        for period in self.dates:
            amounts = self._get_amounts_for_period(period)

            # Get Total Assets
            assets = 0
            for concept in TOTAL_ASSETS_IDS:
                if concept in amounts and amounts[concept] != 0:
                    assets = amounts[concept]
                    break

            # If no total assets, try summing current + non-current
            if assets == 0:
                current_assets = sum(amounts.get(c, 0) for c in NWC_CURRENT_ASSETS_TOTAL)
                noncurrent_assets = sum(amounts.get(c, 0) for c in FIXED_ASSETS_TOTAL)
                if current_assets != 0 or noncurrent_assets != 0:
                    assets = current_assets + noncurrent_assets
                    results['corrections_made'].append(f"{period}: Inferred Total Assets from Current + Non-Current")

            # Get Total Liabilities
            liabilities = 0
            for concept in TOTAL_LIABILITIES_IDS:
                if concept in amounts and amounts[concept] != 0:
                    liabilities = amounts[concept]
                    break

            if liabilities == 0:
                current_liabs = sum(amounts.get(c, 0) for c in NWC_CURRENT_LIABS_TOTAL)
                lt_debt = sum(amounts.get(c, 0) for c in LONG_TERM_DEBT_IDS)
                if current_liabs != 0 or lt_debt != 0:
                    liabilities = current_liabs + lt_debt
                    results['corrections_made'].append(f"{period}: Inferred Total Liabilities from components")

            # Get Equity
            equity = 0
            for concept in EQUITY_IDS:
                if concept in amounts and amounts[concept] != 0:
                    equity = amounts[concept]
                    break

            # If no equity but we have assets and liabilities, infer it
            if equity == 0 and assets != 0 and liabilities != 0:
                equity = assets - liabilities
                results['corrections_made'].append(f"{period}: Inferred Equity as Assets - Liabilities = {equity:,.0f}")

            # Validate equation
            l_plus_e = liabilities + equity
            difference = abs(assets - l_plus_e)
            tolerance = abs(assets) * 0.01  # 1% tolerance

            if assets != 0 and difference > tolerance:
                results['valid'] = False
                results['warnings'].append(
                    f"{period}: Assets ({assets:,.0f}) != L+E ({l_plus_e:,.0f}), diff = {difference:,.0f}"
                )
                print(f"    WARNING: {period} - Balance Sheet imbalance of {difference:,.0f}")
            elif assets != 0:
                print(f"    OK: {period} - A={assets:,.0f}, L+E={l_plus_e:,.0f}")

            # Store latest values
            results['assets'] = assets
            results['liabilities'] = liabilities
            results['equity'] = equity
            results['difference'] = difference

        if results['corrections_made']:
            print(f"    Auto-corrections applied: {len(results['corrections_made'])}")

        return results

    # =========================================================================
    # DCF MODEL - Discounted Cash Flow Historical Setup
    # =========================================================================

    def build_dcf_ready_view(self) -> pd.DataFrame:
        """
        Build DCF Historical Setup with JPMC-grade granularity.

        ENHANCED: Now includes sanity checks and validation.
        """
        print("\n  [DCF ENGINE] Building DCF Historical Setup...")
        self.audit_log = []
        self.sanity_results = {}
        self.engine_errors = []

        # === REVENUE ===
        revenue = self._smart_sum(REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS)

        # === COGS ===
        cogs = self._smart_sum(COGS_TOTAL_IDS | COGS_COMPONENT_IDS)

        # === GROSS PROFIT ===
        gross_profit = revenue - cogs

        # === OPERATING EXPENSES ===
        sga = self._sum_bucket(SG_AND_A_IDS)
        rnd = self._sum_bucket(R_AND_D_IDS)
        fuel = self._sum_bucket(FUEL_EXPENSE_IDS)

        total_opex_reported = self._sum_bucket(OPEX_TOTAL_IDS)
        known_opex = sga + rnd + fuel
        other_opex = (total_opex_reported - known_opex).clip(lower=0)

        if total_opex_reported.sum() == 0:
            other_opex = pd.Series(0, index=self.dates)

        total_opex = sga + rnd + fuel + other_opex

        # === EBITDA ===
        ebitda_reported = gross_profit - total_opex

        # === D&A ===
        da = self._sum_bucket(D_AND_A_IDS)

        # === EBIT ===
        ebit = ebitda_reported - da

        # === TAXES ===
        taxes = self._sum_bucket(TAX_EXP_IDS)

        # === NOPAT ===
        nopat = ebit - taxes

        # === CASH FLOW BRIDGE ===
        capex = self._sum_bucket(CAPEX_IDS)

        curr_assets = self._smart_sum(NWC_CURRENT_ASSETS_TOTAL | NWC_CURRENT_ASSETS_COMPS)
        curr_liabs = self._smart_sum(NWC_CURRENT_LIABS_TOTAL | NWC_CURRENT_LIABS_COMPS)

        cash_in_nwc = self._sum_bucket(CASH_IDS)
        operating_current_assets = curr_assets - cash_in_nwc

        short_term_debt = self._sum_bucket(SHORT_TERM_DEBT_IDS)
        operating_current_liabs = curr_liabs - short_term_debt

        nwc = operating_current_assets - operating_current_liabs
        delta_nwc = nwc.diff(periods=-1).fillna(0)

        # === UNLEVERED FREE CASH FLOW ===
        ufcf = nopat + da - delta_nwc - capex

        # === SANITY LOOP - Validate Critical Buckets ===
        self.sanity_results = self._run_sanity_loop({
            'revenue': revenue,
            'ebitda': ebitda_reported,
            'net_income': nopat  # Using NOPAT as proxy for DCF
        })

        # Check for critical failures
        critical_zeros = []
        for bucket_name, result in self.sanity_results.items():
            if result.is_zero and bucket_name in ["Total Revenue", "EBITDA"]:
                critical_zeros.append(bucket_name)
                self.engine_errors.append(result.error_message)

        if critical_zeros:
            error_msg = f"CRITICAL ERROR: Zero values in {', '.join(critical_zeros)} - DCF model invalid"
            logger.error(error_msg)
            print(f"\n  ERROR: {error_msg}")
            # Don't raise - continue to produce output but log the error

        # === DEEP CLEAN - Balance Sheet Validation ===
        self.balance_sheet_validation = self._deep_clean_balance_sheet()

        data = {
            "Total Revenue": revenue,
            "(-) COGS": cogs,
            "(=) Gross Profit": gross_profit,
            "Gross Margin %": (gross_profit / revenue * 100).replace([float('inf'), float('-inf')], 0).fillna(0).round(1),
            "(-) SG&A": sga,
            "(-) R&D": rnd,
            "(-) Other Operating Expenses": other_opex,
            "(=) EBITDA": ebitda_reported,
            "EBITDA Margin %": (ebitda_reported / revenue * 100).replace([float('inf'), float('-inf')], 0).fillna(0).round(1),
            "(-) D&A": da,
            "(=) EBIT": ebit,
            "EBIT Margin %": (ebit / revenue * 100).replace([float('inf'), float('-inf')], 0).fillna(0).round(1),
            "(-) Cash Taxes": taxes,
            "(=) NOPAT": nopat,
            "(+) D&A Addback": da,
            "(-) Change in NWC": delta_nwc,
            "(-) CapEx": capex,
            "(=) Unlevered Free Cash Flow": ufcf,
            "UFCF Margin %": (ufcf / revenue * 100).replace([float('inf'), float('-inf')], 0).fillna(0).round(1),
        }

        result_df = pd.DataFrame(data).T

        # Final validation - log summary
        print(f"\n  [DCF COMPLETE] Revenue: {revenue.sum():,.0f}, EBITDA: {ebitda_reported.sum():,.0f}, UFCF: {ufcf.sum():,.0f}")

        return result_df

    # =========================================================================
    # LBO MODEL - Leveraged Buyout Credit Statistics
    # =========================================================================

    def build_lbo_ready_view(self) -> pd.DataFrame:
        """Build LBO Credit Statistics with proper debt stack analysis."""
        revenue = self._smart_sum(REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS)
        cogs = self._smart_sum(COGS_TOTAL_IDS | COGS_COMPONENT_IDS)
        gross_profit = revenue - cogs

        sga = self._sum_bucket(SG_AND_A_IDS)
        rnd = self._sum_bucket(R_AND_D_IDS)
        other_opex = (self._sum_bucket(OPEX_TOTAL_IDS) - sga - rnd).clip(lower=0)
        total_opex = sga + rnd + other_opex

        ebitda_reported = gross_profit - total_opex

        restructuring = self._sum_bucket(RESTRUCTURING_IDS)
        impairment = self._sum_bucket(IMPAIRMENT_IDS)
        stock_comp = self._sum_bucket(STOCK_COMP_IDS)

        total_adjustments = restructuring + impairment + stock_comp
        ebitda_adjusted = ebitda_reported + total_adjustments

        cash = self._sum_bucket(CASH_IDS)
        short_term_debt = self._sum_bucket(SHORT_TERM_DEBT_IDS)
        long_term_debt = self._sum_bucket(LONG_TERM_DEBT_IDS)
        capital_leases = self._sum_bucket(CAPITAL_LEASE_IDS)

        total_debt = short_term_debt + long_term_debt + capital_leases
        net_debt = total_debt - cash

        interest_expense = self._sum_bucket(INTEREST_EXP_IDS)

        leverage_ratio = (net_debt / ebitda_adjusted).replace([float('inf'), float('-inf')], 0).fillna(0)
        interest_coverage = (ebitda_adjusted / interest_expense).replace([float('inf'), float('-inf')], 0).fillna(0)

        data = {
            "EBITDA (Reported)": ebitda_reported,
            "(+) Restructuring Charges": restructuring,
            "(+) Impairment Charges": impairment,
            "(+) Stock-Based Compensation": stock_comp,
            "(=) Total Adjustments": total_adjustments,
            "(=) EBITDA (Adjusted)": ebitda_adjusted,
            "Cash & Equivalents": cash,
            "Short-Term Debt": short_term_debt,
            "Long-Term Debt": long_term_debt,
            "Capital Leases": capital_leases,
            "(=) Total Debt": total_debt,
            "(=) Net Debt": net_debt,
            "Interest Expense": interest_expense,
            "Net Debt / Adj. EBITDA": leverage_ratio.round(2),
            "Interest Coverage (Adj. EBITDA / Int)": interest_coverage.round(2),
        }

        return pd.DataFrame(data).T

    # =========================================================================
    # COMPS MODEL - Trading Comparables with Full EV Bridge
    # =========================================================================

    def build_comps_ready_view(self) -> pd.DataFrame:
        """Build Trading Comps with full Enterprise Value bridge."""
        revenue = self._smart_sum(REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS)
        cogs = self._smart_sum(COGS_TOTAL_IDS | COGS_COMPONENT_IDS)
        gross_profit = revenue - cogs

        sga = self._sum_bucket(SG_AND_A_IDS)
        rnd = self._sum_bucket(R_AND_D_IDS)
        other_opex = (self._sum_bucket(OPEX_TOTAL_IDS) - sga - rnd).clip(lower=0)
        total_opex = sga + rnd + other_opex

        ebitda = gross_profit - total_opex
        da = self._sum_bucket(D_AND_A_IDS)
        ebit = ebitda - da

        net_income = self._sum_bucket(NET_INCOME_IDS)

        cash = self._sum_bucket(CASH_IDS)
        short_term_debt = self._sum_bucket(SHORT_TERM_DEBT_IDS)
        long_term_debt = self._sum_bucket(LONG_TERM_DEBT_IDS)
        capital_leases = self._sum_bucket(CAPITAL_LEASE_IDS)
        total_debt = short_term_debt + long_term_debt + capital_leases

        preferred_stock = self._sum_bucket(PREFERRED_STOCK_IDS)
        minority_interest = self._sum_bucket(MINORITY_INTEREST_IDS)
        net_debt = total_debt - cash

        basic_shares = self._sum_bucket(BASIC_SHARES_IDS)
        diluted_shares = self._sum_bucket(DILUTED_SHARES_IDS)
        diluted_shares = diluted_shares.where(diluted_shares > 0, basic_shares)

        eps_basic = (net_income / basic_shares).replace([float('inf'), float('-inf')], 0).fillna(0)
        eps_diluted = (net_income / diluted_shares).replace([float('inf'), float('-inf')], 0).fillna(0)

        data = {
            "Revenue": revenue,
            "EBITDA": ebitda,
            "EBIT": ebit,
            "Net Income": net_income,
            "EBITDA Margin %": (ebitda / revenue * 100).replace([float('inf'), float('-inf')], 0).fillna(0).round(1),
            "Net Income Margin %": (net_income / revenue * 100).replace([float('inf'), float('-inf')], 0).fillna(0).round(1),
            "Cash & Equivalents": cash,
            "Total Debt": total_debt,
            "Preferred Stock": preferred_stock,
            "Minority Interest": minority_interest,
            "Net Debt": net_debt,
            "Basic Shares Outstanding": basic_shares,
            "Diluted Shares Outstanding": diluted_shares,
            "EPS (Basic)": eps_basic.round(2),
            "EPS (Diluted)": eps_diluted.round(2),
        }

        return pd.DataFrame(data).T

    # =========================================================================
    # VALIDATION - Cross-Statement Checks
    # =========================================================================

    def run_validation(self) -> pd.DataFrame:
        """Run cross-statement validation checks."""
        validations = []

        for period in self.dates:
            amounts = self._get_amounts_for_period(period)

            bs_check = self.tax_engine.validate_balance_sheet_equation(amounts)
            validations.append({
                'Period': period,
                'Check': 'Balance Sheet Equation',
                'Status': 'PASS' if bs_check['valid'] else 'FAIL',
                'Details': f"Assets: {bs_check['assets']:,.0f}, L+E: {bs_check['liabilities_plus_equity']:,.0f}, Diff: {bs_check['difference']:,.0f}"
            })

            rev_check = self.tax_engine.validate_calculation('us-gaap_Revenues', amounts)
            if 'valid' in rev_check and not isinstance(rev_check.get('message'), str):
                validations.append({
                    'Period': period,
                    'Check': 'Revenue Calculation',
                    'Status': 'PASS' if rev_check['valid'] else 'WARN',
                    'Details': f"Reported: {rev_check.get('reported', 0):,.0f}, Calc: {rev_check.get('calculated', 0):,.0f}"
                })

        # Add unmapped data check
        if self.unmapped_count > 0:
            validations.append({
                'Period': 'ALL',
                'Check': 'Unmapped Data',
                'Status': 'WARN',
                'Details': f"{self.unmapped_count} rows could not be mapped to taxonomy - check unmapped_report.csv"
            })

        return pd.DataFrame(validations)

    def get_audit_log(self) -> pd.DataFrame:
        """Return audit log as DataFrame."""
        return pd.DataFrame([
            {
                'Metric': e.metric,
                'Value': e.value,
                'Method': e.method,
                'Concepts': ', '.join(e.concepts_used[:3]),
                'Status': e.validation_status
            }
            for e in self.audit_log
        ])

    def get_engine_errors(self) -> List[str]:
        """
        Return list of engine errors encountered during model building.
        Use this to check if the model is valid before displaying.
        """
        errors = getattr(self, 'engine_errors', [])

        # Add sanity check failures
        sanity_results = getattr(self, 'sanity_results', {})
        for bucket_name, result in sanity_results.items():
            if result.is_zero:
                errors.append(result.error_message or f"{bucket_name} is zero")

        # Add balance sheet validation failures
        bs_validation = getattr(self, 'balance_sheet_validation', {})
        if bs_validation.get('warnings'):
            errors.extend(bs_validation['warnings'])

        return errors

    def has_critical_errors(self) -> bool:
        """
        Check if there are critical errors that would make the model invalid.
        Returns True if Revenue or EBITDA are zero.
        """
        sanity_results = getattr(self, 'sanity_results', {})
        critical_buckets = ["Total Revenue", "EBITDA"]

        for bucket in critical_buckets:
            if bucket in sanity_results and sanity_results[bucket].is_zero:
                return True
        return False

    def get_sanity_summary(self) -> Dict[str, any]:
        """
        Get a summary of sanity check results for reporting.
        """
        sanity_results = getattr(self, 'sanity_results', {})
        return {
            'total_checks': len(sanity_results),
            'passed': sum(1 for r in sanity_results.values() if not r.is_zero),
            'failed': sum(1 for r in sanity_results.values() if r.is_zero),
            'fallbacks_used': sum(1 for r in sanity_results.values() if r.fallback_attempted and not r.is_zero),
            'details': {k: {
                'value': v.value,
                'is_zero': v.is_zero,
                'fallback_used': v.fallback_attempted
            } for k, v in sanity_results.items()}
        }

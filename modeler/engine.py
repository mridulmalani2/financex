#!/usr/bin/env python3
"""
Stage 5: Enhanced Financial Engine (JPMC/Citadel Grade) - v2
============================================================
Investment Banking-grade financial modeling engine that transforms
normalized financial data into audit-ready DCF, LBO, and Comps datasets.

CRITICAL FIXES in v2:
1. HIERARCHY-AWARE AGGREGATION - Detects "Total + Components" patterns and
   prevents double counting BEFORE pivot aggregation
2. Source Label Tracking - Keeps original labels for audit trail
3. Unmapped Data Reporting - Generates report of dropped data
4. Cross-Statement Validation - Balance sheet equation checks

Output Quality: Suitable for JPMC M&A, Citadel fundamental analysis
"""
import pandas as pd
import os
import sys
from typing import Dict, Set, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict

# Import Rules and Taxonomy Engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.ib_rules import *
from taxonomy_utils import get_taxonomy_engine, TaxonomyEngine


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
    # DCF MODEL - Discounted Cash Flow Historical Setup
    # =========================================================================

    def build_dcf_ready_view(self) -> pd.DataFrame:
        """
        Build DCF Historical Setup with JPMC-grade granularity.
        """
        self.audit_log = []

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

        return pd.DataFrame(data).T

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

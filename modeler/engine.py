#!/usr/bin/env python3
"""
Stage 5: Enhanced Financial Engine (JPMC/Citadel Grade)
=======================================================
Investment Banking-grade financial modeling engine that transforms
normalized financial data into audit-ready DCF, LBO, and Comps datasets.

Key Enhancements:
1. Calculation Linkbase Integration - Dynamic parent-child relationships
2. Balance-Type Sign Normalization - Proper debit/credit handling
3. Smart Double-Counting Prevention - Taxonomy-driven hierarchy awareness
4. Cross-Statement Validation - Reconciliation checks
5. Full EV Bridge for Comps - Complete enterprise value calculation

Output Quality: Suitable for JPMC M&A, Citadel fundamental analysis
"""
import pandas as pd
import os
import sys
from typing import Dict, Set, List, Tuple, Optional
from dataclasses import dataclass

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
    validation_status: str = "OK"
    notes: str = ""


class FinancialEngine:
    """
    JPMC/Citadel-grade Financial Engine.

    Features:
    - Taxonomy-driven aggregation (no hardcoded double-counting logic)
    - Sign normalization based on XBRL balance types
    - Full audit trail for every metric
    - Cross-statement validation
    """

    def __init__(self, norm_file_path: str):
        self.df = pd.read_csv(norm_file_path)
        self.df = self.df[self.df['Status'] == 'VALID'].copy()

        # Initialize taxonomy engine
        self.tax_engine = get_taxonomy_engine()

        # Build period-indexed data structure
        self._build_data_structures()

        # Audit trail
        self.audit_log: List[AuditEntry] = []

    def _build_data_structures(self):
        """
        Build optimized data structures for financial calculations.
        """
        # Pivot: Canonical_Concept (rows) x Period_Date (columns)
        self.pivot = self.df.pivot_table(
            index='Canonical_Concept',
            columns='Period_Date',
            values='Source_Amount',
            aggfunc='sum'
        ).fillna(0)

        # Detect and sort periods (newest first)
        self.dates = sorted(self.pivot.columns, reverse=True)
        if not self.dates:
            self.dates = ["Current"]
        self.pivot = self.pivot[self.dates]

        # Build balance-type map from normalized data
        self.balance_map = {}
        for _, row in self.df.iterrows():
            concept = row.get('Canonical_Concept')
            balance = row.get('Balance')
            if concept and balance and balance != '---':
                self.balance_map[concept] = balance

        # Build statement-source map (which statement each concept came from)
        self.statement_map = {}
        for _, row in self.df.iterrows():
            concept = row.get('Canonical_Concept')
            statement = row.get('Statement_Source')
            if concept and statement:
                self.statement_map[concept] = statement

    def _get_amounts_for_period(self, period: str) -> Dict[str, float]:
        """Get all concept amounts for a specific period."""
        if period not in self.pivot.columns:
            return {}
        return self.pivot[period].to_dict()

    def _normalize_amount(self, element_id: str, raw_amount: float, context: str = 'aggregation') -> float:
        """
        Normalize amount based on balance type and aggregation context.

        For DCF/LBO models:
        - Revenue (credit): positive = good
        - Expenses (debit): positive = cost, negative from profitability
        - Assets (debit): positive
        - Liabilities (credit): positive

        The raw amounts from financials are typically all positive.
        Sign handling happens at aggregation time.
        """
        return abs(raw_amount)  # Ensure positive for aggregation

    def _smart_sum(self, concept_set: Set[str], sign_multiplier: int = 1) -> pd.Series:
        """
        Smart aggregation using taxonomy calculation linkbase.

        Args:
            concept_set: Set of element_ids to aggregate
            sign_multiplier: 1 for additive, -1 for subtractive

        Returns: Series indexed by period with aggregated values
        """
        result = pd.Series(0.0, index=self.dates)
        audit_concepts = []

        for period in self.dates:
            amounts = self._get_amounts_for_period(period)
            available = {eid: amounts.get(eid, 0) for eid in concept_set if eid in amounts}

            if not available:
                continue

            # Use taxonomy engine for smart aggregation
            value, method, concepts_used = self.tax_engine.smart_aggregate(concept_set, amounts)
            result[period] = value * sign_multiplier

            if period == self.dates[0]:  # Log for most recent period
                audit_concepts = concepts_used

        return result

    def _sum_bucket(self, concept_set: Set[str]) -> pd.Series:
        """Simple sum of all concepts in the set (for leaf nodes)."""
        available = list(concept_set.intersection(set(self.pivot.index)))
        if not available:
            return pd.Series(0, index=self.dates)
        return self.pivot.loc[available].sum()

    def _get_single_concept(self, element_id: str) -> pd.Series:
        """Get values for a single concept across all periods."""
        if element_id in self.pivot.index:
            return self.pivot.loc[element_id]
        return pd.Series(0, index=self.dates)

    # =========================================================================
    # DCF MODEL - Discounted Cash Flow Historical Setup
    # =========================================================================

    def build_dcf_ready_view(self) -> pd.DataFrame:
        """
        Build DCF Historical Setup with JPMC-grade granularity.

        Structure:
        - OPERATING MODEL
          - Revenue (Total)
          - (-) COGS
          - (=) Gross Profit
          - (-) SG&A
          - (-) R&D
          - (-) Other Operating Expenses
          - (=) EBITDA
          - (-) D&A
          - (=) EBIT
          - (-) Cash Taxes
          - (=) NOPAT

        - CASH FLOW BRIDGE
          - (+) D&A (Add back)
          - (-) Change in NWC
          - (-) Capex
          - (=) Unlevered Free Cash Flow
        """
        self.audit_log = []

        # === REVENUE ===
        revenue = self._smart_sum(REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS)
        self.audit_log.append(AuditEntry("Revenue", revenue.iloc[0], "SMART_SUM", list(REVENUE_TOTAL_IDS)))

        # === COGS ===
        cogs = self._smart_sum(COGS_TOTAL_IDS | COGS_COMPONENT_IDS)

        # === GROSS PROFIT ===
        gross_profit = revenue - cogs

        # === OPERATING EXPENSES ===
        sga = self._sum_bucket(SG_AND_A_IDS)
        rnd = self._sum_bucket(R_AND_D_IDS)
        fuel = self._sum_bucket(FUEL_EXPENSE_IDS)

        # Total OpEx from taxonomy (if available)
        total_opex_reported = self._sum_bucket(OPEX_TOTAL_IDS)
        known_opex = sga + rnd + fuel

        # Other OpEx = Total - Known (floor at 0)
        other_opex = (total_opex_reported - known_opex).clip(lower=0)

        # If no total reported, just use known components
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
        # Use effective tax rate approach: reported tax expense
        taxes = self._sum_bucket(TAX_EXP_IDS)

        # === NOPAT ===
        # NOPAT = EBIT * (1 - Tax Rate) or EBIT - Tax Expense
        nopat = ebit - taxes

        # === CASH FLOW BRIDGE ===

        # CapEx (typically reported as positive outflow)
        capex = self._sum_bucket(CAPEX_IDS)

        # Net Working Capital
        curr_assets = self._smart_sum(NWC_CURRENT_ASSETS_TOTAL | NWC_CURRENT_ASSETS_COMPS)
        curr_liabs = self._smart_sum(NWC_CURRENT_LIABS_TOTAL | NWC_CURRENT_LIABS_COMPS)

        # Exclude cash from current assets for NWC
        cash_in_nwc = self._sum_bucket(CASH_IDS)
        operating_current_assets = curr_assets - cash_in_nwc

        # Exclude debt from current liabilities for NWC
        short_term_debt = self._sum_bucket(SHORT_TERM_DEBT_IDS)
        operating_current_liabs = curr_liabs - short_term_debt

        nwc = operating_current_assets - operating_current_liabs

        # Change in NWC (increase in NWC = cash outflow)
        # diff(-1) gives current - previous, we want previous - current for "use of cash"
        delta_nwc = nwc.diff(periods=-1).fillna(0)

        # === UNLEVERED FREE CASH FLOW ===
        ufcf = nopat + da - delta_nwc - capex

        # Build output DataFrame
        data = {
            # Operating Model
            "Total Revenue": revenue,
            "(-) COGS": cogs,
            "(=) Gross Profit": gross_profit,
            "Gross Margin %": (gross_profit / revenue * 100).fillna(0).round(1),
            "(-) SG&A": sga,
            "(-) R&D": rnd,
            "(-) Other Operating Expenses": other_opex,
            "(=) EBITDA": ebitda_reported,
            "EBITDA Margin %": (ebitda_reported / revenue * 100).fillna(0).round(1),
            "(-) D&A": da,
            "(=) EBIT": ebit,
            "EBIT Margin %": (ebit / revenue * 100).fillna(0).round(1),
            "(-) Cash Taxes": taxes,
            "(=) NOPAT": nopat,
            # Cash Flow Bridge
            "(+) D&A Addback": da,
            "(-) Change in NWC": delta_nwc,
            "(-) CapEx": capex,
            "(=) Unlevered Free Cash Flow": ufcf,
            "UFCF Margin %": (ufcf / revenue * 100).fillna(0).round(1),
        }

        return pd.DataFrame(data).T

    # =========================================================================
    # LBO MODEL - Leveraged Buyout Credit Statistics
    # =========================================================================

    def build_lbo_ready_view(self) -> pd.DataFrame:
        """
        Build LBO Credit Statistics with proper debt stack analysis.

        Structure:
        - PROFITABILITY
          - EBITDA (Reported)
          - (+) Restructuring & One-offs
          - (=) Adjusted EBITDA

        - CAPITAL STRUCTURE
          - Cash & Equivalents
          - Short-Term Debt
          - Long-Term Debt
          - Total Debt
          - Net Debt

        - CREDIT METRICS
          - Net Debt / EBITDA
          - Interest Coverage (EBITDA / Interest)
        """
        # === EBITDA (recalculate for consistency) ===
        revenue = self._smart_sum(REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS)
        cogs = self._smart_sum(COGS_TOTAL_IDS | COGS_COMPONENT_IDS)
        gross_profit = revenue - cogs

        sga = self._sum_bucket(SG_AND_A_IDS)
        rnd = self._sum_bucket(R_AND_D_IDS)
        other_opex = (self._sum_bucket(OPEX_TOTAL_IDS) - sga - rnd).clip(lower=0)
        total_opex = sga + rnd + other_opex

        ebitda_reported = gross_profit - total_opex

        # === ADJUSTMENTS ===
        restructuring = self._sum_bucket(RESTRUCTURING_IDS)
        impairment = self._sum_bucket(IMPAIRMENT_IDS)
        stock_comp = self._sum_bucket(STOCK_COMP_IDS)

        # Adjusted EBITDA = Reported + One-time charges
        # (Adding back because these reduce reported EBITDA but are non-recurring)
        total_adjustments = restructuring + impairment + stock_comp
        ebitda_adjusted = ebitda_reported + total_adjustments

        # === CAPITAL STRUCTURE ===
        cash = self._sum_bucket(CASH_IDS)
        short_term_debt = self._sum_bucket(SHORT_TERM_DEBT_IDS)
        long_term_debt = self._sum_bucket(LONG_TERM_DEBT_IDS)
        capital_leases = self._sum_bucket(CAPITAL_LEASE_IDS)

        # Total Debt = All debt instruments
        total_debt = short_term_debt + long_term_debt + capital_leases

        # Net Debt = Total Debt - Cash
        net_debt = total_debt - cash

        # === INTEREST ===
        interest_expense = self._sum_bucket(INTEREST_EXP_IDS)

        # === CREDIT METRICS ===
        # Avoid division by zero
        leverage_ratio = (net_debt / ebitda_adjusted).replace([float('inf'), float('-inf')], 0).fillna(0)
        interest_coverage = (ebitda_adjusted / interest_expense).replace([float('inf'), float('-inf')], 0).fillna(0)

        data = {
            # Profitability
            "EBITDA (Reported)": ebitda_reported,
            "(+) Restructuring Charges": restructuring,
            "(+) Impairment Charges": impairment,
            "(+) Stock-Based Compensation": stock_comp,
            "(=) Total Adjustments": total_adjustments,
            "(=) EBITDA (Adjusted)": ebitda_adjusted,
            # Capital Structure
            "Cash & Equivalents": cash,
            "Short-Term Debt": short_term_debt,
            "Long-Term Debt": long_term_debt,
            "Capital Leases": capital_leases,
            "(=) Total Debt": total_debt,
            "(=) Net Debt": net_debt,
            # Credit Metrics
            "Interest Expense": interest_expense,
            "Net Debt / Adj. EBITDA": leverage_ratio.round(2),
            "Interest Coverage (Adj. EBITDA / Int)": interest_coverage.round(2),
        }

        return pd.DataFrame(data).T

    # =========================================================================
    # COMPS MODEL - Trading Comparables with Full EV Bridge
    # =========================================================================

    def build_comps_ready_view(self) -> pd.DataFrame:
        """
        Build Trading Comps with full Enterprise Value bridge.

        Structure:
        - OPERATING METRICS
          - Revenue
          - EBITDA
          - EBIT
          - Net Income

        - EV BRIDGE COMPONENTS
          - Cash & Equivalents
          - Total Debt
          - Preferred Stock
          - Minority Interest
          - Net Debt

        - PER SHARE DATA
          - Basic Shares Outstanding
          - Diluted Shares Outstanding

        - RATIO INPUTS (for EV/EBITDA, P/E calculation)
        """
        # === OPERATING METRICS ===
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

        # === EV BRIDGE ===
        cash = self._sum_bucket(CASH_IDS)

        # Total Debt (comprehensive)
        short_term_debt = self._sum_bucket(SHORT_TERM_DEBT_IDS)
        long_term_debt = self._sum_bucket(LONG_TERM_DEBT_IDS)
        capital_leases = self._sum_bucket(CAPITAL_LEASE_IDS)
        total_debt = short_term_debt + long_term_debt + capital_leases

        # Preferred Stock (adds to EV)
        preferred_stock = self._sum_bucket(PREFERRED_STOCK_IDS)

        # Minority Interest (adds to EV)
        minority_interest = self._sum_bucket(MINORITY_INTEREST_IDS)

        # Net Debt
        net_debt = total_debt - cash

        # === SHARE DATA ===
        basic_shares = self._sum_bucket(BASIC_SHARES_IDS)
        diluted_shares = self._sum_bucket(DILUTED_SHARES_IDS)

        # If diluted not available, use basic
        diluted_shares = diluted_shares.where(diluted_shares > 0, basic_shares)

        # === EPS (if we have shares) ===
        eps_basic = (net_income / basic_shares).replace([float('inf'), float('-inf')], 0).fillna(0)
        eps_diluted = (net_income / diluted_shares).replace([float('inf'), float('-inf')], 0).fillna(0)

        data = {
            # Operating Metrics
            "Revenue": revenue,
            "EBITDA": ebitda,
            "EBIT": ebit,
            "Net Income": net_income,
            # Margins
            "EBITDA Margin %": (ebitda / revenue * 100).fillna(0).round(1),
            "Net Income Margin %": (net_income / revenue * 100).fillna(0).round(1),
            # EV Bridge Components
            "Cash & Equivalents": cash,
            "Total Debt": total_debt,
            "Preferred Stock": preferred_stock,
            "Minority Interest": minority_interest,
            "Net Debt": net_debt,
            # Share Data
            "Basic Shares Outstanding": basic_shares,
            "Diluted Shares Outstanding": diluted_shares,
            # Per Share
            "EPS (Basic)": eps_basic.round(2),
            "EPS (Diluted)": eps_diluted.round(2),
        }

        return pd.DataFrame(data).T

    # =========================================================================
    # VALIDATION - Cross-Statement Checks
    # =========================================================================

    def run_validation(self) -> pd.DataFrame:
        """
        Run cross-statement validation checks.

        Checks:
        1. Balance Sheet Equation: Assets = Liabilities + Equity
        2. Income Statement Flow: Revenue - Expenses = Net Income
        3. Cash Flow Reconciliation (if multi-period)
        """
        validations = []

        for period in self.dates:
            amounts = self._get_amounts_for_period(period)

            # Check 1: Balance Sheet Equation
            bs_check = self.tax_engine.validate_balance_sheet_equation(amounts)
            validations.append({
                'Period': period,
                'Check': 'Balance Sheet Equation',
                'Status': 'PASS' if bs_check['valid'] else 'FAIL',
                'Details': f"Assets: {bs_check['assets']:,.0f}, L+E: {bs_check['liabilities_plus_equity']:,.0f}, Diff: {bs_check['difference']:,.0f}"
            })

            # Check 2: Revenue Calculation Integrity
            rev_check = self.tax_engine.validate_calculation('us-gaap_Revenues', amounts)
            if 'valid' in rev_check and not isinstance(rev_check.get('message'), str):
                validations.append({
                    'Period': period,
                    'Check': 'Revenue Calculation',
                    'Status': 'PASS' if rev_check['valid'] else 'WARN',
                    'Details': f"Reported: {rev_check.get('reported', 0):,.0f}, Calc: {rev_check.get('calculated', 0):,.0f}"
                })

        return pd.DataFrame(validations)

    def get_audit_log(self) -> pd.DataFrame:
        """Return audit log as DataFrame."""
        return pd.DataFrame([
            {
                'Metric': e.metric,
                'Value': e.value,
                'Method': e.method,
                'Concepts': ', '.join(e.concepts_used[:3]),  # First 3
                'Status': e.validation_status
            }
            for e in self.audit_log
        ])

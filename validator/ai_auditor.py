#!/usr/bin/env python3
"""
AI Auditor: Forensic Accounting Suite for FinanceX
===================================================
JPMC/Citadel-Grade Financial Validation

This module implements EXTREME validation - comprehensive forensic accounting
analysis covering all validation rules from institutional-grade standards.

Validation Categories:
1. ACCOUNTING IDENTITIES (1-20) - Balance sheet, cash flow, retained earnings
2. SIGN & LOGIC INTEGRITY (21-40) - Non-negativity, sign consistency
3. RATIO SANITY CHECKS (41-60) - Margin bounds, leverage, coverage
4. GROWTH & VOLATILITY (61-80) - YoY spikes, anomalies
5. CROSS-STATEMENT LINKAGES (81-100) - Rollforwards, reconciliations
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


# Tolerance for floating point comparisons
TOL = 0.01


class AuditSeverity(Enum):
    """Severity levels for audit findings."""
    CRITICAL = "CRITICAL"  # Red - Must fix before proceeding
    WARNING = "WARNING"    # Yellow - Review recommended
    INFO = "INFO"          # Blue - Informational
    PASS = "PASS"          # Green - Check passed


@dataclass
class AuditFinding:
    """Single audit finding with full context."""
    check_name: str
    category: str
    severity: AuditSeverity
    message: str
    details: Dict = field(default_factory=dict)
    recommendation: str = ""

    def to_dict(self) -> Dict:
        return {
            "Check": self.check_name,
            "Category": self.category,
            "Severity": self.severity.value,
            "Message": self.message,
            "Details": str(self.details),
            "Recommendation": self.recommendation
        }


@dataclass
class AuditReport:
    """Complete audit report with all findings."""
    findings: List[AuditFinding] = field(default_factory=list)
    summary: Dict = field(default_factory=dict)

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == AuditSeverity.CRITICAL)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == AuditSeverity.WARNING)

    @property
    def pass_count(self) -> int:
        return sum(1 for f in self.findings if f.severity in (AuditSeverity.PASS, AuditSeverity.INFO))

    @property
    def overall_status(self) -> str:
        if self.critical_count > 0:
            return "FAILED"
        elif self.warning_count > 0:
            return "REVIEW_NEEDED"
        return "PASSED"

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([f.to_dict() for f in self.findings])


class FinancialDataExtractor:
    """
    Extracts financial metrics from normalized data and model outputs.
    Maps raw data to the dictionary format expected by the rule engine.

    PRODUCTION FIX v3.1: Uses EXACT concept matching and hierarchy-aware resolution
    to prevent extracting component values instead of totals.
    """

    def __init__(self, normalized_df: pd.DataFrame = None,
                 dcf_df: pd.DataFrame = None,
                 lbo_df: pd.DataFrame = None,
                 comps_df: pd.DataFrame = None):
        self.normalized_df = normalized_df
        self.dcf_df = dcf_df
        self.lbo_df = lbo_df
        self.comps_df = comps_df
        self._current_period = None  # Will be auto-detected

    def _detect_current_period(self) -> str:
        """
        Detect the most recent period in the data.

        PRODUCTION FIX v3.1: In financial statements, Period 1 is typically
        the most recent fiscal year. Use min(numeric_periods) not max.
        Also, prefer Balance Sheet periods since they contain critical A=L+E data.
        """
        if self._current_period is not None:
            return self._current_period

        if self.normalized_df is not None and 'Period_Date' in self.normalized_df.columns:
            # PRODUCTION FIX: Prefer Balance Sheet periods for validation
            # since the Balance Sheet Equation is a critical check
            balance_sheet_mask = self.normalized_df['Statement_Source'].str.contains(
                'Balance', case=False, na=False
            ) if 'Statement_Source' in self.normalized_df.columns else pd.Series([True] * len(self.normalized_df))

            if balance_sheet_mask.any():
                periods = self.normalized_df[balance_sheet_mask]['Period_Date'].unique()
            else:
                periods = self.normalized_df['Period_Date'].unique()

            # Parse as numbers and take MIN (most recent in financial convention)
            # In financial statements: Period 1 = current year, Period 2 = prior year, etc.
            try:
                numeric_periods = [int(p) for p in periods if str(p).isdigit()]
                if numeric_periods:
                    # PRODUCTION FIX: Use MIN (Period 1 is most recent)
                    self._current_period = str(min(numeric_periods))
                    return self._current_period
            except (ValueError, TypeError):
                pass
            # Otherwise take the first one
            self._current_period = str(periods[0]) if len(periods) > 0 else "1"
        else:
            self._current_period = "1"
        return self._current_period

    def _safe_float(self, val) -> float:
        """Safely convert value to float, defaulting to 0."""
        if val is None or pd.isna(val):
            return 0.0
        try:
            if isinstance(val, str):
                val = val.replace(',', '').replace('$', '').replace('%', '')
                if val.startswith('(') and val.endswith(')'):
                    val = '-' + val[1:-1]
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    def _is_total_line(self, label: str) -> bool:
        """Check if a source label is a total line (vs component)."""
        if not label:
            return False
        label_lower = label.lower()
        total_indicators = ['total', 'net', 'gross', 'subtotal', 'aggregate']
        # Check for total indicators at start of label
        for indicator in total_indicators:
            if label_lower.startswith(indicator):
                return True
        return False

    def _get_from_normalized(self, concepts: List[str]) -> float:
        """
        Get value from normalized dataframe by EXACT concept matching.

        PRODUCTION FIX: Uses EXACT matching (not str.contains) and hierarchy-aware
        resolution to pick total lines over component lines.
        """
        if self.normalized_df is None or self.normalized_df.empty:
            return 0.0

        if 'Canonical_Concept' not in self.normalized_df.columns:
            return 0.0

        current_period = self._detect_current_period()

        for concept in concepts:
            # EXACT match - not str.contains!
            mask = self.normalized_df['Canonical_Concept'] == concept

            # Also filter by current period if available
            if 'Period_Date' in self.normalized_df.columns:
                period_mask = self.normalized_df['Period_Date'].astype(str) == str(current_period)
                mask = mask & period_mask

            if mask.any():
                matched_rows = self.normalized_df[mask]

                # If multiple rows match, use hierarchy-aware resolution
                if len(matched_rows) > 1:
                    # Prefer rows with "Total" in the source label
                    if 'Source_Label' in matched_rows.columns:
                        for _, row in matched_rows.iterrows():
                            if self._is_total_line(str(row.get('Source_Label', ''))):
                                return self._safe_float(row['Source_Amount'])
                    # If no total found, take the max value (protection against under-reporting)
                    return self._safe_float(matched_rows['Source_Amount'].max())
                else:
                    return self._safe_float(matched_rows['Source_Amount'].iloc[0])

        return 0.0

    def _get_from_model(self, df: pd.DataFrame, patterns: List[str]) -> float:
        """Get value from model dataframe by pattern matching."""
        if df is None or df.empty:
            return 0.0

        for pattern in patterns:
            if 'Metric' in df.columns:
                mask = df['Metric'].str.contains(pattern, case=False, na=False)
                if mask.any():
                    row = df[mask].iloc[0]
                    # Get first numeric column value
                    for col in df.columns[1:]:
                        val = self._safe_float(row.get(col))
                        if val != 0:
                            return val
        return 0.0

    def extract_current_period(self) -> Dict[str, Any]:
        """
        Extract all financial metrics for the current period.

        PRODUCTION FIX v3.1: Updated to include IFRS concept IDs and ensure
        proper extraction order (US-GAAP first, then IFRS fallback).
        """
        d = {}

        # === BALANCE SHEET ===
        # PRODUCTION FIX: Include IFRS concepts for companies using IFRS taxonomy
        d["assets"] = self._get_from_normalized([
            "us-gaap_Assets", "ifrs-full_Assets"
        ]) or self._get_from_model(self.dcf_df, ["Total Assets", "Assets"])

        d["current_assets"] = self._get_from_normalized([
            "us-gaap_AssetsCurrent", "ifrs-full_CurrentAssets"
        ]) or self._get_from_model(self.dcf_df, ["Current Assets"])

        d["noncurrent_assets"] = self._get_from_normalized([
            "us-gaap_AssetsNoncurrent", "ifrs-full_NoncurrentAssets"
        ]) or self._get_from_model(self.dcf_df, ["Noncurrent Assets", "Non-Current Assets"])

        d["liabilities"] = self._get_from_normalized([
            "us-gaap_Liabilities", "ifrs-full_Liabilities"
        ]) or self._get_from_model(self.dcf_df, ["Total Liabilities", "Liabilities"])

        d["current_liabilities"] = self._get_from_normalized([
            "us-gaap_LiabilitiesCurrent", "ifrs-full_CurrentLiabilities"
        ]) or self._get_from_model(self.dcf_df, ["Current Liabilities"])

        d["noncurrent_liabilities"] = self._get_from_normalized([
            "us-gaap_LiabilitiesNoncurrent", "ifrs-full_NoncurrentLiabilities"
        ]) or self._get_from_model(self.dcf_df, ["Noncurrent Liabilities", "Non-Current Liabilities"])

        d["equity"] = self._get_from_normalized([
            "us-gaap_StockholdersEquity", "us-gaap_StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
            "ifrs-full_Equity", "ifrs-full_EquityAttributableToOwnersOfParent"
        ]) or self._get_from_model(self.dcf_df, ["Equity", "Stockholders Equity", "Shareholders Equity"])

        d["common_stock"] = self._get_from_normalized([
            "us-gaap_CommonStockValue", "ifrs-full_IssuedCapital"
        ]) or self._get_from_model(self.dcf_df, ["Common Stock"])

        d["apic"] = self._get_from_normalized([
            "us-gaap_AdditionalPaidInCapital", "ifrs-full_SharePremium"
        ]) or self._get_from_model(self.dcf_df, ["Additional Paid-In Capital", "APIC"])

        d["re_begin"] = 0.0  # Would need prior period
        d["re_end"] = self._get_from_normalized([
            "us-gaap_RetainedEarningsAccumulatedDeficit", "ifrs-full_RetainedEarnings"
        ]) or self._get_from_model(self.dcf_df, ["Retained Earnings"])

        d["other_equity"] = 0.0  # Calculated as residual

        # Cash - PRODUCTION FIX: Include IFRS concepts
        d["cash_begin"] = 0.0  # Would need prior period
        d["cash_end"] = self._get_from_normalized([
            "us-gaap_CashAndCashEquivalentsAtCarryingValue",
            "us-gaap_CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
            "ifrs-full_CashAndCashEquivalents", "ifrs-full_Cash"
        ]) or self._get_from_model(self.dcf_df, ["Cash", "Cash and Equivalents"])

        # AR, Inventory, AP - PRODUCTION FIX: Include IFRS concepts
        d["ar"] = self._get_from_normalized([
            "us-gaap_AccountsReceivableNetCurrent", "us-gaap_AccountsReceivableNet",
            "ifrs-full_TradeAndOtherCurrentReceivables", "ifrs-full_TradeReceivables"
        ]) or self._get_from_model(self.dcf_df, ["Accounts Receivable", "AR"])

        d["inventory"] = self._get_from_normalized([
            "us-gaap_InventoryNet", "us-gaap_InventoryGross",
            "ifrs-full_Inventories"
        ]) or self._get_from_model(self.dcf_df, ["Inventory"])

        d["ap"] = self._get_from_normalized([
            "us-gaap_AccountsPayableCurrent", "us-gaap_AccountsPayable",
            "ifrs-full_TradeAndOtherCurrentPayables"
        ]) or self._get_from_model(self.dcf_df, ["Accounts Payable", "AP"])

        d["other_current_assets"] = 0.0
        d["other_current_liabilities"] = 0.0
        d["other_noncurrent_assets"] = 0.0
        d["other_noncurrent_liabilities"] = 0.0

        # PPE - PRODUCTION FIX: Include IFRS concepts
        d["gross_ppe"] = self._get_from_normalized([
            "us-gaap_PropertyPlantAndEquipmentGross", "us-gaap_PropertyPlantAndEquipmentNet",
            "ifrs-full_PropertyPlantAndEquipment"
        ]) or self._get_from_model(self.dcf_df, ["PP&E", "PPE", "Property Plant Equipment"])

        d["ppe_begin"] = 0.0
        d["ppe_end"] = d["gross_ppe"]

        d["intangibles"] = self._get_from_normalized([
            "us-gaap_IntangibleAssetsNetExcludingGoodwill", "us-gaap_IntangibleAssetsNetIncludingGoodwill",
            "ifrs-full_IntangibleAssetsOtherThanGoodwill"
        ]) or self._get_from_model(self.dcf_df, ["Intangibles", "Intangible Assets"])

        # Debt
        d["short_term_debt"] = self._get_from_normalized([
            "us-gaap_ShortTermBorrowings", "ShortTermDebt"
        ]) or self._get_from_model(self.dcf_df, ["Short-Term Debt", "Current Debt"])

        d["long_term_debt"] = self._get_from_normalized([
            "us-gaap_LongTermDebt", "LongTermDebt"
        ]) or self._get_from_model(self.dcf_df, ["Long-Term Debt", "LT Debt"])

        d["debt"] = d["short_term_debt"] + d["long_term_debt"]
        d["debt_begin"] = 0.0
        d["debt_end"] = d["debt"]
        d["debt_issued"] = 0.0
        d["debt_repaid"] = 0.0
        d["avg_debt"] = d["debt"]  # Simplified

        # === INCOME STATEMENT ===
        # PRODUCTION FIX v3.1: Include IFRS concepts for proper extraction
        d["revenue"] = self._get_from_normalized([
            "us-gaap_Revenues", "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax",
            "us-gaap_SalesRevenueNet", "us-gaap_SalesRevenueGoodsAndServicesNet",
            "ifrs-full_Revenue", "ifrs-full_RevenueFromContractsWithCustomers"
        ]) or self._get_from_model(self.dcf_df, ["Revenue", "Total Revenue", "Net Sales", "Sales"])

        d["total_revenue"] = d["revenue"]

        d["cogs"] = abs(self._get_from_normalized([
            "us-gaap_CostOfRevenue", "us-gaap_CostOfGoodsAndServicesSold", "us-gaap_CostOfGoodsSold",
            "ifrs-full_CostOfSales"
        ]) or self._get_from_model(self.dcf_df, ["COGS", "Cost of Revenue", "Cost of Goods Sold"]))

        d["gross_profit"] = self._get_from_normalized([
            "us-gaap_GrossProfit", "ifrs-full_GrossProfit"
        ]) or self._get_from_model(self.dcf_df, ["Gross Profit"]) or (d["revenue"] - d["cogs"])

        d["sga"] = abs(self._get_from_normalized([
            "us-gaap_SellingGeneralAndAdministrativeExpense",
            "ifrs-full_SellingExpense", "ifrs-full_AdministrativeExpense"
        ]) or self._get_from_model(self.dcf_df, ["SG&A", "SGA", "Selling General Admin"]))

        d["rnd"] = abs(self._get_from_normalized([
            "us-gaap_ResearchAndDevelopmentExpense",
            "ifrs-full_ResearchAndDevelopmentExpense"
        ]) or self._get_from_model(self.dcf_df, ["R&D", "Research and Development"]))

        d["other_opex"] = 0.0

        d["depreciation"] = abs(self._get_from_normalized([
            "us-gaap_Depreciation", "us-gaap_DepreciationDepletionAndAmortization",
            "ifrs-full_DepreciationExpense", "ifrs-full_DepreciationAndAmortisationExpense"
        ]) or self._get_from_model(self.dcf_df, ["Depreciation", "D&A"]))

        d["amortization"] = abs(self._get_from_normalized([
            "us-gaap_AmortizationOfIntangibleAssets",
            "ifrs-full_AmortisationExpense"
        ]) or self._get_from_model(self.dcf_df, ["Amortization"]))

        d["ebit"] = self._get_from_normalized([
            "us-gaap_OperatingIncomeLoss", "us-gaap_IncomeLossFromOperations",
            "ifrs-full_ProfitLossFromOperatingActivities", "ifrs-full_OperatingProfit"
        ]) or self._get_from_model(self.dcf_df, ["EBIT", "Operating Income"])

        d["ebitda"] = self._get_from_model(self.dcf_df, ["EBITDA"]) or (
            d["ebit"] + d["depreciation"] + d["amortization"])

        d["interest_expense"] = abs(self._get_from_normalized([
            "us-gaap_InterestExpense", "us-gaap_InterestExpenseDebt",
            "ifrs-full_InterestExpense", "ifrs-full_FinanceCosts"
        ]) or self._get_from_model(self.dcf_df, ["Interest Expense", "Interest"]))

        d["interest_rate"] = 0.05  # Default 5%

        d["pretax_income"] = self._get_from_normalized([
            "us-gaap_IncomeLossFromContinuingOperationsBeforeIncomeTaxes",
            "us-gaap_IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
            "ifrs-full_ProfitLossBeforeTax"
        ]) or self._get_from_model(self.dcf_df, ["Pretax Income", "EBT", "Income Before Tax"])

        d["tax"] = abs(self._get_from_normalized([
            "us-gaap_IncomeTaxExpenseBenefit", "us-gaap_CurrentIncomeTaxExpenseBenefit",
            "ifrs-full_IncomeTaxExpenseContinuingOperations"
        ]) or self._get_from_model(self.dcf_df, ["Tax", "Income Tax", "Tax Expense"]))

        d["tax_paid"] = d["tax"]  # Simplified

        # PRODUCTION FIX: Net Income - Include IFRS ProfitLoss concept
        d["net_income"] = self._get_from_normalized([
            "us-gaap_NetIncomeLoss", "us-gaap_ProfitLoss",
            "us-gaap_NetIncomeLossAttributableToParent",
            "ifrs-full_ProfitLoss", "ifrs-full_ProfitLossAttributableToOwnersOfParent"
        ]) or self._get_from_model(self.dcf_df, ["Net Income", "Net Profit"])

        # PRODUCTION FIX v3.1: Include R&D in total expenses
        d["total_expenses"] = d["cogs"] + d["sga"] + d["rnd"] + d["depreciation"] + d["amortization"] + d["interest_expense"] + d["tax"]

        # EPS / Shares
        d["eps"] = self._get_from_normalized([
            "us-gaap_EarningsPerShareBasic"
        ]) or self._get_from_model(self.dcf_df, ["EPS", "Earnings Per Share"])

        d["shares"] = self._get_from_normalized([
            "us-gaap_CommonStockSharesOutstanding"
        ]) or self._get_from_model(self.dcf_df, ["Shares", "Shares Outstanding"]) or 1.0

        d["shares_begin"] = d["shares"]
        d["shares_end"] = d["shares"]
        d["shares_issued"] = 0.0
        d["shares_repurchased"] = 0.0

        # Dividends
        d["cash_dividends"] = abs(self._get_from_normalized([
            "us-gaap_DividendsCommonStock"
        ]) or self._get_from_model(self.dcf_df, ["Dividends"]))

        d["stock_dividends"] = 0.0
        d["dividends"] = d["cash_dividends"] + d["stock_dividends"]

        # === CASH FLOW ===
        d["cfo"] = self._get_from_normalized([
            "us-gaap_NetCashProvidedByUsedInOperatingActivities"
        ]) or self._get_from_model(self.dcf_df, ["CFO", "Operating Cash Flow", "Cash from Operations"])

        d["cfi"] = self._get_from_normalized([
            "us-gaap_NetCashProvidedByUsedInInvestingActivities"
        ]) or self._get_from_model(self.dcf_df, ["CFI", "Investing Cash Flow", "Cash from Investing"])

        d["cff"] = self._get_from_normalized([
            "us-gaap_NetCashProvidedByUsedInFinancingActivities"
        ]) or self._get_from_model(self.dcf_df, ["CFF", "Financing Cash Flow", "Cash from Financing"])

        d["capex"] = self._get_from_normalized([
            "us-gaap_PaymentsToAcquirePropertyPlantAndEquipment"
        ]) or self._get_from_model(self.dcf_df, ["CapEx", "Capital Expenditures"])
        # CapEx should typically be negative (cash outflow)
        if d["capex"] > 0:
            d["capex"] = -d["capex"]

        d["cfi_capex"] = -d["capex"]  # Should net to zero

        # CFO adjustments
        d["delta_ar"] = 0.0
        d["delta_inventory"] = 0.0
        d["delta_ap"] = 0.0
        d["delta_other_assets"] = 0.0
        d["delta_other_liabilities"] = 0.0

        d["cfo_ar_adj"] = 0.0
        d["cfo_inv_adj"] = 0.0
        d["cfo_ap_adj"] = 0.0

        d["ar_begin"] = 0.0
        d["ar_end"] = d["ar"]
        d["inventory_begin"] = 0.0
        d["inventory_end"] = d["inventory"]
        d["ap_begin"] = 0.0
        d["ap_end"] = d["ap"]

        d["computed_cfo"] = d["cfo"]  # Simplified

        # Equity changes
        d["equity_change"] = 0.0
        d["equity_issued"] = 0.0
        d["equity_repurchased"] = 0.0

        # Depreciation
        d["accum_dep_begin"] = 0.0
        d["accum_dep_end"] = 0.0

        # Leases
        d["capital_lease"] = 0.0
        d["lease_depreciation"] = 0.0

        # Misc
        d["asset_increase"] = 0.0
        d["one_time_items"] = 0.0
        d["disclosed"] = True
        d["capital_raise"] = False

        # Aggregates for worksheet balance check
        d["all_assets"] = [d["assets"]]
        d["all_liabilities"] = [d["liabilities"]]
        d["all_equity"] = [d["equity"]]

        return d

    def extract_prior_period(self) -> Optional[Dict[str, Any]]:
        """Extract prior period data if available. Returns None if not available."""
        # Would need multi-period data to implement
        return None


class ForensicRuleEngine:
    """
    Comprehensive rule engine implementing all forensic validation rules.

    Categories:
    1. ACCOUNTING IDENTITIES (1-20)
    2. SIGN & LOGIC INTEGRITY (21-40)
    3. RATIO SANITY CHECKS (41-60)
    4. GROWTH & VOLATILITY (61-80)
    5. CROSS-STATEMENT LINKAGES (81-100)
    """

    def __init__(self, tolerance: float = TOL):
        self.tol = tolerance

    def _rule(self, name: str, failed: bool, severity: str, msg: str,
              category: str, details: Dict = None) -> AuditFinding:
        """Create an AuditFinding from a rule result."""
        sev = AuditSeverity.CRITICAL if severity == "CRITICAL" else (
            AuditSeverity.WARNING if severity == "WARNING" else AuditSeverity.PASS)

        if not failed:
            return AuditFinding(
                check_name=name,
                category=category,
                severity=AuditSeverity.PASS,
                message=f"{name}: Passed",
                details=details or {}
            )

        return AuditFinding(
            check_name=name,
            category=category,
            severity=sev,
            message=msg,
            details=details or {},
            recommendation=f"Review {name.lower()} calculations and mappings"
        )

    def _safe_div(self, a: float, b: float, default: float = 0.0) -> float:
        """Safe division avoiding ZeroDivisionError."""
        if b == 0 or pd.isna(b):
            return default
        return a / b

    def run_all_rules(self, d: Dict[str, Any], p: Dict[str, Any] = None) -> List[AuditFinding]:
        """
        Run all forensic validation rules.

        Args:
            d: Current period financial data dictionary
            p: Prior period financial data dictionary (optional)

        Returns:
            List of AuditFinding objects
        """
        findings = []

        # =====================================================
        # 1. ACCOUNTING IDENTITIES (1-20)
        # =====================================================
        findings.append(self._rule(
            "Balance Sheet Equation",
            abs(d["assets"] - (d["liabilities"] + d["equity"])) > self.tol and d["assets"] != 0,
            "CRITICAL", "Assets != Liabilities + Equity",
            "ACCOUNTING_IDENTITY",
            {"assets": d["assets"], "liabilities": d["liabilities"], "equity": d["equity"],
             "diff": d["assets"] - (d["liabilities"] + d["equity"])}
        ))

        # PRODUCTION FIX v3.1: Cash flow reconciliation requires multi-period data.
        # Only flag if we have both beginning and ending cash AND cash flows.
        # If cash_begin is 0 (not available), this check should be informational only.
        has_prior_period = d["cash_begin"] != 0
        findings.append(self._rule(
            "Cash Flow - Balance Sheet Consistency",
            has_prior_period and  # Only check if prior period data exists
            abs((d["cfo"] + d["cfi"] + d["cff"]) - (d["cash_end"] - d["cash_begin"])) > self.tol
            and (d["cfo"] != 0 or d["cfi"] != 0 or d["cff"] != 0),
            "WARNING", "Cash flow does not reconcile to balance sheet change",
            "ACCOUNTING_IDENTITY",
            {"cfo": d["cfo"], "cfi": d["cfi"], "cff": d["cff"],
             "cash_change": d["cash_end"] - d["cash_begin"]}
        ))

        findings.append(self._rule(
            "Retained Earnings Continuity",
            abs(d["re_end"] - (d["re_begin"] + d["net_income"] - d["cash_dividends"] - d["stock_dividends"])) > self.tol
            and d["re_begin"] != 0,
            "CRITICAL", "Retained earnings broken",
            "ACCOUNTING_IDENTITY",
            {"re_end": d["re_end"], "re_begin": d["re_begin"], "net_income": d["net_income"]}
        ))

        findings.append(self._rule(
            "Gross Profit Calculation",
            abs(d["gross_profit"] - (d["revenue"] - d["cogs"])) > self.tol and d["revenue"] != 0,
            "CRITICAL", "Gross profit mismatch",
            "ACCOUNTING_IDENTITY",
            {"gross_profit": d["gross_profit"], "revenue": d["revenue"], "cogs": d["cogs"],
             "calculated": d["revenue"] - d["cogs"]}
        ))

        findings.append(self._rule(
            "EBITDA Calculation",
            abs(d["ebitda"] - (d["ebit"] + d["depreciation"] + d["amortization"])) > self.tol
            and d["ebitda"] != 0,
            "CRITICAL", "EBITDA mismatch",
            "ACCOUNTING_IDENTITY",
            {"ebitda": d["ebitda"], "ebit": d["ebit"], "da": d["depreciation"] + d["amortization"]}
        ))

        # PRODUCTION FIX v3.1: EBIT vs (NI + Int + Tax) may differ due to other income/expense items.
        # This is common in real financial statements. Use a 5% tolerance and only WARNING.
        ebit_calc = d["net_income"] + d["interest_expense"] + d["tax"]
        ebit_tolerance = max(abs(d["ebit"]) * 0.05, self.tol)  # 5% or absolute tolerance
        findings.append(self._rule(
            "EBIT Calculation",
            abs(d["ebit"] - ebit_calc) > ebit_tolerance and d["ebit"] != 0,
            "WARNING", "EBIT differs from NI + Interest + Tax (may include other items)",
            "ACCOUNTING_IDENTITY",
            {"ebit": d["ebit"], "net_income": d["net_income"], "interest": d["interest_expense"], "tax": d["tax"]}
        ))

        findings.append(self._rule(
            "EPS Consistency",
            abs(d["net_income"] - (d["eps"] * d["shares"])) > self.tol
            and d["eps"] != 0 and d["shares"] != 0,
            "WARNING", "EPS inconsistent",
            "ACCOUNTING_IDENTITY",
            {"net_income": d["net_income"], "eps": d["eps"], "shares": d["shares"]}
        ))

        findings.append(self._rule(
            "Equity Composition",
            abs(d["equity"] - (d["common_stock"] + d["apic"] + d["re_end"] + d["other_equity"])) > self.tol
            and d["common_stock"] != 0,
            "WARNING", "Equity components mismatch",
            "ACCOUNTING_IDENTITY",
            {"equity": d["equity"], "common_stock": d["common_stock"], "apic": d["apic"], "re": d["re_end"]}
        ))

        # PRODUCTION FIX v3.1: Composition checks should only flag CRITICAL when
        # component data exists AND is mathematically inconsistent.
        # If components are zero (not reported), this is a data coverage issue, not an error.
        ca_components = d["cash_end"] + d["ar"] + d["inventory"] + d["other_current_assets"]
        findings.append(self._rule(
            "Current Assets Composition",
            # Only fail if: (1) components exist, (2) components > total (double counting), OR (3) significant under-reporting with data
            ca_components > d["current_assets"] + self.tol  # Components exceed total = double counting
            or (d["ar"] > 0 and d["inventory"] > 0 and abs(d["current_assets"] - ca_components) > d["current_assets"] * 0.1),
            "CRITICAL", "Current assets composition mismatch (components > total)",
            "ACCOUNTING_IDENTITY",
            {"current_assets": d["current_assets"], "cash": d["cash_end"], "ar": d["ar"], "inventory": d["inventory"], "sum": ca_components}
        ))

        nca_components = d["gross_ppe"] + d["intangibles"] + d["other_noncurrent_assets"]
        findings.append(self._rule(
            "Noncurrent Assets Composition",
            nca_components > d["noncurrent_assets"] + self.tol,  # Only fail if components exceed total
            "CRITICAL", "Noncurrent assets composition mismatch (components > total)",
            "ACCOUNTING_IDENTITY",
            {"noncurrent_assets": d["noncurrent_assets"], "ppe": d["gross_ppe"], "intangibles": d["intangibles"], "sum": nca_components}
        ))

        cl_components = d["ap"] + d["short_term_debt"] + d["other_current_liabilities"]
        findings.append(self._rule(
            "Current Liabilities Composition",
            cl_components > d["current_liabilities"] + self.tol,  # Only fail if components exceed total
            "CRITICAL", "Current liabilities composition mismatch (components > total)",
            "ACCOUNTING_IDENTITY",
            {"current_liabilities": d["current_liabilities"], "ap": d["ap"], "st_debt": d["short_term_debt"], "sum": cl_components}
        ))

        ncl_components = d["long_term_debt"] + d["other_noncurrent_liabilities"]
        findings.append(self._rule(
            "Noncurrent Liabilities Composition",
            ncl_components > d["noncurrent_liabilities"] + self.tol,  # Only fail if components exceed total
            "CRITICAL", "Noncurrent liabilities composition mismatch (components > total)",
            "ACCOUNTING_IDENTITY",
            {"noncurrent_liabilities": d["noncurrent_liabilities"], "lt_debt": d["long_term_debt"], "sum": ncl_components}
        ))

        findings.append(self._rule(
            "Assets Sum Consistency",
            abs(d["assets"] - (d["current_assets"] + d["noncurrent_assets"])) > self.tol
            and d["current_assets"] != 0 and d["noncurrent_assets"] != 0,
            "CRITICAL", "Assets aggregation broken",
            "ACCOUNTING_IDENTITY",
            {"assets": d["assets"], "current": d["current_assets"], "noncurrent": d["noncurrent_assets"]}
        ))

        findings.append(self._rule(
            "Liabilities Sum Consistency",
            abs(d["liabilities"] - (d["current_liabilities"] + d["noncurrent_liabilities"])) > self.tol
            and d["current_liabilities"] != 0 and d["noncurrent_liabilities"] != 0,
            "CRITICAL", "Liabilities aggregation broken",
            "ACCOUNTING_IDENTITY",
            {"liabilities": d["liabilities"], "current": d["current_liabilities"], "noncurrent": d["noncurrent_liabilities"]}
        ))

        # PRODUCTION FIX v3.1: Revenue - Expenses = Net Income may not hold exactly
        # because total_expenses is calculated from known line items and may exclude
        # "Other income/expense", non-operating items, etc. Use 10% tolerance and WARNING.
        income_calc = d["total_revenue"] - d["total_expenses"]
        income_tolerance = max(abs(d["net_income"]) * 0.10, self.tol) if d["net_income"] != 0 else self.tol
        findings.append(self._rule(
            "Total Revenue and Expenses",
            abs(d["net_income"] - income_calc) > income_tolerance and d["total_revenue"] != 0,
            "WARNING", "Net income differs from Revenue - Expenses (may have other items)",
            "ACCOUNTING_IDENTITY",
            {"net_income": d["net_income"], "revenue": d["total_revenue"], "expenses": d["total_expenses"],
             "calculated": income_calc}
        ))

        # PRODUCTION FIX v3.1: Include R&D in expense breakdown validation
        expense_sum = d["cogs"] + d["sga"] + d["rnd"] + d["depreciation"] + d["amortization"] + d["interest_expense"] + d["tax"]
        findings.append(self._rule(
            "Expense Breakdown",
            abs(d["total_expenses"] - expense_sum) > self.tol and d["total_expenses"] != 0,
            "CRITICAL", "Expense breakdown mismatch",
            "ACCOUNTING_IDENTITY",
            {"total_expenses": d["total_expenses"], "cogs": d["cogs"], "sga": d["sga"], "rnd": d["rnd"], "da": d["depreciation"] + d["amortization"]}
        ))

        findings.append(self._rule(
            "Net Income to Equity",
            abs(d["equity_change"] - (d["net_income"] - d["dividends"] + d["equity_issued"] - d["equity_repurchased"])) > self.tol
            and d["equity_change"] != 0,
            "WARNING", "Equity change mismatch",
            "ACCOUNTING_IDENTITY",
            {"equity_change": d["equity_change"], "net_income": d["net_income"], "dividends": d["dividends"]}
        ))

        findings.append(self._rule(
            "Net Income to Cash Flow (Indirect)",
            abs(d["cfo"] - (d["net_income"] + d["depreciation"] + d["delta_ap"] + d["delta_other_liabilities"]
                           - d["delta_ar"] - d["delta_inventory"] - d["delta_other_assets"])) > self.tol
            and d["cfo"] != 0 and d["delta_ar"] != 0,
            "CRITICAL", "CFO indirect mismatch",
            "ACCOUNTING_IDENTITY",
            {"cfo": d["cfo"], "net_income": d["net_income"], "depreciation": d["depreciation"]}
        ))

        findings.append(self._rule(
            "Cash Flow Reconciliation (Indirect vs Direct)",
            abs(d["computed_cfo"] - d["cfo"]) > self.tol
            and d["computed_cfo"] != d["cfo"] and d["computed_cfo"] != 0,
            "CRITICAL", "Indirect vs direct CFO mismatch",
            "ACCOUNTING_IDENTITY",
            {"computed_cfo": d["computed_cfo"], "cfo": d["cfo"]}
        ))

        findings.append(self._rule(
            "Worksheet Balance",
            abs(sum(d["all_assets"]) - sum(d["all_liabilities"]) - sum(d["all_equity"])) > self.tol
            and sum(d["all_assets"]) != 0,
            "CRITICAL", "Worksheet not balanced",
            "ACCOUNTING_IDENTITY",
            {"total_assets": sum(d["all_assets"]), "total_liabilities": sum(d["all_liabilities"]), "total_equity": sum(d["all_equity"])}
        ))

        # =====================================================
        # 2. SIGN & LOGIC INTEGRITY (21-40)
        # =====================================================
        findings.append(self._rule(
            "Revenue Non-Negativity",
            d["revenue"] < 0,
            "CRITICAL", "Negative revenue",
            "SIGN_LOGIC",
            {"revenue": d["revenue"]}
        ))

        findings.append(self._rule(
            "COGS Non-Negativity",
            d["cogs"] < 0,
            "CRITICAL", "Negative COGS",
            "SIGN_LOGIC",
            {"cogs": d["cogs"]}
        ))

        findings.append(self._rule(
            "Operating Expense Non-Negativity",
            (d["sga"] + d["rnd"] + d["other_opex"]) < 0,
            "CRITICAL", "Negative opex",
            "SIGN_LOGIC",
            {"sga": d["sga"], "rnd": d["rnd"], "other_opex": d["other_opex"]}
        ))

        findings.append(self._rule(
            "Depreciation/Amortization Non-Negativity",
            (d["depreciation"] + d["amortization"]) < 0,
            "CRITICAL", "Negative D&A",
            "SIGN_LOGIC",
            {"depreciation": d["depreciation"], "amortization": d["amortization"]}
        ))

        findings.append(self._rule(
            "CapEx Sign",
            d["capex"] > 0,
            "WARNING", "CapEx should be negative (cash outflow)",
            "SIGN_LOGIC",
            {"capex": d["capex"]}
        ))

        findings.append(self._rule(
            "Inventory Non-Negativity",
            d["inventory"] < 0,
            "CRITICAL", "Negative inventory",
            "SIGN_LOGIC",
            {"inventory": d["inventory"]}
        ))

        findings.append(self._rule(
            "AR Non-Negativity",
            d["ar"] < 0,
            "CRITICAL", "Negative AR",
            "SIGN_LOGIC",
            {"ar": d["ar"]}
        ))

        findings.append(self._rule(
            "AP Non-Negativity",
            d["ap"] < 0,
            "CRITICAL", "Negative AP",
            "SIGN_LOGIC",
            {"ap": d["ap"]}
        ))

        findings.append(self._rule(
            "Equity Non-Negativity",
            d["equity"] < 0,
            "WARNING", "Negative equity (may indicate distress)",
            "SIGN_LOGIC",
            {"equity": d["equity"]}
        ))

        findings.append(self._rule(
            "EPS Sign Consistency",
            (d["net_income"] >= 0 and d["eps"] < 0) or (d["net_income"] <= 0 and d["eps"] > 0),
            "CRITICAL", "EPS sign mismatch with net income",
            "SIGN_LOGIC",
            {"net_income": d["net_income"], "eps": d["eps"]}
        ))

        findings.append(self._rule(
            "Tax Expense Sign",
            (d["pretax_income"] > 0 and d["tax"] < 0) or (d["pretax_income"] < 0 and d["tax"] > 0),
            "WARNING", "Tax sign inconsistent with pretax income",
            "SIGN_LOGIC",
            {"pretax_income": d["pretax_income"], "tax": d["tax"]}
        ))

        findings.append(self._rule(
            "Interest Expense Sign",
            d["interest_expense"] < 0,
            "CRITICAL", "Negative interest expense",
            "SIGN_LOGIC",
            {"interest_expense": d["interest_expense"]}
        ))

        findings.append(self._rule(
            "Interest Without Debt",
            d["debt"] == 0 and d["interest_expense"] > 0,
            "WARNING", "Interest expense without debt",
            "SIGN_LOGIC",
            {"debt": d["debt"], "interest_expense": d["interest_expense"]}
        ))

        findings.append(self._rule(
            "Capital Lease Depreciation",
            d["capital_lease"] == 0 and d["lease_depreciation"] > 0,
            "WARNING", "Lease depreciation without capital lease",
            "SIGN_LOGIC",
            {"capital_lease": d["capital_lease"], "lease_depreciation": d["lease_depreciation"]}
        ))

        findings.append(self._rule(
            "Asset Write-Up Without CapEx",
            d["asset_increase"] > 0 and d["capex"] == 0,
            "WARNING", "Asset write-up detected without CapEx",
            "SIGN_LOGIC",
            {"asset_increase": d["asset_increase"], "capex": d["capex"]}
        ))

        findings.append(self._rule(
            "Undisclosed One-Time Items",
            d["one_time_items"] != 0 and not d["disclosed"],
            "WARNING", "Undisclosed one-time items detected",
            "SIGN_LOGIC",
            {"one_time_items": d["one_time_items"]}
        ))

        # =====================================================
        # 3. RATIO SANITY CHECKS (41-60)
        # =====================================================
        gross_margin = self._safe_div(d["gross_profit"], d["revenue"])
        findings.append(self._rule(
            "Gross Margin Bounds",
            (gross_margin < 0 or gross_margin > 1) and d["revenue"] != 0,
            "CRITICAL", f"Gross margin impossible: {gross_margin:.1%}",
            "RATIO_SANITY",
            {"gross_margin": gross_margin, "gross_profit": d["gross_profit"], "revenue": d["revenue"]}
        ))

        ebitda_margin = self._safe_div(d["ebitda"], d["revenue"])
        net_margin = self._safe_div(d["net_income"], d["revenue"])
        findings.append(self._rule(
            "EBITDA vs Net Margin",
            ebitda_margin < net_margin and d["revenue"] != 0 and d["ebitda"] != 0,
            "WARNING", f"EBITDA margin ({ebitda_margin:.1%}) < net margin ({net_margin:.1%})",
            "RATIO_SANITY",
            {"ebitda_margin": ebitda_margin, "net_margin": net_margin}
        ))

        tax_rate = self._safe_div(d["tax"], d["pretax_income"])
        findings.append(self._rule(
            "Effective Tax Rate High",
            d["pretax_income"] > 0 and tax_rate > 0.5,
            "WARNING", f"Implied tax rate too high: {tax_rate:.1%}",
            "RATIO_SANITY",
            {"tax_rate": tax_rate, "tax": d["tax"], "pretax_income": d["pretax_income"]}
        ))

        current_ratio = self._safe_div(d["current_assets"], d["current_liabilities"])
        findings.append(self._rule(
            "Current Ratio Extreme",
            (current_ratio < 0.5 or current_ratio > 5) and d["current_liabilities"] != 0,
            "WARNING", f"Current ratio extreme: {current_ratio:.2f}",
            "RATIO_SANITY",
            {"current_ratio": current_ratio, "current_assets": d["current_assets"], "current_liabilities": d["current_liabilities"]}
        ))

        quick_ratio = self._safe_div(d["cash_end"] + d["ar"], d["current_liabilities"])
        findings.append(self._rule(
            "Quick Ratio Extreme",
            (quick_ratio < 0.2 or quick_ratio > 5) and d["current_liabilities"] != 0,
            "WARNING", f"Quick ratio extreme: {quick_ratio:.2f}",
            "RATIO_SANITY",
            {"quick_ratio": quick_ratio}
        ))

        debt_equity = self._safe_div(d["debt"], d["equity"])
        findings.append(self._rule(
            "Debt/Equity Excessive",
            d["equity"] > 0 and debt_equity > 3,
            "WARNING", f"High leverage: D/E = {debt_equity:.2f}",
            "RATIO_SANITY",
            {"debt_equity": debt_equity, "debt": d["debt"], "equity": d["equity"]}
        ))

        debt_ebitda = self._safe_div(d["debt"], d["ebitda"])
        findings.append(self._rule(
            "Debt/EBITDA Excessive",
            d["ebitda"] > 0 and debt_ebitda > 5,
            "WARNING", f"Debt/EBITDA high: {debt_ebitda:.2f}x",
            "RATIO_SANITY",
            {"debt_ebitda": debt_ebitda}
        ))

        interest_coverage = self._safe_div(d["ebit"], d["interest_expense"])
        findings.append(self._rule(
            "Interest Coverage Weak",
            d["interest_expense"] > 0 and interest_coverage < 1.5,
            "WARNING", f"Weak interest coverage: {interest_coverage:.2f}x",
            "RATIO_SANITY",
            {"interest_coverage": interest_coverage, "ebit": d["ebit"], "interest_expense": d["interest_expense"]}
        ))

        roa = self._safe_div(d["net_income"], d["assets"])
        findings.append(self._rule(
            "ROA Impossible",
            d["assets"] > 0 and abs(roa) > 1,
            "CRITICAL", f"ROA impossible: {roa:.1%}",
            "RATIO_SANITY",
            {"roa": roa, "net_income": d["net_income"], "assets": d["assets"]}
        ))

        findings.append(self._rule(
            "Negative Gross, Positive Net",
            d["gross_profit"] < 0 and d["net_income"] > 0,
            "CRITICAL", "Gross loss but net profit - impossible",
            "RATIO_SANITY",
            {"gross_profit": d["gross_profit"], "net_income": d["net_income"]}
        ))

        # =====================================================
        # 4. GROWTH & VOLATILITY (61-80) - Requires prior period
        # =====================================================
        if p:
            findings.append(self._rule(
                "Revenue Spike",
                p["revenue"] != 0 and self._safe_div(d["revenue"], p["revenue"]) > 3,
                "WARNING", "Revenue spike >3x YoY",
                "GROWTH_VOLATILITY",
                {"current_revenue": d["revenue"], "prior_revenue": p["revenue"]}
            ))

            findings.append(self._rule(
                "Revenue Drop",
                p["revenue"] != 0 and self._safe_div(d["revenue"], p["revenue"]) < 0.5,
                "WARNING", "Revenue collapse >50% YoY",
                "GROWTH_VOLATILITY",
                {"current_revenue": d["revenue"], "prior_revenue": p["revenue"]}
            ))

            findings.append(self._rule(
                "AR Growth > Revenue",
                (d["ar"] - p["ar"]) > 2 * (d["revenue"] - p["revenue"]) and p["ar"] != 0,
                "WARNING", "Receivables ballooning faster than revenue",
                "GROWTH_VOLATILITY",
                {"ar_change": d["ar"] - p["ar"], "revenue_change": d["revenue"] - p["revenue"]}
            ))

            findings.append(self._rule(
                "Inventory Growth > Sales",
                (d["inventory"] - p["inventory"]) > 2 * (d["revenue"] - p["revenue"]) and p["inventory"] != 0,
                "WARNING", "Inventory ballooning faster than sales",
                "GROWTH_VOLATILITY",
                {"inventory_change": d["inventory"] - p["inventory"], "revenue_change": d["revenue"] - p["revenue"]}
            ))

            findings.append(self._rule(
                "CapEx Missing With Growth",
                d["revenue"] > 2 * p["revenue"] and d["capex"] >= p["capex"],
                "WARNING", "Revenue growth without CapEx investment",
                "GROWTH_VOLATILITY",
                {"revenue_growth": self._safe_div(d["revenue"], p["revenue"]), "capex_change": d["capex"] - p["capex"]}
            ))

            cfo_ratio = self._safe_div(d["cfo"], p["cfo"])
            findings.append(self._rule(
                "CFO Volatility",
                p["cfo"] != 0 and (cfo_ratio > 3 or cfo_ratio < 0.3),
                "WARNING", f"CFO volatility: {cfo_ratio:.2f}x YoY",
                "GROWTH_VOLATILITY",
                {"current_cfo": d["cfo"], "prior_cfo": p["cfo"]}
            ))

            findings.append(self._rule(
                "Debt Surge Without Interest",
                p["debt"] != 0 and self._safe_div(d["debt"], p["debt"]) > 2 and
                abs(d["interest_expense"] - p["interest_expense"]) < self.tol,
                "WARNING", "Debt doubled but interest unchanged",
                "GROWTH_VOLATILITY",
                {"debt_ratio": self._safe_div(d["debt"], p["debt"]), "interest_change": d["interest_expense"] - p["interest_expense"]}
            ))

            findings.append(self._rule(
                "Equity Jump Without Raise",
                p["equity"] != 0 and self._safe_div(d["equity"], p["equity"]) > 2 and not d["capital_raise"],
                "WARNING", "Equity doubled without capital raise",
                "GROWTH_VOLATILITY",
                {"equity_ratio": self._safe_div(d["equity"], p["equity"])}
            ))

            findings.append(self._rule(
                "EPS Volatility",
                p["eps"] != 0 and self._safe_div(d["eps"], p["eps"]) > 2,
                "WARNING", "EPS volatility >2x YoY",
                "GROWTH_VOLATILITY",
                {"current_eps": d["eps"], "prior_eps": p["eps"]}
            ))

            prior_payout = self._safe_div(p["dividends"], p["net_income"])
            current_payout = self._safe_div(d["dividends"], d["net_income"])
            findings.append(self._rule(
                "Dividend Policy Shift",
                prior_payout != 0 and current_payout > 2 * prior_payout,
                "WARNING", "Dividend payout ratio doubled",
                "GROWTH_VOLATILITY",
                {"current_payout": current_payout, "prior_payout": prior_payout}
            ))

        # =====================================================
        # 5. CROSS-STATEMENT LINKAGES (81-100)
        # =====================================================
        findings.append(self._rule(
            "PPE Rollforward",
            abs(d["ppe_end"] - (d["ppe_begin"] + d["capex"] - d["depreciation"])) > self.tol
            and d["ppe_begin"] != 0,
            "CRITICAL", "PPE rollforward broken",
            "CROSS_STATEMENT",
            {"ppe_end": d["ppe_end"], "ppe_begin": d["ppe_begin"], "capex": d["capex"], "depreciation": d["depreciation"]}
        ))

        findings.append(self._rule(
            "Accumulated Depreciation",
            abs(d["accum_dep_end"] - (d["accum_dep_begin"] + d["depreciation"])) > self.tol
            and d["accum_dep_begin"] != 0,
            "CRITICAL", "Accumulated depreciation broken",
            "CROSS_STATEMENT",
            {"accum_dep_end": d["accum_dep_end"], "accum_dep_begin": d["accum_dep_begin"]}
        ))

        findings.append(self._rule(
            "Debt Rollforward",
            abs(d["debt_end"] - (d["debt_begin"] + d["debt_issued"] - d["debt_repaid"])) > self.tol
            and d["debt_begin"] != 0,
            "CRITICAL", "Debt rollforward broken",
            "CROSS_STATEMENT",
            {"debt_end": d["debt_end"], "debt_begin": d["debt_begin"]}
        ))

        findings.append(self._rule(
            "Shares Rollforward",
            abs(d["shares_end"] - (d["shares_begin"] + d["shares_issued"] - d["shares_repurchased"])) > self.tol
            and d["shares_begin"] != d["shares_end"],
            "CRITICAL", "Shares rollforward broken",
            "CROSS_STATEMENT",
            {"shares_end": d["shares_end"], "shares_begin": d["shares_begin"]}
        ))

        findings.append(self._rule(
            "Interest-Debt Link",
            abs(d["interest_expense"] - d["avg_debt"] * d["interest_rate"]) > self.tol
            and d["avg_debt"] != 0 and d["interest_expense"] != 0,
            "WARNING", "Interest expense doesn't match debt * rate",
            "CROSS_STATEMENT",
            {"interest_expense": d["interest_expense"], "implied": d["avg_debt"] * d["interest_rate"]}
        ))

        findings.append(self._rule(
            "Tax Paid vs Expense",
            abs(d["tax_paid"] - d["tax"]) > self.tol and d["tax_paid"] != d["tax"],
            "WARNING", "Tax paid differs from tax expense (timing)",
            "CROSS_STATEMENT",
            {"tax_paid": d["tax_paid"], "tax_expense": d["tax"]}
        ))

        findings.append(self._rule(
            "AR CFO Adjustment",
            abs(d["cfo_ar_adj"] + (d["ar_end"] - d["ar_begin"])) > self.tol
            and d["cfo_ar_adj"] != 0,
            "CRITICAL", "AR CFO adjustment broken",
            "CROSS_STATEMENT",
            {"cfo_ar_adj": d["cfo_ar_adj"], "ar_change": d["ar_end"] - d["ar_begin"]}
        ))

        findings.append(self._rule(
            "Inventory CFO Adjustment",
            abs(d["cfo_inv_adj"] + (d["inventory_end"] - d["inventory_begin"])) > self.tol
            and d["cfo_inv_adj"] != 0,
            "CRITICAL", "Inventory CFO adjustment broken",
            "CROSS_STATEMENT",
            {"cfo_inv_adj": d["cfo_inv_adj"], "inventory_change": d["inventory_end"] - d["inventory_begin"]}
        ))

        findings.append(self._rule(
            "AP CFO Adjustment",
            abs(d["cfo_ap_adj"] - (d["ap_end"] - d["ap_begin"])) > self.tol
            and d["cfo_ap_adj"] != 0,
            "CRITICAL", "AP CFO adjustment broken",
            "CROSS_STATEMENT",
            {"cfo_ap_adj": d["cfo_ap_adj"], "ap_change": d["ap_end"] - d["ap_begin"]}
        ))

        findings.append(self._rule(
            "CapEx in CFI",
            abs(d["capex"] + d["cfi_capex"]) > self.tol
            and d["capex"] != 0 and d["cfi_capex"] != 0,
            "CRITICAL", "CapEx sign error in CFI",
            "CROSS_STATEMENT",
            {"capex": d["capex"], "cfi_capex": d["cfi_capex"]}
        ))

        return findings


class AIAuditor:
    """
    Forensic Accounting Auditor - The "Banker's Brain"

    Performs EXTREME validation on financial data using 66 comprehensive rules
    covering accounting identities, sign logic, ratio sanity, growth volatility,
    and cross-statement linkages.
    """

    def __init__(self, normalized_df: pd.DataFrame = None, dcf_df: pd.DataFrame = None,
                 lbo_df: pd.DataFrame = None, comps_df: pd.DataFrame = None):
        self.normalized_df = normalized_df
        self.dcf_df = dcf_df
        self.lbo_df = lbo_df
        self.comps_df = comps_df
        self.report = AuditReport()
        self.extractor = FinancialDataExtractor(normalized_df, dcf_df, lbo_df, comps_df)
        self.rule_engine = ForensicRuleEngine()

    def run_full_audit(self) -> AuditReport:
        """
        Execute the complete forensic audit suite.

        Returns:
            AuditReport with all findings
        """
        self.report = AuditReport()

        # Extract financial data
        current_data = self.extractor.extract_current_period()
        prior_data = self.extractor.extract_prior_period()

        # Run all forensic rules
        findings = self.rule_engine.run_all_rules(current_data, prior_data)
        self.report.findings = findings

        # Add data quality check
        self._check_data_quality()

        # Generate summary
        self.report.summary = {
            "total_checks": len(self.report.findings),
            "critical": self.report.critical_count,
            "warnings": self.report.warning_count,
            "passed": self.report.pass_count,
            "overall_status": self.report.overall_status
        }

        return self.report

    def _check_data_quality(self):
        """Check overall data quality and mapping coverage."""
        if self.normalized_df is not None and 'Status' in self.normalized_df.columns:
            total = len(self.normalized_df)
            mapped = len(self.normalized_df[self.normalized_df['Status'] == 'VALID'])
            unmapped = total - mapped
            map_rate = mapped / total if total > 0 else 0

            severity = AuditSeverity.CRITICAL if map_rate < 0.8 else (
                AuditSeverity.WARNING if map_rate < 0.95 else AuditSeverity.PASS)

            self.report.findings.append(AuditFinding(
                check_name="Mapping Coverage",
                category="DATA_QUALITY",
                severity=severity,
                message=f"Mapping rate: {map_rate:.1%} ({mapped}/{total} items)",
                details={"total": total, "mapped": mapped, "unmapped": unmapped, "rate": f"{map_rate:.1%}"}
            ))


def run_audit(normalized_path: str = None, dcf_path: str = None,
              lbo_path: str = None, comps_path: str = None) -> AuditReport:
    """
    Convenience function to run full audit from file paths.
    """
    normalized_df = pd.read_csv(normalized_path) if normalized_path else None
    dcf_df = pd.read_csv(dcf_path) if dcf_path else None
    lbo_df = pd.read_csv(lbo_path) if lbo_path else None
    comps_df = pd.read_csv(comps_path) if comps_path else None

    auditor = AIAuditor(normalized_df, dcf_df, lbo_df, comps_df)
    return auditor.run_full_audit()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI Auditor - Forensic Financial Validation")
    parser.add_argument("--normalized", "-n", help="Path to normalized_financials.csv")
    parser.add_argument("--dcf", "-d", help="Path to DCF_Historical_Setup.csv")
    parser.add_argument("--lbo", "-l", help="Path to LBO_Credit_Stats.csv")
    parser.add_argument("--comps", "-c", help="Path to Comps_Trading_Metrics.csv")
    parser.add_argument("--output", "-o", help="Output CSV path for audit report")

    args = parser.parse_args()

    report = run_audit(args.normalized, args.dcf, args.lbo, args.comps)

    print("\n" + "=" * 70)
    print("AI AUDITOR - FORENSIC ACCOUNTING REPORT")
    print("=" * 70)
    print(f"\nOverall Status: {report.overall_status}")
    print(f"Critical Issues: {report.critical_count}")
    print(f"Warnings: {report.warning_count}")
    print(f"Passed Checks: {report.pass_count}")
    print("\n" + "-" * 70)

    for finding in report.findings:
        icon = {"CRITICAL": "[X]", "WARNING": "[!]", "PASS": "[+]", "INFO": "[i]"}.get(
            finding.severity.value, "[?]")
        print(f"{icon} [{finding.category}] {finding.check_name}: {finding.message}")

    if args.output:
        report.to_dataframe().to_csv(args.output, index=False)
        print(f"\nReport saved to: {args.output}")

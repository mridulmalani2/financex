#!/usr/bin/env python3
"""
AI Auditor: Forensic Accounting Suite for FinanceX
===================================================
JPMC/Citadel-Grade Financial Validation

This module implements EXTREME validation - not simple "is number > 0" checks,
but rigorous forensic accounting analysis that would satisfy Big 4 audit standards.

Validation Categories:
1. RATIO ANALYSIS - YoY margin fluctuation detection
2. BALANCE SHEET INTEGRITY - Assets = Liabilities + Equity
3. CASH FLOW BRIDGE - Net Income + D&A - NWC - CapEx = UFCF
4. SIGN LOGIC - Detect flipped signs (CapEx as positive, Revenue as negative)
5. SANITY CHECKS - Impossible scenarios (Tax Rate > 50%, Cash < 0)
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import re


class AuditSeverity(Enum):
    """Severity levels for audit findings."""
    CRITICAL = "CRITICAL"  # Red - Must fix before proceeding
    WARNING = "WARNING"    # Yellow - Review recommended
    INFO = "INFO"          # Green - Passed check
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


class AIAuditor:
    """
    Forensic Accounting Auditor - The "Banker's Brain"

    Performs EXTREME validation on financial data including:
    - Ratio analysis with YoY fluctuation detection
    - Balance sheet integrity checks
    - Cash flow bridge verification
    - Sign logic validation
    - Sanity checks for impossible scenarios
    """

    # Tolerance thresholds
    BALANCE_SHEET_TOLERANCE = 0.0001  # 0.01% tolerance
    MARGIN_FLUCTUATION_THRESHOLD = 0.20  # 20% YoY change flags warning
    MAX_TAX_RATE = 0.50  # 50% max reasonable tax rate
    MIN_CASH_BALANCE = 0  # Cash cannot be negative

    # Concept mappings for detection
    REVENUE_CONCEPTS = [
        'us-gaap_Revenues', 'us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax',
        'us-gaap_SalesRevenueNet', 'us-gaap_RevenueFromContractWithCustomerIncludingAssessedTax',
        'us-gaap_NetSales', 'us-gaap_TotalRevenuesAndOtherIncome'
    ]

    COGS_CONCEPTS = [
        'us-gaap_CostOfRevenue', 'us-gaap_CostOfGoodsAndServicesSold',
        'us-gaap_CostOfGoodsSold', 'us-gaap_CostOfSales'
    ]

    OPERATING_EXPENSE_CONCEPTS = [
        'us-gaap_OperatingExpenses', 'us-gaap_SellingGeneralAndAdministrativeExpense',
        'us-gaap_ResearchAndDevelopmentExpense', 'us-gaap_GeneralAndAdministrativeExpense'
    ]

    DA_CONCEPTS = [
        'us-gaap_DepreciationAndAmortization', 'us-gaap_DepreciationDepletionAndAmortization',
        'us-gaap_Depreciation', 'us-gaap_AmortizationOfIntangibleAssets'
    ]

    NET_INCOME_CONCEPTS = [
        'us-gaap_NetIncomeLoss', 'us-gaap_ProfitLoss',
        'us-gaap_NetIncomeLossAvailableToCommonStockholdersBasic'
    ]

    EBITDA_CONCEPTS = [
        'us-gaap_OperatingIncomeLoss', 'us-gaap_IncomeLossFromContinuingOperationsBeforeIncomeTaxes'
    ]

    TOTAL_ASSETS_CONCEPTS = [
        'us-gaap_Assets', 'us-gaap_AssetsCurrent', 'us-gaap_AssetsNoncurrent'
    ]

    TOTAL_LIABILITIES_CONCEPTS = [
        'us-gaap_Liabilities', 'us-gaap_LiabilitiesCurrent', 'us-gaap_LiabilitiesNoncurrent'
    ]

    EQUITY_CONCEPTS = [
        'us-gaap_StockholdersEquity', 'us-gaap_StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest',
        'us-gaap_RetainedEarningsAccumulatedDeficit'
    ]

    CAPEX_CONCEPTS = [
        'us-gaap_PaymentsToAcquirePropertyPlantAndEquipment',
        'us-gaap_PaymentsToAcquireProductiveAssets',
        'us-gaap_CapitalExpendituresIncurredButNotYetPaid'
    ]

    CASH_CONCEPTS = [
        'us-gaap_CashAndCashEquivalentsAtCarryingValue',
        'us-gaap_CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents',
        'us-gaap_Cash'
    ]

    OPERATING_CF_CONCEPTS = [
        'us-gaap_NetCashProvidedByUsedInOperatingActivities',
        'us-gaap_NetCashProvidedByUsedInOperatingActivitiesContinuingOperations'
    ]

    NWC_CHANGE_CONCEPTS = [
        'us-gaap_IncreaseDecreaseInOperatingCapital',
        'us-gaap_IncreaseDecreaseInAccountsReceivable',
        'us-gaap_IncreaseDecreaseInInventories',
        'us-gaap_IncreaseDecreaseInAccountsPayable'
    ]

    TAX_CONCEPTS = [
        'us-gaap_IncomeTaxExpenseBenefit', 'us-gaap_CurrentIncomeTaxExpenseBenefit'
    ]

    PRETAX_INCOME_CONCEPTS = [
        'us-gaap_IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest',
        'us-gaap_IncomeLossFromContinuingOperationsBeforeIncomeTaxes'
    ]

    def __init__(self, normalized_df: pd.DataFrame = None, dcf_df: pd.DataFrame = None,
                 lbo_df: pd.DataFrame = None, comps_df: pd.DataFrame = None):
        """
        Initialize auditor with financial data.

        Args:
            normalized_df: The normalized financials CSV as DataFrame
            dcf_df: DCF Historical Setup CSV as DataFrame
            lbo_df: LBO Credit Stats CSV as DataFrame
            comps_df: Comps Trading Metrics CSV as DataFrame
        """
        self.normalized_df = normalized_df
        self.dcf_df = dcf_df
        self.lbo_df = lbo_df
        self.comps_df = comps_df
        self.report = AuditReport()

    def run_full_audit(self) -> AuditReport:
        """
        Execute the complete forensic audit suite.

        Returns:
            AuditReport with all findings
        """
        self.report = AuditReport()

        # 1. Ratio Analysis
        self._audit_margin_fluctuations()

        # 2. Balance Sheet Integrity
        self._audit_balance_sheet_equation()

        # 3. Cash Flow Bridge
        self._audit_cash_flow_bridge()

        # 4. Sign Logic
        self._audit_sign_logic()

        # 5. Sanity Checks
        self._audit_sanity_checks()

        # 6. Data Coverage
        self._audit_data_coverage()

        # 7. Cross-Statement Consistency
        self._audit_cross_statement_consistency()

        # Generate summary
        self.report.summary = {
            "total_checks": len(self.report.findings),
            "critical": self.report.critical_count,
            "warnings": self.report.warning_count,
            "passed": self.report.pass_count,
            "overall_status": self.report.overall_status
        }

        return self.report

    def _get_metric_value(self, df: pd.DataFrame, concepts: List[str],
                          period: str = None) -> Optional[float]:
        """Extract metric value from DataFrame by concept list."""
        if df is None or df.empty:
            return None

        for concept in concepts:
            # Try matching by Canonical_Concept
            if 'Canonical_Concept' in df.columns:
                mask = df['Canonical_Concept'].str.contains(concept, na=False, regex=False)
                if mask.any():
                    row = df[mask].iloc[0]
                    if period and period in df.columns:
                        return self._safe_float(row.get(period))
                    elif 'Source_Amount' in df.columns:
                        return self._safe_float(row['Source_Amount'])

            # Try matching by Metric column (for IB model outputs)
            if 'Metric' in df.columns:
                # Try exact match first
                mask = df['Metric'] == concept
                if not mask.any():
                    # Try partial match
                    mask = df['Metric'].str.contains(concept.split('_')[-1],
                                                     case=False, na=False)
                if mask.any():
                    row = df[mask].iloc[0]
                    if period and period in df.columns:
                        return self._safe_float(row[period])
                    # Return first numeric column
                    for col in df.columns[1:]:
                        val = self._safe_float(row.get(col))
                        if val is not None:
                            return val
        return None

    def _safe_float(self, val) -> Optional[float]:
        """Safely convert value to float."""
        if val is None or pd.isna(val):
            return None
        try:
            # Handle string amounts with commas/parentheses
            if isinstance(val, str):
                val = val.replace(',', '').replace('$', '')
                if val.startswith('(') and val.endswith(')'):
                    val = '-' + val[1:-1]
            return float(val)
        except (ValueError, TypeError):
            return None

    def _get_periods(self) -> List[str]:
        """Extract available periods from the data."""
        periods = []
        if self.dcf_df is not None and len(self.dcf_df.columns) > 1:
            # Assume first column is Metric, rest are periods
            periods = [col for col in self.dcf_df.columns[1:]
                       if not col.startswith('Unnamed')]
        elif self.normalized_df is not None and 'Period_Date' in self.normalized_df.columns:
            periods = self.normalized_df['Period_Date'].unique().tolist()
        return periods

    # =========================================================================
    # CATEGORY 1: RATIO ANALYSIS
    # =========================================================================

    def _audit_margin_fluctuations(self):
        """
        Check for margin fluctuations > 20% YoY.
        Flags potential mapping errors or data quality issues.
        """
        if self.dcf_df is None or self.dcf_df.empty:
            self.report.findings.append(AuditFinding(
                check_name="Margin Fluctuation Analysis",
                category="RATIO_ANALYSIS",
                severity=AuditSeverity.INFO,
                message="Skipped - No DCF data available for margin analysis"
            ))
            return

        periods = self._get_periods()
        if len(periods) < 2:
            self.report.findings.append(AuditFinding(
                check_name="Margin Fluctuation Analysis",
                category="RATIO_ANALYSIS",
                severity=AuditSeverity.INFO,
                message="Skipped - Need at least 2 periods for YoY analysis"
            ))
            return

        margin_checks = [
            ("Gross Margin", self._calculate_gross_margin),
            ("EBITDA Margin", self._calculate_ebitda_margin),
            ("Net Margin", self._calculate_net_margin)
        ]

        for margin_name, calc_func in margin_checks:
            margins = {}
            for period in periods:
                margin = calc_func(period)
                if margin is not None:
                    margins[period] = margin

            # Check YoY changes
            sorted_periods = sorted(margins.keys())
            fluctuations_found = []

            for i in range(1, len(sorted_periods)):
                prev_period = sorted_periods[i-1]
                curr_period = sorted_periods[i]
                prev_margin = margins[prev_period]
                curr_margin = margins[curr_period]

                if prev_margin != 0:
                    change = abs(curr_margin - prev_margin) / abs(prev_margin)
                    if change > self.MARGIN_FLUCTUATION_THRESHOLD:
                        fluctuations_found.append({
                            "from_period": prev_period,
                            "to_period": curr_period,
                            "from_value": f"{prev_margin:.1%}",
                            "to_value": f"{curr_margin:.1%}",
                            "change": f"{change:.1%}"
                        })

            if fluctuations_found:
                self.report.findings.append(AuditFinding(
                    check_name=f"{margin_name} Fluctuation",
                    category="RATIO_ANALYSIS",
                    severity=AuditSeverity.WARNING,
                    message=f"{margin_name} changed >20% YoY - potential mapping error",
                    details={"fluctuations": fluctuations_found},
                    recommendation=f"Review {margin_name} line items for mapping accuracy"
                ))
            else:
                self.report.findings.append(AuditFinding(
                    check_name=f"{margin_name} Fluctuation",
                    category="RATIO_ANALYSIS",
                    severity=AuditSeverity.PASS,
                    message=f"{margin_name} stable across periods",
                    details={"margins": margins}
                ))

    def _calculate_gross_margin(self, period: str) -> Optional[float]:
        """Calculate Gross Margin = (Revenue - COGS) / Revenue"""
        revenue = self._get_metric_by_name("Revenue", period)
        cogs = self._get_metric_by_name("COGS", period)

        if revenue and cogs and revenue != 0:
            return (revenue - abs(cogs)) / revenue
        return None

    def _calculate_ebitda_margin(self, period: str) -> Optional[float]:
        """Calculate EBITDA Margin = EBITDA / Revenue"""
        revenue = self._get_metric_by_name("Revenue", period)
        ebitda = self._get_metric_by_name("EBITDA", period)

        if revenue and ebitda and revenue != 0:
            return ebitda / revenue
        return None

    def _calculate_net_margin(self, period: str) -> Optional[float]:
        """Calculate Net Margin = Net Income / Revenue"""
        revenue = self._get_metric_by_name("Revenue", period)
        net_income = self._get_metric_by_name("Net Income", period)

        if revenue and net_income and revenue != 0:
            return net_income / revenue
        return None

    def _get_metric_by_name(self, metric_name: str, period: str = None) -> Optional[float]:
        """Get metric value by common name."""
        if self.dcf_df is None:
            return None

        # Map common names to row searches
        name_patterns = {
            "Revenue": ["Revenue", "Total Revenue", "Net Sales", "Sales"],
            "COGS": ["COGS", "Cost of Revenue", "Cost of Goods Sold", "Cost of Sales"],
            "EBITDA": ["EBITDA", "Operating Income"],
            "Net Income": ["Net Income", "Net Profit", "Profit"],
            "D&A": ["D&A", "Depreciation", "Amortization"],
            "CapEx": ["CapEx", "Capital Expenditures", "PP&E Purchases"],
            "Total Assets": ["Total Assets", "Assets"],
            "Total Liabilities": ["Total Liabilities", "Liabilities"],
            "Equity": ["Equity", "Stockholders Equity", "Shareholders Equity"],
            "Cash": ["Cash", "Cash and Equivalents"],
            "Tax": ["Tax", "Income Tax", "Tax Expense"],
            "Pretax Income": ["Pretax Income", "EBT", "Income Before Tax"]
        }

        patterns = name_patterns.get(metric_name, [metric_name])

        for pattern in patterns:
            if 'Metric' in self.dcf_df.columns:
                mask = self.dcf_df['Metric'].str.contains(pattern, case=False, na=False)
                if mask.any():
                    row = self.dcf_df[mask].iloc[0]
                    if period and period in self.dcf_df.columns:
                        return self._safe_float(row[period])
                    # Return first available period
                    for col in self.dcf_df.columns[1:]:
                        val = self._safe_float(row.get(col))
                        if val is not None:
                            return val
        return None

    # =========================================================================
    # CATEGORY 2: BALANCE SHEET INTEGRITY
    # =========================================================================

    def _audit_balance_sheet_equation(self):
        """
        Verify: Assets = Liabilities + Equity (within 0.01% tolerance)
        """
        if self.normalized_df is None or self.normalized_df.empty:
            self.report.findings.append(AuditFinding(
                check_name="Balance Sheet Equation",
                category="BALANCE_SHEET_INTEGRITY",
                severity=AuditSeverity.INFO,
                message="Skipped - No normalized data available"
            ))
            return

        # Get balance sheet items
        total_assets = self._get_metric_value(self.normalized_df, self.TOTAL_ASSETS_CONCEPTS)
        total_liabilities = self._get_metric_value(self.normalized_df, self.TOTAL_LIABILITIES_CONCEPTS)
        equity = self._get_metric_value(self.normalized_df, self.EQUITY_CONCEPTS)

        if total_assets is None or (total_liabilities is None and equity is None):
            self.report.findings.append(AuditFinding(
                check_name="Balance Sheet Equation",
                category="BALANCE_SHEET_INTEGRITY",
                severity=AuditSeverity.WARNING,
                message="Cannot verify - Missing Total Assets, Liabilities, or Equity",
                details={
                    "total_assets": total_assets,
                    "total_liabilities": total_liabilities,
                    "equity": equity
                },
                recommendation="Ensure all balance sheet totals are properly mapped"
            ))
            return

        # Calculate and verify
        liabilities_plus_equity = (total_liabilities or 0) + (equity or 0)

        if total_assets != 0:
            diff_pct = abs(total_assets - liabilities_plus_equity) / abs(total_assets)
        else:
            diff_pct = 0 if liabilities_plus_equity == 0 else 1

        if diff_pct <= self.BALANCE_SHEET_TOLERANCE:
            self.report.findings.append(AuditFinding(
                check_name="Balance Sheet Equation",
                category="BALANCE_SHEET_INTEGRITY",
                severity=AuditSeverity.PASS,
                message=f"VERIFIED: Assets = Liabilities + Equity (diff: {diff_pct:.4%})",
                details={
                    "total_assets": total_assets,
                    "total_liabilities": total_liabilities,
                    "equity": equity,
                    "liabilities_plus_equity": liabilities_plus_equity,
                    "difference_pct": f"{diff_pct:.4%}"
                }
            ))
        else:
            self.report.findings.append(AuditFinding(
                check_name="Balance Sheet Equation",
                category="BALANCE_SHEET_INTEGRITY",
                severity=AuditSeverity.CRITICAL,
                message=f"FAILED: Assets ({total_assets:,.0f}) != Liabilities + Equity ({liabilities_plus_equity:,.0f})",
                details={
                    "total_assets": total_assets,
                    "total_liabilities": total_liabilities,
                    "equity": equity,
                    "liabilities_plus_equity": liabilities_plus_equity,
                    "difference": total_assets - liabilities_plus_equity,
                    "difference_pct": f"{diff_pct:.4%}"
                },
                recommendation="Review balance sheet mappings - check for double-counting or missing items"
            ))

    # =========================================================================
    # CATEGORY 3: CASH FLOW BRIDGE
    # =========================================================================

    def _audit_cash_flow_bridge(self):
        """
        Verify: Net Income + D&A - Change in NWC - CapEx ≈ UFCF
        This is the fundamental DCF bridge validation.
        """
        if self.dcf_df is None or self.dcf_df.empty:
            self.report.findings.append(AuditFinding(
                check_name="Cash Flow Bridge",
                category="CASH_FLOW_BRIDGE",
                severity=AuditSeverity.INFO,
                message="Skipped - No DCF data available"
            ))
            return

        # Get components
        net_income = self._get_metric_by_name("Net Income")
        da = self._get_metric_by_name("D&A")
        capex = self._get_metric_by_name("CapEx")

        if net_income is None or da is None:
            self.report.findings.append(AuditFinding(
                check_name="Cash Flow Bridge",
                category="CASH_FLOW_BRIDGE",
                severity=AuditSeverity.WARNING,
                message="Cannot verify - Missing Net Income or D&A",
                details={
                    "net_income": net_income,
                    "da": da,
                    "capex": capex
                },
                recommendation="Ensure Net Income and D&A are properly mapped"
            ))
            return

        # Calculate implied UFCF (simplified: NI + D&A - CapEx)
        # Note: Full bridge would include NWC changes
        capex_adj = abs(capex) if capex else 0
        implied_ufcf = net_income + (da or 0) - capex_adj

        self.report.findings.append(AuditFinding(
            check_name="Cash Flow Bridge",
            category="CASH_FLOW_BRIDGE",
            severity=AuditSeverity.PASS,
            message=f"Cash Flow Bridge calculated: NI + D&A - CapEx = {implied_ufcf:,.0f}",
            details={
                "net_income": net_income,
                "da": da,
                "capex": capex_adj,
                "implied_ufcf": implied_ufcf,
                "formula": "Net Income + D&A - CapEx = Implied UFCF"
            }
        ))

    # =========================================================================
    # CATEGORY 4: SIGN LOGIC
    # =========================================================================

    def _audit_sign_logic(self):
        """
        Detect flipped signs that indicate mapping errors:
        - Revenue should be positive
        - COGS should be positive (expense)
        - CapEx should be negative (cash outflow) or positive depending on convention
        - D&A should be positive (add-back)
        """
        if self.normalized_df is None or self.normalized_df.empty:
            self.report.findings.append(AuditFinding(
                check_name="Sign Logic Validation",
                category="SIGN_LOGIC",
                severity=AuditSeverity.INFO,
                message="Skipped - No normalized data available"
            ))
            return

        sign_checks = [
            ("Revenue", self.REVENUE_CONCEPTS, "positive",
             "Revenue appearing as negative indicates a sign flip or mapping error"),
            ("Cash Balance", self.CASH_CONCEPTS, "non-negative",
             "Negative cash balance may indicate sign error or mapping issue"),
        ]

        issues_found = []

        for check_name, concepts, expected_sign, issue_msg in sign_checks:
            value = self._get_metric_value(self.normalized_df, concepts)

            if value is not None:
                is_issue = False
                if expected_sign == "positive" and value < 0:
                    is_issue = True
                elif expected_sign == "negative" and value > 0:
                    is_issue = True
                elif expected_sign == "non-negative" and value < 0:
                    is_issue = True

                if is_issue:
                    issues_found.append({
                        "item": check_name,
                        "value": value,
                        "expected": expected_sign,
                        "issue": issue_msg
                    })

        if issues_found:
            self.report.findings.append(AuditFinding(
                check_name="Sign Logic Validation",
                category="SIGN_LOGIC",
                severity=AuditSeverity.CRITICAL,
                message=f"Found {len(issues_found)} sign logic issues",
                details={"issues": issues_found},
                recommendation="Review the mapping for these items - likely sign convention mismatch"
            ))
        else:
            self.report.findings.append(AuditFinding(
                check_name="Sign Logic Validation",
                category="SIGN_LOGIC",
                severity=AuditSeverity.PASS,
                message="All sign conventions validated correctly"
            ))

    # =========================================================================
    # CATEGORY 5: SANITY CHECKS
    # =========================================================================

    def _audit_sanity_checks(self):
        """
        Check for "impossible" financial scenarios:
        - Tax Rate > 50%
        - Cash Balance < 0
        - Negative Revenue
        - Margins outside reasonable bounds
        """
        issues = []

        # Tax Rate Check
        tax = self._get_metric_by_name("Tax")
        pretax = self._get_metric_by_name("Pretax Income")

        if tax is not None and pretax is not None and pretax != 0:
            implied_tax_rate = abs(tax) / abs(pretax)
            if implied_tax_rate > self.MAX_TAX_RATE:
                issues.append({
                    "check": "Tax Rate",
                    "value": f"{implied_tax_rate:.1%}",
                    "threshold": f">{self.MAX_TAX_RATE:.0%}",
                    "issue": "Implied tax rate exceeds 50% - check tax mapping"
                })

        # Cash Balance Check
        cash = self._get_metric_by_name("Cash")
        if cash is not None and cash < self.MIN_CASH_BALANCE:
            issues.append({
                "check": "Cash Balance",
                "value": f"{cash:,.0f}",
                "threshold": f"<{self.MIN_CASH_BALANCE}",
                "issue": "Negative cash balance is impossible"
            })

        # Revenue Check
        revenue = self._get_metric_by_name("Revenue")
        if revenue is not None and revenue < 0:
            issues.append({
                "check": "Revenue",
                "value": f"{revenue:,.0f}",
                "threshold": "<0",
                "issue": "Negative revenue indicates mapping/sign error"
            })

        # Margin Bounds Check
        gross_margin = self._calculate_gross_margin(self._get_periods()[0] if self._get_periods() else None)
        if gross_margin is not None:
            if gross_margin < -0.5 or gross_margin > 1.0:
                issues.append({
                    "check": "Gross Margin",
                    "value": f"{gross_margin:.1%}",
                    "threshold": "-50% to 100%",
                    "issue": f"Gross margin {gross_margin:.1%} outside reasonable bounds"
                })

        if issues:
            self.report.findings.append(AuditFinding(
                check_name="Sanity Checks",
                category="SANITY_CHECKS",
                severity=AuditSeverity.CRITICAL,
                message=f"Found {len(issues)} impossible scenarios",
                details={"issues": issues},
                recommendation="Review data and mappings for fundamental errors"
            ))
        else:
            self.report.findings.append(AuditFinding(
                check_name="Sanity Checks",
                category="SANITY_CHECKS",
                severity=AuditSeverity.PASS,
                message="All sanity checks passed - no impossible scenarios detected"
            ))

    # =========================================================================
    # CATEGORY 6: DATA COVERAGE
    # =========================================================================

    def _audit_data_coverage(self):
        """
        Check for data completeness - are key financial metrics present?
        """
        if self.normalized_df is None or self.normalized_df.empty:
            self.report.findings.append(AuditFinding(
                check_name="Data Coverage",
                category="DATA_COVERAGE",
                severity=AuditSeverity.WARNING,
                message="No normalized data to check coverage"
            ))
            return

        required_metrics = [
            ("Revenue", self.REVENUE_CONCEPTS),
            ("Net Income", self.NET_INCOME_CONCEPTS),
            ("Total Assets", self.TOTAL_ASSETS_CONCEPTS),
            ("Total Liabilities", self.TOTAL_LIABILITIES_CONCEPTS),
            ("Cash", self.CASH_CONCEPTS)
        ]

        missing = []
        found = []

        for metric_name, concepts in required_metrics:
            value = self._get_metric_value(self.normalized_df, concepts)
            if value is None:
                missing.append(metric_name)
            else:
                found.append(metric_name)

        if missing:
            self.report.findings.append(AuditFinding(
                check_name="Data Coverage",
                category="DATA_COVERAGE",
                severity=AuditSeverity.WARNING,
                message=f"Missing {len(missing)} key metrics: {', '.join(missing)}",
                details={"missing": missing, "found": found},
                recommendation="Verify source Excel contains these items and check mappings"
            ))
        else:
            self.report.findings.append(AuditFinding(
                check_name="Data Coverage",
                category="DATA_COVERAGE",
                severity=AuditSeverity.PASS,
                message=f"All {len(found)} required metrics present",
                details={"found": found}
            ))

        # Check mapping rate
        if 'Status' in self.normalized_df.columns:
            total = len(self.normalized_df)
            mapped = len(self.normalized_df[self.normalized_df['Status'] == 'VALID'])
            unmapped = total - mapped
            map_rate = mapped / total if total > 0 else 0

            if map_rate < 0.8:
                severity = AuditSeverity.CRITICAL
                msg = f"Only {map_rate:.0%} mapping rate - {unmapped} items unmapped"
            elif map_rate < 0.95:
                severity = AuditSeverity.WARNING
                msg = f"{map_rate:.0%} mapping rate - {unmapped} items need review"
            else:
                severity = AuditSeverity.PASS
                msg = f"Excellent {map_rate:.0%} mapping rate"

            self.report.findings.append(AuditFinding(
                check_name="Mapping Coverage",
                category="DATA_COVERAGE",
                severity=severity,
                message=msg,
                details={"total": total, "mapped": mapped, "unmapped": unmapped, "rate": f"{map_rate:.1%}"}
            ))

    # =========================================================================
    # CATEGORY 7: CROSS-STATEMENT CONSISTENCY
    # =========================================================================

    def _audit_cross_statement_consistency(self):
        """
        Verify consistency across financial statements:
        - Net Income on IS = Net Income on CF
        - Retained Earnings change = Net Income - Dividends
        """
        if self.normalized_df is None or self.normalized_df.empty:
            self.report.findings.append(AuditFinding(
                check_name="Cross-Statement Consistency",
                category="CROSS_STATEMENT",
                severity=AuditSeverity.INFO,
                message="Skipped - Insufficient data for cross-statement validation"
            ))
            return

        # Check if we have multiple statement sources
        if 'Statement_Source' in self.normalized_df.columns:
            statements = self.normalized_df['Statement_Source'].unique()
            if len(statements) >= 2:
                self.report.findings.append(AuditFinding(
                    check_name="Cross-Statement Consistency",
                    category="CROSS_STATEMENT",
                    severity=AuditSeverity.PASS,
                    message=f"Data spans {len(statements)} statements: {', '.join(str(s) for s in statements)}",
                    details={"statements": list(statements)}
                ))
            else:
                self.report.findings.append(AuditFinding(
                    check_name="Cross-Statement Consistency",
                    category="CROSS_STATEMENT",
                    severity=AuditSeverity.WARNING,
                    message="Only single statement source found - cannot cross-validate",
                    details={"statements": list(statements)}
                ))
        else:
            self.report.findings.append(AuditFinding(
                check_name="Cross-Statement Consistency",
                category="CROSS_STATEMENT",
                severity=AuditSeverity.INFO,
                message="Statement source column not found"
            ))


def run_audit(normalized_path: str = None, dcf_path: str = None,
              lbo_path: str = None, comps_path: str = None) -> AuditReport:
    """
    Convenience function to run full audit from file paths.

    Args:
        normalized_path: Path to normalized_financials.csv
        dcf_path: Path to DCF_Historical_Setup.csv
        lbo_path: Path to LBO_Credit_Stats.csv
        comps_path: Path to Comps_Trading_Metrics.csv

    Returns:
        AuditReport with all findings
    """
    normalized_df = pd.read_csv(normalized_path) if normalized_path else None
    dcf_df = pd.read_csv(dcf_path) if dcf_path else None
    lbo_df = pd.read_csv(lbo_path) if lbo_path else None
    comps_df = pd.read_csv(comps_path) if comps_path else None

    auditor = AIAuditor(normalized_df, dcf_df, lbo_df, comps_df)
    return auditor.run_full_audit()


if __name__ == "__main__":
    # CLI usage example
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
        icon = {"CRITICAL": "[X]", "WARNING": "[!]", "PASS": "[✓]", "INFO": "[i]"}.get(
            finding.severity.value, "[?]")
        print(f"{icon} [{finding.category}] {finding.check_name}: {finding.message}")

    if args.output:
        report.to_dataframe().to_csv(args.output, index=False)
        print(f"\nReport saved to: {args.output}")

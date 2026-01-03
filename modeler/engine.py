#!/usr/bin/env python3
import pandas as pd
import os
import sys

# Import Rules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.ib_rules import *

class FinancialEngine:
    def __init__(self, norm_file_path):
        self.df = pd.read_csv(norm_file_path)
        self.df = self.df[self.df['Status'] == 'VALID'].copy()
        
        # Pivot on Canonical_Concept
        self.pivot = self.df.pivot_table(
            index='Canonical_Concept', 
            columns='Period_Date', 
            values='Source_Amount', 
            aggfunc='sum'
        ).fillna(0)
        
        self.dates = sorted(self.pivot.columns, reverse=True)
        if not self.dates: self.dates = ["Current"]
        self.pivot = self.pivot[self.dates]

    def _sum_bucket(self, concept_set):
        available = list(concept_set.intersection(set(self.pivot.index)))
        if not available: return pd.Series(0, index=self.dates)
        return self.pivot.loc[available].sum()

    def _smart_sum(self, total_set, comp_set):
        """
        Prevents double counting. 
        Returns Max(Sum(Total_Tags), Sum(Component_Tags)).
        """
        val_total = self._sum_bucket(total_set)
        val_comps = self._sum_bucket(comp_set)
        
        # Return the element-wise max for each year
        # If Total line exists (400) and Comps (100+300), it returns 400.
        # If Total line missing (0) and Comps (400), it returns 400.
        # If both mapped (400 and 400), it returns 400 (not 800).
        df_compare = pd.DataFrame({'total': val_total, 'comps': val_comps})
        return df_compare.max(axis=1)

    def build_dcf_ready_view(self):
        # 1. Revenue: Smart Sum
        # Note: For Apple, we mapped products/services to Revenues (Total) in alias,
        # so REVENUE_TOTAL_IDS will catch everything.
        # If we had distinct tags, smart_sum would handle it.
        revenue = self._sum_bucket(REVENUE_TOTAL_IDS) 
        
        # 2. COGS: Smart Sum
        cogs = self._smart_sum(COGS_TOTAL_IDS, COGS_COMPONENT_IDS)
        gross_profit = revenue + cogs # Expenses assumed negative inputs?
        # Check sign: If inputs are positive, GP = Rev - Cogs.
        # Your CSV shows positive numbers for Cost of Sales.
        # We need to deduct them.
        gross_profit = revenue - cogs
        
        # 3. OPEX
        sga = self._sum_bucket(SG_AND_A_IDS)
        rnd = self._sum_bucket(R_AND_D_IDS)
        fuel = self._sum_bucket(FUEL_EXPENSE_IDS)
        
        # Calculate Total Opex robustly
        total_opex_line = self._sum_bucket(OPEX_TOTAL_IDS)
        sum_of_parts = sga + rnd + fuel
        
        # "Other Opex" is the difference between the Total Line and the Known Parts
        # If Total Line < Parts (e.g. Total missing), Other is 0.
        other_opex = (total_opex_line - sum_of_parts).clip(lower=0)
        
        # Re-construct adjusted Total Opex
        total_opex_final = sga + rnd + fuel + other_opex
        
        ebitda_reported = gross_profit - total_opex_final
        
        da = self._sum_bucket(D_AND_A_IDS)
        ebit = ebitda_reported - da # D&A usually positive number in 10K, so subtract
        
        taxes = self._sum_bucket(TAX_EXP_IDS)
        nopat_proxy = ebit - taxes
        
        capex = self._sum_bucket({"us-gaap_PaymentsToAcquirePropertyPlantAndEquipment"})
        
        # NWC: Smart Sum Assets vs Liabs
        curr_assets = self._smart_sum(NWC_CURRENT_ASSETS_TOTAL, NWC_CURRENT_ASSETS_COMPS)
        curr_liabs = self._smart_sum(NWC_CURRENT_LIABS_TOTAL, NWC_CURRENT_LIABS_COMPS)
        nwc = curr_assets - curr_liabs
        delta_nwc = nwc.diff(periods=-1).fillna(0) # Asset Increase = Cash Outflow
        
        ufcf = nopat_proxy + da - delta_nwc - capex

        data = {
            "Total Revenue": revenue,
            "(-) COGS": cogs,
            "(=) Gross Profit": gross_profit,
            "(-) SG&A": sga,
            "(-) R&D": rnd,
            "(-) Other Opex": other_opex,
            "(=) EBITDA (Reported)": ebitda_reported,
            "(-) D&A": da,
            "(=) EBIT": ebit,
            "(-) Taxes": taxes,
            "(=) NOPAT": nopat_proxy,
            "Plus: D&A": da,
            "Less: Change in NWC": delta_nwc,
            "Less: Capex": capex,
            "(=) Unlevered Free Cash Flow": ufcf
        }
        return pd.DataFrame(data).T

    def build_lbo_ready_view(self):
        revenue = self._sum_bucket(REVENUE_TOTAL_IDS)
        cogs = self._smart_sum(COGS_TOTAL_IDS, COGS_COMPONENT_IDS)
        
        # Recalculate EBITDA consistent with DCF
        sga = self._sum_bucket(SG_AND_A_IDS)
        rnd = self._sum_bucket(R_AND_D_IDS)
        other_opex = (self._sum_bucket(OPEX_TOTAL_IDS) - (sga + rnd)).clip(lower=0)
        opex_total = sga + rnd + other_opex
        
        ebitda_reported = revenue - cogs - opex_total
        
        restructuring = self._sum_bucket(RESTRUCTURING_IDS) 
        ebitda_adjusted = ebitda_reported + restructuring

        # Debt
        total_debt = self._sum_bucket(DEBT_IDS)
        cash = self._sum_bucket(CASH_IDS)
        net_debt = total_debt - cash

        data = {
            "EBITDA (Reported)": ebitda_reported,
            "(+) Restructuring": restructuring,
            "(=) EBITDA (Adjusted)": ebitda_adjusted,
            "Cash": cash,
            "Total Debt": total_debt,
            "Net Debt": net_debt
        }
        return pd.DataFrame(data).T

    def build_comps_ready_view(self):
        # Simplified for brevity, follows same logic
        rev = self._sum_bucket(REVENUE_TOTAL_IDS)
        ebitda = rev - self._smart_sum(COGS_TOTAL_IDS, COGS_COMPONENT_IDS) - self._sum_bucket(OPEX_TOTAL_IDS) # Rough proxy
        
        net_income = self._sum_bucket({"us-gaap_NetIncomeLoss"})
        
        shares = self._sum_bucket({"us-gaap_CommonStockSharesOutstanding", "us-gaap_WeightedAverageNumberOfSharesOutstandingBasic"})
        total_debt = self._sum_bucket(DEBT_IDS)
        cash = self._sum_bucket(CASH_IDS)
        net_debt = total_debt - cash

        data = {
            "Revenue": rev,
            "EBITDA": ebitda,
            "Net Income": net_income,
            "Net Debt": net_debt,
            "Shares Outstanding": shares
        }
        return pd.DataFrame(data).T
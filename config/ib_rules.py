"""
IB Logic Rules (Hierarchy Aware)
================================
Distinguishes between Aggregate (Total) tags and Granular (Component) tags
to prevent double-counting.
"""

# --- 1. REVENUE ---
# Parent Tags (The Totals)
REVENUE_TOTAL_IDS = {
    "us-gaap_Revenues", "us-gaap_SalesRevenueNet", "ifrs-full_Revenue",
    "us-gaap_SalesRevenueGoodsNet", "us-gaap_SalesRevenueServicesNet" 
    # Note: Goods/Services are technically components, but often act as the only revenue lines in tech.
    # We put them here to ensure they are captured if "Total Revenue" is missing.
}
# (We don't strictly need components for Revenue Top Line if we just take the max, 
# but let's keep it simple: The Engine will de-dupe based on logic).

# --- 2. COST OF SALES ---
COGS_TOTAL_IDS = {
    "us-gaap_CostOfRevenue", "us-gaap_CostOfGoodsAndServicesSold"
}
COGS_COMPONENT_IDS = {
    "us-gaap_CostOfGoodsSold", "us-gaap_CostOfServices",
    "us-gaap_FuelAndPurchasedPower", "us-gaap_FuelAndOilExpense"
}

# --- 3. OPEX ---
# The catch-all totals
OPEX_TOTAL_IDS = {
    "us-gaap_OperatingExpenses", "us-gaap_OtherOperatingIncomeExpenseNet"
}
# The specific buckets we want to break out
SG_AND_A_IDS = {
    "us-gaap_SellingGeneralAndAdministrativeExpense", "ifrs-full_AdministrativeExpense"
}
R_AND_D_IDS = {
    "us-gaap_ResearchAndDevelopmentExpense"
}
FUEL_EXPENSE_IDS = {
    "us-gaap_FuelAndOilExpense", "us-gaap_AircraftFuel"
}
# Union of all specific parts
OPEX_COMPONENT_IDS = SG_AND_A_IDS | R_AND_D_IDS | FUEL_EXPENSE_IDS

# --- 4. EBITDA ADJ ---
D_AND_A_IDS = {
    "us-gaap_DepreciationDepletionAndAmortization", "us-gaap_Depreciation",
    "us-gaap_AmortizationOfIntangibleAssets"
}
RESTRUCTURING_IDS = {
    "us-gaap_RestructuringCharges", "us-gaap_AssetImpairmentCharges"
}

# --- 5. BELOW LINE ---
INTEREST_EXP_IDS = {"us-gaap_InterestExpense", "ifrs-full_FinanceCosts"}
TAX_EXP_IDS = {"us-gaap_IncomeTaxExpenseBenefit", "ifrs-full_IncomeTaxExpenseContinuingOperations"}

# --- 6. BALANCE SHEET (Economic) ---
# For BS, double counting is less common as we sum specific line items,
# but we apply the same logic for "Current Assets" vs "Cash + AR + Inv"
NWC_CURRENT_ASSETS_TOTAL = { "us-gaap_AssetsCurrent" }
NWC_CURRENT_ASSETS_COMPS = {
    "us-gaap_AccountsReceivableNetCurrent", "us-gaap_InventoryNet",
    "us-gaap_PrepaidExpenseCurrent", "us-gaap_NontradeReceivablesCurrent",
    "us-gaap_MarketableSecuritiesCurrent", "us-gaap_OtherCurrentAssets"
}

NWC_CURRENT_LIABS_TOTAL = { "us-gaap_LiabilitiesCurrent" }
NWC_CURRENT_LIABS_COMPS = {
    "us-gaap_AccountsPayableCurrent", "us-gaap_AccruedLiabilitiesCurrent",
    "us-gaap_OtherCurrentLiabilities"
}

FIXED_ASSETS_TOTAL = { "us-gaap_AssetsNoncurrent" }
FIXED_ASSETS_COMPS = {
    "us-gaap_PropertyPlantAndEquipmentNet", "us-gaap_IntangibleAssetsNetExcludingGoodwill",
    "us-gaap_Goodwill"
}

DEBT_IDS = {
    "us-gaap_DebtInstrumentCarryingAmount", "us-gaap_LongTermDebt",
    "us-gaap_ShortTermDebt", "us-gaap_CommercialPaper", "us-gaap_SeniorNotes"
}
CASH_IDS = {
    "us-gaap_CashAndCashEquivalentsAtCarryingValue", "ifrs-full_CashAndCashEquivalents"
}
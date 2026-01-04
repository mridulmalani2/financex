"""
IB Logic Rules (JPMC/Citadel Grade)
===================================
Comprehensive concept sets for investment banking financial models.
Distinguishes between Aggregate (Total) tags and Granular (Component) tags
to enable smart double-counting prevention.

Organized by financial statement and model requirements.
"""

# =============================================================================
# INCOME STATEMENT - Revenue
# =============================================================================

# Parent Tags (The Totals)
REVENUE_TOTAL_IDS = {
    "us-gaap_Revenues",
    "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax",
    "us-gaap_SalesRevenueNet",
    "ifrs-full_Revenue",
}

# Component Tags (Granular Breakdown)
REVENUE_COMPONENT_IDS = {
    "us-gaap_SalesRevenueGoodsNet",
    "us-gaap_SalesRevenueServicesNet",
    "us-gaap_RevenueFromContractWithCustomerIncludingAssessedTax",
    "us-gaap_OtherSalesRevenueNet",
    "ifrs-full_RevenueFromSaleOfGoods",
    "ifrs-full_RevenueFromRenderingOfServices",
}

# =============================================================================
# INCOME STATEMENT - Cost of Sales
# =============================================================================

COGS_TOTAL_IDS = {
    "us-gaap_CostOfRevenue",
    "us-gaap_CostOfGoodsAndServicesSold",
    "ifrs-full_CostOfSales",
}

COGS_COMPONENT_IDS = {
    "us-gaap_CostOfGoodsSold",
    "us-gaap_CostOfServices",
    "us-gaap_CostOfGoodsSoldDirectMaterials",
    "us-gaap_CostOfGoodsSoldDirectLabor",
    "us-gaap_CostOfGoodsManufactured",
    # Industry-specific COGS
    "us-gaap_FuelAndPurchasedPower",  # Utilities
    "us-gaap_FuelAndOilExpense",  # Airlines/Transport
}

# =============================================================================
# INCOME STATEMENT - Operating Expenses
# =============================================================================

# Total OpEx (catch-all)
OPEX_TOTAL_IDS = {
    "us-gaap_OperatingExpenses",
    "us-gaap_CostsAndExpenses",
    "ifrs-full_DistributionCosts",
}

# SG&A
SG_AND_A_IDS = {
    "us-gaap_SellingGeneralAndAdministrativeExpense",
    "us-gaap_SellingAndMarketingExpense",
    "us-gaap_GeneralAndAdministrativeExpense",
    "ifrs-full_SellingExpense",
    "ifrs-full_AdministrativeExpense",
}

# R&D
R_AND_D_IDS = {
    "us-gaap_ResearchAndDevelopmentExpense",
    "us-gaap_ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
    "ifrs-full_ResearchAndDevelopmentExpense",
}

# Industry-Specific OpEx
FUEL_EXPENSE_IDS = {
    "us-gaap_FuelAndOilExpense",
    "us-gaap_AircraftFuel",
    "us-gaap_FuelCosts",
}

# Union of all known OpEx components
OPEX_COMPONENT_IDS = SG_AND_A_IDS | R_AND_D_IDS | FUEL_EXPENSE_IDS

# =============================================================================
# INCOME STATEMENT - D&A and Non-Cash Items
# =============================================================================

D_AND_A_IDS = {
    "us-gaap_DepreciationDepletionAndAmortization",
    "us-gaap_Depreciation",
    "us-gaap_DepreciationAndAmortization",
    "us-gaap_AmortizationOfIntangibleAssets",
    "us-gaap_DepreciationNonproduction",
    "ifrs-full_DepreciationAndAmortisationExpense",
    "ifrs-full_DepreciationExpense",
}

# =============================================================================
# INCOME STATEMENT - Adjustments / One-Time Items
# =============================================================================

RESTRUCTURING_IDS = {
    "us-gaap_RestructuringCharges",
    "us-gaap_RestructuringCosts",
    "us-gaap_RestructuringAndRelatedCostIncurredCost",
    "us-gaap_SeveranceCosts1",
    "ifrs-full_RestructuringProvision",
}

IMPAIRMENT_IDS = {
    "us-gaap_AssetImpairmentCharges",
    "us-gaap_GoodwillImpairmentLoss",
    "us-gaap_ImpairmentOfIntangibleAssetsExcludingGoodwill",
    "us-gaap_ImpairmentOfLongLivedAssetsHeldForUse",
    "ifrs-full_ImpairmentLossRecognisedInProfitOrLoss",
}

STOCK_COMP_IDS = {
    "us-gaap_ShareBasedCompensation",
    "us-gaap_AllocatedShareBasedCompensationExpense",
    "us-gaap_StockOptionPlanExpense",
    "ifrs-full_SharebasedPaymentArrangements",
}

# =============================================================================
# INCOME STATEMENT - Below the Line
# =============================================================================

INTEREST_EXP_IDS = {
    "us-gaap_InterestExpense",
    "us-gaap_InterestExpenseDebt",
    "us-gaap_InterestExpenseOther",
    "us-gaap_InterestAndDebtExpense",
    "ifrs-full_FinanceCosts",
    "ifrs-full_InterestExpense",
}

INTEREST_INCOME_IDS = {
    "us-gaap_InterestIncomeOperating",
    "us-gaap_InvestmentIncomeInterest",
    "us-gaap_InterestAndDividendIncomeOperating",
    "ifrs-full_InterestIncome",
}

TAX_EXP_IDS = {
    "us-gaap_IncomeTaxExpenseBenefit",
    "us-gaap_CurrentIncomeTaxExpenseBenefit",
    "us-gaap_DeferredIncomeTaxExpenseBenefit",
    "ifrs-full_IncomeTaxExpenseContinuingOperations",
}

# =============================================================================
# INCOME STATEMENT - Net Income
# =============================================================================

NET_INCOME_IDS = {
    "us-gaap_NetIncomeLoss",
    "us-gaap_ProfitLoss",
    "us-gaap_NetIncomeLossAvailableToCommonStockholdersBasic",
    "us-gaap_NetIncomeLossAttributableToParent",
    "ifrs-full_ProfitLoss",
    "ifrs-full_ProfitLossAttributableToOwnersOfParent",
}

# =============================================================================
# BALANCE SHEET - Current Assets
# =============================================================================

NWC_CURRENT_ASSETS_TOTAL = {
    "us-gaap_AssetsCurrent",
    "ifrs-full_CurrentAssets",
}

NWC_CURRENT_ASSETS_COMPS = {
    "us-gaap_CashAndCashEquivalentsAtCarryingValue",
    "us-gaap_AccountsReceivableNetCurrent",
    "us-gaap_InventoryNet",
    "us-gaap_PrepaidExpenseAndOtherAssetsCurrent",
    "us-gaap_PrepaidExpenseCurrent",
    "us-gaap_NontradeReceivablesCurrent",
    "us-gaap_MarketableSecuritiesCurrent",
    "us-gaap_OtherAssetsCurrent",
    "ifrs-full_CashAndCashEquivalents",
    "ifrs-full_TradeAndOtherCurrentReceivables",
    "ifrs-full_Inventories",
}

CASH_IDS = {
    "us-gaap_CashAndCashEquivalentsAtCarryingValue",
    "us-gaap_CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    "us-gaap_Cash",
    "ifrs-full_CashAndCashEquivalents",
    "ifrs-full_Cash",
}

# =============================================================================
# BALANCE SHEET - Current Liabilities
# =============================================================================

NWC_CURRENT_LIABS_TOTAL = {
    "us-gaap_LiabilitiesCurrent",
    "ifrs-full_CurrentLiabilities",
}

NWC_CURRENT_LIABS_COMPS = {
    "us-gaap_AccountsPayableCurrent",
    "us-gaap_AccruedLiabilitiesCurrent",
    "us-gaap_EmployeeRelatedLiabilitiesCurrent",
    "us-gaap_DeferredRevenueCurrent",
    "us-gaap_OtherLiabilitiesCurrent",
    "us-gaap_AccruedIncomeTaxesCurrent",
    "ifrs-full_TradeAndOtherCurrentPayables",
    "ifrs-full_CurrentTaxLiabilities",
}

# =============================================================================
# BALANCE SHEET - Non-Current Assets
# =============================================================================

FIXED_ASSETS_TOTAL = {
    "us-gaap_AssetsNoncurrent",
    "us-gaap_PropertyPlantAndEquipmentNet",
    "ifrs-full_NoncurrentAssets",
}

FIXED_ASSETS_COMPS = {
    "us-gaap_PropertyPlantAndEquipmentNet",
    "us-gaap_IntangibleAssetsNetExcludingGoodwill",
    "us-gaap_Goodwill",
    "us-gaap_OperatingLeaseRightOfUseAsset",
    "us-gaap_LongTermInvestments",
    "ifrs-full_PropertyPlantAndEquipment",
    "ifrs-full_IntangibleAssetsOtherThanGoodwill",
    "ifrs-full_Goodwill",
}

# =============================================================================
# BALANCE SHEET - Debt (Capital Structure)
# =============================================================================

SHORT_TERM_DEBT_IDS = {
    "us-gaap_ShortTermBorrowings",
    "us-gaap_DebtCurrent",
    "us-gaap_LongTermDebtCurrent",
    "us-gaap_CommercialPaper",
    "us-gaap_NotesPayableCurrent",
    "ifrs-full_ShorttermBorrowings",
}

LONG_TERM_DEBT_IDS = {
    "us-gaap_LongTermDebt",
    "us-gaap_LongTermDebtNoncurrent",
    "us-gaap_DebtInstrumentCarryingAmount",
    "us-gaap_SeniorNotes",
    "us-gaap_ConvertibleDebtNoncurrent",
    "us-gaap_NotesPayableNoncurrent",
    "us-gaap_SecuredDebt",
    "us-gaap_UnsecuredDebt",
    "ifrs-full_NoncurrentBorrowings",
    "ifrs-full_BondsIssued",
}

CAPITAL_LEASE_IDS = {
    "us-gaap_CapitalLeaseObligations",
    "us-gaap_FinanceLeaseLiability",
    "us-gaap_OperatingLeaseLiability",
    "us-gaap_FinanceLeaseLiabilityNoncurrent",
    "us-gaap_OperatingLeaseLiabilityNoncurrent",
    "ifrs-full_LeaseLiabilities",
}

# Combined Debt (for backwards compatibility)
DEBT_IDS = SHORT_TERM_DEBT_IDS | LONG_TERM_DEBT_IDS | CAPITAL_LEASE_IDS

# =============================================================================
# BALANCE SHEET - Equity & EV Bridge Components
# =============================================================================

EQUITY_IDS = {
    "us-gaap_StockholdersEquity",
    "us-gaap_StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    "us-gaap_RetainedEarningsAccumulatedDeficit",
    "ifrs-full_Equity",
    "ifrs-full_EquityAttributableToOwnersOfParent",
}

PREFERRED_STOCK_IDS = {
    "us-gaap_PreferredStockValue",
    "us-gaap_RedeemablePreferredStockCarryingAmount",
    "us-gaap_TemporaryEquityCarryingAmountAttributableToParent",
    "ifrs-full_PreferenceShares",
}

MINORITY_INTEREST_IDS = {
    "us-gaap_MinorityInterest",
    "us-gaap_RedeemableNoncontrollingInterestEquityCarryingAmount",
    "us-gaap_NoncontrollingInterestInConsolidatedEntity",
    "ifrs-full_NoncontrollingInterests",
}

# =============================================================================
# BALANCE SHEET - Total Assets/Liabilities (for validation)
# =============================================================================

TOTAL_ASSETS_IDS = {
    "us-gaap_Assets",
    "ifrs-full_Assets",
}

TOTAL_LIABILITIES_IDS = {
    "us-gaap_Liabilities",
    "us-gaap_LiabilitiesAndStockholdersEquity",
    "ifrs-full_Liabilities",
}

# =============================================================================
# CASH FLOW STATEMENT
# =============================================================================

CAPEX_IDS = {
    "us-gaap_PaymentsToAcquirePropertyPlantAndEquipment",
    "us-gaap_PaymentsToAcquireProductiveAssets",
    "us-gaap_CapitalExpendituresIncurredButNotYetPaid",
    "ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
}

CFO_IDS = {
    "us-gaap_NetCashProvidedByUsedInOperatingActivities",
    "ifrs-full_CashFlowsFromUsedInOperatingActivities",
}

CFI_IDS = {
    "us-gaap_NetCashProvidedByUsedInInvestingActivities",
    "ifrs-full_CashFlowsFromUsedInInvestingActivities",
}

CFF_IDS = {
    "us-gaap_NetCashProvidedByUsedInFinancingActivities",
    "ifrs-full_CashFlowsFromUsedInFinancingActivities",
}

# =============================================================================
# SHARE DATA
# =============================================================================

BASIC_SHARES_IDS = {
    "us-gaap_CommonStockSharesOutstanding",
    "us-gaap_WeightedAverageNumberOfSharesOutstandingBasic",
    "us-gaap_CommonStockSharesIssued",
    "ifrs-full_NumberOfSharesOutstanding",
}

DILUTED_SHARES_IDS = {
    "us-gaap_WeightedAverageNumberOfDilutedSharesOutstanding",
    "us-gaap_WeightedAverageNumberOfShareOutstandingBasicAndDiluted",
    "ifrs-full_WeightedAverageShares",
}

# =============================================================================
# INDUSTRY-SPECIFIC CONCEPTS
# =============================================================================

# Tech/Software
TECH_SPECIFIC_IDS = {
    "us-gaap_ResearchAndDevelopmentExpense",
    "us-gaap_CapitalizedComputerSoftwareNet",
    "us-gaap_DevelopedTechnologyRights",
}

# Financial Services
FINANCIAL_SERVICES_IDS = {
    "us-gaap_InterestAndFeeIncomeLoansAndLeases",
    "us-gaap_ProvisionForLoanLeaseAndOtherLosses",
    "us-gaap_DepositsNegotiableOrderOfWithdrawalNOW",
}

# Energy/Utilities
ENERGY_UTILITY_IDS = {
    "us-gaap_FuelAndPurchasedPower",
    "us-gaap_NuclearFuelNet",
    "us-gaap_ElectricUtilityRevenue",
}

# Healthcare/Pharma
HEALTHCARE_IDS = {
    "us-gaap_PatientServiceRevenue",
    "us-gaap_PremiumsEarnedNetLife",
    "us-gaap_MedicalCostsManaged",
}

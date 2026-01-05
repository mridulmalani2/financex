"""
IB Logic Rules (JPMC/Citadel Grade) - PRODUCTION v3.0
======================================================
Comprehensive concept sets for investment banking financial models.
Distinguishes between Aggregate (Total) tags and Granular (Component) tags
to enable smart double-counting prevention.

PRODUCTION v3.0 ENHANCEMENTS:
1. Massively expanded synonyms and child tags for EVERY bucket
2. Fuzzy keyword mappings for fallback recovery
3. Industry-specific revenue/cost variations (Tech, Banks, Insurance, etc.)
4. Alternative naming conventions from 10-K filings
5. XBRL extension tags commonly used by public companies

Philosophy: "No Silent Failures" - If a concept exists in ANY common format,
we should be able to map it.

Organized by financial statement and model requirements.
"""

# =============================================================================
# INCOME STATEMENT - Revenue (EXPANDED)
# =============================================================================

# Parent Tags (The Totals) - ALL common revenue synonyms - MASSIVELY EXPANDED
REVENUE_TOTAL_IDS = {
    # US-GAAP Primary (Most Common)
    "us-gaap_Revenues",
    "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax",
    "us-gaap_SalesRevenueNet",
    "us-gaap_SalesRevenueGoodsAndServicesNet",
    # US-GAAP Alternative naming (From 10-K filings)
    "us-gaap_RevenueFromContractWithCustomer",
    "us-gaap_NetSales",
    "us-gaap_TotalRevenues",
    "us-gaap_TotalRevenuesAndOtherIncome",
    "us-gaap_RevenuesNetOfInterestExpense",
    "us-gaap_RegulatedAndUnregulatedOperatingRevenue",
    "us-gaap_OperatingRevenues",
    "us-gaap_NetRevenueForManagementFees",
    "us-gaap_RevenueFromRelatedParties",
    # Additional common variations - PRODUCTION FIX
    "us-gaap_SalesRevenueServicesNet",
    "us-gaap_SalesRevenueGoodsNet",
    "us-gaap_RevenueRecognitionPolicyTextBlock",
    "us-gaap_SalesAndOtherOperatingRevenue",
    "us-gaap_RealEstateRevenueNet",
    "us-gaap_HealthCareOrganizationRevenue",
    "us-gaap_BrokerageCommissionsRevenue",
    "us-gaap_InvestmentBankingRevenue",
    "us-gaap_UnderwritingIncome",
    "us-gaap_AdvisoryFeesRevenue",
    "us-gaap_InsurancePremiumsRevenueRecognized",
    "us-gaap_PremiumsEarnedNet",
    # Tech/SaaS specific
    "us-gaap_SubscriptionRevenue",
    "us-gaap_SaaSRevenue",
    "us-gaap_CloudServicesRevenue",
    "us-gaap_PlatformRevenue",
    # Financial Services specific
    "us-gaap_InterestAndDividendIncomeOperating",
    "us-gaap_FeesAndCommissions",
    "us-gaap_TradingGainsLosses",
    "us-gaap_GainsLossesOnSalesOfAssets",
    # Retail/Consumer
    "us-gaap_RetailRevenue",
    "us-gaap_WholesaleRevenue",
    "us-gaap_FranchiseRevenue",
    "us-gaap_MembershipRevenue",
    # IFRS alternatives (expanded)
    "ifrs-full_Revenue",
    "ifrs-full_RevenueFromContractsWithCustomers",
    "ifrs-full_TotalRevenue",
    "ifrs-full_RevenueFromSaleOfGoodsAndRenderingOfServices",
    "ifrs-full_GrossRevenue",
    "ifrs-full_TurnoverRevenue",
    "ifrs-full_SalesRevenue",
}

# Component Tags (Granular Breakdown) - EXPANDED
REVENUE_COMPONENT_IDS = {
    # Products/Goods
    "us-gaap_SalesRevenueGoodsNet",
    "us-gaap_SalesRevenueGoodsGross",
    "us-gaap_RevenueFromSaleOfProduct",
    "us-gaap_ProductRevenue",
    "us-gaap_RevenueFromSalesOfGoods",
    # Services
    "us-gaap_SalesRevenueServicesNet",
    "us-gaap_SalesRevenueServicesGross",
    "us-gaap_RevenueFromServicesRendered",
    "us-gaap_ServiceRevenue",
    "us-gaap_RevenueFromServicesNet",
    # Contract Revenue
    "us-gaap_RevenueFromContractWithCustomerIncludingAssessedTax",
    "us-gaap_ContractWithCustomerLiabilityRevenueRecognized",
    # Other Revenue
    "us-gaap_OtherSalesRevenueNet",
    "us-gaap_OtherRevenue",
    "us-gaap_OtherRevenuesNetOfInterestExpense",
    "us-gaap_OtherOperatingIncome",
    # Subscription/Recurring
    "us-gaap_SubscriptionRevenue",
    "us-gaap_RecurringRevenue",
    "us-gaap_MaintenanceRevenue",
    # Licensing
    "us-gaap_LicenseRevenue",
    "us-gaap_LicensingRevenue",
    "us-gaap_TechnologyServicesRevenue",
    "us-gaap_RoyaltyRevenue",
    # Geographic Segment Revenue
    "us-gaap_RevenueFromExternalCustomersByGeographicAreasTableTextBlock",
    # IFRS Components
    "ifrs-full_RevenueFromSaleOfGoods",
    "ifrs-full_RevenueFromRenderingOfServices",
    "ifrs-full_RevenueFromInterest",
    "ifrs-full_RevenueFromDividends",
    "ifrs-full_RevenueFromRoyalties",
    "ifrs-full_OtherRevenue",
}

# =============================================================================
# INCOME STATEMENT - Cost of Sales (EXPANDED)
# =============================================================================

COGS_TOTAL_IDS = {
    # Primary COGS totals
    "us-gaap_CostOfRevenue",
    "us-gaap_CostOfGoodsAndServicesSold",
    "us-gaap_CostOfGoodsSold",
    "us-gaap_CostOfSales",
    "us-gaap_CostOfProductsSold",
    "us-gaap_CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization",
    "us-gaap_CostOfGoodsSoldExcludingDepreciationDepletionAndAmortization",
    "us-gaap_TotalCostOfRevenue",
    # IFRS
    "ifrs-full_CostOfSales",
    "ifrs-full_CostOfMerchandiseSold",
    "ifrs-full_CostOfGoodsSold",
}

COGS_COMPONENT_IDS = {
    # Products COGS
    "us-gaap_CostOfGoodsSoldProducts",
    "us-gaap_CostOfProductsAndServicesSold",
    # Services COGS
    "us-gaap_CostOfServices",
    "us-gaap_CostOfServicesRendered",
    "us-gaap_CostOfServicesSold",
    # Materials and Labor
    "us-gaap_CostOfGoodsSoldDirectMaterials",
    "us-gaap_CostOfGoodsSoldDirectLabor",
    "us-gaap_DirectOperatingCosts",
    "us-gaap_CostOfGoodsManufactured",
    "us-gaap_DirectCostsOfLeasedAndRentedPropertyOrEquipment",
    # Overhead
    "us-gaap_CostOfGoodsSoldManufacturingOverhead",
    "us-gaap_ManufacturingCosts",
    "us-gaap_ProductionCosts",
    # Subscription/Services COGS
    "us-gaap_CostOfSubscriptionServices",
    "us-gaap_CostOfSupportServices",
    "us-gaap_CostOfMaintenanceRevenue",
    # Industry-specific COGS
    "us-gaap_FuelAndPurchasedPower",  # Utilities
    "us-gaap_FuelAndOilExpense",  # Airlines/Transport
    "us-gaap_CostOfRealEstateRevenue",  # Real Estate
    "us-gaap_CostOfFinancialServicesRevenue",  # Financial Services
    "us-gaap_CostOfHealthcareRevenue",  # Healthcare
    # Depreciation in COGS
    "us-gaap_CostOfGoodsSoldDepreciation",
    "us-gaap_DepreciationCostOfSales",
    # IFRS
    "ifrs-full_RawMaterialsAndConsumablesUsed",
    "ifrs-full_DirectLabourCosts",
    "ifrs-full_ManufacturingOverhead",
}

# =============================================================================
# INCOME STATEMENT - Operating Expenses (EXPANDED)
# =============================================================================

# Total OpEx (catch-all)
OPEX_TOTAL_IDS = {
    "us-gaap_OperatingExpenses",
    "us-gaap_CostsAndExpenses",
    "us-gaap_OperatingCostsAndExpenses",
    "us-gaap_TotalOperatingExpenses",
    "us-gaap_OtherOperatingExpenses",
    "us-gaap_NoninterestExpense",  # Banks
    "ifrs-full_DistributionCosts",
    "ifrs-full_OperatingExpense",
    "ifrs-full_OtherExpenseByNature",
}

# SG&A - EXPANDED
SG_AND_A_IDS = {
    # Combined SG&A
    "us-gaap_SellingGeneralAndAdministrativeExpense",
    "us-gaap_SellingGeneralAndAdministrativeExpenseExcludingDepreciationAndAmortization",
    # Selling & Marketing
    "us-gaap_SellingAndMarketingExpense",
    "us-gaap_SellingExpense",
    "us-gaap_MarketingExpense",
    "us-gaap_AdvertisingExpense",
    "us-gaap_SalesCommissions",
    "us-gaap_SellingAndMarketingCosts",
    # General & Administrative
    "us-gaap_GeneralAndAdministrativeExpense",
    "us-gaap_AdministrativeExpense",
    "us-gaap_OtherGeneralExpense",
    "us-gaap_ProfessionalFees",
    "us-gaap_LegalFees",
    "us-gaap_AccountingFees",
    "us-gaap_InsuranceExpense",
    "us-gaap_RentExpense",
    "us-gaap_UtilitiesExpense",
    "us-gaap_TravelAndEntertainment",
    # Compensation
    "us-gaap_LaborAndRelatedExpense",
    "us-gaap_SalariesAndWages",
    "us-gaap_EmployeeBenefitsAndShareBasedCompensation",
    "us-gaap_PayrollExpense",
    # IFRS
    "ifrs-full_SellingExpense",
    "ifrs-full_AdministrativeExpense",
    "ifrs-full_GeneralAndAdministrativeExpense",
    "ifrs-full_DistributionCosts",
    "ifrs-full_EmployeeBenefitsExpense",
}

# R&D - EXPANDED
R_AND_D_IDS = {
    "us-gaap_ResearchAndDevelopmentExpense",
    "us-gaap_ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
    "us-gaap_ResearchAndDevelopmentExpenseSoftwareExcludingAcquiredInProcessCost",
    "us-gaap_ResearchAndDevelopmentInProcess",
    "us-gaap_DevelopmentCosts",
    "us-gaap_TechnologyExpense",
    "us-gaap_EngineeringExpense",
    "us-gaap_SoftwareDevelopmentCosts",
    # IFRS
    "ifrs-full_ResearchAndDevelopmentExpense",
    "ifrs-full_ResearchExpense",
    "ifrs-full_DevelopmentExpense",
}

# Industry-Specific OpEx - EXPANDED
FUEL_EXPENSE_IDS = {
    "us-gaap_FuelAndOilExpense",
    "us-gaap_AircraftFuel",
    "us-gaap_FuelCosts",
    "us-gaap_FuelExpense",
    "us-gaap_NaturalGasPurchases",
    "us-gaap_ElectricityPurchases",
}

# Additional OpEx Categories
OTHER_OPEX_IDS = {
    "us-gaap_OtherOperatingIncomeExpenseNet",
    "us-gaap_OtherCostAndExpenseOperating",
    "us-gaap_OtherNonoperatingIncomeExpense",
    "us-gaap_OtherExpenses",
    "us-gaap_MiscellaneousOperatingExpense",
    "us-gaap_CommunicationsExpense",
    "us-gaap_OccupancyExpense",
    # IFRS
    "ifrs-full_OtherExpense",
    "ifrs-full_OtherOperatingExpense",
}

# Union of all known OpEx components
OPEX_COMPONENT_IDS = SG_AND_A_IDS | R_AND_D_IDS | FUEL_EXPENSE_IDS | OTHER_OPEX_IDS

# =============================================================================
# INCOME STATEMENT - D&A and Non-Cash Items (EXPANDED)
# =============================================================================

D_AND_A_IDS = {
    # Combined D&A
    "us-gaap_DepreciationDepletionAndAmortization",
    "us-gaap_DepreciationAndAmortization",
    "us-gaap_DepreciationAmortizationAndAccretionNet",
    # Depreciation
    "us-gaap_Depreciation",
    "us-gaap_DepreciationNonproduction",
    "us-gaap_DepreciationExpenseOnReclassifiedAssets",
    "us-gaap_DepreciationOfPropertyPlantAndEquipment",
    # Amortization
    "us-gaap_AmortizationOfIntangibleAssets",
    "us-gaap_AmortizationOfDeferredCharges",
    "us-gaap_AmortizationOfFinancingCosts",
    "us-gaap_AmortizationOfDebtDiscountPremium",
    "us-gaap_AmortizationOfAcquisitionCosts",
    "us-gaap_OtherAmortizationOfDeferredCharges",
    # Right-of-use asset depreciation
    "us-gaap_OperatingLeaseRightOfUseAssetAmortizationExpense",
    "us-gaap_FinanceLeaseRightOfUseAssetAmortization",
    # IFRS
    "ifrs-full_DepreciationAndAmortisationExpense",
    "ifrs-full_DepreciationExpense",
    "ifrs-full_AmortisationExpense",
    "ifrs-full_DepreciationPropertyPlantAndEquipment",
    "ifrs-full_AmortisationIntangibleAssets",
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
# INCOME STATEMENT - Net Income (EXPANDED)
# =============================================================================

NET_INCOME_IDS = {
    # Primary Net Income
    "us-gaap_NetIncomeLoss",
    "us-gaap_ProfitLoss",
    "us-gaap_NetIncomeLossAvailableToCommonStockholdersBasic",
    "us-gaap_NetIncomeLossAvailableToCommonStockholdersDiluted",
    "us-gaap_NetIncomeLossAttributableToParent",
    # From Continuing Operations
    "us-gaap_IncomeLossFromContinuingOperations",
    "us-gaap_IncomeLossFromContinuingOperationsIncludingPortionAttributableToNoncontrollingInterest",
    "us-gaap_IncomeLossFromContinuingOperationsAttributableToParent",
    # Comprehensive Income
    "us-gaap_ComprehensiveIncomeNetOfTax",
    "us-gaap_ComprehensiveIncomeNetOfTaxAttributableToParent",
    # Earnings alternatives
    "us-gaap_NetEarnings",
    "us-gaap_NetEarningsLoss",
    "us-gaap_ConsolidatedNetIncome",
    # Before noncontrolling interest
    "us-gaap_NetIncomeLossIncludingPortionAttributableToNoncontrollingInterest",
    "us-gaap_ProfitLossBeforeNoncontrollingInterests",
    # Operating Income (fallback)
    "us-gaap_OperatingIncomeLoss",
    "us-gaap_IncomeLossFromOperations",
    # IFRS
    "ifrs-full_ProfitLoss",
    "ifrs-full_ProfitLossAttributableToOwnersOfParent",
    "ifrs-full_ProfitLossFromContinuingOperations",
    "ifrs-full_ComprehensiveIncome",
    "ifrs-full_ProfitLossBeforeTax",
}

# Operating Income IDs (for EBIT fallback)
OPERATING_INCOME_IDS = {
    "us-gaap_OperatingIncomeLoss",
    "us-gaap_IncomeLossFromOperations",
    "us-gaap_IncomeFromOperations",
    "us-gaap_OperatingProfit",
    "us-gaap_OperatingProfitLoss",
    "ifrs-full_OperatingProfit",
    "ifrs-full_ProfitLossFromOperatingActivities",
}

# =============================================================================
# BALANCE SHEET - Current Assets (EXPANDED)
# =============================================================================

NWC_CURRENT_ASSETS_TOTAL = {
    "us-gaap_AssetsCurrent",
    "us-gaap_TotalCurrentAssets",
    "ifrs-full_CurrentAssets",
}

NWC_CURRENT_ASSETS_COMPS = {
    # Cash
    "us-gaap_CashAndCashEquivalentsAtCarryingValue",
    "us-gaap_CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    # Receivables
    "us-gaap_AccountsReceivableNetCurrent",
    "us-gaap_AccountsReceivableNet",
    "us-gaap_ReceivablesNetCurrent",
    "us-gaap_TradeReceivables",
    "us-gaap_AccountsNotesAndLoansReceivableNetCurrent",
    "us-gaap_NontradeReceivablesCurrent",
    # Inventory
    "us-gaap_InventoryNet",
    "us-gaap_InventoryFinishedGoodsAndWorkInProcess",
    "us-gaap_InventoryRawMaterialsAndSupplies",
    "us-gaap_InventoryGross",
    # Prepaid and Other
    "us-gaap_PrepaidExpenseAndOtherAssetsCurrent",
    "us-gaap_PrepaidExpenseCurrent",
    "us-gaap_OtherPrepaidExpenseCurrent",
    "us-gaap_OtherAssetsCurrent",
    "us-gaap_DeferredCostsCurrent",
    # Marketable Securities
    "us-gaap_MarketableSecuritiesCurrent",
    "us-gaap_ShortTermInvestments",
    "us-gaap_AvailableForSaleSecuritiesCurrent",
    # Contract Assets
    "us-gaap_ContractWithCustomerAssetNetCurrent",
    # IFRS
    "ifrs-full_CashAndCashEquivalents",
    "ifrs-full_TradeAndOtherCurrentReceivables",
    "ifrs-full_Inventories",
    "ifrs-full_PrepaidExpenses",
    "ifrs-full_OtherCurrentAssets",
}

# Cash and Cash Equivalents - EXPANDED
CASH_IDS = {
    # Primary Cash
    "us-gaap_CashAndCashEquivalentsAtCarryingValue",
    "us-gaap_Cash",
    "us-gaap_CashEquivalentsAtCarryingValue",
    "us-gaap_CashAndDueFromBanks",
    # Restricted Cash
    "us-gaap_CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    "us-gaap_RestrictedCashAndCashEquivalents",
    "us-gaap_RestrictedCash",
    "us-gaap_RestrictedCashCurrent",
    # Short-term investments often treated as cash
    "us-gaap_CashCashEquivalentsAndShortTermInvestments",
    "us-gaap_CashAndShortTermInvestments",
    # IFRS
    "ifrs-full_CashAndCashEquivalents",
    "ifrs-full_Cash",
    "ifrs-full_CashOnHand",
    "ifrs-full_RestrictedCashAndCashEquivalents",
}

# Inventory IDs - EXPANDED
INVENTORY_IDS = {
    "us-gaap_InventoryNet",
    "us-gaap_InventoryGross",
    "us-gaap_InventoryFinishedGoodsAndWorkInProcess",
    "us-gaap_InventoryFinishedGoods",
    "us-gaap_InventoryWorkInProcess",
    "us-gaap_InventoryRawMaterialsAndSupplies",
    "us-gaap_InventoryRawMaterials",
    "us-gaap_InventorySupplies",
    "us-gaap_RetailRelatedInventory",
    # IFRS
    "ifrs-full_Inventories",
    "ifrs-full_InventoriesTotal",
    "ifrs-full_RawMaterials",
    "ifrs-full_FinishedGoods",
    "ifrs-full_WorkInProgress",
}

# Accounts Receivable - EXPANDED
ACCOUNTS_RECEIVABLE_IDS = {
    "us-gaap_AccountsReceivableNetCurrent",
    "us-gaap_AccountsReceivableNet",
    "us-gaap_ReceivablesNetCurrent",
    "us-gaap_TradeReceivables",
    "us-gaap_AccountsNotesAndLoansReceivableNetCurrent",
    "us-gaap_AccountsReceivableGrossCurrent",
    "us-gaap_BilledContractReceivables",
    # IFRS
    "ifrs-full_TradeAndOtherCurrentReceivables",
    "ifrs-full_TradeReceivables",
    "ifrs-full_ReceivablesFromContractsWithCustomers",
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
# CASH FLOW STATEMENT (EXPANDED)
# =============================================================================

# Capital Expenditures - CRITICAL for DCF
CAPEX_IDS = {
    # Primary CapEx
    "us-gaap_PaymentsToAcquirePropertyPlantAndEquipment",
    "us-gaap_CapitalExpenditures",
    "us-gaap_PaymentsToAcquireProductiveAssets",
    "us-gaap_CapitalExpendituresIncurredButNotYetPaid",
    # Additions to PP&E
    "us-gaap_PropertyPlantAndEquipmentAdditions",
    "us-gaap_AdditionsToPropertyPlantAndEquipment",
    # Software/Intangible CapEx
    "us-gaap_PaymentsToAcquireIntangibleAssets",
    "us-gaap_PaymentsForSoftware",
    "us-gaap_CapitalizedComputerSoftwareAdditions",
    # Leased Assets CapEx
    "us-gaap_PaymentsToAcquireAssetsUnderFinanceLease",
    # Combined metrics
    "us-gaap_PaymentsToAcquireOtherProductiveAssets",
    "us-gaap_PurchaseOfPropertyPlantAndEquipmentIntangibleAssetsOtherThanGoodwillInvestmentPropertyAndOtherNoncurrentAssets",
    # IFRS
    "ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
    "ifrs-full_PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities",
    "ifrs-full_AcquisitionOfPropertyPlantAndEquipment",
}

CFO_IDS = {
    "us-gaap_NetCashProvidedByUsedInOperatingActivities",
    "us-gaap_CashProvidedByUsedInOperatingActivities",
    "us-gaap_NetCashProvidedByOperatingActivities",
    "us-gaap_OperatingActivitiesCashFlowsAbstract",
    # IFRS
    "ifrs-full_CashFlowsFromUsedInOperatingActivities",
    "ifrs-full_CashGeneratedFromOperations",
}

CFI_IDS = {
    "us-gaap_NetCashProvidedByUsedInInvestingActivities",
    "us-gaap_CashProvidedByUsedInInvestingActivities",
    "us-gaap_NetCashUsedInInvestingActivities",
    # IFRS
    "ifrs-full_CashFlowsFromUsedInInvestingActivities",
}

CFF_IDS = {
    "us-gaap_NetCashProvidedByUsedInFinancingActivities",
    "us-gaap_CashProvidedByUsedInFinancingActivities",
    "us-gaap_NetCashUsedInFinancingActivities",
    # IFRS
    "ifrs-full_CashFlowsFromUsedInFinancingActivities",
}

# Free Cash Flow
FREE_CASH_FLOW_IDS = {
    "us-gaap_FreeCashFlow",
    "us-gaap_CashFlowFromOperationsLessCapitalExpenditures",
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

# =============================================================================
# KEYWORD FALLBACK MAPPINGS (for Sanity Loop Recovery) - PRODUCTION v3.0
# =============================================================================
# These keywords are used when critical buckets are zero to force-map
# any items that contain these keywords to prevent empty models
#
# PRODUCTION FIX: Massively expanded with common variations from real 10-K filings

KEYWORD_FALLBACK_MAPPINGS = {
    # Revenue - Primary keywords
    "revenue": REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS,
    "revenues": REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS,
    "sales": REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS,
    "net sales": REVENUE_TOTAL_IDS,
    "total sales": REVENUE_TOTAL_IDS,
    "total revenue": REVENUE_TOTAL_IDS,
    "total revenues": REVENUE_TOTAL_IDS,
    "gross revenue": REVENUE_TOTAL_IDS,
    "net revenue": REVENUE_TOTAL_IDS,
    "operating revenue": REVENUE_TOTAL_IDS,
    # Revenue - Industry variations
    "premiums": REVENUE_TOTAL_IDS,
    "fees": REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS,
    "commissions": REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS,
    "subscription": REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS,
    "licensing": REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS,
    "royalt": REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS,
    "turnover": REVENUE_TOTAL_IDS,

    # Cost of Sales - Primary keywords
    "cost of": COGS_TOTAL_IDS | COGS_COMPONENT_IDS,
    "cogs": COGS_TOTAL_IDS | COGS_COMPONENT_IDS,
    "cost of goods": COGS_TOTAL_IDS | COGS_COMPONENT_IDS,
    "cost of sales": COGS_TOTAL_IDS,
    "cost of revenue": COGS_TOTAL_IDS,
    "cost of services": COGS_TOTAL_IDS | COGS_COMPONENT_IDS,
    "cost of products": COGS_TOTAL_IDS | COGS_COMPONENT_IDS,
    "direct cost": COGS_TOTAL_IDS | COGS_COMPONENT_IDS,
    "cost of merchandise": COGS_TOTAL_IDS,
    "manufacturing cost": COGS_TOTAL_IDS | COGS_COMPONENT_IDS,
    "production cost": COGS_TOTAL_IDS | COGS_COMPONENT_IDS,

    # Net Income - Primary keywords
    "net income": NET_INCOME_IDS,
    "net loss": NET_INCOME_IDS,
    "profit": NET_INCOME_IDS,
    "loss": NET_INCOME_IDS,
    "earnings": NET_INCOME_IDS,
    "net earnings": NET_INCOME_IDS,
    "bottom line": NET_INCOME_IDS,
    "income from continuing": NET_INCOME_IDS,
    "comprehensive income": NET_INCOME_IDS,
    "attributable to parent": NET_INCOME_IDS,
    "attributable to shareholders": NET_INCOME_IDS,

    # Operating Income
    "operating income": OPERATING_INCOME_IDS,
    "operating profit": OPERATING_INCOME_IDS,
    "operating loss": OPERATING_INCOME_IDS,
    "income from operations": OPERATING_INCOME_IDS,
    "profit from operations": OPERATING_INCOME_IDS,
    "operating earnings": OPERATING_INCOME_IDS,

    # EBITDA is calculated, not directly mapped - but we can look for reported EBITDA
    "ebitda": set(),
    "adjusted ebitda": set(),

    # Depreciation & Amortization
    "depreciation": D_AND_A_IDS,
    "amortization": D_AND_A_IDS,
    "d&a": D_AND_A_IDS,
    "depr": D_AND_A_IDS,
    "amort": D_AND_A_IDS,
    "depreciation and amortization": D_AND_A_IDS,
    "depreciation expense": D_AND_A_IDS,
    "amortization expense": D_AND_A_IDS,

    # CapEx
    "capex": CAPEX_IDS,
    "capital expenditure": CAPEX_IDS,
    "capital spending": CAPEX_IDS,
    "pp&e": CAPEX_IDS | FIXED_ASSETS_COMPS,
    "ppe": CAPEX_IDS | FIXED_ASSETS_COMPS,
    "property plant": CAPEX_IDS | FIXED_ASSETS_COMPS,
    "property, plant": CAPEX_IDS | FIXED_ASSETS_COMPS,
    "purchases of property": CAPEX_IDS,
    "additions to property": CAPEX_IDS,
    "purchases of equipment": CAPEX_IDS,

    # Inventory
    "inventory": INVENTORY_IDS,
    "inventories": INVENTORY_IDS,
    "merchandise": INVENTORY_IDS,
    "finished goods": INVENTORY_IDS,
    "work in process": INVENTORY_IDS,
    "raw materials": INVENTORY_IDS,

    # Cash
    "cash": CASH_IDS,
    "cash and cash equivalent": CASH_IDS,
    "cash & cash equivalent": CASH_IDS,
    "cash and equivalents": CASH_IDS,
    "short-term investment": CASH_IDS,
    "short term investment": CASH_IDS,
    "marketable securities": CASH_IDS,

    # Receivables
    "receivable": ACCOUNTS_RECEIVABLE_IDS,
    "receivables": ACCOUNTS_RECEIVABLE_IDS,
    "accounts receivable": ACCOUNTS_RECEIVABLE_IDS,
    "trade receivable": ACCOUNTS_RECEIVABLE_IDS,
    "a/r": ACCOUNTS_RECEIVABLE_IDS,
    "ar": ACCOUNTS_RECEIVABLE_IDS,

    # Debt
    "debt": DEBT_IDS,
    "borrowing": DEBT_IDS,
    "borrowings": DEBT_IDS,
    "notes payable": DEBT_IDS,
    "bonds": DEBT_IDS,
    "loans": DEBT_IDS,
    "credit facility": DEBT_IDS,
    "long-term debt": LONG_TERM_DEBT_IDS,
    "long term debt": LONG_TERM_DEBT_IDS,
    "short-term debt": SHORT_TERM_DEBT_IDS,
    "short term debt": SHORT_TERM_DEBT_IDS,
    "current portion of debt": SHORT_TERM_DEBT_IDS,
    "current maturities": SHORT_TERM_DEBT_IDS,

    # Taxes
    "tax": TAX_EXP_IDS,
    "taxes": TAX_EXP_IDS,
    "income tax": TAX_EXP_IDS,
    "provision for": TAX_EXP_IDS,
    "tax expense": TAX_EXP_IDS,
    "tax benefit": TAX_EXP_IDS,

    # SG&A
    "sg&a": SG_AND_A_IDS,
    "sga": SG_AND_A_IDS,
    "selling": SG_AND_A_IDS,
    "general and admin": SG_AND_A_IDS,
    "general & admin": SG_AND_A_IDS,
    "g&a": SG_AND_A_IDS,
    "administrative": SG_AND_A_IDS,
    "marketing": SG_AND_A_IDS,
    "advertising": SG_AND_A_IDS,
    "salaries": SG_AND_A_IDS,
    "compensation": SG_AND_A_IDS,
    "employee": SG_AND_A_IDS,

    # R&D
    "r&d": R_AND_D_IDS,
    "rnd": R_AND_D_IDS,
    "research": R_AND_D_IDS,
    "development": R_AND_D_IDS,
    "research and development": R_AND_D_IDS,
    "product development": R_AND_D_IDS,
    "technology": R_AND_D_IDS,
    "engineering": R_AND_D_IDS,

    # Interest
    "interest expense": INTEREST_EXP_IDS,
    "interest cost": INTEREST_EXP_IDS,
    "finance cost": INTEREST_EXP_IDS,
    "financing cost": INTEREST_EXP_IDS,
    "interest income": INTEREST_INCOME_IDS,
    "interest earned": INTEREST_INCOME_IDS,

    # Equity
    "equity": EQUITY_IDS,
    "stockholder": EQUITY_IDS,
    "shareholder": EQUITY_IDS,
    "retained earnings": EQUITY_IDS,
    "accumulated deficit": EQUITY_IDS,

    # Assets/Liabilities totals
    "total assets": TOTAL_ASSETS_IDS,
    "total liabilities": TOTAL_LIABILITIES_IDS,
    "current assets": NWC_CURRENT_ASSETS_TOTAL,
    "current liabilities": NWC_CURRENT_LIABS_TOTAL,

    # Cash Flow
    "cash from operations": CFO_IDS,
    "operating cash": CFO_IDS,
    "cash from investing": CFI_IDS,
    "investing activities": CFI_IDS,
    "cash from financing": CFF_IDS,
    "financing activities": CFF_IDS,
    "free cash flow": FREE_CASH_FLOW_IDS,
    "fcf": FREE_CASH_FLOW_IDS,
}

# Critical buckets that MUST NOT be zero for a valid model
CRITICAL_DCF_BUCKETS = {
    "Total Revenue": REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS,
    "Net Income": NET_INCOME_IDS,
    "EBITDA": None,  # Calculated, validated separately
}

CRITICAL_LBO_BUCKETS = {
    "EBITDA": None,  # Calculated
    "Total Debt": DEBT_IDS,
}

CRITICAL_COMPS_BUCKETS = {
    "Revenue": REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS,
    "Net Income": NET_INCOME_IDS,
}

# =============================================================================
# FUZZY MATCHING HELPERS - PRODUCTION v3.0
# =============================================================================
# These functions help with fallback recovery when exact matching fails

def fuzzy_match_bucket(source_label: str) -> tuple:
    """
    Fuzzy match a source label to a bucket using keyword matching.

    Returns:
        tuple: (bucket_name, concept_set) if found, (None, None) otherwise

    Example:
        >>> fuzzy_match_bucket("Total Net Sales Revenue")
        ("Revenue", REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS)
    """
    label_lower = source_label.lower().strip()

    # Score each keyword match
    best_match = None
    best_score = 0

    for keyword, concept_set in KEYWORD_FALLBACK_MAPPINGS.items():
        if keyword in label_lower:
            # Score based on keyword length and position
            score = len(keyword)
            if label_lower.startswith(keyword):
                score += 10  # Bonus for prefix match
            if label_lower == keyword:
                score += 50  # Exact match bonus

            if score > best_score:
                best_score = score
                best_match = (keyword, concept_set)

    if best_match:
        keyword, concept_set = best_match
        # Map keyword to bucket name
        bucket_map = {
            "revenue": "Total Revenue",
            "revenues": "Total Revenue",
            "sales": "Total Revenue",
            "net sales": "Total Revenue",
            "total revenue": "Total Revenue",
            "cost of": "COGS",
            "cogs": "COGS",
            "cost of goods": "COGS",
            "cost of sales": "COGS",
            "cost of revenue": "COGS",
            "net income": "Net Income",
            "profit": "Net Income",
            "earnings": "Net Income",
            "operating income": "Operating Income",
            "depreciation": "D&A",
            "amortization": "D&A",
            "capex": "CapEx",
            "capital expenditure": "CapEx",
            "inventory": "Inventory",
            "cash": "Cash",
            "receivable": "Accounts Receivable",
            "debt": "Total Debt",
            "tax": "Taxes",
            "sg&a": "SG&A",
            "r&d": "R&D",
            "research": "R&D",
        }

        bucket_name = None
        for k, v in bucket_map.items():
            if keyword.startswith(k) or k in keyword:
                bucket_name = v
                break

        if bucket_name:
            return (bucket_name, concept_set)

    return (None, None)


def get_all_concept_sets() -> dict:
    """
    Get a dictionary of all concept sets for validation purposes.

    Returns:
        dict: {bucket_name: concept_set}
    """
    return {
        "Revenue": REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS,
        "COGS": COGS_TOTAL_IDS | COGS_COMPONENT_IDS,
        "SG&A": SG_AND_A_IDS,
        "R&D": R_AND_D_IDS,
        "OpEx": OPEX_TOTAL_IDS | OPEX_COMPONENT_IDS,
        "D&A": D_AND_A_IDS,
        "Net Income": NET_INCOME_IDS,
        "Operating Income": OPERATING_INCOME_IDS,
        "Interest Expense": INTEREST_EXP_IDS,
        "Interest Income": INTEREST_INCOME_IDS,
        "Taxes": TAX_EXP_IDS,
        "Cash": CASH_IDS,
        "Inventory": INVENTORY_IDS,
        "Accounts Receivable": ACCOUNTS_RECEIVABLE_IDS,
        "Current Assets": NWC_CURRENT_ASSETS_TOTAL | NWC_CURRENT_ASSETS_COMPS,
        "Current Liabilities": NWC_CURRENT_LIABS_TOTAL | NWC_CURRENT_LIABS_COMPS,
        "Fixed Assets": FIXED_ASSETS_TOTAL | FIXED_ASSETS_COMPS,
        "Short-Term Debt": SHORT_TERM_DEBT_IDS,
        "Long-Term Debt": LONG_TERM_DEBT_IDS,
        "Total Debt": DEBT_IDS,
        "Equity": EQUITY_IDS,
        "Total Assets": TOTAL_ASSETS_IDS,
        "Total Liabilities": TOTAL_LIABILITIES_IDS,
        "CapEx": CAPEX_IDS,
        "CFO": CFO_IDS,
        "CFI": CFI_IDS,
        "CFF": CFF_IDS,
    }


def suggest_mapping(source_label: str) -> list:
    """
    Suggest possible mappings for a source label based on fuzzy matching.

    Returns:
        list: List of (bucket_name, confidence) tuples sorted by confidence
    """
    label_lower = source_label.lower().strip()
    suggestions = []

    for keyword, concept_set in KEYWORD_FALLBACK_MAPPINGS.items():
        if keyword in label_lower or any(word in label_lower for word in keyword.split()):
            # Calculate confidence
            if label_lower == keyword:
                confidence = 1.0
            elif label_lower.startswith(keyword):
                confidence = 0.9
            elif keyword in label_lower:
                confidence = 0.7 + (len(keyword) / len(label_lower)) * 0.2
            else:
                confidence = 0.5

            suggestions.append((keyword, confidence, concept_set))

    # Sort by confidence
    suggestions.sort(key=lambda x: x[1], reverse=True)
    return suggestions[:5]  # Top 5 suggestions

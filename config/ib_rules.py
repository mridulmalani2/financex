"""
IB Logic Rules (JPMC/Citadel Grade) - EXPANDED v2.1
=====================================================
Comprehensive concept sets for investment banking financial models.
Distinguishes between Aggregate (Total) tags and Granular (Component) tags
to enable smart double-counting prevention.

CRITICAL FIX: Expanded with common synonyms, hierarchy parents, and
alternative naming conventions to ensure "Apple-Level" accuracy.

Organized by financial statement and model requirements.
"""

# =============================================================================
# INCOME STATEMENT - Revenue (EXPANDED)
# =============================================================================

# Parent Tags (The Totals) - ALL common revenue synonyms
REVENUE_TOTAL_IDS = {
    # US-GAAP Primary
    "us-gaap_Revenues",
    "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax",
    "us-gaap_SalesRevenueNet",
    "us-gaap_SalesRevenueGoodsAndServicesNet",
    # US-GAAP Alternative naming
    "us-gaap_RevenueFromContractWithCustomer",
    "us-gaap_NetSales",
    "us-gaap_TotalRevenues",
    "us-gaap_TotalRevenuesAndOtherIncome",
    "us-gaap_RevenuesNetOfInterestExpense",
    "us-gaap_RegulatedAndUnregulatedOperatingRevenue",
    "us-gaap_OperatingRevenues",
    "us-gaap_NetRevenueForManagementFees",
    "us-gaap_RevenueFromRelatedParties",
    # IFRS alternatives
    "ifrs-full_Revenue",
    "ifrs-full_RevenueFromContractsWithCustomers",
    "ifrs-full_TotalRevenue",
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
# KEYWORD FALLBACK MAPPINGS (for Sanity Loop Recovery)
# =============================================================================
# These keywords are used when critical buckets are zero to force-map
# any items that contain these keywords to prevent empty models

KEYWORD_FALLBACK_MAPPINGS = {
    "revenue": REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS,
    "sales": REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS,
    "net sales": REVENUE_TOTAL_IDS,
    "total revenue": REVENUE_TOTAL_IDS,
    "cost of": COGS_TOTAL_IDS | COGS_COMPONENT_IDS,
    "cogs": COGS_TOTAL_IDS | COGS_COMPONENT_IDS,
    "cost of goods": COGS_TOTAL_IDS | COGS_COMPONENT_IDS,
    "cost of revenue": COGS_TOTAL_IDS,
    "net income": NET_INCOME_IDS,
    "profit": NET_INCOME_IDS,
    "earnings": NET_INCOME_IDS,
    "net earnings": NET_INCOME_IDS,
    "operating income": OPERATING_INCOME_IDS,
    "ebitda": set(),  # EBITDA is calculated, not directly mapped
    "depreciation": D_AND_A_IDS,
    "amortization": D_AND_A_IDS,
    "d&a": D_AND_A_IDS,
    "capex": CAPEX_IDS,
    "capital expenditure": CAPEX_IDS,
    "pp&e": CAPEX_IDS | FIXED_ASSETS_COMPS,
    "property plant": CAPEX_IDS | FIXED_ASSETS_COMPS,
    "inventory": INVENTORY_IDS,
    "inventories": INVENTORY_IDS,
    "cash": CASH_IDS,
    "receivable": ACCOUNTS_RECEIVABLE_IDS,
    "accounts receivable": ACCOUNTS_RECEIVABLE_IDS,
    "debt": DEBT_IDS,
    "borrowing": DEBT_IDS,
    "long-term debt": LONG_TERM_DEBT_IDS,
    "short-term debt": SHORT_TERM_DEBT_IDS,
    "tax": TAX_EXP_IDS,
    "income tax": TAX_EXP_IDS,
    "sg&a": SG_AND_A_IDS,
    "selling": SG_AND_A_IDS,
    "general and admin": SG_AND_A_IDS,
    "r&d": R_AND_D_IDS,
    "research": R_AND_D_IDS,
    "development": R_AND_D_IDS,
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

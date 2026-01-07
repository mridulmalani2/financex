# Comps Model Structural Redesign
**Investment Bank Standard**
**Date:** 2026-01-07

---

# PART 3: COMPS OUTPUT CRITIQUE

## Current Structure (engine.py:1249-1301)

```python
def build_comps_ready_view(self) -> pd.DataFrame:
    data = {
        "Revenue": revenue,
        "EBITDA": ebitda,
        "EBIT": ebit,
        "Net Income": net_income,
        "EBITDA Margin %": (ebitda / revenue * 100)...,
        "Net Income Margin %": (net_income / revenue * 100)...,
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
```

## Critical Assessment

### **ISSUES PREVENTING INVESTMENT-GRADE USE**

#### 1. **Raw Metrics Mixed with Derived Multiples**

**Problem:** Current output shows:
- Revenue (raw)
- EBITDA Margin % (derived)
- EPS (derived)

But **missing**:
- Market Cap (needed for P/E ratio)
- Enterprise Value (needed for EV/EBITDA)
- Trading multiples (EV/Revenue, EV/EBIT, P/E, P/B)

**Why This Matters:**
- Comps analysis is about **relative valuation**
- Need multiples to compare across companies
- Cannot benchmark against peers without multiples

**Bank Standard:**
```
RAW METRICS:
  Revenue:              $1,000 M
  EBITDA:               $200 M
  Net Income:           $120 M
  Total Debt:           $300 M
  Cash:                 $50 M
  Shares Outstanding:   100 M

DERIVED METRICS:
  Net Debt:             $250 M (Debt - Cash)
  Market Cap:           $2,500 M (Shares × Price)
  Enterprise Value:     $2,750 M (Market Cap + Net Debt)

TRADING MULTIPLES:
  EV / Revenue:         2.8x
  EV / EBITDA:          13.8x
  EV / EBIT:            18.3x
  P / E:                20.8x
  P / B:                3.5x
```

#### 2. **No Market Data Integration**

**Problem:** Missing:
- Stock price
- Market capitalization
- 52-week high/low
- Trading volume
- Beta

**Why This Matters:**
- Cannot calculate P/E ratio without stock price
- Cannot calculate Enterprise Value without market cap
- Missing risk metrics (beta)

**Bank Standard:**
```
MARKET DATA (as of 1/7/2026):
  Stock Price:          $25.00
  52-Week Range:        $18.50 - $28.75
  Market Cap:           $2,500 M
  Avg Daily Volume:     2.5 M shares
  Beta:                 1.15
```

#### 3. **No Normalization Transparency**

**Problem:** Current code has this:
```python
ebitda = gross_profit - total_opex
```

But for comps, analysts normalize:
- Add back one-time items
- Adjust for non-recurring expenses
- Pro forma for acquisitions
- Normalize different accounting policies

**Why This Matters:**
- Direct comparison requires normalized metrics
- EBITDA as reported ≠ EBITDA (adjusted)
- Analysts need to see what adjustments were made

**Bank Standard:**
```
NORMALIZATION RECONCILIATION:
  EBITDA (Reported):              $180 M
  (+) Restructuring Charges:      $15 M
  (+) Stock-Based Compensation:   $25 M
  (+) Legal Settlement:           $10 M
  (=) EBITDA (Adjusted):          $230 M

  Notes:
    - Restructuring: One-time facility closure
    - SBC: Added back for cash-based comparison
    - Legal: Non-recurring litigation settlement
```

#### 4. **Partial Data Silently Dropped**

**Problem:**
```python
diluted_shares = diluted_shares.where(diluted_shares > 0, basic_shares)
```

This **silently substitutes** basic shares when diluted is missing.

**Why This Matters:**
- Analyst doesn't know substitution occurred
- May compare diluted EPS from one company vs. basic EPS from another
- Distorts peer analysis

**Bank Standard:**
```
Company A: EPS (Diluted): $2.50
Company B: EPS (Basic)*:  $2.75  *Diluted shares not available
Company C: EPS (Diluted): $2.60
```

Clear indication when data is substituted or estimated.

#### 5. **No Support for Incomplete Peer Sets**

**Problem:** What if:
- Company doesn't report segment data?
- Company uses different fiscal year?
- Company missing cash flow data?

Current structure: Silent error or zero value.

**Bank Standard:**
```
Metric              | CompanyA | CompanyB | CompanyC | Median | Mean
--------------------|----------|----------|----------|--------|------
EV / Revenue        | 2.5x     | 3.0x     | N/A      | 2.8x   | 2.8x
EV / EBITDA         | 12.0x    | 14.0x    | 15.0x    | 14.0x  | 13.7x
P / E               | 18.0x    | N/A      | 22.0x    | 20.0x  | 20.0x

Note: N/A indicates data not available
      Statistics calculated excluding N/A values
```

#### 6. **Missing Growth Metrics**

**Problem:** Comps analysis needs:
- Revenue growth (historical and projected)
- EBITDA growth
- EPS growth

**Bank Standard:**
```
GROWTH METRICS:
  Revenue Growth (LTM):           8.5%
  Revenue Growth (3Y CAGR):       12.0%
  EBITDA Growth (LTM):            15.0%
  EPS Growth (LTM):               18.0%
  Consensus Rev Growth (NTM):     10.0%  # From analyst estimates
```

#### 7. **No Peer Comparison**

**Problem:** A "comps" model with ONE company is not a comps model.

**Bank Standard:**
```
PEER GROUP COMPARISON:

Metric          | Target | Peer1 | Peer2 | Peer3 | Median | Target vs Median
----------------|--------|-------|-------|-------|--------|------------------
EV / Revenue    | 2.5x   | 3.0x  | 2.8x  | 3.2x  | 3.0x   | -17% (undervalued)
EV / EBITDA     | 12.0x  | 14.0x | 13.5x | 15.0x | 14.0x  | -14% (undervalued)
P / E           | 18.0x  | 22.0x | 20.0x | 24.0x | 22.0x  | -18% (undervalued)
Revenue Growth  | 8.5%   | 12.0% | 10.0% | 15.0% | 12.0%  | -29% (slower)
EBITDA Margin   | 18.0%  | 22.0% | 20.0% | 25.0% | 22.0%  | -18% (lower)

CONCLUSION: Target trading at discount to peers despite comparable growth
```

---

## Redesigned Comps Model Structure

### File Structure (4 Files + Peer Database)

#### File 1: `comps_raw_financials.csv`
```
Section,Metric,LTM,FY2023A,FY2022A,FY2021A,Source,Lineage_ID
INCOME_STATEMENT,Revenue,1020.0,1005.0,990.0,950.0,10-K,comp_raw_001
INCOME_STATEMENT,COGS,704.4,693.5,683.1,665.0,10-K,comp_raw_002
INCOME_STATEMENT,Gross Profit,315.6,311.5,306.9,285.0,Calculated,comp_raw_003
INCOME_STATEMENT,Gross Margin %,30.9%,31.0%,31.0%,30.0%,Calculated,comp_raw_004
INCOME_STATEMENT,Operating Expenses,204.0,201.0,198.0,190.0,10-K,comp_raw_005
INCOME_STATEMENT,EBITDA (Reported),111.6,110.5,108.9,95.0,Calculated,comp_raw_006
INCOME_STATEMENT,EBITDA Margin %,10.9%,11.0%,11.0%,10.0%,Calculated,comp_raw_007
INCOME_STATEMENT,D&A,35.7,35.2,34.7,33.3,10-K,comp_raw_008
INCOME_STATEMENT,EBIT,75.9,75.3,74.2,61.8,Calculated,comp_raw_009
INCOME_STATEMENT,Interest Expense,8.5,9.0,9.5,10.0,10-K,comp_raw_010
INCOME_STATEMENT,Tax Expense,16.9,16.6,16.2,13.0,10-K,comp_raw_011
INCOME_STATEMENT,Net Income (Reported),50.5,49.7,48.5,38.8,10-K,comp_raw_012
INCOME_STATEMENT,Net Margin %,5.0%,4.9%,4.9%,4.1%,Calculated,comp_raw_013
BALANCE_SHEET,Cash & Equivalents,65.0,60.0,55.0,50.0,10-K,comp_raw_014
BALANCE_SHEET,Total Debt,180.0,195.0,210.0,225.0,10-K,comp_raw_015
BALANCE_SHEET,Preferred Stock,0.0,0.0,0.0,0.0,10-K,comp_raw_016
BALANCE_SHEET,Minority Interest,10.0,10.0,10.0,10.0,10-K,comp_raw_017
BALANCE_SHEET,Total Assets,797.0,773.0,749.0,715.0,10-K,comp_raw_018
BALANCE_SHEET,Shareholders' Equity,534.0,497.0,460.0,415.0,10-K,comp_raw_019
BALANCE_SHEET,Book Value per Share,5.34,4.97,4.60,4.15,Calculated,comp_raw_020
SHARES,Basic Shares (M),100.0,100.0,100.0,100.0,10-K,comp_raw_021
SHARES,Diluted Shares (M),102.0,101.5,101.0,100.5,10-K,comp_raw_022
SHARES,Options & Warrants (M),2.0,1.5,1.0,0.5,10-K,comp_raw_023
GROWTH,Revenue Growth %,1.5%,1.5%,4.2%,--,Calculated,comp_raw_024
GROWTH,EBITDA Growth %,1.0%,1.5%,14.6%,--,Calculated,comp_raw_025
GROWTH,EPS Growth %,1.6%,2.5%,25.0%,--,Calculated,comp_raw_026
GROWTH,Revenue 3Y CAGR,2.4%,--,--,--,Calculated,comp_raw_027
```

**Lineage Integration:**
- Each raw financial metric is a node from historical financials
- Growth rates are calculated nodes with formula edges
- Links back to normalized financials from pipeline

#### File 2: `comps_normalization.csv`
```
Section,Adjustment,LTM,FY2023A,FY2022A,FY2021A,Type,Notes,Lineage_ID
EBITDA_RECONCILIATION,EBITDA (Reported),111.6,110.5,108.9,95.0,Base,From financials,comp_norm_001
EBITDA_RECONCILIATION,Restructuring Charges,5.0,3.0,0.0,0.0,Add-back,Facility closure,comp_norm_002
EBITDA_RECONCILIATION,Impairment Charges,0.0,0.0,2.0,0.0,Add-back,Goodwill write-down,comp_norm_003
EBITDA_RECONCILIATION,Stock-Based Comp,8.0,7.5,7.0,6.5,Add-back,Non-cash expense,comp_norm_004
EBITDA_RECONCILIATION,Legal Settlement,0.0,0.0,0.0,5.0,Add-back,One-time litigation,comp_norm_005
EBITDA_RECONCILIATION,EBITDA (Adjusted),124.6,121.0,117.9,106.5,Normalized,For comparability,comp_norm_006
EBITDA_RECONCILIATION,Adj. EBITDA Margin %,12.2%,12.0%,11.9%,11.2%,Calculated,,comp_norm_007
NI_RECONCILIATION,Net Income (Reported),50.5,49.7,48.5,38.8,Base,From financials,comp_norm_008
NI_RECONCILIATION,After-tax Adjustments,9.8,7.9,6.8,8.6,Add-back,Tax-effected @ 25%,comp_norm_009
NI_RECONCILIATION,Net Income (Adjusted),60.3,57.6,55.3,47.4,Normalized,,comp_norm_010
NI_RECONCILIATION,Adj. Net Margin %,5.9%,5.7%,5.6%,5.0%,Calculated,,comp_norm_011
EPS_RECONCILIATION,EPS Diluted (Reported),$0.50,$0.49,$0.48,$0.39,Base,From financials,comp_norm_012
EPS_RECONCILIATION,EPS Diluted (Adjusted),$0.59,$0.57,$0.55,$0.47,Normalized,Adjusted NI / Dil Shares,comp_norm_013
NORMALIZATION_POLICY,Stock-Based Comp,Add-back,--,--,--,Policy,Non-cash for comparability,comp_policy_001
NORMALIZATION_POLICY,Restructuring,Add-back,--,--,--,Policy,One-time items only,comp_policy_002
NORMALIZATION_POLICY,Acquisition Costs,Add-back,--,--,--,Policy,M&A transaction costs,comp_policy_003
NORMALIZATION_POLICY,FX Gains/Losses,No adjustment,--,--,--,Policy,Part of operations,comp_policy_004
```

**Lineage Integration:**
- Adjustment nodes link to raw financial nodes
- Normalization policy nodes provide rationale
- Edge carries: `method="add_back"`, `confidence=1.0`, `source=analyst_judgment`

#### File 3: `comps_market_data.csv`
```
Section,Metric,Value,As_of_Date,Source,Data_Quality,Lineage_ID
CURRENT_PRICE,Stock Symbol,ACME,--,Exchange,--,comp_mkt_001
CURRENT_PRICE,Exchange,NYSE,--,Exchange,--,comp_mkt_002
CURRENT_PRICE,Current Price,$25.00,2026-01-07,Market Data,Live,comp_mkt_003
CURRENT_PRICE,Currency,USD,--,--,--,comp_mkt_004
TRADING_DATA,52-Week High,$28.75,2025-11-15,Market Data,Historical,comp_mkt_005
TRADING_DATA,52-Week Low,$18.50,2025-03-22,Market Data,Historical,comp_mkt_006
TRADING_DATA,% from 52W High,-13.0%,--,Calculated,--,comp_mkt_007
TRADING_DATA,Avg Daily Volume (3M),2.5M,--,Market Data,Live,comp_mkt_008
TRADING_DATA,Market Cap,$2,550.0M,--,Calculated,Price × Dil Shares,comp_mkt_009
RISK_METRICS,Beta (5Y),1.15,--,Bloomberg,Estimated,comp_mkt_010
RISK_METRICS,Volatility (90D),28.5%,--,Market Data,Historical,comp_mkt_011
ANALYST_DATA,Consensus Target Price,$28.00,--,FactSet,Median of 15,comp_mkt_012
ANALYST_DATA,Upside to Target,12.0%,--,Calculated,--,comp_mkt_013
ANALYST_DATA,Rating,Buy,--,Consensus,12 Buy / 3 Hold,comp_mkt_014
ESTIMATES,Revenue (NTM Est),$1,100.0M,--,Consensus,Mean of 15,comp_mkt_015
ESTIMATES,EBITDA (NTM Est),$140.0M,--,Consensus,Mean of 15,comp_mkt_016
ESTIMATES,EPS (NTM Est),$0.65,--,Consensus,Mean of 15,comp_mkt_017
ESTIMATES,Revenue Growth (NTM),7.8%,--,Calculated,--,comp_mkt_018
```

**Lineage Integration:**
- Market price is external data node (source: market_data_feed)
- Market cap is calculated: `Price × Diluted_Shares`
- Estimates are external nodes with confidence scores (analyst consensus)

#### File 4: `comps_valuation_multiples.csv`
```
Section,Multiple,LTM,NTM_Est,Calculation,Lineage_ID
ENTERPRISE_VALUE,Market Capitalization,2550.0,--,Price × Diluted Shares,comp_val_001
ENTERPRISE_VALUE,(+) Total Debt,180.0,--,From balance sheet,comp_val_002
ENTERPRISE_VALUE,(-) Cash,-65.0,--,From balance sheet,comp_val_003
ENTERPRISE_VALUE,(+) Preferred Stock,0.0,--,From balance sheet,comp_val_004
ENTERPRISE_VALUE,(+) Minority Interest,10.0,--,From balance sheet,comp_val_005
ENTERPRISE_VALUE,(=) Enterprise Value,2675.0,--,Market Cap + Net Debt + Pref + MI,comp_val_006
EV_MULTIPLES,EV / Revenue (Reported),2.6x,2.4x,EV / Revenue,comp_val_007
EV_MULTIPLES,EV / Revenue (Adjusted),2.6x,2.4x,EV / Adj Revenue (if normalized),comp_val_008
EV_MULTIPLES,EV / EBITDA (Reported),24.0x,19.1x,EV / EBITDA Reported,comp_val_009
EV_MULTIPLES,EV / EBITDA (Adjusted),21.5x,17.7x,EV / EBITDA Adjusted,comp_val_010
EV_MULTIPLES,EV / EBIT,35.2x,--,EV / EBIT,comp_val_011
EQUITY_MULTIPLES,P / E (Reported),51.0x,38.5x,Price / EPS Reported,comp_val_012
EQUITY_MULTIPLES,P / E (Adjusted),43.2x,35.2x,Price / EPS Adjusted,comp_val_013
EQUITY_MULTIPLES,P / B,4.8x,--,Price / Book Value per Share,comp_val_014
EQUITY_MULTIPLES,P / S,2.5x,2.3x,Market Cap / Revenue,comp_val_015
GROWTH_ADJUSTED,PEG Ratio (LTM),3.2,--,P/E / EPS Growth %,comp_val_016
GROWTH_ADJUSTED,EV/EBITDA / Growth,1.8,--,(EV/EBITDA) / EBITDA Growth %,comp_val_017
YIELD_METRICS,Dividend Yield,0.0%,--,Annual Div / Price,comp_val_018
YIELD_METRICS,FCF Yield,2.2%,--,FCF / Market Cap,comp_val_019
YIELD_METRICS,Earnings Yield,2.0%,--,EPS / Price (inverse P/E),comp_val_020
```

**Lineage Integration:**
- Each multiple is calculated node
- Links to: Market cap node + Financial metric node
- Formula explicit: `EV/EBITDA = comp_val_006 / comp_norm_006`

#### File 5: `comps_peer_comparison.csv`
```
Company,Ticker,Market_Cap,EV,EV_Rev_LTM,EV_EBITDA_LTM,PE_LTM,Rev_Growth,EBITDA_Margin,Data_Quality,Lineage_ID
Target Co,ACME,2550,2675,2.6x,21.5x,43.2x,1.5%,12.2%,Complete,comp_peer_target
Peer 1,PEER1,3200,3500,3.0x,18.0x,28.0x,8.0%,16.7%,Complete,comp_peer_001
Peer 2,PEER2,2800,3100,2.8x,19.5x,32.0x,5.5%,14.5%,Partial*,comp_peer_002
Peer 3,PEER3,4100,4500,3.2x,22.0x,35.0x,12.0%,14.5%,Complete,comp_peer_003
Peer 4,PEER4,1900,2000,2.4x,16.0x,N/A,3.0%,15.0%,Incomplete**,comp_peer_004
--,--,--,--,--,--,--,--,--,--,--
Median,--,2800,3100,2.8x,19.5x,32.0x,5.5%,14.5%,--,comp_peer_median
Mean,--,2875,3150,2.9x,19.1x,31.7x,7.1%,15.2%,--,comp_peer_mean
Min,--,1900,2000,2.4x,16.0x,28.0x,3.0%,14.5%,--,comp_peer_min
Max,--,4100,4500,3.2x,22.0x,35.0x,12.0%,16.7%,--,comp_peer_max
--,--,--,--,--,--,--,--,--,--,--
Target_vs_Median,--,--,--,-7%,10%,36%,-73%,-16%,--,comp_peer_vs_median
Target_Premium_Discount,--,--,--,Discount,Premium,Premium,Below,Below,--,comp_peer_analysis

Notes:
*Peer 2: Estimated EBITDA margin (no detailed P&L disclosure)
**Peer 4: No P/E available (loss-making in LTM period)
Statistics calculated excluding N/A values
```

**Lineage Integration:**
- Each peer is a separate subgraph
- Median/Mean/Min/Max are calculated nodes with edges to all peer nodes
- Partial data flagged with edge attribute: `data_quality="estimated"`, `confidence=0.6`

---

## Structural Specification

### Data Model

```python
@dataclass
class CompanyFinancials:
    """Raw financial metrics."""
    company_name: str
    ticker: str
    fiscal_year_end: str
    currency: str

    # Income statement
    revenue: TimeSeries
    cogs: TimeSeries
    operating_expenses: TimeSeries
    ebitda_reported: TimeSeries
    ebit: TimeSeries
    net_income_reported: TimeSeries

    # Balance sheet
    cash: TimeSeries
    total_debt: TimeSeries
    shareholders_equity: TimeSeries

    # Shares
    basic_shares: TimeSeries
    diluted_shares: TimeSeries

@dataclass
class Normalization:
    """Adjustments for comparability."""
    adjustments: List[NormalizationAdjustment]
    policy: NormalizationPolicy

@dataclass
class NormalizationAdjustment:
    """Single adjustment."""
    item: str  # "Restructuring Charges"
    period: str  # "LTM"
    amount: float
    adjustment_type: str  # "add_back" | "deduct"
    rationale: str  # "One-time facility closure"
    is_recurring: bool = False

@dataclass
class MarketData:
    """Market-based inputs."""
    stock_price: float
    price_date: date
    market_cap: float  # Calculated
    beta: float
    avg_volume: float
    analyst_estimates: AnalystEstimates

@dataclass
class ValuationMultiples:
    """Calculated multiples."""
    enterprise_value: float
    ev_revenue: float
    ev_ebitda: float
    ev_ebit: float
    pe_ratio: float
    pb_ratio: float
    peg_ratio: float

@dataclass
class PeerComparison:
    """Peer group analysis."""
    target: CompanyMetrics
    peers: List[CompanyMetrics]
    statistics: PeerStatistics  # median, mean, min, max
    relative_valuation: RelativeValuation  # premium/discount analysis

@dataclass
class CompanyMetrics:
    """Complete metrics for one company."""
    company_name: str
    financials: CompanyFinancials
    normalizations: Normalization
    market_data: MarketData
    multiples: ValuationMultiples
    data_quality: DataQuality

@dataclass
class DataQuality:
    """Data availability and quality flags."""
    completeness: float  # 0.0 to 1.0
    missing_metrics: List[str]
    estimated_metrics: List[str]
    data_issues: List[str]
```

### File Format Specification

```yaml
comps_raw_financials.csv:
  purpose: Unadjusted financial data
  columns:
    - Section: str (INCOME_STATEMENT | BALANCE_SHEET | SHARES | GROWTH)
    - Metric: str
    - LTM: float (last twelve months)
    - FY2023A: float (fiscal year actual)
    - FY2022A: float
    - FY2021A: float
    - Source: str (10-K | 10-Q | Press Release)
    - Lineage_ID: str
  validation:
    - No derived multiples (only raw data)
    - Growth rates in separate section
    - All actuals suffixed with "A"
    - Missing data marked as "--" not 0

comps_normalization.csv:
  purpose: Adjustments for comparability
  sections:
    - EBITDA_RECONCILIATION: EBITDA adjustments
    - NI_RECONCILIATION: Net income adjustments
    - EPS_RECONCILIATION: EPS adjustments
    - NORMALIZATION_POLICY: Rules for adjustments
  validation:
    - Every adjustment has rationale
    - Adjusted metrics clearly labeled
    - Tax effect applied to NI adjustments
    - Policy section documents approach

comps_market_data.csv:
  purpose: Market-based inputs
  sections:
    - CURRENT_PRICE: Stock price and symbol
    - TRADING_DATA: Volume, range, market cap
    - RISK_METRICS: Beta, volatility
    - ANALYST_DATA: Consensus estimates
  validation:
    - All market data has "As_of_Date"
    - Data_Quality flag (Live | Historical | Estimated)
    - Source documented (Bloomberg | FactSet | etc)
    - Market cap = Price × Shares (calculated)

comps_valuation_multiples.csv:
  purpose: Calculated multiples
  sections:
    - ENTERPRISE_VALUE: EV bridge
    - EV_MULTIPLES: EV-based ratios
    - EQUITY_MULTIPLES: Price-based ratios
    - GROWTH_ADJUSTED: PEG, etc.
    - YIELD_METRICS: Dividend, FCF yield
  validation:
    - Calculation column shows formula
    - Both reported and adjusted multiples
    - LTM and NTM (next twelve months)
    - Missing multiples marked "N/A" not 0.0

comps_peer_comparison.csv:
  purpose: Peer group analysis
  rows: Target + Peers + Statistics
  validation:
    - Data_Quality column for each peer
    - Notes explain data gaps
    - Statistics exclude N/A values
    - Target vs Median row shows premium/discount
```

### Lineage Graph Integration

```python
# Example: EV/EBITDA multiple calculation

# Inputs
ev_node = FinancialNode(
    node_id="comp_val_006",
    value=2675.0,
    concept="enterprise_value",
    label="Enterprise Value"
)

ebitda_adj_node = FinancialNode(
    node_id="comp_norm_006",
    value=124.6,
    concept="ebitda_adjusted",
    label="EBITDA (Adjusted)"
)

# Calculation
ev_ebitda_edge = FinancialEdge(
    edge_id="comp_val_010_calc",
    edge_type=EdgeType.CALCULATION,
    source_node_ids=["comp_val_006", "comp_norm_006"],
    target_node_id="comp_val_010",
    formula="=Enterprise_Value / EBITDA_Adjusted",
    formula_inputs={
        "Enterprise_Value": 2675.0,
        "EBITDA_Adjusted": 124.6
    },
    method="division",
    confidence=1.0
)

# Query: "How was EV/EBITDA calculated?"
graph.trace_backward("comp_val_010")
# Returns:
#   - Enterprise Value node (how EV was built)
#   - EBITDA Adjusted node (what adjustments were made)
#   - Market Cap node (stock price × shares)
#   - Normalization adjustment nodes (restructuring, SBC, etc.)
#   - Raw EBITDA node (from financials)
```

#### Partial Data Handling in Graph

```python
# Peer with missing P/E ratio

peer4_pe_node = FinancialNode(
    node_id="comp_peer_004_pe",
    value=None,
    concept="pe_ratio",
    label="P/E Ratio",
    is_active=False  # Missing data
)

missing_data_edge = FinancialEdge(
    edge_id="comp_peer_004_pe_missing",
    edge_type=EdgeType.CALCULATION,
    source_node_ids=["comp_peer_004_price", "comp_peer_004_eps"],
    target_node_id="comp_peer_004_pe",
    is_active=False,
    condition="Cannot calculate P/E - company reported loss (negative EPS)",
    method="division_by_negative",
    confidence=0.0
)

# When calculating peer group statistics
median_pe_edge = FinancialEdge(
    edge_id="comp_peer_median_pe",
    source_node_ids=["comp_peer_001_pe", "comp_peer_002_pe", "comp_peer_003_pe"],
    # Note: peer_004 excluded (inactive node)
    target_node_id="comp_peer_median_pe",
    formula="=MEDIAN(active_peer_pes)",
    excluded_source_ids=["comp_peer_004_pe"],
    condition="Peer 4 excluded - loss-making"
)

# Query: "Why is Peer 4 P/E missing?"
graph.trace_backward("comp_peer_004_pe")
# Returns: EPS node (negative value) + explanation edge
```

---

## Degradation Strategy

### Missing Data Handling

```python
class CompsBuilder:
    def build_with_partial_data(self, company_financials, market_data):
        """Build comps model with graceful degradation."""

        degradation_log = []

        # Check critical inputs
        if not market_data.stock_price:
            # Cannot calculate any equity multiples
            degradation_log.append({
                "section": "VALUATION_MULTIPLES",
                "metrics_unavailable": ["P/E", "P/B", "P/S", "Market Cap"],
                "impact": "CRITICAL",
                "fallback": "EV multiples only (using book value of equity)"
            })
            # Estimate market cap from book value
            estimated_market_cap = company_financials.shareholders_equity * 1.5  # Assume 1.5x P/B
            market_data.market_cap = estimated_market_cap
            market_data.price = estimated_market_cap / company_financials.diluted_shares
            degradation_log.append({
                "metric": "Market Cap",
                "method": "estimated",
                "assumption": "1.5x P/B ratio",
                "confidence": 0.3
            })

        if not company_financials.diluted_shares:
            # Use basic shares
            company_financials.diluted_shares = company_financials.basic_shares
            degradation_log.append({
                "metric": "Diluted Shares",
                "method": "substituted",
                "value": "Basic shares used",
                "confidence": 0.8
            })

        if company_financials.net_income_reported < 0:
            # Cannot calculate P/E
            degradation_log.append({
                "metric": "P/E Ratio",
                "method": "unavailable",
                "reason": "Loss-making (negative EPS)",
                "display": "N/M"  # Not Meaningful
            })

        return degradation_log
```

### Output Indicators

```
File: comps_valuation_multiples.csv

Section,Multiple,LTM,NTM_Est,Calculation,Notes
EQUITY_MULTIPLES,P / E (Reported),N/M,--,Price / EPS Reported,*Loss-making period
EQUITY_MULTIPLES,Market Cap,2550.0**,--,Estimated,**Using 1.5x P/B (no stock price available)

File: comps_peer_comparison.csv

Company,Ticker,Market_Cap,EV,EV_Rev_LTM,EV_EBITDA_LTM,PE_LTM,Data_Quality
Peer 4,PEER4,1900,2000,2.4x,16.0x,N/M*,Incomplete

Notes:
*N/M = Not Meaningful (loss-making)
**Estimated using industry P/B ratio
```

---

## Integration with Lineage Graph

### Complete Flow Example

```
USER QUERY: "Show me how Target's EV/EBITDA of 21.5x was calculated"

GRAPH TRAVERSAL:
1. Start at: comp_val_010 (EV/EBITDA Adjusted = 21.5x)

2. Trace backward:
   comp_val_010 ← comp_val_006 (EV = 2675.0)
   comp_val_010 ← comp_norm_006 (EBITDA Adj = 124.6)

3. Expand EV calculation:
   comp_val_006 ← comp_mkt_009 (Market Cap = 2550.0)
                ← comp_raw_015 (Total Debt = 180.0)
                ← comp_raw_014 (Cash = 65.0)
                ← comp_raw_017 (Minority Int = 10.0)

4. Expand Market Cap:
   comp_mkt_009 ← comp_mkt_003 (Stock Price = $25.00)
                ← comp_raw_022 (Diluted Shares = 102.0M)

5. Expand EBITDA Adjusted:
   comp_norm_006 ← comp_raw_006 (EBITDA Reported = 111.6)
                 ← comp_norm_002 (Restructuring = 5.0)
                 ← comp_norm_003 (Impairment = 0.0)
                 ← comp_norm_004 (Stock Comp = 8.0)

6. Expand EBITDA Reported:
   comp_raw_006 ← comp_raw_001 (Revenue = 1020.0)
                ← comp_raw_002 (COGS = 704.4)
                ← comp_raw_005 (OpEx = 204.0)

7. Link to original source:
   comp_raw_001 ← [LINEAGE GRAPH] ← node_12345 (Extracted Revenue)
                                  ← Excel Cell: "Income Statement"!C6 = 1020.0

OUTPUT:
EV/EBITDA = 21.5x calculated as:
  Enterprise Value: $2,675.0 M
    = Market Cap ($2,550.0) + Debt ($180.0) - Cash ($65.0) + MI ($10.0)
    = (Stock Price $25.00 × Diluted Shares 102.0M) + $180.0 - $65.0 + $10.0

  EBITDA (Adjusted): $124.6 M
    = EBITDA Reported ($111.6) + Adjustments ($13.0)
    = (Revenue $1,020.0 - COGS $704.4 - OpEx $204.0) + (Restructuring $5.0 + SBC $8.0)

  Multiple: $2,675.0 / $124.6 = 21.5x

LINEAGE CHAIN:
  Excel Cell → Extracted → Normalized → Raw Financial → Adjusted Financial → Multiple

  Nodes touched: 15
  Edges traversed: 14
  Confidence: 1.0 (all inputs verified)
  Data quality: Complete
```

---

## Summary: Comps Redesign

### What Changed
| Aspect | Old | New |
|--------|-----|-----|
| **Files** | 1 output | 5 files (raw, normalization, market, multiples, peers) |
| **Structure** | Mixed raw + derived | Clearly separated |
| **Multiples** | Missing | Complete set (EV + Equity) |
| **Market Data** | Not included | Full integration |
| **Normalization** | Hidden | Explicit reconciliation |
| **Partial Data** | Silent substitution | Flagged with notes |
| **Peer Comparison** | Single company | Full peer group + statistics |
| **Lineage** | None | Every cell linked to graph |
| **Data Quality** | Unknown | Explicit flags |

### Bank Compliance
✅ Separates raw metrics from derived multiples
✅ Normalization choices explicit and documented
✅ Supports partial data with clear indicators
✅ Does not silently drop companies or metrics
✅ Provides complete audit trail (lineage graph)
✅ Peer comparison with statistics (median, mean)
✅ Market data integration
✅ Growth metrics included
✅ Both reported and adjusted figures
✅ Presentation-ready format

---

## Final Integration Summary

### How All Three Models Connect via Lineage Graph

```
HISTORICAL FINANCIALS
        ↓
    [Lineage Graph]
        ↓
    ┌───┴────┐
    │        │
   DCF     Comps
    │        │
    └───┬────┘
        │
       LBO
```

**Data Flow:**
1. Historical financials → Raw metrics nodes in graph
2. DCF uses graph nodes for projections (revenue growth from historical)
3. Comps uses graph nodes for multiples (EBITDA from normalized financials)
4. LBO uses graph nodes for entry valuation (EV from comps) + operating assumptions (from DCF projections)

**Cross-Model Validation:**
```python
# Example: LBO entry valuation should match Comps EV
lbo_entry_ev = graph.get_node("lbo_trans_ev")
comps_ev = graph.get_node("comp_val_006")

validation_edge = FinancialEdge(
    edge_type=EdgeType.VALIDATION,
    source_node_ids=["lbo_trans_ev", "comp_val_006"],
    target_node_id="cross_model_validation_001",
    is_active=(abs(lbo_entry_ev.value - comps_ev.value) < 0.01),
    condition=f"LBO entry EV ({lbo_entry_ev.value}) should match Comps EV ({comps_ev.value})"
)

if not validation_edge.is_active:
    raise ValidationError("LBO entry valuation inconsistent with Comps analysis")
```

**Complete Audit Trail:**
Any final output number can be traced backward through:
- Calculation steps (formulas)
- Assumptions (analyst inputs)
- Normalizations (adjustments)
- Raw financials (extracted data)
- Source Excel cells (original data)

This provides **bank-grade audit capability** for regulatory compliance and model review.

---

**END OF STRUCTURAL REDESIGN**

# LBO Model Structural Redesign
**Investment Bank Standard**
**Date:** 2026-01-07

---

# PART 2: LBO OUTPUT CRITIQUE

## Current Structure (engine.py:1192-1243)

```python
def build_lbo_ready_view(self) -> pd.DataFrame:
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
```

## Critical Assessment

### **THIS IS NOT AN LBO MODEL**

This is a **credit metrics summary**. A true LBO model requires:

1. **Transaction Assumptions**
   - Purchase price
   - Purchase price multiple (Entry EV/EBITDA)
   - Transaction date
   - Sources & Uses table

2. **Capital Structure**
   - Senior debt (amount, rate, amortization schedule)
   - Subordinated debt / Mezzanine (amount, rate, PIK %)
   - Equity contribution
   - Debt tranches with different terms

3. **Operating Model**
   - Revenue projections
   - EBITDA margin assumptions
   - Working capital management
   - CapEx plan

4. **Debt Dynamics**
   - Mandatory amortization
   - Cash sweep (excess cash → debt paydown)
   - Interest calculation (beginning vs. average balance)
   - Refinancing assumptions

5. **Exit Analysis**
   - Exit year (typically Year 5)
   - Exit multiple (Exit EV/EBITDA)
   - Exit enterprise value
   - Remaining debt at exit
   - Equity proceeds

6. **Returns Calculation**
   - IRR (Internal Rate of Return)
   - MoM (Money-on-Money multiple)
   - Breakeven analysis

### What's Missing

#### 1. **No Transaction Setup**

**Problem:** Current model shows historical debt, not a pro forma transaction.

**Bank Standard:**
```
TRANSACTION ASSUMPTIONS:
  Purchase Price:               $1,000.0 M
  Entry Multiple (EV/EBITDA):   10.0x
  Transaction Date:             12/31/2024
  Exit Date:                    12/31/2029
  Holding Period:               5 years
```

#### 2. **Hardcoded Leverage Assumptions**

**Problem:** Template has this:
```
"Senior Debt (3.0x Lev)"
"Mezzanine Debt (1.0x Lev)"
```

This is **NOT how LBOs work**:
- Leverage multiples are **outputs** of credit analysis, not inputs
- Different lenders have different terms
- Debt capacity depends on cash flow coverage, not arbitrary multiples

**Bank Standard:**
```
SOURCES (Inputs):
  Senior Debt:
    - Amount: $600.0 M (60% LTV)
    - Rate: L + 450 bps
    - Term: 7 years
    - Amortization: 5% annually
    - Covenants: Max 5.0x Total Debt/EBITDA

  Mezzanine:
    - Amount: $150.0 M (15% LTV)
    - Rate: 12% cash + 3% PIK
    - Term: 8 years
    - Amortization: Bullet

  Sponsor Equity:
    - Amount: $250.0 M (plug)
    - % of Capital Structure: 25%

USES:
  Purchase Equity Value:        $920.0 M
  Refinance Net Debt:           $50.0 M
  Transaction Fees:             $30.0 M
  Total Uses:                   $1,000.0 M

CHECK: Sources = Uses ✓
```

#### 3. **No Cash Sweep Logic**

**Problem:** LBO models need to track:
- Available cash after operations
- Minimum cash balance requirement
- Excess cash applied to debt paydown
- Which debt tranche gets paid first (waterfall)

**Bank Standard:**
```
YEAR 1 CASH SWEEP:
  Beginning Cash:               $20.0 M
  (+) EBITDA:                   $120.0 M
  (-) Interest:                 $45.0 M
  (-) Taxes:                    $15.0 M
  (-) CapEx:                    $15.0 M
  (-) Mandatory Amortization:   $30.0 M
  (=) Cash Available:           $35.0 M
  (-) Minimum Cash:             $10.0 M
  (=) Excess Cash:              $25.0 M

  SWEEP APPLICATION:
    → Senior Debt Paydown:      $25.0 M

  Ending Cash:                  $10.0 M
  Ending Senior Debt:           $545.0 M (was $570M)
```

#### 4. **No Exit Analysis**

**Problem:** Current output stops at credit metrics. LBOs need exit modeling.

**Bank Standard:**
```
EXIT ANALYSIS (Year 5):
  LTM EBITDA (at exit):         $150.0 M
  Exit Multiple:                12.0x
  Enterprise Value:             $1,800.0 M
  Less: Net Debt at Exit:       ($350.0 M)
  Gross Proceeds to Equity:     $1,450.0 M

  Initial Equity Investment:    $250.0 M
  Gross MoM:                    5.8x
  IRR:                          42.0%
```

#### 5. **No Returns Calculation**

**Problem:** The **entire point** of an LBO model is to calculate returns.

**Bank Standard:**
```
SPONSOR RETURNS:
  Initial Investment:           $250.0 M (12/31/2024)
  Exit Proceeds:                $1,450.0 M (12/31/2029)

  IRR Calculation:
    Year 0: -$250.0 M
    Year 1: $0
    Year 2: $0
    Year 3: $0
    Year 4: $0
    Year 5: +$1,450.0 M
    IRR: 42.0%

  MoM Multiple: 5.8x

  DOWNSIDE SCENARIO:
    Exit Multiple: 8.0x
    IRR: 18.5%
    MoM: 2.4x
```

---

## Redesigned LBO Model Structure

### File Structure (6 Files)

#### File 1: `lbo_transaction.csv`
```
Section,Item,Value,Unit,Source,Notes
PURCHASE_PRICE,Target Company,Acme Corp,--,Transaction,
PURCHASE_PRICE,Transaction Date,12/31/2024,--,Assumed,
PURCHASE_PRICE,LTM EBITDA,100.0,M,Historical,Last 12 months
PURCHASE_PRICE,Entry Multiple (EV/EBITDA),10.0,x,Market Comps,Median peer trading multiple
PURCHASE_PRICE,Enterprise Value,1000.0,M,Calculated,=LTM EBITDA × Multiple
PURCHASE_PRICE,Less: Cash Acquired,-20.0,M,Balance Sheet,
PURCHASE_PRICE,Add: Debt Assumed,50.0,M,Balance Sheet,
PURCHASE_PRICE,Equity Purchase Price,1030.0,M,Calculated,=EV - Cash + Debt
TIMING,Holding Period,5,Years,Standard,Typical sponsor hold
TIMING,Exit Date,12/31/2029,--,Calculated,
EXIT_ASSUMPTIONS,Exit Multiple (EV/EBITDA),12.0,x,Upside Case,15% premium to entry
EXIT_ASSUMPTIONS,Exit Multiple (Downside),8.0,x,Downside Case,20% discount to entry
EXIT_ASSUMPTIONS,Exit Multiple (Base),10.0,x,Base Case,Same as entry
```

**Lineage Integration:**
```python
# Purchase price calculation
ev_node = FinancialNode(
    node_id="lbo_trans_001",
    node_type=NodeType.CALCULATED,
    concept="enterprise_value",
    value=1000.0,
    label="Enterprise Value"
)

ev_edge = FinancialEdge(
    edge_id="lbo_edge_001",
    edge_type=EdgeType.CALCULATION,
    source_node_ids=["lbo_ebitda_node", "lbo_multiple_node"],
    target_node_id="lbo_trans_001",
    formula="=LTM_EBITDA × Entry_Multiple",
    formula_inputs={"LTM_EBITDA": 100.0, "Entry_Multiple": 10.0}
)
```

#### File 2: `lbo_sources_uses.csv`
```
Section,Item,Amount,% of Total,Terms,Lineage_ID
SOURCES,Senior Term Loan,600.0,60.0%,L+450bps | 7yr | 5% annual amort,lbo_src_001
SOURCES,Senior Notes,0.0,0.0%,--,lbo_src_002
SOURCES,Subordinated Debt,150.0,15.0%,12% cash + 3% PIK | 8yr | Bullet,lbo_src_003
SOURCES,Mezzanine,0.0,0.0%,--,lbo_src_004
SOURCES,Common Equity,250.0,25.0%,Sponsor contribution,lbo_src_005
SOURCES,Preferred Equity,0.0,0.0%,--,lbo_src_006
SOURCES,Rollover Equity,0.0,0.0%,Management rollover,lbo_src_007
SOURCES,Total Sources,1000.0,100.0%,,lbo_src_total
USES,Purchase Equity,920.0,92.0%,To selling shareholders,lbo_use_001
USES,Refinance Existing Debt,50.0,5.0%,Pay off target debt,lbo_use_002
USES,Transaction Fees,30.0,3.0%,Legal + Banking + DD,lbo_use_003
USES,Financing Fees,0.0,0.0%,Debt arrangement fees,lbo_use_004
USES,Total Uses,1000.0,100.0%,,lbo_use_total
VALIDATION,Sources - Uses,0.0,--,Must equal zero,lbo_validation
CAPITAL_STRUCTURE,Total Debt,750.0,--,Senior + Sub,lbo_cap_001
CAPITAL_STRUCTURE,Total Equity,250.0,--,Common + Preferred + Rollover,lbo_cap_002
CAPITAL_STRUCTURE,Debt / Equity,3.0,x,,lbo_cap_003
CAPITAL_STRUCTURE,Debt / LTM EBITDA,7.5,x,Initial leverage,lbo_cap_004
```

**Lineage Integration:**
- Sources & Uses balance is a validation edge: `if sources != uses: raise BalanceError`
- Each debt tranche is a separate node with attributes (rate, term, amortization)

#### File 3: `lbo_debt_schedule.csv`
```
Section,Item,Year_0,Year_1,Year_2,Year_3,Year_4,Year_5,Lineage_ID
SENIOR_DEBT,Beginning Balance,600.0,570.0,538.5,505.4,470.5,433.7,lbo_debt_sr_beg
SENIOR_DEBT,Mandatory Amortization,0.0,-30.0,-30.0,-30.0,-30.0,-30.0,lbo_debt_sr_mand
SENIOR_DEBT,Cash Sweep Paydown,0.0,0.0,-1.5,-3.1,-5.1,-7.3,lbo_debt_sr_sweep
SENIOR_DEBT,Ending Balance,600.0,570.0,538.5,505.4,470.5,433.7,lbo_debt_sr_end
SENIOR_DEBT,Interest Rate,7.50%,7.50%,7.50%,7.50%,7.50%,7.50%,lbo_debt_sr_rate
SENIOR_DEBT,Interest Expense,0.0,45.0,42.8,40.4,37.8,35.0,lbo_debt_sr_int
SUB_DEBT,Beginning Balance,150.0,150.0,150.0,150.0,150.0,150.0,lbo_debt_sub_beg
SUB_DEBT,Cash Interest (12%),0.0,18.0,18.0,18.0,18.0,18.0,lbo_debt_sub_cash
SUB_DEBT,PIK Interest (3%),0.0,4.5,4.6,4.8,4.9,5.1,lbo_debt_sub_pik
SUB_DEBT,PIK Accrued to Principal,0.0,4.5,4.6,4.8,4.9,5.1,lbo_debt_sub_accrue
SUB_DEBT,Ending Balance,150.0,154.5,159.2,164.0,168.9,174.0,lbo_debt_sub_end
SUB_DEBT,Total Interest,0.0,22.5,22.6,22.8,22.9,23.1,lbo_debt_sub_tot_int
TOTAL,Total Debt,750.0,724.5,697.7,669.4,639.4,607.7,lbo_debt_total
TOTAL,Total Interest Expense,0.0,67.5,65.4,63.2,60.7,58.1,lbo_debt_total_int
```

**Lineage Integration:**
- Each year's debt balance is a calculated node
- Edges show: `Beginning + PIK - Paydown = Ending`
- Cash sweep nodes link to operating cash flow calculations

#### File 4: `lbo_operating_model.csv`
```
Section,Metric,Year_0,Year_1,Year_2,Year_3,Year_4,Year_5,Assumptions,Lineage_ID
REVENUE,Revenue,1000.0,1050.0,1102.5,1157.6,1215.5,1276.3,5% growth,lbo_op_rev
REVENUE,Revenue Growth %,--,5.0%,5.0%,5.0%,5.0%,5.0%,Assumption,lbo_op_rev_gr
PROFITABILITY,EBITDA,100.0,115.5,133.3,153.4,176.1,201.0,Margin expansion,lbo_op_ebitda
PROFITABILITY,EBITDA Margin %,10.0%,11.0%,12.1%,13.3%,14.5%,15.7%,100bps/year,lbo_op_ebitda_mg
PROFITABILITY,Less: D&A,-35.0,-36.8,-38.6,-40.5,-42.5,-44.6,3.5% of revenue,lbo_op_da
PROFITABILITY,EBIT,65.0,78.7,94.7,112.9,133.6,156.4,Calculated,lbo_op_ebit
PROFITABILITY,Less: Interest Expense,0.0,-67.5,-65.4,-63.2,-60.7,-58.1,From debt schedule,lbo_op_int
PROFITABILITY,EBT,65.0,11.2,29.3,49.7,72.9,98.3,Calculated,lbo_op_ebt
PROFITABILITY,Less: Taxes @ 25%,-16.3,-2.8,-7.3,-12.4,-18.2,-24.6,Statutory rate,lbo_op_tax
PROFITABILITY,Net Income,48.7,8.4,22.0,37.3,54.7,73.7,Calculated,lbo_op_ni
CASH_FLOW,Net Income,48.7,8.4,22.0,37.3,54.7,73.7,From above,lbo_cf_ni
CASH_FLOW,Add: D&A,35.0,36.8,38.6,40.5,42.5,44.6,Non-cash,lbo_cf_da
CASH_FLOW,Less: CapEx,-40.0,-42.0,-44.1,-46.3,-48.6,-51.0,4% of revenue,lbo_cf_capex
CASH_FLOW,Less: Change in NWC,-10.0,-5.3,-5.5,-5.8,-6.1,-6.4,1% of ∆Revenue,lbo_cf_nwc
CASH_FLOW,Operating Cash Flow,33.7,-1.1,11.0,25.7,42.5,60.9,Available for debt,lbo_cf_ocf
```

**Lineage Integration:**
- EBITDA margin assumption → EBITDA calculation
- Interest expense links to debt schedule (separate file)
- Operating cash flow feeds into cash sweep calculation

#### File 5: `lbo_cash_sweep.csv`
```
Section,Item,Year_1,Year_2,Year_3,Year_4,Year_5,Formula,Lineage_ID
CASH_AVAILABLE,Beginning Cash Balance,20.0,10.0,10.0,10.0,10.0,Minimum cash,lbo_sweep_beg
CASH_AVAILABLE,Operating Cash Flow,-1.1,11.0,25.7,42.5,60.9,From operating model,lbo_sweep_ocf
CASH_AVAILABLE,Mandatory Debt Amortization,-30.0,-30.0,-30.0,-30.0,-30.0,5% of senior,lbo_sweep_mand
CASH_AVAILABLE,Cash Available (before sweep),-11.1,-9.0,5.7,22.5,40.9,Sum above,lbo_sweep_avail
CASH_AVAILABLE,Cash Deficit / (Surplus),11.1,0.0,-1.5,-3.1,-5.1,vs. minimum,lbo_sweep_surplus
SWEEP_WATERFALL,Senior Debt Paydown,0.0,-1.5,-3.1,-5.1,-7.3,100% of surplus,lbo_sweep_sr_pay
SWEEP_WATERFALL,Sub Debt Paydown,0.0,0.0,0.0,0.0,0.0,Only after senior paid,lbo_sweep_sub_pay
SWEEP_WATERFALL,Dividend to Sponsors,0.0,0.0,0.0,0.0,0.0,Only after all debt paid,lbo_sweep_div
ENDING_POSITION,Ending Cash Balance,10.0,10.0,10.0,10.0,10.0,Maintained at minimum,lbo_sweep_end
VALIDATION,Cash Sweep Applied,0.0,1.5,3.1,5.1,7.3,Links to debt schedule,lbo_sweep_total
```

**Lineage Integration:**
- Cash sweep nodes link to debt schedule (paydown amounts must match)
- Validation edge: `debt_schedule[paydown] == cash_sweep[applied]`

#### File 6: `lbo_returns.csv`
```
Section,Item,Year_0,Year_1,Year_2,Year_3,Year_4,Year_5,Formula,Lineage_ID
EXIT_VALUE,LTM EBITDA at Exit,--,--,--,--,--,201.0,From operating model,lbo_ret_ebitda
EXIT_VALUE,Exit Multiple (EV/EBITDA),--,--,--,--,--,12.0,x,Assumption,lbo_ret_exit_mult
EXIT_VALUE,Enterprise Value at Exit,--,--,--,--,--,2412.0,=EBITDA × Multiple,lbo_ret_ev
EXIT_VALUE,Less: Net Debt at Exit,--,--,--,--,--,-597.7,From debt schedule,lbo_ret_debt
EXIT_VALUE,Gross Proceeds to Equity,--,--,--,--,--,1814.3,=EV - Debt,lbo_ret_proceeds
SPONSOR_RETURNS,Initial Equity Investment,-250.0,--,--,--,--,--,From sources & uses,lbo_ret_inv
SPONSOR_RETURNS,Exit Proceeds,--,--,--,--,--,1814.3,From above,lbo_ret_exit
SPONSOR_RETURNS,Money-on-Money (MoM),--,--,--,--,--,7.3,x,=Exit / Initial,lbo_ret_mom
SPONSOR_RETURNS,IRR,--,--,--,--,--,48.6%,NPV = 0,lbo_ret_irr
SENSITIVITY,Exit Multiple →,8.0x,9.0x,10.0x,11.0x,12.0x,13.0x,,
SENSITIVITY,IRR ↓,,,,,,,Sensitivity table,
SENSITIVITY,Year 3 Exit,14.5%,21.3%,27.8%,34.1%,40.1%,45.9%,lbo_sens_y3
SENSITIVITY,Year 4 Exit,22.1%,28.5%,34.6%,40.4%,46.0%,51.4%,lbo_sens_y4
SENSITIVITY,Year 5 Exit,26.9%,32.8%,38.5%,44.0%,48.6%,54.4%,lbo_sens_y5
DOWNSIDE_CASE,Exit Multiple,8.0,x,--,--,--,--,20% discount,lbo_down_mult
DOWNSIDE_CASE,Enterprise Value,1608.0,M,--,--,--,--,Calculated,lbo_down_ev
DOWNSIDE_CASE,Equity Proceeds,1000.3,M,--,--,--,--,Calculated,lbo_down_proc
DOWNSIDE_CASE,MoM,4.0,x,--,--,--,--,Calculated,lbo_down_mom
DOWNSIDE_CASE,IRR,32.0,%,--,--,--,--,Calculated,lbo_down_irr
```

**Lineage Integration:**
- Exit EBITDA links to operating model Year 5
- Net debt links to debt schedule Year 5
- IRR calculation: edge shows cash flows used in NPV formula
- Sensitivity table: Each cell is calculated node with edges to input variables

---

## Structural Specification

### Data Model

```python
@dataclass
class LBOTransaction:
    """LBO transaction setup."""
    target_company: str
    transaction_date: date
    ltm_ebitda: float
    entry_multiple: float
    enterprise_value: float  # Calculated
    equity_purchase_price: float  # Calculated
    holding_period_years: int
    exit_assumptions: ExitAssumptions

@dataclass
class SourcesAndUses:
    """Capital structure."""
    sources: List[DebtTranche | EquityTranche]
    uses: List[UseOfProceeds]

    def validate(self) -> bool:
        return sum(s.amount for s in self.sources) == sum(u.amount for u in self.uses)

@dataclass
class DebtTranche:
    """A single debt instrument."""
    name: str  # "Senior Term Loan A"
    amount: float
    interest_rate: float  # Annual %
    pik_rate: float = 0.0  # Payment-in-kind %
    term_years: int
    amortization_pct: float  # Annual % of original principal
    is_bullet: bool = False  # No amortization until maturity
    covenants: Dict[str, float] = field(default_factory=dict)

@dataclass
class CashSweep:
    """Cash sweep waterfall."""
    available_cash: float
    minimum_cash: float
    excess_cash: float
    paydown_waterfall: List[Tuple[str, float]]  # [(tranche_name, amount)]

@dataclass
class LBOReturns:
    """Sponsor returns."""
    initial_investment: float
    exit_proceeds: float
    mom: float  # Money-on-Money
    irr: float  # Internal Rate of Return
    holding_period: int
    cash_flows: List[Tuple[int, float]]  # [(year, amount)] for IRR calc
```

### File Format Specification

```yaml
lbo_transaction.csv:
  purpose: Transaction setup and exit assumptions
  sections:
    - PURCHASE_PRICE: Entry valuation
    - TIMING: Hold period
    - EXIT_ASSUMPTIONS: Exit multiple scenarios
  validation:
    - Enterprise Value = LTM EBITDA × Entry Multiple
    - Equity Purchase Price = EV - Cash + Debt

lbo_sources_uses.csv:
  purpose: Capital structure
  sections:
    - SOURCES: Debt tranches + Equity
    - USES: Purchase price + Fees
    - VALIDATION: Sources = Uses
    - CAPITAL_STRUCTURE: Summary metrics
  validation:
    - Total Sources = Total Uses (must equal)
    - Each debt tranche has: amount, rate, term, amortization
    - Equity is plug (Sources - Debt)

lbo_debt_schedule.csv:
  purpose: Debt dynamics over time
  sections:
    - SENIOR_DEBT: Term loan amortization + cash sweep
    - SUB_DEBT: PIK accrual
    - TOTAL: Aggregate debt + interest
  validation:
    - Beginning + PIK - Paydown = Ending (each period)
    - Cash sweep amounts match lbo_cash_sweep.csv
    - Interest = Avg Balance × Rate

lbo_operating_model.csv:
  purpose: Revenue and cash flow projections
  sections:
    - REVENUE: Growth assumptions
    - PROFITABILITY: EBITDA, EBIT, Net Income
    - CASH_FLOW: OCF available for debt service
  validation:
    - Interest expense matches lbo_debt_schedule.csv
    - EBITDA margin expansion explicit
    - Operating cash flow = NI + D&A - CapEx - ∆NWC

lbo_cash_sweep.csv:
  purpose: Excess cash waterfall
  sections:
    - CASH_AVAILABLE: OCF - Mandatory Amort
    - SWEEP_WATERFALL: Paydown priority
    - ENDING_POSITION: Cash maintained
    - VALIDATION: Links to debt schedule
  validation:
    - Minimum cash always maintained
    - Paydown amounts link to debt schedule
    - Waterfall priority: Senior → Sub → Dividends

lbo_returns.csv:
  purpose: Sponsor returns and sensitivity
  sections:
    - EXIT_VALUE: Exit valuation
    - SPONSOR_RETURNS: IRR and MoM
    - SENSITIVITY: Exit multiple × Exit year
    - DOWNSIDE_CASE: Conservative scenario
  validation:
    - IRR: NPV of cash flows = 0
    - MoM = Exit Proceeds / Initial Investment
    - Exit EBITDA from operating model
```

### Lineage Graph Integration

```python
# Example: Cash sweep links to multiple files

# Operating model node (Year 3 OCF)
ocf_node = FinancialNode(
    node_id="lbo_op_ocf_y3",
    value=25.7,
    concept="operating_cash_flow",
    period="Year_3"
)

# Debt schedule node (Year 3 mandatory amort)
mand_amort_node = FinancialNode(
    node_id="lbo_debt_mand_y3",
    value=-30.0,
    concept="mandatory_amortization",
    period="Year_3"
)

# Cash sweep calculation (Year 3 available cash)
cash_avail_edge = FinancialEdge(
    edge_id="lbo_sweep_calc_y3",
    edge_type=EdgeType.CALCULATION,
    source_node_ids=["lbo_op_ocf_y3", "lbo_debt_mand_y3"],
    target_node_id="lbo_sweep_avail_y3",
    formula="=OCF + Mandatory_Amort + Beginning_Cash",
    formula_inputs={
        "OCF": 25.7,
        "Mandatory_Amort": -30.0,
        "Beginning_Cash": 10.0
    }
)

# Cash sweep paydown links back to debt schedule
paydown_edge = FinancialEdge(
    edge_id="lbo_sweep_to_debt_y3",
    edge_type=EdgeType.CALCULATION,
    source_node_ids=["lbo_sweep_avail_y3"],
    target_node_id="lbo_debt_sr_sweep_y3",
    formula="=Excess_Cash",
    is_active=True,
    condition="Cash sweep applied to senior debt"
)

# Query: "How was Year 3 debt paydown calculated?"
graph.trace_backward("lbo_debt_sr_sweep_y3")
# Returns: Operating cash flow → Mandatory amort → Available cash → Paydown
```

---

## Degradation Strategy

### Missing Data Handling

```python
class LBOBuilder:
    def build_with_degradation(self, transaction, debt_terms, operating_assumptions):
        """Build LBO model with graceful degradation."""

        degradation_log = []

        # Check critical inputs
        if not debt_terms:
            # Fallback: Use industry standard capital structure
            debt_terms = {
                "senior_debt": {
                    "leverage": 5.0,  # 5.0x EBITDA
                    "rate": 0.075,
                    "term": 7,
                    "amortization": 0.05
                },
                "equity": "plug"
            }
            degradation_log.append({
                "section": "SOURCES",
                "issue": "No debt terms provided",
                "fallback": "Industry standard 5.0x leverage",
                "confidence": 0.5
            })

        if "exit_multiple" not in transaction:
            # Fallback: Use entry multiple (flat valuation)
            transaction["exit_multiple"] = transaction["entry_multiple"]
            degradation_log.append({
                "section": "EXIT_ASSUMPTIONS",
                "issue": "No exit multiple",
                "fallback": "Same as entry multiple",
                "confidence": 0.6
            })

        if "revenue_growth" not in operating_assumptions:
            # Fallback: Use historical CAGR
            historical_growth = self._calculate_historical_cagr()
            operating_assumptions["revenue_growth"] = historical_growth
            degradation_log.append({
                "section": "OPERATING_MODEL",
                "issue": "No revenue growth assumption",
                "fallback": f"Historical CAGR {historical_growth:.1%}",
                "confidence": 0.7
            })

        return degradation_log
```

### Output Indicators

```
File: lbo_transaction.csv

Section,Item,Value,Status,Notes
EXIT_ASSUMPTIONS,Exit Multiple (EV/EBITDA),10.0x,DEGRADED*,*Same as entry (no exit assumption provided)
```

---

## Summary: LBO Redesign

### What Changed
| Aspect | Old | New |
|--------|-----|-----|
| **Scope** | Credit metrics only | Full LBO model |
| **Files** | 1 output | 6 files (transaction, S&U, debt, operations, sweep, returns) |
| **Transaction** | None | Purchase price, entry multiple, exit assumptions |
| **Debt** | Static balance | Dynamic schedule with amortization + sweep |
| **Capital Structure** | Hardcoded "3.0x Lev" | Detailed tranches with terms |
| **Cash Sweep** | Not modeled | Waterfall with priority |
| **Returns** | Not calculated | IRR, MoM, sensitivity table |
| **Lineage** | None | Every cell linked to graph |
| **Degradation** | Silent errors | Flagged fallbacks |

### Bank Compliance
✅ True LBO model (not just credit metrics)
✅ Transaction assumptions explicit
✅ Debt dynamics modeled properly
✅ Cash sweep waterfall implemented
✅ Exit analysis with returns calculation
✅ Supports scenario/sensitivity analysis
✅ No hardcoded leverage logic
✅ Degrades gracefully with missing inputs
✅ Remains deterministic (no random defaults)

---

*Continues in PART 3: Comps Output Critique...*

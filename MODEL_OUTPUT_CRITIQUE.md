# FinanceX Model Output Critique & Redesign
**Perspective:** VP-level Model Review, Top-Tier Investment Bank
**Date:** 2026-01-07
**Reviewer:** Senior Principal Engineer / Financial Systems Architect

---

## Executive Summary

**VERDICT:** Current outputs are **NOT investment-grade**.

**Critical Deficiencies:**
1. DCF: Mixing calculations with outputs; no assumption separation; not presentation-ready
2. LBO: Not a true LBO model - just credit metrics with hardcoded leverage
3. Comps: Raw metrics mixed with derived multiples; silent error handling; no normalization transparency

**Impact:**
- Models cannot be presented to clients
- Audit trail is incomplete
- Sensitivity analysis impossible
- Violates bank model review standards

**Recommendation:** Complete structural redesign required before production deployment.

---

# PART 1: DCF OUTPUT CRITIQUE

## Current Structure (engine.py:1159-1186)

```python
data = {
    "Total Revenue": revenue,
    "(-) COGS": cogs,
    "(=) Gross Profit": gross_profit,
    "Gross Margin %": (gross_profit / revenue * 100)...,
    "(-) SG&A": sga,
    "(-) R&D": rnd,
    "(-) Other Operating Expenses": other_opex,
    "(=) EBITDA": ebitda_reported,
    "EBITDA Margin %": (ebitda_reported / revenue * 100)...,
    "(-) D&A": da,
    "(=) EBIT": ebit,
    "EBIT Margin %": (ebit / revenue * 100)...,
    "(-) Cash Taxes": taxes,
    "(=) NOPAT": nopat,
    "(+) D&A Addback": da,
    "(-) Change in NWC": delta_nwc,
    "(-) CapEx": capex,
    "(=) Unlevered Free Cash Flow": ufcf,
    "UFCF Margin %": (ufcf / revenue * 100)...,
}
```

## Issues Identified

### CRITICAL ISSUES

#### 1. **Assumptions Embedded in Calculations**
**Problem:**
```python
"Gross Margin %": (gross_profit / revenue * 100)
```
This is a **derived metric**, not an input. In a proper DCF model:
- Historical margins are **observations**
- Projected margins are **assumptions** (set by analyst)
- The model should separate these clearly

**Why This Matters:**
- Cannot run sensitivity on margins (e.g., "What if EBITDA margin drops 2%?")
- Cannot override calculated margins with analyst assumptions
- Violates separation of concerns (inputs vs. outputs)

**Bank Standard:**
```
ASSUMPTIONS SECTION:
- Revenue Growth % (by year)
- EBITDA Margin % (target)
- Tax Rate %
- CapEx as % of Revenue

CALCULATIONS SECTION:
- Revenue = Prior Revenue × (1 + Growth %)
- EBITDA = Revenue × EBITDA Margin %
- Taxes = EBIT × Tax Rate

OUTPUTS SECTION:
- Unlevered FCF
- Terminal Value
- Enterprise Value
- Implied Valuation
```

#### 2. **No Distinction Between Historical and Projection**
**Problem:** Output shows periods as columns (2021, 2022, 2023) but doesn't indicate:
- Which periods are historical (actuals)
- Which periods are projected (model)
- Where the stub period ends

**Why This Matters:**
- Analysts can't tell where facts end and assumptions begin
- Auditors require clear delineation
- Model review process requires historical accuracy verification

**Bank Standard:**
```
Columns:
LTM | FY2023A | FY2024E | FY2025E | FY2026E | Terminal
 ^       ^         ^         ^         ^          ^
Actual  Actual   Estimate  Estimate  Estimate  Perpetuity
```

#### 3. **Calculations Mixed with Outputs**
**Problem:**
- NOPAT calculation (`ebit - taxes`) happens in model builder
- No intermediate calculation audit trail
- Cannot verify formula logic from output alone

**Why This Matters:**
- Model review requires formula transparency
- Errors in calculation logic are undetectable
- Cannot replicate calculations independently

**Bank Standard:** Separate files/tabs:
- `assumptions.csv` - All model inputs
- `calculations.csv` - Step-by-step formulas with cell references
- `outputs.csv` - Final results only
- `audit_trail.csv` - Formula verification

#### 4. **No Support for Sensitivity Expansion**
**Problem:** Structure doesn't allow adding:
- Downside case (Revenue -10%)
- Base case
- Upside case (Revenue +10%)

**Why This Matters:**
- Every DCF presentation includes scenario analysis
- Lenders require downside case
- Board presentations need range of outcomes

**Bank Standard:**
```
Scenario           | FY2024E Revenue | EBITDA Margin | UFCF
-------------------|-----------------|---------------|------
Downside (-10%)    | $900M          | 18%           | $120M
Base Case          | $1,000M        | 20%           | $150M
Upside (+10%)      | $1,100M        | 22%           | $180M
```

#### 5. **Missing Critical DCF Components**
**Problem:** No support for:
- WACC calculation
- Terminal value
- Discounting periods
- Enterprise value calculation
- Bridge to equity value

**Why This Matters:**
- This is a "historical setup" not a complete DCF
- Cannot produce valuation output
- Misleading to call this "DCF ready"

**Bank Standard:** Full DCF includes:
```
1. Historical Financials (3-5 years)
2. Projection Assumptions
3. Projected Financials (5 years)
4. Free Cash Flow Calculation
5. WACC Calculation
6. DCF Valuation:
   - PV of FCFs
   - Terminal Value
   - Enterprise Value
   - (-) Net Debt
   - (=) Equity Value
   - (/) Shares Outstanding
   - (=) Implied Price per Share
```

### MEDIUM SEVERITY ISSUES

#### 6. **Inconsistent Formatting**
**Problem:**
```python
"(=) EBITDA": ebitda_reported
"EBITDA Margin %": ...
```
Margins are interspersed with dollar amounts - breaks visual hierarchy.

**Bank Standard:** Group by type:
```
P&L (Dollar Amounts):
  Revenue
  COGS
  Gross Profit
  SG&A
  EBITDA

Margins (%):
  Gross Margin %
  EBITDA Margin %
  UFCF Margin %
```

#### 7. **Hardcoded Error Handling**
**Problem:**
```python
.replace([float('inf'), float('-inf')], 0).fillna(0)
```
Silently converts division-by-zero to 0%, hiding data quality issues.

**Bank Standard:**
- Division by zero → Display "N/M" (not meaningful)
- Missing data → Display "--" (not available)
- Negative margins on revenue multiples → Flag as error

#### 8. **No Growth Rates**
**Problem:** Missing year-over-year growth calculations:
```python
Revenue Growth % = (Revenue_t / Revenue_t-1) - 1
```

**Bank Standard:** Every P&L line should have:
- Historical values
- Growth rates (YoY %)
- CAGR (compound annual growth rate)

### LOW SEVERITY ISSUES

#### 9. **Label Inconsistency**
**Problem:**
```python
"(-) Change in NWC"  # Uses "Change in"
"(-) CapEx"          # Doesn't specify it's a use of cash
```

**Bank Standard:**
```
"(Increase) / Decrease in NWC"  # Clarifies sign convention
"Capital Expenditures"          # Full name first occurrence
```

#### 10. **Missing Metadata**
**Problem:** No header rows with:
- Company name
- Model date
- Fiscal year end
- Currency
- Units (thousands, millions)

**Bank Standard:**
```
Company: [Company Name]
Date: January 7, 2026
FYE: December 31
Currency: USD
Units: Millions
```

---

## Redesigned DCF Structure

### Principles
1. **Separation of Concerns:** Assumptions | Calculations | Outputs
2. **Temporal Clarity:** Historical (A) vs. Projected (E) vs. Terminal
3. **Audit Trail:** Every number traceable to source or formula
4. **Extensibility:** Supports scenarios, sensitivities, cases

### File Structure

#### File 1: `dcf_assumptions.csv`
```
Section,Item,FY2024E,FY2025E,FY2026E,Terminal,Source,Notes
REVENUE,Revenue Growth %,5.0%,4.0%,3.5%,2.5%,Management Guidance,Post-COVID normalization
MARGINS,EBITDA Margin %,22.0%,23.0%,24.0%,24.0%,Analyst Estimate,Operating leverage
MARGINS,Tax Rate %,25.0%,25.0%,26.0%,26.0%,Statutory Rate,TCJA expiration
CAPEX,CapEx % of Revenue,4.5%,4.0%,3.5%,3.0%,Industry Average,Maintenance capex
CAPEX,D&A % of Revenue,3.5%,3.5%,3.5%,3.5%,Historical Average,Straight-line
NWC,NWC % of Revenue,12.0%,12.0%,12.0%,12.0%,Historical Average,Working capital
WACC,Cost of Equity,9.5%,,,,,CAPM,Beta 1.2
WACC,Cost of Debt (after-tax),3.5%,,,,,Market Rate,BBB rating
WACC,Target D/E Ratio,0.25,,,,,Capital Structure,Conservative
WACC,WACC,8.2%,,,,,Weighted Average,
TERMINAL,Terminal Growth %,2.5%,,,,,Perpetuity,GDP growth proxy
TERMINAL,Terminal EV/EBITDA,10.0x,,,,,Exit Multiple,Industry median
```

**Lineage Integration:**
- Each assumption cell is a `FinancialNode` (type: ASSUMPTION)
- Linked via edge to source: analyst input, management guidance, market data
- Edge carries: `method="analyst_override"`, `confidence=user_specified`, `source=analyst_brain`

#### File 2: `dcf_historical.csv`
```
Section,Metric,FY2021A,FY2022A,FY2023A,LTM,Lineage_ID
INCOME_STATEMENT,Revenue,950.0,990.0,1005.0,1020.0,node_12345
INCOME_STATEMENT,COGS,665.0,683.1,693.5,704.4,node_12346
INCOME_STATEMENT,Gross Profit,285.0,306.9,311.5,315.6,node_12347
INCOME_STATEMENT,SG&A,142.5,148.5,150.8,153.0,node_12348
INCOME_STATEMENT,R&D,47.5,49.5,50.3,51.0,node_12349
INCOME_STATEMENT,EBITDA,95.0,108.9,110.5,111.6,node_12350
INCOME_STATEMENT,D&A,33.3,34.7,35.2,35.7,node_12351
INCOME_STATEMENT,EBIT,61.8,74.2,75.3,75.9,node_12352
INCOME_STATEMENT,Interest Expense,10.0,9.5,9.0,8.5,node_12353
INCOME_STATEMENT,EBT,51.8,64.7,66.3,67.4,node_12354
INCOME_STATEMENT,Taxes,13.0,16.2,16.6,16.9,node_12355
INCOME_STATEMENT,Net Income,38.8,48.5,49.7,50.5,node_12356
BALANCE_SHEET,Cash,50.0,55.0,60.0,65.0,node_12357
BALANCE_SHEET,Accounts Receivable,95.0,99.0,100.5,102.0,node_12358
BALANCE_SHEET,Inventory,120.0,125.0,127.5,130.0,node_12359
BALANCE_SHEET,Total Current Assets,265.0,279.0,288.0,297.0,node_12360
BALANCE_SHEET,PP&E (Net),450.0,470.0,485.0,500.0,node_12361
BALANCE_SHEET,Total Assets,715.0,749.0,773.0,797.0,node_12362
BALANCE_SHEET,Accounts Payable,75.0,79.0,81.0,83.0,node_12363
BALANCE_SHEET,Short-Term Debt,25.0,20.0,15.0,10.0,node_12364
BALANCE_SHEET,Total Current Liabilities,100.0,99.0,96.0,93.0,node_12365
BALANCE_SHEET,Long-Term Debt,200.0,190.0,180.0,170.0,node_12366
BALANCE_SHEET,Total Liabilities,300.0,289.0,276.0,263.0,node_12367
BALANCE_SHEET,Shareholders' Equity,415.0,460.0,497.0,534.0,node_12368
CASH_FLOW,CFO,85.0,95.0,98.0,100.0,node_12369
CASH_FLOW,CapEx,-40.0,-42.0,-43.0,-44.0,node_12370
CASH_FLOW,FCF,45.0,53.0,55.0,56.0,node_12371
METRICS,Revenue Growth %,--,4.2%,1.5%,1.5%,calculated
METRICS,EBITDA Margin %,10.0%,11.0%,11.0%,10.9%,calculated
METRICS,Net Margin %,4.1%,4.9%,4.9%,5.0%,calculated
METRICS,ROIC %,--,10.5%,10.3%,10.1%,calculated
```

**Lineage Integration:**
- Each historical value has `Lineage_ID` pointing to graph node
- Can trace backward to source Excel cells
- Growth rates are calculated nodes with edges showing formula

#### File 3: `dcf_projections.csv`
```
Section,Metric,FY2024E,FY2025E,FY2026E,Terminal,Formula_Reference,Lineage_ID
REVENUE_BUILD,Prior Year Revenue,1020.0,1071.0,1113.8,1153.8,=Historical[LTM],node_20001
REVENUE_BUILD,Revenue Growth %,5.0%,4.0%,3.5%,2.5%,=Assumptions[Revenue Growth],node_20002
REVENUE_BUILD,Revenue,1071.0,1113.8,1153.8,1182.6,=Prior*(1+Growth),node_20003
MARGIN_CALC,EBITDA Margin %,22.0%,23.0%,24.0%,24.0%,=Assumptions[EBITDA Margin],node_20004
MARGIN_CALC,EBITDA,235.6,256.2,276.9,283.8,=Revenue*Margin,node_20005
MARGIN_CALC,EBITDA Margin (Check),22.0%,23.0%,24.0%,24.0%,=EBITDA/Revenue,node_20006
OPEX_DETAIL,D&A % Revenue,3.5%,3.5%,3.5%,3.5%,=Assumptions[D&A %],node_20007
OPEX_DETAIL,D&A,37.5,39.0,40.4,41.4,=Revenue*D&A%,node_20008
PROFITABILITY,EBIT,198.1,217.2,236.5,242.4,=EBITDA-D&A,node_20009
PROFITABILITY,Tax Rate %,25.0%,25.0%,26.0%,26.0%,=Assumptions[Tax Rate],node_20010
PROFITABILITY,Taxes,49.5,54.3,61.5,63.0,=EBIT*Tax Rate,node_20011
PROFITABILITY,NOPAT,148.6,162.9,175.0,179.4,=EBIT-Taxes,node_20012
CF_BRIDGE,NOPAT,148.6,162.9,175.0,179.4,=From Above,node_20013
CF_BRIDGE,Add: D&A,37.5,39.0,40.4,41.4,=From Above,node_20014
CF_BRIDGE,CapEx % Revenue,4.5%,4.0%,3.5%,3.0%,=Assumptions[CapEx %],node_20015
CF_BRIDGE,Less: CapEx,-48.2,-44.6,-40.4,-35.5,=Revenue*CapEx%,node_20016
CF_BRIDGE,NWC % Revenue,12.0%,12.0%,12.0%,12.0%,=Assumptions[NWC %],node_20017
CF_BRIDGE,NWC Balance,128.5,133.7,138.5,141.9,=Revenue*NWC%,node_20018
CF_BRIDGE,Change in NWC,-5.5,-5.1,-4.8,-3.5,=NWC_t - NWC_t-1,node_20019
CF_BRIDGE,Unlevered FCF,132.4,152.1,170.2,182.8,=NOPAT+D&A-CapEx-∆NWC,node_20020
DISCOUNTING,Discount Period,0.5,1.5,2.5,--,Mid-year convention,node_20021
DISCOUNTING,Discount Factor,0.961,0.889,0.822,--,=1/(1+WACC)^Period,node_20022
DISCOUNTING,PV of FCF,127.3,135.2,139.9,--,=FCF*Discount Factor,node_20023
```

**Lineage Integration:**
- Each projection cell is a CALCULATED node
- Edge shows formula: `formula="=Revenue * EBITDA_Margin"`, `inputs={"Revenue": 1071.0, "Margin": 0.22}`
- Can trace to assumption nodes (EBITDA Margin %) and historical nodes (Revenue growth trend)

#### File 4: `dcf_valuation.csv`
```
Section,Item,Value,Formula,Lineage_ID
OPERATING_VALUE,Sum of PV(FCF FY24E-FY26E),402.4,=SUM(Projections[PV of FCF]),node_30001
TERMINAL_VALUE,Terminal FCF,182.8,=Projections[Terminal FCF],node_30002
TERMINAL_VALUE,Terminal Growth %,2.5%,=Assumptions[Terminal Growth],node_30003
TERMINAL_VALUE,WACC,8.2%,=Assumptions[WACC],node_30004
TERMINAL_VALUE,Terminal Value (Perpetuity),3145.5,=Terminal FCF*(1+g)/(WACC-g),node_30005
TERMINAL_VALUE,PV of Terminal Value,2585.0,=TV*Discount Factor[Terminal],node_30006
ENTERPRISE_VALUE,Enterprise Value (DCF),2987.4,=PV(FCFs)+PV(TV),node_30007
BRIDGE_TO_EQUITY,Enterprise Value,2987.4,=From Above,node_30008
BRIDGE_TO_EQUITY,Less: Net Debt,105.0,=Historical[Total Debt - Cash],node_30009
BRIDGE_TO_EQUITY,Add: Non-Operating Assets,0.0,User Input,node_30010
BRIDGE_TO_EQUITY,Equity Value,2882.4,=EV - Net Debt + NOA,node_30011
PER_SHARE,Equity Value,2882.4,=From Above,node_30012
PER_SHARE,Shares Outstanding (FD),100.0,=Historical[Diluted Shares],node_30013
PER_SHARE,Implied Price per Share,$28.82,=Equity Value / Shares,node_30014
PER_SHARE,Current Market Price,$25.00,User Input / Market Data,node_30015
PER_SHARE,Upside / (Downside),15.3%,=(Implied - Current)/Current,node_30016
SENSITIVITY_TABLE,WACC →,7.2%,7.7%,8.2%,8.7%,9.2%,sensitivity_input
SENSITIVITY_TABLE,Terminal Growth ↓,,,,,,,
SENSITIVITY_TABLE,1.5%,$26.45,$25.12,$23.95,$22.91,$21.99,sensitivity_output
SENSITIVITY_TABLE,2.0%,$28.11,$26.52,$25.12,$23.88,$22.77,sensitivity_output
SENSITIVITY_TABLE,2.5%,$30.12,$28.21,$26.52,$25.00,$23.65,sensitivity_output
SENSITIVITY_TABLE,3.0%,$32.58,$30.29,$28.21,$26.35,$24.67,sensitivity_output
SENSITIVITY_TABLE,3.5%,$35.63,$32.84,$30.29,$27.97,$25.87,sensitivity_output
```

**Lineage Integration:**
- Valuation nodes link to projection nodes and assumption nodes
- Sensitivity table: Each output cell is calculated node with edges to input cells
- Can query: "How did we arrive at $28.82 per share?" → Trace backward through all calculation nodes

---

## Structural Specification

### Data Model

```python
@dataclass
class DCFSection:
    """A section of the DCF model."""
    section_name: str  # "ASSUMPTIONS", "HISTORICAL", "PROJECTIONS", "VALUATION"
    section_type: SectionType  # ASSUMPTION | HISTORICAL | CALCULATED | OUTPUT
    rows: List[DCFRow]

@dataclass
class DCFRow:
    """A single row in the DCF model."""
    row_label: str
    periods: Dict[str, DCFCell]  # period -> cell
    lineage_id: Optional[str]  # Link to graph node

@dataclass
class DCFCell:
    """A single cell in the DCF model."""
    value: Any
    period: str  # "FY2024E", "FY2025E", "Terminal"
    period_type: PeriodType  # ACTUAL | ESTIMATE | TERMINAL
    formula: Optional[str]  # "=Revenue * EBITDA_Margin"
    source: Optional[str]  # "Historical[LTM]", "Assumptions[Revenue Growth]"
    lineage_node_id: str

@dataclass
class SensitivityTable:
    """2D sensitivity analysis."""
    row_variable: str  # "Terminal Growth %"
    col_variable: str  # "WACC"
    output_metric: str  # "Implied Price per Share"
    grid: Dict[Tuple[float, float], float]  # (row_val, col_val) -> output
```

### File Format Specification

```yaml
dcf_assumptions.csv:
  columns:
    - Section: str (REVENUE | MARGINS | CAPEX | NWC | WACC | TERMINAL)
    - Item: str
    - FY2024E: float
    - FY2025E: float
    - FY2026E: float
    - Terminal: float
    - Source: str (Management | Analyst | Market | Historical)
    - Notes: str
  sorting: By Section, then by Item
  validation:
    - All percentages in decimal form (0.05 for 5%)
    - No empty cells (use 0 or "N/A")
    - Terminal column may be blank for non-perpetuity items

dcf_historical.csv:
  columns:
    - Section: str (INCOME_STATEMENT | BALANCE_SHEET | CASH_FLOW | METRICS)
    - Metric: str
    - FY2021A: float
    - FY2022A: float
    - FY2023A: float
    - LTM: float
    - Lineage_ID: str
  suffix_convention:
    - "A" = Actual (audited financials)
    - "LTM" = Last Twelve Months
  validation:
    - Every cell must have Lineage_ID
    - Metrics section uses calculated values only

dcf_projections.csv:
  columns:
    - Section: str (REVENUE_BUILD | MARGIN_CALC | OPEX_DETAIL | etc.)
    - Metric: str
    - FY2024E: float
    - FY2025E: float
    - FY2026E: float
    - Terminal: float
    - Formula_Reference: str
    - Lineage_ID: str
  suffix_convention:
    - "E" = Estimate (projected)
  validation:
    - Formula_Reference must reference Assumptions or Historical
    - All calculated values must have Lineage_ID

dcf_valuation.csv:
  columns:
    - Section: str (OPERATING_VALUE | TERMINAL_VALUE | ENTERPRISE_VALUE | etc.)
    - Item: str
    - Value: float
    - Formula: str
    - Lineage_ID: str
  validation:
    - Formula must be complete (no cell references, use named ranges)
    - Final output: Implied Price per Share
```

### Lineage Graph Integration

```python
# Example: Revenue Growth assumption
assumption_node = FinancialNode(
    node_id="node_20002",
    node_type=NodeType.ASSUMPTION,
    concept="revenue_growth_rate",
    label="Revenue Growth % - FY2024E",
    value=0.05,
    period="FY2024E"
)

# Projected revenue calculation
revenue_edge = FinancialEdge(
    edge_id="edge_20003",
    edge_type=EdgeType.CALCULATION,
    source_node_ids=["node_20001", "node_20002"],  # Prior revenue + growth rate
    target_node_id="node_20003",  # FY2024E Revenue
    method="formula",
    formula="=Prior_Revenue * (1 + Growth_Rate)",
    formula_inputs={
        "Prior_Revenue": 1020.0,
        "Growth_Rate": 0.05
    },
    confidence=1.0
)

# Query: "How was FY2024E Revenue calculated?"
graph.trace_backward("node_20003")
# Returns: [assumption_node, historical_revenue_node] + formulas
```

---

## Degradation Strategy

### Missing Data Handling

```python
class DCFBuilder:
    def build_projections(self, assumptions, historical):
        """Build projections with graceful degradation."""

        # Check for critical assumptions
        if "Revenue Growth %" not in assumptions:
            # Fallback: Use historical CAGR
            growth_rate = self._calculate_historical_cagr(historical["Revenue"])
            self._log_degradation("Revenue Growth %", "assumption", "historical_cagr")

        if "EBITDA Margin %" not in assumptions:
            # Fallback: Use historical average
            margin = historical["EBITDA"].mean() / historical["Revenue"].mean()
            self._log_degradation("EBITDA Margin %", "assumption", "historical_avg")

        # Mark degraded sections
        self.degradation_log.append({
            "section": "PROJECTIONS",
            "item": "Revenue Growth %",
            "status": "DEGRADED",
            "method": "historical_cagr",
            "confidence": 0.6
        })
```

### Output Indicators

```
Section,Metric,FY2024E,FY2025E,Status,Notes
REVENUE_BUILD,Revenue Growth %,5.0%*,4.0%*,DEGRADED,*Historical CAGR fallback
```

---

## Summary: DCF Redesign

### What Changed
| Aspect | Old | New |
|--------|-----|-----|
| **Files** | 1 output CSV | 4 CSV files (assumptions, historical, projections, valuation) |
| **Structure** | Flat | Hierarchical (sections) |
| **Assumptions** | Embedded | Separate file |
| **Formulas** | Hidden | Explicit in Formula_Reference column |
| **Lineage** | None | Every cell has Lineage_ID |
| **Scenarios** | Not supported | Sensitivity table included |
| **Degradation** | Silent | Flagged with notes |
| **Audit Trail** | Incomplete | Complete (formulas + lineage) |

### Bank Compliance
✅ Separates assumptions from calculations
✅ Supports scenario/sensitivity analysis
✅ Provides complete audit trail
✅ Presentation-ready structure
✅ Model-auditable (every formula traceable)
✅ Structurally standard (matches IB templates)
✅ Internally consistent (cross-references validated)

---

*Continues in PART 2: LBO Output Critique...*

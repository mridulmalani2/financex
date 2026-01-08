# FinanceX UI Design Specification
**Version:** 1.0
**Date:** 2026-01-08
**Status:** Design Phase

---

## Design Philosophy

### Core Principles
1. **Trust** - Every number is auditable, every decision is explainable
2. **Traceability** - Complete lineage from Excel source to final output
3. **Fixability** - Users can correct errors and understand impact immediately

### Design Constraints
- ❌ NO marketing UI, hero sections, or feature showcases
- ❌ NO gimmicks, animations, or decorative elements
- ❌ NO hidden complexity or "smart" defaults without explanation
- ✅ ONLY features that support audit, correction, and understanding
- ✅ Every interaction must answer "Why?" and "How do I fix this?"

### Audience
**Primary:** Investment banking analysts, associates, and VPs
**Mindset:** Excel power users, skeptical of automation, need audit trails
**Expectations:** Bloomberg Terminal clarity, Excel-like precision, instant drill-down

---

## Essential Screens (7 Total)

### 1. **Upload & Configure** (Single Screen)
**Purpose:** Get data in, configure session
**Components:**
- Excel file upload (drag & drop)
- Analyst Brain upload (optional, .json)
- Company name input (for labeling outputs)
- Processing status (live progress: Extracting → Mapping → Modeling → Validating)

**What's NOT included:**
- ❌ File format tutorials (should be in docs, not UI)
- ❌ Sample files or guided tours
- ❌ Settings or preferences beyond Brain upload

---

### 2. **Control Panel** (Dashboard)
**Purpose:** System health at a glance, immediate action on problems
**Layout:** 3-column grid

#### Left Column: **Quality Metrics**
```
┌─ SYSTEM STATUS ────────────────┐
│ Processing: ✓ Complete         │
│ Duration: 12.4s                 │
│                                 │
│ ┌─ Audit Results ─────────┐   │
│ │ 🔴 3  CRITICAL           │   │
│ │ 🟡 12 WARNINGS           │   │
│ │ ✅ 51 PASSED             │   │
│ └──────────────────────────┘   │
│                                 │
│ ┌─ Confidence Health ─────┐   │
│ │ DCF:   ⚠️  BLOCKED       │   │
│ │        Revenue: 0.52     │   │
│ │ LBO:   ✅ CLEARED        │   │
│ │        EBITDA: 0.88      │   │
│ │ Comps: ✅ CLEARED        │   │
│ │        Revenue: 0.90     │   │
│ └──────────────────────────┘   │
└─────────────────────────────────┘
```

#### Center Column: **Financial Models**
- Tab navigation: DCF | LBO | Comps
- Each model shows as data table with:
  - Row headers (concept names)
  - Column headers (periods)
  - Cell values with confidence indicators
  - **Critical:** Every cell is clickable → triggers "Why This Number?"

#### Right Column: **Active Issues**
```
┌─ REQUIRES ATTENTION ───────────┐
│                                 │
│ 🔴 DCF Revenue Below Threshold  │
│    Current: 0.52 | Need: 0.60   │
│    → View 4 unmapped items      │
│                                 │
│ 🟡 Balance Sheet: Off by 2.3%   │
│    Assets - Liab ≠ Equity       │
│    → View lineage               │
│                                 │
│ 🟡 12 Unmapped Line Items       │
│    83% of data mapped           │
│    → Fix now                    │
│                                 │
└─────────────────────────────────┘
```

**What's NOT included:**
- ❌ Charts, graphs, or visualizations (can't drill-down on pixels)
- ❌ Summary statistics or derived metrics
- ❌ "Insights" or automated commentary

---

### 3. **"Why This Number?" Modal** (Universal Drill-Down)
**Trigger:** Click any cell in any financial model
**Purpose:** Complete audit trail for a single value

**Layout:** Full-screen overlay, divided into 4 sections

#### Section 1: **Value Summary** (Top bar)
```
┌────────────────────────────────────────────────────────────────┐
│ Revenue | Q4 2024 | $1,234,567,890                             │
│                                                                 │
│ Confidence: 0.88 ████████░░ [CLEARED]                          │
│ Source: Hierarchy Fallback (Tier 4) via Analyst Brain          │
│ Audit Status: ✅ 3 checks passed, 🟡 1 warning                 │
└────────────────────────────────────────────────────────────────┘
```

#### Section 2: **Lineage Graph Slice** (Visual)
```
Excel Source
    ↓ EXTRACTION (conf: 0.95)
Sheet: "Income Statement", Row: 4, Col: E
Value: "$1,234,567,890"
    ↓ MAPPING (conf: 0.70, method: Keyword Match)
Label: "Total Revenues" → Concept: "us-gaap:Revenues"
    ↓ SUPERSEDED (conf: 1.00, via: Analyst Brain Override)
New Concept: "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"
    ↓ AGGREGATION (conf: 0.95, strategy: Total Line Used)
Pivoted: Revenue | 2024-12-31 | $1,234,567,890
    ↓ CALCULATION (conf: 0.88, formula: Direct)
Output: DCF Revenue | Q4 2024 | $1,234,567,890
```

**Interaction:** Each node is clickable
- Click "Excel Source" → Shows screenshot of actual Excel cell (if available)
- Click "MAPPING" edge → Shows why this mapping was chosen, alternatives considered
- Click "SUPERSEDED" → Shows Analyst Brain entry that overrode default
- Click "AGGREGATION" → Shows all components considered, why this total was used

#### Section 3: **Confidence Breakdown** (Table)
```
┌─ CONFIDENCE CALCULATION ────────────────────────────────────────┐
│ Step                  | Score | Reason                          │
├───────────────────────┼───────┼─────────────────────────────────┤
│ Base Mapping          | 0.70  | Keyword match (not exact)       │
│ Analyst Brain Boost   | +0.30 | Human override applied          │
│ → Mapping Confidence  | 1.00  | Analyst Brain = 100% trust      │
│                       |       |                                 │
│ Aggregation Method    | 0.95  | Total line used (preferred)     │
│                       |       |                                 │
│ Propagation Rule      | MIN   | Weakest link determines final   │
│ → Final Confidence    | 0.95  | MIN(1.00, 0.95) = 0.95          │
│                       |       |                                 │
│ Degradation Applied   | -0.07 | Hierarchy depth penalty         │
│ → Output Confidence   | 0.88  | 0.95 × (1 - 0.07) = 0.88        │
└─────────────────────────────────────────────────────────────────┘
```

#### Section 4: **Related Audit Findings** (List)
```
┌─ AUDIT CHECKS FOR THIS VALUE ──────────────────────────────────┐
│                                                                 │
│ ✅ PASS | Revenue Growth Rate (YoY)                            │
│    16.2% growth is within normal range (0-50%)                 │
│                                                                 │
│ ✅ PASS | Revenue Sign Check                                   │
│    Value is positive (expected for revenue)                    │
│                                                                 │
│ ✅ PASS | Cross-Statement Linkage                              │
│    Matches revenue in cash flow statement                      │
│                                                                 │
│ 🟡 WARNING | Revenue Concentration                             │
│    91% from single line item - verify breakdown is complete    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Section 5: **Action Buttons** (Bottom bar)
```
┌────────────────────────────────────────────────────────────────┐
│ [← Back to Model]  [📋 Copy Audit Trail]  [🔧 Fix This Value] │
└────────────────────────────────────────────────────────────────┘
```

**Banker-Friendly Language Translations:**
- NOT: "Node traversal" → USE: "Source chain"
- NOT: "Confidence score" → USE: "Reliability rating"
- NOT: "Aggregation strategy" → USE: "Rollup method"
- NOT: "Superseded edge" → USE: "Your override applied"
- NOT: "Graph query" → USE: "Trace to source"

**What's NOT included:**
- ❌ Technical jargon (nodes, edges, graphs)
- ❌ Code snippets or function names
- ❌ Raw JSON or data structures
- ❌ Irrelevant lineage paths (only show path for THIS value)

---

### 4. **Fix Unmapped** (Correction Interface)
**Purpose:** Map unmapped line items to correct concepts
**Layout:** Split screen

#### Left: **Unmapped Items** (List)
```
┌─ UNMAPPED LINE ITEMS (12) ─────────────────────────────────────┐
│                                                                 │
│ [1] "Product Sales - North America" | $45M | Q4 2024           │
│     Suggestions:                                                │
│     • us-gaap:RevenueFromContractWithCustomerExcludingAssessed  │
│     • us-gaap:ProductRevenue                                    │
│     [Map to...▼]  [Skip]                                        │
│                                                                 │
│ [2] "Cloud Subscriptions (ARR)" | $12M | Q4 2024              │
│     Suggestions:                                                │
│     • us-gaap:SoftwareRevenue                                   │
│     • custom:RecurringRevenue                                   │
│     [Map to...▼]  [Skip]                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Right: **Taxonomy Browser** (Search)
```
┌─ SEARCH TAXONOMY (23,598 concepts) ────────────────────────────┐
│                                                                 │
│ [Search: "revenue"                            🔍]               │
│                                                                 │
│ Results (78):                                                   │
│ • us-gaap:Revenues                                              │
│   "Revenue from all sources"                                    │
│   Used in: DCF, Comps                                           │
│                                                                 │
│ • us-gaap:RevenueFromContractWithCustomerExcludingAssessed      │
│   "Revenue under ASC 606, excluding taxes"                      │
│   Used in: DCF, Comps                                           │
│                                                                 │
│ • ifrs-full:Revenue                                             │
│   "IFRS revenue (all sources)"                                  │
│   Used in: DCF, Comps                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Interaction:**
1. Select unmapped item (left)
2. Search taxonomy (right)
3. Click concept → Auto-fills dropdown
4. Click "Map to..." → Saves to Analyst Brain
5. Re-processes models immediately
6. Shows updated confidence scores

**Feedback Loop:**
```
✅ Mapped "Product Sales - North America" → us-gaap:Revenues
   Saved to Analyst Brain (will apply to future uploads)
   Re-processing models...

   Impact:
   • DCF Revenue confidence: 0.52 → 0.68 ⚠️ Still below threshold
   • 11 unmapped items remaining
```

**What's NOT included:**
- ❌ Bulk mapping tools (one-at-a-time ensures quality)
- ❌ Auto-map suggestions without user confirmation
- ❌ Ability to create custom concepts (must use taxonomy)

---

### 5. **Audit Report** (Validation Results)
**Purpose:** Full forensic accounting review
**Layout:** Tabbed by severity

#### Tab 1: **Critical** (Blockers)
```
┌─ CRITICAL ISSUES (3) ──────────────────────────────────────────┐
│                                                                 │
│ 🔴 FAIL | Balance Sheet Does Not Balance                       │
│    Assets ($450M) ≠ Liabilities ($320M) + Equity ($125M)       │
│    Off by: $5M (1.1%)                                           │
│    → [Trace Assets] [Trace Liabilities] [Trace Equity]         │
│                                                                 │
│ 🔴 FAIL | Negative Revenue in Period                           │
│    Q2 2024: Revenue = -$15M (should be positive)               │
│    → [View Source Cell] [Check Mapping]                        │
│                                                                 │
│ 🔴 FAIL | DCF Blocked - Revenue Confidence Too Low             │
│    Current: 0.52 | Required: 0.60                              │
│    → [Fix Unmapped Items]                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Tab 2: **Warnings** (Review Recommended)
```
┌─ WARNINGS (12) ────────────────────────────────────────────────┐
│                                                                 │
│ 🟡 WARN | High Revenue Growth Rate                             │
│    Q4 2024: +187% YoY (typical range: 0-50%)                   │
│    Verify this is correct                                      │
│    → [View Revenue Over Time] [Check Source]                   │
│                                                                 │
│ 🟡 WARN | Missing D&A                                          │
│    Depreciation & Amortization not found                       │
│    EBITDA calculation may be inaccurate                        │
│    → [Map D&A Manually]                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Tab 3: **Passed** (Informational)
```
┌─ PASSED CHECKS (51) ───────────────────────────────────────────┐
│                                                                 │
│ ✅ PASS | Current Ratio (2.3x in normal range)                 │
│ ✅ PASS | EBITDA Margin Stability (12.5% ± 2%)                 │
│ ✅ PASS | Consistent Period Labels (all quarterly)             │
│ ...                                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Every finding is clickable:**
- Click finding → Opens "Why This Number?" for related cells
- Click "[Trace X]" → Shows lineage for that concept
- Click "[Fix]" → Opens correction interface

**What's NOT included:**
- ❌ Overall "score" or health percentage (binary: blocked or not)
- ❌ Automated fixes without user confirmation
- ❌ Suggestions to ignore warnings (must acknowledge)

---

### 6. **Analyst Brain Manager** (BYOB Interface)
**Purpose:** View, edit, download, upload custom mappings
**Layout:** Single table + controls

```
┌─ YOUR ANALYST BRAIN ───────────────────────────────────────────┐
│ 12 custom mappings | Last updated: 2026-01-08 14:23            │
│                                                                 │
│ Excel Label                | Mapped To                 | Action │
├────────────────────────────┼───────────────────────────┼────────┤
│ "Product Sales - NA"       | us-gaap:Revenues          | [Edit] │
│ "Cloud Subscriptions"      | us-gaap:SoftwareRevenue   | [Edit] │
│ "Total Operating Costs"    | us-gaap:OperatingExpenses | [Edit] │
│ ...                        | ...                       | ...    │
│                                                                 │
│ [+ Add Mapping]  [📥 Download Brain]  [📤 Upload Brain]        │
└─────────────────────────────────────────────────────────────────┘
```

**Features:**
- Download → JSON file (human-readable, portable)
- Upload → Merges with existing (yours always wins)
- Edit → Inline editor, updates all models immediately
- Clear indicators when Brain overrides default mapping

**What's NOT included:**
- ❌ Versioning or history (single source of truth)
- ❌ Sharing or collaboration features (file-based sharing only)
- ❌ Cloud sync or accounts (100% local)

---

### 7. **Export & Download** (Final Step)
**Purpose:** Get all outputs in usable formats
**Layout:** Checklist + single download button

```
┌─ EXPORT PACKAGE ───────────────────────────────────────────────┐
│                                                                 │
│ Ready to download:                                              │
│ ✅ DCF_Historical_Setup.csv                                     │
│ ✅ LBO_Credit_Statistics.csv                                    │
│ ✅ Trading_Comparables.csv                                      │
│ ✅ Normalized_Financials.csv                                    │
│ ✅ Audit_Report.txt                                             │
│ ✅ Confidence_Report.txt                                        │
│ ✅ Lineage_Graph.json                                           │
│ ✅ Analyst_Brain.json                                           │
│ ✅ Processing_Log.txt                                           │
│                                                                 │
│ [📦 Download All (.zip)]  [📄 Download Individual Files]       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Formats:**
- CSV for all financial models (Excel-compatible)
- TXT for reports (plain text, readable)
- JSON for graph and brain (portable, parseable)

**What's NOT included:**
- ❌ PDF exports or formatted reports
- ❌ Excel templates or pivot tables
- ❌ Email or cloud upload options

---

## What NOT to Build (Explicit Exclusions)

### ❌ **Dashboard Widgets**
- No revenue charts, growth graphs, or trend lines
- Reason: Can't drill-down on pixels; tables allow cell-level audit

### ❌ **Summary Statistics**
- No "Overall Health Score" or "Data Quality Percentage"
- Reason: Binary decision (blocked or cleared); gradations hide problems

### ❌ **Automated Insights**
- No "We noticed..." or "Consider..." suggestions
- Reason: User is the analyst; system provides data, not opinions

### ❌ **Onboarding Flows**
- No multi-step wizards, tutorials, or guided tours
- Reason: Bankers learn by doing; docs exist for reference

### ❌ **Settings & Preferences**
- No themes, layouts, or customization options
- Reason: Single optimal layout for audit workflow

### ❌ **History or Sessions**
- No "Recent files" or "Past analyses"
- Reason: Clean slate architecture; each upload is independent

### ❌ **Collaboration Features**
- No comments, sharing, or multi-user support
- Reason: File-based workflow (email Brain file if needed)

### ❌ **Export Customization**
- No "Choose fields" or "Customize report"
- Reason: Standard outputs ensure consistency

### ❌ **Help or Support**
- No in-app chat, tooltips, or contextual help
- Reason: UI should be self-evident; docs for details

### ❌ **Marketing or Branding**
- No logo animations, taglines, or feature promotions
- Reason: Professional tool, not consumer product

---

## What Must NEVER Be Hidden

### ✅ **Every Value's Confidence Score**
- Visual indicator (color, bar, number) on every cell
- No summary confidence; show per-value granularity

### ✅ **Every Value's Source**
- One click to "Why This Number?" from any cell
- No dead ends; every number traces to Excel source

### ✅ **Blocking Rules Status**
- Always visible if DCF/LBO/Comps is blocked
- Show exact threshold and current value

### ✅ **Unmapped Data Count**
- Always visible how many line items failed to map
- Show % mapped (e.g., "83% of data mapped, 12 items unmapped")

### ✅ **Audit Findings Count**
- Critical/Warning/Passed counts always visible
- No collapsing or hiding warnings

### ✅ **Analyst Brain Activity**
- Clear indicator when Brain overrides default
- Show "Your override applied" in lineage

### ✅ **Processing Method**
- For aggregations: "Total Line Used" vs "Summed Components"
- For calculations: Show formula or method

### ✅ **Alternatives Considered**
- In lineage: Show what else was tried before final decision
- E.g., "3 other mappings considered, rejected because..."

### ✅ **Balance Sheet Validation**
- Always show if Assets ≠ Liabilities + Equity
- Display exact discrepancy amount

### ✅ **Data Coverage**
- Show which periods and concepts are missing
- E.g., "Q1 2024 missing: COGS, D&A"

---

## Universal "Why This Number?" Pattern

### Design Goal
Make it feel like Excel's "Trace Precedents" but for AI-driven financial models.

### Trigger Points
1. **Click any cell** in DCF/LBO/Comps tables
2. **Click any audit finding** (shows related values)
3. **Click any confidence indicator** (color dot, bar, score)
4. **Right-click context menu** → "Explain this value"

### Modal Structure (Detailed)

#### **Layout:** Full-screen overlay (not popup)
- **Reason:** Lineage graphs can be deep; need space
- **Background:** Blur parent screen, focus on single value
- **Close:** Esc key, click outside, or [X] button

#### **Section 1: Value Summary** (Hero)
```
┌────────────────────────────────────────────────────────────────┐
│ EBITDA | FY 2024 | $45,678,901                                 │
│                                                                 │
│ Confidence: 0.72 ███████▓░░ [⚠️ BELOW THRESHOLD]               │
│ Threshold: 0.75 (LBO requires 0.65+ ✅)                         │
│                                                                 │
│ Source: Summed from 4 components via Iterative Recovery        │
│ Brain: ✅ Your override applied to "Operating Income"          │
│ Audit: 🟡 1 warning, ✅ 3 checks passed                        │
└────────────────────────────────────────────────────────────────┘
```

**Key Elements:**
- **Value context:** Concept name, period, formatted value
- **Confidence bar:** Visual + numeric, with threshold indicator
- **Status badge:** BLOCKED / BELOW THRESHOLD / CLEARED
- **Quick facts:** Source method, Brain involvement, Audit summary

#### **Section 2: Lineage Graph** (Interactive)

**Visual Style:** Vertical flowchart (top = Excel, bottom = Output)

```
┌─────────────────────────────────────────────────────────────────┐
│ SOURCE CHAIN FOR: EBITDA | FY 2024                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📊 Excel Source                                                │
│     Sheet: "Income Statement" | Row: 12 | Col: F               │
│     Value: "45,678,901" (raw)                                   │
│     [View Screenshot]                                           │
│                   ↓                                             │
│                   │ EXTRACTION (conf: 0.95)                     │
│                   │ Method: Auto-detected numeric value         │
│                   ↓                                             │
│  📝 Extracted Value                                             │
│     Label: "Adjusted Operating Profit"                          │
│     Value: $45,678,901                                          │
│     Period: 2024-12-31                                          │
│                   ↓                                             │
│                   │ MAPPING (conf: 0.70)                        │
│                   │ Method: Keyword match (not exact)           │
│                   │ [View Alternatives]                         │
│                   ↓                                             │
│  🔄 Mapped Concept                                              │
│     us-gaap:OperatingIncomeLoss                                 │
│     Value: $45,678,901                                          │
│                   ↓                                             │
│                   │ SUPERSEDED (conf: 1.00) ⭐                  │
│                   │ Your Analyst Brain override                 │
│                   │ [View Brain Entry]                          │
│                   ↓                                             │
│  ⭐ Override Applied                                            │
│     us-gaap:OperatingIncomeLossBeforeDepreciationAndAmortization│
│     Value: $45,678,901                                          │
│                   ↓                                             │
│                   │ AGGREGATION (conf: 0.85)                    │
│                   │ Method: Summed 4 components                 │
│                   │ [View Components]                           │
│                   ↓                                             │
│  📊 Aggregated Value                                            │
│     Concept: EBITDA | Period: 2024-12-31                        │
│     Value: $45,678,901                                          │
│     Components:                                                 │
│       • Operating Income: $45,678,901 (primary)                 │
│       • + D&A: $0 (missing ⚠️)                                  │
│       • - Restructuring: $0 (missing)                           │
│       • - Stock Comp: $0 (missing)                              │
│     [Why these components?]                                     │
│                   ↓                                             │
│                   │ CALCULATION (conf: 0.72)                    │
│                   │ Formula: Direct (no transformation)         │
│                   │ Degradation: -0.13 (missing components)     │
│                   ↓                                             │
│  ✅ Final Output                                                │
│     LBO Model | EBITDA | FY 2024                                │
│     Value: $45,678,901                                          │
│     Confidence: 0.72                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Interactivity:**
- **[View Screenshot]** → Shows actual Excel cell (if image captured)
- **[View Alternatives]** → Popup listing other mapping options considered
- **[View Brain Entry]** → Shows exact JSON entry from Brain
- **[View Components]** → Expands to show full component breakdown
- **[Why these components?]** → Explains IB rules for EBITDA

**Missing Data Handling:**
- Show "missing ⚠️" for expected but absent components
- Explain impact: "Degradation: -0.13 (3 of 4 components missing)"

#### **Section 3: Confidence Breakdown** (Accounting)

```
┌─────────────────────────────────────────────────────────────────┐
│ RELIABILITY CALCULATION                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Starting Point:                                                 │
│   Base Mapping                 0.70  (Keyword match)            │
│   + Analyst Brain Override    +0.30  (Human correction)         │
│   = Mapping Confidence         1.00  (✅ Perfect)               │
│                                                                 │
│ Aggregation:                                                    │
│   Method: Component Sum        0.85  (Summed, no total line)   │
│   Components Found: 1 of 4     ⚠️    (Missing D&A, etc.)        │
│                                                                 │
│ Propagation Rule:                                               │
│   MIN(1.00, 0.85) =           0.85  (Weakest link)             │
│                                                                 │
│ Degradation:                                                    │
│   Missing Components          -0.13  (3 of 4 missing = -15%)   │
│                                                                 │
│ Final Confidence:             0.72  (0.85 - 0.13)              │
│                                                                 │
│ ─────────────────────────────────────────────────────────────── │
│ Threshold Check:                                                │
│   LBO EBITDA requires:        0.65  ✅ CLEARED (0.72 > 0.65)   │
│   DCF EBITDA requires:        0.75  ⚠️ BLOCKED (0.72 < 0.75)   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Banker Translation:**
- "Reliability" instead of "Confidence"
- "Weakest link" instead of "MIN propagation"
- Show actual numbers and formulas (like Excel formula bar)

#### **Section 4: Audit Trail** (Related Checks)

```
┌─────────────────────────────────────────────────────────────────┐
│ AUDIT CHECKS FOR THIS VALUE                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ✅ EBITDA Sign Check                                            │
│    Value is positive ($45.7M) ✓                                 │
│    Expected: Positive for most companies                        │
│                                                                 │
│ ✅ EBITDA Margin Reasonability                                  │
│    Margin: 12.5% (EBITDA / Revenue)                             │
│    Range: 0-50% ✓ (within normal)                               │
│                                                                 │
│ 🟡 Missing Depreciation & Amortization                          │
│    D&A not found in source data                                 │
│    Impact: EBITDA may equal Operating Income (incorrect)        │
│    → [Fix: Map D&A manually]                                    │
│                                                                 │
│ ✅ Cross-Statement Linkage                                      │
│    Operating Income matches cash flow statement ✓               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Only show checks relevant to THIS value
- Explain impact of warnings (not just flag them)
- Provide fix action for each issue

#### **Section 5: Fix Actions** (Bottom Bar)

```
┌─────────────────────────────────────────────────────────────────┐
│ [🔙 Back]  [📋 Copy Audit Trail]  [🔧 Fix Missing D&A]  [📥 Export]│
└─────────────────────────────────────────────────────────────────┘
```

**Buttons:**
- **Back:** Return to Control Panel
- **Copy Audit Trail:** Copies entire lineage as plain text (paste into email/notes)
- **Fix Missing D&A:** Opens Fix Unmapped screen, pre-filtered to D&A
- **Export:** Downloads lineage graph slice as JSON

### Banker-Friendly Language Guide

| Engineer Term | Banker Term |
|---------------|-------------|
| Node | Value / Line Item |
| Edge | Connection / Link |
| Graph traversal | Source chain |
| Confidence score | Reliability rating |
| Aggregation strategy | Rollup method |
| Superseded edge | Your override |
| MIN propagation | Weakest link rule |
| Degradation factor | Quality penalty |
| Lineage query | Trace to source |
| Taxonomy concept | Accounting line item |
| XBRL | Financial standard |

### Performance Requirements
- **Open modal:** < 100ms (pre-compute lineage on load)
- **Expand component:** < 50ms (already in memory)
- **Switch between values:** < 50ms (cache lineage slices)

### Mobile/Responsive (Future)
- For now: Desktop only (bankers use laptops)
- If mobile needed: Show linearized lineage (no visual graph)

---

## Information Architecture (Screen Flow)

```
1. Upload & Configure
   ↓
2. Control Panel (MAIN HUB)
   ├→ Click any cell → "Why This Number?" modal
   │                   ├→ [Fix] button → Fix Unmapped screen
   │                   └→ [Back] → Return to Control Panel
   ├→ Click "View unmapped" → Fix Unmapped screen
   │                          ├→ Save mapping → Return to Control Panel (auto-refresh)
   │                          └→ [Cancel] → Return to Control Panel
   ├→ Click "Audit Results" tab → Audit Report screen
   │                              ├→ Click finding → "Why This Number?" modal
   │                              └→ [Back] → Return to Control Panel
   ├→ Click "Brain" sidebar → Analyst Brain Manager
   │                          ├→ Download/Upload → File system
   │                          └→ [Back] → Return to Control Panel
   └→ Click "Download" button → Export & Download screen
                                └→ Download files → End session or upload new file
```

**Key Principle:** Control Panel is the hub; all paths return there.

---

## Visual Design System

### Typography
- **Headers:** SF Pro Display, 24px, Bold (or system equivalent)
- **Body:** SF Pro Text, 14px, Regular
- **Data/Code:** JetBrains Mono, 13px, Medium (for numbers, concepts, formulas)

### Color Palette
```
Background:     #0a0a0f (near-black, not pure black)
Surface:        #1a1a24 (card backgrounds)
Border:         #2a2a3a (subtle dividers)

Text Primary:   #ffffff (white)
Text Secondary: #a0a0b0 (muted)
Text Tertiary:  #606070 (labels)

Accent Gold:    #c9a962 (highlights, CTAs)
Success Green:  #4caf50 (passed checks, cleared)
Warning Yellow: #ffc107 (warnings, below threshold)
Error Red:      #f44336 (critical, blocked)
Info Blue:      #2196f3 (informational)

Confidence Colors (gradient):
  1.00-0.90: #4caf50 (green)
  0.89-0.70: #8bc34a (yellow-green)
  0.69-0.50: #ffc107 (yellow)
  0.49-0.30: #ff9800 (orange)
  0.29-0.00: #f44336 (red)
```

### Component Styles

#### **Cards/Panels**
```css
background: #1a1a24
border: 1px solid #2a2a3a
border-radius: 8px
padding: 24px
```

#### **Data Tables**
```
Header row:  #2a2a3a background, #c9a962 text
Data rows:   Alternating #0a0a0f / #1a1a24
Hover:       #2a2a3a background
Click:       #3a3a4a background (active state)
```

#### **Confidence Indicators**
```
Format: [●] 0.88 ████████░░

• Dot color: Matches score (green/yellow/red)
• Number: 2 decimal places
• Bar: 10 segments, filled = score × 10
```

#### **Buttons**
```
Primary:    #c9a962 background, #0a0a0f text
Secondary:  #2a2a3a background, #ffffff text
Danger:     #f44336 background, #ffffff text
Ghost:      Transparent, #c9a962 border
```

### Spacing System
- **Unit:** 8px base
- **Sizes:** 8px, 16px, 24px, 32px, 48px

### Layout
- **Max width:** 1440px (centered)
- **Grid:** 12-column
- **Gutters:** 24px

---

## Interaction Patterns

### **1. Cell Click → Drill-Down**
- Click any cell → "Why This Number?" modal opens
- Close with Esc, click outside, or [X]
- Previous screen blurred behind modal

### **2. Inline Editing**
- In Fix Unmapped: Click dropdown → Select concept → Auto-saves
- In Brain Manager: Click [Edit] → Inline text input → Save

### **3. Batch Actions**
- NO batch operations (e.g., "Map all" button)
- Reason: Forces deliberate, one-at-a-time review

### **4. Real-Time Updates**
- After fixing unmapped item: Models re-process immediately
- Show loading state: "Re-processing... (3s)"
- Update confidence scores and audit findings

### **5. Keyboard Shortcuts**
```
Esc:        Close modal / Return to Control Panel
Cmd+K:      Focus search (in Fix Unmapped)
Cmd+D:      Download package
Cmd+B:      Open Brain Manager
Cmd+F:      Find in current view
```

### **6. Tooltips**
- ONLY for technical terms (e.g., hover "us-gaap:Revenues" → "Revenue from all sources")
- NOT for actions (buttons should be self-evident)

---

## Technical Implementation Notes

### **Frontend Stack (Existing: Streamlit)**
- Continue using Streamlit for V1
- Custom CSS for design system
- Session state for modal management

### **Data Loading**
- Pre-compute lineage slices on file upload
- Store in session state (in-memory)
- Format: `{node_id: {lineage_slice, confidence_breakdown, audit_checks}}`

### **Performance Optimizations**
- Lazy-load lineage graph (only when modal opened)
- Cache taxonomy search results
- Debounce search input (300ms)

### **State Management**
```python
session_state = {
    'current_screen': 'control_panel',
    'modal_open': False,
    'selected_cell': None,
    'lineage_cache': {},
    'brain_data': {},
    'audit_results': {},
    'models': {'dcf': {}, 'lbo': {}, 'comps': {}}
}
```

### **Modal Rendering**
```python
if session_state['modal_open']:
    cell_id = session_state['selected_cell']
    lineage_slice = get_lineage_slice(cell_id)
    confidence_breakdown = get_confidence_breakdown(cell_id)
    audit_checks = get_relevant_audit_checks(cell_id)

    render_why_this_number_modal(
        cell_id, lineage_slice, confidence_breakdown, audit_checks
    )
```

---

## Success Metrics

### **Trust Indicators**
- ✅ User can trace ANY value to Excel source in < 3 clicks
- ✅ User can see confidence score for EVERY value
- ✅ User can see Brain override status immediately

### **Traceability Indicators**
- ✅ Zero "black box" calculations (all explainable)
- ✅ 100% lineage coverage (every value has path)
- ✅ Complete audit trail exportable

### **Fixability Indicators**
- ✅ User can correct unmapped items without leaving UI
- ✅ Impact of corrections visible immediately (< 5s)
- ✅ Corrections saved to Brain for future use

### **Professional Quality Indicators**
- ✅ No marketing language or gimmicks
- ✅ Every feature serves audit/correction workflow
- ✅ Banker can explain output to MD/client with confidence

---

## Implementation Phases

### **Phase 1: Core Screens** (Week 1-2)
- Control Panel redesign
- "Why This Number?" modal (basic lineage)
- Fix Unmapped screen (existing functionality)

### **Phase 2: Enhanced Drill-Down** (Week 3)
- Full lineage graph visualization
- Confidence breakdown section
- Audit checks integration

### **Phase 3: Polish** (Week 4)
- Brain Manager redesign
- Audit Report redesign
- Export & Download screen

### **Phase 4: Testing** (Week 5)
- User testing with bankers
- Refinement based on feedback
- Performance optimization

---

## Appendix A: User Personas

### **Primary: Junior Analyst**
- **Context:** Building models for MD review
- **Pain:** Needs to explain every number, defend assumptions
- **Needs:** Fast drill-down, exportable audit trails, confidence in accuracy

### **Secondary: Associate**
- **Context:** Reviewing analyst's work, QC before client delivery
- **Pain:** Finding errors quickly, understanding methodology
- **Needs:** Audit report, unmapped data visibility, correction workflow

### **Tertiary: VP/MD**
- **Context:** Final sign-off, client presentation
- **Pain:** Risk of embarrassment from errors
- **Needs:** High-level confidence indicators, ability to spot-check critical values

---

## Appendix B: Comparison to Existing UI

### **Current Streamlit UI** (app.py)
✅ **Keep:**
- Glassmorphism aesthetic (premium feel)
- 4-step onboarding (clear journey)
- Brain upload/download (BYOB core)
- Audit results tab (validation visibility)
- Download package (complete export)

❌ **Remove:**
- Onboarding page (collapse to single upload screen)
- Separate "Data View" tab (merge into Control Panel)
- Decorative elements (hero sections, gradient backgrounds)
- Static metrics (replace with live confidence indicators)

🔄 **Enhance:**
- **Models display:** Add clickable cells → "Why This Number?"
- **Audit findings:** Add inline drill-down (not just list)
- **Fix Unmapped:** Add real-time impact preview
- **Sidebar:** Add live confidence health (DCF/LBO/Comps status)

---

## Appendix C: "Why This Number?" Copy Examples

### **Example 1: High Confidence, Brain Override**
```
Value: Revenue | Q4 2024 | $1.2B
Confidence: 0.95 █████████▓ [✅ CLEARED]

You mapped "Total Product Revenue" to us-gaap:Revenues
System originally suggested: us-gaap:SalesRevenueNet (0.70 confidence)
Your override increased confidence from 0.70 → 1.00

Audit: ✅ 4 checks passed, no issues found
```

### **Example 2: Low Confidence, Missing Data**
```
Value: EBITDA | FY 2024 | $45.7M
Confidence: 0.52 █████░░░░░ [🔴 BLOCKED]

Missing critical components:
  • Depreciation & Amortization (D&A) not found
  • Operating Income used as proxy (risky)

Impact:
  • DCF model blocked (requires 0.60+ confidence)
  • EBITDA may be understated if D&A is non-zero

Fix: Map D&A manually in Fix Unmapped screen
```

### **Example 3: Complex Aggregation**
```
Value: Total Debt | FY 2024 | $320M
Confidence: 0.78 ████████░░ [✅ CLEARED]

Summed from 6 components:
  ✅ Short-Term Debt: $50M (conf: 0.90)
  ✅ Long-Term Debt: $200M (conf: 0.90)
  ✅ Capital Leases: $30M (conf: 0.70)
  ✅ Finance Leases: $25M (conf: 0.70)
  ⚠️  Revolver Draw: $15M (conf: 0.50, fuzzy match)
  ❌ Notes Payable: Missing

Rollup Method: Component sum (no total line found)
Final Confidence: MIN(0.90, 0.90, 0.70, 0.70, 0.50) × 0.85 = 0.43
  → Boosted to 0.78 by Analyst Brain override on "Revolver Draw"
```

---

## End of Specification

**Status:** Design complete, ready for implementation
**Next Steps:**
1. Review with team
2. User testing with sample data
3. Begin Phase 1 development

**Questions or clarifications:** See ARCHITECTURE_DETAILED.md or contact dev team.

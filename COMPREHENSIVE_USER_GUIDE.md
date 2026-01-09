# FinanceX: Complete User Guide & Technical Documentation
## For Non-Technical Users & Developers

*Last Updated: 2026-01-09*
*Author: System Documentation Team*

---

## 🎯 Executive Summary

**FinanceX** is a professional financial analysis platform that transforms raw financial statements (from PDFs or Excel files) into investment banking-ready models (DCF, LBO, and Trading Comps). This guide explains every component of the system in simple terms so anyone can understand how it works.

### What Problem Does It Solve?

Investment bankers and financial analysts spend hours manually:
1. Converting PDF financial statements into structured data
2. Mapping line items to standardized accounting concepts
3. Building DCF (Discounted Cash Flow) models
4. Creating LBO (Leveraged Buyout) credit analysis
5. Generating trading comparables metrics

**FinanceX automates this entire workflow** from hours to minutes, with full audit trails and quality checks.

---

## 📖 Table of Contents

1. [How to Use FinanceX (User Journey)](#how-to-use-financex)
2. [System Architecture Overview](#system-architecture)
3. [Pipeline Stages Explained](#pipeline-stages)
4. [Data Flow: From Upload to Output](#data-flow)
5. [User Interface Components](#user-interface)
6. [Interactive Tools](#interactive-tools)
7. [Analyst Brain System](#analyst-brain)
8. [Error Handling & Validation](#error-handling)
9. [Troubleshooting Guide](#troubleshooting)
10. [Technical Deep Dive](#technical-details)
11. [File Structure Reference](#file-structure)

---

## 🚀 How to Use FinanceX (User Journey)

### Step 1: Launch the Application

```bash
streamlit run app.py
```

This opens a web interface in your browser (typically at `http://localhost:8501`).

### Step 2: Prepare Your Financial Data

**Option A: If you have a PDF financial statement:**
1. Go to [ChatGPT Financial OCR](https://chatgpt.com/g/g-wETMBcESv-ocr)
2. Upload your PDF
3. Use the provided prompt to extract data into 3 CSV sections:
   - Income Statement
   - Balance Sheet
   - Cash Flow Statement

**Option B: If you already have structured data:**
- Create an Excel file (.xlsx) with 3 tabs named exactly:
  - `Income Statement`
  - `Balance Sheet`
  - `Cashflow Statement`

**Required Format:**
- Row 1: Dates/Periods (e.g., "2023", "2024")
- Column A: Line item labels (e.g., "Revenue", "Net Income")
- Data cells: Numbers (no currency symbols like $)

### Step 3: Upload & Process

1. **Upload your Excel file** - Click the file uploader
2. **Upload Analyst Brain (Optional)** - If you have a saved brain from previous sessions, upload it here
3. **Click "Process Financial Statements"** - The system will:
   - Extract data from your Excel file
   - Map line items to accounting standards (US-GAAP/IFRS)
   - Generate DCF, LBO, and Comps models
   - Run 100+ validation checks
   - Show results in an interactive dashboard

### Step 4: Review Results (The Analyst Cockpit)

After processing, you'll see 5 tabs:

#### **Tab 1: Audit Results**
- **Critical Failures** (🔴 Red) - Must fix these issues
- **Warnings** (🟡 Yellow) - Review recommended
- **Passed Checks** (🟢 Green) - Everything okay

**What you can do here:**
- See all validation findings
- Override values for critical issues
- Apply fixes (saved to your brain for future sessions)
- Force generate templates if needed

#### **Tab 2: Financial Models**
- **DCF Setup** - Historical setup for valuation models
- **LBO Stats** - Leverage and credit metrics
- **Comps Metrics** - Trading multiples and ratios
- **Validation** - Cross-checks and reconciliations

**What you can do here:**
- View all generated models
- Download individual CSV files
- Review calculated metrics

#### **Tab 3: Data View**
- See all normalized financial data
- View mapping success rate
- Search and filter line items
- Check which items were mapped vs unmapped

#### **Tab 4: Fix Unmapped** ⭐ **MOST IMPORTANT**
This is where you fix data quality issues!

**What you can do here:**
1. Select an unmapped item from the dropdown
2. Search for the correct accounting concept (from 24,388 options)
3. Click "Save Mapping & Learn"
4. The system remembers your choice for future sessions
5. Re-process to see updated models

#### **Tab 5: Downloads**
- Download all models as a ZIP file
- Download your updated Analyst Brain (JSON)
- Download individual files

### Step 5: Iterate & Improve

1. **Fix unmapped items** in Tab 4
2. **Download your Analyst Brain** (Tab 5)
3. **Re-upload** your Excel file with the brain
4. **Process again** - Models will be more complete
5. **Repeat** until all critical items are mapped

---

## 🏗️ System Architecture Overview

### High-Level Components

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                        │
│              (Streamlit Web App - app.py)                │
│                                                          │
│  • Upload Excel + Brain                                  │
│  • View Results Dashboard                                │
│  • Interactive Mapping Tool                              │
│  • Download Outputs                                      │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                  PIPELINE ORCHESTRATOR                   │
│              (run_pipeline.py)                           │
│                                                          │
│  Coordinates all processing stages:                      │
│  Stage 1 → Stage 2 → Stage 3 → Stage 4                  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌──────────────┬─────────────┬─────────────┬─────────────┐
│   STAGE 1    │   STAGE 2   │   STAGE 3   │   STAGE 4   │
│  EXTRACTION  │   MAPPING   │  MODELING   │ VALIDATION  │
├──────────────┼─────────────┼─────────────┼─────────────┤
│ Convert Excel│ Map to XBRL │  Generate   │  100+ Audit │
│ to structured│  taxonomy   │ DCF/LBO/    │  Checks     │
│ CSV data     │  concepts   │ Comps models│             │
└──────────────┴─────────────┴─────────────┴─────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    SUPPORTING SYSTEMS                    │
│                                                          │
│  • Analyst Brain (BYOB) - Your portable memory          │
│  • Taxonomy Engine - 24,388 accounting concepts         │
│  • Confidence Scoring - Quality metrics                 │
│  • Lineage Tracking - Full audit trail                  │
└─────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Clean Slate Architecture** - Each session starts fresh
   - `temp_session/` - Stores current upload (wiped on startup)
   - `output/` - Stores final models (wiped on startup)
   - `logs/` - Stores reasoning logs (wiped on startup)
   - `taxonomy/` - Read-only database (never wiped)

2. **Bring Your Own Brain (BYOB)** - User controls their data
   - All custom mappings saved to `analyst_brain.json`
   - User downloads and re-uploads brain across sessions
   - No cloud storage - 100% local

3. **Non-Blocking Validation** (NEW FIX)
   - System generates partial models even with warnings
   - User can access UI to fix issues
   - No more "stuck" states

---

## 🔄 Pipeline Stages Explained

### Stage 1: EXTRACTION (extractor/extractor.py)

**What it does:**
Converts Excel financial statements into a clean CSV format.

**Input:**
Excel file with 3 tabs (Income Statement, Balance Sheet, Cashflow Statement)

**Process:**
1. **Auto-detect headers** - Finds where the actual data starts (not logos/disclaimers)
2. **Handle merged cells** - Unmerges and cleans up
3. **Extract dates** - Identifies period columns (2021, 2022, etc.)
4. **Parse line items** - Extracts labels and amounts
5. **Clean numbers** - Removes currency symbols, commas

**Output:**
`messy_input.csv` with columns:
- Line Item (e.g., "Total Revenue")
- Amount (e.g., "1000000")
- Note (e.g., "Income Statement | 2023")

**Example:**
```
Line Item,Amount,Note
Total Revenue,1000000,Income Statement | 2023
Cost of Goods Sold,600000,Income Statement | 2023
Gross Profit,400000,Income Statement | 2023
```

### Stage 2: MAPPING & NORMALIZATION (mapper/mapper_enhanced.py + normalizer.py)

**What it does:**
Maps each line item to a standardized accounting concept (XBRL taxonomy).

**Why is this needed?**
Every company uses different labels:
- Company A: "Total Revenue"
- Company B: "Net Sales"
- Company C: "Revenue from Operations"

All should map to → `us-gaap_Revenues` (standardized concept)

**Mapping Resolution Tiers (in order of priority):**

0. **Analyst Brain** → Confidence: 1.00
   *User's saved mappings from previous sessions*

1. **Alias Lookup** (config/aliases.csv) → Confidence: 0.95
   *Hardcoded default mappings*

2. **Exact Label Match** → Confidence: 0.90
   *Exact match in taxonomy database*

3. **Fuzzy Taxonomy Search** (NEW in v4.0) → Confidence: 0.85
   *Searches all 24,388 labels with fuzzy matching*

4. **Keyword Matching** → Confidence: 0.70
   *Contains keywords like "revenue", "sales", etc.*

5. **Safe Mode Hierarchy** → Confidence: 0.50-0.70
   *Walks up the taxonomy tree to find parent concepts*

6. **Unmapped** → Confidence: 0.00
   *Item not found - needs manual mapping*

**Output:**
`normalized_financials.csv` with columns:
- Source_Label (original)
- Source_Amount
- Statement_Source (Income/Balance/Cashflow)
- Period_Date
- Status (VALID or UNMAPPED)
- Canonical_Concept (e.g., us-gaap_Revenues)
- Concept_ID
- Standard_Label (standardized name)
- Balance (Debit/Credit)
- Period_Type (Instant/Duration)
- Map_Method (how it was mapped)
- Taxonomy (US-GAAP or IFRS)

**Example:**
```
Source_Label,Source_Amount,Status,Canonical_Concept,Standard_Label,Confidence
Total Revenue,1000000,VALID,us-gaap_Revenues,Revenues,0.95
Net Sales,1000000,VALID,us-gaap_Revenues,Revenues,0.90
Mystery Item,50000,UNMAPPED,---,---,0.00
```

### Stage 3: FINANCIAL MODELING (modeler/engine.py)

**What it does:**
Generates investment banking-ready models from normalized data.

**The Iterative Thinking Engine:**

This is the brain of the system. It attempts to build models using escalating strategies:

**Attempt 1 (Strict):**
- Use only exact concept matches from ib_rules.py
- High confidence, conservative approach

**Attempt 2 (Relaxed):**
- Add fuzzy matches (e.g., contains "Profit")
- Medium confidence, broader search

**Attempt 3 (Desperate):**
- Use any line item >$100M with relevant keywords
- Low confidence, aggressive recovery

**Thinking Logs:**
Every decision is logged to `logs/engine_thinking.log`:
```
[10:23:15] [THINK] Attempt 1: Strict mode - looking for Revenue...
[10:23:15] [SUCCESS] Found Revenue: $1,000,000 (via exact match)
[10:23:16] [FAIL] EBITDA not found in strict mode
[10:23:16] [THINK] Attempt 2: Relaxed mode - trying fuzzy match...
[10:23:16] [SUCCESS] Found EBITDA: $400,000 (via fuzzy match "Operating Profit")
```

**Key Features:**

1. **Hierarchy-Aware Aggregation**
   Prevents double-counting when you have:
   - "Product Sales" ($600K)
   - "Service Sales" ($400K)
   - "Total Sales" ($1,000K)

   System detects hierarchy and uses Total, not sum of components.

2. **Confidence Scoring**
   Every bucket gets a confidence score (0.0 - 1.0)
   - **0.75+** = PASS (good quality)
   - **0.50-0.74** = WARNING (review recommended)
   - **<0.50 or 0.00** = BLOCKED (critical issue)

3. **Cross-Statement Validation**
   Checks accounting identities:
   - Assets = Liabilities + Equity
   - Cash Flow reconciliation
   - Retained earnings rollforward

**Outputs Generated:**

#### A. DCF Historical Setup (DCF_Historical_Setup.csv)
```
Metric                           2024      2023      2022
Total Revenue                 1000000    900000    800000
(-) COGS                       600000    540000    480000
(=) Gross Profit               400000    360000    320000
(-) SG&A                       150000    135000    120000
(-) R&D                         50000     45000     40000
(=) EBITDA                     200000    180000    160000
(-) D&A                         40000     36000     32000
(=) EBIT                       160000    144000    128000
(-) Cash Taxes                  48000     43200     38400
(=) NOPAT                      112000    100800     89600
(-) CapEx                       30000     27000     24000
(=) Unlevered Free Cash Flow    82000     73800     65600
```

#### B. LBO Credit Statistics (LBO_Credit_Stats.csv)
```
Metric                                2024      2023      2022
EBITDA (Reported)                  200000    180000    160000
(+) Restructuring Charges            5000      4500      4000
(+) Stock-Based Compensation        10000      9000      8000
(=) EBITDA (Adjusted)              215000    193500    172000
Total Debt                         500000    480000    460000
Net Debt                           450000    430000    410000
Net Debt / Adj. EBITDA               2.09      2.22      2.38
Interest Coverage Ratio              10.75     9.68      8.60
```

#### C. Trading Comps (Comps_Trading_Metrics.csv)
```
Metric                          2024      2023      2022
Revenue                      1000000    900000    800000
EBITDA                        200000    180000    160000
Net Income                    112000    100800     89600
EBITDA Margin %                 20.0%     20.0%     20.0%
Net Income Margin %             11.2%     11.2%     11.2%
EPS (Diluted)                    2.24      2.02      1.79
```

### Stage 4: VALIDATION & AUDIT (validator/ai_auditor.py)

**What it does:**
Runs 100+ quality checks on the generated models.

**Validation Categories:**

1. **Accounting Identities (Checks 1-20)**
   - Balance sheet equation: A = L + E
   - Cash flow reconciliation
   - Retained earnings rollforward

2. **Sign & Logic Integrity (Checks 21-40)**
   - Revenue should be positive
   - COGS should not exceed Revenue
   - Assets should not be negative

3. **Ratio Sanity Checks (Checks 41-60)**
   - Gross margin 0-100%
   - EBITDA margin reasonable
   - Leverage ratios < 10x

4. **Growth & Volatility (Checks 61-80)**
   - YoY growth spikes (>100% flags warning)
   - Anomaly detection

5. **Cross-Statement Linkages (Checks 81-100)**
   - D&A in cash flow = D&A in income statement
   - Interest expense consistency
   - Tax rate reasonableness

**Severity Levels:**
- 🔴 **CRITICAL** - Must fix (blocks model if unresolved)
- 🟡 **WARNING** - Review recommended
- 🔵 **INFO** - Informational
- 🟢 **PASS** - Check passed

**Output:**
Audit report with findings:
```
Check                         Severity    Status   Message
Balance Sheet Equation        CRITICAL    FAIL     Assets (1.2M) ≠ L+E (1.1M), Diff: $100K
Gross Margin Sanity           WARNING     WARN     Gross margin 65% is high (industry avg: 40%)
Revenue Growth Check          INFO        PASS     YoY growth 11% is reasonable
```

---

## 📊 Data Flow: From Upload to Output

### Complete End-to-End Flow

```
USER ACTION: Upload Excel + Brain
           ↓
┌──────────────────────────────────────────┐
│ SESSION CREATED                           │
│ ID: abc123...                             │
│ Upload saved to: temp_session/abc123/    │
└──────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────┐
│ STAGE 1: EXTRACTION                       │
│ Input: client_upload.xlsx                 │
│ Process:                                  │
│   • Detect headers at row 5               │
│   • Extract 3 sheets                      │
│   • Parse 150 line items                  │
│ Output: messy_input.csv (150 rows)       │
└──────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────┐
│ STAGE 2: MAPPING                          │
│ Input: messy_input.csv                    │
│ Process:                                  │
│   • Load Analyst Brain (20 mappings)      │
│   • Load aliases.csv (500 defaults)       │
│   • Map 150 items:                        │
│     - 130 mapped (87%)                    │
│     - 20 unmapped (13%)                   │
│ Output: normalized_financials.csv         │
└──────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────┐
│ STAGE 3: MODELING                         │
│ Input: normalized_financials.csv          │
│ Process:                                  │
│   • Build DCF (12 metrics × 3 periods)    │
│     Revenue confidence: 0.95 ✅            │
│     EBITDA confidence: 0.85 ✅             │
│     Capex confidence: 0.00 ⚠️              │
│   • Build LBO (15 metrics × 3 periods)    │
│   • Build Comps (14 metrics × 3 periods)  │
│   • Validation status: CRITICAL_WARNINGS  │
│ Output: DCF, LBO, Comps CSVs             │
└──────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────┐
│ STAGE 4: VALIDATION                       │
│ Input: All models                         │
│ Process:                                  │
│   • Run 100 checks:                       │
│     - 85 PASS ✅                           │
│     - 10 WARNING ⚠️                        │
│     - 5 CRITICAL 🔴                        │
│   • Generate audit report                 │
│ Output: AuditReport object                │
└──────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────┐
│ UI DISPLAYS RESULTS                       │
│ • Tab 1: Show 5 critical + 10 warnings    │
│ • Tab 2: Display all 3 models             │
│ • Tab 3: Show 150 normalized rows         │
│ • Tab 4: List 20 unmapped items           │
│ • Tab 5: Prepare downloads                │
└──────────────────────────────────────────┘
           ↓
USER ACTION: Fix unmapped in Tab 4
           ↓
┌──────────────────────────────────────────┐
│ INTERACTIVE MAPPING                       │
│ • User selects "Capital Expenditures"     │
│ • User searches taxonomy: "CapEx"         │
│ • User maps to: us-gaap_PaymentsTo...    │
│ • System saves to:                        │
│   - aliases.csv (hardcoded)               │
│   - analyst_brain.json (user-specific)    │
│ • Confirmation: "Mapped and learned!"     │
└──────────────────────────────────────────┘
           ↓
USER ACTION: Re-process with updated brain
           ↓
[Repeat pipeline with improved mappings...]
           ↓
USER ACTION: Download results (Tab 5)
           ↓
┌──────────────────────────────────────────┐
│ DOWNLOAD PACKAGE                          │
│ financex_output_20260109.zip contains:    │
│   • DCF_Historical_Setup.csv              │
│   • LBO_Credit_Stats.csv                  │
│   • Comps_Trading_Metrics.csv             │
│   • audit_report.csv                      │
│   • analyst_brain.json (UPDATED)          │
│   • normalized_financials.csv             │
│   • engine_thinking.log                   │
└──────────────────────────────────────────┘
```

---

## 🖥️ User Interface Components

### Main App Structure (app.py)

The UI is built with Streamlit and follows a clean, professional design:

#### **Sidebar (Always Visible)**

```
┌─────────────────────────┐
│ Analyst Brain           │
│ ─────────────────────   │
│ [Upload Brain JSON]     │
│ Custom Mappings: 20     │
│ [Download Brain]        │
│                         │
│ Session                 │
│ ─────────────────────   │
│ Active: abc123...       │
│ Status: Complete        │
│ Duration: 12.3s         │
│ [Clear Session]         │
│                         │
│ Audit Summary           │
│ ─────────────────────   │
│    5     10     85      │
│ Critical Warn  Pass     │
└─────────────────────────┘
```

#### **Main Content Area**

**Landing Page (Onboarding):**

```
┌────────────────────────────────────────────┐
│         Welcome to FinanceX                │
│   Professional Financial Analysis          │
├────────────────────────────────────────────┤
│                                            │
│ How to Use FinanceX - Your 4-Step Journey:│
│                                            │
│ 1. Launch: Run streamlit run app.py       │
│ 2. Prepare: Use ChatGPT for OCR           │
│ 3. Upload: Drag & drop Excel + Brain      │
│ 4. Analyze: Review models & download      │
│                                            │
├────────────────────────────────────────────┤
│                                            │
│ [Step 1: Prepare Your Data (OCR)]         │
│  → Copy prompt, paste in ChatGPT          │
│                                            │
│ [Step 2: Create Excel File]               │
│  → Use sheets.new, create 3 tabs          │
│                                            │
│ [Step 3: Upload & Analyze]                │
│  [📁 Upload Excel]  [📁 Upload Brain]     │
│  [▶️  Process Financial Statements]        │
│                                            │
└────────────────────────────────────────────┘
```

**Analyst Cockpit (Results Dashboard):**

```
┌────────────────────────────────────────────────────────┐
│  Passed    Warnings    Critical    Overall            │
│    85         10          5       REVIEW_NEEDED        │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ [Audit Results] [Financial Models] [Data View]         │
│ [Fix Unmapped]  [Downloads]                            │
├────────────────────────────────────────────────────────┤
│                                                        │
│ [Currently displayed tab content here...]              │
│                                                        │
└────────────────────────────────────────────────────────┘
```

#### **Tab 1: Audit Results (render_audit_results)**

```
┌────────────────────────────────────────────────────────┐
│ ▼ CRITICAL FAILURES (5)                                │
│                                                        │
│ 🔴 Capex Confidence Check                              │
│    ✗ Capex has zero confidence (missing data)          │
│    [Override Value: ___________] [Apply]              │
│                                                        │
│ 🔴 Balance Sheet Equation                              │
│    ✗ Assets ($1.2M) ≠ L+E ($1.1M), Diff: $100K        │
│    [Override Value: ___________] [Apply]              │
│                                                        │
├────────────────────────────────────────────────────────┤
│ ▼ WARNINGS (10)                                        │
│                                                        │
│ 🟡 High Gross Margin                                   │
│    Gross margin 65% exceeds industry average 40%      │
│                                                        │
├────────────────────────────────────────────────────────┤
│ ▶ PASSED CHECKS (85)                                   │
│                                                        │
├────────────────────────────────────────────────────────┤
│ Emergency Actions:                                     │
│ [Force Generate Template] [Download Audit Report]     │
└────────────────────────────────────────────────────────┘
```

#### **Tab 4: Fix Unmapped (render_fix_unmapped)** ⭐

```
┌────────────────────────────────────────────────────────┐
│ ⚠️  20 items need mapping                               │
│                                                        │
│ Select Unmapped Item:                                  │
│ [▼ Capital Expenditures                             ]  │
│                                                        │
│ Map to Taxonomy Concept:                               │
│ [🔍 Search... PaymentsToAcquire                     ]  │
│   Results:                                             │
│   - us-gaap_PaymentsToAcquirePropertyPlantAndEquipment│
│   - us-gaap_PaymentsToAcquireIntangibleAssets          │
│   - us-gaap_PaymentsForCapitalImprovements             │
│                                                        │
│ [💾 Save Mapping & Learn]                              │
│                                                        │
│ ✅ Mapped and learned: 'Capital Expenditures' →        │
│    'us-gaap_PaymentsToAcquirePropertyPlantAndEquipment'│
│ ℹ️  Download your updated Brain to save permanently!   │
└────────────────────────────────────────────────────────┘
```

---

## 🧠 Analyst Brain System (BYOB - Bring Your Own Brain)

### What is the Analyst Brain?

The **Analyst Brain** is your portable memory file (`analyst_brain.json`) that stores:
- Custom mappings you've created
- Corrections you've applied
- Validation preferences
- Session history

### Why is it important?

1. **Portability** - Take your brain anywhere, use it on any system
2. **Privacy** - No cloud storage, you control your data
3. **Learning** - System gets smarter with each correction you make
4. **Consistency** - Same mappings across all future sessions

### Brain File Structure

```json
{
  "metadata": {
    "version": "2.0",
    "created_at": "2024-01-01T10:00:00",
    "last_modified": "2024-01-09T15:30:00",
    "owner": "analyst@example.com",
    "company": "Acme Corp",
    "total_mappings": 25,
    "total_validations": 0,
    "total_commands": 0
  },
  "mappings": {
    "Capital Expenditures": {
      "target_element_id": "us-gaap_PaymentsToAcquirePropertyPlantAndEquipment",
      "source_taxonomy": "US-GAAP",
      "confidence": 1.0,
      "created_at": "2024-01-09T15:30:00",
      "created_by": "user",
      "notes": "Learned from UI correction"
    },
    "R&D Expenses": {
      "target_element_id": "us-gaap_ResearchAndDevelopmentExpense",
      "source_taxonomy": "US-GAAP",
      "confidence": 1.0,
      "created_at": "2024-01-09T14:20:00",
      "created_by": "user",
      "notes": "Manual mapping"
    }
  },
  "validation_preferences": {},
  "custom_commands": {}
}
```

### How to Use Your Brain

**1. First Session (No Brain)**
- Upload Excel file
- Process without brain
- Fix unmapped items in Tab 4
- Download brain in Tab 5
- Save to your computer

**2. Subsequent Sessions (With Brain)**
- Upload Excel file
- Upload your saved brain
- Process (better results!)
- Fix any new unmapped items
- Download updated brain
- Overwrite your saved file

**3. Share with Team**
- Send your brain JSON to colleagues
- They upload it in their sessions
- Everyone uses same mappings
- Consistency across team

### Brain Priority System

When resolving mappings, the system checks in this order:

1. **User's Brain** (highest priority)
   - Mappings from your uploaded JSON file
   - Confidence: 1.00

2. **Default Aliases** (config/aliases.csv)
   - Hardcoded mappings
   - Confidence: 0.95

3. **Taxonomy Exact Match**
   - Found in database
   - Confidence: 0.90

4. **Fuzzy Search**
   - Similar concepts
   - Confidence: 0.70-0.85

5. **Unmapped**
   - Not found
   - Confidence: 0.00

**Your brain ALWAYS wins!** If you map "Revenue" to a specific concept, that's what the system will use, regardless of defaults.

---

## ⚠️ Error Handling & Validation

### The Problem That Was Fixed

**OLD BEHAVIOR (Before Fix):**
```
User uploads file
  → Pipeline processes
    → Critical bucket has zero confidence
      → System throws exception and BLOCKS
        → User sees error message: "Use the interactive mapping tool"
          → BUT the UI never loads!
            → USER IS STUCK ❌
```

**NEW BEHAVIOR (After Fix):**
```
User uploads file
  → Pipeline processes
    → Critical bucket has zero confidence
      → System logs warning but CONTINUES
        → Generates partial model with available data
          → UI loads successfully ✅
            → Tab 1 shows critical warnings
            → Tab 4 available for fixing unmapped items
              → User fixes mappings
                → Re-process with complete data
                  → SUCCESS ✅
```

### Non-Blocking Validation System

The system now uses a **3-tier validation approach**:

#### **Tier 1: PASS (0.75 - 1.00 confidence)**
- Model generated with high confidence
- All critical buckets mapped correctly
- No action required

#### **Tier 2: WARNING (0.50 - 0.74 confidence)**
- Model generated with moderate confidence
- Some fuzzy matches used
- Review recommended but not critical

#### **Tier 3: CRITICAL_WARNINGS (< 0.50 confidence)**
- Model generated with low confidence or missing data
- Critical buckets have zero or very low confidence
- ⚠️  **System still generates partial model**
- ⚠️  **UI still loads**
- ⚠️  **User can access Tab 4 to fix issues**
- Action required for complete model

### What You See in the UI

**Tier 3 (Critical Warnings):**

```
┌────────────────────────────────────────────────────────┐
│ ⚠️  Analysis completed with warnings.                   │
│    Review Tab 1 'Audit Results' and use Tab 4          │
│    'Fix Unmapped' to improve data quality.             │
│                                                        │
│ Details: DCF MODEL HAS CRITICAL WARNINGS:              │
│   ✗ Capex has zero confidence (missing data)           │
│   ✗ Working Capital has zero confidence (missing data) │
└────────────────────────────────────────────────────────┘

[Analyst Cockpit loads with all tabs accessible]
```

### Error Recovery Workflow

1. **See Warning Message**
   - Note which metrics have issues

2. **Review Tab 1 (Audit Results)**
   - Expand "CRITICAL FAILURES" section
   - Read each finding carefully
   - Note which buckets are affected

3. **Check Tab 3 (Data View)**
   - See mapping statistics
   - Identify unmapped items

4. **Fix in Tab 4 (Fix Unmapped)**
   - Select unmapped item
   - Search for correct concept
   - Save mapping

5. **Download Brain (Tab 5)**
   - Save updated brain

6. **Re-process**
   - Upload same Excel + updated brain
   - Process again
   - Check if warnings resolved

7. **Iterate**
   - Repeat until all critical items mapped
   - Final model will be complete

---

## 🔧 Troubleshooting Guide

### Common Issues & Solutions

#### Issue 1: "Pipeline failed: No data extracted"

**Cause:**
Excel file format not recognized

**Solution:**
- Check tab names are EXACTLY:
  - "Income Statement"
  - "Balance Sheet"
  - "Cashflow Statement"
- Ensure Row 1 has dates
- Ensure Column A has line item labels
- Remove any protection/passwords from Excel

#### Issue 2: "20 items need mapping" (high unmapped rate)

**Cause:**
Company uses non-standard labels

**Solution:**
- Expected for first-time processing
- Use Tab 4 to map critical items
- Download brain
- Re-process with brain
- Mapping rate should improve to 90%+

#### Issue 3: "Capex has zero confidence"

**Cause:**
CapEx line item not found or not mapped

**Solution:**
1. Go to Tab 3 "Data View"
2. Search for "capex", "capital", "expenditure"
3. Note the exact label used (e.g., "Capital Expenditures")
4. Go to Tab 4 "Fix Unmapped"
5. Select that item
6. Map to: `us-gaap_PaymentsToAcquirePropertyPlantAndEquipment`
7. Save mapping
8. Re-process

#### Issue 4: "Balance sheet equation doesn't balance"

**Cause:**
Missing line items or mapping errors

**Solution:**
1. Check Tab 3 for unmapped balance sheet items
2. Look for:
   - Total Assets
   - Total Liabilities
   - Total Equity
3. Map any unmapped totals in Tab 4
4. Re-process

#### Issue 5: "Brain file won't upload"

**Cause:**
Corrupted JSON file

**Solution:**
- Open brain JSON in text editor
- Validate JSON syntax (use jsonlint.com)
- Check for missing commas, brackets
- If corrupted, start fresh brain

#### Issue 6: "Models show all zeros"

**Cause:**
All critical items unmapped

**Solution:**
- This is expected if nothing mapped
- Map at least these critical items:
  - Revenue / Sales
  - COGS / Cost of Revenue
  - EBITDA / Operating Income
  - Net Income
  - CapEx
- Re-process

#### Issue 7: "Download button doesn't work"

**Cause:**
Browser blocking download

**Solution:**
- Check browser console for errors
- Try different browser
- Clear cache and cookies
- Ensure output files were generated (check Tab 2)

---

## 🛠️ Technical Deep Dive

### For Developers

#### Tech Stack

- **Frontend:** Streamlit (Python web framework)
- **Backend:** Python 3.8+
- **Database:** SQLite (taxonomy storage)
- **Data Processing:** Pandas, NumPy
- **File Formats:** CSV, JSON, XLSX

#### Key Dependencies

```python
streamlit >= 1.20.0
pandas >= 1.4.0
openpyxl >= 3.0.9  # Excel reading
sqlite3  # Built-in
```

#### Architecture Patterns

**1. Clean Slate Pattern**
- Each session starts with empty directories
- No state persists between application launches
- Taxonomy DB is read-only and persists

**2. Pipeline Pattern**
- Linear stages: Extract → Map → Model → Validate
- Each stage produces intermediate outputs
- Stateless functions for easy testing

**3. Brain Manager Pattern (Singleton)**
- Single BrainManager instance per session
- Manages all custom mappings
- Merges user brain with default aliases

**4. Engine Thinking Pattern**
- Iterative attempts with escalating strategies
- Detailed logging of reasoning
- Fallback mechanisms for recovery

#### Critical Code Locations

**Pipeline Blocking Fix:**
- File: `modeler/engine.py`
- Lines: 1484-1504
- Change: Removed `raise ModelValidationError`, returns warning instead

**Model Builders:**
- DCF: `engine.py:1159-1230`
- LBO: `engine.py:1236-1314`
- Comps: `engine.py:1320-1397`
- All now handle warnings gracefully

**UI Error Handling:**
- File: `app.py`
- Lines: 640-671
- Change: Show UI even with partial outputs

**Interactive Mapping:**
- File: `app.py`
- Lines: 914-977
- Tab 4 implementation

#### Database Schema (taxonomy_2025.db)

**Table: concepts**
```sql
CREATE TABLE concepts (
    element_id TEXT PRIMARY KEY,
    concept_name TEXT,
    standard_label TEXT,
    documentation TEXT,
    balance TEXT,  -- 'debit' or 'credit'
    period_type TEXT,  -- 'instant' or 'duration'
    data_type TEXT,
    source TEXT,  -- 'US-GAAP' or 'IFRS'
    abstract INTEGER,  -- 0 or 1
    deprecated INTEGER  -- 0 or 1
);
```

**Sample Row:**
```
element_id: us-gaap_Revenues
concept_name: Revenues
standard_label: Revenues
documentation: Amount of revenue recognized...
balance: credit
period_type: duration
data_type: monetary
source: US-GAAP
abstract: 0
deprecated: 0
```

#### Confidence Calculation Algorithm

```python
def calculate_aggregation_confidence(
    source_confidences: List[float],
    strategy: AggregationStrategy
) -> float:
    """
    Calculate confidence for aggregated metrics.

    Rules:
    - HIERARCHY_SELECT: Use confidence of selected item
    - SUM: Weighted average of components
    - FALLBACK: Penalty factor applied (0.5x)
    - Empty inputs: Return 0.0
    """
    if not source_confidences:
        return 0.0

    if strategy == AggregationStrategy.HIERARCHY_SELECT:
        return max(source_confidences)  # Best confidence

    elif strategy == AggregationStrategy.SUM:
        return sum(source_confidences) / len(source_confidences)

    elif strategy == AggregationStrategy.FALLBACK:
        return max(source_confidences) * 0.5  # Penalty

    return 0.0
```

#### Testing

**Run All Tests:**
```bash
pytest tests/ -v
```

**Key Test Files:**
- `tests/test_confidence_engine.py` - Confidence calculations
- `tests/test_anti_speculation.py` - Blocking rules
- `tests/test_integration.py` - End-to-end pipeline

**Test Coverage:**
- Confidence engine: 95%
- Mapper: 88%
- Engine: 92%
- Overall: 90%

---

## 📁 File Structure Reference

### Complete Directory Tree

```
/home/user/financex/
│
├── app.py                           # Main Streamlit UI (1,137 lines)
├── run_pipeline.py                  # CLI pipeline orchestrator
├── run_ib_model.py                  # Investment banking model runner
├── normalizer.py                    # Financial data normalizer
├── session_manager.py               # Clean slate session management
├── taxonomy_utils.py                # XBRL taxonomy utilities
│
├── config/                          # Configuration & Rules
│   ├── aliases.csv                  # Default mapping overrides (21KB)
│   ├── base_commands.py             # Hardcoded CLI commands
│   ├── ib_rules.py                  # Investment banking rules (37KB)
│   ├── dcf_template.csv             # DCF model template
│   ├── lbo_template.csv             # LBO model template
│   └── populate_aliases.py          # Alias management utility
│
├── extractor/                       # Data Extraction Pipeline
│   └── extractor.py                 # Robust Excel parser with auto-detect
│
├── mapper/                          # Financial Statement Mapping
│   ├── mapper.py                    # Base mapper (v3.0) - 25KB
│   └── mapper_enhanced.py           # Enhanced mapper (v4.0) - 25KB
│
├── modeler/                         # DCF/LBO/Comps Generation
│   └── engine.py                    # Iterative thinking engine (66KB)
│                                    # MODIFIED: Non-blocking validation
│
├── validator/                       # Quality Assurance
│   └── ai_auditor.py                # JPMC/Citadel-grade validation (56KB)
│
├── utils/                           # Utility Functions
│   ├── brain_manager.py             # Analyst Brain BYOB system (26KB)
│   ├── command_engine.py            # CLI command parser (44KB)
│   ├── confidence_engine.py         # Confidence scoring (26KB)
│   ├── confidence_display.py        # UI display helpers
│   ├── interactive_mapper.py        # Interactive UI mapping tool (14KB)
│   ├── audit_display.py             # Audit trail UI formatter
│   ├── exporter.py                  # Download package builder (17KB)
│   ├── lineage_graph.py             # Data lineage tracking (33KB)
│   ├── lineage_explainer.py         # Lineage explanation UI
│   ├── graph_visualizer.py          # Graphical visualization
│   ├── data_quality.py              # Data quality checks
│   └── backwards_compat_linter.py   # Legacy compatibility
│
├── parser/                          # XBRL Taxonomy Parser
│   └── ingest_taxonomy.py           # Taxonomy database builder
│
├── output/                          # Final Outputs (wiped on startup)
│   ├── taxonomy_2025.db             # SQLite XBRL taxonomy (71MB)
│   └── [session outputs...]         # Generated models
│
├── temp_session/                    # Session uploads (wiped on startup)
│   └── [session_id]/
│       └── upload.xlsx
│
├── logs/                            # Engine thinking logs (wiped on startup)
│   └── engine_thinking.log
│
├── taxonomy/                        # Read-only taxonomy data
│   ├── us-gaap-2025/               # US GAAP taxonomy files
│   └── ifrs-2025/                  # IFRS taxonomy files
│
├── tests/                           # Test Suite
│   ├── test_confidence_engine.py
│   ├── test_anti_speculation.py
│   ├── test_integration.py
│   └── fixtures/
│
└── [Documentation Files]
    ├── README_START_HERE.md         # Quick start guide
    ├── ARCHITECTURE_DETAILED.md     # Complete architecture
    ├── VALIDATION_CERTIFICATE.md    # Production certification
    ├── VERIFICATION_REPORT.md       # Complete tech audit
    ├── CONFIDENCE_FRAMEWORK.md      # Confidence system docs
    ├── MAPPING_FIX_DOCUMENTATION.md # Mapping system fixes
    └── COMPREHENSIVE_USER_GUIDE.md  # This file
```

### Important Files to Know

**For Users:**
- `app.py` - The UI you interact with
- `analyst_brain.json` - Your saved mappings (you download this)
- Output CSVs - Your final models (DCF, LBO, Comps)

**For Developers:**
- `modeler/engine.py` - Core modeling logic (MODIFIED)
- `mapper/mapper_enhanced.py` - Mapping algorithm
- `utils/confidence_engine.py` - Validation rules
- `run_pipeline.py` - Pipeline orchestration

**For Configuration:**
- `config/aliases.csv` - Default mappings (edit to add hardcoded mappings)
- `config/ib_rules.py` - Financial rules and buckets

---

## 🎓 Learning Resources

### Understanding XBRL Taxonomy

**What is XBRL?**
eXtensible Business Reporting Language - a global standard for exchanging business information.

**Key Concepts:**
- **Element ID**: Unique identifier (e.g., `us-gaap_Revenues`)
- **Concept**: The accounting concept (e.g., "Revenue")
- **Label**: Human-readable name (e.g., "Total Revenue")
- **Balance**: Debit or Credit
- **Period Type**: Instant (point in time) or Duration (period)

**Example:**
```
Element ID: us-gaap_Revenues
Concept: Revenues
Standard Label: Revenues
Terse Label: Revenue
Verbose Label: Revenue from Operations
Balance: Credit
Period Type: Duration
```

### Financial Modeling Concepts

**DCF (Discounted Cash Flow):**
- Valuation method based on future cash flows
- Projects Unlevered Free Cash Flow (UFCF)
- Discounts to present value using WACC

**LBO (Leveraged Buyout):**
- Acquisition using significant debt
- Focus on leverage ratios and coverage
- Exit strategy at 5-7 years

**Trading Comps:**
- Compare company to peers
- Use multiples (EV/EBITDA, P/E)
- Benchmark performance

### Accounting Identities

**Balance Sheet Equation:**
```
Assets = Liabilities + Equity
```

**Cash Flow Reconciliation:**
```
Net Income
+ Non-Cash Charges (D&A)
+ Changes in Working Capital
= Operating Cash Flow
- CapEx
= Free Cash Flow
```

**Retained Earnings Rollforward:**
```
Beginning RE
+ Net Income
- Dividends
= Ending RE
```

---

## 📞 Support & Contact

### Getting Help

**For Technical Issues:**
1. Check this guide's Troubleshooting section
2. Review logs: `logs/engine_thinking.log`
3. Check validation report in Tab 1

**For Mapping Issues:**
1. Use Tab 4 "Fix Unmapped"
2. Search taxonomy database (24,388 concepts)
3. Save to brain and re-process

**For Model Questions:**
1. Review Tab 2 "Financial Models"
2. Check validation report
3. Verify input data in Tab 3

### Documentation References

- **Quick Start**: `README_START_HERE.md`
- **Architecture**: `ARCHITECTURE_DETAILED.md`
- **Validation**: `VALIDATION_CERTIFICATE.md`
- **Confidence System**: `CONFIDENCE_FRAMEWORK.md`
- **This Guide**: `COMPREHENSIVE_USER_GUIDE.md`

---

## 🔄 Version History

### v3.1 (Current) - 2026-01-09

**Major Changes:**
- ✅ **Fixed blocking validation issue** - System no longer blocks UI access
- ✅ **Partial model generation** - Generates models even with warnings
- ✅ **Improved error messages** - Clear guidance on next steps
- ✅ **Non-blocking pipeline** - Users can always access Tab 4

**Technical Details:**
- Modified `modeler/engine.py` (lines 1484-1504)
- Updated `app.py` error handling (lines 640-671)
- Changed validation from blocking exception to warning return
- Added partial output support in UI

### v3.0 - Previous Release

- Iterative Thinking Engine
- 3-attempt recovery system
- Thinking logs
- Confidence scoring

### v2.0 - Initial Release

- Basic pipeline
- Mapping system
- Model generation

---

## ✅ Summary & Next Steps

### What You Learned

1. **System Overview** - How FinanceX transforms financial statements into models
2. **Pipeline Stages** - Extract → Map → Model → Validate
3. **User Journey** - Upload → Process → Review → Fix → Download
4. **Analyst Brain** - Your portable mapping memory
5. **Error Handling** - Non-blocking system, always accessible UI
6. **Interactive Tools** - Tab 4 for fixing unmapped items

### Your First Session Checklist

- [ ] Launch app: `streamlit run app.py`
- [ ] Prepare Excel with 3 tabs
- [ ] Upload file (no brain first time)
- [ ] Review results in all 5 tabs
- [ ] Fix critical unmapped items in Tab 4
- [ ] Download brain from Tab 5
- [ ] Save brain to your computer
- [ ] Try second session with brain
- [ ] Verify mapping rate improved
- [ ] Download final models

### Pro Tips

1. **Start Simple** - First session will have many unmapped items (normal!)
2. **Focus on Critical** - Fix CapEx, Revenue, EBITDA first
3. **Save Your Brain** - Always download after mapping
4. **Iterate** - Each re-process improves results
5. **Team Sharing** - Share brain JSON with colleagues
6. **Review Logs** - Check `engine_thinking.log` for details

---

*End of Comprehensive User Guide*

**Questions? Issues? Improvements?**
This is a living document. If you found issues or have suggestions, please update this guide or contact the development team.

**Happy Analyzing! 📊**

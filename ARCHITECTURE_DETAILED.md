# FinanceX - Complete Architecture Documentation
## Comprehensive Code-Level Reference with Line Numbers

**Version:** Production V1.0
**Last Updated:** 2026-01-07
**Purpose:** Complete technical documentation showing the entire engine architecture

---

## Table of Contents

1. [Overview](#overview)
2. [Entry Points](#entry-points)
3. [Core Processing Pipeline](#core-processing-pipeline)
4. [Data Flow Architecture](#data-flow-architecture)
5. [Configuration & Rules](#configuration--rules)
6. [Utility Modules](#utility-modules)
7. [Database & Taxonomy](#database--taxonomy)
8. [Testing & Validation](#testing--validation)
9. [Architecture Diagrams](#architecture-diagrams)

---

## Overview

FinanceX is a production-grade financial analysis platform that transforms raw Excel financial statements into investment banking-ready models (DCF, LBO, Comps). The system uses XBRL taxonomy mapping, iterative thinking engine, and forensic validation.

**Core Philosophy:**
- "No Silent Failures" - All zero values trigger recovery attempts
- "Clean Slate Architecture" - Stateless processing with session isolation
- "BYOB (Bring Your Own Brain)" - Portable JSON memory for analyst corrections

---

## Entry Points

### 1. Web Application - `app.py`

**File:** `/app.py` (1,138 lines)

**Purpose:** Streamlit-based web UI with glassmorphism design

**Key Components:**

#### Header & Configuration (lines 1-290)
```python
# Lines 1-13: Module docstring
"""
FinanceX: Production V1.0 - Professional Financial Analysis
Flow: Onboarding -> Upload Brain -> Process -> Audit -> Download
"""

# Lines 15-31: Core imports
from session_manager import SessionManager, initialize_clean_slate
from run_pipeline import run_pipeline_programmatic
from validator.ai_auditor import AIAuditor
from utils.brain_manager import BrainManager
from utils.exporter import create_download_package
```

#### Session State Initialization (lines 291-328)
- **Lines 296-299:** Clean slate initialization
- **Lines 301-303:** SessionManager singleton
- **Lines 305-327:** Session state variables (pipeline_result, audit_report, brain_manager, etc.)

#### UI Rendering Functions:

1. **render_header()** (lines 397-405)
   - Displays main FinanceX branding

2. **render_sidebar()** (lines 410-492)
   - Brain upload/download (lines 416-446)
   - Session info display (lines 451-474)
   - Audit summary (lines 476-488)

3. **render_onboarding()** (lines 517-655)
   - 3-step onboarding flow
   - OCR prompt display (lines 529-553)
   - Excel setup guide (lines 557-579)
   - File upload handler (lines 592-654)

4. **render_analyst_cockpit()** (lines 660-722)
   - Main results dashboard
   - Metrics bar (lines 664-696)
   - Tab navigation (lines 701-721)

5. **Audit Results** - render_audit_results() (lines 724-818)
   - Critical failures display (lines 738-768)
   - Warnings display (lines 771-782)
   - Passed checks (lines 784-788)
   - Emergency actions (lines 792-817)

6. **Financial Models** - render_financial_models() (lines 820-880)
   - DCF display (lines 831-843)
   - LBO display (lines 845-857)
   - Comps display (lines 859-871)
   - Validation display (lines 873-879)

#### Core Workflow (lines 621-654)
```python
# Upload file -> Create session -> Run pipeline -> Run AI Auditor
sm.save_upload(session.session_id, uploaded_file.getvalue())
result = run_pipeline_programmatic(upload_path, output_dir, quiet=True)
auditor = AIAuditor(normalized_df, dcf_df, lbo_df, comps_df)
st.session_state.audit_report = auditor.run_full_audit()
```

---

### 2. CLI Pipeline - `run_pipeline.py`

**File:** `/run_pipeline.py` (444 lines)

**Purpose:** Unified end-to-end processing pipeline (CLI + programmatic interface)

#### Pipeline Stages:

1. **run_extractor()** (lines 70-92)
   - Converts Excel to CSV
   - Calls: `extractor.extract_standardized_excel()`
   - Output: `messy_input.csv`

2. **run_normalizer()** (lines 95-178)
   - Maps messy labels to XBRL taxonomy
   - Uses: `FinancialMapper` (mapper/mapper.py)
   - Output: `normalized_financials.csv`

3. **run_engine()** (lines 181-257)
   - Generates IB models
   - Uses: `FinancialEngine` (modeler/engine.py)
   - Outputs: DCF, LBO, Comps, Validation reports

#### Programmatic Interface (lines 260-340)
```python
def run_pipeline_programmatic(excel_path, output_dir, quiet=False):
    """
    Stateless function: Input Path -> Process -> Output Paths
    Returns: {
        "success": bool,
        "error": str,
        "duration": float,
        "files": {...}
    }
    """
```

**Key Features:**
- Stateless design
- Error handling with traceback
- Duration tracking
- Optional stdout suppression

---

### 3. Model Generator - `run_ib_model.py`

**File:** `/run_ib_model.py` (158 lines)

**Purpose:** Standalone investment banking model generator

**Workflow:**
1. Initialize FinancialEngine (lines 58-66)
2. Generate DCF (lines 69-77)
3. Generate LBO (lines 80-88)
4. Generate Comps (lines 91-99)
5. Run validation (lines 102-116)
6. Generate audit reports (lines 119-135)

---

## Core Processing Pipeline

### Stage 1: Extraction - `extractor/extractor.py`

**File:** `/extractor/extractor.py` (347 lines)

**Purpose:** Robust Excel extractor with auto-detection of structure

#### Key Functions:

1. **is_date_like()** (lines 50-70)
   - Detects period headers (2023, FY23, Q1 23, etc.)
   - Regex patterns (lines 38-47)

2. **is_label_like()** (lines 73-89)
   - Identifies line item labels
   - Filters out numeric values

3. **detect_header_row()** (lines 92-108)
   - Auto-detects which row contains dates
   - Searches first 20 rows

4. **detect_label_column()** (lines 111-126)
   - Auto-detects which column has labels
   - Checks first 5 columns

5. **clean_numeric_value()** (lines 129-160)
   - Handles: commas, parentheses (negatives), currency symbols, dashes
   - Returns: float or None

6. **extract_sheet()** (lines 163-230)
   - Core extraction logic
   - Auto-detects header and label positions
   - Returns: List of {Line Item, Amount, Note} dicts

7. **extract_standardized_excel()** (lines 233-273)
   - Main entry point
   - Processes all sheets
   - Skips non-standard tabs

**Input Format:**
- Excel file with 3 tabs: "Income Statement", "Balance Sheet", "Cash Flow"
- Row 1: Dates (or auto-detected)
- Column A: Line Item Labels (or auto-detected)

**Output Format:**
```csv
Line Item,Amount,Note
Revenue,100000,Income Statement | 2024
```

---

### Stage 2: Mapping - `mapper/mapper.py`

**File:** `/mapper/mapper.py` (550 lines)

**Purpose:** Deterministic financial mapper with BYOB integration

#### Architecture:

**Resolution Order (Tier 0 = Highest Priority):**
- Tier 0: Analyst Brain (user JSON memory) - lines 387-400
- Tier 1: Explicit Alias (config/aliases.csv) - lines 162-197
- Tier 2: Exact Label Match (DB reverse index) - lines 136-160
- Tier 3: Keyword/Partial Match - lines 263-358
- Tier 4: Safe Mode (hierarchy fallback) - lines 427-444
- Tier 5: Unmapped (error) - lines 446-454

#### Class: FinancialMapper

**Initialization (lines 83-104):**
```python
def __init__(self, db_path, alias_path, brain_manager=None):
    self.lookup_index = {}      # Normalized label -> concept mapping
    self.reverse_id_map = {}    # element_id -> concept_id
    self.presentation_parents = {}  # Hierarchy relationships
    self.brain_manager = brain_manager  # BYOB integration
```

**Key Methods:**

1. **connect()** (lines 106-116)
   - Loads DB, labels, aliases, hierarchy
   - Calls: `_load_reverse_id_map()`, `_load_db_labels()`, `_load_aliases()`, `_load_presentation_hierarchy()`

2. **map_input()** (lines 371-454)
   - **CRITICAL:** Core mapping function
   - Returns: `{input, found, element_id, source, concept_id, method}`

3. **_try_partial_match()** (lines 263-358)
   - Keyword matching for revenue/expense patterns
   - Handles: "Product Revenue" -> us-gaap_Revenues
   - Keyword maps (lines 270-357)

4. **_find_safe_parent()** (lines 227-261)
   - Walks presentation hierarchy
   - Finds safe parent concepts (lines 52-79)
   - Max depth: 5 levels

**BYOB Integration (lines 387-400):**
```python
# Tier 0: Analyst Brain - HIGHEST priority
if self.brain_enabled and self.brain_manager:
    brain_mapping = self.brain_manager.get_mapping(raw_input)
    if brain_mapping:
        return {
            "element_id": brain_mapping,
            "method": "Analyst Brain (User Memory)"
        }
```

---

### Stage 3: Normalization - `normalizer.py`

**File:** `/normalizer.py` (117 lines)

**Purpose:** Thin wrapper that applies mapper to all rows

**Process:**
1. Read messy_input.csv (lines 52-75)
2. For each row, call mapper.map_input()
3. Get metadata (balance, period_type)
4. Write normalized row

**Output Columns:**
- Source_Label, Source_Amount
- Statement_Source, Period_Date
- Status (VALID/UNMAPPED)
- Canonical_Concept, Concept_ID, Standard_Label
- Balance, Period_Type, Map_Method, Taxonomy

---

### Stage 4: Financial Modeling - `modeler/engine.py`

**File:** `/modeler/engine.py` (1,376 lines)

**Purpose:** JPMC/Citadel-grade financial engine with iterative thinking

#### Architecture Overview:

**Class Hierarchy:**
1. `ThinkingLogger` (lines 58-128) - Logs reasoning trail
2. `AttemptResult` (lines 153-162) - Tracks iteration results
3. `AuditEntry` (lines 179-188) - Audit trail
4. `SanityCheckResult` (lines 191-201) - Bucket validation
5. `FinancialEngine` (lines 212-1376) - Main engine

#### FinancialEngine Class:

**Initialization (lines 229-253):**
```python
def __init__(self, norm_file_path):
    self.raw_df = pd.read_csv(norm_file_path)
    self.unmapped_df = self.raw_df[Status != 'VALID']  # Track unmapped
    self.df = self.raw_df[Status == 'VALID']  # Only process valid
    self.tax_engine = get_taxonomy_engine()  # Taxonomy queries
    self._build_hierarchy_aware_structures()  # Prevent double-counting
```

**Hierarchy-Aware Aggregation (lines 284-353):**

*CRITICAL INNOVATION:* Prevents double-counting when multiple source labels map to same concept.

**Example Problem Solved:**
```
"Products net sales" ($60K) → us-gaap_Revenues
"Services net sales" ($40K) → us-gaap_Revenues
"Total net sales" ($100K) → us-gaap_Revenues

OLD BEHAVIOR: Sum all = $200K (WRONG!)
NEW BEHAVIOR: Detect hierarchy, use Total = $100K (CORRECT!)
```

**Algorithm (lines 397-443):**
1. Detect total lines (contains "total", "net", "gross")
2. Detect component lines (contains "product", "service", "segment")
3. If total + components: verify total >= sum(components), use total
4. If only components: sum them
5. If ambiguous: use MAX for safety

**Iterative Thinking Engine (lines 794-1029):**

3-attempt recovery with escalating strategies:

1. **Attempt 1 - STRICT** (lines 795-817)
   - Uses ib_rules.py strict tags only
   - Revenue: REVENUE_TOTAL_IDS
   - Net Income: NET_INCOME_IDS

2. **Attempt 2 - RELAXED** (lines 820-861)
   - Fuzzy matches (contains "Profit", "Revenue")
   - Searches raw_df for keywords

3. **Attempt 3 - DESPERATE** (lines 863-924)
   - Any line item >$100M with keyword "Sales"
   - Uses MAX value as last resort

**Workflow (lines 926-1029):**
```python
while attempt < max_attempts:
    if revenue.sum() > 0:
        # Success - break and use this result
        break
    else:
        # Failed - escalate to next attempt
        attempt += 1
```

**Model Builders:**

1. **build_dcf_ready_view()** (lines 1035-1158)
   - Revenue cascade (lines 1050-1053)
   - COGS, Gross Profit (lines 1056-1059)
   - OpEx breakdown (SG&A, R&D, Other)
   - EBITDA, EBIT, NOPAT
   - NWC calculation (lines 1093-1102)
   - Unlevered FCF (line 1106)
   - Sanity loop validation (lines 1108-1126)
   - Balance sheet validation (line 1129)

2. **build_lbo_ready_view()** (lines 1164-1215)
   - Adjusted EBITDA (add back restructuring, impairment, stock comp)
   - Debt stack (short-term, long-term, capital leases)
   - Net debt calculation
   - Leverage ratio (Net Debt / Adj EBITDA)
   - Interest coverage (EBITDA / Interest)

3. **build_comps_ready_view()** (lines 1221-1273)
   - Revenue, EBITDA, EBIT, Net Income
   - Margins (EBITDA %, Net Income %)
   - EV bridge (Cash, Debt, Preferred, Minority Interest)
   - Share data (Basic, Diluted)
   - EPS calculation

**Sanity Loop (lines 509-697):**

Multi-level fallback recovery when critical buckets are zero:

- **Level 1:** Keyword matching on mapped data (lines 540-553)
- **Level 2:** Fuzzy matching on unmapped data (lines 556-581)
- **Level 3:** Raw data scan with synonyms (lines 584-623)

**Deep Clean (lines 703-789):**

Balance sheet validation & auto-correction:
- Verifies: Assets = Liabilities + Equity
- Infers missing values (e.g., Equity = Assets - Liabilities)
- 1% tolerance for floating point errors

---

## Data Flow Architecture

### Complete Data Flow:

```
1. Excel Upload (app.py:618)
   ↓
2. SessionManager.save_upload() (session_manager.py:362)
   ↓
3. run_pipeline_programmatic() (run_pipeline.py:260)
   ↓
4. Extraction (extractor/extractor.py:233)
   Excel → messy_input.csv
   ↓
5. Normalization (mapper/mapper.py:371)
   messy_input.csv → normalized_financials.csv
   ↓
6. Financial Modeling (modeler/engine.py:1035)
   normalized_financials.csv → DCF, LBO, Comps
   ↓
7. AI Auditor (validator/ai_auditor.py:1206)
   Models → AuditReport
   ↓
8. Display Results (app.py:660)
   AuditReport → UI
```

---

## Configuration & Rules

### Investment Banking Rules - `config/ib_rules.py`

**File:** `/config/ib_rules.py` (1,094 lines)

**Purpose:** Comprehensive concept sets for IB models

#### Structure:

**Revenue (lines 22-120):**
- REVENUE_TOTAL_IDS: 78 total concepts
- REVENUE_COMPONENT_IDS: 20 component concepts
- Includes: US-GAAP, IFRS, Tech/SaaS, Financial Services, Retail variations

**COGS (lines 123-177):**
- COGS_TOTAL_IDS: 10 concepts
- COGS_COMPONENT_IDS: 25 concepts
- Includes: Products, Services, Materials, Labor, Overhead, Industry-specific

**Operating Expenses (lines 180-273):**
- SG_AND_A_IDS: 28 concepts (Selling, Marketing, G&A, Compensation)
- R_AND_D_IDS: 10 concepts (Research, Development, Engineering)
- FUEL_EXPENSE_IDS: 6 concepts (Airlines, Utilities)
- OTHER_OPEX_IDS: 9 concepts

**D&A (lines 277-305):**
- 18 concepts (Depreciation, Amortization, Right-of-use assets)

**Adjustments (lines 309-332):**
- RESTRUCTURING_IDS, IMPAIRMENT_IDS, STOCK_COMP_IDS

**Below the Line (lines 335-395):**
- INTEREST_EXP_IDS, TAX_EXP_IDS, NET_INCOME_IDS (25 net income variations)

**Balance Sheet (lines 409-628):**
- Current Assets (72 concepts total)
- Current Liabilities (8 concepts)
- Fixed Assets (9 concepts)
- Debt (22 concepts)
- Equity (13 concepts)

**Cash Flow (lines 632-689):**
- CAPEX_IDS: 15 concepts
- CFO_IDS, CFI_IDS, CFF_IDS

**Keyword Fallback Mappings (lines 743-931):**

Massively expanded synonym dictionary for fallback recovery:
- 189 keyword mappings
- Covers: common variations, industry-specific terms, alternative naming from 10-K filings

**Example:**
```python
KEYWORD_FALLBACK_MAPPINGS = {
    "revenue": REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS,
    "net sales": REVENUE_TOTAL_IDS,
    "subscription": REVENUE_TOTAL_IDS | REVENUE_COMPONENT_IDS,
    "premiums": REVENUE_TOTAL_IDS,  # Insurance
    ...
}
```

**Fuzzy Matching (lines 955-1027):**
```python
def fuzzy_match_bucket(source_label):
    """Keyword-based bucket matching with scoring"""
    # Returns: (bucket_name, concept_set)
```

---

## Utility Modules

### Session Manager - `session_manager.py`

**File:** `/session_manager.py` (605 lines)

**Purpose:** Clean Slate directory management

#### Clean Slate Architecture (lines 61-133):

**Directory Structure:**
```
├── temp_session/   # Created on launch, wiped on exit
├── taxonomy/       # ReadOnly DB (XBRL data)
├── output/         # Final models (wiped on launch)
└── logs/           # Thinking logs (wiped on launch)
```

**Key Functions:**

1. **initialize_clean_slate()** (lines 61-133)
   - Wipes temp_session/ and output/ on launch
   - Preserves taxonomy_2025.db
   - Creates fresh logs/

2. **cleanup_on_exit()** (lines 136-146)
   - Registered with atexit
   - Wipes temp_session/

3. **save_current_upload()** (lines 181-209)
   - Saves file to temp_session/uploads/
   - Clears existing uploads (single session model)

4. **write_thinking_log()** (lines 212-233)
   - Writes reasoning trail to logs/

#### SessionManager Class (lines 261-538):

**Purpose:** Multi-session isolation for concurrent processing

**Methods:**
- create_session(): Creates isolated session directory
- save_upload(): Saves file to session
- get_session_files(): Returns all output paths
- cleanup_session(): Deletes session
- cleanup_expired_sessions(): Auto-cleanup (24hr expiry)

---

### Brain Manager - `utils/brain_manager.py`

**File:** `/utils/brain_manager.py` (752 lines)

**Purpose:** Analyst Brain (BYOB) - Portable JSON memory

#### Data Structures:

1. **MappingEntry** (lines 48-57)
   ```python
   source_label: str
   target_element_id: str
   source_taxonomy: str
   confidence: float
   created_at: str
   notes: str
   ```

2. **BrainMetadata** (lines 60-70)
   - Version, timestamps, owner, totals

3. **CustomCommand** (lines 73-82)
   - User-defined commands (Teach Me flow)

4. **ValidationPreference** (lines 85-91)
   - Custom thresholds, severity overrides

#### BrainManager Class (lines 94-628):

**Key Methods:**

1. **load_from_file()** (lines 126-203)
   - Loads JSON brain file
   - Parses: metadata, mappings, validation prefs, commands, history

2. **_rebuild_merged_mappings()** (lines 381-423)
   - **CRITICAL:** User brain ALWAYS overrides defaults
   - Load defaults from aliases.csv (base layer)
   - Apply user brain mappings on top (user wins)

3. **get_mapping()** (lines 353-366)
   - Returns element_id for a source label
   - Checks merged view (defaults + user brain)

4. **add_mapping()** (lines 286-325)
   - Adds/updates mapping in brain
   - Logs to session history

5. **learn_from_correction()** (lines 578-600)
   - Learns from UI corrections
   - Used during interactive fixing

**BYOB Workflow:**
1. Analyst uploads brain JSON (app.py:424)
2. Brain loaded and merged with defaults (lines 193-423)
3. Mapper uses brain for Tier 0 lookups (mapper.py:387-400)
4. User makes corrections in UI (app.py:957-976)
5. Brain learns corrections (brain_manager.py:578-600)
6. Analyst downloads updated brain (app.py:439-446)

---

### Taxonomy Utilities - `taxonomy_utils.py`

**File:** `/taxonomy_utils.py` (525 lines)

**Purpose:** Dynamic XBRL taxonomy queries

#### TaxonomyEngine Class (lines 22-465):

**Architecture:**
- Caches: concepts, calculation trees, hierarchy (lines 32-103)
- Provides: calculation linkbase, hierarchy traversal, validation

**Key Methods:**

1. **get_calculation_children()** (lines 109-118)
   - Returns: List of {child_id, weight, order}
   - Example: us-gaap_Revenues → [ProductRevenue, ServiceRevenue]

2. **smart_aggregate()** (lines 139-209)
   - **CORE FUNCTION:** Intelligent aggregation preventing double-counting
   - Algorithm:
     - Identify totals vs components
     - If total exists: validate against calc sum, use total
     - If no total: sum components (excluding descendants)
     - Returns: (value, method, audit_trail)

3. **normalize_sign()** (lines 220-252)
   - Normalizes amounts based on balance type (debit/credit)
   - Handles sign conventions for IB models

4. **find_safe_parent()** (lines 301-333)
   - Walks presentation hierarchy to find mappable ancestor
   - Max depth: 5 levels

5. **validate_calculation()** (lines 360-406)
   - Verifies: reported total = sum(children)
   - Tolerance: 1%

6. **validate_balance_sheet_equation()** (lines 408-431)
   - Verifies: Assets = Liabilities + Equity
   - Tolerance: 0.1%

---

### AI Auditor - `validator/ai_auditor.py`

**File:** `/validator/ai_auditor.py` (1,302 lines)

**Purpose:** Forensic accounting validation (66 comprehensive rules)

#### Architecture:

**Severity Levels (lines 29-35):**
- CRITICAL: Must fix before proceeding
- WARNING: Review recommended
- INFO: Informational
- PASS: Check passed

**Data Structures:**
- AuditFinding (lines 38-55): Single finding
- AuditReport (lines 58-85): Complete audit with all findings

#### FinancialDataExtractor Class (lines 88-515):

**Purpose:** Extracts metrics from normalized data and models

**Key Method: extract_current_period()** (lines 229-510)

Extracts 100+ financial metrics:
- Balance Sheet: Assets, Liabilities, Equity (lines 240-310)
- Income Statement: Revenue, COGS, Expenses, Net Income (lines 344-420)
- Cash Flow: CFO, CFI, CFF, CapEx (lines 445-464)

**PRODUCTION FIX (lines 107-144):**
- Uses EXACT concept matching (not str.contains)
- Hierarchy-aware: prefers "Total" lines over components
- Period detection: uses MIN (Period 1 = most recent)

#### ForensicRuleEngine Class (lines 518-1184):

**66 Validation Rules:**

**1. ACCOUNTING IDENTITIES (Rules 1-20, lines 576-778):**
- Balance Sheet Equation (line 579)
- Cash Flow Consistency (line 591)
- Retained Earnings Continuity (line 603)
- Gross Profit Calculation (line 612)
- EBITDA Calculation (line 621)
- EBIT Calculation (line 632)
- EPS Consistency (line 642)
- Equity Composition (line 651)
- Current Assets Composition (line 664)
- Noncurrent Assets Composition (line 674)
- Current Liabilities Composition (line 683)
- Noncurrent Liabilities Composition (line 692)
- Assets Sum Consistency (line 701)
- Liabilities Sum Consistency (line 710)
- Total Revenue and Expenses (line 722)
- Expense Breakdown (line 734)
- Net Income to Equity (line 743)
- Net Income to Cash Flow (line 752)
- Cash Flow Reconciliation (line 762)
- Worksheet Balance (line 771)

**2. SIGN & LOGIC INTEGRITY (Rules 21-40, lines 780-910):**
- Revenue Non-Negativity (line 783)
- COGS Non-Negativity (line 791)
- Operating Expense Non-Negativity (line 799)
- D&A Non-Negativity (line 807)
- CapEx Sign (line 815)
- Inventory Non-Negativity (line 823)
- AR Non-Negativity (line 831)
- AP Non-Negativity (line 839)
- Equity Non-Negativity (line 847)
- EPS Sign Consistency (line 855)
- Tax Expense Sign (line 863)
- Interest Expense Sign (line 871)
- Interest Without Debt (line 879)
- Capital Lease Depreciation (line 887)
- Asset Write-Up Without CapEx (line 895)
- Undisclosed One-Time Items (line 903)

**3. RATIO SANITY CHECKS (Rules 41-60, lines 912-1002):**
- Gross Margin Bounds (line 915)
- EBITDA vs Net Margin (line 924)
- Effective Tax Rate High (line 933)
- Current Ratio Extreme (line 942)
- Quick Ratio Extreme (line 951)
- Debt/Equity Excessive (line 960)
- Debt/EBITDA Excessive (line 969)
- Interest Coverage Weak (line 978)
- ROA Impossible (line 987)
- Negative Gross, Positive Net (line 996)

**4. GROWTH & VOLATILITY (Rules 61-80, lines 1005-1091):**
- Revenue Spike (line 1008)
- Revenue Drop (line 1016)
- AR Growth > Revenue (line 1024)
- Inventory Growth > Sales (line 1032)
- CapEx Missing With Growth (line 1040)
- CFO Volatility (line 1048)
- Debt Surge Without Interest (line 1057)
- Equity Jump Without Raise (line 1066)
- EPS Volatility (line 1074)
- Dividend Policy Shift (line 1083)

**5. CROSS-STATEMENT LINKAGES (Rules 81-100, lines 1093-1183):**
- PPE Rollforward (line 1095)
- Accumulated Depreciation (line 1104)
- Debt Rollforward (line 1113)
- Shares Rollforward (line 1122)
- Interest-Debt Link (line 1131)
- Tax Paid vs Expense (line 1140)
- AR CFO Adjustment (line 1148)
- Inventory CFO Adjustment (line 1157)
- AP CFO Adjustment (line 1166)
- CapEx in CFI (line 1175)

#### AIAuditor Class (lines 1187-1254):

**Main Method: run_full_audit()** (lines 1206-1235)
```python
def run_full_audit():
    current_data = self.extractor.extract_current_period()
    prior_data = self.extractor.extract_prior_period()
    findings = self.rule_engine.run_all_rules(current_data, prior_data)
    self._check_data_quality()  # Mapping coverage check
    return AuditReport(findings, summary)
```

---

## Database & Taxonomy

### Taxonomy Database: `output/taxonomy_2025.db`

**Tables:**

1. **concepts** - XBRL concepts
   - concept_id (UUID)
   - element_id (us-gaap_Revenues)
   - concept_name (Revenues)
   - source (US_GAAP / IFRS)
   - balance (debit / credit)
   - period_type (instant / duration)
   - data_type (monetaryItemType, etc.)

2. **labels** - Human-readable labels
   - concept_id
   - label_role (standard, terse, verbose)
   - label_text ("Revenues, Net")

3. **calculations** - Calculation relationships
   - parent_concept_id
   - child_concept_id
   - weight (+1.0 or -1.0)
   - order_index

4. **presentation_roles** - Presentation hierarchy
   - concept_id
   - parent_concept_id
   - order_index

**Size:** ~19,000 concepts (US-GAAP + IFRS)

**Loaded By:**
- mapper.py (lines 108-116, 124-160)
- taxonomy_utils.py (lines 43-103)

---

## Testing & Validation

### Test File: `tests/test_comprehensive_validation.py`

**File:** `/tests/test_comprehensive_validation.py`

**Purpose:** End-to-end validation tests

---

## Architecture Diagrams

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         ENTRY POINTS                            │
├─────────────────────────────────────────────────────────────────┤
│  app.py (Web UI)  │  run_pipeline.py (CLI)  │  run_ib_model.py │
└──────────┬──────────────────┬────────────────────────┬──────────┘
           │                  │                        │
           └──────────────────┴────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  CORE PIPELINE    │
                    └─────────┬─────────┘
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
     ┌─────▼─────┐     ┌─────▼─────┐     ┌─────▼─────┐
     │EXTRACTION │     │ MAPPING   │     │ MODELING  │
     │ extractor │     │  mapper   │     │  engine   │
     └─────┬─────┘     └─────┬─────┘     └─────┬─────┘
           │                  │                  │
           │                  │                  │
    messy_input.csv   normalized.csv    DCF/LBO/Comps
           │                  │                  │
           └──────────────────┴──────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  VALIDATION       │
                    │  ai_auditor       │
                    └─────────┬─────────┘
                              │
                         AuditReport
```

### Data Flow Through Mapper

```
Raw Label: "Total Net Sales Revenue"
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│ TIER 0: Analyst Brain (User Memory)                    │
│   brain_manager.get_mapping("Total Net Sales Revenue") │
│   ✓ Found: us-gaap_SalesRevenueNet                     │
└─────────────────────────────────────────────────────────┘
     │
     ▼ (if not found, continue)
┌─────────────────────────────────────────────────────────┐
│ TIER 1: Explicit Alias (config/aliases.csv)            │
│   lookup_index["total net sales revenue"]              │
└─────────────────────────────────────────────────────────┘
     │
     ▼ (if not found, continue)
┌─────────────────────────────────────────────────────────┐
│ TIER 2: Exact Label Match (DB reverse index)           │
│   Query: SELECT concept_id WHERE label = ...           │
└─────────────────────────────────────────────────────────┘
     │
     ▼ (if not found, continue)
┌─────────────────────────────────────────────────────────┐
│ TIER 3: Keyword Match (partial)                        │
│   if "revenue" in label: → us-gaap_Revenues            │
│   if "sales" in label: → us-gaap_SalesRevenueNet       │
└─────────────────────────────────────────────────────────┘
     │
     ▼ (if not found, continue)
┌─────────────────────────────────────────────────────────┐
│ TIER 4: Safe Mode (hierarchy fallback)                 │
│   Walk presentation tree to find safe parent           │
└─────────────────────────────────────────────────────────┘
     │
     ▼
Result: {
    "found": true,
    "element_id": "us-gaap_Revenues",
    "method": "Analyst Brain (User Memory)"
}
```

### Iterative Thinking Engine Flow

```
Critical Bucket: "Total Revenue" = 0
     │
     ▼
┌──────────────────────────────────────────────────────────┐
│ ATTEMPT 1: STRICT                                        │
│   Use ib_rules.py strict tags (REVENUE_TOTAL_IDS)       │
│   Result: Revenue = 0 ❌                                 │
└──────────────────────────────────────────────────────────┘
     │
     ▼ FAILED - Thinking...
┌──────────────────────────────────────────────────────────┐
│ ATTEMPT 2: RELAXED                                       │
│   Fuzzy matching: contains "Revenue", "Sales"           │
│   Search raw_df for keywords                            │
│   Result: Revenue = $500M ✓                             │
└──────────────────────────────────────────────────────────┘
     │
     ▼ SUCCESS
Store: self._iterative_revenue = pd.Series([500M, 450M, 400M])
Use in model building
```

### BYOB (Analyst Brain) Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Analyst uploads analyst_brain.json                  │
│    (app.py:424 - st.file_uploader)                     │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Brain loaded and merged                             │
│    brain_manager.load_from_json_string()               │
│    _rebuild_merged_mappings()                          │
│      - Load defaults from aliases.csv                  │
│      - Apply user brain ON TOP (user wins)             │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Mapper uses brain (Tier 0 lookup)                   │
│    mapper.map_input("Custom Label")                    │
│      → brain_manager.get_mapping("Custom Label")       │
│      → Returns: us-gaap_CustomConcept                  │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ 4. User makes corrections in UI                        │
│    (app.py:957-976 - Fix Unmapped tab)                │
│    brain_manager.add_mapping(label, element_id)        │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ 5. Download updated brain                              │
│    (app.py:439 - Download Updated Brain button)       │
│    brain_manager.to_json_string()                      │
│    → analyst_brain_updated.json                        │
└─────────────────────────────────────────────────────────┘
```

---

## Critical Code Patterns

### 1. Hierarchy-Aware Aggregation Pattern

**Problem:** Multiple source labels mapping to same concept causes double-counting

**Solution:** (modeler/engine.py:284-443)

```python
# Step 1: Group by (Concept, Period)
for row in df:
    key = f"{concept}|{period}"
    concept_groups[key]['entries'].append({
        'source_label': label,
        'amount': amount,
        'is_total': self._detect_total_line(label),
        'is_component': self._detect_component_line(label)
    })

# Step 2: Resolve conflicts
if len(entries) > 1:
    totals = [e for e in entries if e['is_total']]
    components = [e for e in entries if e['is_component']]

    if totals:
        # Use total line (prevents double-counting)
        resolved_value = totals[0]['amount']
        method = 'TOTAL_LINE_USED'
    else:
        # Sum components
        resolved_value = sum(c['amount'] for c in components)
        method = 'COMPONENT_SUM'
```

### 2. Iterative Thinking Pattern

**Problem:** Critical buckets (Revenue, EBITDA) are zero due to mapping failures

**Solution:** (modeler/engine.py:926-1029)

```python
attempt = 0
while attempt < max_attempts:
    attempt += 1

    if attempt == 1:
        revenue = self._attempt_strict()  # Use strict tags
    elif attempt == 2:
        revenue = self._attempt_relaxed()  # Fuzzy matching
    else:
        revenue = self._attempt_desperate()  # >$100M + keyword

    if revenue.sum() > 0:
        # SUCCESS - use this result
        self._iterative_revenue = revenue
        break
```

### 3. BYOB Override Pattern

**Problem:** Default aliases may be incorrect for specific companies

**Solution:** (mapper/mapper.py:387-400 + brain_manager.py:381-423)

```python
# Tier 0: Check user brain FIRST (highest priority)
if self.brain_enabled:
    brain_mapping = self.brain_manager.get_mapping(raw_input)
    if brain_mapping:
        return {
            "element_id": brain_mapping,
            "method": "Analyst Brain (User Memory)"
        }

# Merge logic ensures user wins:
# 1. Load defaults
# 2. Apply user brain ON TOP (overwrites defaults)
for key, entry in self.mappings.items():
    self._merged_mappings[key] = entry.target_element_id  # User wins
```

### 4. Forensic Validation Pattern

**Problem:** Financial models may have mathematical inconsistencies

**Solution:** (validator/ai_auditor.py:579-586)

```python
# Balance Sheet Equation check
findings.append(self._rule(
    "Balance Sheet Equation",
    abs(d["assets"] - (d["liabilities"] + d["equity"])) > self.tol and d["assets"] != 0,
    "CRITICAL",
    "Assets != Liabilities + Equity",
    "ACCOUNTING_IDENTITY",
    {"assets": d["assets"], "liabilities": d["liabilities"], "equity": d["equity"]}
))
```

---

## Performance Characteristics

### Processing Pipeline Benchmarks:

**Typical 3-Statement Company (100 line items):**
- Extraction: ~0.5s
- Normalization: ~1.0s
- Modeling: ~2.0s (including 3 iterative attempts)
- Validation: ~0.5s
- **Total: ~4.0s**

**Large Company (500 line items):**
- Extraction: ~1.5s
- Normalization: ~3.0s
- Modeling: ~5.0s
- Validation: ~1.5s
- **Total: ~11.0s**

### Memory Usage:

**Typical Session:**
- Taxonomy DB cache: ~50MB
- Normalized data: ~2MB
- Models: ~1MB
- **Total: ~53MB**

---

## Error Handling Strategy

### 1. Graceful Degradation:
- If strict mapping fails → use relaxed
- If relaxed fails → use desperate
- If all fail → proceed with zeros (flagged)

### 2. Audit Trail:
- Every mapping decision logged
- Hierarchy resolutions tracked
- Iterative attempts recorded

### 3. User Feedback:
- Critical errors: Block processing
- Warnings: Allow with review
- Info: Display for transparency

---

## Extension Points

### Adding New Concepts:
1. Add to `config/ib_rules.py` concept sets
2. Add to `KEYWORD_FALLBACK_MAPPINGS`
3. Update `get_all_concept_sets()`

### Adding New Models:
1. Create `build_*_view()` in `modeler/engine.py`
2. Add to `run_engine()` in `run_pipeline.py`
3. Add tab in `app.py` UI

### Adding New Validation Rules:
1. Add to `ForensicRuleEngine.run_all_rules()` in `validator/ai_auditor.py`
2. Categorize (ACCOUNTING_IDENTITY, SIGN_LOGIC, etc.)

---

## Security & Privacy

### Data Isolation:
- Each session isolated in temp directory
- Auto-cleanup on exit
- No permanent storage of user data

### Taxonomy Database:
- Read-only
- No user data mixed with taxonomy
- Portable (can be copied)

### Brain File:
- JSON format (human-readable)
- No PII required
- Portable across analysts

---

## Deployment Architecture

### Production Deployment:
```
Streamlit Cloud / Docker Container
    │
    ├── app.py (Streamlit web server)
    ├── taxonomy_2025.db (Read-only)
    ├── config/aliases.csv (Defaults)
    └── temp_session/ (Ephemeral)
```

### Local Development:
```bash
python -m streamlit run app.py
```

---

## Conclusion

This architecture documentation provides complete code-level transparency into FinanceX's engine. Every critical component is documented with exact file paths and line numbers.

**Key Architectural Innovations:**
1. **Hierarchy-Aware Aggregation** - Prevents double-counting
2. **Iterative Thinking Engine** - No silent failures
3. **BYOB Architecture** - Portable analyst memory
4. **Forensic Validation** - 66 comprehensive rules
5. **Clean Slate Design** - Stateless processing

**For Further Reading:**
- `README_START_HERE.md` - User guide
- `VALIDATION_CERTIFICATE.md` - Validation report
- `FIXES_IMPLEMENTED.md` - Bug fixes log

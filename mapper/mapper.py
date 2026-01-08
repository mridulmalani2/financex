#!/usr/bin/env python3
"""
Stage 2: Enhanced Deterministic Financial Mapper - PRODUCTION v3.0
===================================================================
This script acts as the "Compiler Frontend". It maps messy input strings
to canonical XBRL concept IDs using a strict, tiered resolution strategy.

PRODUCTION v3.0 - BYOB Architecture Integration:
  - Integrates with Analyst Brain (portable JSON memory)
  - Brain mappings have HIGHEST priority (user memory wins)

PRODUCTION v3.1 - CONFIDENCE SCORING:
  - Every mapping carries a deterministic confidence score (0.0 to 1.0)
  - Confidence based on mapping resolution tier
  - Fully explainable and traceable

Resolution Order:
  0. Analyst Brain (user's JSON memory) -> HIGHEST priority (confidence: 1.00)
  1. Alias Lookup (config/aliases.csv) -> High priority overrides (confidence: 0.95)
  2. Exact Label Match (DB Reverse Index) -> Official taxonomy labels (confidence: 0.90)
  3. Keyword Match -> Fuzzy matching (confidence: 0.70)
  4. SAFE MODE: Hierarchy Fallback -> Walk up presentation tree (confidence: 0.50-0.70)
  5. Fallback: Unmapped (Error) -> Failed to map (confidence: 0.00)

Safe Mode Feature:
  When a granular concept can't be mapped directly, the mapper walks up
  the XBRL presentation hierarchy to find a valid parent concept.
  Example: "Apple iPhone Sales" -> walks up to "us-gaap_Revenues"

It DOES NOT use fuzzy matching, ML, or embeddings.
It ensures 100% traceability to a specific rule or standard.
"""
import sqlite3
import csv
import os
import sys
from typing import Dict, Optional, Tuple, List, Set

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import Brain Manager
try:
    from utils.brain_manager import BrainManager, get_brain_manager
    BRAIN_AVAILABLE = True
except ImportError:
    BRAIN_AVAILABLE = False
    print("  Warning: Brain Manager not available. BYOB features disabled.")

# Import Confidence Engine
try:
    from utils.confidence_engine import calculate_mapping_confidence
    from utils.lineage_graph import MappingSource
    CONFIDENCE_ENGINE_AVAILABLE = True
except ImportError:
    CONFIDENCE_ENGINE_AVAILABLE = False
    print("  Warning: Confidence Engine not available. Confidence scoring disabled.")

# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "output", "taxonomy_2025.db")
ALIAS_PATH = os.path.join(BASE_DIR, "config", "aliases.csv")

# Safe Parent Concepts - these are valid fallback targets
SAFE_PARENT_CONCEPTS = {
    # Revenue
    "us-gaap_Revenues", "us-gaap_SalesRevenueNet", "ifrs-full_Revenue",
    # COGS
    "us-gaap_CostOfRevenue", "us-gaap_CostOfGoodsAndServicesSold",
    # OpEx
    "us-gaap_OperatingExpenses", "us-gaap_SellingGeneralAndAdministrativeExpense",
    "us-gaap_ResearchAndDevelopmentExpense",
    # Assets
    "us-gaap_Assets", "us-gaap_AssetsCurrent", "us-gaap_AssetsNoncurrent",
    "us-gaap_CashAndCashEquivalentsAtCarryingValue",
    "us-gaap_AccountsReceivableNetCurrent", "us-gaap_InventoryNet",
    "us-gaap_PropertyPlantAndEquipmentNet",
    # Liabilities
    "us-gaap_Liabilities", "us-gaap_LiabilitiesCurrent", "us-gaap_LiabilitiesNoncurrent",
    "us-gaap_AccountsPayableCurrent", "us-gaap_LongTermDebt",
    # Equity
    "us-gaap_StockholdersEquity", "us-gaap_RetainedEarningsAccumulatedDeficit",
    # Cash Flow
    "us-gaap_NetCashProvidedByUsedInOperatingActivities",
    "us-gaap_PaymentsToAcquirePropertyPlantAndEquipment",
    # Net Income
    "us-gaap_NetIncomeLoss",
    # D&A
    "us-gaap_DepreciationDepletionAndAmortization",
    # Interest/Tax
    "us-gaap_InterestExpense", "us-gaap_IncomeTaxExpenseBenefit",
}


class FinancialMapper:
    def __init__(self, db_path: str, alias_path: str, brain_manager: 'BrainManager' = None):
        """
        Initialize the Financial Mapper.

        Args:
            db_path: Path to the taxonomy database
            alias_path: Path to the aliases CSV file
            brain_manager: Optional BrainManager instance for BYOB integration
        """
        self.db_path = db_path
        self.alias_path = alias_path
        self.conn = None

        # Memory Indexes
        self.lookup_index: Dict[str, dict] = {}
        self.reverse_id_map: Dict[str, str] = {}  # element_id -> concept_id
        self.presentation_parents: Dict[str, List[str]] = {}  # child -> [parents]
        self.safe_mode_enabled = True

        # BYOB Integration
        self.brain_manager = brain_manager
        self.brain_enabled = brain_manager is not None and BRAIN_AVAILABLE

    def connect(self):
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

        # Load data immediately upon connection
        self._load_reverse_id_map()
        self._load_db_labels()
        self._load_aliases()
        self._load_presentation_hierarchy()

    def _normalize(self, text: str) -> str:
        """Strict normalization: lowercase, stripped."""
        if not text: return ""
        return text.strip().lower()

    def _load_reverse_id_map(self):
        """Cache element_id (us-gaap_Assets) -> concept_id (UUID) for fast alias resolution."""
        print("  Loading Concept ID map...")
        cur = self.conn.cursor()
        cur.execute("SELECT element_id, concept_id FROM concepts WHERE element_id IS NOT NULL")
        count = 0
        for row in cur.fetchall():
            self.reverse_id_map[row['element_id']] = row['concept_id']
            count += 1
        print(f"    Loaded {count:,} canonical IDs.")

    def _load_db_labels(self):
        """Tier 2: Load all standard labels from the database."""
        print("  Indexing Taxonomy Labels (Tier 2)...")
        cur = self.conn.cursor()

        # Get standard labels joined with source info
        query = """
            SELECT l.label_text, c.concept_id, c.element_id, c.source
            FROM labels l
            JOIN concepts c ON l.concept_id = c.concept_id
            WHERE l.label_role = 'standard'
        """
        cur.execute(query)
        count = 0
        for row in cur.fetchall():
            norm_label = self._normalize(row['label_text'])
            # Only add if not already present (collisions favor first entry, or explicit alias later)
            if norm_label not in self.lookup_index:
                self.lookup_index[norm_label] = {
                    "concept_id": row['concept_id'],
                    "element_id": row['element_id'],
                    "source": row['source'],
                    "method": "Standard Label",
                    "match_text": row['label_text']
                }
                count += 1
        print(f"    Indexed {count:,} standard labels.")

    def _load_aliases(self):
        """Tier 1: Load aliases from CSV. These OVERRIDE standard labels."""
        if not os.path.exists(self.alias_path):
            print(f"  Warning: No alias file found at {self.alias_path}. Skipping Tier 1.")
            return

        print("  Indexing Aliases (Tier 1)...")
        count = 0
        with open(self.alias_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                alias = row.get('alias')
                target_element_id = row.get('element_id')
                source = row.get('source', 'MANUAL')

                if not alias or not target_element_id:
                    continue

                # Verify the target exists in our Taxonomy
                if target_element_id not in self.reverse_id_map:
                    print(f"    [WARNING] Alias '{alias}' points to unknown ID '{target_element_id}'. Skipping.")
                    continue

                concept_id = self.reverse_id_map[target_element_id]
                norm_alias = self._normalize(alias)

                # Overwrite existing entry if any
                self.lookup_index[norm_alias] = {
                    "concept_id": concept_id,
                    "element_id": target_element_id,
                    "source": source,
                    "method": "Explicit Alias",
                    "match_text": alias
                }
                count += 1
        print(f"    Indexed {count} aliases.")

    def _load_presentation_hierarchy(self):
        """Load presentation hierarchy for Safe Mode fallback."""
        print("  Loading Presentation Hierarchy (Tier 3 - Safe Mode)...")
        cur = self.conn.cursor()

        # Get parent-child relationships
        query = """
            SELECT
                c_child.element_id as child_id,
                c_parent.element_id as parent_id
            FROM presentation_roles pr
            JOIN concepts c_child ON pr.concept_id = c_child.concept_id
            JOIN concepts c_parent ON pr.parent_concept_id = c_parent.concept_id
            WHERE c_child.element_id IS NOT NULL
              AND c_parent.element_id IS NOT NULL
        """
        cur.execute(query)
        count = 0
        for row in cur.fetchall():
            child_id = row['child_id']
            parent_id = row['parent_id']
            if child_id not in self.presentation_parents:
                self.presentation_parents[child_id] = []
            if parent_id not in self.presentation_parents[child_id]:
                self.presentation_parents[child_id].append(parent_id)
                count += 1
        print(f"    Loaded {count:,} hierarchy relationships.")

    def _find_safe_parent(self, element_id: str, max_depth: int = 5) -> Optional[Tuple[str, int, List[str]]]:
        """
        Walk up the presentation hierarchy to find a valid safe parent.

        Args:
            element_id: Starting concept
            max_depth: Maximum levels to traverse

        Returns:
            (safe_parent_id, depth, path) or None
        """
        visited = set()
        queue = [(element_id, 0, [element_id])]

        while queue:
            current, depth, path = queue.pop(0)

            if depth > max_depth:
                continue

            if current in visited:
                continue
            visited.add(current)

            # Check if current concept is a safe parent
            if current in SAFE_PARENT_CONCEPTS and current != element_id:
                return (current, depth, path)

            # Get parents
            parents = self.presentation_parents.get(current, [])
            for parent in parents:
                if parent not in visited:
                    queue.append((parent, depth + 1, path + [parent]))

        return None

    def _try_partial_match(self, raw_input: str) -> Optional[dict]:
        """
        Try to find a partial match for revenue/expense-like labels.
        This handles cases like "Product Revenue" or "Service Costs".
        """
        norm_input = self._normalize(raw_input)

        # Revenue patterns
        revenue_keywords = ['revenue', 'sales', 'net sales', 'total sales', 'total revenue']
        for kw in revenue_keywords:
            if kw in norm_input:
                element_id = 'us-gaap_Revenues'
                if element_id in self.reverse_id_map:
                    return {
                        "concept_id": self.reverse_id_map[element_id],
                        "element_id": element_id,
                        "source": "US_GAAP",
                        "method": "Keyword Match (Revenue)",
                        "match_text": raw_input
                    }

        # Cost patterns
        cost_keywords = ['cost of', 'cogs', 'cost of sales', 'cost of goods', 'cost of revenue']
        for kw in cost_keywords:
            if kw in norm_input:
                element_id = 'us-gaap_CostOfRevenue'
                if element_id in self.reverse_id_map:
                    return {
                        "concept_id": self.reverse_id_map[element_id],
                        "element_id": element_id,
                        "source": "US_GAAP",
                        "method": "Keyword Match (COGS)",
                        "match_text": raw_input
                    }

        # Expense patterns
        expense_map = {
            'research': 'us-gaap_ResearchAndDevelopmentExpense',
            'r&d': 'us-gaap_ResearchAndDevelopmentExpense',
            'selling': 'us-gaap_SellingGeneralAndAdministrativeExpense',
            'general': 'us-gaap_SellingGeneralAndAdministrativeExpense',
            'administrative': 'us-gaap_SellingGeneralAndAdministrativeExpense',
            'sg&a': 'us-gaap_SellingGeneralAndAdministrativeExpense',
            'depreciation': 'us-gaap_DepreciationDepletionAndAmortization',
            'amortization': 'us-gaap_DepreciationDepletionAndAmortization',
            'd&a': 'us-gaap_DepreciationDepletionAndAmortization',
            'interest expense': 'us-gaap_InterestExpense',
            'income tax': 'us-gaap_IncomeTaxExpenseBenefit',
            'tax expense': 'us-gaap_IncomeTaxExpenseBenefit',
        }

        for keyword, element_id in expense_map.items():
            if keyword in norm_input:
                if element_id in self.reverse_id_map:
                    return {
                        "concept_id": self.reverse_id_map[element_id],
                        "element_id": element_id,
                        "source": "US_GAAP",
                        "method": f"Keyword Match ({keyword})",
                        "match_text": raw_input
                    }

        # Balance sheet patterns
        bs_map = {
            'cash': 'us-gaap_CashAndCashEquivalentsAtCarryingValue',
            'accounts receivable': 'us-gaap_AccountsReceivableNetCurrent',
            'receivable': 'us-gaap_AccountsReceivableNetCurrent',
            'inventory': 'us-gaap_InventoryNet',
            'inventories': 'us-gaap_InventoryNet',
            'property': 'us-gaap_PropertyPlantAndEquipmentNet',
            'ppe': 'us-gaap_PropertyPlantAndEquipmentNet',
            'accounts payable': 'us-gaap_AccountsPayableCurrent',
            'payable': 'us-gaap_AccountsPayableCurrent',
            'long-term debt': 'us-gaap_LongTermDebt',
            'long term debt': 'us-gaap_LongTermDebt',
            'total debt': 'us-gaap_LongTermDebt',
            'stockholders equity': 'us-gaap_StockholdersEquity',
            'shareholders equity': 'us-gaap_StockholdersEquity',
            'retained earnings': 'us-gaap_RetainedEarningsAccumulatedDeficit',
            'total assets': 'us-gaap_Assets',
            'total liabilities': 'us-gaap_Liabilities',
            'net income': 'us-gaap_NetIncomeLoss',
            'net loss': 'us-gaap_NetIncomeLoss',
        }

        for keyword, element_id in bs_map.items():
            if keyword in norm_input:
                if element_id in self.reverse_id_map:
                    return {
                        "concept_id": self.reverse_id_map[element_id],
                        "element_id": element_id,
                        "source": "US_GAAP",
                        "method": f"Keyword Match ({keyword})",
                        "match_text": raw_input
                    }

        return None

    def set_brain_manager(self, brain_manager: 'BrainManager'):
        """
        Set or update the brain manager for BYOB integration.

        Args:
            brain_manager: BrainManager instance
        """
        self.brain_manager = brain_manager
        self.brain_enabled = brain_manager is not None and BRAIN_AVAILABLE

    def map_input(self, raw_input: str) -> dict:
        """
        The Core Function. Maps a string to a concept using tiered resolution.

        Tiers:
        0. Analyst Brain (HIGHEST priority - user memory wins) - confidence: 1.00
        1. Explicit Alias (high priority) - confidence: 0.95
        2. Exact Label Match - confidence: 0.90
        3. Keyword/Partial Match - confidence: 0.70
        4. Safe Mode Hierarchy Fallback - confidence: 0.50-0.70 (depth-dependent)
        5. Unmapped (error) - confidence: 0.00

        Returns a dict with result metadata including confidence score.
        """
        norm_input = self._normalize(raw_input)

        # Tier 0: Analyst Brain (BYOB) - User memory has HIGHEST priority
        if self.brain_enabled and self.brain_manager:
            brain_mapping = self.brain_manager.get_mapping(raw_input)
            if brain_mapping:
                # Validate that the target exists in our taxonomy
                if brain_mapping in self.reverse_id_map:
                    # Calculate confidence
                    confidence, confidence_explanation = self._calculate_confidence(
                        "Analyst Brain (User Memory)",
                        MappingSource.ANALYST_BRAIN if CONFIDENCE_ENGINE_AVAILABLE else None,
                        0
                    )
                    return {
                        "input": raw_input,
                        "found": True,
                        "element_id": brain_mapping,
                        "source": "BRAIN",
                        "concept_id": self.reverse_id_map[brain_mapping],
                        "method": "Analyst Brain (User Memory)",
                        "mapping_source": MappingSource.ANALYST_BRAIN if CONFIDENCE_ENGINE_AVAILABLE else None,
                        "confidence": confidence,
                        "confidence_explanation": confidence_explanation
                    }

        # Tier 1 & 2: Exact Match (alias or standard label)
        if norm_input in self.lookup_index:
            match = self.lookup_index[norm_input]
            # Determine mapping source based on method
            mapping_source = None
            if CONFIDENCE_ENGINE_AVAILABLE:
                if match["source"] == "ALIAS":
                    mapping_source = MappingSource.ALIAS
                else:
                    mapping_source = MappingSource.EXACT_LABEL

            confidence, confidence_explanation = self._calculate_confidence(
                match["method"],
                mapping_source,
                0
            )
            return {
                "input": raw_input,
                "found": True,
                "element_id": match["element_id"],
                "source": match["source"],
                "concept_id": match["concept_id"],
                "method": match["method"],
                "mapping_source": mapping_source,
                "confidence": confidence,
                "confidence_explanation": confidence_explanation
            }

        # Tier 3: Keyword/Partial Match
        partial_match = self._try_partial_match(raw_input)
        if partial_match:
            mapping_source = MappingSource.KEYWORD if CONFIDENCE_ENGINE_AVAILABLE else None
            confidence, confidence_explanation = self._calculate_confidence(
                partial_match["method"],
                mapping_source,
                0
            )
            return {
                "input": raw_input,
                "found": True,
                "element_id": partial_match["element_id"],
                "source": partial_match["source"],
                "concept_id": partial_match["concept_id"],
                "method": partial_match["method"],
                "mapping_source": mapping_source,
                "confidence": confidence,
                "confidence_explanation": confidence_explanation
            }

        # Tier 4: Safe Mode - Walk up hierarchy
        if self.safe_mode_enabled:
            # Try to find if the input contains any known element_id
            for element_id in self.reverse_id_map.keys():
                # Check if element_id name (after prefix) matches
                concept_name = element_id.split('_', 1)[-1] if '_' in element_id else element_id
                if self._normalize(concept_name) in norm_input or norm_input in self._normalize(concept_name):
                    safe_parent = self._find_safe_parent(element_id)
                    if safe_parent:
                        parent_id, depth, path = safe_parent
                        mapping_source = MappingSource.HIERARCHY if CONFIDENCE_ENGINE_AVAILABLE else None
                        method = f"Safe Parent Fallback (depth={depth})"
                        confidence, confidence_explanation = self._calculate_confidence(
                            method,
                            mapping_source,
                            depth
                        )
                        return {
                            "input": raw_input,
                            "found": True,
                            "element_id": parent_id,
                            "source": "US_GAAP",
                            "concept_id": self.reverse_id_map.get(parent_id),
                            "method": method,
                            "mapping_source": mapping_source,
                            "fallback_path": " -> ".join(path),
                            "confidence": confidence,
                            "confidence_explanation": confidence_explanation
                        }

        # Tier 5: Unmapped
        mapping_source = MappingSource.UNMAPPED if CONFIDENCE_ENGINE_AVAILABLE else None
        confidence, confidence_explanation = self._calculate_confidence(
            "Unmapped",
            mapping_source,
            0
        )
        return {
            "input": raw_input,
            "found": False,
            "element_id": None,
            "source": None,
            "concept_id": None,
            "method": "Unmapped",
            "mapping_source": mapping_source,
            "confidence": confidence,
            "confidence_explanation": confidence_explanation
        }

    def _calculate_confidence(self, method: str, mapping_source: Optional['MappingSource'], depth: int) -> Tuple[float, str]:
        """
        Calculate confidence score for a mapping.

        Args:
            method: Mapping method description
            mapping_source: MappingSource enum (if available)
            depth: Hierarchy depth (for fallback mappings)

        Returns:
            Tuple of (confidence_score, explanation)
        """
        if CONFIDENCE_ENGINE_AVAILABLE:
            return calculate_mapping_confidence(method, mapping_source, depth)
        else:
            # Fallback if confidence engine not available
            return (1.0, "Confidence engine not available")

    def get_concept_metadata(self, concept_id: str) -> dict:
        """Get full metadata for a concept from the database."""
        if not concept_id or not self.conn:
            return {"balance": None, "period_type": None, "data_type": None}

        cur = self.conn.cursor()
        cur.execute("""
            SELECT balance, period_type, data_type
            FROM concepts
            WHERE concept_id = ?
        """, (concept_id,))
        row = cur.fetchone()

        if row:
            return {
                "balance": row['balance'],
                "period_type": row['period_type'],
                "data_type": row['data_type']
            }
        return {"balance": None, "period_type": None, "data_type": None}

    def get_standard_label(self, concept_id: str) -> Optional[str]:
        """Get the standard label for a concept."""
        if not concept_id or not self.conn:
            return None

        cur = self.conn.cursor()
        cur.execute("""
            SELECT label_text
            FROM labels
            WHERE concept_id = ? AND label_role = 'standard'
            LIMIT 1
        """, (concept_id,))
        row = cur.fetchone()
        return row['label_text'] if row else None


# -------------------------------------------------
# RUNNER
# -------------------------------------------------
def main():
    print("="*60)
    print("ENHANCED DETERMINISTIC FINANCIAL MAPPER (STAGE 2)")
    print("="*60)

    # 1. Initialize
    mapper = FinancialMapper(DB_PATH, ALIAS_PATH)
    try:
        mapper.connect()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return

    # 2. Test Inputs (Simulating a messy CSV header)
    test_inputs = [
        # Exact matches
        "Assets",
        "Current Assets",
        "Revenues",
        # Alias matches
        "Total Revenue",
        "Sales",
        # Keyword matches
        "Product Revenue",
        "Service Costs",
        "R&D Expense",
        "SG&A",
        # Safe mode candidates
        "iPhone Revenue",
        "Apple Product Sales",
        "Cloud Services Revenue",
        # Should fail
        "Mystery Account 123",
        # Normalization test
        "  liabilities  "
    ]

    print("\nMapping Test Batch:")
    print("-" * 120)
    print(f"{'INPUT':<30} | {'STATUS':<10} | {'METHOD':<30} | {'MAPPED ID'}")
    print("-" * 120)

    for txt in test_inputs:
        res = mapper.map_input(txt)
        status = "MATCH" if res["found"] else "MISS"
        mapped_id = res["element_id"] if res["element_id"] else "---"
        method = res["method"][:28] if res["method"] else "---"
        print(f"{res['input']:<30} | {status:<10} | {method:<30} | {mapped_id}")

    print("-" * 120)
    print(f"\nMatched: {sum(1 for t in test_inputs if mapper.map_input(t)['found'])}/{len(test_inputs)}")

if __name__ == "__main__":
    main()

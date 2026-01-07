#!/usr/bin/env python3
"""
Stage 2: ENHANCED Deterministic Financial Mapper - PRODUCTION v4.0
===================================================================
This is the ENHANCED version with proper taxonomy database utilization.

NEW in V4.0:
- Tier 2.5: Fuzzy Taxonomy Label Search across ALL 24,388 labels
- Multi-role label matching (standard, terse, verbose, total, net, etc.)
- Confidence scoring for matches
- Better XBRL concept resolution

Resolution Order:
  0. Analyst Brain (user's JSON memory) -> HIGHEST priority
  1. Alias Lookup (config/aliases.csv) -> High priority overrides
  2. Exact Label Match (DB Reverse Index) -> Official taxonomy labels
  2.5. FUZZY TAXONOMY LABEL SEARCH -> NEW! Searches all label types
  3. Keyword Matching -> Fallback for common patterns
  4. SAFE MODE: Hierarchy Fallback -> Walk up presentation tree
  5. Fallback: Unmapped (Error)

Philosophy: "Maximize taxonomy utilization - use all 24,388 labels!"
"""
import sqlite3
import csv
import os
import sys
from typing import Dict, Optional, Tuple, List, Set
from difflib import SequenceMatcher

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import Brain Manager
try:
    from utils.brain_manager import BrainManager, get_brain_manager
    BRAIN_AVAILABLE = True
except ImportError:
    BRAIN_AVAILABLE = False

# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "output", "taxonomy_2025.db")
ALIAS_PATH = os.path.join(BASE_DIR, "config", "aliases.csv")

# Safe Parent Concepts
SAFE_PARENT_CONCEPTS = {
    "us-gaap_Revenues", "us-gaap_SalesRevenueNet", "ifrs-full_Revenue",
    "us-gaap_CostOfRevenue", "us-gaap_CostOfGoodsAndServicesSold",
    "us-gaap_OperatingExpenses", "us-gaap_SellingGeneralAndAdministrativeExpense",
    "us-gaap_ResearchAndDevelopmentExpense",
    "us-gaap_Assets", "us-gaap_AssetsCurrent", "us-gaap_AssetsNoncurrent",
    "us-gaap_CashAndCashEquivalentsAtCarryingValue",
    "us-gaap_AccountsReceivableNetCurrent", "us-gaap_InventoryNet",
    "us-gaap_PropertyPlantAndEquipmentNet",
    "us-gaap_Liabilities", "us-gaap_LiabilitiesCurrent", "us-gaap_LiabilitiesNoncurrent",
    "us-gaap_AccountsPayableCurrent", "us-gaap_LongTermDebt",
    "us-gaap_StockholdersEquity", "us-gaap_RetainedEarningsAccumulatedDeficit",
    "us-gaap_NetCashProvidedByUsedInOperatingActivities",
    "us-gaap_PaymentsToAcquirePropertyPlantAndEquipment",
    "us-gaap_NetIncomeLoss",
    "us-gaap_DepreciationDepletionAndAmortization",
    "us-gaap_InterestExpense", "us-gaap_IncomeTaxExpenseBenefit",
}


class EnhancedFinancialMapper:
    """
    Enhanced Financial Mapper with proper taxonomy database utilization.

    NEW: Uses fuzzy label search across all 24,388 taxonomy labels
    instead of relying on hardcoded keyword mappings.
    """

    def __init__(self, db_path: str, alias_path: str, brain_manager: 'BrainManager' = None):
        self.db_path = db_path
        self.alias_path = alias_path
        self.conn = None

        # Memory Indexes
        self.lookup_index: Dict[str, dict] = {}
        self.reverse_id_map: Dict[str, str] = {}
        self.presentation_parents: Dict[str, List[str]] = {}
        self.safe_mode_enabled = True

        # BYOB Integration
        self.brain_manager = brain_manager
        self.brain_enabled = brain_manager is not None and BRAIN_AVAILABLE

        # Statistics
        self.stats = {
            'tier_0_brain': 0,
            'tier_1_alias': 0,
            'tier_2_exact': 0,
            'tier_2_5_fuzzy_taxonomy': 0,
            'tier_3_keyword': 0,
            'tier_4_hierarchy': 0,
            'tier_5_unmapped': 0
        }

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

    def _similarity_score(self, a: str, b: str) -> float:
        """Calculate string similarity score (0.0 to 1.0)."""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def _load_reverse_id_map(self):
        """Cache element_id -> concept_id for fast alias resolution."""
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
        """Tier 1: Load aliases from CSV."""
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

                if target_element_id not in self.reverse_id_map:
                    continue

                concept_id = self.reverse_id_map[target_element_id]
                norm_alias = self._normalize(alias)

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
        print("  Loading Presentation Hierarchy (Tier 4 - Safe Mode)...")
        cur = self.conn.cursor()

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

    # =========================================================================
    # NEW: TIER 2.5 - FUZZY TAXONOMY LABEL SEARCH
    # =========================================================================

    def _search_taxonomy_labels(self, raw_input: str) -> Optional[dict]:
        """
        NEW in V4.0: Search all taxonomy labels with fuzzy matching.

        Searches across ALL label roles:
        - standard, terse, verbose
        - total, net, gross
        - period start, period end
        - positive, negative, negated

        Returns best match with confidence score.
        """
        if not self.conn:
            return None

        norm_input = self._normalize(raw_input)

        if len(norm_input) < 3:
            return None

        cur = self.conn.cursor()

        # Search strategy: progressively broader searches with confidence scores
        search_queries = [
            # Query 1: Exact match (highest confidence)
            ("""
                SELECT
                    c.element_id,
                    c.concept_id,
                    c.source,
                    l.label_text,
                    l.label_role,
                    100 as confidence
                FROM concepts c
                JOIN labels l ON c.concept_id = l.concept_id
                WHERE LOWER(l.label_text) = ?
                LIMIT 1
            """, (norm_input,)),

            # Query 2: Starts with (high confidence)
            ("""
                SELECT
                    c.element_id,
                    c.concept_id,
                    c.source,
                    l.label_text,
                    l.label_role,
                    90 as confidence
                FROM concepts c
                JOIN labels l ON c.concept_id = l.concept_id
                WHERE LOWER(l.label_text) LIKE ?
                AND l.label_role IN ('standard', 'total', 'net')
                ORDER BY LENGTH(l.label_text) ASC
                LIMIT 5
            """, (f"{norm_input}%",)),

            # Query 3: Contains (medium confidence)
            ("""
                SELECT
                    c.element_id,
                    c.concept_id,
                    c.source,
                    l.label_text,
                    l.label_role,
                    70 as confidence
                FROM concepts c
                JOIN labels l ON c.concept_id = l.concept_id
                WHERE LOWER(l.label_text) LIKE ?
                AND l.label_role IN ('standard', 'terse', 'total', 'net')
                ORDER BY LENGTH(l.label_text) ASC
                LIMIT 10
            """, (f"%{norm_input}%",)),

            # Query 4: Word-based fuzzy matching (lower confidence)
            ("""
                SELECT
                    c.element_id,
                    c.concept_id,
                    c.source,
                    l.label_text,
                    l.label_role,
                    50 as confidence
                FROM concepts c
                JOIN labels l ON c.concept_id = l.concept_id
                WHERE {}
                AND l.label_role IN ('standard', 'terse', 'total')
                LIMIT 15
            """.format(" OR ".join([f"LOWER(l.label_text) LIKE '%{word}%'"
                                     for word in norm_input.split() if len(word) > 2])),
             None)
        ]

        all_results = []

        for query, params in search_queries:
            try:
                if params:
                    cur.execute(query, params)
                else:
                    cur.execute(query)

                results = cur.fetchall()
                all_results.extend(results)

                # If we have a high-confidence exact match, return immediately
                if results and results[0][5] == 100:
                    break

            except Exception as e:
                continue

        if not all_results:
            return None

        # Calculate additional similarity scores for ranking
        scored_results = []
        for row in all_results:
            element_id = row[0]
            concept_id = row[1]
            source = row[2]
            label_text = row[3]
            label_role = row[4]
            base_confidence = row[5]

            # Calculate string similarity
            similarity = self._similarity_score(raw_input, label_text)

            # Adjust confidence based on label role
            role_boost = {
                'standard': 10,
                'total': 8,
                'net': 7,
                'terse': 5,
                'verbose': 3
            }.get(label_role, 0)

            # Final score
            final_score = base_confidence * 0.7 + similarity * 100 * 0.2 + role_boost

            scored_results.append((element_id, concept_id, source, label_text, label_role, final_score))

        # Sort by score and return best match
        scored_results.sort(key=lambda x: x[5], reverse=True)
        best_match = scored_results[0]

        return {
            "concept_id": best_match[1],
            "element_id": best_match[0],
            "source": best_match[2],
            "method": f"Fuzzy Taxonomy ({best_match[4]}, conf={int(best_match[5])})",
            "match_text": best_match[3],
            "confidence": best_match[5]
        }

    # =========================================================================
    # MAPPING LOGIC
    # =========================================================================

    def _find_safe_parent(self, element_id: str, max_depth: int = 5) -> Optional[Tuple[str, int, List[str]]]:
        """Walk up the presentation hierarchy to find a valid safe parent."""
        visited = set()
        queue = [(element_id, 0, [element_id])]

        while queue:
            current, depth, path = queue.pop(0)

            if depth > max_depth:
                continue

            if current in visited:
                continue
            visited.add(current)

            if current in SAFE_PARENT_CONCEPTS and current != element_id:
                return (current, depth, path)

            parents = self.presentation_parents.get(current, [])
            for parent in parents:
                if parent not in visited:
                    queue.append((parent, depth + 1, path + [parent]))

        return None

    def _try_keyword_fallback(self, raw_input: str) -> Optional[dict]:
        """
        LEGACY Tier 3: Keyword matching fallback.
        This is now only used if fuzzy taxonomy search fails.
        """
        norm_input = self._normalize(raw_input)

        # Simple keyword mappings (much smaller than before)
        keyword_map = {
            'revenue': 'us-gaap_Revenues',
            'sales': 'us-gaap_Revenues',
            'cost of': 'us-gaap_CostOfRevenue',
            'cogs': 'us-gaap_CostOfRevenue',
            'net income': 'us-gaap_NetIncomeLoss',
            'cash': 'us-gaap_CashAndCashEquivalentsAtCarryingValue',
            'assets': 'us-gaap_Assets',
            'liabilities': 'us-gaap_Liabilities',
        }

        for keyword, element_id in keyword_map.items():
            if keyword in norm_input:
                if element_id in self.reverse_id_map:
                    return {
                        "concept_id": self.reverse_id_map[element_id],
                        "element_id": element_id,
                        "source": "US_GAAP",
                        "method": f"Keyword Fallback ({keyword})",
                        "match_text": raw_input
                    }

        return None

    def set_brain_manager(self, brain_manager: 'BrainManager'):
        """Set or update the brain manager for BYOB integration."""
        self.brain_manager = brain_manager
        self.brain_enabled = brain_manager is not None and BRAIN_AVAILABLE

    def map_input(self, raw_input: str) -> dict:
        """
        Core mapping function with enhanced taxonomy utilization.

        NEW Tier 2.5: Fuzzy Taxonomy Label Search!

        Tiers:
        0. Analyst Brain (HIGHEST priority)
        1. Explicit Alias
        2. Exact Label Match
        2.5. FUZZY TAXONOMY LABEL SEARCH (NEW!)
        3. Keyword Fallback
        4. Safe Mode Hierarchy
        5. Unmapped
        """
        norm_input = self._normalize(raw_input)

        # Tier 0: Analyst Brain
        if self.brain_enabled and self.brain_manager:
            brain_mapping = self.brain_manager.get_mapping(raw_input)
            if brain_mapping and brain_mapping in self.reverse_id_map:
                self.stats['tier_0_brain'] += 1
                return {
                    "input": raw_input,
                    "found": True,
                    "element_id": brain_mapping,
                    "source": "BRAIN",
                    "concept_id": self.reverse_id_map[brain_mapping],
                    "method": "Analyst Brain (User Memory)"
                }

        # Tier 1 & 2: Exact Match
        if norm_input in self.lookup_index:
            match = self.lookup_index[norm_input]
            if match['method'] == 'Explicit Alias':
                self.stats['tier_1_alias'] += 1
            else:
                self.stats['tier_2_exact'] += 1
            return {
                "input": raw_input,
                "found": True,
                "element_id": match["element_id"],
                "source": match["source"],
                "concept_id": match["concept_id"],
                "method": match["method"]
            }

        # Tier 2.5: NEW! FUZZY TAXONOMY LABEL SEARCH
        taxonomy_match = self._search_taxonomy_labels(raw_input)
        if taxonomy_match:
            self.stats['tier_2_5_fuzzy_taxonomy'] += 1
            return {
                "input": raw_input,
                "found": True,
                "element_id": taxonomy_match["element_id"],
                "source": taxonomy_match["source"],
                "concept_id": taxonomy_match["concept_id"],
                "method": taxonomy_match["method"],
                "confidence": taxonomy_match.get("confidence", 0)
            }

        # Tier 3: Keyword Fallback
        keyword_match = self._try_keyword_fallback(raw_input)
        if keyword_match:
            self.stats['tier_3_keyword'] += 1
            return {
                "input": raw_input,
                "found": True,
                "element_id": keyword_match["element_id"],
                "source": keyword_match["source"],
                "concept_id": keyword_match["concept_id"],
                "method": keyword_match["method"]
            }

        # Tier 4: Safe Mode Hierarchy
        if self.safe_mode_enabled:
            for element_id in self.reverse_id_map.keys():
                concept_name = element_id.split('_', 1)[-1] if '_' in element_id else element_id
                if self._normalize(concept_name) in norm_input or norm_input in self._normalize(concept_name):
                    safe_parent = self._find_safe_parent(element_id)
                    if safe_parent:
                        parent_id, depth, path = safe_parent
                        self.stats['tier_4_hierarchy'] += 1
                        return {
                            "input": raw_input,
                            "found": True,
                            "element_id": parent_id,
                            "source": "US_GAAP",
                            "concept_id": self.reverse_id_map.get(parent_id),
                            "method": f"Safe Parent Fallback (depth={depth})",
                            "fallback_path": " -> ".join(path)
                        }

        # Tier 5: Unmapped
        self.stats['tier_5_unmapped'] += 1
        return {
            "input": raw_input,
            "found": False,
            "element_id": None,
            "source": None,
            "concept_id": None,
            "method": "Unmapped"
        }

    def get_concept_metadata(self, concept_id: str) -> dict:
        """Get full metadata for a concept."""
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

    def get_mapping_stats(self) -> dict:
        """Get statistics on which tiers are being used."""
        total = sum(self.stats.values())
        if total == 0:
            return self.stats

        return {
            **self.stats,
            'total_mapped': total,
            'tier_0_pct': round(self.stats['tier_0_brain'] / total * 100, 1) if total > 0 else 0,
            'tier_1_pct': round(self.stats['tier_1_alias'] / total * 100, 1) if total > 0 else 0,
            'tier_2_pct': round(self.stats['tier_2_exact'] / total * 100, 1) if total > 0 else 0,
            'tier_2_5_pct': round(self.stats['tier_2_5_fuzzy_taxonomy'] / total * 100, 1) if total > 0 else 0,
            'tier_3_pct': round(self.stats['tier_3_keyword'] / total * 100, 1) if total > 0 else 0,
            'tier_4_pct': round(self.stats['tier_4_hierarchy'] / total * 100, 1) if total > 0 else 0,
            'tier_5_pct': round(self.stats['tier_5_unmapped'] / total * 100, 1) if total > 0 else 0,
        }


# -------------------------------------------------
# BACKWARDS COMPATIBILITY
# -------------------------------------------------
# So existing code can use the new mapper without changes
FinancialMapper = EnhancedFinancialMapper


# -------------------------------------------------
# TEST RUNNER
# -------------------------------------------------
def main():
    print("="*60)
    print("ENHANCED FINANCIAL MAPPER v4.0 - TEST")
    print("="*60)

    mapper = EnhancedFinancialMapper(DB_PATH, ALIAS_PATH)
    try:
        mapper.connect()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return

    # Test Inputs
    test_inputs = [
        # Exact matches
        "Revenues",
        "Assets",
        # Should match with fuzzy taxonomy search
        "Total Net Sales Revenue",
        "Net Sales",
        "Product Revenue",
        "Service Revenue",
        "Total Operating Expenses",
        "Research and Development",
        "Cash and Equivalents",
        "Accounts Receivable",
        "Property and Equipment",
        "Long-term Debt",
        # Edge cases
        "Revenue from Products",
        "Cost of Goods Sold",
        "Selling, General & Admin",
        # Should still work with keyword fallback
        "Sales",
        "COGS",
        # Mystery (should fail)
        "Mystery Account 123",
    ]

    print("\nMapping Test Batch:")
    print("-" * 130)
    print(f"{'INPUT':<40} | {'STATUS':<10} | {'METHOD':<45} | {'MAPPED ID'}")
    print("-" * 130)

    for txt in test_inputs:
        res = mapper.map_input(txt)
        status = "✅ MATCH" if res["found"] else "❌ MISS"
        mapped_id = res["element_id"] if res["element_id"] else "---"
        method = res["method"][:43] if res["method"] else "---"
        print(f"{res['input']:<40} | {status:<10} | {method:<45} | {mapped_id}")

    print("-" * 130)

    # Statistics
    stats = mapper.get_mapping_stats()
    print(f"\nMapping Statistics:")
    print(f"  Total Mapped: {stats['total_mapped']}")
    print(f"  Tier 0 (Brain):           {stats['tier_0_brain']} ({stats['tier_0_pct']}%)")
    print(f"  Tier 1 (Alias):           {stats['tier_1_alias']} ({stats['tier_1_pct']}%)")
    print(f"  Tier 2 (Exact Label):     {stats['tier_2_exact']} ({stats['tier_2_pct']}%)")
    print(f"  Tier 2.5 (Fuzzy Taxonomy): {stats['tier_2_5_fuzzy_taxonomy']} ({stats['tier_2_5_pct']}%) ⭐ NEW!")
    print(f"  Tier 3 (Keyword):         {stats['tier_3_keyword']} ({stats['tier_3_pct']}%)")
    print(f"  Tier 4 (Hierarchy):       {stats['tier_4_hierarchy']} ({stats['tier_4_pct']}%)")
    print(f"  Tier 5 (Unmapped):        {stats['tier_5_unmapped']} ({stats['tier_5_pct']}%)")
    print(f"\n  Success Rate: {100 - stats['tier_5_pct']:.1f}%")


if __name__ == "__main__":
    main()

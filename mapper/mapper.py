#!/usr/bin/env python3
"""
Stage 2: Deterministic Financial Mapper
=======================================
This script acts as the "Compiler Frontend". It maps messy input strings
to canonical XBRL concept IDs using a strict, tiered resolution strategy.

Resolution Order:
  1. Alias Lookup (config/aliases.csv) -> High priority overrides
  2. Exact Label Match (DB Reverse Index) -> Official taxonomy labels
  3. Fallback: Unmapped (Error)

It DOES NOT use fuzzy matching, ML, or embeddings. 
It ensures 100% traceability to a specific rule or standard.
"""
import sqlite3
import csv
import os
import sys
from typing import Dict, Optional, Tuple, List

# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "output", "taxonomy_2025.db")
ALIAS_PATH = os.path.join(BASE_DIR, "config", "aliases.csv")

class FinancialMapper:
    def __init__(self, db_path: str, alias_path: str):
        self.db_path = db_path
        self.alias_path = alias_path
        self.conn = None
        
        # Memory Indexes
        # { "normalized_string": { "concept_id": "...", "source": "...", "method": "..." } }
        self.lookup_index: Dict[str, dict] = {} 
        self.reverse_id_map: Dict[str, str] = {} # element_id -> concept_id

    def connect(self):
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        # Load data immediately upon connection
        self._load_reverse_id_map()
        self._load_db_labels()
        self._load_aliases()

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
        for eid, cid in cur.fetchall():
            self.reverse_id_map[eid] = cid
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
        for label, cid, eid, source in cur.fetchall():
            norm_label = self._normalize(label)
            # Only add if not already present (collisions favor first entry, or explicit alias later)
            if norm_label not in self.lookup_index:
                self.lookup_index[norm_label] = {
                    "concept_id": cid,
                    "element_id": eid,
                    "source": source,
                    "method": "Standard Label",
                    "match_text": label
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

    def map_input(self, raw_input: str) -> dict:
        """
        The Core Function. Maps a string to a concept.
        Returns a dict with result metadata.
        """
        norm_input = self._normalize(raw_input)
        
        if norm_input in self.lookup_index:
            match = self.lookup_index[norm_input]
            return {
                "input": raw_input,
                "found": True,
                "element_id": match["element_id"],
                "source": match["source"],
                "concept_id": match["concept_id"],
                "method": match["method"]
            }
        
        return {
            "input": raw_input,
            "found": False,
            "element_id": None,
            "source": None,
            "concept_id": None,
            "method": "Unmapped"
        }

# -------------------------------------------------
# RUNNER
# -------------------------------------------------
def main():
    print("="*60)
    print("DETERMINISTIC FINANCIAL MAPPER (STAGE 2)")
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
        "Assets",                   # Exact match US GAAP
        "Current Assets",           # Exact match US GAAP
        "Cash",                     # Alias -> CashAndCashEquivalents
        "Total Revenue",            # Alias -> Revenues
        "Sales",                    # Alias -> Revenues
        "Profit for the year",      # Alias -> IFRS ProfitLoss
        "Mystery Account 123",      # Should Fail
        "  liabilities  "           # Case/Whitespace normalization
    ]

    print("\nMapping Test Batch:")
    print("-" * 100)
    print(f"{'INPUT':<25} | {'STATUS':<10} | {'METHOD':<15} | {'MAPPED ID'}")
    print("-" * 100)

    for txt in test_inputs:
        res = mapper.map_input(txt)
        status = "✅ MATCH" if res["found"] else "❌ MISS"
        mapped_id = res["element_id"] if res["element_id"] else "---"
        print(f"{res['input']:<25} | {status:<10} | {res['method']:<15} | {mapped_id}")

    print("-" * 100)

if __name__ == "__main__":
    main()
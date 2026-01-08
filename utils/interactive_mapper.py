#!/usr/bin/env python3
"""
Interactive Mapping Helper - User-Assisted Mapping System
==========================================================
This module provides interactive mapping assistance when automatic mapping fails.

Core Principles:
1. NEVER block the pipeline - always ask user for help
2. Save all user mappings to brain JSON for future use
3. Provide intelligent suggestions from taxonomy
4. Handle critical metrics first (Revenue, CapEx, EBITDA, etc.)
5. Gracefully degrade for non-critical items

Flow:
1. Detect unmapped items after normalization
2. Identify critical vs non-critical unmapped items
3. For critical items: Prompt user with suggestions
4. Save mappings to brain JSON
5. Re-run normalization with updated brain
6. Repeat until all critical items mapped or user skips
"""

import os
import sys
from typing import Dict, List, Tuple, Optional, Set
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.brain_manager import BrainManager
from config.ib_rules import (
    REVENUE_TOTAL_IDS, CAPEX_IDS,
    COGS_TOTAL_IDS, TOTAL_ASSETS_IDS, TOTAL_LIABILITIES_IDS,
    CASH_IDS, D_AND_A_IDS, NET_INCOME_IDS,
    fuzzy_match_bucket
)


# Critical metrics that must be mapped for DCF/LBO/Comps
# Note: EBITDA is a calculated metric (Net Income + Interest + Tax + D&A), not directly mapped
CRITICAL_BUCKETS = {
    "Revenue": REVENUE_TOTAL_IDS,
    "CapEx": CAPEX_IDS,
    "COGS": COGS_TOTAL_IDS,
    "Cash": CASH_IDS,
    "D&A": D_AND_A_IDS,
    "Net Income": NET_INCOME_IDS,
}


class InteractiveMapper:
    """
    Provides interactive mapping assistance for unmapped financial items.
    """

    def __init__(self, brain_manager: BrainManager, mapper, taxonomy_db_path: str):
        """
        Initialize the interactive mapper.

        Args:
            brain_manager: BrainManager instance to save mappings
            mapper: FinancialMapper instance for suggestions
            taxonomy_db_path: Path to taxonomy database for searching
        """
        self.brain = brain_manager
        self.mapper = mapper
        self.taxonomy_db_path = taxonomy_db_path

    def detect_unmapped_items(self, normalized_df: pd.DataFrame) -> List[Dict]:
        """
        Detect unmapped items from normalized financials.

        Args:
            normalized_df: DataFrame with normalized financials

        Returns:
            List of unmapped items with metadata
        """
        unmapped = normalized_df[normalized_df['Status'] == 'UNMAPPED'].copy()

        unmapped_items = []
        for _, row in unmapped.iterrows():
            unmapped_items.append({
                'source_label': row['Source_Label'],
                'source_amount': row.get('Source_Amount', ''),
                'statement': row.get('Statement_Source', ''),
                'period': row.get('Period_Date', ''),
            })

        return unmapped_items

    def classify_unmapped_items(self, unmapped_items: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Classify unmapped items as critical or non-critical.

        Args:
            unmapped_items: List of unmapped items

        Returns:
            Dict with 'critical' and 'non_critical' lists
        """
        critical = []
        non_critical = []

        for item in unmapped_items:
            label = item['source_label'].lower()

            # Check if label contains keywords for critical buckets
            is_critical = False
            matched_bucket = None

            for bucket_name, bucket_ids in CRITICAL_BUCKETS.items():
                # Try fuzzy match to see if this could be in a critical bucket
                fuzzy_result = fuzzy_match_bucket(label)
                if fuzzy_result and fuzzy_result in bucket_ids:
                    is_critical = True
                    matched_bucket = bucket_name
                    break

            if is_critical:
                item['suggested_bucket'] = matched_bucket
                critical.append(item)
            else:
                non_critical.append(item)

        return {
            'critical': critical,
            'non_critical': non_critical
        }

    def get_suggestions(self, source_label: str, top_n: int = 5) -> List[Dict]:
        """
        Get mapping suggestions for a source label.

        Args:
            source_label: The unmapped label
            top_n: Number of suggestions to return

        Returns:
            List of suggestion dicts with element_id, standard_label, and score
        """
        import sqlite3

        suggestions = []

        # Try fuzzy match first
        fuzzy_concept = fuzzy_match_bucket(source_label)
        if fuzzy_concept:
            suggestions.append({
                'element_id': fuzzy_concept,
                'method': 'Fuzzy Keyword Match',
                'score': 0.70
            })

        # Search taxonomy database for similar labels
        try:
            conn = sqlite3.connect(self.taxonomy_db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # Extract keywords from source label
            keywords = source_label.lower().split()
            keywords = [k for k in keywords if len(k) > 3]  # Filter short words

            if keywords:
                # Build LIKE query for each keyword
                like_conditions = " OR ".join([f"LOWER(l.label_text) LIKE ?" for _ in keywords])
                like_params = [f"%{k}%" for k in keywords]

                query = f"""
                    SELECT DISTINCT c.element_id, l.label_text, c.source
                    FROM labels l
                    JOIN concepts c ON l.concept_id = c.concept_id
                    WHERE l.label_role = 'standard'
                    AND ({like_conditions})
                    LIMIT {top_n * 2}
                """

                cur.execute(query, like_params)
                rows = cur.fetchall()

                for row in rows:
                    # Calculate simple score based on keyword matches
                    label_text = row['label_text'].lower()
                    matches = sum(1 for k in keywords if k in label_text)
                    score = min(0.85, 0.50 + (matches * 0.10))

                    suggestions.append({
                        'element_id': row['element_id'],
                        'standard_label': row['label_text'],
                        'taxonomy': row['source'],
                        'method': 'Taxonomy Search',
                        'score': score
                    })

            conn.close()

        except Exception as e:
            print(f"Warning: Could not search taxonomy: {e}")

        # Sort by score and return top N
        suggestions.sort(key=lambda x: x.get('score', 0), reverse=True)
        return suggestions[:top_n]

    def prompt_user_mapping(self, item: Dict, suggestions: List[Dict]) -> Optional[str]:
        """
        Prompt user to map an item (CLI version).

        Args:
            item: Unmapped item dict
            suggestions: List of suggested mappings

        Returns:
            Selected element_id or None if skipped
        """
        print(f"\n{'='*70}")
        print(f"UNMAPPED ITEM: {item['source_label']}")
        print(f"{'='*70}")
        print(f"Amount: {item.get('source_amount', 'N/A')}")
        print(f"Statement: {item.get('statement', 'N/A')}")
        print(f"Period: {item.get('period', 'N/A')}")

        if item.get('suggested_bucket'):
            print(f"Likely Category: {item['suggested_bucket']}")

        print(f"\nSuggested Mappings:")
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                element_id = suggestion['element_id']
                label = suggestion.get('standard_label', element_id)
                method = suggestion.get('method', 'Unknown')
                score = suggestion.get('score', 0)
                print(f"  [{i}] {element_id}")
                print(f"      Label: {label}")
                print(f"      Method: {method} (confidence: {score:.2f})")
                print()
        else:
            print("  No suggestions available.")

        print(f"\nOptions:")
        print(f"  1-{len(suggestions)}: Select a suggestion")
        print(f"  'custom': Enter custom element ID (e.g., us-gaap_Revenues)")
        print(f"  'skip': Skip this item (non-critical)")
        print(f"  'quit': Stop mapping and proceed with current mappings")

        while True:
            choice = input(f"\nYour choice: ").strip().lower()

            if choice == 'skip':
                return None
            elif choice == 'quit':
                return 'QUIT'
            elif choice == 'custom':
                custom_id = input("Enter element ID (e.g., us-gaap_Revenues): ").strip()
                if custom_id:
                    return custom_id
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(suggestions):
                    return suggestions[idx]['element_id']
                else:
                    print(f"Invalid selection. Choose 1-{len(suggestions)}.")
            else:
                print("Invalid choice. Please try again.")

    def add_mapping_to_brain(self, source_label: str, element_id: str, notes: str = ""):
        """
        Add a user mapping to the brain and save.

        Args:
            source_label: The source label
            element_id: The target element ID
            notes: Optional notes
        """
        self.brain.add_mapping(
            source_label=source_label,
            target_element_id=element_id,
            source_taxonomy="US_GAAP",
            confidence=1.0,  # User mappings always have max confidence
            notes=notes
        )
        print(f"  ✓ Saved mapping: '{source_label}' → {element_id}")

    def run_interactive_session(
        self,
        unmapped_items: List[Dict],
        brain_save_path: str,
        auto_mode: bool = False
    ) -> Tuple[int, bool]:
        """
        Run interactive mapping session for unmapped items.

        Args:
            unmapped_items: List of unmapped items
            brain_save_path: Path to save brain JSON
            auto_mode: If True, skip user prompts (for testing)

        Returns:
            Tuple of (num_mapped, should_rerun)
        """
        if not unmapped_items:
            return 0, False

        # Classify items
        classified = self.classify_unmapped_items(unmapped_items)
        critical = classified['critical']
        non_critical = classified['non_critical']

        print(f"\n{'='*70}")
        print(f"UNMAPPED ITEMS DETECTED")
        print(f"{'='*70}")
        print(f"Critical items (required for DCF/LBO): {len(critical)}")
        print(f"Non-critical items: {len(non_critical)}")
        print(f"\nThe pipeline needs your help to map critical items.")
        print(f"Your mappings will be saved to: {brain_save_path}")
        print(f"{'='*70}")

        if auto_mode:
            print("\nAuto mode enabled - skipping interactive mapping.")
            return 0, False

        num_mapped = 0
        should_quit = False

        # Handle critical items first
        for item in critical:
            if should_quit:
                break

            suggestions = self.get_suggestions(item['source_label'])
            selected = self.prompt_user_mapping(item, suggestions)

            if selected == 'QUIT':
                should_quit = True
                break
            elif selected:
                self.add_mapping_to_brain(
                    source_label=item['source_label'],
                    element_id=selected,
                    notes=f"User mapping for critical item: {item.get('suggested_bucket', 'Unknown')}"
                )
                num_mapped += 1

        # Ask about non-critical items
        if not should_quit and non_critical:
            print(f"\n{'='*70}")
            map_non_critical = input(
                f"\nMap {len(non_critical)} non-critical items? (y/n): "
            ).strip().lower()

            if map_non_critical == 'y':
                for item in non_critical:
                    if should_quit:
                        break

                    suggestions = self.get_suggestions(item['source_label'])
                    selected = self.prompt_user_mapping(item, suggestions)

                    if selected == 'QUIT':
                        should_quit = True
                        break
                    elif selected:
                        self.add_mapping_to_brain(
                            source_label=item['source_label'],
                            element_id=selected,
                            notes="User mapping for non-critical item"
                        )
                        num_mapped += 1

        # Save brain
        if num_mapped > 0:
            success = self.brain.save_to_file(brain_save_path)
            if success:
                print(f"\n✓ Saved {num_mapped} mappings to {brain_save_path}")
                return num_mapped, True  # Should rerun normalization
            else:
                print(f"\n✗ Failed to save brain file")
                return num_mapped, False
        else:
            print(f"\nNo new mappings added.")
            return 0, False


def create_default_brain_if_missing(brain_path: str, aliases_path: str) -> BrainManager:
    """
    Create a default brain file if it doesn't exist.

    Args:
        brain_path: Path to brain JSON file
        aliases_path: Path to aliases CSV

    Returns:
        BrainManager instance
    """
    from utils.brain_manager import load_brain_and_merge, BrainManager

    if not os.path.exists(brain_path):
        print(f"Creating new analyst brain at: {brain_path}")
        brain = BrainManager(aliases_path)
        brain.metadata.owner = "Analyst"
        brain.metadata.company = "FinanceX User"
        brain.save_to_file(brain_path)
    else:
        brain = load_brain_and_merge(brain_path, aliases_path)

    return brain

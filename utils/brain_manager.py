#!/usr/bin/env python3
"""
Brain Manager - Analyst Brain (BYOB Architecture)
==================================================
Implements "Bring Your Own Brain" portable JSON memory system for FinanceX.

The Analyst Brain is a JSON file that contains:
1. User-defined mapping corrections (overrides default aliases)
2. Custom synonyms and aliases learned from user input
3. Validation preferences and thresholds
4. Session history and audit trail

ARCHITECTURE:
- No database required
- Portable JSON file that travels with the analyst
- Merges with default aliases (user memory always wins)
- Can be uploaded, modified, and downloaded

Usage:
    brain = BrainManager()
    brain.load_from_file("analyst_brain.json")  # Optional
    brain.add_mapping("My Custom Label", "us-gaap_Revenues")
    brain.save_to_file("updated_brain.json")
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import csv


@dataclass
class MappingEntry:
    """A single mapping entry in the brain."""
    source_label: str
    target_element_id: str
    source_taxonomy: str = "US_GAAP"
    confidence: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    created_by: str = "user"
    notes: str = ""


@dataclass
class BrainMetadata:
    """Metadata about the brain file."""
    version: str = "1.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())
    owner: str = "anonymous"
    company: str = ""
    total_mappings: int = 0
    total_validations: int = 0


@dataclass
class ValidationPreference:
    """User preference for validation thresholds."""
    check_name: str
    severity_override: str = ""  # "ignore", "warning", "critical"
    threshold_override: float = 0.0
    enabled: bool = True


class BrainManager:
    """
    Manages the Analyst Brain - a portable JSON memory for mapping corrections.

    The brain contains:
    - Custom mappings: User-defined label -> element_id mappings
    - Validation preferences: Custom thresholds and overrides
    - Session history: Audit trail of changes

    Features:
    - Merge with default aliases (brain always wins on conflicts)
    - Export updated brain for portability
    - Learn from user corrections during session
    """

    def __init__(self, default_aliases_path: str = None):
        """
        Initialize the Brain Manager.

        Args:
            default_aliases_path: Path to default aliases.csv file
        """
        self.metadata = BrainMetadata()
        self.mappings: Dict[str, MappingEntry] = {}
        self.validation_preferences: Dict[str, ValidationPreference] = {}
        self.session_history: List[Dict[str, Any]] = []
        self.default_aliases_path = default_aliases_path

        # Merged view (defaults + user brain)
        self._merged_mappings: Dict[str, str] = {}

    def load_from_file(self, file_path: str) -> bool:
        """
        Load brain from a JSON file.

        Args:
            file_path: Path to the brain JSON file

        Returns:
            bool: True if loaded successfully
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Load metadata
            if 'metadata' in data:
                meta = data['metadata']
                self.metadata = BrainMetadata(
                    version=meta.get('version', '1.0'),
                    created_at=meta.get('created_at', datetime.now().isoformat()),
                    last_modified=meta.get('last_modified', datetime.now().isoformat()),
                    owner=meta.get('owner', 'anonymous'),
                    company=meta.get('company', ''),
                    total_mappings=meta.get('total_mappings', 0),
                    total_validations=meta.get('total_validations', 0)
                )

            # Load mappings
            if 'mappings' in data:
                for key, entry in data['mappings'].items():
                    self.mappings[key] = MappingEntry(
                        source_label=entry.get('source_label', key),
                        target_element_id=entry.get('target_element_id', ''),
                        source_taxonomy=entry.get('source_taxonomy', 'US_GAAP'),
                        confidence=entry.get('confidence', 1.0),
                        created_at=entry.get('created_at', datetime.now().isoformat()),
                        created_by=entry.get('created_by', 'user'),
                        notes=entry.get('notes', '')
                    )

            # Load validation preferences
            if 'validation_preferences' in data:
                for key, pref in data['validation_preferences'].items():
                    self.validation_preferences[key] = ValidationPreference(
                        check_name=pref.get('check_name', key),
                        severity_override=pref.get('severity_override', ''),
                        threshold_override=pref.get('threshold_override', 0.0),
                        enabled=pref.get('enabled', True)
                    )

            # Load session history
            if 'session_history' in data:
                self.session_history = data['session_history']

            self._rebuild_merged_mappings()
            return True

        except FileNotFoundError:
            return False
        except json.JSONDecodeError as e:
            print(f"Error parsing brain file: {e}")
            return False
        except Exception as e:
            print(f"Error loading brain: {e}")
            return False

    def load_from_json_string(self, json_string: str) -> bool:
        """
        Load brain from a JSON string (for upload handling).

        Args:
            json_string: JSON string containing brain data

        Returns:
            bool: True if loaded successfully
        """
        try:
            data = json.loads(json_string)
            # Create temp file and load
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(data, f)
                temp_path = f.name

            result = self.load_from_file(temp_path)
            os.unlink(temp_path)
            return result

        except Exception as e:
            print(f"Error loading brain from string: {e}")
            return False

    def save_to_file(self, file_path: str) -> bool:
        """
        Save brain to a JSON file.

        Args:
            file_path: Path to save the brain

        Returns:
            bool: True if saved successfully
        """
        try:
            self.metadata.last_modified = datetime.now().isoformat()
            self.metadata.total_mappings = len(self.mappings)
            self.metadata.total_validations = len(self.validation_preferences)

            data = {
                'metadata': asdict(self.metadata),
                'mappings': {k: asdict(v) for k, v in self.mappings.items()},
                'validation_preferences': {k: asdict(v) for k, v in self.validation_preferences.items()},
                'session_history': self.session_history[-100:]  # Keep last 100 entries
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error saving brain: {e}")
            return False

    def to_json_string(self) -> str:
        """
        Export brain as JSON string (for download).

        Returns:
            str: JSON string of the brain
        """
        self.metadata.last_modified = datetime.now().isoformat()
        self.metadata.total_mappings = len(self.mappings)
        self.metadata.total_validations = len(self.validation_preferences)

        data = {
            'metadata': asdict(self.metadata),
            'mappings': {k: asdict(v) for k, v in self.mappings.items()},
            'validation_preferences': {k: asdict(v) for k, v in self.validation_preferences.items()},
            'session_history': self.session_history[-100:]
        }

        return json.dumps(data, indent=2, ensure_ascii=False)

    def add_mapping(self, source_label: str, target_element_id: str,
                    source_taxonomy: str = "US_GAAP", confidence: float = 1.0,
                    notes: str = "") -> bool:
        """
        Add or update a mapping in the brain.

        Args:
            source_label: The original label from the user's data
            target_element_id: The XBRL element ID to map to
            source_taxonomy: US_GAAP or IFRS
            confidence: Confidence score (0-1)
            notes: Optional notes about the mapping

        Returns:
            bool: True if added successfully
        """
        key = source_label.lower().strip()

        entry = MappingEntry(
            source_label=source_label,
            target_element_id=target_element_id,
            source_taxonomy=source_taxonomy,
            confidence=confidence,
            created_at=datetime.now().isoformat(),
            created_by="user",
            notes=notes
        )

        self.mappings[key] = entry

        # Add to session history
        self.session_history.append({
            'action': 'add_mapping',
            'timestamp': datetime.now().isoformat(),
            'source_label': source_label,
            'target_element_id': target_element_id
        })

        self._rebuild_merged_mappings()
        return True

    def remove_mapping(self, source_label: str) -> bool:
        """
        Remove a mapping from the brain.

        Args:
            source_label: The label to remove

        Returns:
            bool: True if removed
        """
        key = source_label.lower().strip()

        if key in self.mappings:
            del self.mappings[key]

            self.session_history.append({
                'action': 'remove_mapping',
                'timestamp': datetime.now().isoformat(),
                'source_label': source_label
            })

            self._rebuild_merged_mappings()
            return True

        return False

    def get_mapping(self, source_label: str) -> Optional[str]:
        """
        Get the target element ID for a source label.

        Checks user brain first, then falls back to defaults.

        Args:
            source_label: The label to look up

        Returns:
            Optional[str]: The target element ID or None
        """
        key = source_label.lower().strip()
        return self._merged_mappings.get(key)

    def has_mapping(self, source_label: str) -> bool:
        """Check if a mapping exists for a source label."""
        key = source_label.lower().strip()
        return key in self._merged_mappings

    def get_all_user_mappings(self) -> Dict[str, MappingEntry]:
        """Get all user-defined mappings."""
        return self.mappings.copy()

    def get_merged_mappings(self) -> Dict[str, str]:
        """Get the merged view of all mappings (defaults + user)."""
        return self._merged_mappings.copy()

    def _rebuild_merged_mappings(self):
        """
        Rebuild the merged mappings view.

        Order of precedence:
        1. User brain mappings (highest priority)
        2. Default aliases from aliases.csv
        """
        self._merged_mappings = {}

        # Load defaults first
        if self.default_aliases_path and os.path.exists(self.default_aliases_path):
            try:
                with open(self.default_aliases_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader, None)  # Skip header
                    for row in reader:
                        if len(row) >= 3:
                            source_taxonomy, alias, element_id = row[0], row[1], row[2]
                            key = alias.lower().strip()
                            self._merged_mappings[key] = element_id
            except Exception as e:
                print(f"Warning: Could not load default aliases: {e}")

        # User mappings override defaults
        for key, entry in self.mappings.items():
            self._merged_mappings[key] = entry.target_element_id

    def set_validation_preference(self, check_name: str, severity_override: str = "",
                                   threshold_override: float = 0.0, enabled: bool = True):
        """
        Set a validation preference.

        Args:
            check_name: Name of the validation check
            severity_override: "ignore", "warning", or "critical"
            threshold_override: Custom threshold value
            enabled: Whether the check is enabled
        """
        self.validation_preferences[check_name] = ValidationPreference(
            check_name=check_name,
            severity_override=severity_override,
            threshold_override=threshold_override,
            enabled=enabled
        )

        self.session_history.append({
            'action': 'set_validation',
            'timestamp': datetime.now().isoformat(),
            'check_name': check_name,
            'enabled': enabled
        })

    def get_validation_preference(self, check_name: str) -> Optional[ValidationPreference]:
        """Get validation preference for a check."""
        return self.validation_preferences.get(check_name)

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about the current session."""
        return {
            'total_user_mappings': len(self.mappings),
            'total_merged_mappings': len(self._merged_mappings),
            'validation_preferences': len(self.validation_preferences),
            'session_actions': len(self.session_history),
            'last_modified': self.metadata.last_modified,
            'owner': self.metadata.owner,
            'company': self.metadata.company
        }

    def set_owner(self, owner: str, company: str = ""):
        """Set the owner and company for this brain."""
        self.metadata.owner = owner
        self.metadata.company = company

    def create_empty_brain(self) -> str:
        """
        Create a new empty brain file template.

        Returns:
            str: JSON string of empty brain
        """
        empty_brain = BrainManager()
        empty_brain.metadata = BrainMetadata(
            version="1.0",
            created_at=datetime.now().isoformat(),
            last_modified=datetime.now().isoformat(),
            owner="New Analyst",
            company="",
            total_mappings=0,
            total_validations=0
        )
        return empty_brain.to_json_string()

    def learn_from_correction(self, source_label: str, corrected_element_id: str,
                               original_element_id: str = None):
        """
        Learn from a user correction (used during interactive fixing).

        Args:
            source_label: The label that was corrected
            corrected_element_id: The correct element ID
            original_element_id: The original (wrong) element ID
        """
        self.add_mapping(
            source_label=source_label,
            target_element_id=corrected_element_id,
            notes=f"Corrected from {original_element_id}" if original_element_id else "User correction"
        )

        self.session_history.append({
            'action': 'learn_correction',
            'timestamp': datetime.now().isoformat(),
            'source_label': source_label,
            'from': original_element_id,
            'to': corrected_element_id
        })

    def export_to_aliases_csv(self, output_path: str) -> bool:
        """
        Export user mappings to aliases.csv format for backup.

        Args:
            output_path: Path to save the CSV

        Returns:
            bool: True if exported successfully
        """
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['source', 'alias', 'element_id'])

                for key, entry in self.mappings.items():
                    writer.writerow([
                        entry.source_taxonomy,
                        entry.source_label,
                        entry.target_element_id
                    ])

            return True
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False


# Singleton instance for easy access
_brain_instance: Optional[BrainManager] = None


def get_brain_manager(default_aliases_path: str = None) -> BrainManager:
    """
    Get the singleton BrainManager instance.

    Args:
        default_aliases_path: Path to default aliases.csv

    Returns:
        BrainManager: The singleton instance
    """
    global _brain_instance

    if _brain_instance is None:
        _brain_instance = BrainManager(default_aliases_path)

    return _brain_instance


def reset_brain_manager():
    """Reset the singleton instance (for testing)."""
    global _brain_instance
    _brain_instance = None

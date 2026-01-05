#!/usr/bin/env python3
"""
Command Engine - FinanceX Conversational CLI
=============================================
Deterministic command parser and executor for the Analyst Workstation.

Architecture:
1. Load base_commands (Hardcoded from config/base_commands.py)
2. Load user_commands (From analyst_brain.json)
3. Merge them (User overrides Base)
4. Parse input against regex patterns
5. Execute backend actions

NO LLM. 100% Regex-based. Local execution only.
"""

import re
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict

# Import base commands
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.base_commands import (
    get_all_base_commands,
    get_commands_by_category,
    get_backend_actions,
    get_action_names,
    BACKEND_ACTIONS
)


@dataclass
class CommandDefinition:
    """Schema for a command definition."""
    intent_id: str
    canonical_phrase: str
    regex_pattern: str
    backend_action: str
    fixed_params: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    created_by: str = "system"
    is_user_defined: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommandDefinition":
        return cls(
            intent_id=data.get("intent_id", ""),
            canonical_phrase=data.get("canonical_phrase", ""),
            regex_pattern=data.get("regex_pattern", ""),
            backend_action=data.get("backend_action", ""),
            fixed_params=data.get("fixed_params", {}),
            created_at=data.get("created_at", datetime.now().isoformat()),
            created_by=data.get("created_by", "user"),
            is_user_defined=data.get("is_user_defined", True)
        )


@dataclass
class ParseResult:
    """Result of parsing a user command."""
    success: bool
    intent_id: Optional[str] = None
    backend_action: Optional[str] = None
    extracted_params: Dict[str, Any] = field(default_factory=dict)
    fixed_params: Dict[str, Any] = field(default_factory=dict)
    canonical_phrase: Optional[str] = None
    raw_input: str = ""
    error_message: Optional[str] = None
    is_user_defined: bool = False

    def get_all_params(self) -> Dict[str, Any]:
        """Merge fixed and extracted params (extracted wins on conflict)."""
        merged = dict(self.fixed_params)
        merged.update(self.extracted_params)
        return merged


@dataclass
class ExecutionResult:
    """Result of executing a command."""
    success: bool
    action: str
    message: str
    data: Any = None
    requires_refresh: bool = False
    navigate_to: Optional[str] = None
    download_data: Optional[bytes] = None
    download_filename: Optional[str] = None


class CommandEngine:
    """
    The Command Execution Engine for FinanceX.

    Features:
    - Loads ~100 base commands from config
    - Loads user-defined commands from analyst_brain.json
    - Merges commands (user overrides base)
    - Parses input using regex patterns
    - Executes backend actions
    - Supports "Teach Me" learning loop
    """

    def __init__(self, brain_path: Optional[str] = None):
        """
        Initialize the Command Engine.

        Args:
            brain_path: Path to analyst_brain.json for user commands
        """
        self.brain_path = brain_path
        self.base_commands: Dict[str, CommandDefinition] = {}
        self.user_commands: Dict[str, CommandDefinition] = {}
        self.merged_commands: Dict[str, CommandDefinition] = {}
        self.command_history: List[Dict[str, Any]] = []

        # Compiled regex patterns for performance
        self._compiled_patterns: Dict[str, re.Pattern] = {}

        # Load commands
        self._load_base_commands()
        if brain_path:
            self._load_user_commands(brain_path)
        self._merge_commands()

    def _load_base_commands(self):
        """Load base commands from config/base_commands.py."""
        base_list = get_all_base_commands()
        for cmd_data in base_list:
            cmd = CommandDefinition(
                intent_id=cmd_data["intent_id"],
                canonical_phrase=cmd_data["canonical_phrase"],
                regex_pattern=cmd_data["regex_pattern"],
                backend_action=cmd_data["backend_action"],
                fixed_params=cmd_data.get("fixed_params", {}),
                created_by="system",
                is_user_defined=False
            )
            self.base_commands[cmd.intent_id] = cmd

    def _load_user_commands(self, brain_path: str):
        """Load user-defined commands from analyst_brain.json."""
        if not os.path.exists(brain_path):
            return

        try:
            with open(brain_path, 'r', encoding='utf-8') as f:
                brain_data = json.load(f)

            # User commands are stored under "custom_commands" key
            custom_commands = brain_data.get("custom_commands", {})
            for intent_id, cmd_data in custom_commands.items():
                cmd = CommandDefinition.from_dict(cmd_data)
                cmd.is_user_defined = True
                self.user_commands[intent_id] = cmd

        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Warning: Could not load user commands: {e}")

    def _merge_commands(self):
        """Merge base and user commands. User commands override base."""
        self.merged_commands = {}
        self._compiled_patterns = {}

        # Add base commands first
        for intent_id, cmd in self.base_commands.items():
            self.merged_commands[intent_id] = cmd

        # User commands override base
        for intent_id, cmd in self.user_commands.items():
            self.merged_commands[intent_id] = cmd

        # Compile all regex patterns
        for intent_id, cmd in self.merged_commands.items():
            try:
                self._compiled_patterns[intent_id] = re.compile(cmd.regex_pattern)
            except re.error as e:
                print(f"Warning: Invalid regex for {intent_id}: {e}")

    def load_user_commands_from_json(self, json_string: str) -> bool:
        """
        Load user commands from a JSON string.

        Args:
            json_string: JSON string containing brain data

        Returns:
            bool: True if loaded successfully
        """
        try:
            brain_data = json.loads(json_string)
            custom_commands = brain_data.get("custom_commands", {})

            self.user_commands = {}
            for intent_id, cmd_data in custom_commands.items():
                cmd = CommandDefinition.from_dict(cmd_data)
                cmd.is_user_defined = True
                self.user_commands[intent_id] = cmd

            self._merge_commands()
            return True

        except json.JSONDecodeError as e:
            print(f"Error parsing user commands: {e}")
            return False

    def parse(self, user_input: str) -> ParseResult:
        """
        Parse user input and extract command intent.

        Args:
            user_input: Raw user input string

        Returns:
            ParseResult with success=True if matched, False otherwise
        """
        user_input = user_input.strip()

        if not user_input:
            return ParseResult(
                success=False,
                raw_input=user_input,
                error_message="Empty input"
            )

        # Try each pattern in order (user commands checked first via merge)
        for intent_id, pattern in self._compiled_patterns.items():
            match = pattern.match(user_input)
            if match:
                cmd = self.merged_commands[intent_id]

                # Extract named groups from regex
                extracted_params = {
                    k: v for k, v in match.groupdict().items()
                    if v is not None
                }

                return ParseResult(
                    success=True,
                    intent_id=intent_id,
                    backend_action=cmd.backend_action,
                    extracted_params=extracted_params,
                    fixed_params=cmd.fixed_params.copy(),
                    canonical_phrase=cmd.canonical_phrase,
                    raw_input=user_input,
                    is_user_defined=cmd.is_user_defined
                )

        # No match found
        return ParseResult(
            success=False,
            raw_input=user_input,
            error_message="Unknown command"
        )

    def add_user_command(
        self,
        phrase: str,
        backend_action: str,
        params: Dict[str, Any] = None,
        intent_id: str = None
    ) -> Tuple[bool, str, CommandDefinition]:
        """
        Add a new user-defined command (Teach Me flow).

        Args:
            phrase: The natural language phrase (e.g., "Fix tax rate")
            backend_action: The action to execute
            params: Fixed parameters for the action
            intent_id: Optional custom intent ID

        Returns:
            Tuple of (success, message, command_definition)
        """
        params = params or {}

        # Generate intent ID if not provided
        if not intent_id:
            # Create ID from phrase: "Fix tax rate" -> "USER_FIX_TAX_RATE"
            clean_phrase = re.sub(r'[^a-zA-Z0-9\s]', '', phrase)
            intent_id = "USER_" + "_".join(clean_phrase.upper().split())

        # Check for duplicate
        if intent_id in self.user_commands:
            return False, f"Command '{intent_id}' already exists", None

        # Convert phrase to regex pattern
        regex_pattern = self._phrase_to_regex(phrase)

        # Create command definition
        cmd = CommandDefinition(
            intent_id=intent_id,
            canonical_phrase=phrase,
            regex_pattern=regex_pattern,
            backend_action=backend_action,
            fixed_params=params,
            created_by="user",
            is_user_defined=True
        )

        # Add to user commands
        self.user_commands[intent_id] = cmd

        # Re-merge
        self._merge_commands()

        # Log to history
        self.command_history.append({
            "action": "add_command",
            "intent_id": intent_id,
            "phrase": phrase,
            "timestamp": datetime.now().isoformat()
        })

        return True, f"Command '{phrase}' added successfully", cmd

    def _phrase_to_regex(self, phrase: str) -> str:
        """
        Convert a natural phrase to a regex pattern.

        Handles:
        - {placeholder} -> (?P<placeholder>.+?)
        - Case insensitive
        - Flexible whitespace

        Args:
            phrase: Natural language phrase

        Returns:
            Regex pattern string
        """
        # Escape special regex characters (except our placeholders)
        escaped = re.escape(phrase)

        # Convert escaped placeholders back: \{name\} -> (?P<name>.+?)
        pattern = re.sub(
            r'\\{(\w+)\\}',
            r'(?P<\1>.+?)',
            escaped
        )

        # Replace escaped spaces with flexible whitespace
        pattern = pattern.replace(r'\ ', r'\s+')

        # Make case insensitive and anchor
        pattern = f"^(?i){pattern}$"

        return pattern

    def remove_user_command(self, intent_id: str) -> bool:
        """
        Remove a user-defined command.

        Args:
            intent_id: The command ID to remove

        Returns:
            bool: True if removed
        """
        if intent_id in self.user_commands:
            del self.user_commands[intent_id]
            self._merge_commands()

            self.command_history.append({
                "action": "remove_command",
                "intent_id": intent_id,
                "timestamp": datetime.now().isoformat()
            })
            return True

        return False

    def get_user_commands_json(self) -> Dict[str, Any]:
        """
        Export user commands as JSON-serializable dict.

        Returns:
            Dict ready for JSON serialization
        """
        return {
            intent_id: cmd.to_dict()
            for intent_id, cmd in self.user_commands.items()
        }

    def save_to_brain(self, brain_path: str) -> bool:
        """
        Save user commands to analyst_brain.json.

        Args:
            brain_path: Path to brain file

        Returns:
            bool: True if saved successfully
        """
        try:
            # Load existing brain or create new
            brain_data = {}
            if os.path.exists(brain_path):
                with open(brain_path, 'r', encoding='utf-8') as f:
                    brain_data = json.load(f)

            # Add custom commands
            brain_data["custom_commands"] = self.get_user_commands_json()
            brain_data["command_history"] = self.command_history[-100:]

            with open(brain_path, 'w', encoding='utf-8') as f:
                json.dump(brain_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error saving to brain: {e}")
            return False

    def get_all_commands(self) -> List[CommandDefinition]:
        """Get all merged commands."""
        return list(self.merged_commands.values())

    def get_commands_by_action(self, action: str) -> List[CommandDefinition]:
        """Get all commands for a specific backend action."""
        return [
            cmd for cmd in self.merged_commands.values()
            if cmd.backend_action == action
        ]

    def get_similar_commands(self, user_input: str, limit: int = 5) -> List[CommandDefinition]:
        """
        Find commands similar to the input (for suggestions).

        Args:
            user_input: The failed input
            limit: Max suggestions to return

        Returns:
            List of similar command definitions
        """
        user_lower = user_input.lower()
        user_words = set(user_lower.split())

        scored_commands = []
        for cmd in self.merged_commands.values():
            phrase_lower = cmd.canonical_phrase.lower()
            phrase_words = set(phrase_lower.split())

            # Score by word overlap
            common_words = user_words & phrase_words
            score = len(common_words)

            # Bonus for partial matches
            for word in user_words:
                if word in phrase_lower:
                    score += 0.5

            if score > 0:
                scored_commands.append((score, cmd))

        # Sort by score descending
        scored_commands.sort(key=lambda x: x[0], reverse=True)

        return [cmd for _, cmd in scored_commands[:limit]]

    def get_command_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded commands."""
        return {
            "total_commands": len(self.merged_commands),
            "base_commands": len(self.base_commands),
            "user_commands": len(self.user_commands),
            "commands_by_action": self._count_by_action(),
            "history_count": len(self.command_history)
        }

    def _count_by_action(self) -> Dict[str, int]:
        """Count commands by backend action."""
        counts = {}
        for cmd in self.merged_commands.values():
            action = cmd.backend_action
            counts[action] = counts.get(action, 0) + 1
        return counts

    def get_help_text(self, topic: Optional[str] = None) -> str:
        """
        Generate help text for commands.

        Args:
            topic: Optional topic to filter by

        Returns:
            Formatted help text
        """
        if topic:
            # Filter by topic
            topic_lower = topic.lower()
            matching = [
                cmd for cmd in self.merged_commands.values()
                if topic_lower in cmd.canonical_phrase.lower()
                or topic_lower in cmd.backend_action.lower()
            ]
            if matching:
                lines = ["Matching commands:"]
                for cmd in matching[:10]:
                    lines.append(f"  {cmd.canonical_phrase}")
                return "\n".join(lines)
            return f"No commands found for '{topic}'"

        # General help
        categories = get_commands_by_category()
        lines = ["Available command categories:"]
        for category, cmds in categories.items():
            lines.append(f"  {category}: {len(cmds)} commands")
        lines.append("")
        lines.append("Examples:")
        lines.append("  Map Revenue Line to Revenue")
        lines.append("  Show DCF")
        lines.append("  Ignore warning balance sheet")
        lines.append("  Set EBITDA to 500000")
        lines.append("")
        lines.append("Type 'list commands' to see all available commands.")
        return "\n".join(lines)

    def get_examples(self) -> List[str]:
        """Get example commands for each category."""
        examples = []
        categories = get_commands_by_category()
        for category, cmds in categories.items():
            if cmds:
                # Get first command as example
                cmd = cmds[0]
                examples.append(f"{category}: {cmd['canonical_phrase']}")
        return examples


class CommandExecutor:
    """
    Executes parsed commands by calling appropriate backend functions.

    This class bridges the CommandEngine to the actual FinanceX operations.
    """

    def __init__(self, session_state: Any = None):
        """
        Initialize executor with session state.

        Args:
            session_state: Streamlit session state or equivalent
        """
        self.session_state = session_state
        self.action_handlers = self._build_handlers()

    def _build_handlers(self) -> Dict[str, callable]:
        """Build mapping of action names to handler methods."""
        return {
            # Mapping actions
            "update_mapping": self._handle_update_mapping,
            "remove_mapping": self._handle_remove_mapping,

            # Auditing actions
            "ignore_warning": self._handle_ignore_warning,
            "ignore_rule": self._handle_ignore_rule,
            "disable_check": self._handle_disable_check,
            "enable_check": self._handle_enable_check,
            "explain_warning": self._handle_explain_warning,
            "show_warnings": self._handle_show_warnings,
            "show_critical": self._handle_show_critical,
            "show_errors": self._handle_show_errors,
            "show_passed": self._handle_show_passed,

            # Navigation actions
            "navigate_to": self._handle_navigate_to,
            "navigate_to_tab": self._handle_navigate_to_tab,
            "reset_view": self._handle_reset_view,
            "navigate_back": self._handle_navigate_back,
            "refresh_view": self._handle_refresh_view,
            "filter_statement": self._handle_filter_statement,

            # Pipeline actions
            "force_generate": self._handle_force_generate,
            "run_pipeline": self._handle_run_pipeline,
            "run_clean": self._handle_run_clean,
            "rerun_pipeline": self._handle_rerun_pipeline,
            "regenerate_model": self._handle_regenerate_model,
            "recalculate": self._handle_recalculate,
            "clear_session": self._handle_clear_session,
            "new_session": self._handle_new_session,
            "cancel_operation": self._handle_cancel,
            "run_validation": self._handle_run_validation,
            "export_all": self._handle_export_all,

            # Override actions
            "set_override": self._handle_set_override,
            "clear_override": self._handle_clear_override,
            "clear_all_overrides": self._handle_clear_all_overrides,
            "show_overrides": self._handle_show_overrides,
            "undo_override": self._handle_undo_override,

            # Brain actions
            "save_brain": self._handle_save_brain,
            "download_brain": self._handle_download_brain,
            "load_brain": self._handle_load_brain,
            "upload_brain": self._handle_upload_brain,
            "show_brain_status": self._handle_show_brain_status,
            "clear_brain": self._handle_clear_brain,
            "reset_brain": self._handle_reset_brain,
            "export_brain": self._handle_export_brain,
            "show_brain_stats": self._handle_show_brain_stats,
            "list_brain_mappings": self._handle_list_brain_mappings,

            # Search actions
            "search_concepts": self._handle_search_concepts,
            "explain_concept": self._handle_explain_concept,
            "locate_item": self._handle_locate_item,
            "show_concept_details": self._handle_show_concept_details,
            "apply_filter": self._handle_apply_filter,
            "apply_sort": self._handle_apply_sort,
            "clear_filters": self._handle_clear_filters,

            # Help actions
            "show_help": self._handle_show_help,
            "list_commands": self._handle_list_commands,
            "show_examples": self._handle_show_examples,
            "show_howto": self._handle_show_howto,
            "show_version": self._handle_show_version,

            # Export actions
            "export_model": self._handle_export_model,
            "export_audit": self._handle_export_audit,
            "export_normalized": self._handle_export_normalized,

            # Additional auditing
            "list_rules": self._handle_list_rules,
            "list_checks": self._handle_list_checks,
            "suppress_warning": self._handle_suppress_warning,
            "enable_warning": self._handle_enable_warning,
            "accept_warning": self._handle_accept_warning,
            "dismiss_warning": self._handle_dismiss_warning,
            "show_audit_status": self._handle_show_audit_status,
            "run_audit": self._handle_run_audit,
            "recheck_item": self._handle_recheck_item,
        }

    def execute(self, parse_result: ParseResult) -> ExecutionResult:
        """
        Execute a parsed command.

        Args:
            parse_result: The result from CommandEngine.parse()

        Returns:
            ExecutionResult with outcome
        """
        if not parse_result.success:
            return ExecutionResult(
                success=False,
                action="none",
                message=parse_result.error_message or "Parse failed"
            )

        action = parse_result.backend_action
        params = parse_result.get_all_params()

        handler = self.action_handlers.get(action)
        if handler:
            try:
                return handler(params)
            except Exception as e:
                return ExecutionResult(
                    success=False,
                    action=action,
                    message=f"Execution error: {str(e)}"
                )
        else:
            return ExecutionResult(
                success=False,
                action=action,
                message=f"No handler for action: {action}"
            )

    # =========================================================================
    # MAPPING HANDLERS
    # =========================================================================
    def _handle_update_mapping(self, params: Dict) -> ExecutionResult:
        source = params.get("source", "")
        target = params.get("target", "")

        if not source:
            return ExecutionResult(False, "update_mapping", "Missing source label")

        if self.session_state and hasattr(self.session_state, 'brain_manager'):
            brain = self.session_state.brain_manager
            brain.add_mapping(source, target)
            return ExecutionResult(
                success=True,
                action="update_mapping",
                message=f"Mapped '{source}' to '{target}'",
                requires_refresh=True
            )

        return ExecutionResult(True, "update_mapping", f"Mapped '{source}' to '{target}'")

    def _handle_remove_mapping(self, params: Dict) -> ExecutionResult:
        source = params.get("source", "")
        if self.session_state and hasattr(self.session_state, 'brain_manager'):
            self.session_state.brain_manager.remove_mapping(source)
        return ExecutionResult(True, "remove_mapping", f"Removed mapping for '{source}'")

    # =========================================================================
    # AUDITING HANDLERS
    # =========================================================================
    def _handle_ignore_warning(self, params: Dict) -> ExecutionResult:
        rule_name = params.get("rule_name", "")
        if self.session_state and hasattr(self.session_state, 'brain_manager'):
            self.session_state.brain_manager.set_validation_preference(
                rule_name, severity_override="ignore"
            )
        return ExecutionResult(True, "ignore_warning", f"Ignoring warning: {rule_name}")

    def _handle_ignore_rule(self, params: Dict) -> ExecutionResult:
        return self._handle_ignore_warning(params)

    def _handle_disable_check(self, params: Dict) -> ExecutionResult:
        check_name = params.get("check_name", "")
        if self.session_state and hasattr(self.session_state, 'brain_manager'):
            self.session_state.brain_manager.set_validation_preference(
                check_name, enabled=False
            )
        return ExecutionResult(True, "disable_check", f"Disabled check: {check_name}")

    def _handle_enable_check(self, params: Dict) -> ExecutionResult:
        check_name = params.get("check_name", "")
        if self.session_state and hasattr(self.session_state, 'brain_manager'):
            self.session_state.brain_manager.set_validation_preference(
                check_name, enabled=True
            )
        return ExecutionResult(True, "enable_check", f"Enabled check: {check_name}")

    def _handle_explain_warning(self, params: Dict) -> ExecutionResult:
        item = params.get("item", "")
        # Look up explanation in audit report
        explanation = f"Explanation for '{item}': Check the audit results for details."
        return ExecutionResult(True, "explain_warning", explanation)

    def _handle_show_warnings(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="show_warnings",
            message="Showing warnings",
            navigate_to="audit"
        )

    def _handle_show_critical(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="show_critical",
            message="Showing critical issues",
            navigate_to="audit"
        )

    def _handle_show_errors(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="show_errors",
            message="Showing errors",
            navigate_to="audit"
        )

    def _handle_show_passed(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="show_passed",
            message="Showing passed checks",
            navigate_to="audit"
        )

    # =========================================================================
    # NAVIGATION HANDLERS
    # =========================================================================
    def _handle_navigate_to(self, params: Dict) -> ExecutionResult:
        target = params.get("target_view", "home")
        return ExecutionResult(
            success=True,
            action="navigate_to",
            message=f"Navigating to {target}",
            navigate_to=target
        )

    def _handle_navigate_to_tab(self, params: Dict) -> ExecutionResult:
        tab_name = params.get("tab_name", params.get("view", ""))
        return ExecutionResult(
            success=True,
            action="navigate_to_tab",
            message=f"Switching to {tab_name}",
            navigate_to=tab_name.lower()
        )

    def _handle_reset_view(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="reset_view",
            message="View reset",
            navigate_to="home"
        )

    def _handle_navigate_back(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(True, "navigate_back", "Going back")

    def _handle_refresh_view(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(True, "refresh_view", "Refreshing", requires_refresh=True)

    def _handle_filter_statement(self, params: Dict) -> ExecutionResult:
        statement = params.get("statement", "")
        return ExecutionResult(
            success=True,
            action="filter_statement",
            message=f"Filtering by {statement}",
            data={"filter_statement": statement}
        )

    # =========================================================================
    # PIPELINE HANDLERS
    # =========================================================================
    def _handle_force_generate(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="force_generate",
            message="Force generating outputs...",
            data={"trigger": "force_generate"}
        )

    def _handle_run_pipeline(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="run_pipeline",
            message="Running pipeline...",
            data={"trigger": "run_pipeline"}
        )

    def _handle_run_clean(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="run_clean",
            message="Running clean pipeline...",
            data={"trigger": "run_clean"}
        )

    def _handle_rerun_pipeline(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="rerun_pipeline",
            message="Rerunning pipeline...",
            requires_refresh=True
        )

    def _handle_regenerate_model(self, params: Dict) -> ExecutionResult:
        model = params.get("model", "all")
        return ExecutionResult(
            success=True,
            action="regenerate_model",
            message=f"Regenerating {model}...",
            data={"model": model}
        )

    def _handle_recalculate(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="recalculate",
            message="Recalculating all models...",
            requires_refresh=True
        )

    def _handle_clear_session(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="clear_session",
            message="Session cleared",
            data={"trigger": "clear_session"}
        )

    def _handle_new_session(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="new_session",
            message="Starting new session...",
            data={"trigger": "new_session"}
        )

    def _handle_cancel(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(True, "cancel_operation", "Operation cancelled")

    def _handle_run_validation(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="run_validation",
            message="Running validation...",
            data={"trigger": "run_validation"}
        )

    def _handle_export_all(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="export_all",
            message="Exporting all outputs...",
            navigate_to="downloads"
        )

    # =========================================================================
    # OVERRIDE HANDLERS
    # =========================================================================
    def _handle_set_override(self, params: Dict) -> ExecutionResult:
        metric = params.get("metric", "")
        value_str = params.get("value", "0")

        # Parse value (handle commas, negatives)
        try:
            value = float(value_str.replace(",", ""))
        except ValueError:
            return ExecutionResult(False, "set_override", f"Invalid value: {value_str}")

        if self.session_state and hasattr(self.session_state, 'manual_overrides'):
            self.session_state.manual_overrides[metric] = value

        return ExecutionResult(
            success=True,
            action="set_override",
            message=f"Set {metric} = {value:,.2f}",
            requires_refresh=True
        )

    def _handle_clear_override(self, params: Dict) -> ExecutionResult:
        metric = params.get("metric", "")
        if self.session_state and hasattr(self.session_state, 'manual_overrides'):
            self.session_state.manual_overrides.pop(metric, None)
        return ExecutionResult(True, "clear_override", f"Cleared override for {metric}")

    def _handle_clear_all_overrides(self, params: Dict) -> ExecutionResult:
        if self.session_state and hasattr(self.session_state, 'manual_overrides'):
            self.session_state.manual_overrides.clear()
        return ExecutionResult(True, "clear_all_overrides", "All overrides cleared")

    def _handle_show_overrides(self, params: Dict) -> ExecutionResult:
        overrides = {}
        if self.session_state and hasattr(self.session_state, 'manual_overrides'):
            overrides = self.session_state.manual_overrides
        return ExecutionResult(True, "show_overrides", f"Current overrides: {overrides}")

    def _handle_undo_override(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(True, "undo_override", "Last override undone")

    # =========================================================================
    # BRAIN HANDLERS
    # =========================================================================
    def _handle_save_brain(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="save_brain",
            message="Brain saved",
            data={"trigger": "save_brain"}
        )

    def _handle_download_brain(self, params: Dict) -> ExecutionResult:
        if self.session_state and hasattr(self.session_state, 'brain_manager'):
            brain_json = self.session_state.brain_manager.to_json_string()
            return ExecutionResult(
                success=True,
                action="download_brain",
                message="Brain ready for download",
                download_data=brain_json.encode('utf-8'),
                download_filename="analyst_brain.json"
            )
        return ExecutionResult(True, "download_brain", "Download brain")

    def _handle_load_brain(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="load_brain",
            message="Ready to load brain",
            data={"trigger": "load_brain"}
        )

    def _handle_upload_brain(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="upload_brain",
            message="Ready to upload brain",
            data={"trigger": "upload_brain"}
        )

    def _handle_show_brain_status(self, params: Dict) -> ExecutionResult:
        if self.session_state and hasattr(self.session_state, 'brain_manager'):
            stats = self.session_state.brain_manager.get_session_stats()
            return ExecutionResult(True, "show_brain_status", f"Brain status: {stats}")
        return ExecutionResult(True, "show_brain_status", "Brain not loaded")

    def _handle_clear_brain(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="clear_brain",
            message="Brain cleared",
            data={"trigger": "clear_brain"}
        )

    def _handle_reset_brain(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="reset_brain",
            message="Brain reset to defaults",
            data={"trigger": "reset_brain"}
        )

    def _handle_export_brain(self, params: Dict) -> ExecutionResult:
        format_type = params.get("format", "json")
        return ExecutionResult(
            success=True,
            action="export_brain",
            message=f"Exporting brain as {format_type}",
            data={"format": format_type}
        )

    def _handle_show_brain_stats(self, params: Dict) -> ExecutionResult:
        return self._handle_show_brain_status(params)

    def _handle_list_brain_mappings(self, params: Dict) -> ExecutionResult:
        if self.session_state and hasattr(self.session_state, 'brain_manager'):
            mappings = self.session_state.brain_manager.get_all_user_mappings()
            return ExecutionResult(True, "list_brain_mappings", f"{len(mappings)} mappings", data=mappings)
        return ExecutionResult(True, "list_brain_mappings", "No mappings")

    # =========================================================================
    # SEARCH HANDLERS
    # =========================================================================
    def _handle_search_concepts(self, params: Dict) -> ExecutionResult:
        query = params.get("query", "")
        return ExecutionResult(
            success=True,
            action="search_concepts",
            message=f"Searching for '{query}'...",
            data={"query": query, "trigger": "search"}
        )

    def _handle_explain_concept(self, params: Dict) -> ExecutionResult:
        query = params.get("query", "")
        return ExecutionResult(
            success=True,
            action="explain_concept",
            message=f"Looking up '{query}'...",
            data={"query": query}
        )

    def _handle_locate_item(self, params: Dict) -> ExecutionResult:
        query = params.get("query", "")
        return ExecutionResult(True, "locate_item", f"Locating '{query}'...")

    def _handle_show_concept_details(self, params: Dict) -> ExecutionResult:
        concept_id = params.get("concept_id", "")
        return ExecutionResult(True, "show_concept_details", f"Details for {concept_id}")

    def _handle_apply_filter(self, params: Dict) -> ExecutionResult:
        criteria = params.get("criteria", "")
        return ExecutionResult(
            success=True,
            action="apply_filter",
            message=f"Filtering by: {criteria}",
            data={"filter": criteria}
        )

    def _handle_apply_sort(self, params: Dict) -> ExecutionResult:
        column = params.get("column", "")
        order = params.get("order", "asc")
        return ExecutionResult(
            success=True,
            action="apply_sort",
            message=f"Sorting by {column} ({order})",
            data={"sort_column": column, "sort_order": order}
        )

    def _handle_clear_filters(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(True, "clear_filters", "Filters cleared")

    # =========================================================================
    # HELP HANDLERS
    # =========================================================================
    def _handle_show_help(self, params: Dict) -> ExecutionResult:
        topic = params.get("topic", "")
        help_text = f"Help for: {topic}" if topic else "Type 'list commands' to see all commands."
        return ExecutionResult(True, "show_help", help_text)

    def _handle_list_commands(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="list_commands",
            message="Listing all commands...",
            data={"trigger": "list_commands"}
        )

    def _handle_show_examples(self, params: Dict) -> ExecutionResult:
        examples = [
            "Map Sales Revenue to Revenue",
            "Show DCF",
            "Set EBITDA to 500000",
            "Ignore warning balance sheet",
            "Force generate",
            "Download brain"
        ]
        return ExecutionResult(True, "show_examples", "\n".join(examples))

    def _handle_show_howto(self, params: Dict) -> ExecutionResult:
        topic = params.get("topic", "")
        return ExecutionResult(True, "show_howto", f"How to {topic}: See documentation.")

    def _handle_show_version(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(True, "show_version", "FinanceX Command Layer v2.0")

    # =========================================================================
    # EXPORT HANDLERS
    # =========================================================================
    def _handle_export_model(self, params: Dict) -> ExecutionResult:
        model = params.get("model", "dcf")
        format_type = params.get("format", "csv")
        return ExecutionResult(
            success=True,
            action="export_model",
            message=f"Exporting {model} as {format_type}",
            navigate_to="downloads"
        )

    def _handle_export_audit(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="export_audit",
            message="Exporting audit report",
            navigate_to="downloads"
        )

    def _handle_export_normalized(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="export_normalized",
            message="Exporting normalized data",
            navigate_to="downloads"
        )

    # =========================================================================
    # ADDITIONAL AUDITING HANDLERS
    # =========================================================================
    def _handle_list_rules(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(True, "list_rules", "Listing all rules...")

    def _handle_list_checks(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(True, "list_checks", "Listing all checks...")

    def _handle_suppress_warning(self, params: Dict) -> ExecutionResult:
        warning = params.get("warning", "")
        return ExecutionResult(True, "suppress_warning", f"Suppressed: {warning}")

    def _handle_enable_warning(self, params: Dict) -> ExecutionResult:
        warning = params.get("warning", "")
        return ExecutionResult(True, "enable_warning", f"Enabled: {warning}")

    def _handle_accept_warning(self, params: Dict) -> ExecutionResult:
        warning = params.get("warning", "")
        return ExecutionResult(True, "accept_warning", f"Accepted: {warning}")

    def _handle_dismiss_warning(self, params: Dict) -> ExecutionResult:
        warning = params.get("warning", "")
        return ExecutionResult(True, "dismiss_warning", f"Dismissed: {warning}")

    def _handle_show_audit_status(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(True, "show_audit_status", "Showing audit status...")

    def _handle_run_audit(self, params: Dict) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            action="run_audit",
            message="Running full audit...",
            data={"trigger": "run_audit"}
        )

    def _handle_recheck_item(self, params: Dict) -> ExecutionResult:
        item = params.get("item", "")
        return ExecutionResult(True, "recheck_item", f"Rechecking: {item}")


# =============================================================================
# SINGLETON ACCESS
# =============================================================================
_engine_instance: Optional[CommandEngine] = None


def get_command_engine(brain_path: Optional[str] = None) -> CommandEngine:
    """Get or create the singleton CommandEngine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = CommandEngine(brain_path)
    return _engine_instance


def reset_command_engine():
    """Reset the singleton instance."""
    global _engine_instance
    _engine_instance = None

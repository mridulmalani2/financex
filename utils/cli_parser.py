#!/usr/bin/env python3
"""
CLI Parser - FinanceX Chat Command Parser
==========================================
Production V1.0 - Regex-based command parsing for the Analyst Chat Interface.

This module handles parsing of natural language commands typed in the chat,
extracting intents and parameters for execution.

Key Commands Supported:
- "Map 'X' to Y" - Map a label to a taxonomy concept
- "Set Revenue to 100000" - Override a bucket value
- "Show DCF" / "Show Audit" - Navigate to views
- "Download Brain" / "Download Models" - Trigger downloads
- "Ignore warning X" - Dismiss specific warnings
- "Help" / "?" - Show available commands

Philosophy: 100% Regex, No LLM, Deterministic Execution
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ParsedCommand:
    """Result of parsing a chat command."""
    success: bool
    intent: str
    action: str
    params: Dict[str, Any]
    raw_input: str
    error_message: Optional[str] = None
    confidence: float = 1.0

    def __repr__(self):
        if self.success:
            return f"ParsedCommand(intent={self.intent}, action={self.action}, params={self.params})"
        return f"ParsedCommand(FAILED: {self.error_message})"


# =============================================================================
# COMMAND PATTERNS - Core Regex Definitions
# =============================================================================

# Pattern format: (regex_pattern, intent, action, param_names)
COMMAND_PATTERNS: List[Tuple[str, str, str, List[str]]] = [
    # Mapping Commands
    (
        r"^(?:map|assign|set)\s+['\"]?(.+?)['\"]?\s+(?:to|as|->)\s+(.+?)$",
        "MAP_LABEL",
        "map_custom_label",
        ["source_label", "target"]
    ),
    (
        r"^['\"]?(.+?)['\"]?\s+(?:should be|is|means)\s+(.+?)$",
        "MAP_LABEL",
        "map_custom_label",
        ["source_label", "target"]
    ),

    # Value Override Commands
    (
        r"^(?:set|override)\s+(.+?)\s+(?:to|=|:)\s+\$?([\d,\.]+)(?:M|m|MM|mm)?$",
        "SET_VALUE",
        "override_bucket",
        ["bucket", "value"]
    ),
    (
        r"^(.+?)\s+(?:is|=|:)\s+\$?([\d,\.]+)(?:M|m|MM|mm)?$",
        "SET_VALUE",
        "override_bucket",
        ["bucket", "value"]
    ),

    # Navigation Commands
    (
        r"^(?:show|view|go to|open)\s+(.+?)$",
        "NAVIGATE",
        "navigate_to",
        ["destination"]
    ),
    (
        r"^(?:dcf|lbo|comps|audit|data|downloads?|unmapped|home)$",
        "NAVIGATE",
        "navigate_to",
        ["destination"]
    ),

    # Download Commands
    (
        r"^(?:download|export|save)\s+(?:the\s+)?brain$",
        "DOWNLOAD_BRAIN",
        "download_brain",
        []
    ),
    (
        r"^(?:download|export|save)\s+(?:the\s+)?(?:all|package|models?|everything)$",
        "DOWNLOAD_PACKAGE",
        "download_package",
        []
    ),
    (
        r"^(?:download|export|save)\s+(?:the\s+)?(.+?)$",
        "DOWNLOAD_SPECIFIC",
        "download_specific",
        ["file_type"]
    ),

    # Ignore/Dismiss Commands
    (
        r"^(?:ignore|dismiss|skip|hide)\s+(?:warning\s+)?['\"]?(.+?)['\"]?$",
        "IGNORE_WARNING",
        "ignore_warning",
        ["warning_name"]
    ),
    (
        r"^(?:don'?t\s+)?(?:warn|alert)\s+(?:me\s+)?(?:about\s+)?['\"]?(.+?)['\"]?$",
        "IGNORE_WARNING",
        "ignore_warning",
        ["warning_name"]
    ),

    # Help Commands
    (
        r"^(?:help|\?|commands|what can you do)$",
        "HELP",
        "show_help",
        []
    ),
    (
        r"^(?:how\s+(?:do|can)\s+I|what'?s?\s+the\s+command\s+(?:to|for))\s+(.+?)$",
        "HELP_SPECIFIC",
        "show_help_for",
        ["topic"]
    ),

    # Brain/Stats Commands
    (
        r"^(?:show|what'?s?\s+(?:in|my)?)\s+(?:the\s+)?brain(?:\s+stats?)?$",
        "BRAIN_STATS",
        "show_brain_stats",
        []
    ),
    (
        r"^(?:brain\s+)?stats?$",
        "BRAIN_STATS",
        "show_brain_stats",
        []
    ),

    # Undo/Clear Commands
    (
        r"^(?:undo|revert)\s+(?:last\s+)?(?:change|command|mapping)?$",
        "UNDO",
        "undo_last",
        []
    ),
    (
        r"^(?:clear|reset)\s+(?:all\s+)?(?:mappings|overrides|brain)$",
        "CLEAR",
        "clear_session",
        []
    ),

    # Re-run Engine
    (
        r"^(?:re-?run|refresh|recalculate|update)\s*(?:the\s+)?(?:engine|models?)?$",
        "RERUN",
        "rerun_engine",
        []
    ),

    # List Commands
    (
        r"^(?:list|show)\s+(?:all\s+)?(?:mappings|custom\s+mappings|my\s+mappings)$",
        "LIST_MAPPINGS",
        "list_mappings",
        []
    ),
    (
        r"^(?:list|show)\s+(?:all\s+)?(?:commands|available\s+commands)$",
        "LIST_COMMANDS",
        "list_commands",
        []
    ),
]


# =============================================================================
# TARGET RESOLUTION - Map common names to XBRL concepts
# =============================================================================

TARGET_ALIASES: Dict[str, str] = {
    # Revenue
    "revenue": "us-gaap_Revenues",
    "sales": "us-gaap_Revenues",
    "net sales": "us-gaap_Revenues",
    "total revenue": "us-gaap_Revenues",
    "turnover": "us-gaap_Revenues",
    "top line": "us-gaap_Revenues",

    # Net Income
    "net income": "us-gaap_NetIncomeLoss",
    "profit": "us-gaap_NetIncomeLoss",
    "earnings": "us-gaap_NetIncomeLoss",
    "bottom line": "us-gaap_NetIncomeLoss",
    "net profit": "us-gaap_NetIncomeLoss",
    "net earnings": "us-gaap_NetIncomeLoss",

    # COGS
    "cogs": "us-gaap_CostOfGoodsAndServicesSold",
    "cost of goods": "us-gaap_CostOfGoodsAndServicesSold",
    "cost of sales": "us-gaap_CostOfGoodsAndServicesSold",
    "cost of revenue": "us-gaap_CostOfRevenue",

    # Gross Profit
    "gross profit": "us-gaap_GrossProfit",
    "gross margin": "us-gaap_GrossProfit",

    # SG&A
    "sga": "us-gaap_SellingGeneralAndAdministrativeExpense",
    "sg&a": "us-gaap_SellingGeneralAndAdministrativeExpense",
    "operating expenses": "us-gaap_OperatingExpenses",
    "opex": "us-gaap_OperatingExpenses",

    # R&D
    "r&d": "us-gaap_ResearchAndDevelopmentExpense",
    "research": "us-gaap_ResearchAndDevelopmentExpense",
    "r and d": "us-gaap_ResearchAndDevelopmentExpense",

    # D&A
    "d&a": "us-gaap_DepreciationDepletionAndAmortization",
    "depreciation": "us-gaap_DepreciationDepletionAndAmortization",
    "amortization": "us-gaap_DepreciationDepletionAndAmortization",

    # EBITDA
    "ebitda": "CALCULATED_EBITDA",

    # EBIT
    "ebit": "us-gaap_OperatingIncomeLoss",
    "operating income": "us-gaap_OperatingIncomeLoss",

    # Interest
    "interest expense": "us-gaap_InterestExpense",
    "interest income": "us-gaap_InterestIncomeOperating",

    # Taxes
    "taxes": "us-gaap_IncomeTaxExpenseBenefit",
    "tax expense": "us-gaap_IncomeTaxExpenseBenefit",
    "income tax": "us-gaap_IncomeTaxExpenseBenefit",

    # Balance Sheet
    "cash": "us-gaap_CashAndCashEquivalentsAtCarryingValue",
    "inventory": "us-gaap_InventoryNet",
    "receivables": "us-gaap_AccountsReceivableNetCurrent",
    "accounts receivable": "us-gaap_AccountsReceivableNetCurrent",
    "total assets": "us-gaap_Assets",
    "total liabilities": "us-gaap_Liabilities",
    "equity": "us-gaap_StockholdersEquity",
    "debt": "us-gaap_LongTermDebt",
    "long term debt": "us-gaap_LongTermDebtNoncurrent",
    "short term debt": "us-gaap_ShortTermBorrowings",

    # Cash Flow
    "capex": "us-gaap_PaymentsToAcquirePropertyPlantAndEquipment",
    "capital expenditure": "us-gaap_PaymentsToAcquirePropertyPlantAndEquipment",
    "free cash flow": "us-gaap_FreeCashFlow",
    "fcf": "us-gaap_FreeCashFlow",
}


NAVIGATION_ALIASES: Dict[str, str] = {
    "dcf": "dcf",
    "discounted cash flow": "dcf",
    "lbo": "lbo",
    "leveraged buyout": "lbo",
    "comps": "comps",
    "comparables": "comps",
    "trading comps": "comps",
    "audit": "audit",
    "audit results": "audit",
    "audits": "audit",
    "findings": "audit",
    "data": "data",
    "normalized": "data",
    "normalized data": "data",
    "unmapped": "unmapped",
    "fix unmapped": "unmapped",
    "downloads": "downloads",
    "download": "downloads",
    "export": "downloads",
    "home": "home",
    "start": "home",
    "models": "dcf",
    "financial models": "dcf",
}


# =============================================================================
# CHAT PARSER CLASS
# =============================================================================

class ChatParser:
    """
    Parses natural language commands from the chat interface.

    Usage:
        parser = ChatParser()
        result = parser.parse("Map 'Turnover' to Revenue")
        if result.success:
            print(f"Action: {result.action}, Params: {result.params}")
    """

    def __init__(self):
        """Initialize the parser with compiled regex patterns."""
        self.patterns = [
            (re.compile(pattern, re.IGNORECASE), intent, action, param_names)
            for pattern, intent, action, param_names in COMMAND_PATTERNS
        ]
        self.target_aliases = TARGET_ALIASES
        self.nav_aliases = NAVIGATION_ALIASES

    def parse(self, user_input: str) -> ParsedCommand:
        """
        Parse a user command from the chat.

        Args:
            user_input: The raw text input from the user

        Returns:
            ParsedCommand with parsed intent, action, and parameters
        """
        # Clean input
        text = user_input.strip()
        if not text:
            return ParsedCommand(
                success=False,
                intent="",
                action="",
                params={},
                raw_input=user_input,
                error_message="Empty command"
            )

        # Try each pattern
        for regex, intent, action, param_names in self.patterns:
            match = regex.match(text)
            if match:
                # Extract parameters
                params = {}
                groups = match.groups()
                for i, name in enumerate(param_names):
                    if i < len(groups):
                        params[name] = groups[i].strip()

                # Post-process parameters
                params = self._process_params(intent, action, params)

                return ParsedCommand(
                    success=True,
                    intent=intent,
                    action=action,
                    params=params,
                    raw_input=user_input,
                    confidence=1.0
                )

        # No match found
        return ParsedCommand(
            success=False,
            intent="",
            action="",
            params={},
            raw_input=user_input,
            error_message=f"Command not recognized: '{text}'"
        )

    def _process_params(self, intent: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process extracted parameters."""

        # Resolve target aliases for mapping commands
        if intent == "MAP_LABEL" and "target" in params:
            target = params["target"].lower().strip()
            if target in self.target_aliases:
                params["target_element_id"] = self.target_aliases[target]
                params["target_resolved"] = True
            else:
                # Assume it's already an element ID or needs user confirmation
                params["target_element_id"] = target
                params["target_resolved"] = False

        # Resolve navigation aliases
        if intent == "NAVIGATE" and "destination" in params:
            dest = params["destination"].lower().strip()
            if dest in self.nav_aliases:
                params["destination"] = self.nav_aliases[dest]

        # Parse numeric values
        if intent == "SET_VALUE" and "value" in params:
            value_str = params["value"].replace(",", "").replace("$", "")
            try:
                value = float(value_str)
                # Check for M/MM suffix (millions)
                if "m" in user_input.lower() and "mm" not in user_input.lower():
                    value *= 1_000_000
                elif "mm" in user_input.lower():
                    value *= 1_000_000
                params["value"] = value
            except ValueError:
                params["value"] = 0.0

        return params

    def get_help_text(self) -> str:
        """Get help text showing available commands."""
        return """
**Available Commands:**

**Mapping:**
- `Map 'Turnover' to Revenue` - Map a label to a concept
- `'Operating Income' should be EBIT` - Alternative mapping syntax

**Values:**
- `Set Revenue to 100M` - Override a bucket value
- `EBITDA = 50,000,000` - Alternative value syntax

**Navigation:**
- `Show DCF` - View DCF model
- `Show Audit` - View audit results
- `Go to Downloads` - Navigate to downloads

**Downloads:**
- `Download Brain` - Export your analyst brain
- `Download Package` - Get all models + brain

**Other:**
- `Ignore warning X` - Dismiss a warning
- `Re-run engine` - Recalculate models
- `Brain stats` - Show brain statistics
- `Help` - Show this help
        """

    def suggest_command(self, failed_input: str) -> Optional[str]:
        """Suggest a correction for a failed command."""
        lower = failed_input.lower()

        # Common typos and alternatives
        suggestions = {
            "mapping": "Map '{label}' to {target}",
            "set value": "Set {bucket} to {value}",
            "navigate": "Show {destination}",
            "download": "Download {type}",
        }

        for keyword, template in suggestions.items():
            if keyword in lower:
                return f"Did you mean: `{template}`?"

        return None


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Global parser instance
_parser: Optional[ChatParser] = None


def get_chat_parser() -> ChatParser:
    """Get the global ChatParser instance."""
    global _parser
    if _parser is None:
        _parser = ChatParser()
    return _parser


def parse_command(user_input: str) -> ParsedCommand:
    """Parse a command using the global parser."""
    return get_chat_parser().parse(user_input)


def get_help() -> str:
    """Get help text for the chat interface."""
    return get_chat_parser().get_help_text()


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    # Test the parser
    parser = ChatParser()

    test_commands = [
        "Map 'Turnover' to Revenue",
        "Map Operating Income to EBIT",
        "'Net Sales' should be Revenue",
        "Set Revenue to 100M",
        "EBITDA = 50,000,000",
        "Show DCF",
        "Go to Audit",
        "Download Brain",
        "Download Package",
        "Ignore warning zero revenue",
        "Re-run engine",
        "Brain stats",
        "Help",
        "list commands",
        "This is not a command",
    ]

    print("Testing CLI Parser:")
    print("=" * 60)

    for cmd in test_commands:
        result = parser.parse(cmd)
        print(f"\nInput: '{cmd}'")
        print(f"  -> {result}")

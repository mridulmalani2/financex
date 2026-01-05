#!/usr/bin/env python3
"""
Base Commands Library - FinanceX Command Layer
===============================================
Pre-populated vocabulary of ~100 essential commands for the Conversational CLI.

Each command follows the strict schema:
{
    "intent_id": "UNIQUE_ID",
    "canonical_phrase": "Human-readable template with {placeholders}",
    "regex_pattern": "^(?i)regex pattern with (?P<named_groups>.+)$",
    "backend_action": "function_name_to_execute",
    "fixed_params": {"key": "value"}  # Optional static parameters
}

Categories:
1. MAPPING - Map labels to concepts (Map X to Y, Set X as Y)
2. AUDITING - Manage warnings and rules (Ignore, Why, Show)
3. NAVIGATION - View switching (Show DCF, Go to LBO)
4. PIPELINE - Execution control (Force Generate, Run Clean)
5. DATA - Data manipulation (Filter, Sort, Export)
6. BRAIN - Memory management (Save, Load, Clear brain)
7. OVERRIDE - Manual value overrides (Set value, Fix amount)
8. SEARCH - Find items (Find, Search, Lookup)
9. HELP - System assistance (Help, List commands)
"""

from typing import Dict, List, Any

# =============================================================================
# MAPPING COMMANDS (~25 commands)
# =============================================================================
MAPPING_COMMANDS: List[Dict[str, Any]] = [
    {
        "intent_id": "MAP_TO_CONCEPT",
        "canonical_phrase": "Map {source} to {target}",
        "regex_pattern": r"^(?i)map\s+(?P<source>.+?)\s+to\s+(?P<target>.+)$",
        "backend_action": "update_mapping",
        "fixed_params": {}
    },
    {
        "intent_id": "MAP_TO_REVENUE",
        "canonical_phrase": "Map {source} to Revenue",
        "regex_pattern": r"^(?i)map\s+(?P<source>.+?)\s+to\s+revenue$",
        "backend_action": "update_mapping",
        "fixed_params": {"target": "us-gaap_Revenues"}
    },
    {
        "intent_id": "MAP_TO_COGS",
        "canonical_phrase": "Map {source} to COGS",
        "regex_pattern": r"^(?i)map\s+(?P<source>.+?)\s+to\s+(?:cogs|cost\s+of\s+(?:goods\s+)?(?:sold|sales))$",
        "backend_action": "update_mapping",
        "fixed_params": {"target": "us-gaap_CostOfGoodsAndServicesSold"}
    },
    {
        "intent_id": "MAP_TO_EBITDA",
        "canonical_phrase": "Map {source} to EBITDA",
        "regex_pattern": r"^(?i)map\s+(?P<source>.+?)\s+to\s+ebitda$",
        "backend_action": "update_mapping",
        "fixed_params": {"target": "us-gaap_OperatingIncomeLoss"}
    },
    {
        "intent_id": "MAP_TO_NET_INCOME",
        "canonical_phrase": "Map {source} to Net Income",
        "regex_pattern": r"^(?i)map\s+(?P<source>.+?)\s+to\s+net\s+income$",
        "backend_action": "update_mapping",
        "fixed_params": {"target": "us-gaap_NetIncomeLoss"}
    },
    {
        "intent_id": "MAP_TO_ASSETS",
        "canonical_phrase": "Map {source} to Total Assets",
        "regex_pattern": r"^(?i)map\s+(?P<source>.+?)\s+to\s+(?:total\s+)?assets$",
        "backend_action": "update_mapping",
        "fixed_params": {"target": "us-gaap_Assets"}
    },
    {
        "intent_id": "MAP_TO_LIABILITIES",
        "canonical_phrase": "Map {source} to Total Liabilities",
        "regex_pattern": r"^(?i)map\s+(?P<source>.+?)\s+to\s+(?:total\s+)?liabilities$",
        "backend_action": "update_mapping",
        "fixed_params": {"target": "us-gaap_Liabilities"}
    },
    {
        "intent_id": "MAP_TO_EQUITY",
        "canonical_phrase": "Map {source} to Equity",
        "regex_pattern": r"^(?i)map\s+(?P<source>.+?)\s+to\s+(?:total\s+)?(?:stockholders?\s+)?equity$",
        "backend_action": "update_mapping",
        "fixed_params": {"target": "us-gaap_StockholdersEquity"}
    },
    {
        "intent_id": "MAP_TO_CASH",
        "canonical_phrase": "Map {source} to Cash",
        "regex_pattern": r"^(?i)map\s+(?P<source>.+?)\s+to\s+(?:cash|cash\s+and\s+(?:cash\s+)?equivalents)$",
        "backend_action": "update_mapping",
        "fixed_params": {"target": "us-gaap_CashAndCashEquivalentsAtCarryingValue"}
    },
    {
        "intent_id": "MAP_TO_DEBT",
        "canonical_phrase": "Map {source} to Debt",
        "regex_pattern": r"^(?i)map\s+(?P<source>.+?)\s+to\s+(?:total\s+)?debt$",
        "backend_action": "update_mapping",
        "fixed_params": {"target": "us-gaap_LongTermDebt"}
    },
    {
        "intent_id": "MAP_TO_CAPEX",
        "canonical_phrase": "Map {source} to CapEx",
        "regex_pattern": r"^(?i)map\s+(?P<source>.+?)\s+to\s+(?:capex|capital\s+expenditures?)$",
        "backend_action": "update_mapping",
        "fixed_params": {"target": "us-gaap_PaymentsToAcquirePropertyPlantAndEquipment"}
    },
    {
        "intent_id": "MAP_TO_DA",
        "canonical_phrase": "Map {source} to D&A",
        "regex_pattern": r"^(?i)map\s+(?P<source>.+?)\s+to\s+(?:d&a|depreciation(?:\s+and\s+amortization)?)$",
        "backend_action": "update_mapping",
        "fixed_params": {"target": "us-gaap_DepreciationDepletionAndAmortization"}
    },
    {
        "intent_id": "MAP_TO_SGA",
        "canonical_phrase": "Map {source} to SG&A",
        "regex_pattern": r"^(?i)map\s+(?P<source>.+?)\s+to\s+(?:sg&a|selling.+general.+admin)$",
        "backend_action": "update_mapping",
        "fixed_params": {"target": "us-gaap_SellingGeneralAndAdministrativeExpense"}
    },
    {
        "intent_id": "MAP_TO_RD",
        "canonical_phrase": "Map {source} to R&D",
        "regex_pattern": r"^(?i)map\s+(?P<source>.+?)\s+to\s+(?:r&d|research\s+(?:and\s+)?development)$",
        "backend_action": "update_mapping",
        "fixed_params": {"target": "us-gaap_ResearchAndDevelopmentExpense"}
    },
    {
        "intent_id": "MAP_TO_INTEREST",
        "canonical_phrase": "Map {source} to Interest Expense",
        "regex_pattern": r"^(?i)map\s+(?P<source>.+?)\s+to\s+interest(?:\s+expense)?$",
        "backend_action": "update_mapping",
        "fixed_params": {"target": "us-gaap_InterestExpense"}
    },
    {
        "intent_id": "SET_AS_CONCEPT",
        "canonical_phrase": "Set {source} as {target}",
        "regex_pattern": r"^(?i)set\s+(?P<source>.+?)\s+as\s+(?P<target>.+)$",
        "backend_action": "update_mapping",
        "fixed_params": {}
    },
    {
        "intent_id": "DEFINE_IS_CONCEPT",
        "canonical_phrase": "Define {source} is {target}",
        "regex_pattern": r"^(?i)define\s+(?P<source>.+?)\s+(?:is|as|=)\s+(?P<target>.+)$",
        "backend_action": "update_mapping",
        "fixed_params": {}
    },
    {
        "intent_id": "LINK_TO_CONCEPT",
        "canonical_phrase": "Link {source} to {target}",
        "regex_pattern": r"^(?i)link\s+(?P<source>.+?)\s+to\s+(?P<target>.+)$",
        "backend_action": "update_mapping",
        "fixed_params": {}
    },
    {
        "intent_id": "ASSIGN_CONCEPT",
        "canonical_phrase": "Assign {source} to {target}",
        "regex_pattern": r"^(?i)assign\s+(?P<source>.+?)\s+to\s+(?P<target>.+)$",
        "backend_action": "update_mapping",
        "fixed_params": {}
    },
    {
        "intent_id": "CLASSIFY_AS",
        "canonical_phrase": "Classify {source} as {target}",
        "regex_pattern": r"^(?i)classify\s+(?P<source>.+?)\s+as\s+(?P<target>.+)$",
        "backend_action": "update_mapping",
        "fixed_params": {}
    },
    {
        "intent_id": "UNMAP_LABEL",
        "canonical_phrase": "Unmap {source}",
        "regex_pattern": r"^(?i)unmap\s+(?P<source>.+)$",
        "backend_action": "remove_mapping",
        "fixed_params": {}
    },
    {
        "intent_id": "REMOVE_MAPPING",
        "canonical_phrase": "Remove mapping for {source}",
        "regex_pattern": r"^(?i)remove\s+(?:mapping\s+(?:for\s+)?)?(?P<source>.+)$",
        "backend_action": "remove_mapping",
        "fixed_params": {}
    },
    {
        "intent_id": "CLEAR_MAPPING",
        "canonical_phrase": "Clear mapping {source}",
        "regex_pattern": r"^(?i)clear\s+(?:mapping\s+)?(?P<source>.+)$",
        "backend_action": "remove_mapping",
        "fixed_params": {}
    },
    {
        "intent_id": "TREAT_AS",
        "canonical_phrase": "Treat {source} as {target}",
        "regex_pattern": r"^(?i)treat\s+(?P<source>.+?)\s+as\s+(?P<target>.+)$",
        "backend_action": "update_mapping",
        "fixed_params": {}
    },
    {
        "intent_id": "USE_FOR",
        "canonical_phrase": "Use {source} for {target}",
        "regex_pattern": r"^(?i)use\s+(?P<source>.+?)\s+(?:for|as)\s+(?P<target>.+)$",
        "backend_action": "update_mapping",
        "fixed_params": {}
    },
]

# =============================================================================
# AUDITING COMMANDS (~20 commands)
# =============================================================================
AUDITING_COMMANDS: List[Dict[str, Any]] = [
    {
        "intent_id": "IGNORE_WARNING",
        "canonical_phrase": "Ignore warning {rule_name}",
        "regex_pattern": r"^(?i)ignore\s+(?:warning\s+)?(?P<rule_name>.+)$",
        "backend_action": "ignore_warning",
        "fixed_params": {}
    },
    {
        "intent_id": "IGNORE_RULE",
        "canonical_phrase": "Ignore rule {rule_name}",
        "regex_pattern": r"^(?i)ignore\s+rule\s+(?P<rule_name>.+)$",
        "backend_action": "ignore_rule",
        "fixed_params": {}
    },
    {
        "intent_id": "DISABLE_CHECK",
        "canonical_phrase": "Disable check {check_name}",
        "regex_pattern": r"^(?i)disable\s+(?:check\s+)?(?P<check_name>.+)$",
        "backend_action": "disable_check",
        "fixed_params": {}
    },
    {
        "intent_id": "ENABLE_CHECK",
        "canonical_phrase": "Enable check {check_name}",
        "regex_pattern": r"^(?i)enable\s+(?:check\s+)?(?P<check_name>.+)$",
        "backend_action": "enable_check",
        "fixed_params": {}
    },
    {
        "intent_id": "WHY_WARNING",
        "canonical_phrase": "Why {item}",
        "regex_pattern": r"^(?i)why\s+(?P<item>.+)$",
        "backend_action": "explain_warning",
        "fixed_params": {}
    },
    {
        "intent_id": "EXPLAIN_WARNING",
        "canonical_phrase": "Explain {item}",
        "regex_pattern": r"^(?i)explain\s+(?P<item>.+)$",
        "backend_action": "explain_warning",
        "fixed_params": {}
    },
    {
        "intent_id": "SHOW_WARNINGS",
        "canonical_phrase": "Show warnings",
        "regex_pattern": r"^(?i)show\s+warnings?$",
        "backend_action": "show_warnings",
        "fixed_params": {}
    },
    {
        "intent_id": "SHOW_CRITICAL",
        "canonical_phrase": "Show critical",
        "regex_pattern": r"^(?i)show\s+critical(?:\s+(?:errors?|issues?))?$",
        "backend_action": "show_critical",
        "fixed_params": {}
    },
    {
        "intent_id": "SHOW_ERRORS",
        "canonical_phrase": "Show errors",
        "regex_pattern": r"^(?i)show\s+errors?$",
        "backend_action": "show_errors",
        "fixed_params": {}
    },
    {
        "intent_id": "SHOW_PASSED",
        "canonical_phrase": "Show passed",
        "regex_pattern": r"^(?i)show\s+passed(?:\s+checks?)?$",
        "backend_action": "show_passed",
        "fixed_params": {}
    },
    {
        "intent_id": "LIST_RULES",
        "canonical_phrase": "List rules",
        "regex_pattern": r"^(?i)list\s+(?:all\s+)?rules?$",
        "backend_action": "list_rules",
        "fixed_params": {}
    },
    {
        "intent_id": "LIST_CHECKS",
        "canonical_phrase": "List checks",
        "regex_pattern": r"^(?i)list\s+(?:all\s+)?checks?$",
        "backend_action": "list_checks",
        "fixed_params": {}
    },
    {
        "intent_id": "SUPPRESS_WARNING",
        "canonical_phrase": "Suppress {warning}",
        "regex_pattern": r"^(?i)suppress\s+(?P<warning>.+)$",
        "backend_action": "suppress_warning",
        "fixed_params": {}
    },
    {
        "intent_id": "MUTE_WARNING",
        "canonical_phrase": "Mute {warning}",
        "regex_pattern": r"^(?i)mute\s+(?P<warning>.+)$",
        "backend_action": "suppress_warning",
        "fixed_params": {}
    },
    {
        "intent_id": "UNMUTE_WARNING",
        "canonical_phrase": "Unmute {warning}",
        "regex_pattern": r"^(?i)unmute\s+(?P<warning>.+)$",
        "backend_action": "enable_warning",
        "fixed_params": {}
    },
    {
        "intent_id": "ACCEPT_WARNING",
        "canonical_phrase": "Accept {warning}",
        "regex_pattern": r"^(?i)accept\s+(?P<warning>.+)$",
        "backend_action": "accept_warning",
        "fixed_params": {}
    },
    {
        "intent_id": "DISMISS_WARNING",
        "canonical_phrase": "Dismiss {warning}",
        "regex_pattern": r"^(?i)dismiss\s+(?P<warning>.+)$",
        "backend_action": "dismiss_warning",
        "fixed_params": {}
    },
    {
        "intent_id": "AUDIT_STATUS",
        "canonical_phrase": "Audit status",
        "regex_pattern": r"^(?i)(?:show\s+)?audit\s+status$",
        "backend_action": "show_audit_status",
        "fixed_params": {}
    },
    {
        "intent_id": "RUN_AUDIT",
        "canonical_phrase": "Run audit",
        "regex_pattern": r"^(?i)run\s+(?:full\s+)?audit$",
        "backend_action": "run_audit",
        "fixed_params": {}
    },
    {
        "intent_id": "RECHECK",
        "canonical_phrase": "Recheck {item}",
        "regex_pattern": r"^(?i)recheck\s+(?P<item>.+)$",
        "backend_action": "recheck_item",
        "fixed_params": {}
    },
]

# =============================================================================
# NAVIGATION COMMANDS (~15 commands)
# =============================================================================
NAVIGATION_COMMANDS: List[Dict[str, Any]] = [
    {
        "intent_id": "SHOW_DCF",
        "canonical_phrase": "Show DCF",
        "regex_pattern": r"^(?i)(?:show|view|open|go\s+to)\s+dcf(?:\s+(?:model|setup))?$",
        "backend_action": "navigate_to",
        "fixed_params": {"target_view": "dcf"}
    },
    {
        "intent_id": "SHOW_LBO",
        "canonical_phrase": "Show LBO",
        "regex_pattern": r"^(?i)(?:show|view|open|go\s+to)\s+lbo(?:\s+(?:model|stats?))?$",
        "backend_action": "navigate_to",
        "fixed_params": {"target_view": "lbo"}
    },
    {
        "intent_id": "SHOW_COMPS",
        "canonical_phrase": "Show Comps",
        "regex_pattern": r"^(?i)(?:show|view|open|go\s+to)\s+comps?(?:\s+(?:model|metrics?))?$",
        "backend_action": "navigate_to",
        "fixed_params": {"target_view": "comps"}
    },
    {
        "intent_id": "SHOW_DATA",
        "canonical_phrase": "Show data",
        "regex_pattern": r"^(?i)(?:show|view|open)\s+(?:raw\s+)?data$",
        "backend_action": "navigate_to",
        "fixed_params": {"target_view": "data"}
    },
    {
        "intent_id": "SHOW_AUDIT",
        "canonical_phrase": "Show audit",
        "regex_pattern": r"^(?i)(?:show|view|open)\s+audit(?:\s+(?:results?|report))?$",
        "backend_action": "navigate_to",
        "fixed_params": {"target_view": "audit"}
    },
    {
        "intent_id": "SHOW_UNMAPPED",
        "canonical_phrase": "Show unmapped",
        "regex_pattern": r"^(?i)(?:show|view|list)\s+unmapped(?:\s+(?:items?|data))?$",
        "backend_action": "navigate_to",
        "fixed_params": {"target_view": "unmapped"}
    },
    {
        "intent_id": "SHOW_DOWNLOADS",
        "canonical_phrase": "Show downloads",
        "regex_pattern": r"^(?i)(?:show|view|open)\s+downloads?$",
        "backend_action": "navigate_to",
        "fixed_params": {"target_view": "downloads"}
    },
    {
        "intent_id": "GO_TO_TAB",
        "canonical_phrase": "Go to {tab_name}",
        "regex_pattern": r"^(?i)go\s+to\s+(?P<tab_name>.+)$",
        "backend_action": "navigate_to_tab",
        "fixed_params": {}
    },
    {
        "intent_id": "SWITCH_TO",
        "canonical_phrase": "Switch to {view}",
        "regex_pattern": r"^(?i)switch\s+to\s+(?P<view>.+)$",
        "backend_action": "navigate_to_tab",
        "fixed_params": {}
    },
    {
        "intent_id": "RESET_VIEW",
        "canonical_phrase": "Reset",
        "regex_pattern": r"^(?i)reset(?:\s+view)?$",
        "backend_action": "reset_view",
        "fixed_params": {}
    },
    {
        "intent_id": "HOME",
        "canonical_phrase": "Home",
        "regex_pattern": r"^(?i)(?:home|main|start)$",
        "backend_action": "navigate_to",
        "fixed_params": {"target_view": "home"}
    },
    {
        "intent_id": "BACK",
        "canonical_phrase": "Back",
        "regex_pattern": r"^(?i)(?:back|previous|prev)$",
        "backend_action": "navigate_back",
        "fixed_params": {}
    },
    {
        "intent_id": "REFRESH",
        "canonical_phrase": "Refresh",
        "regex_pattern": r"^(?i)refresh(?:\s+(?:view|page|data))?$",
        "backend_action": "refresh_view",
        "fixed_params": {}
    },
    {
        "intent_id": "SHOW_BALANCE_SHEET",
        "canonical_phrase": "Show Balance Sheet",
        "regex_pattern": r"^(?i)(?:show|view)\s+balance\s+sheet$",
        "backend_action": "filter_statement",
        "fixed_params": {"statement": "Balance Sheet"}
    },
    {
        "intent_id": "SHOW_INCOME_STATEMENT",
        "canonical_phrase": "Show Income Statement",
        "regex_pattern": r"^(?i)(?:show|view)\s+(?:income\s+statement|p&l|pnl)$",
        "backend_action": "filter_statement",
        "fixed_params": {"statement": "Income Statement"}
    },
]

# =============================================================================
# PIPELINE COMMANDS (~15 commands)
# =============================================================================
PIPELINE_COMMANDS: List[Dict[str, Any]] = [
    {
        "intent_id": "FORCE_GENERATE",
        "canonical_phrase": "Force generate",
        "regex_pattern": r"^(?i)force\s+generate(?:\s+(?:template|model|output))?$",
        "backend_action": "force_generate",
        "fixed_params": {}
    },
    {
        "intent_id": "RUN_PIPELINE",
        "canonical_phrase": "Run pipeline",
        "regex_pattern": r"^(?i)run\s+(?:the\s+)?pipeline$",
        "backend_action": "run_pipeline",
        "fixed_params": {}
    },
    {
        "intent_id": "RUN_CLEAN",
        "canonical_phrase": "Run clean",
        "regex_pattern": r"^(?i)run\s+clean$",
        "backend_action": "run_clean",
        "fixed_params": {}
    },
    {
        "intent_id": "RERUN",
        "canonical_phrase": "Rerun",
        "regex_pattern": r"^(?i)(?:re-?run|run\s+again)(?:\s+(?:analysis|pipeline))?$",
        "backend_action": "rerun_pipeline",
        "fixed_params": {}
    },
    {
        "intent_id": "PROCESS",
        "canonical_phrase": "Process",
        "regex_pattern": r"^(?i)process(?:\s+(?:data|file))?$",
        "backend_action": "run_pipeline",
        "fixed_params": {}
    },
    {
        "intent_id": "ANALYZE",
        "canonical_phrase": "Analyze",
        "regex_pattern": r"^(?i)analyze(?:\s+(?:data|file))?$",
        "backend_action": "run_pipeline",
        "fixed_params": {}
    },
    {
        "intent_id": "REGENERATE",
        "canonical_phrase": "Regenerate {model}",
        "regex_pattern": r"^(?i)regenerate\s+(?P<model>.+)$",
        "backend_action": "regenerate_model",
        "fixed_params": {}
    },
    {
        "intent_id": "REBUILD",
        "canonical_phrase": "Rebuild {model}",
        "regex_pattern": r"^(?i)rebuild\s+(?P<model>.+)$",
        "backend_action": "regenerate_model",
        "fixed_params": {}
    },
    {
        "intent_id": "RECALCULATE",
        "canonical_phrase": "Recalculate",
        "regex_pattern": r"^(?i)recalculate(?:\s+(?:all|models?))?$",
        "backend_action": "recalculate",
        "fixed_params": {}
    },
    {
        "intent_id": "CLEAR_SESSION",
        "canonical_phrase": "Clear session",
        "regex_pattern": r"^(?i)clear\s+session$",
        "backend_action": "clear_session",
        "fixed_params": {}
    },
    {
        "intent_id": "NEW_SESSION",
        "canonical_phrase": "New session",
        "regex_pattern": r"^(?i)(?:new|start\s+(?:new\s+)?|create\s+)session$",
        "backend_action": "new_session",
        "fixed_params": {}
    },
    {
        "intent_id": "CANCEL",
        "canonical_phrase": "Cancel",
        "regex_pattern": r"^(?i)cancel(?:\s+(?:operation|process))?$",
        "backend_action": "cancel_operation",
        "fixed_params": {}
    },
    {
        "intent_id": "STOP",
        "canonical_phrase": "Stop",
        "regex_pattern": r"^(?i)stop(?:\s+(?:processing|pipeline))?$",
        "backend_action": "cancel_operation",
        "fixed_params": {}
    },
    {
        "intent_id": "VALIDATE",
        "canonical_phrase": "Validate",
        "regex_pattern": r"^(?i)validate(?:\s+(?:data|models?))?$",
        "backend_action": "run_validation",
        "fixed_params": {}
    },
    {
        "intent_id": "EXPORT_ALL",
        "canonical_phrase": "Export all",
        "regex_pattern": r"^(?i)export\s+(?:all|everything)$",
        "backend_action": "export_all",
        "fixed_params": {}
    },
]

# =============================================================================
# OVERRIDE COMMANDS (~15 commands)
# =============================================================================
OVERRIDE_COMMANDS: List[Dict[str, Any]] = [
    {
        "intent_id": "SET_VALUE",
        "canonical_phrase": "Set {metric} to {value}",
        "regex_pattern": r"^(?i)set\s+(?P<metric>.+?)\s+(?:to|=)\s+(?P<value>[\d,.-]+)$",
        "backend_action": "set_override",
        "fixed_params": {}
    },
    {
        "intent_id": "FIX_VALUE",
        "canonical_phrase": "Fix {metric} to {value}",
        "regex_pattern": r"^(?i)fix\s+(?P<metric>.+?)\s+(?:to|at|=)\s+(?P<value>[\d,.-]+)$",
        "backend_action": "set_override",
        "fixed_params": {}
    },
    {
        "intent_id": "OVERRIDE_VALUE",
        "canonical_phrase": "Override {metric} with {value}",
        "regex_pattern": r"^(?i)override\s+(?P<metric>.+?)\s+(?:with|to|=)\s+(?P<value>[\d,.-]+)$",
        "backend_action": "set_override",
        "fixed_params": {}
    },
    {
        "intent_id": "SET_REVENUE",
        "canonical_phrase": "Set revenue to {value}",
        "regex_pattern": r"^(?i)set\s+(?:total\s+)?revenue\s+(?:to|=)\s+(?P<value>[\d,.-]+)$",
        "backend_action": "set_override",
        "fixed_params": {"metric": "Total Revenue"}
    },
    {
        "intent_id": "SET_EBITDA",
        "canonical_phrase": "Set EBITDA to {value}",
        "regex_pattern": r"^(?i)set\s+ebitda\s+(?:to|=)\s+(?P<value>[\d,.-]+)$",
        "backend_action": "set_override",
        "fixed_params": {"metric": "EBITDA"}
    },
    {
        "intent_id": "SET_NET_INCOME",
        "canonical_phrase": "Set net income to {value}",
        "regex_pattern": r"^(?i)set\s+net\s+income\s+(?:to|=)\s+(?P<value>[\d,.-]+)$",
        "backend_action": "set_override",
        "fixed_params": {"metric": "Net Income"}
    },
    {
        "intent_id": "ADJUST_VALUE",
        "canonical_phrase": "Adjust {metric} to {value}",
        "regex_pattern": r"^(?i)adjust\s+(?P<metric>.+?)\s+(?:to|by)\s+(?P<value>[\d,.-]+)$",
        "backend_action": "set_override",
        "fixed_params": {}
    },
    {
        "intent_id": "CORRECT_VALUE",
        "canonical_phrase": "Correct {metric} to {value}",
        "regex_pattern": r"^(?i)correct\s+(?P<metric>.+?)\s+to\s+(?P<value>[\d,.-]+)$",
        "backend_action": "set_override",
        "fixed_params": {}
    },
    {
        "intent_id": "CLEAR_OVERRIDE",
        "canonical_phrase": "Clear override {metric}",
        "regex_pattern": r"^(?i)clear\s+override\s+(?P<metric>.+)$",
        "backend_action": "clear_override",
        "fixed_params": {}
    },
    {
        "intent_id": "CLEAR_ALL_OVERRIDES",
        "canonical_phrase": "Clear all overrides",
        "regex_pattern": r"^(?i)clear\s+(?:all\s+)?overrides?$",
        "backend_action": "clear_all_overrides",
        "fixed_params": {}
    },
    {
        "intent_id": "SHOW_OVERRIDES",
        "canonical_phrase": "Show overrides",
        "regex_pattern": r"^(?i)(?:show|list)\s+(?:all\s+)?overrides?$",
        "backend_action": "show_overrides",
        "fixed_params": {}
    },
    {
        "intent_id": "UNDO_OVERRIDE",
        "canonical_phrase": "Undo override",
        "regex_pattern": r"^(?i)undo\s+(?:last\s+)?override$",
        "backend_action": "undo_override",
        "fixed_params": {}
    },
    {
        "intent_id": "SET_TAX_RATE",
        "canonical_phrase": "Set tax rate to {value}",
        "regex_pattern": r"^(?i)set\s+(?:effective\s+)?tax\s+rate\s+(?:to|=)\s+(?P<value>[\d.]+)%?$",
        "backend_action": "set_override",
        "fixed_params": {"metric": "Effective Tax Rate"}
    },
    {
        "intent_id": "FIX_TAX_RATE",
        "canonical_phrase": "Fix tax rate to {value}",
        "regex_pattern": r"^(?i)fix\s+tax\s+rate\s+(?:to|at)\s+(?P<value>[\d.]+)%?$",
        "backend_action": "set_override",
        "fixed_params": {"metric": "Effective Tax Rate"}
    },
    {
        "intent_id": "SET_SHARES",
        "canonical_phrase": "Set shares to {value}",
        "regex_pattern": r"^(?i)set\s+(?:diluted\s+)?shares\s+(?:outstanding\s+)?(?:to|=)\s+(?P<value>[\d,.-]+)$",
        "backend_action": "set_override",
        "fixed_params": {"metric": "Shares Outstanding"}
    },
]

# =============================================================================
# BRAIN COMMANDS (~10 commands)
# =============================================================================
BRAIN_COMMANDS: List[Dict[str, Any]] = [
    {
        "intent_id": "SAVE_BRAIN",
        "canonical_phrase": "Save brain",
        "regex_pattern": r"^(?i)save\s+(?:my\s+)?brain$",
        "backend_action": "save_brain",
        "fixed_params": {}
    },
    {
        "intent_id": "DOWNLOAD_BRAIN",
        "canonical_phrase": "Download brain",
        "regex_pattern": r"^(?i)download\s+(?:my\s+)?brain$",
        "backend_action": "download_brain",
        "fixed_params": {}
    },
    {
        "intent_id": "LOAD_BRAIN",
        "canonical_phrase": "Load brain",
        "regex_pattern": r"^(?i)load\s+(?:my\s+)?brain$",
        "backend_action": "load_brain",
        "fixed_params": {}
    },
    {
        "intent_id": "UPLOAD_BRAIN",
        "canonical_phrase": "Upload brain",
        "regex_pattern": r"^(?i)upload\s+(?:my\s+)?brain$",
        "backend_action": "upload_brain",
        "fixed_params": {}
    },
    {
        "intent_id": "SHOW_BRAIN",
        "canonical_phrase": "Show brain",
        "regex_pattern": r"^(?i)(?:show|view)\s+(?:my\s+)?brain(?:\s+(?:status|mappings?))?$",
        "backend_action": "show_brain_status",
        "fixed_params": {}
    },
    {
        "intent_id": "CLEAR_BRAIN",
        "canonical_phrase": "Clear brain",
        "regex_pattern": r"^(?i)clear\s+(?:my\s+)?brain$",
        "backend_action": "clear_brain",
        "fixed_params": {}
    },
    {
        "intent_id": "RESET_BRAIN",
        "canonical_phrase": "Reset brain",
        "regex_pattern": r"^(?i)reset\s+(?:my\s+)?brain$",
        "backend_action": "reset_brain",
        "fixed_params": {}
    },
    {
        "intent_id": "EXPORT_BRAIN",
        "canonical_phrase": "Export brain",
        "regex_pattern": r"^(?i)export\s+(?:my\s+)?brain(?:\s+(?:to\s+)?(?P<format>csv|json))?$",
        "backend_action": "export_brain",
        "fixed_params": {}
    },
    {
        "intent_id": "BRAIN_STATS",
        "canonical_phrase": "Brain stats",
        "regex_pattern": r"^(?i)(?:brain\s+)?(?:stats?|statistics?)$",
        "backend_action": "show_brain_stats",
        "fixed_params": {}
    },
    {
        "intent_id": "LIST_MAPPINGS",
        "canonical_phrase": "List mappings",
        "regex_pattern": r"^(?i)list\s+(?:all\s+)?(?:my\s+)?mappings?$",
        "backend_action": "list_brain_mappings",
        "fixed_params": {}
    },
]

# =============================================================================
# SEARCH COMMANDS (~10 commands)
# =============================================================================
SEARCH_COMMANDS: List[Dict[str, Any]] = [
    {
        "intent_id": "FIND_CONCEPT",
        "canonical_phrase": "Find {query}",
        "regex_pattern": r"^(?i)find\s+(?P<query>.+)$",
        "backend_action": "search_concepts",
        "fixed_params": {}
    },
    {
        "intent_id": "SEARCH_CONCEPT",
        "canonical_phrase": "Search {query}",
        "regex_pattern": r"^(?i)search\s+(?:for\s+)?(?P<query>.+)$",
        "backend_action": "search_concepts",
        "fixed_params": {}
    },
    {
        "intent_id": "LOOKUP_CONCEPT",
        "canonical_phrase": "Lookup {query}",
        "regex_pattern": r"^(?i)look\s*up\s+(?P<query>.+)$",
        "backend_action": "search_concepts",
        "fixed_params": {}
    },
    {
        "intent_id": "WHAT_IS",
        "canonical_phrase": "What is {query}",
        "regex_pattern": r"^(?i)what\s+(?:is|are)\s+(?P<query>.+)$",
        "backend_action": "explain_concept",
        "fixed_params": {}
    },
    {
        "intent_id": "WHERE_IS",
        "canonical_phrase": "Where is {query}",
        "regex_pattern": r"^(?i)where\s+(?:is|are)\s+(?P<query>.+)$",
        "backend_action": "locate_item",
        "fixed_params": {}
    },
    {
        "intent_id": "SHOW_CONCEPT",
        "canonical_phrase": "Show concept {concept_id}",
        "regex_pattern": r"^(?i)show\s+concept\s+(?P<concept_id>.+)$",
        "backend_action": "show_concept_details",
        "fixed_params": {}
    },
    {
        "intent_id": "FILTER_BY",
        "canonical_phrase": "Filter by {criteria}",
        "regex_pattern": r"^(?i)filter\s+(?:by\s+)?(?P<criteria>.+)$",
        "backend_action": "apply_filter",
        "fixed_params": {}
    },
    {
        "intent_id": "SORT_BY",
        "canonical_phrase": "Sort by {column}",
        "regex_pattern": r"^(?i)sort\s+(?:by\s+)?(?P<column>.+?)(?:\s+(?P<order>asc|desc))?$",
        "backend_action": "apply_sort",
        "fixed_params": {}
    },
    {
        "intent_id": "CLEAR_FILTER",
        "canonical_phrase": "Clear filter",
        "regex_pattern": r"^(?i)clear\s+(?:all\s+)?filter(?:s)?$",
        "backend_action": "clear_filters",
        "fixed_params": {}
    },
    {
        "intent_id": "SHOW_ALL",
        "canonical_phrase": "Show all",
        "regex_pattern": r"^(?i)show\s+all(?:\s+data)?$",
        "backend_action": "clear_filters",
        "fixed_params": {}
    },
]

# =============================================================================
# HELP COMMANDS (~5 commands)
# =============================================================================
HELP_COMMANDS: List[Dict[str, Any]] = [
    {
        "intent_id": "HELP",
        "canonical_phrase": "Help",
        "regex_pattern": r"^(?i)(?:\?|help)(?:\s+(?P<topic>.+))?$",
        "backend_action": "show_help",
        "fixed_params": {}
    },
    {
        "intent_id": "LIST_COMMANDS",
        "canonical_phrase": "List commands",
        "regex_pattern": r"^(?i)list\s+(?:all\s+)?commands?$",
        "backend_action": "list_commands",
        "fixed_params": {}
    },
    {
        "intent_id": "SHOW_EXAMPLES",
        "canonical_phrase": "Show examples",
        "regex_pattern": r"^(?i)(?:show\s+)?examples?$",
        "backend_action": "show_examples",
        "fixed_params": {}
    },
    {
        "intent_id": "HOW_TO",
        "canonical_phrase": "How to {topic}",
        "regex_pattern": r"^(?i)how\s+(?:do\s+I\s+|to\s+)?(?P<topic>.+)$",
        "backend_action": "show_howto",
        "fixed_params": {}
    },
    {
        "intent_id": "VERSION",
        "canonical_phrase": "Version",
        "regex_pattern": r"^(?i)(?:version|v|about)$",
        "backend_action": "show_version",
        "fixed_params": {}
    },
]

# =============================================================================
# EXPORT COMMANDS (~5 commands)
# =============================================================================
EXPORT_COMMANDS: List[Dict[str, Any]] = [
    {
        "intent_id": "EXPORT_DCF",
        "canonical_phrase": "Export DCF",
        "regex_pattern": r"^(?i)export\s+dcf(?:\s+(?:to\s+)?(?P<format>csv|xlsx|json))?$",
        "backend_action": "export_model",
        "fixed_params": {"model": "dcf"}
    },
    {
        "intent_id": "EXPORT_LBO",
        "canonical_phrase": "Export LBO",
        "regex_pattern": r"^(?i)export\s+lbo(?:\s+(?:to\s+)?(?P<format>csv|xlsx|json))?$",
        "backend_action": "export_model",
        "fixed_params": {"model": "lbo"}
    },
    {
        "intent_id": "EXPORT_COMPS",
        "canonical_phrase": "Export Comps",
        "regex_pattern": r"^(?i)export\s+comps?(?:\s+(?:to\s+)?(?P<format>csv|xlsx|json))?$",
        "backend_action": "export_model",
        "fixed_params": {"model": "comps"}
    },
    {
        "intent_id": "EXPORT_AUDIT",
        "canonical_phrase": "Export audit",
        "regex_pattern": r"^(?i)export\s+audit(?:\s+(?:report|results?))?$",
        "backend_action": "export_audit",
        "fixed_params": {}
    },
    {
        "intent_id": "EXPORT_DATA",
        "canonical_phrase": "Export data",
        "regex_pattern": r"^(?i)export\s+(?:normalized\s+)?data$",
        "backend_action": "export_normalized",
        "fixed_params": {}
    },
]


# =============================================================================
# AGGREGATE ALL BASE COMMANDS
# =============================================================================
def get_all_base_commands() -> List[Dict[str, Any]]:
    """
    Returns all base commands as a single list.

    Returns:
        List of all command definitions (~100 commands)
    """
    all_commands = []
    all_commands.extend(MAPPING_COMMANDS)
    all_commands.extend(AUDITING_COMMANDS)
    all_commands.extend(NAVIGATION_COMMANDS)
    all_commands.extend(PIPELINE_COMMANDS)
    all_commands.extend(OVERRIDE_COMMANDS)
    all_commands.extend(BRAIN_COMMANDS)
    all_commands.extend(SEARCH_COMMANDS)
    all_commands.extend(HELP_COMMANDS)
    all_commands.extend(EXPORT_COMMANDS)
    return all_commands


def get_commands_by_category() -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns commands organized by category.

    Returns:
        Dictionary of category -> list of commands
    """
    return {
        "Mapping": MAPPING_COMMANDS,
        "Auditing": AUDITING_COMMANDS,
        "Navigation": NAVIGATION_COMMANDS,
        "Pipeline": PIPELINE_COMMANDS,
        "Override": OVERRIDE_COMMANDS,
        "Brain": BRAIN_COMMANDS,
        "Search": SEARCH_COMMANDS,
        "Help": HELP_COMMANDS,
        "Export": EXPORT_COMMANDS,
    }


def get_command_count() -> int:
    """Returns total number of base commands."""
    return len(get_all_base_commands())


# =============================================================================
# BACKEND ACTION REGISTRY
# Maps action names to their descriptions for the "Teach Me" UI
# =============================================================================
BACKEND_ACTIONS = {
    "update_mapping": {
        "description": "Map a source label to a target XBRL concept",
        "required_params": ["source"],
        "optional_params": ["target"],
        "category": "Mapping"
    },
    "remove_mapping": {
        "description": "Remove a mapping from the brain",
        "required_params": ["source"],
        "optional_params": [],
        "category": "Mapping"
    },
    "ignore_warning": {
        "description": "Suppress a specific warning",
        "required_params": ["rule_name"],
        "optional_params": [],
        "category": "Auditing"
    },
    "ignore_rule": {
        "description": "Disable a validation rule",
        "required_params": ["rule_name"],
        "optional_params": [],
        "category": "Auditing"
    },
    "disable_check": {
        "description": "Turn off a validation check",
        "required_params": ["check_name"],
        "optional_params": [],
        "category": "Auditing"
    },
    "enable_check": {
        "description": "Turn on a validation check",
        "required_params": ["check_name"],
        "optional_params": [],
        "category": "Auditing"
    },
    "explain_warning": {
        "description": "Get explanation for a warning or item",
        "required_params": ["item"],
        "optional_params": [],
        "category": "Auditing"
    },
    "show_warnings": {
        "description": "Display all warnings",
        "required_params": [],
        "optional_params": [],
        "category": "Auditing"
    },
    "show_critical": {
        "description": "Display critical issues",
        "required_params": [],
        "optional_params": [],
        "category": "Auditing"
    },
    "show_errors": {
        "description": "Display all errors",
        "required_params": [],
        "optional_params": [],
        "category": "Auditing"
    },
    "show_passed": {
        "description": "Display passed checks",
        "required_params": [],
        "optional_params": [],
        "category": "Auditing"
    },
    "navigate_to": {
        "description": "Switch to a specific view/tab",
        "required_params": [],
        "optional_params": ["target_view"],
        "category": "Navigation"
    },
    "navigate_to_tab": {
        "description": "Navigate to a named tab",
        "required_params": ["tab_name"],
        "optional_params": [],
        "category": "Navigation"
    },
    "reset_view": {
        "description": "Reset current view to default",
        "required_params": [],
        "optional_params": [],
        "category": "Navigation"
    },
    "navigate_back": {
        "description": "Go to previous view",
        "required_params": [],
        "optional_params": [],
        "category": "Navigation"
    },
    "refresh_view": {
        "description": "Refresh current view",
        "required_params": [],
        "optional_params": [],
        "category": "Navigation"
    },
    "force_generate": {
        "description": "Force generate outputs despite errors",
        "required_params": [],
        "optional_params": [],
        "category": "Pipeline"
    },
    "run_pipeline": {
        "description": "Execute the full analysis pipeline",
        "required_params": [],
        "optional_params": [],
        "category": "Pipeline"
    },
    "run_clean": {
        "description": "Run pipeline with clean state",
        "required_params": [],
        "optional_params": [],
        "category": "Pipeline"
    },
    "rerun_pipeline": {
        "description": "Re-execute the pipeline",
        "required_params": [],
        "optional_params": [],
        "category": "Pipeline"
    },
    "regenerate_model": {
        "description": "Regenerate a specific model",
        "required_params": ["model"],
        "optional_params": [],
        "category": "Pipeline"
    },
    "recalculate": {
        "description": "Recalculate all models",
        "required_params": [],
        "optional_params": [],
        "category": "Pipeline"
    },
    "clear_session": {
        "description": "Clear current session data",
        "required_params": [],
        "optional_params": [],
        "category": "Pipeline"
    },
    "new_session": {
        "description": "Start a new session",
        "required_params": [],
        "optional_params": [],
        "category": "Pipeline"
    },
    "cancel_operation": {
        "description": "Cancel running operation",
        "required_params": [],
        "optional_params": [],
        "category": "Pipeline"
    },
    "run_validation": {
        "description": "Run validation checks",
        "required_params": [],
        "optional_params": [],
        "category": "Pipeline"
    },
    "export_all": {
        "description": "Export all outputs",
        "required_params": [],
        "optional_params": [],
        "category": "Pipeline"
    },
    "set_override": {
        "description": "Set a manual value override",
        "required_params": ["value"],
        "optional_params": ["metric"],
        "category": "Override"
    },
    "clear_override": {
        "description": "Clear a specific override",
        "required_params": ["metric"],
        "optional_params": [],
        "category": "Override"
    },
    "clear_all_overrides": {
        "description": "Clear all overrides",
        "required_params": [],
        "optional_params": [],
        "category": "Override"
    },
    "show_overrides": {
        "description": "Display all overrides",
        "required_params": [],
        "optional_params": [],
        "category": "Override"
    },
    "undo_override": {
        "description": "Undo the last override",
        "required_params": [],
        "optional_params": [],
        "category": "Override"
    },
    "save_brain": {
        "description": "Save analyst brain to file",
        "required_params": [],
        "optional_params": [],
        "category": "Brain"
    },
    "download_brain": {
        "description": "Download analyst brain",
        "required_params": [],
        "optional_params": [],
        "category": "Brain"
    },
    "load_brain": {
        "description": "Load analyst brain from file",
        "required_params": [],
        "optional_params": [],
        "category": "Brain"
    },
    "upload_brain": {
        "description": "Upload analyst brain",
        "required_params": [],
        "optional_params": [],
        "category": "Brain"
    },
    "show_brain_status": {
        "description": "Display brain status",
        "required_params": [],
        "optional_params": [],
        "category": "Brain"
    },
    "clear_brain": {
        "description": "Clear all brain data",
        "required_params": [],
        "optional_params": [],
        "category": "Brain"
    },
    "reset_brain": {
        "description": "Reset brain to defaults",
        "required_params": [],
        "optional_params": [],
        "category": "Brain"
    },
    "export_brain": {
        "description": "Export brain to file",
        "required_params": [],
        "optional_params": ["format"],
        "category": "Brain"
    },
    "show_brain_stats": {
        "description": "Display brain statistics",
        "required_params": [],
        "optional_params": [],
        "category": "Brain"
    },
    "list_brain_mappings": {
        "description": "List all brain mappings",
        "required_params": [],
        "optional_params": [],
        "category": "Brain"
    },
    "search_concepts": {
        "description": "Search for concepts",
        "required_params": ["query"],
        "optional_params": [],
        "category": "Search"
    },
    "explain_concept": {
        "description": "Explain a concept",
        "required_params": ["query"],
        "optional_params": [],
        "category": "Search"
    },
    "locate_item": {
        "description": "Find location of an item",
        "required_params": ["query"],
        "optional_params": [],
        "category": "Search"
    },
    "show_concept_details": {
        "description": "Show concept details",
        "required_params": ["concept_id"],
        "optional_params": [],
        "category": "Search"
    },
    "apply_filter": {
        "description": "Apply data filter",
        "required_params": ["criteria"],
        "optional_params": [],
        "category": "Search"
    },
    "apply_sort": {
        "description": "Sort data",
        "required_params": ["column"],
        "optional_params": ["order"],
        "category": "Search"
    },
    "clear_filters": {
        "description": "Clear all filters",
        "required_params": [],
        "optional_params": [],
        "category": "Search"
    },
    "filter_statement": {
        "description": "Filter by financial statement",
        "required_params": [],
        "optional_params": ["statement"],
        "category": "Navigation"
    },
    "show_help": {
        "description": "Show help information",
        "required_params": [],
        "optional_params": ["topic"],
        "category": "Help"
    },
    "list_commands": {
        "description": "List all available commands",
        "required_params": [],
        "optional_params": [],
        "category": "Help"
    },
    "show_examples": {
        "description": "Show command examples",
        "required_params": [],
        "optional_params": [],
        "category": "Help"
    },
    "show_howto": {
        "description": "Show how-to guide",
        "required_params": ["topic"],
        "optional_params": [],
        "category": "Help"
    },
    "show_version": {
        "description": "Show version information",
        "required_params": [],
        "optional_params": [],
        "category": "Help"
    },
    "export_model": {
        "description": "Export a financial model",
        "required_params": [],
        "optional_params": ["model", "format"],
        "category": "Export"
    },
    "export_audit": {
        "description": "Export audit report",
        "required_params": [],
        "optional_params": [],
        "category": "Export"
    },
    "export_normalized": {
        "description": "Export normalized data",
        "required_params": [],
        "optional_params": [],
        "category": "Export"
    },
    "list_rules": {
        "description": "List all validation rules",
        "required_params": [],
        "optional_params": [],
        "category": "Auditing"
    },
    "list_checks": {
        "description": "List all checks",
        "required_params": [],
        "optional_params": [],
        "category": "Auditing"
    },
    "suppress_warning": {
        "description": "Suppress a warning",
        "required_params": ["warning"],
        "optional_params": [],
        "category": "Auditing"
    },
    "enable_warning": {
        "description": "Enable a warning",
        "required_params": ["warning"],
        "optional_params": [],
        "category": "Auditing"
    },
    "accept_warning": {
        "description": "Accept a warning",
        "required_params": ["warning"],
        "optional_params": [],
        "category": "Auditing"
    },
    "dismiss_warning": {
        "description": "Dismiss a warning",
        "required_params": ["warning"],
        "optional_params": [],
        "category": "Auditing"
    },
    "show_audit_status": {
        "description": "Show audit status",
        "required_params": [],
        "optional_params": [],
        "category": "Auditing"
    },
    "run_audit": {
        "description": "Run full audit",
        "required_params": [],
        "optional_params": [],
        "category": "Auditing"
    },
    "recheck_item": {
        "description": "Recheck an item",
        "required_params": ["item"],
        "optional_params": [],
        "category": "Auditing"
    },
}


def get_backend_actions() -> Dict[str, Dict]:
    """Returns all backend actions with metadata."""
    return BACKEND_ACTIONS


def get_action_names() -> List[str]:
    """Returns list of all action names for dropdown."""
    return sorted(BACKEND_ACTIONS.keys())


def get_actions_by_category() -> Dict[str, List[str]]:
    """Returns actions grouped by category."""
    result = {}
    for action_name, action_info in BACKEND_ACTIONS.items():
        category = action_info.get("category", "Other")
        if category not in result:
            result[category] = []
        result[category].append(action_name)
    return result

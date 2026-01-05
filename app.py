#!/usr/bin/env python3
"""
FinanceX: Production V1.0 - Goldman-Futuristic Interface
==========================================================
JPMC/Citadel-Grade Financial Workbench with:

1. ONBOARDING JOURNEY - 3-step guide for new users
2. ANALYST BRAIN (BYOB) - Portable JSON memory upload/download
3. ANALYST COCKPIT - Grouped audits with interactive fixes
4. GLASSMORPHISM UI - High-Finance Aesthetic

Flow: Onboarding -> Upload Brain -> Process -> Audit -> Download
"""

import streamlit as st
import pandas as pd
import sqlite3
import os
import csv
import io
import json
import zipfile
from datetime import datetime

# Local imports
from session_manager import (
    SessionManager, cleanup_on_startup,
    initialize_clean_slate, get_clean_slate_paths,
    save_current_upload, write_thinking_log, append_thinking_log,
    TEMP_SESSION_DIR, OUTPUT_DIR, LOGS_DIR, TAXONOMY_DIR
)
from run_pipeline import run_pipeline_programmatic
from validator.ai_auditor import AIAuditor, AuditSeverity
from utils.brain_manager import BrainManager, get_brain_manager
from utils.command_engine import (
    CommandEngine, CommandExecutor, ParseResult, ExecutionResult,
    get_command_engine, reset_command_engine
)
from utils.cli_parser import ChatParser, parse_command as cli_parse, get_help as cli_help
from utils.exporter import create_download_package, export_brain_only, ExportResult
from config.base_commands import (
    get_commands_by_category, get_action_names, get_backend_actions
)

# -------------------------------------------------
# CONFIGURATION - Production V1.0 Clean Slate
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Use Clean Slate paths
DB_PATH = os.path.join(OUTPUT_DIR, "taxonomy_2025.db")
ALIAS_PATH = os.path.join(BASE_DIR, "config", "aliases.csv")

# Initialize Clean Slate on first import (web app startup)
_CLEAN_SLATE_INITIALIZED = False

# -------------------------------------------------
# GLASSMORPHISM CSS - High-Finance Aesthetic
# -------------------------------------------------
GOLDMAN_CSS = """
<style>
    /* Import professional fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* Root variables */
    :root {
        --primary-dark: #0a0a0f;
        --secondary-dark: #12121a;
        --accent-gold: #c9a962;
        --accent-blue: #3b82f6;
        --accent-green: #10b981;
        --accent-red: #ef4444;
        --accent-yellow: #f59e0b;
        --glass-bg: rgba(18, 18, 26, 0.85);
        --glass-border: rgba(201, 169, 98, 0.2);
        --text-primary: #ffffff;
        --text-secondary: #a1a1aa;
    }

    /* Global styles */
    .stApp {
        background: linear-gradient(135deg, var(--primary-dark) 0%, var(--secondary-dark) 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Glassmorphism cards */
    .glass-card {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }

    .glass-card-highlight {
        background: linear-gradient(135deg, rgba(201, 169, 98, 0.1) 0%, rgba(18, 18, 26, 0.9) 100%);
        border: 1px solid var(--accent-gold);
    }

    /* Headers */
    .main-header {
        text-align: center;
        padding: 40px 0;
        margin-bottom: 20px;
    }

    .main-header h1 {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, var(--accent-gold) 0%, #f0d890 50%, var(--accent-gold) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        letter-spacing: -0.02em;
    }

    .main-header p {
        color: var(--text-secondary);
        font-size: 1.1rem;
        margin-top: 8px;
        font-weight: 400;
    }

    /* Step indicators */
    .step-indicator {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 16px;
    }

    .step-number {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--accent-gold) 0%, #d4b06a 100%);
        color: var(--primary-dark);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 1rem;
    }

    .step-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    /* Severity badges */
    .badge-critical {
        background: rgba(239, 68, 68, 0.2);
        border: 1px solid var(--accent-red);
        color: var(--accent-red);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .badge-warning {
        background: rgba(245, 158, 11, 0.2);
        border: 1px solid var(--accent-yellow);
        color: var(--accent-yellow);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .badge-pass {
        background: rgba(16, 185, 129, 0.2);
        border: 1px solid var(--accent-green);
        color: var(--accent-green);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    /* Code blocks */
    .ocr-prompt {
        background: rgba(0, 0, 0, 0.4);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        padding: 20px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9rem;
        color: var(--text-secondary);
        white-space: pre-wrap;
        line-height: 1.6;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-gold) 0%, #d4b06a 100%);
        color: var(--primary-dark);
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 12px 24px;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(201, 169, 98, 0.3);
    }

    /* Force Generate Button */
    .force-btn {
        background: linear-gradient(135deg, var(--accent-red) 0%, #dc2626 100%) !important;
        color: white !important;
    }

    /* Metrics */
    .metric-card {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--accent-gold);
    }

    .metric-label {
        font-size: 0.9rem;
        color: var(--text-secondary);
        margin-top: 4px;
    }

    /* Sidebar styling */
    .css-1d391kg, .css-1lcbmhc {
        background: var(--secondary-dark);
    }

    /* Hide streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Expander styling */
    .streamlit-expanderHeader {
        background: var(--glass-bg);
        border-radius: 8px;
    }

    /* Table styling */
    .dataframe {
        background: var(--glass-bg) !important;
    }

    /* Link styling */
    a {
        color: var(--accent-gold);
        text-decoration: none;
    }

    a:hover {
        text-decoration: underline;
    }
</style>
"""

# OCR Prompt for users
OCR_PROMPT = """I have a PDF of financial statements. Please extract the data into 3 separate CSV blocks:

1. Income Statement
2. Balance Sheet
3. Cash Flow Statement

Formatting Rules:
- Column A must contain the Line Item Labels.
- Row 1 must contain the Dates (e.g., '2023', 'FY24').
- Do not merge cells. Ensure numbers are clean (no currency symbols).
- If a statement spans multiple pages, merge them into one CSV block."""

# Page config
st.set_page_config(
    page_title="FinanceX - Production V1.0",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject CSS
st.markdown(GOLDMAN_CSS, unsafe_allow_html=True)

# -------------------------------------------------
# SESSION STATE INITIALIZATION - Clean Slate Architecture
# -------------------------------------------------

# Initialize Clean Slate on first run
if 'clean_slate_initialized' not in st.session_state:
    initialize_clean_slate()
    st.session_state.clean_slate_initialized = True
    st.session_state.clean_slate_paths = get_clean_slate_paths()

if 'session_manager' not in st.session_state:
    st.session_state.session_manager = SessionManager()
    cleanup_on_startup()

if 'current_session' not in st.session_state:
    st.session_state.current_session = None

if 'pipeline_result' not in st.session_state:
    st.session_state.pipeline_result = None

if 'audit_report' not in st.session_state:
    st.session_state.audit_report = None

if 'brain_manager' not in st.session_state:
    st.session_state.brain_manager = BrainManager(ALIAS_PATH)

if 'manual_overrides' not in st.session_state:
    st.session_state.manual_overrides = {}

if 'onboarding_complete' not in st.session_state:
    st.session_state.onboarding_complete = False

if 'current_step' not in st.session_state:
    st.session_state.current_step = 1

if 'command_engine' not in st.session_state:
    st.session_state.command_engine = CommandEngine()

if 'command_executor' not in st.session_state:
    st.session_state.command_executor = CommandExecutor(st.session_state)

if 'command_history' not in st.session_state:
    st.session_state.command_history = []

if 'current_tab' not in st.session_state:
    st.session_state.current_tab = 0

if 'show_teach_me' not in st.session_state:
    st.session_state.show_teach_me = False

if 'failed_command' not in st.session_state:
    st.session_state.failed_command = ""

if 'chat_parser' not in st.session_state:
    st.session_state.chat_parser = ChatParser()

if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

if 'pending_rerun' not in st.session_state:
    st.session_state.pending_rerun = False


# -------------------------------------------------
# HARD RESET FOR NEW UPLOADS - Enforce Data Integrity
# -------------------------------------------------
def reset_session_state_for_new_upload():
    """
    HARD RESET: Wipe all data-related session state before processing a new file.

    This ensures:
    1. No stale data persists from previous uploads
    2. No fallback to old data if new processing fails
    3. Clean slate for each file upload

    Called IMMEDIATELY when a new file is detected, BEFORE any processing.
    """
    # Clear all data caches first
    st.cache_data.clear()

    # Note: We intentionally do NOT clear cache_resource (database connections)
    # as those are truly static resources, not user data

    # Clear previous session data
    if st.session_state.current_session:
        sm = st.session_state.session_manager
        try:
            sm.cleanup_session(st.session_state.current_session.session_id)
        except Exception:
            pass  # Session may already be cleaned up

    # Reset all data-holding session state variables
    st.session_state.current_session = None
    st.session_state.pipeline_result = None
    st.session_state.audit_report = None
    st.session_state.manual_overrides = {}
    st.session_state.onboarding_complete = False
    st.session_state.current_step = 1

    # Clear command history (may contain references to old data)
    st.session_state.command_history = []
    st.session_state.chat_messages = []
    st.session_state.failed_command = ""
    st.session_state.show_teach_me = False
    st.session_state.pending_rerun = False

    # Reset command engine state
    st.session_state.command_engine = CommandEngine()
    st.session_state.command_executor = CommandExecutor(st.session_state)

    # Note: We preserve brain_manager as it contains user's learned mappings
    # which should persist across uploads (user's institutional knowledge)


# -------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------
@st.cache_resource
def get_db_connection():
    """Get cached database connection."""
    if os.path.exists(DB_PATH):
        return sqlite3.connect(DB_PATH, check_same_thread=False)
    return None


@st.cache_data
def load_taxonomy_concepts():
    """Load all valid concepts for the dropdown search."""
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    df = pd.read_sql("SELECT element_id, concept_name, source FROM concepts", conn)
    df['display'] = df['element_id'] + " (" + df['concept_name'] + ")"
    return df


def save_new_alias(source_label: str, target_element_id: str, source_taxonomy: str) -> tuple:
    """Writes a new correction to aliases.csv."""
    try:
        if os.path.exists(ALIAS_PATH):
            current = pd.read_csv(ALIAS_PATH)
            if source_label in current['alias'].values:
                return False, "Alias already exists!"
    except Exception:
        pass

    with open(ALIAS_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([source_taxonomy, source_label, target_element_id])
    return True, "Success"


def get_severity_color(severity: AuditSeverity) -> str:
    """Get color for audit severity."""
    return {
        AuditSeverity.CRITICAL: "#ef4444",
        AuditSeverity.WARNING: "#f59e0b",
        AuditSeverity.PASS: "#10b981",
        AuditSeverity.INFO: "#3b82f6",
    }.get(severity, "#a1a1aa")


def phrase_to_regex(phrase: str) -> str:
    """Convert a natural phrase to a regex pattern."""
    import re
    escaped = re.escape(phrase)
    pattern = re.sub(r'\\{(\w+)\\}', r'(?P<\1>.+?)', escaped)
    pattern = pattern.replace(r'\ ', r'\s+')
    pattern = f"^(?i){pattern}$"
    return pattern


def process_command(user_input: str) -> dict:
    """
    Process a user command through the engine.

    Returns dict with:
      - success: bool
      - message: str
      - requires_refresh: bool
      - navigate_to: Optional[str]
    """
    engine = st.session_state.command_engine
    executor = st.session_state.command_executor

    # Parse the command
    parse_result = engine.parse(user_input)

    if not parse_result.success:
        # Command not recognized - trigger Teach Me flow
        st.session_state.show_teach_me = True
        st.session_state.failed_command = user_input
        return {
            "success": False,
            "message": f"Unknown command: '{user_input}'",
            "requires_refresh": False,
            "navigate_to": None
        }

    # Execute the command
    exec_result = executor.execute(parse_result)

    # Add to history
    st.session_state.command_history.append({
        "input": user_input,
        "intent": parse_result.intent_id,
        "action": parse_result.backend_action,
        "success": exec_result.success,
        "message": exec_result.message,
        "timestamp": datetime.now().isoformat()
    })

    # Handle navigation
    if exec_result.navigate_to:
        tab_map = {
            "audit": 0,
            "dcf": 1,
            "lbo": 1,
            "comps": 1,
            "data": 2,
            "unmapped": 3,
            "downloads": 4,
            "home": 0
        }
        if exec_result.navigate_to.lower() in tab_map:
            st.session_state.current_tab = tab_map[exec_result.navigate_to.lower()]

    return {
        "success": exec_result.success,
        "message": exec_result.message,
        "requires_refresh": exec_result.requires_refresh,
        "navigate_to": exec_result.navigate_to,
        "data": exec_result.data
    }


def create_download_zip(session_id: str) -> bytes:
    """Create a ZIP file with all outputs."""
    sm = st.session_state.session_manager
    files = sm.get_session_files(session_id)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_type, file_path in files.items():
            if file_path and os.path.exists(file_path):
                arcname = os.path.basename(file_path)
                zf.write(file_path, arcname)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


# -------------------------------------------------
# MAIN HEADER
# -------------------------------------------------
def render_header():
    """Render the Goldman-style header."""
    st.markdown("""
    <div class="main-header">
        <h1>FinanceX</h1>
        <p>Investment Banking-Grade Financial Analysis | Production V1.0</p>
    </div>
    """, unsafe_allow_html=True)


# -------------------------------------------------
# SIDEBAR - Analyst Brain & Session Info
# -------------------------------------------------
def render_sidebar():
    """Render sidebar with Brain upload and session info."""
    with st.sidebar:
        st.markdown("## Analyst Brain")
        st.markdown("*Your portable mapping memory*")

        # Brain Upload
        brain_file = st.file_uploader(
            "Upload Brain (JSON)",
            type=["json"],
            help="Upload your analyst_brain.json to restore your mapping history"
        )

        if brain_file:
            try:
                brain_data = brain_file.read().decode('utf-8')
                if st.session_state.brain_manager.load_from_json_string(brain_data):
                    st.success(f"Brain loaded! {len(st.session_state.brain_manager.mappings)} custom mappings")
                else:
                    st.error("Failed to parse brain file")
            except Exception as e:
                st.error(f"Error: {str(e)}")

        # Brain Stats
        if st.session_state.brain_manager.mappings:
            stats = st.session_state.brain_manager.get_session_stats()
            st.metric("Custom Mappings", stats['total_user_mappings'])

        # Brain Download
        if st.button("Download Updated Brain", use_container_width=True):
            brain_json = st.session_state.brain_manager.to_json_string()
            st.download_button(
                label="Save analyst_brain.json",
                data=brain_json,
                file_name="analyst_brain.json",
                mime="application/json"
            )

        st.divider()

        # Session Info
        st.markdown("## Session")
        session = st.session_state.current_session
        if session:
            st.success(f"Active: {session.session_id[:16]}...")

            if st.session_state.pipeline_result:
                result = st.session_state.pipeline_result
                if result["success"]:
                    st.metric("Status", "Complete")
                    st.metric("Duration", f"{result['duration']:.1f}s")
                else:
                    st.error(f"Failed")

            if st.button("Clear Session", type="secondary", use_container_width=True):
                # Use centralized reset function for consistency
                reset_session_state_for_new_upload()
                st.rerun()
        else:
            st.info("No active session")

        # Audit Summary
        if st.session_state.audit_report:
            st.divider()
            st.markdown("## Audit Summary")
            report = st.session_state.audit_report

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"<div style='text-align:center;color:#ef4444;font-size:1.5rem;font-weight:bold;'>{report.critical_count}</div><div style='text-align:center;color:#a1a1aa;font-size:0.8rem;'>Critical</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div style='text-align:center;color:#f59e0b;font-size:1.5rem;font-weight:bold;'>{report.warning_count}</div><div style='text-align:center;color:#a1a1aa;font-size:0.8rem;'>Warnings</div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<div style='text-align:center;color:#10b981;font-size:1.5rem;font-weight:bold;'>{report.pass_count}</div><div style='text-align:center;color:#a1a1aa;font-size:0.8rem;'>Passed</div>", unsafe_allow_html=True)

        st.divider()
        st.caption("FinanceX Production V1.0")
        st.caption("100% Local | Zero Cloud | BYOB Architecture")


# -------------------------------------------------
# COMMAND INTERFACE - Conversational CLI with Auto-Rerun
# -------------------------------------------------
def execute_chat_command(user_input: str) -> dict:
    """
    Execute a chat command using both the CLI parser and command engine.
    Handles mapping commands with brain updates and auto-rerun.

    Returns dict with execution results.
    """
    # First try the new CLI parser for quick mapping commands
    parsed = st.session_state.chat_parser.parse(user_input)

    if parsed.success:
        # Handle based on intent
        if parsed.intent == "MAP_LABEL":
            # Map command: Update brain and trigger rerun
            source_label = parsed.params.get("source_label", "")
            target_id = parsed.params.get("target_element_id", "")

            if source_label and target_id:
                # Update brain manager
                st.session_state.brain_manager.add_mapping(
                    source_label=source_label,
                    target_element_id=target_id,
                    notes=f"Added via chat: '{user_input}'"
                )

                # Save to aliases.csv for persistence
                save_new_alias(source_label, target_id, "US_GAAP")

                # Add to chat history
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": user_input
                })
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": f"Mapped '{source_label}' to `{target_id}`. Brain updated. Re-running engine..."
                })

                return {
                    "success": True,
                    "message": f"Mapped '{source_label}' to {target_id}",
                    "requires_refresh": True,
                    "trigger_rerun": True
                }

        elif parsed.intent == "SET_VALUE":
            # Value override
            bucket = parsed.params.get("bucket", "")
            value = parsed.params.get("value", 0)

            if bucket:
                st.session_state.manual_overrides[bucket] = value
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": user_input
                })
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": f"Set {bucket} to ${value:,.0f}. Override applied."
                })

                return {
                    "success": True,
                    "message": f"Override: {bucket} = ${value:,.0f}",
                    "requires_refresh": True
                }

        elif parsed.intent == "NAVIGATE":
            dest = parsed.params.get("destination", "")
            tab_map = {"dcf": 1, "lbo": 1, "comps": 1, "audit": 0, "data": 2, "unmapped": 3, "downloads": 4}
            if dest in tab_map:
                st.session_state.current_tab = tab_map[dest]
                return {
                    "success": True,
                    "message": f"Navigated to {dest}",
                    "requires_refresh": True
                }

        elif parsed.intent == "DOWNLOAD_BRAIN":
            return {
                "success": True,
                "message": "Brain download ready",
                "download_brain": True
            }

        elif parsed.intent == "DOWNLOAD_PACKAGE":
            return {
                "success": True,
                "message": "Package download ready",
                "download_package": True
            }

        elif parsed.intent == "HELP":
            return {
                "success": True,
                "message": cli_help(),
                "show_help": True
            }

        elif parsed.intent == "BRAIN_STATS":
            stats = st.session_state.brain_manager.get_session_stats()
            return {
                "success": True,
                "message": f"Brain: {stats['total_user_mappings']} mappings, {stats['custom_commands']} commands",
                "data": stats
            }

        elif parsed.intent == "RERUN":
            return {
                "success": True,
                "message": "Re-running engine...",
                "trigger_rerun": True,
                "requires_refresh": True
            }

    # Fall back to the original command engine
    result = process_command(user_input)
    return result


def render_command_interface():
    """Render the enhanced command line interface panel with chat."""
    st.markdown("""
    <div class="glass-card" style="border-left: 3px solid #c9a962;">
        <h3 style="color: #c9a962; margin: 0 0 16px 0;">Analyst Chat</h3>
    </div>
    """, unsafe_allow_html=True)

    # Display chat history
    chat_container = st.container()
    with chat_container:
        if st.session_state.chat_messages:
            for msg in st.session_state.chat_messages[-10:]:
                if msg["role"] == "user":
                    st.markdown(f"**You:** {msg['content']}")
                else:
                    st.markdown(f"*System:* {msg['content']}")

    st.divider()

    # Command input
    user_input = st.text_input(
        "Enter command",
        placeholder="e.g., Map 'Turnover' to Revenue",
        key="command_input",
        label_visibility="collapsed"
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        execute_btn = st.button("Send", type="primary", use_container_width=True)
    with col2:
        help_btn = st.button("?", help="Show command help")

    if help_btn:
        with st.expander("Command Examples", expanded=True):
            st.markdown("""
            **Mapping (Auto-rerun enabled):**
            - `Map 'Turnover' to Revenue`
            - `'Operating Income' should be EBIT`

            **Value Override:**
            - `Set EBITDA to 500000`
            - `Revenue = 1000000`

            **Navigation:**
            - `Show DCF` / `Show LBO` / `Show Comps`
            - `Show Audit` / `Show Data`

            **Downloads:**
            - `Download Brain` - Export your brain
            - `Download Package` - Get everything

            **Other:**
            - `Re-run` - Recalculate models
            - `Brain stats` - Show brain info
            - `Help` - Show this help
            """)

    # Process command on button click
    if execute_btn and user_input.strip():
        result = execute_chat_command(user_input.strip())

        # Add to command history
        st.session_state.command_history.append({
            "input": user_input,
            "success": result["success"],
            "message": result["message"],
            "timestamp": datetime.now().isoformat()
        })

        if result["success"]:
            # Handle special actions
            if result.get("show_help"):
                st.markdown(result["message"])

            elif result.get("download_brain"):
                brain_json = st.session_state.brain_manager.to_json_string()
                st.download_button(
                    label="Download Brain JSON",
                    data=brain_json,
                    file_name="analyst_brain.json",
                    mime="application/json",
                    key="chat_brain_download"
                )

            elif result.get("download_package"):
                # Use the new exporter
                if st.session_state.current_session:
                    sm = st.session_state.session_manager
                    files = sm.get_session_files(st.session_state.current_session.session_id)
                    model_files = {
                        "DCF": files.get("dcf"),
                        "LBO": files.get("lbo"),
                        "Comps": files.get("comps"),
                        "Validation": files.get("validation")
                    }
                    export_result = create_download_package(
                        st.session_state.brain_manager,
                        model_files
                    )
                    if export_result.success:
                        st.download_button(
                            label=f"Download {export_result.filename}",
                            data=export_result.data,
                            file_name=export_result.filename,
                            mime=export_result.mime_type,
                            key="chat_package_download"
                        )
                    else:
                        st.error(f"Export failed: {export_result.error_message}")

            elif result.get("trigger_rerun"):
                # Re-run the pipeline with updated mappings
                if st.session_state.current_session:
                    with st.spinner("Re-running engine with updated mappings..."):
                        sm = st.session_state.session_manager
                        session = st.session_state.current_session
                        files = sm.get_session_files(session.session_id)

                        if files.get("upload"):
                            output_dir = sm.get_output_dir(session.session_id)
                            result = run_pipeline_programmatic(files["upload"], output_dir, quiet=True)
                            st.session_state.pipeline_result = result

                            if result["success"]:
                                # Re-run audit
                                auditor = AIAuditor(
                                    normalized_df=pd.read_csv(files["normalized"]) if files.get("normalized") else None,
                                    dcf_df=pd.read_csv(files["dcf"]) if files.get("dcf") else None,
                                    lbo_df=pd.read_csv(files["lbo"]) if files.get("lbo") else None,
                                    comps_df=pd.read_csv(files["comps"]) if files.get("comps") else None
                                )
                                st.session_state.audit_report = auditor.run_full_audit()
                                st.success("Engine re-run complete!")

            else:
                st.success(f"OK: {result['message']}")

            if result.get("requires_refresh"):
                st.rerun()
        else:
            st.error(result["message"])
            # Show Teach Me wizard for unrecognized commands
            st.session_state.show_teach_me = True
            st.session_state.failed_command = user_input
            render_teach_me_wizard()

    # Show Teach Me wizard if triggered
    if st.session_state.show_teach_me and not (execute_btn and user_input.strip()):
        render_teach_me_wizard()

    # Command history
    if st.session_state.command_history:
        with st.expander("Recent Commands", expanded=False):
            for cmd in reversed(st.session_state.command_history[-10:]):
                status_icon = "+" if cmd["success"] else "x"
                st.markdown(f"`{status_icon}` **{cmd['input']}** -> {cmd['message']}")


def render_teach_me_wizard():
    """Render the Teach Me wizard for defining new commands."""
    if not st.session_state.show_teach_me:
        return

    st.markdown("""
    <div class="glass-card" style="border: 1px solid #f59e0b; margin-top: 16px;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
            <span style="font-size: 1.5rem;">+</span>
            <span style="color: #f59e0b; font-weight: 600;">Define New Command</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("teach_me_form"):
        # Field 1: The Phrase (auto-filled with failed input)
        phrase = st.text_input(
            "Command Phrase",
            value=st.session_state.failed_command,
            help="The phrase to recognize. Use {placeholder} for variable parts."
        )

        st.caption("Use `{name}` for placeholders. Example: `Fix {metric} to {value}`")

        # Field 2: The Action (dropdown)
        actions = get_action_names()
        action_info = get_backend_actions()

        # Group actions by category for easier selection
        action_categories = {}
        for action in actions:
            cat = action_info.get(action, {}).get("category", "Other")
            if cat not in action_categories:
                action_categories[cat] = []
            action_categories[cat].append(action)

        selected_action = st.selectbox(
            "Backend Action",
            options=actions,
            format_func=lambda x: f"{x} - {action_info.get(x, {}).get('description', '')}"[:60],
            help="What should this command do?"
        )

        # Show action details
        if selected_action:
            info = action_info.get(selected_action, {})
            st.info(f"**{info.get('description', 'No description')}** (Category: {info.get('category', 'Other')})")

            required_params = info.get("required_params", [])
            optional_params = info.get("optional_params", [])

            if required_params or optional_params:
                st.markdown("**Parameters:**")
                if required_params:
                    st.markdown(f"Required: `{', '.join(required_params)}`")
                if optional_params:
                    st.markdown(f"Optional: `{', '.join(optional_params)}`")

        # Field 3: Fixed Parameters (optional)
        st.markdown("**Fixed Parameters** (optional)")
        param_col1, param_col2 = st.columns(2)
        with param_col1:
            param_key = st.text_input("Parameter Name", placeholder="e.g., target")
        with param_col2:
            param_value = st.text_input("Parameter Value", placeholder="e.g., us-gaap_Revenues")

        # Submit buttons
        col1, col2 = st.columns(2)
        with col1:
            save_execute = st.form_submit_button("Save & Execute", type="primary")
        with col2:
            cancel = st.form_submit_button("Cancel")

        if cancel:
            st.session_state.show_teach_me = False
            st.session_state.failed_command = ""
            st.rerun()

        if save_execute and phrase and selected_action:
            # Build fixed params
            fixed_params = {}
            if param_key and param_value:
                fixed_params[param_key] = param_value

            # Generate intent ID
            import re
            clean_phrase = re.sub(r'[^a-zA-Z0-9\s]', '', phrase)
            intent_id = "USER_" + "_".join(clean_phrase.upper().split())[:50]

            # Generate regex pattern
            regex_pattern = phrase_to_regex(phrase)

            # Add to brain manager
            st.session_state.brain_manager.add_custom_command(
                intent_id=intent_id,
                canonical_phrase=phrase,
                regex_pattern=regex_pattern,
                backend_action=selected_action,
                fixed_params=fixed_params
            )

            # Add to command engine
            success, msg, cmd = st.session_state.command_engine.add_user_command(
                phrase=phrase,
                backend_action=selected_action,
                params=fixed_params,
                intent_id=intent_id
            )

            if success:
                st.success(f"Command learned: '{phrase}'")

                # Execute immediately
                result = process_command(phrase)
                if result["success"]:
                    st.success(f"Executed: {result['message']}")

                st.session_state.show_teach_me = False
                st.session_state.failed_command = ""

                st.info("Download your Brain to save this command permanently.")
                st.rerun()
            else:
                st.error(f"Could not save command: {msg}")


# -------------------------------------------------
# ONBOARDING JOURNEY - 3-Step Guide
# -------------------------------------------------
def render_user_instruction_block():
    """
    Render the EXACT user instruction guide as specified.
    This must be displayed prominently on the landing page.
    """
    st.info("""
**How to Use FinanceX - Your 5-Step Journey:**

1. **Launch:** Run `streamlit run app.py` in your terminal.

2. **Prepare:** Use ChatGPT to OCR your PDF into our 3-tab Excel format.

3. **Upload:** Drag & drop your Excel file + your `Analyst_Brain.json`.

4. **Refine:** Use the Chat to fix warnings (e.g., `"Map X to Y"`).

5. **Evolve:** Download your new Brain file to make the tool smarter for next time.
    """)


def render_onboarding():
    """Render the onboarding journey for new users."""
    st.markdown("""
    <div class="glass-card glass-card-highlight" style="text-align: center; padding: 40px;">
        <h2 style="color: #c9a962; margin-bottom: 8px;">Welcome to FinanceX</h2>
        <p style="color: #a1a1aa; font-size: 1.1rem;">Investment Banking-Grade Financial Analysis</p>
    </div>
    """, unsafe_allow_html=True)

    # USER INSTRUCTION BLOCK - Display prominently
    render_user_instruction_block()

    # Step 1: OCR
    st.markdown("""
    <div class="glass-card">
        <div class="step-indicator">
            <div class="step-number">1</div>
            <div class="step-title">Prepare Your Data (OCR)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    We do not parse PDFs directly. Use AI to convert your financial statements to structured data.

    **Free OCR Tool:** [ChatGPT Financial Statement OCR](https://chatgpt.com/g/g-wETMBcESv-ocr)

    Copy this prompt and paste it along with your PDF:
    """)

    st.code(OCR_PROMPT, language="text")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Copy Prompt to Clipboard", use_container_width=True):
            st.toast("Prompt copied! Paste it in ChatGPT with your PDF.")

    st.divider()

    # Step 2: Google Sheets Setup
    st.markdown("""
    <div class="glass-card">
        <div class="step-indicator">
            <div class="step-number">2</div>
            <div class="step-title">Create Your Excel File</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    After getting the CSVs from the OCR tool:

    1. Go to **[sheets.new](https://sheets.new)** to create a new Google Sheet
    2. Create 3 tabs named **exactly**:
       - `Income Statement`
       - `Balance Sheet`
       - `Cashflow Statement`
    3. Paste each CSV into the corresponding tab
    4. Download as **.xlsx** (File > Download > Microsoft Excel)
    """)

    st.info("Tab names must match exactly for the parser to work correctly.")

    st.divider()

    # Step 3: Upload
    st.markdown("""
    <div class="glass-card">
        <div class="step-indicator">
            <div class="step-number">3</div>
            <div class="step-title">Upload & Analyze</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Upload Your Financial Data**")
        uploaded_file = st.file_uploader(
            "Excel file (.xlsx)",
            type=["xlsx", "xls"],
            help="Your prepared financial statements"
        )

    with col2:
        st.markdown("**Upload Analyst Brain (Optional)**")
        brain_file = st.file_uploader(
            "Brain file (.json)",
            type=["json"],
            help="Your saved mapping history"
        )

        if brain_file:
            try:
                brain_data = brain_file.read().decode('utf-8')
                if st.session_state.brain_manager.load_from_json_string(brain_data):
                    st.success(f"Brain loaded!")
            except Exception as e:
                st.error(f"Error loading brain: {str(e)}")

    if uploaded_file:
        st.success(f"File ready: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")

        if st.button("Process Financial Statements", type="primary", use_container_width=True):
            # =============================================================
            # HARD RESET: Wipe ALL previous data BEFORE processing new file
            # This ensures no stale data can ever be displayed
            # =============================================================
            reset_session_state_for_new_upload()

            with st.spinner("Processing your data..."):
                try:
                    # Create fresh session
                    sm = st.session_state.session_manager
                    session = sm.create_session()
                    st.session_state.current_session = session

                    # Save upload
                    upload_path = sm.save_upload(
                        session.session_id,
                        uploaded_file.getvalue(),
                        uploaded_file.name
                    )

                    # Run pipeline
                    output_dir = sm.get_output_dir(session.session_id)
                    result = run_pipeline_programmatic(upload_path, output_dir, quiet=True)
                    st.session_state.pipeline_result = result

                    if result["success"]:
                        # Run AI Auditor
                        files = sm.get_session_files(session.session_id)
                        auditor = AIAuditor(
                            normalized_df=pd.read_csv(files["normalized"]) if files.get("normalized") else None,
                            dcf_df=pd.read_csv(files["dcf"]) if files.get("dcf") else None,
                            lbo_df=pd.read_csv(files["lbo"]) if files.get("lbo") else None,
                            comps_df=pd.read_csv(files["comps"]) if files.get("comps") else None
                        )
                        st.session_state.audit_report = auditor.run_full_audit()
                        st.session_state.onboarding_complete = True
                        st.success("Analysis complete!")
                        st.rerun()
                    else:
                        # Pipeline failed - show error, NO fallback to old data
                        st.error(f"Pipeline failed: {result['error']}")
                        st.warning("Please fix the issue and re-upload your file. No data will be displayed until processing succeeds.")

                except Exception as e:
                    # Catch-all for any processing errors - NO fallback to old data
                    st.error(f"Processing error: {str(e)}")
                    st.warning("An error occurred during processing. Please check your file and try again.")
                    # Ensure session state remains clean (no stale data)
                    st.session_state.pipeline_result = None
                    st.session_state.audit_report = None
                    st.session_state.onboarding_complete = False


# -------------------------------------------------
# ANALYST COCKPIT - Results Dashboard
# -------------------------------------------------
def render_analyst_cockpit():
    """Render the main analysis cockpit with grouped audits."""

    # Top metrics bar
    if st.session_state.audit_report:
        report = st.session_state.audit_report

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #10b981;">{report.pass_count}</div>
                <div class="metric-label">Passed</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #f59e0b;">{report.warning_count}</div>
                <div class="metric-label">Warnings</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #ef4444;">{report.critical_count}</div>
                <div class="metric-label">Critical</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            status_color = "#10b981" if report.overall_status == "PASSED" else "#f59e0b" if report.overall_status == "REVIEW_NEEDED" else "#ef4444"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: {status_color};">{report.overall_status}</div>
                <div class="metric-label">Overall</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Tabs for different views
    tabs = st.tabs(["Audit Results", "Financial Models", "Data View", "Fix Unmapped", "Downloads"])

    # Tab 1: Audit Results
    with tabs[0]:
        render_audit_results()

    # Tab 2: Financial Models
    with tabs[1]:
        render_financial_models()

    # Tab 3: Data View
    with tabs[2]:
        render_data_view()

    # Tab 4: Fix Unmapped
    with tabs[3]:
        render_fix_unmapped()

    # Tab 5: Downloads
    with tabs[4]:
        render_downloads()


def render_audit_results():
    """Render audit results with grouped findings."""
    if not st.session_state.audit_report:
        st.info("No audit results available. Process your data first.")
        return

    report = st.session_state.audit_report

    # Categorize findings
    critical_findings = [f for f in report.findings if f.severity == AuditSeverity.CRITICAL]
    warning_findings = [f for f in report.findings if f.severity == AuditSeverity.WARNING]
    passed_findings = [f for f in report.findings if f.severity == AuditSeverity.PASS]

    # CRITICAL FAILURES (Expanded)
    if critical_findings:
        with st.expander(f"CRITICAL FAILURES ({len(critical_findings)})", expanded=True):
            st.error("These issues require immediate attention.")

            for i, finding in enumerate(critical_findings):
                st.markdown(f"""
                <div class="glass-card" style="border-left: 4px solid #ef4444; margin: 8px 0;">
                    <strong style="color: #ef4444;">{finding.check_name}</strong>
                    <p style="color: #a1a1aa; margin: 8px 0;">{finding.message}</p>
                </div>
                """, unsafe_allow_html=True)

                # Interactive fix
                bucket_name = _extract_bucket_name(finding)
                if bucket_name:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        override_value = st.number_input(
                            f"Override {bucket_name}",
                            value=st.session_state.manual_overrides.get(bucket_name, 0.0),
                            key=f"critical_{i}_{finding.check_name}"
                        )
                    with col2:
                        if st.button("Apply", key=f"apply_critical_{i}"):
                            st.session_state.manual_overrides[bucket_name] = override_value
                            # Learn this correction
                            st.session_state.brain_manager.learn_from_correction(
                                finding.check_name, str(override_value)
                            )
                            st.success(f"Override applied and learned!")
                            st.rerun()

    # WARNINGS (Expanded)
    if warning_findings:
        with st.expander(f"WARNINGS ({len(warning_findings)})", expanded=True):
            st.warning("Review these items for accuracy.")

            for i, finding in enumerate(warning_findings):
                st.markdown(f"""
                <div class="glass-card" style="border-left: 4px solid #f59e0b; margin: 8px 0;">
                    <strong style="color: #f59e0b;">{finding.check_name}</strong>
                    <p style="color: #a1a1aa; margin: 8px 0;">{finding.message}</p>
                </div>
                """, unsafe_allow_html=True)

    # PASSED (Collapsed)
    if passed_findings:
        with st.expander(f"PASSED CHECKS ({len(passed_findings)})", expanded=False):
            for finding in passed_findings:
                st.markdown(f"+ **{finding.check_name}**: {finding.message}")

    st.divider()

    # Emergency Actions
    st.markdown("### Emergency Actions")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Force Generate Template**

        Generate outputs even with critical errors.
        Missing values will be set to 0.0 and flagged.
        """)

        if st.button("Force Generate Template", type="secondary"):
            _force_generate_template()

    with col2:
        # Export audit report
        audit_df = report.to_dataframe()
        csv_data = audit_df.to_csv(index=False).encode('utf-8')

        st.download_button(
            label="Download Audit Report (CSV)",
            data=csv_data,
            file_name="audit_report.csv",
            mime="text/csv"
        )


def render_financial_models():
    """Render financial model outputs."""
    if not st.session_state.current_session:
        st.info("No models available. Process your data first.")
        return

    sm = st.session_state.session_manager
    files = sm.get_session_files(st.session_state.current_session.session_id)

    model_tabs = st.tabs(["DCF Setup", "LBO Stats", "Comps Metrics", "Validation"])

    with model_tabs[0]:
        dcf_path = files.get("dcf")
        if dcf_path and os.path.exists(dcf_path):
            df = pd.read_csv(dcf_path, index_col=0)
            st.dataframe(df, use_container_width=True, height=400)
            st.download_button(
                "Download DCF CSV",
                df.to_csv().encode('utf-8'),
                "DCF_Historical_Setup.csv",
                "text/csv"
            )
        else:
            st.warning("DCF model not available")

    with model_tabs[1]:
        lbo_path = files.get("lbo")
        if lbo_path and os.path.exists(lbo_path):
            df = pd.read_csv(lbo_path, index_col=0)
            st.dataframe(df, use_container_width=True, height=400)
            st.download_button(
                "Download LBO CSV",
                df.to_csv().encode('utf-8'),
                "LBO_Credit_Stats.csv",
                "text/csv"
            )
        else:
            st.warning("LBO model not available")

    with model_tabs[2]:
        comps_path = files.get("comps")
        if comps_path and os.path.exists(comps_path):
            df = pd.read_csv(comps_path, index_col=0)
            st.dataframe(df, use_container_width=True, height=400)
            st.download_button(
                "Download Comps CSV",
                df.to_csv().encode('utf-8'),
                "Comps_Trading_Metrics.csv",
                "text/csv"
            )
        else:
            st.warning("Comps model not available")

    with model_tabs[3]:
        validation_path = files.get("validation")
        if validation_path and os.path.exists(validation_path):
            df = pd.read_csv(validation_path)
            st.dataframe(df, use_container_width=True, height=400)
        else:
            st.info("No validation report available")


def render_data_view():
    """Render normalized data view."""
    if not st.session_state.current_session:
        st.info("No data available. Process your data first.")
        return

    sm = st.session_state.session_manager
    files = sm.get_session_files(st.session_state.current_session.session_id)

    if not files.get("normalized"):
        st.warning("Normalized data not available.")
        return

    df = pd.read_csv(files["normalized"])

    # Stats
    col1, col2, col3 = st.columns(3)
    total = len(df)
    valid = len(df[df['Status'] == 'VALID']) if 'Status' in df.columns else 0
    unmapped = total - valid

    with col1:
        st.metric("Total Rows", total)
    with col2:
        st.metric("Mapped", valid, delta=f"{valid/total*100:.0f}%" if total > 0 else "0%")
    with col3:
        st.metric("Unmapped", unmapped)

    st.divider()
    st.dataframe(df, use_container_width=True, height=400)


def render_fix_unmapped():
    """Render fix unmapped interface with brain learning."""
    if not st.session_state.current_session:
        st.info("No data available. Process your data first.")
        return

    sm = st.session_state.session_manager
    files = sm.get_session_files(st.session_state.current_session.session_id)

    if not files.get("normalized"):
        st.warning("No normalized data available.")
        return

    df = pd.read_csv(files["normalized"])

    if 'Status' not in df.columns:
        st.warning("Status column not found.")
        return

    unmapped_items = df[df['Status'] == 'UNMAPPED']['Source_Label'].unique()

    if len(unmapped_items) == 0:
        st.success("All items mapped successfully!")
        return

    st.warning(f"{len(unmapped_items)} items need mapping")

    col1, col2 = st.columns(2)

    with col1:
        selected_label = st.selectbox("Select Unmapped Item", unmapped_items)

    with col2:
        concepts_df = load_taxonomy_concepts()
        if len(concepts_df) == 0:
            st.error("Taxonomy database not found!")
            return

        target = st.selectbox(
            "Map to Taxonomy Concept",
            concepts_df['display']
        )

    if st.button("Save Mapping & Learn", type="primary"):
        target_id = target.split(" (")[0]
        target_source = concepts_df[concepts_df['element_id'] == target_id]['source'].values[0]

        # Save to aliases
        success, msg = save_new_alias(selected_label, target_id, target_source)

        # Learn in brain
        st.session_state.brain_manager.add_mapping(
            source_label=selected_label,
            target_element_id=target_id,
            source_taxonomy=target_source,
            notes="Learned from UI correction"
        )

        if success:
            st.success(f"Mapped and learned: '{selected_label}' -> '{target_id}'")
            st.info("Download your updated Brain to save this mapping permanently!")
        else:
            st.warning(msg)


def render_downloads():
    """Render downloads section."""
    if not st.session_state.current_session:
        st.info("No files available. Process your data first.")
        return

    st.markdown("### Download All Outputs")

    col1, col2 = st.columns(2)

    with col1:
        zip_data = create_download_zip(st.session_state.current_session.session_id)
        st.download_button(
            label="Download All Models (ZIP)",
            data=zip_data,
            file_name=f"financex_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True
        )

    with col2:
        brain_json = st.session_state.brain_manager.to_json_string()
        st.download_button(
            label="Download Analyst Brain (JSON)",
            data=brain_json,
            file_name="analyst_brain.json",
            mime="application/json",
            use_container_width=True
        )

    st.divider()

    st.markdown("### Individual Files")

    sm = st.session_state.session_manager
    files = sm.get_session_files(st.session_state.current_session.session_id)

    for file_type, file_path in files.items():
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                st.download_button(
                    label=f"Download {os.path.basename(file_path)}",
                    data=f.read(),
                    file_name=os.path.basename(file_path),
                    mime="text/csv"
                )


# -------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------
def _extract_bucket_name(finding) -> str:
    """Extract bucket name from finding for override purposes."""
    message = finding.message.lower() if finding.message else ""
    check_name = finding.check_name.lower() if finding.check_name else ""

    bucket_patterns = {
        "revenue": "Total Revenue",
        "net income": "Net Income",
        "ebitda": "EBITDA",
        "cogs": "COGS",
        "gross profit": "Gross Profit",
        "operating": "Operating Income",
        "capex": "CapEx",
        "cash": "Cash",
        "debt": "Total Debt",
        "assets": "Total Assets",
        "liabilities": "Total Liabilities",
        "equity": "Equity",
    }

    for pattern, bucket in bucket_patterns.items():
        if pattern in message or pattern in check_name:
            return bucket

    return None


def _force_generate_template():
    """Force generate template files despite errors."""
    if not st.session_state.current_session:
        st.error("No active session")
        return

    sm = st.session_state.session_manager
    session_id = st.session_state.current_session.session_id
    files = sm.get_session_files(session_id)

    try:
        with st.spinner("Force generating templates..."):
            if files.get("dcf") and os.path.exists(files["dcf"]):
                dcf_df = pd.read_csv(files["dcf"], index_col=0)
            else:
                periods = ["2024", "2023", "2022"]
                dcf_template = {
                    "Total Revenue": [0.0, 0.0, 0.0],
                    "(-) COGS": [0.0, 0.0, 0.0],
                    "(=) Gross Profit": [0.0, 0.0, 0.0],
                    "(-) SG&A": [0.0, 0.0, 0.0],
                    "(-) R&D": [0.0, 0.0, 0.0],
                    "(=) EBITDA": [0.0, 0.0, 0.0],
                    "(-) D&A": [0.0, 0.0, 0.0],
                    "(=) EBIT": [0.0, 0.0, 0.0],
                    "(-) Cash Taxes": [0.0, 0.0, 0.0],
                    "(=) NOPAT": [0.0, 0.0, 0.0],
                    "(-) CapEx": [0.0, 0.0, 0.0],
                    "(=) Unlevered Free Cash Flow": [0.0, 0.0, 0.0],
                }
                dcf_df = pd.DataFrame(dcf_template, index=periods).T

            # Apply overrides
            for bucket_name, value in st.session_state.manual_overrides.items():
                if bucket_name in dcf_df.index:
                    for col in dcf_df.columns:
                        dcf_df.loc[bucket_name, col] = value

            dcf_df["_FORCED"] = "YES"

            output_dir = sm.get_output_dir(session_id)
            forced_path = os.path.join(output_dir, "DCF_Historical_Setup_FORCED.csv")
            dcf_df.to_csv(forced_path)

            if files.get("dcf"):
                dcf_df.to_csv(files["dcf"])

            st.success("Force generated successfully!")

            csv_data = dcf_df.to_csv().encode('utf-8')
            st.download_button(
                label="Download Forced DCF",
                data=csv_data,
                file_name="DCF_Historical_Setup_FORCED.csv",
                mime="text/csv",
                type="primary"
            )

    except Exception as e:
        st.error(f"Force generation failed: {str(e)}")


# -------------------------------------------------
# MAIN APPLICATION
# -------------------------------------------------
def main():
    """Main application entry point."""
    render_header()
    render_sidebar()

    # Show onboarding or cockpit based on state
    if not st.session_state.onboarding_complete:
        render_onboarding()
    else:
        # Split layout: Main content (left) + Command Interface (right)
        main_col, cmd_col = st.columns([3, 1])

        with main_col:
            render_analyst_cockpit()

        with cmd_col:
            render_command_interface()

            # Command stats
            engine = st.session_state.command_engine
            stats = engine.get_command_stats()

            st.divider()
            st.markdown("**Engine Stats**")
            st.caption(f"Base: {stats['base_commands']} | Custom: {stats['user_commands']}")

            # Quick actions
            st.markdown("**Quick Actions**")
            if st.button("List Commands", use_container_width=True, key="quick_list"):
                categories = get_commands_by_category()
                with st.expander("All Commands", expanded=True):
                    for cat, cmds in categories.items():
                        st.markdown(f"**{cat}** ({len(cmds)})")
                        for cmd in cmds[:3]:
                            st.caption(f"  {cmd['canonical_phrase']}")
                        if len(cmds) > 3:
                            st.caption(f"  ... and {len(cmds) - 3} more")

            if st.button("Clear History", use_container_width=True, key="quick_clear"):
                st.session_state.command_history = []
                st.rerun()


if __name__ == "__main__":
    main()

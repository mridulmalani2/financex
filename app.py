#!/usr/bin/env python3
"""
FinanceX: Professional Streamlit Application
=============================================
JPMC/Citadel-Grade Financial Workbench UI

This is the main application layer implementing:
1. Session-based file isolation (temp_sessions/)
2. Dynamic pipeline execution
3. AI Auditor dashboard with forensic accounting results
4. Download functionality for all outputs

Flow: Upload -> Save to Temp -> Run Pipeline -> Display Audit -> Download
"""

import streamlit as st
import pandas as pd
import sqlite3
import os
import csv
import io
import zipfile
from datetime import datetime

# Local imports
from session_manager import SessionManager, cleanup_on_startup
from run_pipeline import run_pipeline_programmatic
from validator.ai_auditor import AIAuditor, AuditSeverity

# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "output", "taxonomy_2025.db")
ALIAS_PATH = os.path.join(BASE_DIR, "config", "aliases.csv")

# Page config
st.set_page_config(
    page_title="FinanceX Workbench",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------
# SESSION STATE INITIALIZATION
# -------------------------------------------------
if 'session_manager' not in st.session_state:
    st.session_state.session_manager = SessionManager()
    # Cleanup old sessions on app startup
    cleanup_on_startup()

if 'current_session' not in st.session_state:
    st.session_state.current_session = None

if 'pipeline_result' not in st.session_state:
    st.session_state.pipeline_result = None

if 'audit_report' not in st.session_state:
    st.session_state.audit_report = None


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
        AuditSeverity.CRITICAL: "#dc3545",  # Red
        AuditSeverity.WARNING: "#ffc107",   # Yellow
        AuditSeverity.PASS: "#28a745",      # Green
        AuditSeverity.INFO: "#17a2b8",      # Blue
    }.get(severity, "#6c757d")


def get_severity_icon(severity: AuditSeverity) -> str:
    """Get icon for audit severity."""
    return {
        AuditSeverity.CRITICAL: "X",
        AuditSeverity.WARNING: "!",
        AuditSeverity.PASS: "+",
        AuditSeverity.INFO: "i",
    }.get(severity, "?")


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
# MAIN UI
# -------------------------------------------------
def render_header():
    """Render the application header."""
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h1 style="margin: 0;">FinanceX Workbench</h1>
        <p style="color: #666; margin: 0;">JPMC / Citadel Grade Financial Analysis</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with session info and stats."""
    with st.sidebar:
        st.header("Session Info")

        session = st.session_state.current_session
        if session:
            st.success(f"Active: {session.session_id[:20]}...")

            # Show pipeline status
            if st.session_state.pipeline_result:
                result = st.session_state.pipeline_result
                if result["success"]:
                    st.metric("Pipeline Status", "Complete")
                    st.metric("Duration", f"{result['duration']:.1f}s")
                else:
                    st.error(f"Failed: {result['error'][:50]}...")

            # Cleanup button
            if st.button("Clear Session", type="secondary"):
                sm = st.session_state.session_manager
                sm.cleanup_session(session.session_id)
                st.session_state.current_session = None
                st.session_state.pipeline_result = None
                st.session_state.audit_report = None
                st.rerun()
        else:
            st.info("No active session")

        st.divider()

        # Audit Summary
        if st.session_state.audit_report:
            report = st.session_state.audit_report
            st.header("Audit Summary")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Critical", report.critical_count,
                          delta_color="inverse" if report.critical_count > 0 else "off")
            with col2:
                st.metric("Warnings", report.warning_count,
                          delta_color="inverse" if report.warning_count > 0 else "off")
            with col3:
                st.metric("Passed", report.pass_count)

            # Overall status indicator
            if report.overall_status == "PASSED":
                st.success("All Checks Passed")
            elif report.overall_status == "REVIEW_NEEDED":
                st.warning("Review Recommended")
            else:
                st.error("Critical Issues Found")

        st.divider()
        st.caption("FinanceX v2.0")
        st.caption("100% Local - Zero Cloud Dependencies")


def render_upload_tab():
    """Render the file upload tab."""
    st.markdown("### Step 1: Upload Financial Statements")
    st.markdown("Upload an Excel file (.xlsx) containing Income Statement, Balance Sheet, and Cash Flow Statement.")

    uploaded_file = st.file_uploader(
        "Choose Excel file",
        type=["xlsx", "xls"],
        help="Supported formats: .xlsx, .xls"
    )

    if uploaded_file:
        st.success(f"File selected: {uploaded_file.name}")

        # Show file preview info
        st.info(f"Size: {uploaded_file.size / 1024:.1f} KB")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Process File", type="primary", use_container_width=True):
                with st.spinner("Processing..."):
                    # Create session
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

                        st.success("Pipeline completed successfully!")
                        st.rerun()
                    else:
                        st.error(f"Pipeline failed: {result['error']}")

        with col2:
            if st.button("Clear", use_container_width=True):
                st.session_state.current_session = None
                st.session_state.pipeline_result = None
                st.session_state.audit_report = None
                st.rerun()


def render_audit_tab():
    """Render the AI Auditor dashboard."""
    st.markdown("### AI Auditor - Forensic Accounting Dashboard")

    if not st.session_state.audit_report:
        st.info("Run the pipeline first to see audit results.")
        return

    report = st.session_state.audit_report

    # Overall Status Banner
    if report.overall_status == "PASSED":
        st.success("**AUDIT PASSED** - All forensic checks validated successfully")
    elif report.overall_status == "REVIEW_NEEDED":
        st.warning("**REVIEW NEEDED** - Some items require attention")
    else:
        st.error("**CRITICAL ISSUES** - Data quality concerns detected")

    st.divider()

    # Category-wise findings
    categories = {}
    for finding in report.findings:
        cat = finding.category
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(finding)

    for category, findings in categories.items():
        with st.expander(f"**{category.replace('_', ' ').title()}** ({len(findings)} checks)", expanded=True):
            for finding in findings:
                color = get_severity_color(finding.severity)
                icon = get_severity_icon(finding.severity)

                # Severity badge
                severity_html = f"""
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem; padding: 0.5rem;
                            border-left: 4px solid {color}; background: #f8f9fa;">
                    <span style="background: {color}; color: white; padding: 2px 8px;
                                 border-radius: 4px; font-weight: bold; margin-right: 10px;">
                        [{icon}] {finding.severity.value}
                    </span>
                    <span style="font-weight: 500;">{finding.check_name}</span>
                </div>
                """
                st.markdown(severity_html, unsafe_allow_html=True)
                st.markdown(f"> {finding.message}")

                if finding.details:
                    with st.popover("View Details"):
                        st.json(finding.details)

                if finding.recommendation:
                    st.caption(f"Recommendation: {finding.recommendation}")

    # Export audit report
    st.divider()
    audit_df = report.to_dataframe()
    csv_data = audit_df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="Download Audit Report (CSV)",
        data=csv_data,
        file_name="audit_report.csv",
        mime="text/csv"
    )


def render_data_tab():
    """Render the normalized data view."""
    st.markdown("### Normalized Financial Data")

    if not st.session_state.current_session or not st.session_state.pipeline_result:
        st.info("Run the pipeline first to see data.")
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
        st.metric("Unmapped", unmapped, delta_color="inverse" if unmapped > 0 else "off")

    st.divider()

    # Data table with highlighting
    def highlight_status(val):
        if val == 'VALID':
            return 'background-color: #d4edda'
        elif val == 'UNMAPPED':
            return 'background-color: #f8d7da'
        return ''

    if 'Status' in df.columns:
        styled_df = df.style.applymap(highlight_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True, height=400)
    else:
        st.dataframe(df, use_container_width=True, height=400)


def check_model_has_data(df: pd.DataFrame) -> dict:
    """
    Check if a model DataFrame has actual data (non-zero values).
    Returns dict with validation info.
    """
    if df is None or df.empty:
        return {'valid': False, 'error': 'No data available'}

    # Check for critical zero values
    critical_rows = ['Total Revenue', 'Revenue', 'EBITDA', 'Net Income']
    zero_criticals = []

    for row in critical_rows:
        if row in df.index:
            row_values = df.loc[row]
            if isinstance(row_values, pd.Series):
                if row_values.sum() == 0:
                    zero_criticals.append(row)

    if zero_criticals:
        return {
            'valid': False,
            'error': f"Critical values are zero: {', '.join(zero_criticals)}",
            'zero_buckets': zero_criticals
        }

    return {'valid': True, 'error': None}


def render_models_tab():
    """Render the IB models output view with enhanced error handling."""
    st.markdown("### Investment Banking Models")

    if not st.session_state.current_session or not st.session_state.pipeline_result:
        st.info("Run the pipeline first to see models.")
        return

    # Check if pipeline had errors
    result = st.session_state.pipeline_result
    if not result.get("success"):
        st.error(f"Pipeline Error: {result.get('error', 'Unknown error')}")
        st.warning("Models may not be available due to pipeline failure.")

    sm = st.session_state.session_manager
    files = sm.get_session_files(st.session_state.current_session.session_id)

    model_tabs = st.tabs(["DCF Setup", "LBO Stats", "Comps Metrics", "Validation", "Engine Log"])

    with model_tabs[0]:
        dcf_path = files.get("dcf")
        # Check file existence explicitly
        if dcf_path and os.path.exists(dcf_path):
            try:
                df = pd.read_csv(dcf_path, index_col=0)

                # Validate the data
                validation = check_model_has_data(df)
                if not validation['valid']:
                    st.error(f"DCF Model Issue: {validation['error']}")
                    st.warning("The model contains zero values in critical buckets. This may indicate mapping issues.")

                    # Show the data anyway for debugging
                    with st.expander("View Raw DCF Data (Debug)", expanded=False):
                        st.dataframe(df, use_container_width=True, height=300)
                else:
                    st.dataframe(df, use_container_width=True, height=400)
                    st.download_button(
                        "Download DCF CSV",
                        df.to_csv().encode('utf-8'),
                        "DCF_Historical_Setup.csv",
                        "text/csv"
                    )
            except Exception as e:
                st.error(f"Error reading DCF file: {str(e)}")
        else:
            st.error("DCF Data Not Available")
            st.markdown("""
            **Possible causes:**
            1. Pipeline failed to complete
            2. No valid financial data was mapped
            3. Engine encountered critical errors

            **Check the Engine Log tab for details.**
            """)

    with model_tabs[1]:
        lbo_path = files.get("lbo")
        if lbo_path and os.path.exists(lbo_path):
            try:
                df = pd.read_csv(lbo_path, index_col=0)
                validation = check_model_has_data(df)
                if not validation['valid']:
                    st.warning(f"LBO Model Issue: {validation['error']}")
                st.dataframe(df, use_container_width=True, height=400)
                st.download_button(
                    "Download LBO CSV",
                    df.to_csv().encode('utf-8'),
                    "LBO_Credit_Stats.csv",
                    "text/csv"
                )
            except Exception as e:
                st.error(f"Error reading LBO file: {str(e)}")
        else:
            st.warning("LBO data not available - check Engine Log for errors")

    with model_tabs[2]:
        comps_path = files.get("comps")
        if comps_path and os.path.exists(comps_path):
            try:
                df = pd.read_csv(comps_path, index_col=0)
                validation = check_model_has_data(df)
                if not validation['valid']:
                    st.warning(f"Comps Model Issue: {validation['error']}")
                st.dataframe(df, use_container_width=True, height=400)
                st.download_button(
                    "Download Comps CSV",
                    df.to_csv().encode('utf-8'),
                    "Comps_Trading_Metrics.csv",
                    "text/csv"
                )
            except Exception as e:
                st.error(f"Error reading Comps file: {str(e)}")
        else:
            st.warning("Comps data not available - check Engine Log for errors")

    with model_tabs[3]:
        validation_path = files.get("validation")
        if validation_path and os.path.exists(validation_path):
            df = pd.read_csv(validation_path)
            # Highlight failures
            def highlight_status(val):
                if val == 'FAIL':
                    return 'background-color: #f8d7da; color: #721c24'
                elif val == 'WARN':
                    return 'background-color: #fff3cd; color: #856404'
                elif val == 'PASS':
                    return 'background-color: #d4edda; color: #155724'
                return ''

            if 'Status' in df.columns:
                styled_df = df.style.applymap(highlight_status, subset=['Status'])
                st.dataframe(styled_df, use_container_width=True, height=400)
            else:
                st.dataframe(df, use_container_width=True, height=400)
        else:
            st.info("No validation report available")

    with model_tabs[4]:
        st.markdown("### Engine Execution Log")

        # Show pipeline result details
        if result:
            if result.get("success"):
                st.success(f"Pipeline completed in {result.get('duration', 0):.2f}s")
            else:
                st.error(f"Pipeline failed: {result.get('error', 'Unknown')}")

        # Show unmapped data if available
        unmapped_path = files.get("unmapped")
        if unmapped_path and os.path.exists(unmapped_path):
            unmapped_df = pd.read_csv(unmapped_path)
            if len(unmapped_df) > 0:
                st.warning(f"{len(unmapped_df)} items could not be mapped")
                with st.expander("View Unmapped Items"):
                    st.dataframe(unmapped_df, use_container_width=True, height=200)

        # Show hierarchy resolutions
        hierarchy_path = files.get("hierarchy")
        if hierarchy_path and os.path.exists(hierarchy_path):
            hierarchy_df = pd.read_csv(hierarchy_path)
            if len(hierarchy_df) > 0:
                st.info(f"{len(hierarchy_df)} hierarchy conflicts resolved (prevented double-counting)")
                with st.expander("View Hierarchy Resolutions"):
                    st.dataframe(hierarchy_df, use_container_width=True, height=200)

    # Download all as ZIP
    st.divider()
    if st.session_state.current_session:
        zip_data = create_download_zip(st.session_state.current_session.session_id)
        st.download_button(
            label="Download All Outputs (ZIP)",
            data=zip_data,
            file_name=f"financex_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip",
            type="primary"
        )


def render_fix_unmapped_tab():
    """Render the fix unmapped items interface."""
    st.markdown("### Teach the System")
    st.markdown("Map unknown items here. Changes are saved to `aliases.csv` for future runs.")

    if not st.session_state.current_session or not st.session_state.pipeline_result:
        st.info("Run the pipeline first to see unmapped items.")
        return

    sm = st.session_state.session_manager
    files = sm.get_session_files(st.session_state.current_session.session_id)

    if not files.get("normalized"):
        st.warning("No normalized data available.")
        return

    df = pd.read_csv(files["normalized"])

    if 'Status' not in df.columns:
        st.warning("Status column not found in data.")
        return

    unmapped_items = df[df['Status'] == 'UNMAPPED']['Source_Label'].unique()

    if len(unmapped_items) == 0:
        st.success("No unmapped items! The data is clean.")
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
            "Search Official Taxonomy",
            concepts_df['display'],
            help="Type to search for 'Revenue', 'Assets', etc."
        )

    if st.button("Save Mapping", type="primary"):
        target_id = target.split(" (")[0]
        target_source = concepts_df[concepts_df['element_id'] == target_id]['source'].values[0]

        success, msg = save_new_alias(selected_label, target_id, target_source)

        if success:
            st.success(f"Mapped '{selected_label}' -> '{target_id}'")
            st.info("Re-run the pipeline to apply these changes.")
        else:
            st.warning(msg)


def main():
    """Main application entry point."""
    render_header()
    render_sidebar()

    # Main content tabs
    tabs = st.tabs([
        "Upload",
        "AI Auditor",
        "Data View",
        "IB Models",
        "Fix Unmapped"
    ])

    with tabs[0]:
        render_upload_tab()

    with tabs[1]:
        render_audit_tab()

    with tabs[2]:
        render_data_tab()

    with tabs[3]:
        render_models_tab()

    with tabs[4]:
        render_fix_unmapped_tab()


if __name__ == "__main__":
    main()

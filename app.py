import streamlit as st
import pandas as pd
import sqlite3
import os
import csv

# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "output", "taxonomy_2025.db")
NORM_FILE = os.path.join(BASE_DIR, "normalized_financials.csv")
ALIAS_PATH = os.path.join(BASE_DIR, "config", "aliases.csv")

st.set_page_config(page_title="FinanceX Reviewer", layout="wide")

# -------------------------------------------------
# DATABASE UTILS
# -------------------------------------------------
@st.cache_resource
def get_db_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

@st.cache_data
def load_taxonomy_concepts():
    """Load all valid concepts for the dropdown search."""
    conn = get_db_connection()
    df = pd.read_sql("SELECT element_id, concept_name, source FROM concepts", conn)
    # Create a searchable label: "us-gaap_Revenues (Revenues)"
    df['display'] = df['element_id'] + " (" + df['concept_name'] + ")"
    return df

def save_new_alias(source_label, target_element_id, source_taxonomy):
    """Writes a new correction to aliases.csv."""
    # Check if already exists to prevent duplicates
    try:
        current = pd.read_csv(ALIAS_PATH)
        if source_label in current['alias'].values:
            return False, "Alias already exists!"
    except:
        pass
    
    with open(ALIAS_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Format: source, alias, element_id
        writer.writerow([source_taxonomy, source_label, target_element_id])
    return True, "Success"

# -------------------------------------------------
# UI LAYOUT
# -------------------------------------------------
st.title("FinanceX: Intelligent Review Interface")

# 1. LOAD DATA
if not os.path.exists(NORM_FILE):
    st.error(f"No normalized data found at {NORM_FILE}. Run normalizer.py first.")
    st.stop()

df_norm = pd.read_csv(NORM_FILE)

# Sidebar Stats
st.sidebar.header("Batch Statistics")
total_rows = len(df_norm)
valid_rows = len(df_norm[df_norm['Status'] == 'VALID'])
unmapped_rows = len(df_norm[df_norm['Status'] == 'UNMAPPED'])

st.sidebar.metric("Total Rows", total_rows)
st.sidebar.metric("Mapped (Green)", valid_rows)
st.sidebar.metric("Unmapped (Red)", unmapped_rows, delta_color="inverse")

# 2. MAIN DASHBOARD
tab1, tab2 = st.tabs(["🔍 Audit Data", "🛠️ Fix Unmapped Items"])

with tab1:
    st.markdown("### Normalized Financials")
    
    # Visual Highlights
    def highlight_status(val):
        color = '#d4edda' if val == 'VALID' else '#f8d7da'
        return f'background-color: {color}'

    st.dataframe(
        df_norm.style.applymap(highlight_status, subset=['Status']),
        use_container_width=True,
        column_config={
            "Source_Label": "Input Label",
            "Canonical_Concept": "Mapped To",
            "Statement_Source": "Sheet",
            "Period_Date": "Period"
        }
    )

with tab2:
    st.markdown("### Teach the System")
    st.markdown("Map unknown items here. Changes are saved to `aliases.csv` for future runs.")
    
    # Filter for unmapped items unique list
    unmapped_items = df_norm[df_norm['Status'] == 'UNMAPPED']['Source_Label'].unique()
    
    if len(unmapped_items) == 0:
        st.success("🎉 No unmapped items! The data is clean.")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            selected_label = st.selectbox("Select Unmapped Item", unmapped_items)
            
        with col2:
            # Load taxonomy for search
            concepts_df = load_taxonomy_concepts()
            # Simple fuzzy search simulation via dropdown typing
            target = st.selectbox(
                "Search Official Taxonomy", 
                concepts_df['display'],
                help="Type to search for 'Revenue', 'Assets', etc."
            )
        
        if st.button("Save Mapping"):
            # Extract ID from display string "id (name)"
            target_id = target.split(" (")[0]
            # Determine source (US_GAAP or IFRS) from the dataframe
            target_source = concepts_df[concepts_df['element_id'] == target_id]['source'].values[0]
            
            success, msg = save_new_alias(selected_label, target_id, target_source)
            
            if success:
                st.success(f"✅ Mapped '{selected_label}' -> '{target_id}'")
                st.info("Please re-run 'normalizer.py' to apply these changes.")
            else:
                st.warning(msg)
#!/usr/bin/env python3
"""
Stage 3: Financial Normalizer (The Compiler) - v3 (Robust Split)
================================================================
Updates in v3:
- Splits 'Note' into 'Statement_Source' and 'Period_Date'.
- Prevents CSV column shifting caused by commas in dates.
- Clean separation for downstream LBO/DCF modeling.
"""
import csv
import os
import sys
from mapper.mapper import FinancialMapper

# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "output", "taxonomy_2025.db")
ALIAS_PATH = os.path.join(BASE_DIR, "config", "aliases.csv")
INPUT_FILE = os.path.join(BASE_DIR, "messy_input.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "normalized_financials.csv")

def get_concept_metadata(conn, concept_id):
    if not concept_id:
        return {"balance": "---", "period_type": "---", "type": "---"}
    
    cur = conn.cursor()
    cur.execute("SELECT balance, period_type, data_type FROM concepts WHERE concept_id = ?", (concept_id,))
    row = cur.fetchone()
    if row:
        return {"balance": row[0], "period_type": row[1], "type": row[2]}
    return {"balance": "unknown", "period_type": "unknown", "type": "unknown"}

def main():
    print("="*60)
    print("FINANCIAL NORMALIZER (STAGE 3) - ROBUST SPLIT")
    print("="*60)

    if not os.path.exists(DB_PATH):
        print(f"CRITICAL: Database missing at {DB_PATH}")
        return
    
    mapper = FinancialMapper(DB_PATH, ALIAS_PATH)
    mapper.connect()
    
    if not os.path.exists(INPUT_FILE):
        print(f"CRITICAL: Input file missing at {INPUT_FILE}")
        return

    print(f"Processing {INPUT_FILE}...")
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f_in, \
         open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f_out:
        
        reader = csv.DictReader(f_in)
        
        # New Header Structure: Split Context into Source and Date
        headers = [
            "Source_Label", "Source_Amount", 
            "Statement_Source", "Period_Date", # <--- Split columns
            "Status", "Canonical_Concept", "Concept_ID", "Standard_Label",
            "Balance", "Period_Type", "Map_Method", "Taxonomy"
        ]
        writer = csv.DictWriter(f_out, fieldnames=headers)
        writer.writeheader()
        
        row_count = 0
        mapped_count = 0
        
        for row in reader:
            raw_label = row.get("Line Item", "")
            amount = row.get("Amount", "")
            raw_note = row.get("Note", "--- | ---")
            
            # Robust Split Logic
            if " | " in raw_note:
                sheet_name, period_str = raw_note.split(" | ", 1)
            else:
                sheet_name, period_str = raw_note, "Unknown"

            result = mapper.map_input(raw_label)
            meta = get_concept_metadata(mapper.conn, result["concept_id"])
            
            std_label = "---"
            if result["found"]:
                cur = mapper.conn.cursor()
                cur.execute("SELECT label_text FROM labels WHERE concept_id = ? AND label_role = 'standard' LIMIT 1", (result["concept_id"],))
                res = cur.fetchone()
                if res: std_label = res[0]

            writer.writerow({
                "Source_Label": raw_label,
                "Source_Amount": amount,
                "Statement_Source": sheet_name.strip(),
                "Period_Date": period_str.strip(),
                "Status": "VALID" if result["found"] else "UNMAPPED",
                "Canonical_Concept": result["element_id"] if result["element_id"] else "---",
                "Concept_ID": result["concept_id"] if result["concept_id"] else "---",
                "Standard_Label": std_label,
                "Balance": meta["balance"],
                "Period_Type": meta["period_type"], 
                "Map_Method": result["method"],
                "Taxonomy": result["source"] if result["source"] else "---"
            })
            
            row_count += 1
            if result["found"]: mapped_count += 1

    print(f"\nProcessing Complete.")
    print(f"Rows Processed: {row_count}")
    print(f"Success Rate: {round(mapped_count/row_count*100, 1)}%")
    print(f"Output generated: {OUTPUT_FILE}")
    print("="*60)

if __name__ == "__main__":
    main()
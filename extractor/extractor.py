#!/usr/bin/env python3
"""
Stage 4: Strict Financial Extractor
===================================
Standardized Extractor for the FinanceX System.

It relies on the 'Standard Submission Format':
1. File must have tabs named 'Income Statement', 'Balance Sheet', 'Cash Flow'.
2. Row 1 (Header) must contain Dates.
3. Column A must contain Line Item Labels.
4. No logos/merged cells at the top.
"""
import pandas as pd
import os
import sys

# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(BASE_DIR, "messy_input.csv")

def extract_standardized_excel(excel_path):
    print(f"Reading Standardized File: {os.path.basename(excel_path)}...")
    
    # Load all sheets. header=0 implies Row 1 is the header (Dates)
    try:
        xls = pd.read_excel(excel_path, sheet_name=None, header=0)
    except Exception as e:
        print(f"CRITICAL ERROR: Could not read Excel file. {e}")
        return []
    
    extracted_rows = []
    
    for sheet_name, df in xls.items():
        print(f"  Processing Tab: '{sheet_name}'")
        
        # 1. Validate Column A (Labels)
        # Pandas reads the first column header as the index name or 'Unnamed: 0' if empty
        # We rename the first column to "Label" for consistency
        df.rename(columns={df.columns[0]: 'Label'}, inplace=True)
        
        # 2. Identify Date Columns
        # All columns except the first one ('Label') are treated as Date/Period columns
        date_columns = [c for c in df.columns if c != 'Label']
        
        if not date_columns:
            print(f"    -> Warning: No date columns found in '{sheet_name}'. Skipping.")
            continue
            
        print(f"    -> Detected Periods: {date_columns}")

        # 3. Unpivot (Melt) the Data
        # Transforms wide format (Years across top) to long format (Row per value)
        for _, row in df.iterrows():
            raw_label = str(row['Label']).strip()
            
            # Skip empty or junk rows
            if not raw_label or raw_label.lower() in ['nan', 'none', '']:
                continue
            
            for period in date_columns:
                val = row[period]
                
                # Cleanup formatting (handle parentheses for negatives)
                try:
                    val_str = str(val).replace(',', '').replace(' ', '')
                    if '(' in val_str and ')' in val_str:
                        val_str = '-' + val_str.replace('(', '').replace(')', '')
                    
                    amount = float(val_str)
                    
                    extracted_rows.append({
                        "Line Item": raw_label,
                        "Amount": amount,
                        "Note": f"{sheet_name} | {period}" # Captures "Income Statement | 2023"
                    })
                except:
                    # Value wasn't a number, skip (probably a sub-header)
                    continue

    return extracted_rows

def main():
    # Default to a test file if none provided
    input_path = os.path.join(BASE_DIR, "standardized_financials.xlsx")
    
    if len(sys.argv) > 1:
        input_path = sys.argv[1]

    if not os.path.exists(input_path):
        print(f"Error: File not found at {input_path}")
        print("Run 'python generate_standardized_test.py' first!")
        return

    data = extract_standardized_excel(input_path)
    
    if not data:
        print("No data extracted. Ensure tabs are named correctly and format is clean.")
        return

    # Save to the CSV format that Stage 3 (Normalizer) expects
    df_out = pd.DataFrame(data)
    df_out.to_csv(OUTPUT_FILE, index=False)
    
    print("\nExtraction Complete!")
    print(f"Generated {len(data)} rows.")
    print(f"Saved to: {OUTPUT_FILE}")
    print("Now run: python normalizer.py")

if __name__ == "__main__":
    main()
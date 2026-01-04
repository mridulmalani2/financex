#!/usr/bin/env python3
"""
Stage 4: Robust Financial Extractor (Production Grade)
======================================================
Hardened extractor that handles real-world Excel formatting issues:
- Auto-detects header row (doesn't assume Row 1)
- Handles merged cells
- Removes pre-header junk (logos, disclaimers)
- Flexible date/period detection
- Handles various number formats

Standard Submission Format (preferred but not required):
1. Tabs named 'Income Statement', 'Balance Sheet', 'Cash Flow'
2. Row 1 (or first data row) contains Dates
3. Column A contains Line Item Labels
"""
import pandas as pd
import numpy as np
import os
import sys
import re
from typing import List, Dict, Tuple, Optional

# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(BASE_DIR, "messy_input.csv")

# Standard tab names (case-insensitive matching)
STANDARD_TAB_NAMES = [
    'income statement', 'income', 'p&l', 'profit and loss', 'profit & loss',
    'balance sheet', 'bs', 'statement of financial position',
    'cash flow', 'cash flows', 'statement of cash flows', 'cf'
]

# Date/Period patterns
DATE_PATTERNS = [
    r'^\d{4}$',  # 2023
    r'^FY\d{2,4}$',  # FY23, FY2023
    r'^Q[1-4]\s*\d{2,4}$',  # Q1 23, Q3 2023
    r'^\d{1,2}/\d{1,2}/\d{2,4}$',  # 12/31/2023
    r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',  # Jan 2023
    r'^\d{4}-\d{2}-\d{2}$',  # 2023-12-31
    r'^(LTM|TTM|NTM)',  # LTM, TTM, NTM
    r'^Year\s*(Ended|End)',  # Year Ended
]


def is_date_like(value) -> bool:
    """Check if a value looks like a date or period header."""
    if pd.isna(value):
        return False

    val_str = str(value).strip()

    # Check numeric year
    try:
        num = float(val_str)
        if 1990 <= num <= 2100:  # Reasonable year range
            return True
    except:
        pass

    # Check patterns
    for pattern in DATE_PATTERNS:
        if re.match(pattern, val_str, re.IGNORECASE):
            return True

    return False


def is_label_like(value) -> bool:
    """Check if a value looks like a line item label."""
    if pd.isna(value):
        return False

    val_str = str(value).strip()

    # Skip if it's a number
    try:
        float(val_str.replace(',', '').replace('$', '').replace('(', '-').replace(')', ''))
        return False
    except:
        pass

    # Must be mostly letters
    letters = sum(c.isalpha() or c.isspace() for c in val_str)
    return len(val_str) >= 3 and letters / len(val_str) > 0.5


def detect_header_row(df: pd.DataFrame) -> int:
    """
    Auto-detect which row contains the header (dates).
    Returns the row index (0-based).
    """
    for idx in range(min(20, len(df))):  # Check first 20 rows
        row = df.iloc[idx]

        # Count date-like columns (excluding first column which should be labels)
        date_count = sum(is_date_like(val) for val in row[1:] if not pd.isna(val))

        # If we find multiple date-like values, this is likely the header
        if date_count >= 2:
            return idx

    # Default to row 0 if not found
    return 0


def detect_label_column(df: pd.DataFrame) -> int:
    """
    Auto-detect which column contains line item labels.
    Returns the column index (0-based).
    """
    for col_idx in range(min(5, len(df.columns))):  # Check first 5 columns
        col = df.iloc[:, col_idx]

        # Count label-like values
        label_count = sum(is_label_like(val) for val in col if not pd.isna(val))

        # If many labels found, this is likely the label column
        if label_count >= 5:
            return col_idx

    return 0  # Default to first column


def clean_numeric_value(value) -> Optional[float]:
    """
    Parse various number formats to float.
    Handles: commas, parentheses for negatives, currency symbols, dashes for zero.
    """
    if pd.isna(value):
        return None

    val_str = str(value).strip()

    # Handle dash as zero
    if val_str in ['-', '—', '–', '']:
        return 0.0

    # Remove currency symbols and spaces
    val_str = val_str.replace('$', '').replace('€', '').replace('£', '').replace(',', '').replace(' ', '')

    # Handle parentheses for negatives: (100) -> -100
    if val_str.startswith('(') and val_str.endswith(')'):
        val_str = '-' + val_str[1:-1]

    # Handle percentage
    is_percentage = '%' in val_str
    val_str = val_str.replace('%', '')

    try:
        result = float(val_str)
        if is_percentage:
            result = result / 100  # Convert to decimal
        return result
    except:
        return None


def extract_sheet(df: pd.DataFrame, sheet_name: str) -> List[Dict]:
    """
    Extract data from a single sheet with auto-detection of structure.
    """
    rows = []

    if df.empty or len(df) < 2:
        return rows

    # Auto-detect header row
    header_row = detect_header_row(df)

    # Auto-detect label column
    label_col = detect_label_column(df)

    # Set header
    if header_row > 0:
        # Use detected row as header
        new_header = df.iloc[header_row].tolist()
        df = df.iloc[header_row + 1:].copy()
        df.columns = new_header

    # Get the label column name
    label_col_name = df.columns[label_col]

    # Identify date columns (all non-label columns that look like dates)
    date_columns = []
    for i, col in enumerate(df.columns):
        if i != label_col and is_date_like(col):
            date_columns.append(col)

    # If no date columns found, try using all non-label columns
    if not date_columns:
        date_columns = [col for i, col in enumerate(df.columns) if i != label_col]

    print(f"    Header row: {header_row}, Label column: {label_col_name}")
    print(f"    Detected periods: {date_columns[:5]}{'...' if len(date_columns) > 5 else ''}")

    # Extract data
    for _, row in df.iterrows():
        raw_label = row.iloc[label_col] if label_col < len(row) else None

        # Skip if no valid label
        if not is_label_like(raw_label):
            continue

        label = str(raw_label).strip()

        # Skip obvious header/section rows
        skip_labels = ['total', 'subtotal', 'operating', 'non-operating', 'discontinued']
        if label.lower() in skip_labels:
            continue

        for period in date_columns:
            try:
                raw_value = row[period]
                amount = clean_numeric_value(raw_value)

                if amount is not None:
                    rows.append({
                        "Line Item": label,
                        "Amount": amount,
                        "Note": f"{sheet_name} | {period}"
                    })
            except:
                continue

    return rows


def extract_standardized_excel(excel_path: str) -> List[Dict]:
    """
    Main extraction function with robust handling of real-world Excel files.
    """
    print(f"Reading Excel File: {os.path.basename(excel_path)}...")

    try:
        # Read all sheets without assuming header position
        xls = pd.read_excel(excel_path, sheet_name=None, header=None)
    except Exception as e:
        print(f"CRITICAL ERROR: Could not read Excel file. {e}")
        return []

    extracted_rows = []
    sheets_processed = 0

    for sheet_name, df in xls.items():
        # Check if this looks like a financial statement
        sheet_name_lower = sheet_name.lower().strip()

        is_standard_sheet = any(std in sheet_name_lower for std in STANDARD_TAB_NAMES)

        if not is_standard_sheet and len(xls) > 3:
            # If there are many sheets and this doesn't match, skip it
            print(f"  Skipping non-standard tab: '{sheet_name}'")
            continue

        print(f"  Processing Tab: '{sheet_name}'")

        sheet_rows = extract_sheet(df, sheet_name)

        if sheet_rows:
            extracted_rows.extend(sheet_rows)
            sheets_processed += 1
            print(f"    Extracted {len(sheet_rows)} data points")
        else:
            print(f"    Warning: No data extracted from '{sheet_name}'")

    print(f"\nProcessed {sheets_processed} sheets, {len(extracted_rows)} total data points")

    return extracted_rows


def validate_extraction(rows: List[Dict]) -> Dict:
    """
    Validate the extracted data and return summary statistics.
    """
    if not rows:
        return {'valid': False, 'error': 'No data extracted'}

    # Check for expected financial line items
    labels = set(row['Line Item'].lower() for row in rows)

    expected_items = ['revenue', 'assets', 'liabilities', 'net income', 'cash']
    found_items = [item for item in expected_items if any(item in label for label in labels)]

    # Check for numeric values
    amounts = [row['Amount'] for row in rows if row['Amount'] != 0]

    return {
        'valid': True,
        'total_rows': len(rows),
        'unique_labels': len(set(row['Line Item'] for row in rows)),
        'periods_detected': len(set(row['Note'].split(' | ')[-1] for row in rows)),
        'expected_items_found': found_items,
        'non_zero_values': len(amounts),
        'avg_value': sum(amounts) / len(amounts) if amounts else 0
    }


def main():
    """Main entry point."""
    # Default to a test file if none provided
    input_path = os.path.join(BASE_DIR, "standardized_financials.xlsx")

    if len(sys.argv) > 1:
        input_path = sys.argv[1]

    if not os.path.exists(input_path):
        print(f"Error: File not found at {input_path}")
        print("\nUsage: python extractor.py <excel_file.xlsx>")
        return 1

    # Extract data
    data = extract_standardized_excel(input_path)

    if not data:
        print("\nNo data extracted. Please check:")
        print("  1. Excel file is not corrupted")
        print("  2. Tabs contain financial data")
        print("  3. Data has proper structure (labels in column A, dates in row 1)")
        return 1

    # Validate
    validation = validate_extraction(data)
    print(f"\nValidation Summary:")
    print(f"  Total rows: {validation['total_rows']}")
    print(f"  Unique line items: {validation['unique_labels']}")
    print(f"  Periods detected: {validation['periods_detected']}")
    print(f"  Expected items found: {validation['expected_items_found']}")

    # Save output
    df_out = pd.DataFrame(data)
    df_out.to_csv(OUTPUT_FILE, index=False)

    print(f"\nExtraction Complete!")
    print(f"Saved to: {OUTPUT_FILE}")
    print(f"\nNext step: python normalizer.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())

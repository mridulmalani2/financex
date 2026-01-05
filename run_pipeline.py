#!/usr/bin/env python3
"""
FinanceX: Production V1.0 - Unified End-to-End Pipeline
=========================================================
Automated Financial Workbench for Investment Banking

PRODUCTION V1.0 - CLEAN SLATE ARCHITECTURE:
├── temp_session/      Created on launch, wiped on exit. Stores current upload.
├── taxonomy/          ReadOnly DB. XBRL taxonomy data.
├── output/            Stores final models (DCF, LBO, Comps).
└── logs/              Stores the "Thinking" logs from the iterative engine.

NO TEST FILES: This pipeline only processes user-uploaded files.
               References to client_upload.xlsx have been removed.

Pipeline Stages:
  1. Extract data from Excel (Extractor)
  2. Map and normalize to XBRL taxonomy (Normalizer)
  3. Generate IB-ready datasets via Iterative Thinking Engine
  4. Validate and quality check (Validation)

Usage:
  python run_pipeline.py <excel_file.xlsx> [--output-dir <dir>]

Example:
  python run_pipeline.py user_financials.xlsx
  python run_pipeline.py apple_10k.xlsx --output-dir ./apple_models
"""
import os
import sys
import argparse
from datetime import datetime

# Ensure imports work
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Import Clean Slate architecture
from session_manager import (
    initialize_clean_slate,
    get_clean_slate_paths,
    write_thinking_log,
    append_thinking_log,
    TEMP_SESSION_DIR,
    OUTPUT_DIR,
    LOGS_DIR,
    TAXONOMY_DIR
)


def print_banner():
    """Print the FinanceX banner."""
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   ███████╗██╗███╗   ██╗ █████╗ ███╗   ██╗ ██████╗███████╗██╗  ██╗    ║
║   ██╔════╝██║████╗  ██║██╔══██╗████╗  ██║██╔════╝██╔════╝╚██╗██╔╝    ║
║   █████╗  ██║██╔██╗ ██║███████║██╔██╗ ██║██║     █████╗   ╚███╔╝     ║
║   ██╔══╝  ██║██║╚██╗██║██╔══██║██║╚██╗██║██║     ██╔══╝   ██╔██╗     ║
║   ██║     ██║██║ ╚████║██║  ██║██║ ╚████║╚██████╗███████╗██╔╝ ██╗    ║
║   ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝╚═╝  ╚═╝    ║
║                                                                       ║
║   Automated Financial Workbench for Investment Banking               ║
║   Quality: JPMC / Citadel Grade                                       ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)


def run_extractor(excel_path: str, output_dir: str) -> str:
    """Run the extractor to convert Excel to CSV."""
    from extractor.extractor import extract_standardized_excel
    import pandas as pd

    print("\n" + "=" * 70)
    print("STAGE 1: EXTRACTION")
    print("=" * 70)
    print(f"Input: {excel_path}")

    data = extract_standardized_excel(excel_path)

    if not data:
        raise ValueError("No data extracted. Check Excel format and tab names.")

    output_file = os.path.join(output_dir, "messy_input.csv")
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)

    print(f"\nExtracted {len(data)} rows")
    print(f"Output: {output_file}")

    return output_file


def run_normalizer(messy_file: str, output_dir: str) -> str:
    """Run the normalizer to map to XBRL taxonomy."""
    import csv
    from mapper.mapper import FinancialMapper

    print("\n" + "=" * 70)
    print("STAGE 2: NORMALIZATION & MAPPING")
    print("=" * 70)

    # Use Clean Slate taxonomy path (falls back to output for DB)
    db_path = os.path.join(OUTPUT_DIR, "taxonomy_2025.db")
    if not os.path.exists(db_path):
        # Try taxonomy directory
        db_path = os.path.join(TAXONOMY_DIR, "taxonomy_2025.db")
    alias_path = os.path.join(BASE_DIR, "config", "aliases.csv")
    output_file = os.path.join(output_dir, "normalized_financials.csv")

    # Initialize mapper
    print("Loading taxonomy and aliases...")
    mapper = FinancialMapper(db_path, alias_path)
    mapper.connect()

    # Process input
    print(f"Processing {messy_file}...")

    with open(messy_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', newline='', encoding='utf-8') as f_out:

        reader = csv.DictReader(f_in)

        headers = [
            "Source_Label", "Source_Amount",
            "Statement_Source", "Period_Date",
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

            # Split note
            if " | " in raw_note:
                sheet_name, period_str = raw_note.split(" | ", 1)
            else:
                sheet_name, period_str = raw_note, "Unknown"

            # Map
            result = mapper.map_input(raw_label)
            meta = mapper.get_concept_metadata(result.get("concept_id"))
            std_label = mapper.get_standard_label(result.get("concept_id")) or "---"

            writer.writerow({
                "Source_Label": raw_label,
                "Source_Amount": amount,
                "Statement_Source": sheet_name.strip(),
                "Period_Date": period_str.strip(),
                "Status": "VALID" if result["found"] else "UNMAPPED",
                "Canonical_Concept": result["element_id"] or "---",
                "Concept_ID": result["concept_id"] or "---",
                "Standard_Label": std_label,
                "Balance": meta.get("balance") or "---",
                "Period_Type": meta.get("period_type") or "---",
                "Map_Method": result["method"],
                "Taxonomy": result["source"] or "---"
            })

            row_count += 1
            if result["found"]:
                mapped_count += 1

    success_rate = round(mapped_count / row_count * 100, 1) if row_count > 0 else 0
    print(f"\nProcessed: {row_count} rows")
    print(f"Mapped: {mapped_count} ({success_rate}%)")
    print(f"Unmapped: {row_count - mapped_count}")
    print(f"Output: {output_file}")

    return output_file


def run_engine(normalized_file: str, output_dir: str) -> dict:
    """Run the financial engine to generate IB models."""
    from modeler.engine import FinancialEngine

    print("\n" + "=" * 70)
    print("STAGE 3: FINANCIAL MODELING")
    print("=" * 70)

    # Create models directory
    models_dir = os.path.join(output_dir, "final_ib_models")
    os.makedirs(models_dir, exist_ok=True)

    # Initialize engine
    print("Initializing Financial Engine...")
    engine = FinancialEngine(normalized_file)
    print(f"  Loaded {len(engine.df)} validated rows")
    print(f"  Periods: {engine.dates}")

    outputs = {}

    # DCF
    print("\n[1/4] Building DCF Historical Setup...")
    dcf = engine.build_dcf_ready_view()
    dcf_path = os.path.join(models_dir, "DCF_Historical_Setup.csv")
    dcf.to_csv(dcf_path)
    outputs['dcf'] = dcf_path
    print(f"  -> {dcf_path} ({len(dcf)} metrics)")

    # LBO
    print("\n[2/4] Building LBO Credit Statistics...")
    lbo = engine.build_lbo_ready_view()
    lbo_path = os.path.join(models_dir, "LBO_Credit_Stats.csv")
    lbo.to_csv(lbo_path)
    outputs['lbo'] = lbo_path
    print(f"  -> {lbo_path} ({len(lbo)} metrics)")

    # Comps
    print("\n[3/4] Building Comps Trading Metrics...")
    comps = engine.build_comps_ready_view()
    comps_path = os.path.join(models_dir, "Comps_Trading_Metrics.csv")
    comps.to_csv(comps_path)
    outputs['comps'] = comps_path
    print(f"  -> {comps_path} ({len(comps)} metrics)")

    # Validation
    print("\n[4/4] Running Validation...")
    validation = engine.run_validation()
    val_path = os.path.join(models_dir, "Validation_Report.csv")
    validation.to_csv(val_path, index=False)
    outputs['validation'] = val_path

    if len(validation) > 0:
        pass_count = len(validation[validation['Status'] == 'PASS'])
        fail_count = len(validation[validation['Status'] == 'FAIL'])
        warn_count = len(validation[validation['Status'] == 'WARN'])
        print(f"  -> {val_path}")
        print(f"     Results: {pass_count} PASS, {warn_count} WARN, {fail_count} FAIL")

    # Audit Reports
    print("\n[5/5] Generating Audit Reports...")
    unmapped = engine.get_unmapped_report()
    if len(unmapped) > 0:
        unmapped_path = os.path.join(models_dir, "Unmapped_Data_Report.csv")
        unmapped.to_csv(unmapped_path, index=False)
        outputs['unmapped'] = unmapped_path
        print(f"  WARNING: {len(unmapped)} unmapped rows - see {unmapped_path}")
    else:
        print(f"  All data mapped successfully")

    hierarchy = engine.get_hierarchy_resolution_report()
    if len(hierarchy) > 0:
        hierarchy_path = os.path.join(models_dir, "Hierarchy_Resolution_Report.csv")
        hierarchy.to_csv(hierarchy_path, index=False)
        outputs['hierarchy'] = hierarchy_path
        print(f"  Hierarchy conflicts resolved: {len(hierarchy)} - see {hierarchy_path}")

    return outputs


def run_pipeline_programmatic(excel_path: str, output_dir: str,
                              quiet: bool = False) -> dict:
    """
    Programmatic interface for the pipeline.

    This is the stateless function: Input Path -> Process -> Output Paths

    Args:
        excel_path: Path to the input Excel file
        output_dir: Directory for all output files
        quiet: If True, suppress console output

    Returns:
        dict with status and file paths:
        {
            "success": bool,
            "error": str or None,
            "duration": float (seconds),
            "files": {
                "messy_input": str,
                "normalized": str,
                "dcf": str,
                "lbo": str,
                "comps": str,
                "validation": str,
                ...
            }
        }
    """
    import io
    import contextlib

    result = {
        "success": False,
        "error": None,
        "duration": 0,
        "files": {}
    }

    # Validate input
    if not os.path.exists(excel_path):
        result["error"] = f"File not found: {excel_path}"
        return result

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    start_time = datetime.now()

    # Optionally suppress output
    if quiet:
        output_capture = io.StringIO()
        context = contextlib.redirect_stdout(output_capture)
    else:
        context = contextlib.nullcontext()

    try:
        with context:
            # Stage 1: Extract
            messy_file = run_extractor(excel_path, output_dir)
            result["files"]["messy_input"] = messy_file

            # Stage 2: Normalize
            normalized_file = run_normalizer(messy_file, output_dir)
            result["files"]["normalized"] = normalized_file

            # Stage 3: Generate Models
            outputs = run_engine(normalized_file, output_dir)
            result["files"].update(outputs)

        result["success"] = True

    except Exception as e:
        result["error"] = str(e)
        import traceback
        result["traceback"] = traceback.format_exc()

    end_time = datetime.now()
    result["duration"] = (end_time - start_time).total_seconds()

    return result


def main():
    """Main entry point with Clean Slate architecture."""
    parser = argparse.ArgumentParser(
        description="FinanceX: Automated Financial Workbench for Investment Banking"
    )
    parser.add_argument(
        "excel_file",
        help="Path to the Excel file with financial statements"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=None,
        help="Output directory (default: output/)"
    )
    parser.add_argument(
        "--clean-slate",
        action="store_true",
        help="Initialize clean slate directories on startup"
    )

    args = parser.parse_args()

    # Validate input
    if not os.path.exists(args.excel_file):
        print(f"ERROR: File not found: {args.excel_file}")
        return 1

    # Initialize Clean Slate if requested
    if args.clean_slate:
        initialize_clean_slate()

    # Use Clean Slate output directory by default
    output_dir = args.output_dir if args.output_dir else OUTPUT_DIR

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "final_ib_models"), exist_ok=True)

    # Print banner
    print_banner()

    start_time = datetime.now()
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Input File: {args.excel_file}")
    print(f"Output Directory: {output_dir}")

    # Start thinking log
    thinking_log = os.path.join(LOGS_DIR, "pipeline_thinking.log")
    os.makedirs(LOGS_DIR, exist_ok=True)
    append_thinking_log(f"Pipeline started for: {args.excel_file}", thinking_log)

    try:
        # Stage 1: Extract
        append_thinking_log("Stage 1: Beginning extraction...", thinking_log)
        messy_file = run_extractor(args.excel_file, output_dir)
        append_thinking_log(f"Stage 1 complete: {messy_file}", thinking_log)

        # Stage 2: Normalize
        append_thinking_log("Stage 2: Beginning normalization...", thinking_log)
        normalized_file = run_normalizer(messy_file, output_dir)
        append_thinking_log(f"Stage 2 complete: {normalized_file}", thinking_log)

        # Stage 3: Generate Models (with Iterative Thinking Engine)
        append_thinking_log("Stage 3: Beginning financial modeling with Iterative Thinking Engine...", thinking_log)
        outputs = run_engine(normalized_file, output_dir)
        append_thinking_log(f"Stage 3 complete: Generated {len(outputs)} outputs", thinking_log)

        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("\n" + "=" * 70)
        print("PIPELINE COMPLETE")
        print("=" * 70)
        print(f"Duration: {duration:.1f} seconds")
        print(f"\nGenerated Files:")
        print(f"  - {outputs.get('dcf', 'N/A')}")
        print(f"  - {outputs.get('lbo', 'N/A')}")
        print(f"  - {outputs.get('comps', 'N/A')}")
        print(f"  - {outputs.get('validation', 'N/A')}")
        print(f"\nThinking Log: {thinking_log}")
        print("\nThese files are JPMC/Citadel-grade and ready for:")
        print("  - DCF Valuation Modeling")
        print("  - LBO / Leverage Analysis")
        print("  - Trading Comparables Analysis")
        print("=" * 70)

        append_thinking_log(f"Pipeline complete. Duration: {duration:.1f}s", thinking_log)
        return 0

    except Exception as e:
        error_msg = f"Pipeline failed - {e}"
        print(f"\nERROR: {error_msg}")
        append_thinking_log(f"ERROR: {error_msg}", thinking_log)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

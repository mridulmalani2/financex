#!/usr/bin/env python3
"""
Stage 6: Investment Banking Model Generator
============================================
Generates JPMC/Citadel-grade financial datasets:
  - DCF Historical Setup (Valuation)
  - LBO Credit Statistics (Leverage)
  - Comps Trading Metrics (Relative Valuation)
  - Validation Report (Quality Assurance)

Usage:
  python run_ib_model.py [normalized_financials.csv]

Output:
  final_ib_models/
    ├── DCF_Historical_Setup.csv
    ├── LBO_Credit_Stats.csv
    ├── Comps_Trading_Metrics.csv
    └── Validation_Report.csv
"""
import os
import sys

# Ensure we can import from parent
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modeler.engine import FinancialEngine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUT = os.path.join(BASE_DIR, "normalized_financials.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "final_ib_models")


def main():
    print("=" * 70)
    print("FINANCEX: INVESTMENT BANKING MODEL GENERATOR")
    print("=" * 70)
    print("Output Quality: JPMC/Citadel Grade")
    print("-" * 70)

    # Determine input file
    input_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT

    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}")
        print("\nTo generate this file, run:")
        print("  1. python extractor/extractor.py <your_excel_file.xlsx>")
        print("  2. python normalizer.py")
        return 1

    print(f"Input: {input_file}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print("-" * 70)

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Initialize engine
    print("\nInitializing Financial Engine...")
    try:
        engine = FinancialEngine(input_file)
        print(f"  Loaded {len(engine.df)} validated rows")
        print(f"  Periods detected: {engine.dates}")
    except Exception as e:
        print(f"ERROR: Failed to initialize engine: {e}")
        return 1

    # Generate DCF Model
    print("\n[1/4] Building DCF Historical Setup...")
    try:
        dcf = engine.build_dcf_ready_view()
        dcf_path = os.path.join(OUTPUT_DIR, "DCF_Historical_Setup.csv")
        dcf.to_csv(dcf_path)
        print(f"  Generated: {dcf_path}")
        print(f"  Metrics: {len(dcf)} rows")
    except Exception as e:
        print(f"  ERROR: {e}")

    # Generate LBO Model
    print("\n[2/4] Building LBO Credit Statistics...")
    try:
        lbo = engine.build_lbo_ready_view()
        lbo_path = os.path.join(OUTPUT_DIR, "LBO_Credit_Stats.csv")
        lbo.to_csv(lbo_path)
        print(f"  Generated: {lbo_path}")
        print(f"  Metrics: {len(lbo)} rows")
    except Exception as e:
        print(f"  ERROR: {e}")

    # Generate Comps Model
    print("\n[3/4] Building Comps Trading Metrics...")
    try:
        comps = engine.build_comps_ready_view()
        comps_path = os.path.join(OUTPUT_DIR, "Comps_Trading_Metrics.csv")
        comps.to_csv(comps_path)
        print(f"  Generated: {comps_path}")
        print(f"  Metrics: {len(comps)} rows")
    except Exception as e:
        print(f"  ERROR: {e}")

    # Run Validation
    print("\n[4/4] Running Cross-Statement Validation...")
    try:
        validation = engine.run_validation()
        validation_path = os.path.join(OUTPUT_DIR, "Validation_Report.csv")
        validation.to_csv(validation_path, index=False)
        print(f"  Generated: {validation_path}")

        # Summary
        if len(validation) > 0:
            pass_count = len(validation[validation['Status'] == 'PASS'])
            fail_count = len(validation[validation['Status'] == 'FAIL'])
            warn_count = len(validation[validation['Status'] == 'WARN'])
            print(f"  Results: {pass_count} PASS, {warn_count} WARN, {fail_count} FAIL")
    except Exception as e:
        print(f"  ERROR: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)
    print(f"\nOutput files in: {OUTPUT_DIR}/")
    print("  - DCF_Historical_Setup.csv    (Valuation Model)")
    print("  - LBO_Credit_Stats.csv        (Leverage Analysis)")
    print("  - Comps_Trading_Metrics.csv   (Trading Comparables)")
    print("  - Validation_Report.csv       (Quality Assurance)")
    print("\nThese files are ready for direct import into Excel/Google Sheets")
    print("for DCF, LBO, and Comps analysis.")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())

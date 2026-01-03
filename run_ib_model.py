#!/usr/bin/env python3
import os
import pandas as pd
from modeler.engine import FinancialEngine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NORM_FILE = os.path.join(BASE_DIR, "normalized_financials.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "final_ib_models")

def main():
    if not os.path.exists(NORM_FILE):
        print("Error: No normalized data found. Run normalizer.py first.")
        return

    print("Initializing Financial Structuring Engine...")
    engine = FinancialEngine(NORM_FILE)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. DCF Ready Data
    print("Generating DCF Historical Data...")
    df_dcf = engine.build_dcf_ready_view()
    df_dcf.to_csv(os.path.join(OUTPUT_DIR, "DCF_Historical_Setup.csv"))

    # 2. LBO Ready Data
    print("Generating LBO Cap Structure Data...")
    df_lbo = engine.build_lbo_ready_view()
    df_lbo.to_csv(os.path.join(OUTPUT_DIR, "LBO_Credit_Stats.csv"))

    # 3. Comps Ready Data
    print("Generating Comps Trading Data...")
    df_comps = engine.build_comps_ready_view()
    df_comps.to_csv(os.path.join(OUTPUT_DIR, "Comps_Trading_Metrics.csv"))

    print("\nSUCCESS: 3 Clean IB Datasets generated in 'final_ib_models/'")

if __name__ == "__main__":
    main()
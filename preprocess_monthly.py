#!/usr/bin/env python3
"""
Preprocess Daily Data to Monthly Aggregates
Converts daily precipitation and runoff data to monthly sums for all basins.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

BASIN_LIST = "/icebox/data/shares/mh2/mosavat/Lumped/temporal_test_basins.txt"
INPUT_DIR = "/icebox/data/shares/mh2/mosavat/Lumped/data/processed/temporal_test/timeseries"
OUTPUT_DIR = "/icebox/data/shares/mh2/mosavat/Lumped/data/processed/temporal_test/timeseries_monthly"

print("="*70)
print("DAILY TO MONTHLY DATA PREPROCESSING")
print("="*70)

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================================
# LOAD BASIN LIST
# ============================================================================

print("\n[1/3] Loading basin list...")
with open(BASIN_LIST, 'r') as f:
    basin_ids = [line.strip() for line in f.readlines()]

print(f"   Total basins: {len(basin_ids)}")

# ============================================================================
# PROCESS EACH BASIN
# ============================================================================

print("\n[2/3] Converting daily to monthly data...")

success_count = 0
error_count = 0
errors = []

for i, basin_id in enumerate(basin_ids, 1):
    try:
        # Load daily data
        input_file = os.path.join(INPUT_DIR, f"{basin_id}.csv")
        df = pd.read_csv(input_file)
        
        # Parse date column
        df['date'] = pd.to_datetime(df['date'])
        
        # Set date as index for resampling
        df = df.set_index('date')
        
        # Extract only precipitation and runoff
        daily_data = df[['prcp', 'runoff']].copy()
        
        # Resample to monthly (sum both precipitation and runoff)
        monthly_data = daily_data.resample('M').sum()
        
        # Reset index to get date as column
        monthly_data = monthly_data.reset_index()
        
        # Rename date column to year_month for clarity
        monthly_data['year_month'] = monthly_data['date'].dt.to_period('M')
        
        # Keep both date and year_month
        monthly_data = monthly_data[['date', 'year_month', 'prcp', 'runoff']]
        
        # Save monthly data
        output_file = os.path.join(OUTPUT_DIR, f"{basin_id}.csv")
        monthly_data.to_csv(output_file, index=False)
        
        success_count += 1
        
        if i % 100 == 0:
            print(f"   Processed {i}/{len(basin_ids)} basins...")
            
    except Exception as e:
        error_count += 1
        errors.append((basin_id, str(e)))
        print(f"   Error processing {basin_id}: {e}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n[3/3] Processing complete!")
print("="*70)
print(f"Successfully processed: {success_count} basins")
print(f"Errors: {error_count} basins")

if error_count > 0:
    print("\nBasins with errors:")
    for basin_id, error in errors[:10]:  # Show first 10 errors
        print(f"  {basin_id}: {error}")
    if len(errors) > 10:
        print(f"  ... and {len(errors)-10} more")

print(f"\nMonthly data saved to: {OUTPUT_DIR}")
print("="*70)

# Show example of first basin
if success_count > 0:
    print("\nExample: First basin monthly data")
    example_file = os.path.join(OUTPUT_DIR, f"{basin_ids[0]}.csv")
    example_df = pd.read_csv(example_file)
    print(example_df.head(12))
    print(f"\nTotal months: {len(example_df)}")
    print(f"Expected: ~120 months (10 years)")

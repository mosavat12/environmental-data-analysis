#!/usr/bin/env python3
"""
Merge individual basin results into a single CSV file.
"""

import os
import pandas as pd
import glob

# Paths
temp_dir = "/icebox/data/shares/mh2/mosavat/Lumped/results/temp"
output_file = "/icebox/data/shares/mh2/mosavat/Lumped/results/all_basins_results.csv"

print("Merging basin results...")

# Find all temporary result files
result_files = sorted(glob.glob(f"{temp_dir}/basin_*.csv"))

print(f"Found {len(result_files)} result files")

if len(result_files) == 0:
    print("Error: No result files found!")
    exit(1)

# Read and concatenate all results
all_results = []

for result_file in result_files:
    try:
        df = pd.read_csv(result_file)
        all_results.append(df)
    except Exception as e:
        print(f"Warning: Could not read {result_file}: {e}")

# Combine into single DataFrame
combined_df = pd.concat(all_results, ignore_index=True)

# Sort by basin_id
combined_df = combined_df.sort_values('basin_id').reset_index(drop=True)

# Save to final output file
os.makedirs(os.path.dirname(output_file), exist_ok=True)
combined_df.to_csv(output_file, index=False)

print(f"Successfully merged {len(combined_df)} basins")
print(f"Results saved to: {output_file}")

# Print summary statistics
print("\n" + "="*60)
print("SUMMARY STATISTICS")
print("="*60)

print(f"\nTotal basins analyzed: {len(combined_df)}")

print("\nSpearman Correlation:")
print(f"  Mean: {combined_df['spearman_rho'].mean():.4f}")
print(f"  Std:  {combined_df['spearman_rho'].std():.4f}")
print(f"  Min:  {combined_df['spearman_rho'].min():.4f}")
print(f"  Max:  {combined_df['spearman_rho'].max():.4f}")

print("\nKendall's Tau:")
print(f"  Mean: {combined_df['kendall_tau'].mean():.4f}")
print(f"  Std:  {combined_df['kendall_tau'].std():.4f}")

print("\nTail Dependence:")
print(f"  Upper (?_U): Mean={combined_df['chi_upper'].mean():.4f}, Std={combined_df['chi_upper'].std():.4f}")
print(f"  Lower (?_L): Mean={combined_df['chi_lower'].mean():.4f}, Std={combined_df['chi_lower'].std():.4f}")

print("\nBest Copula Distribution:")
copula_counts = combined_df['best_copula'].value_counts()
for copula, count in copula_counts.items():
    print(f"  {copula}: {count} ({count/len(combined_df)*100:.1f}%)")

print("\nSignificant Correlations (p < 0.05):")
sig_spearman = (combined_df['spearman_pvalue'] < 0.05).sum()
sig_kendall = (combined_df['kendall_pvalue'] < 0.05).sum()
print(f"  Spearman: {sig_spearman}/{len(combined_df)} ({sig_spearman/len(combined_df)*100:.1f}%)")
print(f"  Kendall:  {sig_kendall}/{len(combined_df)} ({sig_kendall/len(combined_df)*100:.1f}%)")

print("\n" + "="*60)
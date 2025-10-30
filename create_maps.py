#!/usr/bin/env python3
"""
Spatial Visualization of Rainfall-Runoff Statistical Analysis Results
Creates professional maps showing correlation strength, significance, and copula types across US basins
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm, Normalize
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Paths
RESULTS_FILE = "/icebox/data/shares/mh2/mosavat/Environmental_Data_Analysis/results/all_basins_results.csv"
SHAPEFILE = "/icebox/data/shares/mh2/mosavat/HUC-10/CONUS_HUC10.shp"
OUTPUT_DIR = "/icebox/data/shares/mh2/mosavat/Environmental_Data_Analysis/results"

# Map settings
DPI = 300
FIGSIZE = (20, 12)

print("="*70)
print("RAINFALL-RUNOFF SPATIAL VISUALIZATION")
print("="*70)

# ============================================================================
# LOAD DATA
# ============================================================================

print("\n[1/6] Loading results data...")
results_df = pd.read_csv(RESULTS_FILE)
print(f"   Loaded {len(results_df)} basin results")

print("\n[2/6] Loading shapefile...")
gdf = gpd.read_file(SHAPEFILE)
print(f"   Loaded {len(gdf)} basin polygons")
print(f"   CRS: {gdf.crs}")

# ============================================================================
# DATA PREPARATION
# ============================================================================

print("\n[3/6] Merging results with spatial data...")

# Ensure basin IDs are strings with leading zeros
results_df['basin_id'] = results_df['basin_id'].astype(str).str.zfill(10)
gdf['huc10'] = gdf['huc10'].astype(str).str.zfill(10)

# Merge results with geometries
gdf_merged = gdf.merge(results_df, left_on='huc10', right_on='basin_id', how='inner')
print(f"   Successfully matched {len(gdf_merged)} basins")

# Create significance categories
gdf_merged['significant'] = gdf_merged['spearman_pvalue'] < 0.05
gdf_merged['correlation_strength'] = pd.cut(
    gdf_merged['spearman_rho'],
    bins=[-1, 0, 0.1, 0.2, 0.3, 0.4, 1],
    labels=['Negative', 'Very Weak (0-0.1)', 'Weak (0.1-0.2)', 
            'Moderate (0.2-0.3)', 'Strong (0.3-0.4)', 'Very Strong (>0.4)']
)

# ============================================================================
# MAP 1: STATISTICAL SIGNIFICANCE
# ============================================================================

print("\n[4/6] Creating Map 1: Statistical Significance...")

fig, ax = plt.subplots(1, 1, figsize=FIGSIZE)

# Plot non-significant basins in gray
gdf_merged[~gdf_merged['significant']].plot(
    ax=ax, 
    color='lightgray', 
    edgecolor='white', 
    linewidth=0.3,
    label='Not Significant (p >= 0.05)'
)

# Plot significant basins in blue
gdf_merged[gdf_merged['significant']].plot(
    ax=ax, 
    color='#2E86AB', 
    edgecolor='white', 
    linewidth=0.3,
    label='Significant (p < 0.05)'
)

# Styling
ax.set_title('Statistical Significance of Rainfall-Runoff Correlation\nAcross US Basins (n=1089)', 
             fontsize=20, fontweight='bold', pad=20)
ax.axis('off')

# Legend
legend_elements = [
    mpatches.Patch(facecolor='#2E86AB', edgecolor='white', 
                   label=f'Significant (p < 0.05): {gdf_merged["significant"].sum()} basins '
                         f'({gdf_merged["significant"].sum()/len(gdf_merged)*100:.1f}%)'),
    mpatches.Patch(facecolor='lightgray', edgecolor='white', 
                   label=f'Not Significant (p >= 0.05): {(~gdf_merged["significant"]).sum()} basins '
                         f'({(~gdf_merged["significant"]).sum()/len(gdf_merged)*100:.1f}%)')
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=14, 
          frameon=True, fancybox=True, shadow=True)

# Add text box with summary statistics
textstr = f'Statistical Test: Spearman Correlation\nSignificance Level: a = 0.05\nTotal Basins Analyzed: {len(gdf_merged)}'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', bbox=props)

plt.tight_layout()
output_file1 = f"{OUTPUT_DIR}/map_1_significance.png"
plt.savefig(output_file1, dpi=DPI, bbox_inches='tight', facecolor='white')
print(f"   Saved: {output_file1}")
plt.close()

# ============================================================================
# MAP 2: CORRELATION STRENGTH (SPEARMAN RHO)
# ============================================================================

print("\n[5/6] Creating Map 2: Correlation Strength...")

fig, ax = plt.subplots(1, 1, figsize=FIGSIZE)

# Create custom colormap
colors = ['#d73027', '#f46d43', '#fdae61', '#fee090', '#e0f3f8', '#abd9e9', '#74add1', '#4575b4']
n_bins = 100
cmap = LinearSegmentedColormap.from_list('correlation', colors, N=n_bins)

# Plot with continuous color scale
vmin = gdf_merged['spearman_rho'].min()
vmax = gdf_merged['spearman_rho'].max()

gdf_merged.plot(
    column='spearman_rho',
    ax=ax,
    cmap=cmap,
    edgecolor='white',
    linewidth=0.3,
    legend=True,
    vmin=vmin,
    vmax=vmax,
    legend_kwds={
        'label': "Spearman Correlation Coefficient (?)",
        'orientation': "horizontal",
        'shrink': 0.6,
        'pad': 0.05
    }
)

# Styling
ax.set_title('Rainfall-Runoff Correlation Strength Across US Basins\n(Spearman Correlation Coefficient)', 
             fontsize=20, fontweight='bold', pad=20)
ax.axis('off')

# Add statistics text box
stats_text = (f'Mean ?: {gdf_merged["spearman_rho"].mean():.3f}\n'
              f'Std Dev: {gdf_merged["spearman_rho"].std():.3f}\n'
              f'Range: [{vmin:.3f}, {vmax:.3f}]\n'
              f'Median: {gdf_merged["spearman_rho"].median():.3f}')
props = dict(boxstyle='round', facecolor='wheat', alpha=0.9)
ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', bbox=props)

plt.tight_layout()
output_file2 = f"{OUTPUT_DIR}/map_2_correlation_strength.png"
plt.savefig(output_file2, dpi=DPI, bbox_inches='tight', facecolor='white')
print(f"   Saved: {output_file2}")
plt.close()

# ============================================================================
# MAP 3: CORRELATION CATEGORIES
# ============================================================================

print("\n[5/6] Creating Map 3: Correlation Categories...")

fig, ax = plt.subplots(1, 1, figsize=FIGSIZE)

# Define colors for categories
category_colors = {
    'Negative': '#d73027',
    'Very Weak (0-0.1)': '#fdae61',
    'Weak (0.1-0.2)': '#fee090',
    'Moderate (0.2-0.3)': '#e0f3f8',
    'Strong (0.3-0.4)': '#74add1',
    'Very Strong (>0.4)': '#4575b4'
}

# Plot each category
for category, color in category_colors.items():
    subset = gdf_merged[gdf_merged['correlation_strength'] == category]
    if len(subset) > 0:
        subset.plot(ax=ax, color=color, edgecolor='white', linewidth=0.3)

# Styling
ax.set_title('Categorized Rainfall-Runoff Correlation Strength\nAcross US Basins', 
             fontsize=20, fontweight='bold', pad=20)
ax.axis('off')

# Create legend
legend_elements = []
for category, color in category_colors.items():
    count = len(gdf_merged[gdf_merged['correlation_strength'] == category])
    if count > 0:
        pct = count / len(gdf_merged) * 100
        legend_elements.append(
            mpatches.Patch(facecolor=color, edgecolor='white',
                          label=f'{category}: {count} ({pct:.1f}%)')
        )

ax.legend(handles=legend_elements, loc='lower right', fontsize=12,
          frameon=True, fancybox=True, shadow=True, title='Correlation Strength')

plt.tight_layout()
output_file3 = f"{OUTPUT_DIR}/map_3_correlation_categories.png"
plt.savefig(output_file3, dpi=DPI, bbox_inches='tight', facecolor='white')
print(f"   Saved: {output_file3}")
plt.close()

# ============================================================================
# MAP 4: TAIL DEPENDENCE (UPPER)
# ============================================================================

print("\n[5/6] Creating Map 4: Upper Tail Dependence...")

fig, ax = plt.subplots(1, 1, figsize=FIGSIZE)

# Create colormap for tail dependence
cmap_tail = plt.cm.YlOrRd

gdf_merged.plot(
    column='chi_upper',
    ax=ax,
    cmap=cmap_tail,
    edgecolor='white',
    linewidth=0.3,
    legend=True,
    vmin=0,
    vmax=gdf_merged['chi_upper'].max(),
    legend_kwds={
        'label': "Upper Tail Dependence Coefficient (chi_U at q=0.95)",
        'orientation': "horizontal",
        'shrink': 0.6,
        'pad': 0.05
    }
)

# Styling
ax.set_title('Upper Tail Dependence: Extreme Rainfall -> Extreme Runoff\nAcross US Basins', 
             fontsize=20, fontweight='bold', pad=20)
ax.axis('off')

# Add interpretation text
interp_text = (f'Mean chi_U: {gdf_merged["chi_upper"].mean():.3f}\n'
               f'Max chi_U: {gdf_merged["chi_upper"].max():.3f}\n\n'
               f'Interpretation:\n'
               f'chi_U = 1: Perfect upper tail dependence\n'
               f'chi_U = 0: Tail independence\n\n'
               f'Higher values indicate extreme rainfall\n'
               f'more likely leads to extreme runoff')
props = dict(boxstyle='round', facecolor='wheat', alpha=0.9)
ax.text(0.02, 0.98, interp_text, transform=ax.transAxes, fontsize=11,
        verticalalignment='top', bbox=props)

plt.tight_layout()
output_file4 = f"{OUTPUT_DIR}/map_4_upper_tail_dependence.png"
plt.savefig(output_file4, dpi=DPI, bbox_inches='tight', facecolor='white')
print(f"   Saved: {output_file4}")
plt.close()

# ============================================================================
# MAP 5: BEST COPULA TYPE
# ============================================================================

print("\n[6/6] Creating Map 5: Best-Fit Copula Distribution...")

fig, ax = plt.subplots(1, 1, figsize=FIGSIZE)

# Define colors for copula types
copula_colors = {
    'Gaussian': '#4575b4',
    'Clayton': '#fee090',
    'Gumbel': '#d73027',
    'Frank': '#91cf60'
}

# Plot each copula type
for copula_type, color in copula_colors.items():
    subset = gdf_merged[gdf_merged['best_copula'] == copula_type]
    if len(subset) > 0:
        subset.plot(ax=ax, color=color, edgecolor='white', linewidth=0.3)

# Styling
ax.set_title('Best-Fit Copula Type for Rainfall-Runoff Dependence\nAcross US Basins', 
             fontsize=20, fontweight='bold', pad=20)
ax.axis('off')

# Create legend with counts
legend_elements = []
for copula_type, color in copula_colors.items():
    count = len(gdf_merged[gdf_merged['best_copula'] == copula_type])
    if count > 0:
        pct = count / len(gdf_merged) * 100
        legend_elements.append(
            mpatches.Patch(facecolor=color, edgecolor='white',
                          label=f'{copula_type}: {count} ({pct:.1f}%)')
        )

ax.legend(handles=legend_elements, loc='lower right', fontsize=12,
          frameon=True, fancybox=True, shadow=True, title='Best-Fit Copula')

# Add interpretation text
copula_interp = ('Copula Interpretation:\n'
                 '- Gaussian: Symmetric, no tail dependence\n'
                 '- Clayton: Lower tail dependence (droughts)\n'
                 '- Gumbel: Upper tail dependence (floods)\n'
                 '- Frank: Symmetric, weak tail dependence')
props = dict(boxstyle='round', facecolor='lightblue', alpha=0.8)
ax.text(0.02, 0.98, copula_interp, transform=ax.transAxes, fontsize=11,
        verticalalignment='top', bbox=props, family='monospace')

plt.tight_layout()
output_file5 = f"{OUTPUT_DIR}/map_5_copula_types.png"
plt.savefig(output_file5, dpi=DPI, bbox_inches='tight', facecolor='white')
print(f"   Saved: {output_file5}")
plt.close()

# ============================================================================
# MAP 6: P-VALUE DISTRIBUTION
# ============================================================================

print("\n[6/6] Creating Map 6: P-Value Distribution...")

fig, ax = plt.subplots(1, 1, figsize=FIGSIZE)

# Create bins for p-values
gdf_merged['p_category'] = pd.cut(
    gdf_merged['spearman_pvalue'],
    bins=[0, 0.001, 0.01, 0.05, 1.0],
    labels=['p < 0.001 (Very Strong)', 'p < 0.01 (Strong)', 
            'p < 0.05 (Moderate)', 'p >= 0.05 (Not Significant)']
)

# Define colors
p_colors = {
    'p < 0.001 (Very Strong)': '#053061',
    'p < 0.01 (Strong)': '#2166ac',
    'p < 0.05 (Moderate)': '#92c5de',
    'p >= 0.05 (Not Significant)': '#d3d3d3'
}

# Plot each category
for p_cat, color in p_colors.items():
    subset = gdf_merged[gdf_merged['p_category'] == p_cat]
    if len(subset) > 0:
        subset.plot(ax=ax, color=color, edgecolor='white', linewidth=0.3)

# Styling
ax.set_title('Statistical Significance Level (P-Value)\nof Rainfall-Runoff Correlation Across US Basins', 
             fontsize=20, fontweight='bold', pad=20)
ax.axis('off')

# Legend
legend_elements = []
for p_cat, color in p_colors.items():
    count = len(gdf_merged[gdf_merged['p_category'] == p_cat])
    if count > 0:
        pct = count / len(gdf_merged) * 100
        legend_elements.append(
            mpatches.Patch(facecolor=color, edgecolor='white',
                          label=f'{p_cat}: {count} ({pct:.1f}%)')
        )

ax.legend(handles=legend_elements, loc='lower right', fontsize=12,
          frameon=True, fancybox=True, shadow=True, title='Significance Level')

# Add note
note_text = ('Lower p-values indicate stronger\nevidence against H0 (no correlation)')
props = dict(boxstyle='round', facecolor='wheat', alpha=0.9)
ax.text(0.02, 0.98, note_text, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', bbox=props)

plt.tight_layout()
output_file6 = f"{OUTPUT_DIR}/map_6_pvalue_distribution.png"
plt.savefig(output_file6, dpi=DPI, bbox_inches='tight', facecolor='white')
print(f"   Saved: {output_file6}")
plt.close()

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*70)
print("MAPPING COMPLETED SUCCESSFULLY!")
print("="*70)
print("\nGenerated Maps:")
print(f"  1. {output_file1}")
print(f"  2. {output_file2}")
print(f"  3. {output_file3}")
print(f"  4. {output_file4}")
print(f"  5. {output_file5}")
print(f"  6. {output_file6}")
print("\nAll maps saved to:", OUTPUT_DIR)
print("="*70)
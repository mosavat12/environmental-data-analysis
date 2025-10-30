#!/usr/bin/env python3
"""
Spatial Visualization of Monthly Rainfall-Runoff Analysis Results
Creates professional maps with basemaps showing key statistical metrics
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm, Normalize, ListedColormap
import numpy as np
import contextily as ctx
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Paths
RESULTS_FILE = "/icebox/data/shares/mh2/mosavat/Environmental_Data_Analysis/results/all_basins_results_monthly.csv"
SHAPEFILE = "/icebox/data/shares/mh2/mosavat/HUC-10/CONUS_HUC10.shp"
OUTPUT_DIR = "/icebox/data/shares/mh2/mosavat/Environmental_Data_Analysis/results"

# Map settings
DPI = 300
FIGSIZE = (22, 14)

print("="*70)
print("MONTHLY RAINFALL-RUNOFF SPATIAL VISUALIZATION WITH BASEMAPS")
print("="*70)

# ============================================================================
# LOAD DATA
# ============================================================================

print("\n[1/5] Loading results data...")
results_df = pd.read_csv(RESULTS_FILE)
print(f"   Loaded {len(results_df)} basin results")

print("\n[2/5] Loading shapefile...")
gdf = gpd.read_file(SHAPEFILE)
print(f"   Loaded {len(gdf)} basin polygons")
print(f"   Original CRS: {gdf.crs}")

# ============================================================================
# DATA PREPARATION
# ============================================================================

print("\n[3/5] Merging results with spatial data...")

# Ensure basin IDs are strings with leading zeros
results_df['basin_id'] = results_df['basin_id'].astype(str).str.zfill(10)
gdf['huc10'] = gdf['huc10'].astype(str).str.zfill(10)

# Merge results with geometries
gdf_merged = gdf.merge(results_df, left_on='huc10', right_on='basin_id', how='inner')
print(f"   Successfully matched {len(gdf_merged)} basins")

# Reproject to Web Mercator for basemap (EPSG:3857)
print("\n[4/5] Reprojecting to Web Mercator for basemap...")
gdf_merged = gdf_merged.to_crs(epsg=3857)
print(f"   New CRS: {gdf_merged.crs}")

# Create significance categories
gdf_merged['significant'] = gdf_merged['spearman_pvalue'] < 0.05

# Create correlation strength categories
gdf_merged['correlation_category'] = pd.cut(
    gdf_merged['spearman_rho'],
    bins=[-1, 0, 0.2, 0.4, 0.6, 0.8, 1],
    labels=['Negative', 'Weak (0-0.2)', 'Moderate (0.2-0.4)', 
            'Strong (0.4-0.6)', 'Very Strong (0.6-0.8)', 'Excellent (>0.8)']
)

print("\n[5/5] Creating maps with basemaps...")

# ============================================================================
# MAP 1: STATISTICAL SIGNIFICANCE
# ============================================================================

print("\n   Creating Map 1: Statistical Significance...")

fig, ax = plt.subplots(1, 1, figsize=FIGSIZE)

# Plot non-significant basins
gdf_merged[~gdf_merged['significant']].plot(
    ax=ax, 
    color='#d62728',  # Red for not significant
    edgecolor='black', 
    linewidth=0.5,
    alpha=0.8,
    label='Not Significant (p >= 0.05)'
)

# Plot significant basins
gdf_merged[gdf_merged['significant']].plot(
    ax=ax, 
    color='#2ca02c',  # Green for significant
    edgecolor='black', 
    linewidth=0.5,
    alpha=0.8,
    label='Significant (p < 0.05)'
)

# Add basemap
try:
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=5, alpha=0.5)
    print("      Basemap added successfully")
except Exception as e:
    print(f"      Warning: Could not add basemap: {e}")

# Styling
ax.set_title('Statistical Significance of Monthly Rainfall-Runoff Correlation\nAcross US Basins (n=1089)', 
             fontsize=22, fontweight='bold', pad=20)
ax.axis('off')

# Legend
sig_count = gdf_merged['significant'].sum()
not_sig_count = (~gdf_merged['significant']).sum()
legend_elements = [
    mpatches.Patch(facecolor='#2ca02c', edgecolor='black', 
                   label=f'Significant (p < 0.05): {sig_count} basins ({sig_count/len(gdf_merged)*100:.1f}%)'),
    mpatches.Patch(facecolor='#d62728', edgecolor='black', 
                   label=f'Not Significant (p >= 0.05): {not_sig_count} basins ({not_sig_count/len(gdf_merged)*100:.1f}%)')
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=16, 
          frameon=True, fancybox=True, shadow=True)

plt.tight_layout()
output_file1 = f"{OUTPUT_DIR}/monthly_map_1_significance.png"
plt.savefig(output_file1, dpi=DPI, bbox_inches='tight', facecolor='white')
print(f"      Saved: {output_file1}")
plt.close()

# ============================================================================
# MAP 2: HYDROLOGICAL REGIME (Gaussian/Gumbel/Clayton)
# ============================================================================

print("\n   Creating Map 2: Hydrological Regime (COPULA TYPE)...")

fig, ax = plt.subplots(1, 1, figsize=FIGSIZE)

# Define colors for hydrological regimes
regime_colors = {
    'Gaussian': '#4575b4',      # Blue - Symmetric
    'Gumbel': '#d73027',        # Red - Flood-prone (upper tail)
    'Clayton': '#fee090',       # Yellow - Drought-prone (lower tail)
    'Frank': '#91cf60'          # Green - Weak tail dependence
}

# Plot each regime
for regime, color in regime_colors.items():
    subset = gdf_merged[gdf_merged['best_copula'] == regime]
    if len(subset) > 0:
        subset.plot(ax=ax, color=color, edgecolor='black', linewidth=0.5, alpha=0.8)

# Add basemap
try:
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=5, alpha=0.5)
    print("      Basemap added successfully")
except Exception as e:
    print(f"      Warning: Could not add basemap: {e}")

# Styling
ax.set_title('Hydrological Regime Classification\nBased on Best-Fit Copula Type (Monthly Analysis)', 
             fontsize=22, fontweight='bold', pad=20)
ax.axis('off')

# Create legend with interpretation
legend_elements = []
regime_interp = {
    'Gaussian': 'Symmetric (no extreme tail dependence)',
    'Gumbel': 'Flood-Prone (upper tail dependence)',
    'Clayton': 'Drought-Prone (lower tail dependence)',
    'Frank': 'Weak tail dependence'
}

for regime, color in regime_colors.items():
    count = len(gdf_merged[gdf_merged['best_copula'] == regime])
    if count > 0:
        pct = count / len(gdf_merged) * 100
        legend_elements.append(
            mpatches.Patch(facecolor=color, edgecolor='black',
                          label=f'{regime}: {count} ({pct:.1f}%) - {regime_interp[regime]}')
        )

ax.legend(handles=legend_elements, loc='lower right', fontsize=13,
          frameon=True, fancybox=True, shadow=True, title='Hydrological Regime')

plt.tight_layout()
output_file2 = f"{OUTPUT_DIR}/monthly_map_2_hydrological_regime.png"
plt.savefig(output_file2, dpi=DPI, bbox_inches='tight', facecolor='white')
print(f"      Saved: {output_file2}")
plt.close()

# ============================================================================
# MAP 3: CORRELATION STRENGTH (CONTINUOUS)
# ============================================================================

print("\n   Creating Map 3: Correlation Strength (Continuous)...")

fig, ax = plt.subplots(1, 1, figsize=FIGSIZE)

# Create colormap (red to blue through white)
colors_list = ['#d73027', '#f46d43', '#fdae61', '#fee090', '#e0f3f8', 
               '#abd9e9', '#74add1', '#4575b4', '#313695']
n_bins = 100
cmap = LinearSegmentedColormap.from_list('correlation', colors_list, N=n_bins)

# Plot
vmin = gdf_merged['spearman_rho'].min()
vmax = gdf_merged['spearman_rho'].max()

gdf_merged.plot(
    column='spearman_rho',
    ax=ax,
    cmap=cmap,
    edgecolor='black',
    linewidth=0.3,
    legend=True,
    vmin=vmin,
    vmax=vmax,
    legend_kwds={
        'label': "Spearman Correlation Coefficient (?)",
        'orientation': "horizontal",
        'shrink': 0.5,
        'pad': 0.05,
        'aspect': 30
    }
)

# Add basemap
try:
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=5, alpha=0.4)
    print("      Basemap added successfully")
except Exception as e:
    print(f"      Warning: Could not add basemap: {e}")

# Styling
ax.set_title('Monthly Rainfall-Runoff Correlation Strength\nSpearman Correlation Coefficient (?)', 
             fontsize=22, fontweight='bold', pad=20)
ax.axis('off')

plt.tight_layout()
output_file3 = f"{OUTPUT_DIR}/monthly_map_3_correlation_strength.png"
plt.savefig(output_file3, dpi=DPI, bbox_inches='tight', facecolor='white')
print(f"      Saved: {output_file3}")
plt.close()

# ============================================================================
# MAP 4: UPPER TAIL DEPENDENCE
# ============================================================================

print("\n   Creating Map 4: Upper Tail Dependence (Flood Risk)...")

fig, ax = plt.subplots(1, 1, figsize=FIGSIZE)

# Colormap for upper tail (white to dark red)
cmap_upper = plt.cm.YlOrRd

gdf_merged.plot(
    column='chi_upper',
    ax=ax,
    cmap=cmap_upper,
    edgecolor='black',
    linewidth=0.3,
    legend=True,
    vmin=0,
    vmax=1,
    legend_kwds={
        'label': "Upper Tail Dependence Coefficient (chi_U at q=0.95)",
        'orientation': "horizontal",
        'shrink': 0.5,
        'pad': 0.05,
        'aspect': 30
    }
)

# Add basemap
try:
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=5, alpha=0.4)
    print("      Basemap added successfully")
except Exception as e:
    print(f"      Warning: Could not add basemap: {e}")

# Styling
ax.set_title('Upper Tail Dependence: Extreme Rainfall -> Extreme Runoff\nFlood Risk Assessment (Monthly Analysis)', 
             fontsize=22, fontweight='bold', pad=20)
ax.axis('off')

plt.tight_layout()
output_file4 = f"{OUTPUT_DIR}/monthly_map_4_upper_tail_flood.png"
plt.savefig(output_file4, dpi=DPI, bbox_inches='tight', facecolor='white')
print(f"      Saved: {output_file4}")
plt.close()

# ============================================================================
# MAP 5: LOWER TAIL DEPENDENCE
# ============================================================================

print("\n   Creating Map 5: Lower Tail Dependence (Drought Risk)...")

fig, ax = plt.subplots(1, 1, figsize=FIGSIZE)

# Colormap for lower tail (white to dark brown/purple)
cmap_lower = plt.cm.PuBu

gdf_merged.plot(
    column='chi_lower',
    ax=ax,
    cmap=cmap_lower,
    edgecolor='black',
    linewidth=0.3,
    legend=True,
    vmin=0,
    vmax=1,
    legend_kwds={
        'label': "Lower Tail Dependence Coefficient (chi_L at q=0.05)",
        'orientation': "horizontal",
        'shrink': 0.5,
        'pad': 0.05,
        'aspect': 30
    }
)

# Add basemap
try:
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=5, alpha=0.4)
    print("      Basemap added successfully")
except Exception as e:
    print(f"      Warning: Could not add basemap: {e}")

# Styling
ax.set_title('Lower Tail Dependence: Low Rainfall -> Low Runoff\nDrought Propagation Assessment (Monthly Analysis)', 
             fontsize=22, fontweight='bold', pad=20)
ax.axis('off')

plt.tight_layout()
output_file5 = f"{OUTPUT_DIR}/monthly_map_5_lower_tail_drought.png"
plt.savefig(output_file5, dpi=DPI, bbox_inches='tight', facecolor='white')
print(f"      Saved: {output_file5}")
plt.close()

# ============================================================================
# MAP 6: COMBINED TAIL DEPENDENCE (BOTH UPPER AND LOWER)
# ============================================================================

print("\n   Creating Map 6: Combined Tail Dependence Analysis...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(28, 12))

# Left: Upper Tail
gdf_merged.plot(
    column='chi_upper',
    ax=ax1,
    cmap=plt.cm.YlOrRd,
    edgecolor='black',
    linewidth=0.3,
    legend=True,
    vmin=0,
    vmax=1,
    legend_kwds={
        'label': "Upper Tail (chi_U): Flood Risk",
        'orientation': "vertical",
        'shrink': 0.8
    }
)

try:
    ctx.add_basemap(ax1, source=ctx.providers.CartoDB.Positron, zoom=5, alpha=0.4)
except:
    pass

ax1.set_title('FLOOD RISK\n(Upper Tail Dependence)', fontsize=20, fontweight='bold', pad=15)
ax1.axis('off')

# Right: Lower Tail
gdf_merged.plot(
    column='chi_lower',
    ax=ax2,
    cmap=plt.cm.PuBu,
    edgecolor='black',
    linewidth=0.3,
    legend=True,
    vmin=0,
    vmax=1,
    legend_kwds={
        'label': "Lower Tail (chi_L): Drought Risk",
        'orientation': "vertical",
        'shrink': 0.8
    }
)

try:
    ctx.add_basemap(ax2, source=ctx.providers.CartoDB.Positron, zoom=5, alpha=0.4)
except:
    pass

ax2.set_title('DROUGHT RISK\n(Lower Tail Dependence)', fontsize=20, fontweight='bold', pad=15)
ax2.axis('off')

# Overall title
fig.suptitle('Extreme Event Analysis: Tail Dependence Structure\nMonthly Rainfall-Runoff Analysis Across US Basins', 
             fontsize=24, fontweight='bold', y=0.98)

plt.tight_layout()
output_file6 = f"{OUTPUT_DIR}/monthly_map_6_combined_tail_dependence.png"
plt.savefig(output_file6, dpi=DPI, bbox_inches='tight', facecolor='white')
print(f"      Saved: {output_file6}")
plt.close()

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*70)
print("MAPPING COMPLETED SUCCESSFULLY!")
print("="*70)
print("\nGenerated Maps:")
print(f"  1. {output_file1}")
print(f"     -> Statistical Significance")
print(f"  2. {output_file2}")
print(f"     -> Hydrological Regime (Copula-based classification)")
print(f"  3. {output_file3}")
print(f"     -> Correlation Strength (continuous)")
print(f"  4. {output_file4}")
print(f"     -> Upper Tail Dependence (Flood Risk)")
print(f"  5. {output_file5}")
print(f"     -> Lower Tail Dependence (Drought Risk)")
print(f"  6. {output_file6}")
print(f"     -> Combined Tail Analysis (side-by-side)")
print("\nAll maps saved to:", OUTPUT_DIR)
print("="*70)
# Complete Workflow Summary: Daily vs Monthly Analysis

## Overview

You now have **TWO complete analysis pipelines**:

1. ✅ **Daily Analysis** (COMPLETED)
2. 🆕 **Monthly Analysis** (READY TO RUN)

---

## 📁 File Structure

### Daily Analysis (Existing)
```
/icebox/data/shares/mh2/mosavat/Environmental_Data_Analysis/
├── rainfall_runoff_analysis.py
├── submit_analysis.sh
├── merge_results.py
├── create_maps.py
├── log/
│   └── basin_*.out/err
└── results/
    ├── temp/
    │   └── basin_*.csv (individual results)
    └── all_basins_results.csv (merged results)
```

### Monthly Analysis (New)
```
/icebox/data/shares/mh2/mosavat/Environmental_Data_Analysis/
├── preprocess_monthly.py
├── rainfall_runoff_analysis_monthly.py
├── submit_analysis_monthly.sh
├── merge_results_monthly.py
├── log_monthly/
│   └── basin_*.out/err
└── results/
    └── all_basins_results_monthly.csv (merged results)

/icebox/data/shares/mh2/mosavat/Lumped/data/processed/temporal_test/
└── timeseries_monthly/
    └── [basin_id].csv (monthly aggregated data)
```

---

## 🚀 Step-by-Step: Monthly Analysis

### STEP 0: Preprocess Data (ONE TIME)
```bash
cd /icebox/data/shares/mh2/mosavat/Environmental_Data_Analysis/
python preprocess_monthly.py
```

**What it does:**
- Reads daily data (3650 points per basin)
- Aggregates to monthly (SUM for both prcp and runoff)
- Saves ~120 monthly points per basin
- Creates `/Lumped/data/processed/temporal_test/timeseries_monthly/`

**Time:** ~5-10 minutes for all 1089 basins

---

### STEP 1: Run Monthly Analysis
```bash
chmod +x submit_analysis_monthly.sh
sbatch submit_analysis_monthly.sh
```

**What it does:**
- Launches 1089 parallel jobs
- Each analyzes one basin (monthly data)
- Saves individual results to `temp_monthly/`

**Time:** ~5-10 minutes (parallel)

---

### STEP 2: Monitor Progress
```bash
# Check job status
squeue -u $USER

# Count completed
ls /icebox/data/shares/mh2/mosavat/Lumped/results/temp_monthly/*.csv | wc -l

# Should show: 1089 when done
```

---

### STEP 3: Merge Results
```bash
python merge_results_monthly.py
```

**What it does:**
- Combines all 1089 individual results
- Saves to `results/all_basins_results_monthly.csv`
- Prints comparison with daily results!

**Output:**
- Summary statistics for monthly analysis
- Direct comparison: daily vs monthly correlation strength

---

## 📊 Expected Results Comparison

| Metric | Daily | Monthly (Expected) |
|--------|-------|-------------------|
| Mean Spearman ρ | 0.119 | 0.40-0.50 |
| Std Dev | 0.096 | 0.15-0.20 |
| Max ρ | 0.588 | 0.80-0.90 |
| Significant (p<0.05) | 95.9% | >95% |
| Data points/basin | 3650 | ~120 |
| **Improvement** | baseline | **3-5x stronger** |

---

## 🗺️ Creating Monthly Maps

Once monthly results are ready, modify `create_maps.py`:

```python
# Change this line:
RESULTS_FILE = "/icebox/.../results/all_basins_results_monthly.csv"

# And output names:
output_file1 = f"{OUTPUT_DIR}/map_1_significance_MONTHLY.png"
```

Or create `create_maps_monthly.py` (copy and modify create_maps.py)

---

## 🎓 For Your Presentation

### Slide Structure Suggestion:

**Slide 1: Two Approaches**
- Daily timestep: Tests instantaneous relationship
- Monthly timestep: Accounts for lag and storage

**Slide 2: Daily Results**
- Mean ρ = 0.12 (weak but significant)
- 95.9% basins significant
- Interpretation: Lag and storage mask true relationship

**Slide 3: Monthly Results**  
- Mean ρ = 0.XX (3-5x stronger)
- >95% basins significant
- Interpretation: Monthly aggregation reveals water balance relationship

**Slide 4: Why Monthly is Better**
- Integrates temporal lag (runoff response within month)
- Captures storage effects (soil moisture memory)
- Represents water balance (monthly input → output)
- Standard approach in hydrology

**Slide 5: Maps**
- Side-by-side: Daily vs Monthly correlation maps
- Show spatial patterns clearer in monthly

**Slide 6: Conclusion**
- Both analyses confirm significant rainfall-runoff relationship
- Monthly analysis reveals true strength (3-5x improvement)
- Demonstrates importance of temporal scale selection
- Copula analysis captures complex nonlinear dependencies

---

## 📈 Quick Comparison After Both Complete

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load both results
daily = pd.read_csv('results/all_basins_results.csv')
monthly = pd.read_csv('results/all_basins_results_monthly.csv')

# Compare correlations
print(f"Daily:   mean={daily['spearman_rho'].mean():.3f}, std={daily['spearman_rho'].std():.3f}")
print(f"Monthly: mean={monthly['spearman_rho'].mean():.3f}, std={monthly['spearman_rho'].std():.3f}")
print(f"Improvement: {monthly['spearman_rho'].mean() / daily['spearman_rho'].mean():.2f}x")

# Histogram comparison
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].hist(daily['spearman_rho'], bins=50, alpha=0.7, label='Daily')
axes[0].set_title('Daily Correlation Distribution')
axes[0].set_xlabel('Spearman ρ')
axes[0].set_ylabel('Frequency')

axes[1].hist(monthly['spearman_rho'], bins=50, alpha=0.7, label='Monthly', color='orange')
axes[1].set_title('Monthly Correlation Distribution')
axes[1].set_xlabel('Spearman ρ')
axes[1].set_ylabel('Frequency')

plt.tight_layout()
plt.savefig('results/comparison_daily_vs_monthly.png', dpi=300)
print("Comparison plot saved!")
```

---

## ✅ Checklist

**Daily Analysis (DONE):**
- [x] Run analysis for all 1089 basins
- [x] Merge results
- [x] Create maps
- [x] Interpret results

**Monthly Analysis (TO DO):**
- [ ] Run preprocessing (STEP 0)
- [ ] Submit batch job (STEP 1)
- [ ] Wait for completion (STEP 2)
- [ ] Merge results (STEP 3)
- [ ] Create monthly maps (optional)
- [ ] Compare with daily results

---

## 🎯 Key Takeaway

**You're not replacing your daily analysis - you're ENRICHING it!**

- Daily: Shows challenge of instantaneous correlation
- Monthly: Shows power of appropriate temporal aggregation
- Together: Demonstrate importance of scale selection in hydrology

This makes your presentation MORE sophisticated, not less!

---

## Questions to Address in Presentation

**Q: Why is daily correlation weak?**
A: Temporal lag, storage effects, threshold behavior

**Q: Why is monthly correlation stronger?**
A: Integrates lag, captures water balance, reduces noise

**Q: Which is correct?**
A: Both! They answer different questions at different scales

**Q: Which should water managers use?**
A: Monthly for planning, daily for operations/flood forecasting

---

Good luck with your monthly analysis! The results should be much more impressive! 🚀

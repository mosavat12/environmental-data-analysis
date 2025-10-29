# Rainfall-Runoff Statistical Analysis

Statistical analysis framework for investigating the dependence between precipitation and runoff across 1089 US basins using copula-based methods.

## Overview

This project performs:
1. **Rank correlation analysis** (Spearman's ?, Kendall's t)
2. **Tail dependence assessment** (upper and lower tail at q=0.95)
3. **Copula modeling** (Gaussian, Clayton, Gumbel, Frank)
4. **Goodness-of-fit testing** (Cramér-von Mises)

## Files

- `rainfall_runoff_analysis.py` - Main analysis script
- `submit_analysis.sh` - SLURM batch submission script
- `merge_results.py` - Combines individual basin results
- `README.md` - This file

## Requirements

### Python Packages
```bash
numpy
pandas
scipy
```

Install if needed:
```bash
pip install numpy pandas scipy
```

## Directory Structure

```
project/
+-- rainfall_runoff_analysis.py
+-- submit_analysis.sh
+-- merge_results.py
+-- log/                          # Created automatically
¦   +-- basin_0001.out
¦   +-- basin_0001.err
¦   +-- ...
+-- results/
    +-- temp/                     # Temporary individual results
    ¦   +-- basin_0000.csv
    ¦   +-- ...
    +-- all_basins_results.csv    # Final merged results
```

## Usage

### Step 1: Submit SLURM Job Array

```bash
# Make the submission script executable
chmod +x submit_analysis.sh

# Submit jobs (1089 jobs, one per basin)
sbatch submit_analysis.sh
```

This will:
- Launch 1089 parallel jobs (one per basin)
- Each job runs for up to 1 hour with 4GB RAM
- Output logs saved to `log/basin_*.out` and `log/basin_*.err`
- Individual results saved to `/icebox/data/shares/mh2/mosavat/Lumped/results/temp/`

### Step 2: Monitor Job Progress

```bash
# Check job status
squeue -u $USER

# Check specific job
squeue -j <job_id>

# View output of a specific basin
tail -f log/basin_0001.out

# Count completed jobs
ls /icebox/data/shares/mh2/mosavat/Lumped/results/temp/basin_*.csv | wc -l
```

### Step 3: Merge Results

Once all (or most) jobs complete:

```bash
python merge_results.py
```

This will:
- Combine all individual basin results
- Generate summary statistics
- Save final results to `/icebox/data/shares/mh2/mosavat/Lumped/results/all_basins_results.csv`

## Output Format

### Final Results CSV (`all_basins_results.csv`)

Columns:
- `basin_id` - Basin identifier
- `spearman_rho` - Spearman correlation coefficient
- `spearman_pvalue` - P-value for Spearman test
- `kendall_tau` - Kendall's tau coefficient
- `kendall_pvalue` - P-value for Kendall test
- `chi_upper` - Upper tail dependence (q=0.95)
- `chi_lower` - Lower tail dependence (q=0.95)
- `best_copula` - Best-fit copula family
- `copula_parameter` - Parameter of best copula
- `copula_gof_statistic` - Cramér-von Mises test statistic
- `copula_gof_pvalue` - P-value for goodness-of-fit test

### Interpretation

**Hypothesis Testing:**
- H0: No significant relationship between precipitation and runoff
- H1: Significant relationship exists

**Decision Rule:**
- If `spearman_pvalue < 0.05` ? Reject H0 (significant correlation)
- If `kendall_pvalue < 0.05` ? Reject H0 (significant correlation)

**Tail Dependence:**
- `chi_upper` close to 1 ? Strong upper tail dependence (extreme rainfall ? extreme runoff)
- `chi_lower` close to 1 ? Strong lower tail dependence (low rainfall ? low runoff)
- Values close to 0 ? Tail independence

**Copula Selection:**
- **Gaussian** - Symmetric dependence, no tail dependence
- **Clayton** - Lower tail dependence (drought emphasis)
- **Gumbel** - Upper tail dependence (flood emphasis)
- **Frank** - Symmetric, weak tail dependence

## Troubleshooting

### Jobs Failing

Check error logs:
```bash
cat log/basin_0001.err
```

Common issues:
- Missing Python packages ? Install required packages
- File permission issues ? Check read/write permissions
- Data file missing ? Verify basin CSV exists

### Incomplete Results

If some basins failed:
```bash
# Find which basins completed
ls /icebox/data/shares/mh2/mosavat/Lumped/results/temp/ | wc -l

# Merge available results anyway
python merge_results.py
```

### Re-running Failed Basins

Identify failed basin indices from logs, then:
```bash
# Re-run specific basin (e.g., basin 42)
python rainfall_runoff_analysis.py 42
```

## Customization

### Adjust Analysis Parameters

Edit `rainfall_runoff_analysis.py`:

```python
# Line 228: Change tail dependence quantile
chi_upper, chi_lower = calculate_tail_dependence(u, v, q=0.95)  # Change q

# Line 238-243: Add/remove copula families
copulas = [
    GaussianCopula(),
    ClaytonCopula(),
    GumbelCopula(),
    FrankCopula()
]
```

### Adjust SLURM Resources

Edit `submit_analysis.sh`:

```bash
#SBATCH --time=02:00:00      # Increase time limit
#SBATCH --mem=8G             # Increase memory
#SBATCH --cpus-per-task=2    # Use more CPUs
```

## Data Paths

Default paths (change if needed):
- Basin list: `/icebox/data/shares/mh2/mosavat/Lumped/temporal_test_basins.txt`
- Time series data: `/icebox/data/shares/mh2/mosavat/Lumped/data/processed/temporal_test/timeseries/`
- Output directory: `/icebox/data/shares/mh2/mosavat/Lumped/results/`

## Expected Runtime

- **Per basin**: ~1-5 minutes
- **Total (1089 basins in parallel)**: ~5-10 minutes
- **Sequential (not recommended)**: ~2-9 hours

## Notes

- Each basin has 3650 daily timesteps (10 years)
- Analysis uses empirical CDF (non-parametric) for marginals
- Copula goodness-of-fit uses simplified Cramér-von Mises test
- Significance level a = 0.05

## Contact

For questions about the analysis framework, refer to the course materials on multivariate probability distributions and copula theory.

## Citation

Methods based on:
- Spearman, C. (1904). "The proof and measurement of association between two things"
- Kendall, M. G. (1938). "A new measure of rank correlation"
- Nelsen, R. B. (2006). "An Introduction to Copulas"
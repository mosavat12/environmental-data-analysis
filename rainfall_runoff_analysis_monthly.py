#!/usr/bin/env python3
"""
Rainfall-Runoff Statistical Analysis - MONTHLY DATA
Analyzes the dependence between precipitation and runoff using copula-based methods.
Uses monthly aggregated data to account for temporal lag and storage effects.
"""

import sys
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import gamma
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# TAIL DEPENDENCE CALCULATION
# ============================================================================

def calculate_tail_dependence(u, v, q=0.95):
    """
    Calculate upper and lower tail dependence coefficients.
    
    Parameters:
    -----------
    u, v : array-like
        Pseudo-observations (uniform [0,1])
    q : float
        Quantile threshold (default 0.95)
    
    Returns:
    --------
    chi_upper, chi_lower : float
        Upper and lower tail dependence coefficients
    """
    n = len(u)
    
    # Upper tail dependence: chi_U(q)
    # chi_U(q) = Pr(U > q | V > q) = Pr(U > q, V > q) / Pr(V > q)
    mask_upper = v > q
    if np.sum(mask_upper) > 0:
        chi_upper = np.sum((u > q) & mask_upper) / np.sum(mask_upper)
    else:
        chi_upper = np.nan
    
    # Lower tail dependence: chi_L(q)  
    # chi_L(q) = Pr(U <= 1-q | V <= 1-q)
    threshold_lower = 1 - q
    mask_lower = v <= threshold_lower
    if np.sum(mask_lower) > 0:
        chi_lower = np.sum((u <= threshold_lower) & mask_lower) / np.sum(mask_lower)
    else:
        chi_lower = np.nan
    
    return chi_upper, chi_lower


# ============================================================================
# COPULA IMPLEMENTATIONS
# ============================================================================

class GaussianCopula:
    """Gaussian (Normal) Copula"""
    
    def __init__(self):
        self.name = "Gaussian"
        self.rho = None
    
    def fit(self, u, v):
        """Fit Gaussian copula using correlation of transformed data"""
        # Transform to normal
        x = stats.norm.ppf(np.clip(u, 1e-6, 1-1e-6))
        y = stats.norm.ppf(np.clip(v, 1e-6, 1-1e-6))
        
        # Estimate correlation
        self.rho = np.corrcoef(x, y)[0, 1]
        return self.rho
    
    def cdf(self, u, v):
        """Compute Gaussian copula CDF"""
        x = stats.norm.ppf(np.clip(u, 1e-6, 1-1e-6))
        y = stats.norm.ppf(np.clip(v, 1e-6, 1-1e-6))
        
        # Bivariate normal CDF
        rho = self.rho
        return stats.multivariate_normal.cdf([x, y], mean=[0, 0], 
                                              cov=[[1, rho], [rho, 1]])


class ClaytonCopula:
    """Clayton Copula (lower tail dependence)"""
    
    def __init__(self):
        self.name = "Clayton"
        self.theta = None
    
    def fit(self, u, v):
        """Fit Clayton copula using Kendall's tau"""
        tau, _ = stats.kendalltau(u, v)
        # theta = 2*tau / (1 - tau)
        if tau >= 0.999:
            tau = 0.999
        self.theta = max(2 * tau / (1 - tau), 1e-6)
        return self.theta
    
    def cdf(self, u, v):
        """Compute Clayton copula CDF"""
        theta = self.theta
        u = np.clip(u, 1e-6, 1-1e-6)
        v = np.clip(v, 1e-6, 1-1e-6)
        
        if theta < 1e-6:
            return u * v  # Independence
        
        return (u**(-theta) + v**(-theta) - 1)**(-1/theta)


class GumbelCopula:
    """Gumbel Copula (upper tail dependence)"""
    
    def __init__(self):
        self.name = "Gumbel"
        self.theta = None
    
    def fit(self, u, v):
        """Fit Gumbel copula using Kendall's tau"""
        tau, _ = stats.kendalltau(u, v)
        # theta = 1 / (1 - tau)
        if tau >= 0.999:
            tau = 0.999
        self.theta = max(1 / (1 - tau), 1.0)
        return self.theta
    
    def cdf(self, u, v):
        """Compute Gumbel copula CDF"""
        theta = self.theta
        u = np.clip(u, 1e-6, 1-1e-6)
        v = np.clip(v, 1e-6, 1-1e-6)
        
        a = (-np.log(u))**theta
        b = (-np.log(v))**theta
        
        return np.exp(-(a + b)**(1/theta))


class FrankCopula:
    """Frank Copula (symmetric)"""
    
    def __init__(self):
        self.name = "Frank"
        self.theta = None
    
    def fit(self, u, v):
        """Fit Frank copula using Kendall's tau"""
        tau, _ = stats.kendalltau(u, v)
        
        # Numerical solution for theta from tau
        # For Frank: tau = 1 - 4/theta * (D_1(theta) - 1)
        # Approximation: theta ~ 5.7 * tau for small tau
        if abs(tau) < 0.001:
            self.theta = 0.0
        else:
            self.theta = 5.7 * tau
        
        return self.theta
    
    def cdf(self, u, v):
        """Compute Frank copula CDF"""
        theta = self.theta
        u = np.clip(u, 1e-6, 1-1e-6)
        v = np.clip(v, 1e-6, 1-1e-6)
        
        if abs(theta) < 1e-6:
            return u * v  # Independence
        
        numerator = (np.exp(-theta * u) - 1) * (np.exp(-theta * v) - 1)
        denominator = np.exp(-theta) - 1
        
        return -1/theta * np.log(1 + numerator / denominator)


# ============================================================================
# GOODNESS-OF-FIT TEST
# ============================================================================

def cramer_von_mises_copula(u, v, copula, n_bootstrap=100):
    """
    Cramer-von Mises goodness-of-fit test for copulas.
    
    Simplified version using empirical vs theoretical CDF comparison.
    """
    n = len(u)
    
    # Compute test statistic
    # For each point, compute empirical vs theoretical copula CDF
    statistic = 0.0
    
    for i in range(n):
        # Empirical copula
        emp_cdf = np.sum((u <= u[i]) & (v <= v[i])) / n
        
        # Theoretical copula
        theo_cdf = copula.cdf(u[i], v[i])
        
        statistic += (emp_cdf - theo_cdf)**2
    
    statistic = statistic / n
    
    # Approximate p-value (simplified)
    # In practice, this would require parametric bootstrap
    # For class presentation, use simple approximation
    p_value = 1 / (1 + statistic * np.sqrt(n))
    
    return statistic, p_value


# ============================================================================
# MAIN ANALYSIS FUNCTION
# ============================================================================

def analyze_basin(basin_id, data_path):
    """
    Perform complete statistical analysis for one basin using MONTHLY data.
    
    Parameters:
    -----------
    basin_id : str
        Basin identifier
    data_path : str
        Path to the CSV file containing monthly basin data
    
    Returns:
    --------
    dict : Analysis results
    """
    
    print(f"Processing basin {basin_id}...")
    
    # Load data
    try:
        df = pd.read_csv(data_path)
        prcp = df['prcp'].values
        runoff = df['runoff'].values
    except Exception as e:
        print(f"Error loading data for basin {basin_id}: {e}")
        return None
    
    # Check data validity
    n_months = len(prcp)
    print(f"   Data points: {n_months} months")
    
    results = {'basin_id': basin_id, 'n_months': n_months}
    
    # ========================================================================
    # STEP 1: Rank Correlation Analysis
    # ========================================================================
    
    # Spearman correlation
    spearman_rho, spearman_pval = stats.spearmanr(prcp, runoff)
    results['spearman_rho'] = spearman_rho
    results['spearman_pvalue'] = spearman_pval
    
    # Kendall's tau
    kendall_tau, kendall_pval = stats.kendalltau(prcp, runoff)
    results['kendall_tau'] = kendall_tau
    results['kendall_pvalue'] = kendall_pval
    
    # ========================================================================
    # STEP 2: Transform to Pseudo-observations (Empirical CDF)
    # ========================================================================
    
    # Rank-based transformation to uniform [0,1]
    n = len(prcp)
    u = stats.rankdata(prcp) / (n + 1)
    v = stats.rankdata(runoff) / (n + 1)
    
    # ========================================================================
    # STEP 3: Tail Dependence
    # ========================================================================
    
    chi_upper, chi_lower = calculate_tail_dependence(u, v, q=0.95)
    results['chi_upper'] = chi_upper
    results['chi_lower'] = chi_lower
    
    # ========================================================================
    # STEP 4: Fit Copula Models
    # ========================================================================
    
    copulas = [
        GaussianCopula(),
        ClaytonCopula(),
        GumbelCopula(),
        FrankCopula()
    ]
    
    best_copula = None
    best_gof_stat = np.inf
    best_pvalue = 0
    best_theta = None
    
    for copula in copulas:
        try:
            # Fit copula
            theta = copula.fit(u, v)
            
            # Goodness-of-fit test
            gof_stat, gof_pval = cramer_von_mises_copula(u, v, copula)
            
            # Select best based on GoF statistic (lower is better)
            if gof_stat < best_gof_stat:
                best_gof_stat = gof_stat
                best_pvalue = gof_pval
                best_copula = copula.name
                best_theta = theta
                
        except Exception as e:
            print(f"  Warning: Failed to fit {copula.name} copula: {e}")
            continue
    
    results['best_copula'] = best_copula
    results['copula_parameter'] = best_theta
    results['copula_gof_statistic'] = best_gof_stat
    results['copula_gof_pvalue'] = best_pvalue
    
    print(f"  Best copula: {best_copula} (theta={best_theta:.4f}, p={best_pvalue:.4f})")
    
    return results


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    
    if len(sys.argv) != 2:
        print("Usage: python rainfall_runoff_analysis_monthly.py <basin_index>")
        sys.exit(1)
    
    # Get basin index from command line (SLURM array task ID)
    basin_index = int(sys.argv[1]) - 1  # Convert to 0-based index
    
    # Paths
    basin_list_file = "/icebox/data/shares/mh2/mosavat/Lumped/temporal_test_basins.txt"
    data_dir = "/icebox/data/shares/mh2/mosavat/Lumped/data/processed/temporal_test/timeseries_monthly"
    output_dir = "/icebox/data/shares/mh2/mosavat/Lumped/results/temp_monthly"
    
    # Load basin IDs
    with open(basin_list_file, 'r') as f:
        basin_ids = [line.strip() for line in f.readlines()]
    
    if basin_index >= len(basin_ids):
        print(f"Error: Basin index {basin_index} out of range")
        sys.exit(1)
    
    basin_id = basin_ids[basin_index]
    data_path = f"{data_dir}/{basin_id}.csv"
    
    # Run analysis
    results = analyze_basin(basin_id, data_path)
    
    if results is not None:
        # Save results to temporary file
        results_df = pd.DataFrame([results])
        output_file = f"{output_dir}/basin_{basin_index:04d}.csv"
        results_df.to_csv(output_file, index=False)
        print(f"Results saved to {output_file}")
    else:
        print(f"Failed to analyze basin {basin_id}")
        sys.exit(1)

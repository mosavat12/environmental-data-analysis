#!/bin/bash
#SBATCH --job-name=rainfall_runoff_monthly
#SBATCH --time=01:00:00
#SBATCH --mem=4G
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --partition=mh1
#SBATCH --qos=mh1
#SBATCH --output=log_monthly/basin_%a.out
#SBATCH --error=log_monthly/basin_%a.err
#SBATCH --array=1-1089

# Create output directories if they don't exist
mkdir -p log_monthly
mkdir -p /icebox/data/shares/mh2/mosavat/Lumped/results/temp_monthly

# Run monthly analysis for this basin
python rainfall_runoff_analysis_monthly.py $SLURM_ARRAY_TASK_ID

echo "Basin $SLURM_ARRAY_TASK_ID (monthly) completed"

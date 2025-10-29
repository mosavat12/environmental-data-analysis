#!/bin/bash
#SBATCH --job-name=rainfall_runoff
#SBATCH --time=02:00:00
#SBATCH --mem=4G
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --partition=mh1
#SBATCH --qos=mh1
#SBATCH --output=log/basin_%a.out
#SBATCH --error=log/basin_%a.err
#SBATCH --array=1-1089%100

# Load required modules (adjust based on your HPC environment)
# module load python/3.9  # Uncomment and adjust if needed

# Create output directories if they don't exist
mkdir -p log
mkdir -p /icebox/data/shares/mh2/mosavat/Lumped/results/temp

# Run analysis for this basin
python rainfall_runoff_analysis.py $SLURM_ARRAY_TASK_ID

echo "Basin $SLURM_ARRAY_TASK_ID completed"
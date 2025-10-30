#!/bin/bash
#SBATCH --job-name=conf
#SBATCH --time=01:00:00
#SBATCH --mem=4G
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --exclude=uahpc-gpu003,uahpc-gpu004,uahpc-gpu008
#SBATCH --partition=mh1
#SBATCH --qos=mh1
#SBATCH --output=log/map.out
#SBATCH --error=log/map.err
#SBATCH --array=1

python create_maps_monthly.py
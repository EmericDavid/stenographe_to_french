#!/bin/bash
#SBATCH --job-name=process_wikipedia_V2
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --partition=gpu
#SBATCH --gpus-per-node=0
#SBATCH --mem=8G
#SBATCH --time=1:00:00
#SBATCH --output=logs/wikipedia_job_%A_%a.out
#SBATCH --error=logs/wikipedia_job_%A_%a.err

cd /home/nas-wks01/users/uapv2502538/wikipedia

source /etc/profile.d/conda.sh
conda activate /home/nas-wks01/users/uapv2502538/.conda/envs/env-wikipedia

echo "Processing URL: $1"
echo "Node: $(hostname)"

python process_single_url.py $1
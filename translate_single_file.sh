#!/bin/bash
#SBATCH --job-name=translate_wikipedia
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --partition=gpu
#SBATCH --gpus-per-node=0
#SBATCH --mem=16G
#SBATCH --time=1:00:00
#SBATCH --output=logs/wikipedia_translated/%x.%j.output.log
#SBATCH --error=logs/wikipedia_translated/%x.%j.error.log


cd /home/nas-wks01/users/uapv2502538/wikipedia

source /etc/profile.d/conda.sh
conda activate /home/nas-wks01/users/uapv2502538/.conda/envs/env-wikipedia

echo "Processing file python: $1"
echo "Node: $(hostname)"

python sent2steno.py $1
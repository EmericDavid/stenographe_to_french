#!/bin/bash
cd /home/nas-wks01/users/uapv2502538/wikipedia

mkdir -p logs/wikipedia_translated
mkdir -p data/wikipedia_translated


# for each file csv that don't contain _nopost in the name

for file in $(ls data/wikipedia_output/* | grep -v "_nopost"); do
    echo "Processing file shell: $file"
    sbatch translate_single_file.sh $file
    sleep 2
done

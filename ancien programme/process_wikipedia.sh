#!/bin/bash
#SBATCH --job-name=wiki_processing
#SBATCH --ntasks=5
#SBATCH --cpus-per-task=4
#SBATCH --partition=gpu
#SBATCH --mem=16G
#SBATCH --time=1:00:00
#SBATCH --array=0-14%4
#SBATCH --output=logs/wikipedia_job_%A_%a.out
#SBATCH --error=logs/wikipedia_job_%A_%a.err

# On descend dans le dossier
cd /home/nas-wks01/users/uapv2502538/wikipedia

# Créer les dossiers de logs et résultats si nécessaires
mkdir -p logs
mkdir -p data/wikipedia_dump
mkdir -p data/wikipedia_output

# Activer l'environnement conda si nécessaire
# Décommentez les lignes suivantes si vous utilisez conda
source /etc/profile.d/conda.sh
conda activate /home/nas-wks01/users/uapv2502538/.conda/envs/env-wikipedia

# Liste des URLs en format array bash
URLS=(
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles1.xml-p1p306134.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles2.xml-p306135p1050822.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles3.xml-p1050823p2550822.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles3.xml-p2550823p2977214.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles4.xml-p2977215p4477214.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles4.xml-p4477215p5202073.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles5.xml-p5202074p6702073.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles5.xml-p6702074p8202073.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles5.xml-p8202074p9074283.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles6.xml-p9074284p10574283.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles6.xml-p10574284p12074283.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles6.xml-p12074284p13574283.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles6.xml-p13574284p15074283.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles6.xml-p15074284p16574283.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles6.xml-p16574284p16733183.bz2"
)

# Récupérer l'URL correspondant à l'index de l'array job
URL=${URLS[$SLURM_ARRAY_TASK_ID]}

echo "Job started: $(date)"
echo "Processing URL: $URL"
echo "Task ID: $SLURM_ARRAY_TASK_ID"
echo "Node: $(hostname)"

# Créer un script Python temporaire pour traiter un seul URL
cat > process_single_url.py << 'EOL'
import download_wikipedia_xml
import xml_to_csv_wikipedia_old
import os
import sys

# Récupérer l'URL depuis les arguments
url = sys.argv[1]

# Traiter l'URL
print(f"Processing URL: {url}")
result = download_wikipedia_xml.process_url(url)
print(f"Processing result: {result}")

# Vérifier si le téléchargement a réussi
if not result['verified']:
    print(f'Error: {result["error"]}')
    sys.exit(1)

filepath_dump = result['filepath'].replace("\\", "/")
print(f"Filepath dump: {filepath_dump}")

filepath_output = filepath_dump.replace("data/wikipedia_dump", "data/wikipedia_output")

# Vérifier si le fichier est déjà converti en CSV
if not os.path.exists(filepath_output + ".csv"):
    print("Démarrage de l'extraction des phrases...")
    sentences = xml_to_csv_wikipedia_old.extract_text_from_xml(filepath_dump)

    # Écrire dans un fichier CSV
    output_file = f'{filepath_output}_nopost.csv'
    xml_to_csv_wikipedia_old.write_to_csv(sentences, output_file)

    print("Démarrage du post-traitement pour éliminer les lignes problématiques...")
    final_output = f'{filepath_output}.csv'
    xml_to_csv_wikipedia_old.post_process_csv(output_file, final_output)
    
    # Valider le jeu de données final
    xml_to_csv_wikipedia_old.validate_final_dataset(final_output)
    
    print(f"Traitement terminé pour {url}")
else:
    print(f"Le fichier {filepath_output}.csv existe déjà. Aucune conversion nécessaire.")
EOL

# Exécuter le script Python avec l'URL spécifique
python process_single_url.py "$URL"

# Vérifier que le script s'est bien exécuté
if [ $? -eq 0 ]; then
    echo "Job completed successfully: $(date)"
else
    echo "Job failed with error code $?: $(date)"
    exit 1
fi

# Nettoyer le script temporaire
rm process_single_url.py

echo "Job finished: $(date)"
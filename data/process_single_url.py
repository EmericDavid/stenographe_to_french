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

filepath_output = filepath_dump.replace("wikipedia_dump", "wikipedia_output")

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
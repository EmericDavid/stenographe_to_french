import download_wikipedia_xml
import xml_to_csv_wikipedia_old
import os

urls = [
    #"https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles1.xml-p1p306134.bz2",
    #"https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles2.xml-p306135p1050822.bz2",
    #"https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles3.xml-p1050823p2550822.bz2",
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles3.xml-p2550823p2977214.bz2",
    #"https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles4.xml-p2977215p4477214.bz2",
    #"https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles4.xml-p4477215p5202073.bz2",
    #"https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles5.xml-p5202074p6702073.bz2",
    #"https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles5.xml-p6702074p8202073.bz2",
    #"https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles5.xml-p8202074p9074283.bz2",
    #"https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles6.xml-p9074284p10574283.bz2",
    #"https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles6.xml-p10574284p12074283.bz2",
    #"https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles6.xml-p12074284p13574283.bz2",
    #"https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles6.xml-p13574284p15074283.bz2",
    #"https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles6.xml-p15074284p16574283.bz2",
    #"https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles6.xml-p16574284p16733183.bz2"
]


# Créer le dossier de sortie si nécessaire
if not os.path.exists('data/wikipedia_dump'):
    os.makedirs('data/wikipedia_dump')

if not os.path.exists('data/wikipedia_output'):
    os.makedirs('data/wikipedia_output')

for url in urls:
    result = download_wikipedia_xml.process_url(url)
    print(f"Processing result: {result}")

    # check if verified is True
    if not result['verified']:
        print(f'Error : {result["error"]}')
        exit(1)
    
    filepath_dump = result['filepath'].replace("\\", "/")
    print(f"Filepath dump: {filepath_dump}")

    filepath_output = filepath_dump.replace("data/wikipedia_dump", "data/wikipedia_output")

    #check if already converted to csv
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

    else:
        print(f"Le fichier {filepath_output}.csv existe déjà. Aucune conversion nécessaire.")

from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import csv
import re
from num2words import num2words

# Compile regular expressions once
reg = re.compile(r"[0-9]+-[0-9]+|1er[e]?[s]?|2d[e]?[s]?|[0-9]+ème|[0-9]+e|[0-9]+")

def convert_match(match):
    it = match.group()
    if '-' in it:
        return it.replace("-", " à ")
    elif re.match(r"1er[e]?[s]?|2d[e]?[s]?|[0-9]+ème|[0-9]+e", it):
        num = re.sub(r"[^0-9]", "", it)
        return num2words(num, lang='fr', to='ordinal')
    else:
        return num2words(it, lang='fr')

def pre_traitement(phrase):
    return reg.sub(convert_match, phrase)

def process_row(row):
    phrase_steno, french_phrase = row
    french_phrase = pre_traitement(french_phrase)  # Prétraiter la phrase
    return [phrase_steno, french_phrase]

def process_csv_file(csv_filepath):
    """
    Lit un fichier CSV et applique la fonction pre_traitement sur la seconde colonne.
    Format CSV attendu: phrase_steno,phrase_fr
    """
    updated_rows = []
    fails = 0

    # Compter le nombre total de lignes pour la barre de progression
    with open(csv_filepath, 'r', encoding='utf-8') as file:
        total_lines = sum(1 for _ in file) - 1  # -1 pour l'en-tête

    with open(csv_filepath, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=',')
        header = next(reader)  # Skip header
        updated_rows.append(header)

        # Process rows in chunks to reduce memory usage
        def chunked_reader(reader, chunk_size=100):
            chunk = []
            for row in reader:
                chunk.append(row)
                if len(chunk) == chunk_size:
                    yield chunk
                    chunk = []
            if chunk:
                yield chunk

        with Pool(processes=cpu_count()) as pool:
            with tqdm(total=total_lines, desc="Traitement des phrases") as pbar:
                for chunk in chunked_reader(reader):
                    results = pool.map(process_row, chunk)
                    updated_rows.extend(results)
                    pbar.update(len(chunk))  # Update progress bar by the chunk size

    # Réécriture dans le même fichier
    with open(csv_filepath, 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerows(updated_rows)

    return fails

if __name__ == "__main__":
    # Traiter le fichier CSV
    csv_filepath = 'data/wikipedia_phrases.csv'
    fails = process_csv_file(csv_filepath)
    with open(csv_filepath, 'r', encoding='utf-8') as file:
        content = file.read()
        length = len(content.split('\n')) - 1
    print(f"\nTraitement terminé. Le fichier {csv_filepath} a été mis à jour.")
    print(f"Il y a {length-fails} phrases qui ont pu être traitées.")
import re
import csv
from tqdm import tqdm
from nombres_en_lettres import pre_traitement

def create_word_to_steno_dict(filepath):
    """
    Crée un dictionnaire qui associe chaque mot à ses sténogrammes.
    """
    word_to_steno = {}
    
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for line in lines:
            try:
                word, stenos = line.strip().split(" :: ")
                word = word.lower()  # Convertir en minuscules pour la recherche
                word_to_steno[word] = stenos
            except ValueError:
                continue
    
    return word_to_steno

def extract_words_and_punct(phrase):
    """
    Sépare les mots et la ponctuation d'une phrase.
    Retourne une liste de tuples (mot, ponctuation).
    """
    # Définir les ponctuations de fin de phrase et de milieu de phrase
    end_punct = ['.', '!', '?', '...']
    mid_punct = [':', ',', ';', '-', '—', '(', ')', '[', ']', '{', '}', '<', '>', '"', '«', '»']
    
    words = []
    current_word = ""
    current_punct = ""
    
    for char in phrase.strip() + " ":  # Ajouter un espace à la fin pour traiter le dernier mot
        if char.isspace():
            if current_word:
                words.append((current_word, current_punct))
                current_word = ""
                current_punct = ""
        elif char in end_punct + mid_punct:
            if current_word:
                words.append((current_word, char))
                current_word = ""
                current_punct = ""
            else:
                # Si on a une ponctuation sans mot précédent, on l'ajoute comme élément séparé
                words.append(("", char))
        else:
            current_word += char
            
    return words

def convert_to_steno(phrase, word_to_steno):
    """
    Convertit une phrase en sténogrammes.
    Retourne (None, liste_mots_manquants) si des mots ne sont pas dans le vocabulaire.
    Retourne (stenos, []) si tous les mots sont trouvés.
    """
    result = []
    missing_words = []
    words_and_punct = extract_words_and_punct(phrase.lower())
    
    for word, punct in words_and_punct:
        if word:  # Si on a un mot
            if word not in word_to_steno:
                missing_words.append(word)
            else:
                result.append(word_to_steno[word] + punct)
        else:  # Si on a juste une ponctuation
            result.append(punct)
    
    if missing_words:
        return None, missing_words
    return " ".join(result), []

def process_csv_file(csv_filepath, word_to_steno):
    """
    Lit un fichier CSV et traduit les phrases en sténogrammes.
    Format CSV attendu: id;phrase en francais;phrase en stenogramme
    """
    updated_rows = []
    translated_rows = []  # Pour stocker les phrases traduites
    fails = 0
    
    # Compter le nombre total de lignes pour la barre de progression
    with open(csv_filepath, 'r', encoding='utf-8') as file:
        total_lines = sum(1 for _ in file) - 1  # -1 pour l'en-tête
    
    with open(csv_filepath, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=',')
        header = next(reader)  # Skip header
        updated_rows.append(header)
        translated_rows.append(header)  # Ajouter l'en-tête au fichier des phrases traduites
        
        # Utiliser tqdm pour afficher la progression
        for row in tqdm(reader, total=total_lines, desc="Traduction des phrases"):
            id, french_phrase, _ = row
            #french_phrase=pre_traitement(french_phrase)  # Prétraiter la phrase
            result, missing_words = convert_to_steno(french_phrase, word_to_steno)
            
            if result is None:
                fails += 1
                updated_rows.append([id, french_phrase, "NULL"])
            else:
                updated_rows.append([id, french_phrase, result])
                translated_rows.append([id, french_phrase, result])  # Ajouter les phrases traduites
    
    
    # Écriture des phrases traduites dans un autre fichier
    with open('translated_phrases.csv', 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerows(translated_rows)
    
    return fails

if __name__ == "__main__":
    # Charger le dictionnaire
    word_to_steno = create_word_to_steno_dict('train.steno.txt')
    
    # Traiter le fichier CSV
    csv_filepath = 'wikipedia_phrases.csv'
    fails = process_csv_file(csv_filepath, word_to_steno)
    with open(csv_filepath, 'r', encoding='utf-8') as file:
        content = file.read()
        length = len(content.split('\n')) - 1
    print(f"\nTraitement terminé. Le fichier {csv_filepath} a été mis à jour.")
    print(f"Un fichier 'translated_phrases.csv' a été créé avec toutes les phrases traduites.")
    print(f"Il y a {length-fails} phrases qui ont pu être traduites.")
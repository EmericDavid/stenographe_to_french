import xml.etree.ElementTree as ET
import csv
import re
from tqdm import tqdm
import nltk
import os
import multiprocessing
from functools import partial
import io

# Alternative avec une valeur fixe
csv.field_size_limit(10000000)  # 10 millions de caractères

# Télécharger les ressources NLTK pour la tokenisation des phrases
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
from nltk.tokenize import sent_tokenize

def clean_text(text):
    """Nettoie le texte en supprimant les balises wiki, HTML, et autres éléments non textuels."""
    if not text:
        return ""
        
    # Supprimer les redirections
    if text.startswith('#REDIRECT') or text.startswith('#redirect'):
        return ""
    
    # Supprimer les formules mathématiques avec \lim, \to, etc.
    text = re.sub(r'\\lim_[^}]+}', '', text)
    text = re.sub(r'\\to', '', text)
    text = re.sub(r'\\[a-zA-Z]+', '', text)  # Autres commandes LaTeX
    
    # Supprimer les notations mathématiques courantes
    text = re.sub(r'\$[^$]*\$', '', text)  # Formules entre $...$
    text = re.sub(r'\$\$[^$]*\$\$', '', text)  # Formules entre $$...$$
    
    # Nettoyer les symboles mathématiques spécifiques
    text = re.sub(r'[\+\-\*\/\=\(\)\[\]\{\}\^\_\<\>\~\|]', ' ', text)
    
    # Supprimer les pages de catégorie
    if "Catégorie:" in text or "Category:" in text:
        text = re.sub(r'Catégorie:.*?(\n|\Z)', '', text, flags=re.DOTALL)
        text = re.sub(r'Category:.*?(\n|\Z)', '', text, flags=re.DOTALL)
    
    # Supprimer les tableaux wiki complets
    text = re.sub(r'\{\|.*?\|\}', ' ', text, flags=re.DOTALL)
    
    # Supprimer les templates wiki
    text = re.sub(r'\{\{.*?\}\}', ' ', text, flags=re.DOTALL)
    
    # Supprimer les balises XML/HTML
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Supprimer les références Wiki comme [[...]]
    text = re.sub(r'\[\[[^\]]*\|([^\]]*)\]\]', r'\1', text)
    text = re.sub(r'\[\[([^\]]*)\]\]', r'\1', text)
    
    # Supprimer les liens externes
    text = re.sub(r'\[https?://[^\s\]]+\s+([^\]]*)\]', r'\1', text)
    text = re.sub(r'\[https?://[^\s\]]+\]', '', text)
    
    # Supprimer les styles wiki
    text = re.sub(r"'{2,}", '', text)
    
    # Supprimer les sections
    text = re.sub(r'==+[^=]+=+=', ' ', text)
    
    # Supprimer les listes et autres formatages wiki
    text = re.sub(r'^\*+\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\#+\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\:+\s+', '', text, flags=re.MULTILINE)
    
    # Supprimer les lignes de tableau
    text = re.sub(r'^\|.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^!.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\|-.*$', '', text, flags=re.MULTILINE)
    
    # Supprimer les fichiers et images
    text = re.sub(r'\[\[File:[^\]]*\]\]', '', text)
    text = re.sub(r'\[\[Image:[^\]]*\]\]', '', text)
    text = re.sub(r'\[\[Fichier:[^\]]*\]\]', '', text)
    text = re.sub(r'Image:.*?(?:\.jpg|\.png|\.gif)', '', text, flags=re.IGNORECASE)
    
    # Supprimer les attributs HTML
    text = re.sub(r'(class|style|align|cellpadding|cellspacing|colspan|bgcolor|width|height)="[^"]*"', '', text)
    
    # Supprimer les mentions "small"
    text = re.sub(r'small', '', text)
    
    # Remplacer les espaces multiples par un seul
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def has_balanced_structure(sentence):
    """Vérifie si la phrase a une structure équilibrée (ratio mots/ponctuation)"""
    words = re.findall(r'\b\w+\b', sentence)
    punctuation_count = len(re.findall(r'[,;:]', sentence))
    
    # Une phrase bien formée a généralement plus de mots que de signes de ponctuation
    if len(words) > 0 and punctuation_count > 0:
        ratio = len(words) / punctuation_count
        return ratio > 3  # Au moins 3 mots pour chaque signe de ponctuation
    
    return True  # Si pas de ponctuation, c'est acceptable

def is_complete_sentence(sentence):
    """Détecte si la phrase contient probablement un sujet et un verbe"""
    # Recherche un modèle simple: [mot(s)] + [verbe conjugué]
    return re.search(r'\b[A-Za-zÀ-ÿ]+\b[\s\w]*\b(?:est|sont|était|étaient|a|ont|avait|avaient|(?:[a-zéèêëàâäôöîïù]+(?:e|es|ent|ons|ez|ait|aient)))\b', sentence) is not None

def is_valid_sentence(sentence):
    """Vérifie si une phrase est valide selon des critères linguistiques plus stricts."""
    # Ignorer les phrases trop courtes
    if len(sentence) < 15:
        return False
    
    # Ignorer les phrases avec "Image:" ou "File:" qui sont probablement des résidus de balises d'image
    if re.search(r'Image:|File:|Fichier:', sentence, re.IGNORECASE):
        return False
    
    # Ignorer les phrases avec "px", "right", "left" qui sont souvent des résidus de formatage d'image
    if re.search(r'\b(?:px|right|left)\b', sentence):
        return False
    
    # Ignorer les phrases avec trop de virgules par rapport aux mots
    words = re.findall(r'\b\w+\b', sentence)
    if len(words) > 0 and sentence.count(',') > len(words) / 3:
        return False
    
    # Ignorer les listes de noms, qui contiennent beaucoup de virgules et peu de verbes
    if sentence.count(',') > 3 and sentence.count('.') < 2:
        if not re.search(r'\b(?:est|sont|était|étaient|a|ont|avait|avaient|sera|seront)\b', sentence):
            return False
    
    # Ignorer les phrases commençant par "Voir aussi" qui sont souvent des références
    if sentence.startswith("Voir aussi"):
        return False
        
    # Ignorer les phrases contenant "small" qui sont des résidus de formatage
    if "small" in sentence:
        return False
    
    # Ignorer les entrées de type dictionnaire/encyclopédie sans verbe
    if re.match(r'^[A-Z][a-z]+\s*:', sentence) or re.match(r'^[A-Z][a-z]+\s+\(', sentence):
        if not is_complete_sentence(sentence):
            return False
    
    # Ignorer les phrases avec beaucoup d'années entre parenthèses (souvent des listes biographiques)
    year_pattern = r'\(\d{4}\s*[-–]\s*\d{4}\)'
    year_matches = re.findall(year_pattern, sentence)
    if len(year_matches) > 1:
        if sentence.count(',') > 2:  # Si c'est une liste biographique
            return False
    
    # Les vérifications existantes...
    if any(symbol in sentence for symbol in ['lim', '\\to', '\\infty', '→', 'ℓ', '}}', '{{', 'px']):
        return False
        
    if re.search(r'[_\^{}\\]', sentence):
        return False
    
    # Vérifier que la phrase contient un verbe conjugué
    if not is_complete_sentence(sentence):
        return False
    
    # Ignorer les phrases qui sont des énumérations
    if re.match(r'^[\w\s]+\s+\([^)]+\)(,\s+[\w\s]+\s+\([^)]+\))+', sentence):
        return False
    
    # Vérifier que la phrase se termine par un signe de ponctuation approprié
    if not re.search(r'[.!?]$', sentence):
        return False
    
    # Ignorer les phrases contenant trop de nombres/dates
    if len(re.findall(r'\d{4}', sentence)) > 3:
        return False
    
    # Vérifier structure équilibrée
    if not has_balanced_structure(sentence):
        return False
    
    return True

def split_xml_file(file_path, num_chunks):
    """Divise le fichier XML en chunks pour le traitement parallèle sans comptage préalable."""
    # Obtenir la taille du fichier en octets
    file_size = os.path.getsize(file_path)
    chunk_size_bytes = file_size // num_chunks
    
    # Liste pour stocker les positions de début et fin de chaque chunk
    chunks = []
    
    print("Préparation des chunks pour le traitement parallèle...")
    
    # Créer des chunks basés sur les offsets de fichier
    for i in range(num_chunks):
        start_pos = i * chunk_size_bytes
        end_pos = (i + 1) * chunk_size_bytes if i < num_chunks - 1 else file_size
        chunks.append((start_pos, end_pos))
    
    return chunks

def process_chunk(file_path, chunk_range, lock):
    """Traite un chunk du fichier XML basé sur des positions en octets."""
    start_pos, end_pos = chunk_range
    sentences = []
    
    # Créer une barre de progression locale
    with lock:
        pbar = tqdm(total=1, 
                    desc=f"Chunk {start_pos}-{end_pos}", 
                    position=multiprocessing.current_process()._identity[0] % os.cpu_count(),
                    leave=False)
    
    # Ouvrir le fichier et se positionner au début du chunk
    with open(file_path, 'rb') as f:
        f.seek(start_pos)
        
        # Si ce n'est pas le premier chunk, chercher la balise <page> complète suivante
        if start_pos > 0:
            # Lire les données jusqu'à trouver une balise <page> complète
            chunk_data = b""
            while True:
                line = f.readline()
                if not line:  # Fin du fichier
                    break
                if b"<page>" in line:
                    chunk_data = line
                    break
        else:
            # Pour le premier chunk, commencer au début du fichier
            chunk_data = b""
        
        # Lire jusqu'à la position de fin ou jusqu'à ce que le chunk se termine correctement
        current_pos = f.tell()
        while current_pos < end_pos:
            line = f.readline()
            if not line:  # Fin du fichier
                break
                
            chunk_data += line
            current_pos = f.tell()
        
        # Si ce n'est pas le dernier chunk, lire jusqu'à trouver la fin d'une page
        if end_pos < os.path.getsize(file_path):
            while True:
                line = f.readline()
                if not line:  # Fin du fichier
                    break
                    
                chunk_data += line
                if b"</page>" in line:
                    break
    
    # Analyser le chunk XML
    try:
        context = ET.iterparse(io.BytesIO(chunk_data), events=('end',))
        for event, elem in context:
            if elem.tag.endswith('page'):
                # Traiter la page
                title = None
                text = None
                
                for child in elem:
                    if child.tag.endswith('title'):
                        title = child.text
                    elif child.tag.endswith('revision'):
                        for rev_child in child:
                            if rev_child.tag.endswith('text'):
                                text = rev_child.text
                
                # Ignorer les pages de catégorie, portail, etc.
                if title and any(prefix in title for prefix in ["Catégorie:", "Category:", "Portail:", "Portal:", "Modèle:", "Template:", "Aide:", "Help:"]):
                    elem.clear()
                    continue
                    
                if text:
                    # Nettoyer le texte
                    cleaned_text = clean_text(text)
                    
                    # Ignorer les pages vides après nettoyage
                    if cleaned_text:
                        # Tokeniser le texte en phrases
                        try:
                            tokenized_sentences = sent_tokenize(cleaned_text, language='french')
                            
                            # Filtrer les phrases
                            for s in tokenized_sentences:
                                s = s.strip()
                                if is_valid_sentence(s):
                                    sentences.append(['', s])
                        except Exception as e:
                            with lock:
                                print(f"Erreur lors de la tokenisation de la page '{title}': {e}")
                
                elem.clear()
        
    except ET.ParseError as e:
        with lock:
            print(f"Erreur d'analyse XML dans le chunk {start_pos}-{end_pos}: {e}")
    
    with lock:
        pbar.update(1)
        pbar.close()
    
    return sentences

def extract_text_from_xml_parallel(file_path, num_processes=None):
    """Extrait le texte de chaque page de l'XML de Wikipedia en utilisant le parallélisme."""
    if num_processes is None:
        num_processes = min(os.cpu_count(), 8)
    
    print(f"Utilisation de {num_processes} processus pour le traitement parallèle.")
    
    # Diviser le fichier en chunks basés sur la taille du fichier
    chunks = split_xml_file(file_path, num_processes)
    print(f"Fichier divisé en {len(chunks)} chunks.")
    
    # Créer un verrou pour les opérations d'affichage
    manager = multiprocessing.Manager()
    lock = manager.Lock()
    
    # Créer un pool de processus et leur attribuer des chunks
    pool = multiprocessing.Pool(processes=num_processes)
    process_chunk_partial = partial(process_chunk, file_path, lock=lock)
    
    # Traiter les chunks en parallèle
    print("Démarrage du traitement parallèle...")
    results = pool.map(process_chunk_partial, chunks)
    
    # Fermer le pool et attendre que tous les processus soient terminés
    pool.close()
    pool.join()
    
    # Fusionner les résultats
    all_sentences = []
    for chunk_sentences in results:
        all_sentences.extend(chunk_sentences)
    
    return all_sentences

def write_to_csv(sentences, output_file):
    """Écrit les phrases extraites dans un fichier CSV."""
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["phrase_steno","phrase_fr"])
        writer.writerows(sentences)
        
    print(f"Fichier CSV créé avec succès: {output_file}")
    print(f"Nombre total de phrases extraites: {len(sentences)}")

def post_process_csv_worker(chunk, lock):
    """Traite un chunk de lignes CSV pour le post-traitement parallèle."""
    rows_to_keep = []
    
    for row in chunk:
        phrase = row[1]
        
        # Supprimer les guillemets qui entourent toute la phrase
        if phrase.startswith('"') and phrase.endswith('"'):
            phrase = phrase[1:-1]
        
        # Vérifier tous les critères encore une fois pour être sûr
        if is_valid_sentence(phrase):
            row[1] = phrase  # Mettre à jour la phrase sans guillemets
            rows_to_keep.append(row)
    
    # Incrémenter la barre de progression
    with lock:
        pbar.update(len(chunk))
    
    return rows_to_keep

def post_process_csv(input_file, output_file, num_processes=None):
    """Effectue un post-traitement parallèle du CSV pour éliminer les lignes problématiques."""
    # Définir le nombre de processus (par défaut: nombre de CPU)
    if num_processes is None:
        num_processes = min(os.cpu_count(), 8)  # Limiter à 8 processus max par défaut
    
    print(f"Utilisation de {num_processes} processus pour le post-traitement.")
    
    # Lire toutes les lignes du fichier CSV
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        all_rows = list(reader)
    
    # Créer un manager et un verrou pour les opérations d'affichage
    manager = multiprocessing.Manager()
    lock = manager.Lock()
    
    # Initialiser la barre de progression globale
    global pbar
    pbar = tqdm(total=len(all_rows), desc="Post-traitement des phrases", unit="phrase")
    
    # Diviser les lignes en chunks pour le traitement parallèle
    chunk_size = len(all_rows) // num_processes + (1 if len(all_rows) % num_processes != 0 else 0)
    chunks = [all_rows[i:i+chunk_size] for i in range(0, len(all_rows), chunk_size)]
    
    # Créer un pool de processus
    pool = multiprocessing.Pool(processes=num_processes)
    post_process_chunk_partial = partial(post_process_csv_worker, lock=lock)
    
    # Traiter les chunks en parallèle
    results = pool.map(post_process_chunk_partial, chunks)
    
    # Fermer le pool et attendre que tous les processus soient terminés
    pool.close()
    pool.join()
    
    # Fermer la barre de progression
    pbar.close()
    
    # Fusionner les résultats
    rows_to_keep = []
    for chunk_rows in results:
        rows_to_keep.extend(chunk_rows)
    
    # Réécrire le fichier avec les ID réindexés
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        for i, row in enumerate(rows_to_keep, 1):
            writer.writerow(['', row[1]])
    
    total_kept = len(rows_to_keep)
    total_rows = len(all_rows)
    print(f"Post-traitement terminé. {total_kept} phrases conservées sur {total_rows} phrases initiales ({(total_kept/total_rows)*100:.2f}%).")
    print(f"Fichier nettoyé: {output_file}")

def validate_final_dataset(file_path):
    """Valide la qualité du jeu de données final en affichant un échantillon des phrases."""
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Sauter l'en-tête
        rows = list(reader)

    print(f"Nombre total de phrases dans le jeu de données final: {len(rows)}")

if __name__ == "__main__":
    # Chemin du fichier XML Wikipedia
    file_path = 'data/wikipedia_output/frwiki-20250301-pages-articles3.xml-p2550823p2977214'
    #file_path = 'data/wikipedia_output/frwiki-20250301-pages-articles.xml'
    
    # Vérifier que le fichier existe
    if not os.path.isfile(file_path):
        print(f"Erreur: Le fichier {file_path} n'existe pas.")
        exit(1)
    
    # Créer le dossier de sortie si nécessaire
    if not os.path.exists('data/wikipedia_output'):
        os.makedirs('data/wikipedia_output')
    
    # Obtenir le nombre de processeurs disponibles
    num_cpus = os.cpu_count()
    # Utiliser 75% des cœurs disponibles (au moins 2)
    num_processes = max(2, int(num_cpus * 0.75))
    print(f"Détection de {num_cpus} CPU disponibles. Utilisation de {num_processes} processus.")
    
    # Extraire les phrases en parallèle
    print("Démarrage de l'extraction parallèle des phrases...")
    sentences = extract_text_from_xml_parallel(file_path, num_processes=num_processes)
    
    # Écrire dans un fichier CSV
    output_file = 'data/wikipedia_output/wikipedia_phrases_nopost.csv'
    write_to_csv(sentences, output_file)
    
    # Effectuer un post-traitement pour éliminer les lignes problématiques
    print("Démarrage du post-traitement parallèle pour éliminer les lignes problématiques...")
    final_output = 'data/wikipedia_output/wikipedia_phrases.csv'
    post_process_csv(output_file, final_output, num_processes=num_processes)
    
    # Valider le jeu de données final
    validate_final_dataset(final_output)
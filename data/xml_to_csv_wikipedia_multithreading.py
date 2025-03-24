import xml.etree.ElementTree as ET
import csv
import re
from tqdm import tqdm
import nltk
import os
import concurrent.futures
import multiprocessing
import queue
import threading
import time

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

def process_page(page_data):
    """Traite une page pour en extraire les phrases valides."""
    title, text = page_data
    
    # Ignorer les pages de catégorie, portail, etc.
    if title and any(prefix in title for prefix in ["Catégorie:", "Category:", "Portail:", "Portal:", "Modèle:", "Template:", "Aide:", "Help:"]):
        return []
    
    filtered_sentences = []
    
    if text:
        # Nettoyer le texte
        cleaned_text = clean_text(text)
        
        # Ignorer les pages vides après nettoyage
        if cleaned_text:
            # Tokeniser le texte en phrases
            try:
                sentences = sent_tokenize(cleaned_text, language='french')
                
                # Filtrer les phrases
                for s in sentences:
                    s = s.strip()
                    # Vérifier si la phrase est valide (critères stricts)
                    if (len(s) > 15 and 
                        not s.startswith('{') and 
                        not s.startswith('|') and 
                        not s.startswith('!') and
                        not s.startswith('Catégorie:') and
                        not s.startswith('Category:') and
                        not s.startswith('Voir aussi') and
                        not re.search(r'Image:|File:|Fichier:', s, re.IGNORECASE) and
                        not "small" in s and
                        not re.search(r'class=|style=|align=|colspan=', s) and
                        re.search(r'[.!?]$', s) and  # S'assurer que la phrase se termine par un signe de ponctuation
                        is_complete_sentence(s)):  # Vérifier si c'est une phrase complète
                        
                        if is_valid_sentence(s):  # Appliquer tous les filtres avancés
                            filtered_sentences.append(s)
            
            except Exception as e:
                print(f"Erreur lors de la tokenisation de la page '{title}': {e}")
    
    return filtered_sentences

def extract_text_from_xml_multithreaded(file_path, num_workers=None):
    """
    Extrait le texte de chaque page de l'XML de Wikipedia en utilisant le multithreading
    avec une barre de progression individuelle pour chaque thread.
    """
    # Si num_workers n'est pas spécifié, utiliser le nombre de processeurs disponibles
    if num_workers is None:
        num_workers = multiprocessing.cpu_count()
    
    print(f"Utilisation de {num_workers} threads pour l'extraction et le traitement des pages")
        
    # Initialiser une liste pour stocker les pages (titre, texte)
    pages_to_process = []
    
    # Initialiser une queue pour collecter les résultats et un verrou pour gérer les barres de progression
    result_queue = queue.Queue()
    tqdm_lock = threading.Lock()
    
    # Mettre en place la barre de progression pour la collecte des pages
    pbar = tqdm(desc="Collecte des pages", unit="page")
    
    # Parcourir le fichier XML et collecter les pages
    print("Collecte des pages à traiter...")
    for event, elem in ET.iterparse(file_path, events=('end',)):
        if elem.tag.endswith('page'):
            # Trouver le titre et le texte
            title = None
            text = None
            
            for child in elem:
                if child.tag.endswith('title'):
                    title = child.text
                elif child.tag.endswith('revision'):
                    for rev_child in child:
                        if rev_child.tag.endswith('text'):
                            text = rev_child.text
            
            # Ajouter la page à la liste à traiter
            pages_to_process.append((title, text))
            
            # Vider l'élément pour libérer la mémoire
            elem.clear()
            
            # Mettre à jour la barre de progression
            pbar.update(1)
    
    pbar.close()
    print(f"Collecte terminée. {len(pages_to_process)} pages à traiter.")
    
    # Répartir les pages en lots pour les threads
    batches = []
    batch_size = len(pages_to_process) // num_workers
    if batch_size == 0:
        batch_size = 1
    
    for i in range(0, len(pages_to_process), batch_size):
        batches.append(pages_to_process[i:i+batch_size])
    
    # Ajuster le dernier lot si nécessaire
    if len(batches) > num_workers:
        batches[-2].extend(batches[-1])
        batches.pop()
    
    print(f"Démarrage du traitement multithreadé avec {len(batches)} lots")
    
    # Fonction pour traiter une page avec sa propre barre de progression
    def process_page_batch(pages_batch, thread_id):
        # Créer une barre de progression pour ce thread
        with tqdm_lock:
            thread_pbar = tqdm(total=len(pages_batch), 
                              desc=f"Thread {thread_id}", 
                              position=thread_id+1, 
                              leave=True,
                              unit="page")
        
        batch_sentences = []
        for page_data in pages_batch:
            sentences = process_page(page_data)
            batch_sentences.extend(sentences)
            with tqdm_lock:
                thread_pbar.update(1)
        
        # Fermer la barre de progression du thread
        with tqdm_lock:
            thread_pbar.close()
            
        # Mettre les résultats dans la queue
        result_queue.put((thread_id, batch_sentences))
    
    # Pour garder les barres de progression alignées
    print("\n" * (num_workers + 1))  # Ajouter de l'espace pour toutes les barres de progression
    
    # Créer et démarrer les threads
    threads = []
    for i, batch in enumerate(batches):
        thread = threading.Thread(target=process_page_batch, args=(batch, i))
        threads.append(thread)
        thread.start()
    
    # Mettre en place une barre de progression globale pour suivre les threads terminés
    with tqdm_lock:
        global_pbar = tqdm(total=len(threads), 
                         desc="Threads terminés",
                         position=0, 
                         leave=True,
                         unit="thread")
    
    # Collecter les résultats
    all_sentences = []
    completed_threads = 0
    
    while completed_threads < len(threads):
        try:
            thread_id, sentences = result_queue.get(timeout=1)
            all_sentences.extend([(s, '') for s in sentences])
            completed_threads += 1
            with tqdm_lock:
                global_pbar.update(1)
        except queue.Empty:
            continue
    
    # Attendre que tous les threads se terminent
    for thread in threads:
        thread.join()
    
    with tqdm_lock:
        global_pbar.close()
    
    # Formater les résultats pour CSV (phrase_steno, phrase_fr)
    formatted_sentences = [['', s] for s, _ in all_sentences]
    
    print(f"\nExtraction terminée. {len(formatted_sentences)} phrases extraites au total.")
    return formatted_sentences

def post_process_csv_multithreaded(input_file, output_file, num_workers=None):
    """Effectue un post-traitement du CSV avec multithreading pour éliminer les lignes problématiques."""
    # Si num_workers n'est pas spécifié, utiliser le nombre de processeurs disponibles
    if num_workers is None:
        num_workers = multiprocessing.cpu_count()
    
    print(f"Utilisation de {num_workers} threads pour le post-traitement")
    
    # Lire toutes les phrases du fichier
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)  # Garder l'en-tête
        rows = list(reader)
    
    total_rows = len(rows)
    print(f"Nombre total de phrases à traiter: {total_rows}")
    
    # Créer un verrou pour les barres de progression
    tqdm_lock = threading.Lock()
    
    # Initialiser une queue pour collecter les résultats
    result_queue = queue.Queue()
    
    # Fonction pour traiter un lot de phrases avec sa propre barre de progression
    def process_sentence_batch(batch, batch_id):
        # Créer une barre de progression pour ce thread
        with tqdm_lock:
            thread_pbar = tqdm(total=len(batch), 
                              desc=f"Thread {batch_id}", 
                              position=batch_id+1, 
                              leave=True,
                              unit="phrase")
            
        valid_sentences = []
        for row in batch:
            phrase = row[1]
            
            # Supprimer les guillemets qui entourent toute la phrase
            if phrase.startswith('"') and phrase.endswith('"'):
                phrase = phrase[1:-1]
            
            # Vérifier tous les critères encore une fois pour être sûr
            if is_valid_sentence(phrase):
                valid_sentences.append(row)
            
            # Mettre à jour la barre de progression
            with tqdm_lock:
                thread_pbar.update(1)
        
        # Fermer la barre de progression
        with tqdm_lock:
            thread_pbar.close()
            
        # Mettre les résultats dans la queue
        result_queue.put((batch_id, valid_sentences))
    
    # Répartir les phrases en lots
    batches = []
    batch_size = total_rows // num_workers
    if batch_size == 0:
        batch_size = 1
    
    for i in range(0, total_rows, batch_size):
        batches.append(rows[i:i+batch_size])
    
    # Pour garder les barres de progression alignées
    print("\n" * (num_workers + 1))  # Ajouter de l'espace pour toutes les barres de progression
    
    # Créer et démarrer les threads
    threads = []
    for i, batch in enumerate(batches):
        thread = threading.Thread(target=process_sentence_batch, args=(batch, i))
        threads.append(thread)
        thread.start()
    
    # Mettre en place une barre de progression globale pour suivre les threads terminés
    with tqdm_lock:
        global_pbar = tqdm(total=len(threads), 
                          desc="Threads terminés", 
                          position=0, 
                          leave=True,
                          unit="thread")
    
    # Collecter les résultats
    valid_rows = []
    completed_threads = 0
    
    while completed_threads < len(threads):
        try:
            batch_id, sentences = result_queue.get(timeout=1)
            valid_rows.append((batch_id, sentences))
            completed_threads += 1
            with tqdm_lock:
                global_pbar.update(1)
        except queue.Empty:
            continue
    
    # Attendre que tous les threads se terminent
    for thread in threads:
        thread.join()
    
    with tqdm_lock:
        global_pbar.close()
    
    # Trier les résultats par ID de lot pour maintenir l'ordre
    valid_rows.sort(key=lambda x: x[0])
    flattened_rows = []
    for _, batch_sentences in valid_rows:
        flattened_rows.extend(batch_sentences)
    
    # Réécrire le fichier avec les lignes valides
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        for row in flattened_rows:
            writer.writerow(['', row[1]])
    
    print(f"\nPost-traitement terminé. {len(flattened_rows)} phrases conservées sur {total_rows} phrases initiales ({(len(flattened_rows)/total_rows)*100:.2f}%).")
    print(f"Fichier nettoyé: {output_file}")
    
    return len(flattened_rows)

def write_to_csv(sentences, output_file):
    """Écrit les phrases extraites dans un fichier CSV."""
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["phrase_steno", "phrase_fr"])
        writer.writerows(sentences)
        
    print(f"Fichier CSV créé avec succès: {output_file}")
    print(f"Nombre total de phrases extraites: {len(sentences)}")

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
    
    # Déterminer le nombre optimal de workers (processeurs/threads à utiliser)
    num_workers = multiprocessing.cpu_count()
    print(f"Nombre de processeurs disponibles: {num_workers}")
    
    # Extraire les phrases avec multithreading
    print("Démarrage de l'extraction des phrases avec multithreading...")
    sentences = extract_text_from_xml_multithreaded(file_path, num_workers=num_workers)
    
    # Écrire dans un fichier CSV
    output_file = 'data/wikipedia_output/wikipedia_phrases_nopost.csv'
    write_to_csv(sentences, output_file)
    
    # Effectuer un post-traitement pour éliminer les lignes problématiques avec multithreading
    print("Démarrage du post-traitement multithreadé pour éliminer les lignes problématiques...")
    final_output = 'data/wikipedia_output/wikipedia_phrases.csv'
    post_process_csv_multithreaded(output_file, final_output, num_workers=num_workers)
    
    # Valider le jeu de données final
    validate_final_dataset(final_output)
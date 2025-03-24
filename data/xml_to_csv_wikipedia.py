import xml.etree.ElementTree as ET
import csv
import re
from tqdm import tqdm
import nltk
import os

# Alternative avec une valeur fixe
csv.field_size_limit(10000000)  # 10 millions de caractères

# Télécharger les ressources NLTK pour la tokenisation des phrases
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
from nltk.tokenize import sent_tokenize

def count_elements(file_path, target_element='page'):
    """Compte le nombre total d'éléments d'un type spécifique dans le fichier XML."""
    count = 0
    for _, elem in ET.iterparse(file_path, events=('end',)):
        if elem.tag.endswith(target_element):
            count += 1
        elem.clear()
    return count

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

def extract_text_from_xml(file_path):
    """
    Extrait le texte de chaque page de l'XML de Wikipedia en utilisant iterparse
    pour économiser de la mémoire.
    """
    # Compter d'abord le nombre de pages pour initialiser tqdm
    print("Comptage du nombre de pages...")
    total_pages = count_elements(file_path)
    print(f"Nombre total de pages: {total_pages}")
    
    # Initialiser la barre de progression
    pbar = tqdm(total=total_pages, desc="Extraction des pages", unit="page")
    
    # Initialiser une liste pour stocker les phrases extraites
    all_sentences = []
    
    # Parcourir le fichier XML avec iterparse
    context = ET.iterparse(file_path, events=('end',))
    
    sentence_id = 0
    
    for event, elem in context:
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
            
            # Ignorer les pages de catégorie, portail, etc.
            if title and any(prefix in title for prefix in ["Catégorie:", "Category:", "Portail:", "Portal:", "Modèle:", "Template:", "Aide:", "Help:"]):
                elem.clear()
                pbar.update(1)
                continue
                
            if text:
                # Nettoyer le texte
                cleaned_text = clean_text(text)
                
                # Ignorer les pages vides après nettoyage
                if cleaned_text:
                    # Tokeniser le texte en phrases
                    try:
                        sentences = sent_tokenize(cleaned_text, language='french')
                        
                        # Filtrer les phrases
                        filtered_sentences = []
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
                        
                        # Ajouter les phrases avec ID
                        for sentence in filtered_sentences:
                            sentence_id += 1
                            all_sentences.append(['',sentence])
                    
                    except Exception as e:
                        print(f"Erreur lors de la tokenisation de la page '{title}': {e}")
            
            # Mettre à jour la barre de progression
            pbar.update(1)
            
            # Vider l'élément pour libérer la mémoire
            elem.clear()
    
    pbar.close()
    return all_sentences

def write_to_csv(sentences, output_file):
    """Écrit les phrases extraites dans un fichier CSV."""
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["phrase_steno","phrase_fr"])
        writer.writerows(sentences)
        
    print(f"Fichier CSV créé avec succès: {output_file}")
    print(f"Nombre total de phrases extraites: {len(sentences)}")

def post_process_csv(input_file, output_file):
    """Effectue un post-traitement du CSV pour éliminer les lignes problématiques."""
    rows_to_keep = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        # Garder l'en-tête
        header = next(reader)
        rows_to_keep.append(header)
        
        # Utiliser tqdm pour suivre la progression
        print("Post-traitement du fichier CSV...")
        total_rows = sum(1 for _ in open(input_file, 'r', encoding='utf-8')) - 1  # Soustraire l'en-tête
        pbar = tqdm(total=total_rows, desc="Filtrage des phrases")
        
        for row in reader:
            pbar.update(1)
            phrase = row[1]
            
            # Supprimer les guillemets qui entourent toute la phrase
            if phrase.startswith('"') and phrase.endswith('"'):
                phrase = phrase[1:-1]
            
            # Vérifier tous les critères encore une fois pour être sûr
            if is_valid_sentence(phrase):
                rows_to_keep.append(row)
        
        pbar.close()
    
    # Réécrire le fichier avec les ID réindexés
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        for i, row in enumerate(rows_to_keep[1:], 1):  # Commencer à 1 pour sauter l'en-tête
            writer.writerow(['', row[1]])
    
    total_kept = len(rows_to_keep) - 1  # Soustraire l'en-tête
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
    
    # Extraire les phrases
    print("Démarrage de l'extraction des phrases...")
    sentences = extract_text_from_xml(file_path)
    
    # Écrire dans un fichier CSV
    output_file = 'data/wikipedia_output/wikipedia_phrases_nopost.csv'
    write_to_csv(sentences, output_file)
    
    # Effectuer un post-traitement pour éliminer les lignes problématiques
    print("Démarrage du post-traitement pour éliminer les lignes problématiques...")
    final_output = 'data/wikipedia_output/wikipedia_phrases.csv'
    post_process_csv(output_file, final_output)
    
    # Valider le jeu de données final
    validate_final_dataset(final_output)
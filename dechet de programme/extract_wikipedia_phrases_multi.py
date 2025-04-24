import os
import csv
import re
import logging
import xml.etree.ElementTree as ET
from tqdm import tqdm
import nltk
import traceback
import multiprocessing
from functools import partial

# Ensure NLTK resources are downloaded
try:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
except Exception as e:
    logging.warning(f"NLTK download error: {e}")

from nltk.tokenize import sent_tokenize

# Configure larger CSV field size
csv.field_size_limit(10000000)  # 10 million characters

def count_elements(file_path, target_element='page'):
    """
    Count the total number of specific elements in the XML file.
    
    Args:
        file_path (str): Path to the XML file
        target_element (str, optional): XML element to count. Defaults to 'page'.
    
    Returns:
        int: Total count of specified elements
    """
    count = 0
    for _, elem in ET.iterparse(file_path, events=('end',)):
        if elem.tag.endswith(target_element):
            count += 1
        elem.clear()
    return count

def clean_text(text):
    """Thoroughly clean Wikipedia text by removing wiki markup, HTML, and non-textual elements."""
    if not text:
        return ""
    
    # Remove redirects
    if text.startswith('#REDIRECT') or text.startswith('#redirect'):
        return ""
    
    # Remove mathematical formulas and notations
    text = re.sub(r'\\lim_[^}]+}', '', text)
    text = re.sub(r'\\to', '', text)
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    text = re.sub(r'\$[^$]*\$', '', text)
    text = re.sub(r'\$\$[^$]*\$\$', '', text)
    text = re.sub(r'[\+\-\*\/\=\(\)\[\]\{\}\^\_\<\>\~\|]', ' ', text)
    
    # Remove category pages
    text = re.sub(r'Catégorie:.*?(\n|\Z)', '', text, flags=re.DOTALL)
    text = re.sub(r'Category:.*?(\n|\Z)', '', text, flags=re.DOTALL)
    
    # Remove wiki tables, templates, and XML/HTML tags
    text = re.sub(r'\{\|.*?\|\}', ' ', text, flags=re.DOTALL)
    text = re.sub(r'\{\{.*?\}\}', ' ', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Remove wiki references and links
    text = re.sub(r'\[\[[^\]]*\|([^\]]*)\]\]', r'\1', text)
    text = re.sub(r'\[\[([^\]]*)\]\]', r'\1', text)
    text = re.sub(r'\[https?://[^\s\]]+\s+([^\]]*)\]', r'\1', text)
    text = re.sub(r'\[https?://[^\s\]]+\]', '', text)
    
    # Remove wiki styles and formatting
    text = re.sub(r"'{2,}", '', text)
    text = re.sub(r'==+[^=]+=+=', ' ', text)
    text = re.sub(r'^\*+\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\#+\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\:+\s+', '', text, flags=re.MULTILINE)
    
    # Remove table rows and attributes
    text = re.sub(r'^\|.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^!.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\|-.*$', '', text, flags=re.MULTILINE)
    
    # Remove files and images
    text = re.sub(r'\[\[File:[^\]]*\]\]', '', text)
    text = re.sub(r'\[\[Image:[^\]]*\]\]', '', text)
    text = re.sub(r'\[\[Fichier:[^\]]*\]\]', '', text)
    text = re.sub(r'Image:.*?(?:\.jpg|\.png|\.gif)', '', text, flags=re.IGNORECASE)
    
    # Clean up remaining markup
    text = re.sub(r'(class|style|align|cellpadding|cellspacing|colspan|bgcolor|width|height)="[^"]*"', '', text)
    text = re.sub(r'small', '', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def has_balanced_structure(sentence):
    """Check if the sentence has a balanced structure (word/punctuation ratio)"""
    words = re.findall(r'\b\w+\b', sentence)
    punctuation_count = len(re.findall(r'[,;:]', sentence))
    
    if len(words) > 0 and punctuation_count > 0:
        ratio = len(words) / punctuation_count
        return ratio > 3  # At least 3 words for each punctuation mark
    
    return True  # If no punctuation, it's acceptable

def is_complete_sentence(sentence):
    """Detect if the sentence likely contains a subject and verb"""
    return re.search(r'\b[A-Za-zÀ-ÿ]+\b[\s\w]*\b(?:est|sont|était|étaient|a|ont|avait|avaient|(?:[a-zéèêëàâäôöîïù]+(?:e|es|ent|ons|ez|ait|aient)))\b', sentence) is not None

def is_valid_sentence(sentence):
    """Perform advanced validation on a sentence"""
    # Ignore very short sentences
    if len(sentence) < 15:
        return False
    
    # Ignore sentences with image, file references, or formatting hints
    if (re.search(r'Image:|File:|Fichier:', sentence, re.IGNORECASE) or
        re.search(r'\b(?:px|right|left)\b', sentence) or
        "small" in sentence or
        re.search(r'class=|style=|align=|colspan=', sentence) or
        sentence.startswith("Voir aussi")):
        return False
    
    # Ignore sentences with too many commas relative to words
    words = re.findall(r'\b\w+\b', sentence)
    if words:
        if sentence.count(',') > len(words) / 3:
            return False
    
    # Ignore lists of names or biographical entries
    if sentence.count(',') > 3 and sentence.count('.') < 2:
        if not re.search(r'\b(?:est|sont|était|étaient|a|ont|avait|avaient|sera|seront)\b', sentence):
            return False
    
    # Ignore sentences with mathematical symbols or complex notations
    if any(symbol in sentence for symbol in ['lim', '\\to', '\\infty', '→', 'ℓ', '}}', '{{', 'px']):
        return False
    
    # Ignore entries that look like dictionary/encyclopedia headings without a full sentence
    if (re.match(r'^[A-Z][a-z]+\s*:', sentence) or 
        re.match(r'^[A-Z][a-z]+\s+\(', sentence)):
        if not is_complete_sentence(sentence):
            return False
    
    # Ignore mathematical or programmatic notations
    if re.search(r'[_\^{}\\]', sentence):
        return False
    
    # Ensure the sentence contains a conjugated verb
    if not is_complete_sentence(sentence):
        return False
    
    # Ignore list-like enumerations
    if re.match(r'^[\w\s]+\s+\([^)]+\)(,\s+[\w\s]+\s+\([^)]+\))+', sentence):
        return False
    
    # Ensure the sentence ends with appropriate punctuation
    if not re.search(r'[.!?]$', sentence):
        return False
    
    # Limit the number of years/dates in a sentence
    if len(re.findall(r'\d{4}', sentence)) > 3:
        return False
    
    # Check for balanced sentence structure
    if not has_balanced_structure(sentence):
        return False
    
    return True

def process_page(page_data):
    """
    Process a single page from the XML dump.
    
    Args:
        page_data (tuple): A tuple containing page title and text
    
    Returns:
        list: Extracted valid sentences
    """
    title, text = page_data
    
    # Skip non-article pages
    if title and any(prefix in title for prefix in ["Catégorie:", "Category:", "Portail:", "Portal:", "Modèle:", "Template:", "Aide:", "Help:"]):
        return []
    
    # Extract text
    if text:
        cleaned_text = clean_text(text)
        
        if cleaned_text:
            try:
                sentences = sent_tokenize(cleaned_text, language='french')
                
                filtered_sentences = []
                for s in sentences:
                    s = s.strip()
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
                        re.search(r'[.!?]$', s) and
                        is_complete_sentence(s)):
                        
                        if is_valid_sentence(s):
                            filtered_sentences.append(s)
                
                return filtered_sentences
            
            except Exception as e:
                logging.error(f"Tokenization error for page '{title}': {e}")
                return []
    
    return []

def extract_pages_from_xml(file_path):
    """
    Extract pages from a Wikipedia XML dump.
    
    Args:
        file_path (str): Path to the XML file
    
    Returns:
        list: List of page tuples (title, text)
    """
    pages = []
    context = ET.iterparse(file_path, events=('end',))
    
    try:
        for event, elem in context:
            if elem.tag.endswith('page'):
                # Find the title and text
                title = None
                text = None
                
                for child in elem:
                    if child.tag.endswith('title'):
                        title = child.text
                    elif child.tag.endswith('revision'):
                        for rev_child in child:
                            if rev_child.tag.endswith('text'):
                                text = rev_child.text
                
                if title and text:
                    pages.append((title, text))
                
                # Clear memory
                elem.clear()
    
    except Exception as e:
        logging.error(f"Unexpected error during page extraction: {e}")
        logging.error(traceback.format_exc())
    
    return pages

def extract_text_from_xml(file_path, num_workers=None):
    """
    Extract sentences using multiprocessing.
    
    Args:
        file_path (str): Path to the XML file
        num_workers (int, optional): Number of workers to use. Defaults to number of CPU cores.
    
    Returns:
        list: Extracted sentences
    """
    if num_workers is None:
        num_workers = multiprocessing.cpu_count()
    
    # Extract pages
    pages = extract_pages_from_xml(file_path)
    logging.info(f"Total pages to process: {len(pages)}")
    
    # Use multiprocessing to extract sentences
    with multiprocessing.Pool(processes=num_workers) as pool:
        # Progress tracking with tqdm
        sentences = list(tqdm(
            pool.imap(process_page, pages),
            total=len(pages),
            desc="Extracting sentences",
            unit="page"
        ))
    
    # Flatten the list of sentences and add IDs
    all_sentences = []
    sentence_id = 0
    for page_sentences in sentences:
        for sentence in page_sentences:
            sentence_id += 1
            all_sentences.append(['', sentence])
    
    logging.info(f"Extraction complete. Total sentences: {len(all_sentences)}")
    return all_sentences

def write_to_csv(sentences, output_file):
    """
    Write extracted sentences to a CSV file.
    
    Args:
        sentences (list): List of sentences to write
        output_file (str): Path to output CSV file
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["phrase_steno", "phrase_fr"])
            writer.writerows(sentences)
        
        logging.info(f"CSV file created: {output_file}")
        logging.info(f"Total sentences extracted: {len(sentences)}")
    
    except Exception as e:
        logging.error(f"Error writing CSV: {e}")
        raise

def post_process_csv(input_file, output_file):
    """
    Post-process the CSV to remove problematic lines using multiprocessing.
    
    Args:
        input_file (str): Input CSV file path
        output_file (str): Output processed CSV file path
    """
    rows_to_keep = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows_to_keep.append(header)
        
        print("Post-processing CSV file...")
        rows = list(reader)
        total_rows = len(rows)
        
        # Multiprocessing setup
        num_workers = multiprocessing.cpu_count()
        with multiprocessing.Pool(processes=num_workers) as pool:
            valid_rows = list(tqdm(
                pool.imap(is_valid_sentence, [row[1] for row in rows]),
                total=total_rows,
                desc="Filtering sentences",
                unit="sentence"
            ))
        
        rows_kept = [row for row, is_valid in zip(rows, valid_rows) if is_valid]
        
    # Rewrite the file with reindexed IDs
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        for i, row in enumerate(rows_kept, 1):
            writer.writerow(['', row[1]])
    
    total_kept = len(rows_kept)
    print(f"Post-processing complete. {total_kept} sentences kept out of {total_rows} initial sentences ({(total_kept/total_rows)*100:.2f}%).")
    print(f"Cleaned file: {output_file}")

def validate_final_dataset(file_path):
    """
    Validate the quality of the final dataset by displaying statistics.
    
    Args:
        file_path (str): Path to the final CSV file
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        rows = list(reader)

    print(f"Total number of sentences in the final dataset: {len(rows)}")
    
    # Optional: Sample a few sentences to verify quality
    if len(rows) > 0:
        print("\nSample of extracted sentences:")
        for i in range(min(5, len(rows))):
            print(f"{i+1}. {rows[i][1]}")

def process_wikipedia_dump(input_file, output_file, num_workers=None):
    """
    Complete process for extracting sentences from a Wikipedia XML dump.
    
    Args:
        input_file (str): Path to input XML file
        output_file (str): Path to output CSV file
        num_workers (int, optional): Number of workers to use. Defaults to None (CPU count).
    
    Returns:
        dict: Processing results
    """
    try:
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("wikipedia_phrase_extraction.log"),
                logging.StreamHandler()
            ]
        )
        
        # Validate input file
        if not os.path.isfile(input_file):
            logging.error(f"Input file not found: {input_file}")
            return {
                'success': False,
                'error': f"Input file not found: {input_file}"
            }
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Extract sentences
        sentences = extract_text_from_xml(input_file, num_workers)
        
        # Intermediate CSV before post-processing
        intermediate_file = output_file.replace('.csv', '_nopost.csv')
        write_to_csv(sentences, intermediate_file)
        
        # Post-process the CSV
        write_to_csv(sentences, output_file)
        post_process_csv(intermediate_file, output_file)
        
        # Validate final dataset
        validate_final_dataset(output_file)
        
        return {
            'success': True,
            'total_sentences': len(sentences),
            'output_file': output_file
        }
    
    except Exception as e:
        logging.error(f"Error processing Wikipedia dump: {e}")
        logging.error(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    # Example usage
    input_file = 'data/wikipedia_output/frwiki-20250301-pages-articles1.xml-p1p306134'
    output_file = input_file.replace('.xml', "") + '.csv'
    
    result = process_wikipedia_dump(input_file, output_file)
    
    if result['success']:
        print(f"Successfully extracted {result['total_sentences']} sentences.")
        print(f"Output saved to: {result['output_file']}")
    else:
        print(f"Processing failed: {result.get('error', 'Unknown error')}")
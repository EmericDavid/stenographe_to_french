import xml.etree.ElementTree as ET
import csv
import re
import os
import multiprocessing as mp
from functools import lru_cache
import nltk
from nltk.tokenize import sent_tokenize
from tqdm import tqdm
import io

# Set CSV field size limit
csv.field_size_limit(10000000)  # 10 million characters

# Download NLTK resources for sentence tokenization
nltk.download('punkt', quiet=True)

# Compile regex patterns once for efficiency
REDIRECT_PATTERN = re.compile(r'#REDIRECT|#redirect')
MATH_FORMULA_PATTERN = re.compile(r'\\lim_[^}]+}|\\to|\\[a-zA-Z]+')
DOLLAR_FORMULA_PATTERN = re.compile(r'\$[^$]*\$|\$\$[^$]*\$\$')
MATH_SYMBOLS_PATTERN = re.compile(r'[\+\-\*\/\=\(\)\[\]\{\}\^\_\<\>\~\|]')
CATEGORY_PATTERN = re.compile(r'Catégorie:.*?(\n|\Z)|Category:.*?(\n|\Z)', re.DOTALL)
TABLE_PATTERN = re.compile(r'\{\|.*?\|\}', re.DOTALL)
TEMPLATE_PATTERN = re.compile(r'\{\{.*?\}\}', re.DOTALL)
HTML_TAG_PATTERN = re.compile(r'<[^>]+>')
WIKI_LINK_WITH_TEXT_PATTERN = re.compile(r'\[\[[^\]]*\|([^\]]*)\]\]')
WIKI_LINK_PATTERN = re.compile(r'\[\[([^\]]*)\]\]')
EXTERNAL_LINK_WITH_TEXT_PATTERN = re.compile(r'\[https?://[^\s\]]+\s+([^\]]*)\]')
EXTERNAL_LINK_PATTERN = re.compile(r'\[https?://[^\s\]]+\]')
WIKI_STYLE_PATTERN = re.compile(r"'{2,}")
SECTION_PATTERN = re.compile(r'==+[^=]+=+=')
LIST_PATTERN = re.compile(r'^\*+\s+|^\#+\s+|^\:+\s+', re.MULTILINE)
TABLE_LINE_PATTERN = re.compile(r'^\|.*$|^!.*$|^\|-.*$', re.MULTILINE)
FILE_IMAGE_PATTERN = re.compile(r'\[\[File:[^\]]*\]\]|\[\[Image:[^\]]*\]\]|\[\[Fichier:[^\]]*\]\]')
IMAGE_PATTERN = re.compile(r'Image:.*?(?:\.jpg|\.png|\.gif)', re.IGNORECASE)
HTML_ATTR_PATTERN = re.compile(r'(class|style|align|cellpadding|cellspacing|colspan|bgcolor|width|height)="[^"]*"')
MULTIPLE_SPACES_PATTERN = re.compile(r'\s+')

# Sentence validation patterns
COMPLETE_SENTENCE_PATTERN = re.compile(r'\b[A-Za-zÀ-ÿ]+\b[\s\w]*\b(?:est|sont|était|étaient|a|ont|avait|avaient|(?:[a-zéèêëàâäôöîïù]+(?:e|es|ent|ons|ez|ait|aient)))\b')
PUNCTUATION_END_PATTERN = re.compile(r'[.!?]$')
IMAGE_FILE_PATTERN = re.compile(r'Image:|File:|Fichier:', re.IGNORECASE)
FORMAT_RESIDUE_PATTERN = re.compile(r'\b(?:px|right|left)\b')
WORD_PATTERN = re.compile(r'\b\w+\b')
YEAR_PATTERN = re.compile(r'\(\d{4}\s*[-–]\s*\d{4}\)')
MATH_RESIDUE_PATTERN = re.compile(r'[_\^{}\\]')
ENUMERATION_PATTERN = re.compile(r'^[\w\s]+\s+\([^)]+\)(,\s+[\w\s]+\s+\([^)]+\))+')
YEAR_DIGIT_PATTERN = re.compile(r'\d{4}')


@lru_cache(maxsize=1024)
def clean_text(text):
    """Cleans text by removing wiki tags, HTML, and other non-textual elements with optimized regex."""
    if not text:
        return ""
        
    # Remove redirections
    if REDIRECT_PATTERN.search(text):
        return ""
    
    # Apply regex replacements in a single pass through the text
    # This reduces the number of times we iterate through the string
    text = MATH_FORMULA_PATTERN.sub('', text)
    text = DOLLAR_FORMULA_PATTERN.sub('', text)
    text = MATH_SYMBOLS_PATTERN.sub(' ', text)
    text = CATEGORY_PATTERN.sub('', text)
    text = TABLE_PATTERN.sub(' ', text)
    text = TEMPLATE_PATTERN.sub(' ', text)
    text = HTML_TAG_PATTERN.sub(' ', text)
    
    # Remove wiki links and external links
    text = WIKI_LINK_WITH_TEXT_PATTERN.sub(r'\1', text)
    text = WIKI_LINK_PATTERN.sub(r'\1', text)
    text = EXTERNAL_LINK_WITH_TEXT_PATTERN.sub(r'\1', text)
    text = EXTERNAL_LINK_PATTERN.sub('', text)
    
    # Remove styles, sections, lists, tables, files, images
    text = WIKI_STYLE_PATTERN.sub('', text)
    text = SECTION_PATTERN.sub(' ', text)
    text = LIST_PATTERN.sub('', text)
    text = TABLE_LINE_PATTERN.sub('', text)
    text = FILE_IMAGE_PATTERN.sub('', text)
    text = IMAGE_PATTERN.sub('', text)
    text = HTML_ATTR_PATTERN.sub('', text)
    
    # Replace multiple spaces with a single space
    text = MULTIPLE_SPACES_PATTERN.sub(' ', text)
    
    return text.strip()


def is_valid_sentence(sentence):
    """Checks if a sentence is valid using optimized criteria and cached regex patterns."""
    # Quick length check
    if len(sentence) < 15:
        return False
    
    # Check for image/file tags and formatting residues
    if IMAGE_FILE_PATTERN.search(sentence) or "small" in sentence or FORMAT_RESIDUE_PATTERN.search(sentence):
        return False
    
    # Check for common issues
    words = WORD_PATTERN.findall(sentence)
    word_count = len(words)
    if word_count == 0:
        return False
        
    comma_count = sentence.count(',')
    
    # Check for too many commas
    if comma_count > word_count / 3:
        return False
    
    # Check for lists of names with commas
    if comma_count > 3 and sentence.count('.') < 2:
        if not re.search(r'\b(?:est|sont|était|étaient|a|ont|avait|avaient|sera|seront)\b', sentence):
            return False
    
    # Check for "Voir aussi" references
    if sentence.startswith("Voir aussi"):
        return False
    
    # Check for dictionary/encyclopedia entries
    if re.match(r'^[A-Z][a-z]+\s*:', sentence) or re.match(r'^[A-Z][a-z]+\s+\(', sentence):
        if not COMPLETE_SENTENCE_PATTERN.search(sentence):
            return False
    
    # Check for biographical lists
    year_matches = YEAR_PATTERN.findall(sentence)
    if len(year_matches) > 1 and comma_count > 2:
        return False
    
    # Check for math symbols
    if any(symbol in sentence for symbol in ['lim', '\\to', '\\infty', '→', 'ℓ', '}}', '{{', 'px']):
        return False
        
    if MATH_RESIDUE_PATTERN.search(sentence):
        return False
    
    # Check for a conjugated verb
    if not COMPLETE_SENTENCE_PATTERN.search(sentence):
        return False
    
    # Check for enumerations
    if ENUMERATION_PATTERN.match(sentence):
        return False
    
    # Check for proper ending
    if not PUNCTUATION_END_PATTERN.search(sentence):
        return False
    
    # Check for too many numbers/dates
    if len(YEAR_DIGIT_PATTERN.findall(sentence)) > 3:
        return False
    
    # Check for balanced structure
    punctuation_count = len(re.findall(r'[,;:]', sentence))
    if punctuation_count > 0:
        ratio = word_count / punctuation_count
        if ratio <= 3:
            return False
    
    return True


def extract_pages_from_xml(xml_file, queue, chunk_size=5000):
    """Extract pages from XML in chunks and feed them to the processing queue."""
    # Initialize progress tracking variables
    total_pages = 0
    batch = []
    
    # Create progress bar without total (we don't know how many pages in advance)
    with tqdm(desc="Reading XML pages", unit="pages") as pbar:
        # Use ElementTree's iterparse to process the file incrementally
        for event, elem in ET.iterparse(xml_file, events=('end',)):
            if elem.tag.endswith('page'):
                # Extract title and text
                title = None
                text = None
                
                for child in elem:
                    if child.tag.endswith('title'):
                        title = child.text
                    elif child.tag.endswith('revision'):
                        for rev_child in child:
                            if rev_child.tag.endswith('text'):
                                text = rev_child.text
                
                # Skip pages without text or with irrelevant titles
                if text and title and not any(prefix in title for prefix in 
                                         ["Catégorie:", "Category:", "Portail:", "Portal:", 
                                          "Modèle:", "Template:", "Aide:", "Help:"]):
                    batch.append((title, text))
                    total_pages += 1
                    
                    # When batch is full, put it in queue and create a new batch
                    if len(batch) >= chunk_size:
                        queue.put(batch)
                        batch = []
                        pbar.update(chunk_size)
                
                # Free memory
                elem.clear()
        
        # Add remaining pages
        if batch:
            queue.put(batch)
            pbar.update(len(batch))
    
    # Signal the end of pages
    queue.put(None)
    print(f"Total pages extracted: {total_pages}")


def process_page_batch(queue, result_queue, process_id):
    """Process a batch of pages and extract valid sentences."""
    total_processed = 0
    total_sentences = 0
    
    # Create a progress bar for this process
    with tqdm(desc=f"Process {process_id}", unit="pages", position=process_id) as pbar:
        while True:
            batch = queue.get()
            if batch is None:
                # Signal that this process is done
                result_queue.put(None)
                break
                
            valid_sentences = []
            
            for title, text in batch:
                # Clean the text
                cleaned_text = clean_text(text)
                
                if cleaned_text:
                    try:
                        # Tokenize into sentences
                        sentences = sent_tokenize(cleaned_text, language='french')
                        
                        # Filter valid sentences
                        for sentence in sentences:
                            sentence = sentence.strip()
                            if is_valid_sentence(sentence):
                                valid_sentences.append(sentence)
                                total_sentences += 1
                                
                    except Exception as e:
                        pass  # Skip problematic pages
                
                total_processed += 1
            
            # Update progress
            pbar.update(len(batch))
            
            # Send valid sentences to result queue
            if valid_sentences:
                result_queue.put(valid_sentences)
    
    print(f"Process {process_id} completed: processed {total_processed} pages, found {total_sentences} valid sentences")


def write_results(result_queue, output_file, num_processes):
    """Collect results from processes and write to CSV file."""
    completed = 0
    total_sentences = 0
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["phrase_steno", "phrase_fr"])
        
        with tqdm(desc="Writing results", unit="sentences") as pbar:
            while completed < num_processes:
                result = result_queue.get()
                if result is None:
                    completed += 1
                else:
                    # Write sentences to file
                    for sentence in result:
                        writer.writerow(['', sentence])
                        total_sentences += 1
                    pbar.update(len(result))
    
    print(f"Extraction complete. {total_sentences} sentences extracted.")
    return total_sentences


def main():
    # Input file path
    file_path = 'data/wikipedia_output/frwiki-20250301-pages-articles3.xml-p2550823p2977214'
    
    # Check if file exists
    if not os.path.isfile(file_path):
        print(f"Error: File {file_path} doesn't exist.")
        return
    
    # Create output directory if needed
    os.makedirs('data/wikipedia_output', exist_ok=True)
    
    # Determine number of cores to use
    num_processes = mp.cpu_count()
    print(f"Using {num_processes} processes for extraction")
    
    # Create queues for communication
    page_queue = mp.Queue(maxsize=100)  # Limit queue size to control memory usage
    result_queue = mp.Queue()
    
    # Start reader process
    reader = mp.Process(target=extract_pages_from_xml, args=(file_path, page_queue))
    reader.start()
    
    # Start worker processes
    processes = []
    for i in range(num_processes):
        p = mp.Process(target=process_page_batch, args=(page_queue, result_queue, i))
        processes.append(p)
        p.start()
    
    # Start writer process and wait for completion
    output_file = 'data/wikipedia_output/wikipedia_phrases_optimized.csv'
    total_sentences = write_results(result_queue, output_file, num_processes)
    
    # Wait for all processes to complete
    reader.join()
    for p in processes:
        p.join()
    
    print(f"All processes completed. Total sentences extracted: {total_sentences}")
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    main()
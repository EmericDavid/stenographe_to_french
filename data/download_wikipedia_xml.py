# data/download_wikipedia_xml.py
import os
import requests
import bz2
import xml.etree.ElementTree as ET
from tqdm import tqdm
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("wikipedia_download.log"),
                        logging.StreamHandler()
                    ])

def download_file(url, output_dir='data/wikipedia_output'):
    """
    Download a file from a given URL with progress tracking
    
    Args:
        url (str): URL of the file to download
        output_dir (str): Directory to save the downloaded file
    
    Returns:
        str: Path to the downloaded file
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract filename from URL
    filename = os.path.join(output_dir, url.split('/')[-1])
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            chunk_size = 8192
            
            logging.info(f"Downloading {url} to {filename}")
            
            with open(filename, 'wb') as f:
                progress_bar = tqdm(
                    r.iter_content(chunk_size=chunk_size), 
                    total=total_size // chunk_size, 
                    unit='KB', 
                    desc=f"Downloading {os.path.basename(filename)}"
                )
                for chunk in progress_bar:
                    f.write(chunk)
        
        logging.info(f"Successfully downloaded {filename}")
        return filename
    except Exception as e:
        logging.error(f"Error downloading {url}: {e}")
        logging.error(traceback.format_exc())
        raise

def decompress_file(filename, ram_available_gb=4):
    """
    Decompress a .bz2 file with memory-efficient chunking
    
    Args:
        filename (str): Path to the .bz2 file
        ram_available_gb (int): Amount of RAM to use for decompression
    
    Returns:
        str: Path to the decompressed file
    """
    decompressed_filename = filename.replace(".bz2", "")
    
    try:
        # Taille des chunks pour la lecture du fichier compressé (plus petite pour mises à jour plus fréquentes)
        chunk_size = 1024 * 1024  # 1 MB
        
        total_size = os.path.getsize(filename)
        bytes_read = 0
        
        with bz2.BZ2File(filename, "rb") as f_in, open(decompressed_filename, "wb") as f_out:
            with tqdm(total=total_size, unit="B", unit_scale=True, 
                      desc=f"Decompressing {os.path.basename(filename)}") as pbar:
                
                while True:
                    # Position actuelle dans le fichier compressé
                    current_position = f_in.tell()
                    
                    # Lire un chunk
                    chunk = f_in.read(chunk_size)
                    if not chunk:
                        break
                        
                    # Écrire le chunk décompressé
                    f_out.write(chunk)
                    
                    # Calculer combien d'octets compressés ont été lus
                    new_position = f_in.tell()
                    bytes_read_chunk = new_position - current_position
                    
                    # Mettre à jour la barre de progression avec les octets compressés lus
                    pbar.update(bytes_read_chunk)
        
        logging.info(f"Successfully decompressed {filename}")
        return decompressed_filename
    except Exception as e:
        logging.error(f"Error decompressing {filename}: {e}")
        logging.error(traceback.format_exc())
        raise

def verify_file(filename):
    """
    Verify the XML structure of the decompressed file
    
    Args:
        filename (str): Path to the XML file
    
    Returns:
        bool: True if file is valid, False otherwise
    """
    try:
        context = ET.iterparse(filename, events=("start","end"))
        context = iter(context)
        _, root = next(context)

        logging.info(f"Verifying XML structure of {filename}")
        
        for event, elem in context:
            if event == 'end' and elem.tag.endswith('page'):
                logging.info('First page found!')
                elem.clear()
                break
        
        logging.info(f'XML structure of {filename} is valid')
        return True
    except Exception as e:
        logging.error(f"Error verifying {filename}: {e}")
        logging.error(traceback.format_exc())
        return False

def process_url(url, output_dir='data/wikipedia_output', ram_available_gb=4):
    """
    Complete process for a single URL: download, decompress, and verify
    
    Args:
        url (str): URL of the Wikipedia dump
        output_dir (str): Directory to save files
        ram_available_gb (int): RAM to use for decompression
    
    Returns:
        dict: Processing results
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract filename from URL
        filename = os.path.join(output_dir, url.split('/')[-1])
        
        # Skip if already downloaded and decompressed
        if os.path.exists(filename) and os.path.exists(filename.replace(".bz2", "")):
            logging.info(f"File {filename} already exists. Skipping download.")
            verify_result = verify_file(filename.replace(".bz2", ""))
            return {
                'url': url,
                'filepath': filename.replace(".bz2", ""),
                'downloaded': False,
                'decompressed': True,
                'verified': verify_result
            }
        
        # Download file
        downloaded_file = download_file(url, output_dir)
        
        # Decompress file
        decompressed_file = decompress_file(downloaded_file, ram_available_gb)
        
        # Verify file
        verified = verify_file(decompressed_file)
        
        return {
            'url': url,
            'filepath': decompressed_file,
            'downloaded': True,
            'decompressed': True,
            'verified': verified
        }
    
    except Exception as e:
        logging.error(f"Error processing {url}: {e}")
        logging.error(traceback.format_exc())
        return {
            'url': url,
            'downloaded': False,
            'decompressed': False,
            'verified': False,
            'error': str(e)
        }
    
if __name__ == "__main__":
    # Example usage
    urls = [
        "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles1.xml-p1p306134.bz2",
        #"https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles2.xml-p306135p1050822.bz2",
        #"https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles3.xml-p1050823p2550822.bz2"
    ]
    
    for url in urls:
        result = process_url(url)
        logging.info(f"Processing result: {result}")
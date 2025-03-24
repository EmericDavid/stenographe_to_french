import requests
import os
from tqdm import tqdm
import bz2
import xml.etree.ElementTree as ET

url = 'https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles.xml.bz2'
filename = "data/wikipedia_output/frwiki-20250301-pages-articles.xml.bz2"
#url = "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles3.xml-p2550823p2977214.bz2"
#filename = "data/wikipedia_output/frwiki-20250301-pages-articles3.xml-p2550823p2977214.bz2"
decompressed_filename = filename.replace(".bz2", "")

def download_file(url):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        chunk_size = 8192
        with open(filename, 'wb') as f:
            for chunk in tqdm(r.iter_content(chunk_size=chunk_size), 
                              total=total_size // chunk_size, unit='KB'):
                f.write(chunk)
    return filename

def decompress_file(filename, decompressed_filename, ram_available_gb=2):
    # Convert GB to bytes (1 GB = 1024^3 bytes)
    ram_available_bytes = ram_available_gb * (1024 ** 3)
    
    # Use a portion of available RAM for the buffer (e.g., 80%)
    # This leaves some room for Python overhead and other operations
    chunk_size = int(ram_available_bytes * 0.8)
    
    with bz2.open(filename, "rb") as f_in, open(decompressed_filename, "wb") as f_out:
        total_size = os.path.getsize(filename)
        with tqdm(total=total_size, unit="B", unit_scale=True, desc="Decompressing") as pbar:
            for chunk in iter(lambda: f_in.read(chunk_size), b""):
                f_out.write(chunk)
                pbar.update(len(chunk))

    return decompressed_filename

def verify_file(filename):
    context = ET.iterparse(filename, events=("start","end"))
    context = iter(context)
    _, root = next(context)

    print("Vérification du fichier XML...")
    for event, elem in context:
        if event == 'end' and elem.tag.endswith('page'):
            print('Première page trouvée!')
            # Nettoyer la mémoire en supprimant l'élément après utilisation
            elem.clear()
            break
    
    print('Structure XML valide')
    
if not os.path.exists(filename) or not os.path.exists(filename.replace(".bz2", "")):
    download_file(url)
    decompress_file(filename, decompressed_filename, ram_available_gb=4)
    verify_file(decompressed_filename)
    print("Download complete")
else:
    print("File already downloaded and decompressed")
    verify_file(decompressed_filename)



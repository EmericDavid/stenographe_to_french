import requests
import os
from tqdm import tqdm
import bz2

url = 'https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles3.xml-p2550823p2977214.bz2'
filename = "data/frwiki-20250301-pages-articles3.xml-p2550823p2977214.bz2"

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

def decompress_file(filename):
    with bz2.open(filename, "rb") as f_in, open(filename.replace(".bz2", ""), "wb") as f_out:
        total_size = os.path.getsize(filename)
        chunk_size = 1024 * 1024
        with tqdm(total=total_size, unit="B", unit_scale=True, desc="Decompressing") as pbar:
            for chunk in iter(lambda: f_in.read(chunk_size), b""):
                f_out.write(chunk)
                pbar.update(len(chunk))

    return filename.replace(".bz2", "")

if not os.path.exists(filename):
    download_file(url)
    decompress_file(filename)
    print("Download complete")
else:
    #check if already decompressed
    if not os.path.exists(filename.replace(".bz2", "")):
        decompress_file(filename)
        print("Decompression complete")
    else:
        print("File already downloaded and decompressed")

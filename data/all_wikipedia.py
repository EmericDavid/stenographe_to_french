import download_wikipedia_xml
import xml_to_csv_wikipedia_old


urls = [
        #"https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles1.xml-p1p306134.bz2",
        #"https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles2.xml-p306135p1050822.bz2",
        "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles3.xml-p1050823p2550822.bz2"
    ]


for url in urls:
    result = download_wikipedia_xml.process_url(url)
    print(f"Processing result: {result}")

    # check if verified is True
    if not result['verified']:
        print(f'Error : {result["error"]}')
        exit(1)
    
    # {'url': 'https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles3.xml-p1050823p2550822.bz2', 'filepath': 'data/wikipedia_output\\frwiki-20250301-pages-articles3.xml-p1050823p2550822', 'downloaded': False, 'decompressed': True, 'verified': True}
    # get the filepath
    filepath = result['filepath'].replace("\\", "/")
    print(f"Filepath: {filepath}")





from tqdm import tqdm
import xml.etree.ElementTree as ET

file_path = 'data/frwiki-20250301-pages-articles3.xml-p2550823p2977214'
context = ET.iterparse(file_path, events=("start","end"))
context = iter(context)
_, root = next(context)

for event, elem in tqdm(context, desc="Parsing XML"):
    if event == 'end' and elem.tag == root.tag:
        print('Root tag:', root.tag)

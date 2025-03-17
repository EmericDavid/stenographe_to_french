import re

def get_data_from_file(path_file: str):
    """
    Parser les phonégrammes du fichier pour avoir les différents sténogrammes
    """
    steno_dict = {}
    mots = {}

    with open(path_file, 'r', encoding='utf-8') as file:
        for line in file:
            if line.strip("\n\r ") == '':
                continue
            line = re.sub(r"\{.\}", "", line)

            word, stenogrammes = line.split(' :: ')
            stenogrammes = stenogrammes.strip().split()

            tr = []
            for p in stenogrammes:
                if p not in steno_dict.keys():
                    steno_dict[p] = len(steno_dict)
                
                tr.append(steno_dict[p])
            
            mots[word] = tr
        
    return mots, steno_dict



if __name__ == "__main__":
    dico_mots, dico_phonemes = get_data_from_file('test.steno.txt')

    with open('dico_phonegraphes.txt', 'w', encoding='utf-8') as file:
        for key, value in dico_phonemes.items():
            file.write(f"{key} :: {value}\n")
    
    with open('test.steno.as_indices.txt', 'w', encoding='utf-8') as file:
        for key, value in dico_mots.items():
            value = ' '.join(map(str, value))
            file.write(f"{key} :: {value}\n")
    

def get_data_from_file(path_file: str):
    """
    Parser les phonégrammes du fichier pour avoir les différents sténogrammes
    """
    phonemes_dict = {}
    mots = {}

    with open(path_file, 'r', encoding='utf-8') as file:
        for line in file:
            if line.strip("\n\r ") == '':
                continue

            word, phonegrammes = line.split(' :: ')

            phonegrammes = phonegrammes.strip().split()

            tr = []
            for p in phonegrammes:
                if p not in phonemes_dict.keys():
                    phonemes_dict[p] = len(phonemes_dict)
                
                tr.append(phonemes_dict[p])

            
            mots[word] = tr
        
    return mots, phonemes_dict



if __name__ == "__main__":
    dico_mots, dico_phonemes = get_data_from_file('test.steno.txt')

    with open('dico_phonegraphes.txt', 'w', encoding='utf-8') as file:
        for key, value in dico_phonemes.items():
            file.write(f"{key} :: {value}\n")
    
    with open('test.steno.as_indices.txt', 'w', encoding='utf-8') as file:
        for key, value in dico_mots.items():
            value = ' '.join(map(str, value))
            file.write(f"{key} :: {value}\n")
    

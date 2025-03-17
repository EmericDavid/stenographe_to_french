def get_data_from_file(path_file: str):
    """
    Parser les phonégrammes du fichier pour avoir les différents sténogrammes
    """
    phonemes_dict = {}
    mots = {}

    with open(path_file, 'r', encoding='utf-8') as file:
        for line in file:
            if line.strip() == '':
                continue

            word, phonegrammes = line.split(' :: ')
            
            phonegrammes = phonegrammes.strip("\n\r").split(' ')

            tr = []
            for p in phonegrammes:
                if p not in phonemes_dict.keys():
                    phonemes_dict[p] = len(phonemes_dict)+1
                
                tr.append(phonemes_dict[p])
            
            mots[word] = tr
        
    return mots, phonemes_dict



if __name__ == "__main__":
    dico_mots, dico_phonemes = get_data_from_file('test.steno.txt')

    print(dico_phonemes)
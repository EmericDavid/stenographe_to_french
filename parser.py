def get_data_fron_file(path_file: str):
    """
    Parser les phonégrammes du fichier pour avoir les différents sténogrammes
    """
    phonemes_dict = {}
    mots = []

    with open(path_file, 'r', encoding='utf-8') as file:
        for line in file:
            if line.strip() == '':
                continue

            word, phonegrammes = line.split(' :: ')
            phonegrammes = phonegrammes.split(' ')

            tr = []
            for p in phonegrammes:
                if p not in phonemes_dict.keys():
                    phonemes_dict[p] = len(phonemes_dict)+1
                
                tr.append(phonemes_dict[p])
            
            mots.append((word, tr))
        
    return mots, phonemes_dict

a, b = get_data_fron_file('test.steno.txt')

print(b)
print(a)
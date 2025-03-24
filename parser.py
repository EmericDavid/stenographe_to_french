import re
import matplotlib.pyplot as plt
def count_unique_words(filepath):
    """
    Compte le nombre de mots différents dans le dataset.
    """
    unique_words = set()

    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()

        for line in lines:
            try:
                word, _ = line.strip().split(" :: ")
                unique_words.add(word.strip())
            except ValueError:
                continue  # Ignore les lignes mal formatées

    return len(unique_words)
def count_unique_stenograms(filepath):
    """
    Compte le nombre de sténogrammes uniques en fonction du nombre de lignes prises en compte.
    """
    unique_stenograms = set()
    stenogram_counts = []

    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()

        for i, line in enumerate(lines, start=1):
            # Extraire les sténogrammes de chaque ligne
            try:
                _, stenograms = line.strip().split(" :: ")
                stenograms_list = stenograms.split()
                unique_stenograms.update(stenograms_list)
            except ValueError:
                continue  # Ignore les lignes mal formatées

            # Ajouter le nombre unique actuel à la liste
            stenogram_counts.append(len(unique_stenograms))

    return stenogram_counts

def plot_stenogram_counts(stenogram_counts):
    """
    Trace un graphe du nombre de sténogrammes uniques en fonction du nombre de lignes.
    """
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(stenogram_counts) + 1), stenogram_counts, marker='o', label="Sténogrammes uniques")
    plt.title("Nombre de sténogrammes uniques en fonction des lignes prises en compte")
    plt.xlabel("Nombre de lignes prises en compte")
    plt.ylabel("Nombre de sténogrammes uniques")
    plt.grid(True)
    plt.legend()
    plt.show()
    
def parse_steno_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Regular expression to match steno entries
    pattern = re.compile(r'(.+?)\s*::\s*(.+)')
    matches = pattern.findall(content)
    
    steno_dict = {}
    steno_index = {}
    current_index = 0
    
    for match in matches:
        word, stenos = match
        word = word.strip()
        stenos = stenos.strip().split()
        
        indices = []
        for steno in stenos:
            if steno not in steno_index:
                steno_index[steno] = current_index
                current_index += 1
            indices.append(steno_index[steno])
        
        steno_dict[word] = indices
    
    return steno_dict, steno_index


if __name__ == "__main__":

    filepath = 'train.steno.txt'
    steno_dict, steno_index = parse_steno_file(filepath)
    
    # Write steno_dict to a file
    with open('word_to_steno_indices.txt', 'w', encoding='utf-8') as file:
        for word, indices in steno_dict.items():
            indices_str = ' '.join(map(str, indices))
            file.write(f"{word} :: {indices_str}\n")
    with open('steno_to_indices.txt', 'w', encoding='utf-8') as file:
        for steno, index in steno_index.items():
            file.write(f"{steno} :: {index}\n")
    

    filepaths = 'word_to_steno_indices.txt'

    # Calculer le nombre de sténogrammes uniques
    stenogram_counts = count_unique_stenograms(filepaths)

    # Tracer le graphe
    unique_word_count = count_unique_words(filepaths)
    print(f"Nombre de mots différents dans le dataset : {unique_word_count}")
    plot_stenogram_counts(stenogram_counts)

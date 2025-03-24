import csv
import matplotlib.pyplot as plt
import re

# Fonction pour calculer la fréquence des sténogrammes
def get_steno_freq(steno_phrases):
    steno_freq = {}
    
    for phrase in steno_phrases:
        phrase = re.sub(r'[,.;!?-]', '', phrase)  
        stenos = phrase.split()  
        for steno in stenos:
            if steno in steno_freq:
                steno_freq[steno] += 1
            else:
                steno_freq[steno] = 1
    
    return steno_freq

# Chemin du fichier CSV
input_csv = "translated_phrases.csv"

# Lire les phrases sténogrammes depuis le fichier CSV
steno_phrases = []
with open(input_csv, "r", encoding="utf-8") as file:
    reader = csv.reader(file, delimiter=';')
    next(reader)  
    for row in reader:
        steno_phrase = row[2]  
        if steno_phrase != "NULL":  
            steno_phrases.append(steno_phrase)

steno_freq = get_steno_freq(steno_phrases)
sorted_steno_freq = sorted(steno_freq.items(), key=lambda x: x[1], reverse=True)
top_50_steno = dict(sorted_steno_freq[:50])

# Générer l'histogramme
plt.figure(figsize=(20, 10))
plt.bar(top_50_steno.keys(), top_50_steno.values())
plt.xlabel("Sténogramme")
plt.ylabel("Fréquence")
plt.title("50 sténogrammes les plus fréquents")
plt.xticks(rotation=90)  
plt.tight_layout()
plt.show()


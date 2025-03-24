import unicodedata

# Fonction pour convertir les caractères décomposés en composés
def decomposed_to_composed(text):
    # Utilisation de unicodedata.normalize pour recomposer les caractères
    return unicodedata.normalize('NFC', text)

# Lire le contenu du fichier
with open('test.steno.txt', 'r', encoding='utf-8') as file:
    content = file.read()

# Convertir les accents décomposés en accent classiquespub
content_composed = decomposed_to_composed(content)

# Sauvegarder le texte modifié dans un nouveau fichier
with open('test.steno.txt', 'w', encoding='utf-8') as file:
    file.write(content_composed)

print("La conversion a été effectuée avec succès.")

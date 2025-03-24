from num2words import num2words
import re

# Compilation des expressions régulières
reg_intervalles = re.compile(r"\b[0-9]+-[0-9]+\b")  # Intervalles (ex : 39-45)
reg_ordinaux = re.compile(r"\b(1er|[0-9]+(?:ème|e))\b")  # Ordinaux (ex : 1er, 22ème)
reg_nombres = re.compile(r"\b[0-9]+\b")  # Nombres simples (ex : 1984, 12)

def convert_intervalles(match):
    """
    Convertit les intervalles numériques en lettres (ex : 39-45 -> 39 à 45).
    """
    return match.group().replace("-", " à ")

def convert_ordinaux(match):
    """
    Convertit les nombres ordinaux en lettres (ex : 1er -> premier, 22ème -> vingt-deuxième).
    """
    num = re.sub(r"[^0-9]", "", match.group())
    return num2words(num, lang='fr', to='ordinal')

def convert_nombres(match):
    """
    Convertit les nombres simples en lettres (ex : 1984 -> mille neuf cent quatre-vingt-quatre).
    """
    return num2words(match.group(), lang='fr')

def pre_traitement(phrase):
    """
    Applique les transformations nécessaires pour convertir les nombres en lettres.
    """
    # Appliquer les transformations dans un ordre logique
    phrase = reg_intervalles.sub(convert_intervalles, phrase)
    phrase = reg_ordinaux.sub(convert_ordinaux, phrase)
    phrase = reg_nombres.sub(convert_nombres, phrase)
    return phrase

if __name__ == "__main__":
    # Tests pour vérifier le fonctionnement
    test_phrases = [
        "Ce roman a été écrit en 1984 plus de 12 fois",
        "Nous avons perdu notre 22ème soldat aujourd'hui",
        "4 enfants ont trouvé un clown dans les égouts",
        "Jolan aime le nombre 28 j'crois",
        "Je sais pas quoi dire, 160 poules proutprout",
        "La guerre de 39-45",
        "La guerre 39-45"
    ]
    
    for phrase in test_phrases:
        print(pre_traitement(phrase))
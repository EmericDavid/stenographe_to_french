from datetime import datetime
from num2words import num2words
import re


def intervalles_en_lettres(phrase):
    re_it = r"[0-9]+-[0-9]+"
     
    def convert_match(match):
        it = match.group()
        it = re.sub("-", " à ", it)
        return it

    return re.sub(re_it, convert_match, phrase)


def ordinaux_en_lettres(phrase):
    re_ord = r"1er|[0-9]+ème|[0-9]+e"
     
    def convert_match(match):
        num = re.sub(r"[^0-9]", "", match.group())
        return num2words(num, lang='fr', to='ordinal')

    return re.sub(re_ord, convert_match, phrase)


def nombres_en_lettres(phrase):
    re_nombre = r"[0-9]+"
    
    def convert_match(match):
        num = match.group()
        
        return num2words(num, lang='fr')

    return re.sub(re_nombre, convert_match, phrase)


def pre_traitement(phrase):
    phrase = intervalles_en_lettres(phrase)
    phrase = ordinaux_en_lettres(phrase)
    phrase = nombres_en_lettres(phrase)
    return phrase


if __name__ == "__main__":

    test = [
        "Ce roman a été écrit en 1984 plus de 12 fois",
        "Nous avons perdu notre 22ème soldat aujourd'hui",
        "4 enfants ont trouvé un clown dans les égouts",
        "Jolan aime le nombre 28 j'crois",
        "Je sais pas quoi dire, 160 poules proutprout",
        "La guerre de 39-45",
        "La guerre 39-45"
        ]
    
    for n in test:
        print(pre_traitement(n))
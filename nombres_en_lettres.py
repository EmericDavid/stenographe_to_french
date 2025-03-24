from num2words import num2words
import re

# Compile regular expressions once
re_it = re.compile(r"[0-9]+-[0-9]+")
re_ord = re.compile(r"1er|[0-9]+ème|[0-9]+e")
re_nombre = re.compile(r"[0-9]+")

def intervalles_en_lettres(phrase):
    def convert_match(match):
        it = match.group()
        it = it.replace("-", " à ")
        return it

    return re_it.sub(convert_match, phrase)

def ordinaux_en_lettres(phrase):
    def convert_match(match):
        num = re.sub(r"[^0-9]", "", match.group())
        return num2words(num, lang='fr', to='ordinal')

    return re_ord.sub(convert_match, phrase)

def nombres_en_lettres(phrase):
    def convert_match(match):
        num = match.group()
        return num2words(num, lang='fr')

    return re_nombre.sub(convert_match, phrase)

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
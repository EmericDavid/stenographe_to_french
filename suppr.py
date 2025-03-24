#vide la colonne "phrase steno" du fichier csv sachant que le format est "id;phrase fr;phrase steno"
import csv
import sys

def remove_steno_column(input_csv, output_csv):
    with open(input_csv, "r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=';')
        with open(output_csv, "w", encoding="utf-8", newline='') as out_file:
            writer = csv.writer(out_file, delimiter=';')
            for row in reader:
                writer.writerow([row[0], row[1]],";")

if __name__ == "__main__":
    input_csv = "wikipedia_phrases_clean.csv"
    output_csv = "wikipedia_phrases_clean_no_steno.csv"
    remove_steno_column(input_csv, output_csv)
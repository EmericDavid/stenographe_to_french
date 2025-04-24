import pandas as pd
import os
from tqdm import tqdm

os.chdir(os.path.dirname(os.path.abspath(__file__)))

df_all = pd.DataFrame()

csv_files = [file for file in os.listdir("./wikipedia_server/") if file.endswith(".csv")]

for file in tqdm(csv_files, desc="Merging CSV files"):
    df = pd.read_csv(f"./wikipedia_server/{file}")
    df_all = pd.concat([df_all, df], ignore_index=True)

print(f"Nombre de lignes: {df_all.shape[0]}")

df_all.to_csv("./wikipedia_server/all.csv", index=False)
print("All files merged into all.csv")
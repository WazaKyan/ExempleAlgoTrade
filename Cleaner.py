import pandas as pd
import os

DATA_DIR = r"C:\Users\33750\OneDrive\Bureau\BackTesting\PLUTO\AKIRA\DATA\DATA_PARQUET"
TICKERS_FILE = r"C:\Users\33750\OneDrive\Bureau\BackTesting\PLUTO\AKIRA\DATA\sp500_tickers.txt"

def read_tickers_from_file():
    with open(TICKERS_FILE, 'r') as f:
        tickers = [line.strip() for line in f if line.strip()]
    return tickers

def check_and_delete_significant_changes(ticker):
    file_path = os.path.join(DATA_DIR, f"{ticker}.parquet")
    if not os.path.exists(file_path):
        return False
    
    df = pd.read_parquet(file_path)
    df['price change'] = df['Adj Close'].pct_change()
    erreur = df['price change'] > 0.4
    
    if erreur.any():
        os.remove(file_path)
        print(f"Fichier supprimé : {file_path}")
        return True
    return False

def update_tickers_file():
    tickers = read_tickers_from_file()
    tickers_to_keep = [ticker for ticker in tickers if os.path.exists(os.path.join(DATA_DIR, f"{ticker}.parquet"))]

    with open(TICKERS_FILE, 'w') as f:
        for ticker in tickers_to_keep:
            f.write(ticker + '\n')
    
    print("Fichier de tickers mis à jour.")

tickers = read_tickers_from_file()
concerned_tickers = []

for ticker in tickers:
    if check_and_delete_significant_changes(ticker):
        concerned_tickers.append(ticker)

# Tri des tickers concernés par ordre alphabétique
concerned_tickers.sort()

# Création d'un DataFrame à partir de la liste triée et écriture dans un fichier CSV
chemin_csv = r"C:\Users\33750\OneDrive\Bureau\BackTesting\Tickers_Concernes.csv"
pd.DataFrame(concerned_tickers, columns=['Ticker']).to_csv(chemin_csv, index=False)

# Mise à jour du fichier de tickers
update_tickers_file()

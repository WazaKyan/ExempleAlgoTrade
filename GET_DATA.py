import os
import pandas as pd
import yfinance as yf
from datetime import datetime


DATA_DIR = r"C:\Users\33750\OneDrive\Bureau\BackTesting\PLUTO\AKIRA\DATA\DATA_PARQUET"
TICKERS_FILE = r"C:\Users\33750\OneDrive\Bureau\BackTesting\PLUTO\AKIRA\DATA\sp500_tickers.txt"


def download_sp500_history():
    try:
        tables = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', header=[0,1])
        historical_table = tables[1]
        added = historical_table['Date'].join(historical_table[('Added', 'Ticker')].rename('Ticker')).dropna()
        added['Action'] = 'Added'
        removed = historical_table['Date'].join(historical_table[('Removed', 'Ticker')].rename('Ticker')).dropna()
        removed['Action'] = 'Removed'
        history = pd.concat([added, removed])
        history['Ticker'] = history['Ticker'].str.replace('.', '-')
        # Convertissez les dates du format complet au format YYYY-MM-DD
        history['Date'] = pd.to_datetime(history['Date']).dt.strftime('%Y-%m-%d')
        return history
    except Exception as e:
        print(f"Erreur lors de l'extraction des données historiques : {e}")
        return pd.DataFrame()


def get_active_periods(historical_df, ticker, default_start_date='2000-01-01'):
    ticker_history = historical_df[historical_df['Ticker'] == ticker]
    active_periods = []

    for _, row in ticker_history.iterrows():
        if row['Action'] == 'Added':
            start_date = row['Date']
        elif row['Action'] == 'Removed' and 'start_date' not in locals():
            # Si un ticker est retiré sans date d'ajout connue, utilisez la date de début par défaut
            start_date = default_start_date

        if 'start_date' in locals():
            removed_dates = ticker_history[(ticker_history['Date'] > start_date) & (ticker_history['Action'] == 'Removed')]['Date']
            end_date = removed_dates.min() if not removed_dates.empty else datetime.now().strftime('%Y-%m-%d')
            active_periods.append((start_date, end_date))
            del start_date  # Réinitialisez start_date pour le prochain cycle

    # Si aucune période active n'est trouvée pour le ticker, utilisez la période par défaut
    if not active_periods:
        print(f"Aucune période active trouvée pour {ticker}. Utilisation de la période par défaut.")
        default_end_date = datetime.now().strftime('%Y-%m-%d')
        active_periods.append((default_start_date, default_end_date))

    return active_periods


def update_tickers_with_historical_data(historical_df):
    # Étape 1 : Lire les tickers actuels du fichier
    current_tickers = read_sp500_tickers_from_file()
    
    # Étape 2 : Extraire les tickers du DataFrame historique
    historical_tickers = historical_df['Ticker'].unique().tolist()
    
    # Étape 3 : Fusionner les listes et éliminer les doublons
    combined_tickers = list(set(current_tickers + historical_tickers))
    
    # Étape 4 : Mettre à jour le fichier .txt avec la liste combinée
    save_sp500_tickers(combined_tickers)
    print(f"Le fichier {TICKERS_FILE} a été mis à jour avec les tickers historiques et actuels.")

# Assurez-vous que votre DataFrame historique 'sp500_history' est correctement défini avant d'appeler cette fonction
# update_tickers_with_historical_data(sp500_history)


def save_sp500_tickers(tickers):
    with open(TICKERS_FILE, 'w') as f:
        for ticker in tickers:
            f.write(ticker + '\n')



def download_sp500_tickers():
    try:
        table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
        tickers = table[0]['Symbol'].tolist()
        tickers = [ticker.replace('.', '-') for ticker in tickers]
        save_sp500_tickers(tickers)
        return tickers
    except Exception as e:
        print(f"Erreur lors du téléchargement de la liste des tickers : {e}")
        return []

def read_sp500_tickers_from_file():
    with open(TICKERS_FILE, 'r') as f:
        tickers = [line.strip() for line in f]
    return tickers

def download_ticker_data(historical_df, tickers, default_start_date='2000-01-01'):
    files_downloaded = 0  # Initialisez un compteur pour les fichiers téléchargés
    for ticker in tickers:
        print(f"Téléchargement des données pour : {ticker}")

        # Obtenez les périodes actives pour le ticker
        active_periods = get_active_periods(historical_df, ticker)

        for start_date, end_date in active_periods:
            print(f"Téléchargement des données de {start_date} à {end_date} pour {ticker}")
            try:
                data = yf.download(ticker, start=start_date, end=end_date)
                if data.empty:
                    print(f"Aucune donnée disponible pour {ticker} du {start_date} au {end_date}, aucun fichier créé.")
                    continue
                file_path = os.path.join(DATA_DIR, f'{ticker}.parquet')
                data.to_parquet(file_path)
                files_downloaded += 1  # Incrémentez le compteur après chaque téléchargement réussi
            except Exception as e:
                print(f"Erreur lors du téléchargement des données pour {ticker} du {start_date} au {end_date} : {e}")

    return files_downloaded  # Retournez le nombre de fichiers téléchargés


if __name__ == "__main__":
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    sp500_history = download_sp500_history()

    # Vérifiez si le fichier TICKERS_FILE existe, sinon créez-le
    if not os.path.exists(TICKERS_FILE):
        print(f"Le fichier {TICKERS_FILE} n'existe pas. Téléchargement des tickers S&P 500 actuels...")
        download_sp500_tickers()  # Cela va créer le fichier avec les tickers actuels

    update_tickers_with_historical_data(sp500_history)  # Assurez-vous que cette fonction est appelée

    tickers = read_sp500_tickers_from_file()
    
    # Récupérez le nombre de fichiers téléchargés
    files_downloaded = download_ticker_data(sp500_history, tickers)
    print(f"Nombre total de fichiers téléchargés : {files_downloaded}")


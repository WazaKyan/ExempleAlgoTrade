import pandas as pd
import matplotlib.pyplot as plt
import math
from tqdm import tqdm
import os
import argparse
print
# Désactivation des avertissements pour les affectations chaînées
pd.options.mode.chained_assignment = None  

# Chemin d'accès au fichier des tickers
TICKERS_FILE = r"C:\Users\33750\OneDrive\Bureau\BackTesting\PLUTO\AKIRA\DATA\sp500_tickers.txt"

# Parsez les arguments
parser = argparse.ArgumentParser()
parser.add_argument('--EMA_MOUV', type=int, default=184)
parser.add_argument('--window_SMA', type=int, default=23)
parser.add_argument('--TIME_TO_SELL', type=int, default=66)
parser.add_argument('--RSI_LOW_BUY', type=int, default=88)
parser.add_argument('--RSI_NO_BUY', type=int, default=3)
parser.add_argument('--RSI_HIGHT_SELL', type=int, default=65)
parser.add_argument('--StopLoss', type=int, default=303)
parser.add_argument('--COMMISSION', type=float, default=0.02)
parser.add_argument('--window_SMA_SHORT', type=int, default=2)
parser.add_argument('--EMA_MOUV_SHORT', type=int, default=63)
parser.add_argument('--RSI_HIGHT_SELL_SHORT', type=int, default=24)
parser.add_argument('--RSI_LOW_BUY_SHORT', type=int, default=79)
parser.add_argument('--TIME_TO_SELL_SHORT', type=int, default=46)
parser.add_argument('--RSI_NO_BUY_SHORT', type=int, default=56)
args = parser.parse_args()

#Meilleurs paramètres: EMA_MOUV=184, window_SMA=23, TIME_TO_SELL=66, RSI_LOW_BUY=88, RSI_NO_BUY=3, RSI_HIGHT_SELL=65, StopLoss=303, COMMISSION=0.02, window_SMA_SHORT=2, EMA_MOUV_SHORT=63, RSI_HIGHT_SELL_SHORT=24, RSI_LOW_BUY_SHORT=79, TIME_TO_SELL_SHORT=46, RSI_NO_BUY_SHORT=56
#Meilleur Total: 145117068.8437277
Capital_Initial = 1000000


# Lecture des tickers depuis le fichier local
def read_tickers_from_file():
    with open(TICKERS_FILE, 'r') as f:
        tickers = [line.strip() for line in f if line.strip()]
    return tickers

# Extraction et préparation des symboles boursiers
tickers = read_tickers_from_file()

capital_per_ticker = {ticker: Capital_Initial / len(tickers) for ticker in tickers}
# Chemin d'accès au dossier contenant les fichiers Parquet
DATA_DIR = r"C:\Users\33750\OneDrive\Bureau\BackTesting\PLUTO\AKIRA\DATA\DATA_PARQUET"

def RSIcalc(asset, capital_per_ticker, data_dir):
    file_path = f"{data_dir}\\{asset}.parquet"
    # Vérifier l'existence du fichier et charger les données
    if not os.path.exists(file_path):
        return pd.DataFrame()   
    df = pd.read_parquet(file_path)
    if df.empty:
        return pd.DataFrame()   
    # Calcul de la moyenne mobile sur 200 jours et des composantes du RSI
    df['MA200'] = df['Adj Close'].rolling(window=args.window_SMA).mean()
    df['MA200_SHORT'] = df['Adj Close'].rolling(window=args.window_SMA_SHORT).mean()
    df['price change'] = df['Adj Close'].pct_change()
    df['Upmove'] = df['price change'].clip(lower=0)
    df['Downmove'] = -df['price change'].clip(upper=0)
    df['avg Up'] = df['Upmove'].ewm(span=args.EMA_MOUV).mean()
    df['avg Up_SHORT'] = df['Upmove'].ewm(span=args.EMA_MOUV_SHORT).mean()
    df['avg Down'] = df['Downmove'].ewm(span=args.EMA_MOUV).mean()
    df['avg Down_SHORT'] = df['Downmove'].ewm(span=args.EMA_MOUV_SHORT).mean()
    df['RS'] = df['avg Up'] / df['avg Down']
    df['RS_SHORT'] = df['avg Up_SHORT'] / df['avg Down_SHORT']
    df['RSI'] = 100 - (100 / (1 + df['RS']))
    df['RSI_SHORT'] = 100 - (100 / (1 + df['RS_SHORT']))
    # Initialisation des colonnes pour les signaux d'achat et de vente à découvert
    df['Buy'] = False
    df['Short'] = False
    df['Shares'] = 0
    # Définition des conditions pour les signaux d'achat et de vente à découvert
    condition_buy = (df['Adj Close'] > df['MA200']) & (df['RSI'] > args.RSI_NO_BUY) & (df['RSI'] < args.RSI_LOW_BUY)
    condition_short = (df['Adj Close'] < df['MA200_SHORT']) & (df['RSI_SHORT'] > args.RSI_HIGHT_SELL_SHORT)
    # Application des conditions pour définir les signaux et le nombre d'actions
    df.loc[condition_buy, 'Buy'] = True
    df.loc[condition_short, 'Short'] = True
    df.loc[condition_buy | condition_short, 'Shares'] = (capital_per_ticker / df.loc[condition_buy | condition_short, 'Adj Close']).round().astype(int)
    # Nettoyage du DataFrame pour retirer les lignes sans signal d'achat ou de vente à découvert
    df = df[(df['Buy'] == True) | (df['Short'] == True)]
    return df


def getSignals(df):
    if df.empty:
        return [], [], [], [], [], []

    # Gestion des signaux d'achat
    df['Signal_Buy'] = df['Buy'].shift(1) != df['Buy']
    buy_signals = df[(df['Buy'] == True) & df['Signal_Buy']]
    Buying_dates = buy_signals.index.tolist()
    Shares_bought = buy_signals['Shares'].tolist()

    Selling_dates = []
    for buy_date in Buying_dates:
        sell_condition = (df.index > buy_date) & (df['RSI'] > args.RSI_HIGHT_SELL)
        sell_dates = df.index[sell_condition]
        if not sell_dates.empty:
            Selling_dates.append(sell_dates[0])
        else:
            sell_index = min(len(df.index) - 1, df.index.get_loc(buy_date) + args.TIME_TO_SELL)
            Selling_dates.append(df.index[sell_index])

    # Gestion des signaux de vente à découvert
    df['Signal_Short'] = df['Short'].shift(1) != df['Short']
    short_signals = df[(df['Short'] == True) & df['Signal_Short']]
    Shorting_dates = short_signals.index.tolist()
    Shares_shorted = short_signals['Shares'].tolist()

    Covering_dates = []
    for short_date in Shorting_dates:
        cover_condition = (df.index > short_date) & (df['RSI_SHORT'] < args.RSI_LOW_BUY_SHORT) & (df['RSI_SHORT'] > args.RSI_NO_BUY_SHORT)
        cover_dates = df.index[cover_condition]
        if not cover_dates.empty:
            Covering_dates.append(cover_dates[0])
        else:
            cover_index = min(len(df.index) - 1, df.index.get_loc(short_date) + args.TIME_TO_SELL_SHORT)
            Covering_dates.append(df.index[cover_index])

    return Buying_dates, Selling_dates, Shares_bought, Shorting_dates, Covering_dates, Shares_shorted


def plot_profit_distribution(profits):
    plt.figure(figsize=(10, 6))
    plt.hist(profits, bins=50, color='blue', edgecolor='black')
    plt.title('Distribution des Profits et Pertes')
    plt.xlabel('Profit par opération')
    plt.ylabel('Nombre d\'opérations')
    plt.axvline(x=0, color='red', linestyle='--')  # Ligne pour marquer le point d'équilibre
    plt.grid(True)
    plt.show()


def plot_capital_allocation(capital_per_ticker):
    
    #Fonction pour visualiser le capital alloué à chaque actif.
    # Tri du dictionnaire par capital alloué pour une meilleure visualisation
    sorted_capital = dict(sorted(capital_per_ticker.items(), key=lambda item: item[1], reverse=True))
    # Création des listes de tickers et de leur capital associé pour le tracé
    tickers = list(sorted_capital.keys())
    capital = list(sorted_capital.values())
    # Création du graphique en barres
    plt.figure(figsize=(10, 6))
    plt.bar(tickers, capital, color='skyblue')
    plt.xlabel('Tickers')
    plt.ylabel('Capital Alloué ($)')
    plt.title('Allocation du Capital par Actif')
    plt.xticks(rotation=90)  # Rotation des étiquettes sur l'axe des x pour une meilleure lisibilité
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()

def print_final_capital_allocation(capital_per_ticker):
    # Tri du dictionnaire par capital alloué pour une meilleure lisibilité
    sorted_capital = dict(sorted(capital_per_ticker.items(), key=lambda item: item[1], reverse=True))
    print("Capital Final Alloué par Actif:")
    for ticker, capital in sorted_capital.items():
        print(f"{ticker}: ${capital:.2f}")


# Processus principal
matrixsignal_long = []
matrixprofit_long = []
matrixsignal_short = []
matrixprofit_short = []

for ticker in tqdm(tickers, desc='Calculating indicators'):
    frame = RSIcalc(ticker, capital_per_ticker[ticker], DATA_DIR)
    buy, sell, shares_bought, short, cover, shares_shorted = getSignals(frame)
    
    # Gestion des profits pour les positions longues
    Profits_long = []
    for i in range(len(buy)):
        sell_price = frame.loc[sell[i]].Open
        profit_per_share = sell_price - frame.loc[buy[i]].Open
        total_profit = profit_per_share * shares_bought[i] - args.COMMISSION * sell_price * shares_bought[i]
        capital_per_ticker[ticker] += total_profit
        Profits_long.append(total_profit)
        capital_per_ticker[ticker] = max(capital_per_ticker[ticker], 0)

    # Assurer que le capital par ticker ne devient pas négatif
    
    # Gestion des profits pour les positions courtes
    Profits_short = []
    for i in range(len(short)):
        cover_price = frame.loc[cover[i]].Open
        profit_per_share = frame.loc[short[i]].Open - cover_price
        total_profit = profit_per_share * shares_shorted[i] - args.COMMISSION * cover_price * shares_shorted[i]
        capital_per_ticker[ticker] += total_profit
        Profits_short.append(total_profit)

    # Mise à jour des matrices de signaux et de profits
    matrixsignal_long.append(buy)
    matrixprofit_long.append(Profits_long)
    matrixsignal_short.append(short)
    matrixprofit_short.append(Profits_short)

    
    


# Rassembler tous les profits pour un total final
allprofit_long = [profit for sublist in matrixprofit_long for profit in sublist if not math.isnan(profit)]
allprofit_short = [profit for sublist in matrixprofit_short for profit in sublist if not math.isnan(profit)]
Total = sum(allprofit_long) + sum(allprofit_short)


# Vous pouvez décommenter ces lignes si vous souhaitez voir les graphiques et les allocations finales
plot_profit_distribution(allprofit_long)
plot_profit_distribution(allprofit_short)
plot_capital_allocation(capital_per_ticker)
print_final_capital_allocation(capital_per_ticker)

print(Total)

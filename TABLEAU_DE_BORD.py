import subprocess
from skopt import gp_minimize
from skopt.space import Integer, Categorical
from skopt.utils import use_named_args
from tqdm.auto import tqdm
import numpy as np
import csv


# Définir l'espace des paramètres
space = [
    Integer(1, 200, name='EMA_MOUV'),
    Integer(1, 130, name='window_SMA'),
    Integer(1, 200, name='TIME_TO_SELL'),
    Integer(1, 100, name='RSI_LOW_BUY'),
    Integer(1, 100, name='RSI_NO_BUY'),
    Integer(1, 100, name='RSI_HIGHT_SELL'),
    Integer(1, 500, name='StopLoss'),
    Categorical([0.02], name='COMMISSION'),
    Integer(1, 200, name='window_SMA_SHORT'),
    Integer(1, 200, name='EMA_MOUV_SHORT'),
    Integer(1, 100, name='RSI_HIGHT_SELL_SHORT'),
    Integer(1, 100, name='RSI_LOW_BUY_SHORT'),
    Integer(1, 200, name='TIME_TO_SELL_SHORT'),
    Integer(1, 100, name='RSI_NO_BUY_SHORT'),
]

import csv
import subprocess

def executer_rsi(params):
    try:
        # Construction de la liste des arguments pour subprocess
        args = ["python", "C:\\Users\\33750\\OneDrive\\Bureau\\BackTesting\\PLUTO\\AKIRA\\SCRIPT_RSI_SHORT_BUY.py"]
        # Extension de la liste des arguments avec les paramètres sous forme de paires '--param value'
        for var, val in params.items():
            args.extend([f'--{var}', str(val)])

        # Exécution du script RSI avec les paramètres fournis
        processus = subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        sortie = processus.stdout

        # Extraction du résultat final depuis la sortie standard
        total = float(sortie.strip().split("\n")[-1])
    except (subprocess.CalledProcessError, ValueError) as e:
        print(f"Erreur lors de l'exécution du script : {e}")
        total = -1  # Valeur par défaut en cas d'échec

    # Enregistrement des arguments et du résultat dans le fichier CSV spécifié
    chemin_csv = "C:\\Users\\33750\\OneDrive\\Bureau\\BackTesting\\Suivit.csv"
    with open(chemin_csv, mode='a', newline='') as fichier:
        ecrivain_csv = csv.writer(fichier)
        # Conversion des paramètres en une liste pour l'enregistrement dans le CSV
        params_liste = [f"{var}={val}" for var, val in params.items()]
        ecrivain_csv.writerow(params_liste + [total])

    return -total  # Retourner la négation du total si nécessaire pour une minimisation


@use_named_args(space)
def objective(**params):
    result = executer_rsi(params)
    pbar.update(1)
    return result

def main():
    global pbar
    n_calls = 50
    pbar = tqdm(total=n_calls, desc="Optimisation progress")

    resultat = gp_minimize(objective, space, n_calls=n_calls, random_state=0)
    pbar.close()

    # Associer les noms des paramètres à leurs meilleures valeurs trouvées
    noms_parametres = [param.name for param in space]
    meilleures_valeurs = resultat.x
    parametres_et_valeurs = zip(noms_parametres, meilleures_valeurs)

    # Formatter les paramètres et leurs valeurs
    parametres_valeurs_str = ', '.join([f"{param}={val}" for param, val in parametres_et_valeurs])

    # Afficher les meilleurs paramètres et le meilleur score
    print(f"Meilleurs paramètres: {parametres_valeurs_str}")
    print(f"Meilleur Total: {-resultat.fun}")

if __name__ == "__main__":
    main()

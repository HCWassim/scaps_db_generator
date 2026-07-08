"""
merge_datasets.py

À utiliser à la place de merge_machines.py + un dataset_generator.py final :
chaque machine ayant déjà lancé SON PROPRE dataset_generator.py (sur ses CSV
IV/QE locaux), on récupère directement 40 fichiers dataset.csv de 40 960
lignes chacun et on les concatène. Beaucoup plus léger que de fusionner les
courbes brutes (286 720 lignes/machine) puis de refaire la jointure une
seule fois côté machine centrale.

------------------------ A REALISER AVANT ------------------------
Pré-requis : sur chaque PC, après db_batch_generator_multimachine.py,
lancer le pipeline de traitement existant qui produit CSV_IV_PROCESSED_PATH,
puis dataset_generator.py (inchangés), en pointant leurs chemins de sortie
vers un dossier propre à la machine, ex: ./csv/machine_07/dataset.csv.

Rapatriez ensuite tous les dataset.csv des 40 PC dans un dossier commun :
    csv/machine_00/dataset.csv
    csv/machine_01/dataset.csv
    ...
    csv/machine_39/dataset.csv

Usage :
    python merge_datasets.py --root ./csv --out ./csv/dataset_final.csv
"""

import argparse
import glob
import os
import pandas as pd

SHARED_KEYS = ["Rs", "Rsh", "N_A", "N_t", "mu_h", "mu_n"]
EXPECTED_TOTAL_ROWS = 1_638_400
EXPECTED_ROWS_PER_MACHINE = 40_960


def merge(root: str, out_path: str):
    files = sorted(glob.glob(os.path.join(root, "machine_*", "dataset.csv")))
    if not files:
        raise FileNotFoundError(f"Aucun dataset.csv trouvé sous {root}/machine_*/")

    frames = []
    for f in files:
        df = pd.read_csv(f)
        n = len(df)
        flag = "" if n == EXPECTED_ROWS_PER_MACHINE else "  <-- INATTENDU"
        print(f"  {f} : {n} lignes{flag}")
        frames.append(df)

    merged = pd.concat(frames, ignore_index=True)

    # Vérification qu'aucune machine n'a recouvert une plage d'une autre
    n_before = len(merged)
    dupes = merged.duplicated(subset=SHARED_KEYS)
    n_dupes = int(dupes.sum())
    if n_dupes:
        print(f"[Warning] {n_dupes} combinaison(s) en double sur {SHARED_KEYS} "
              f"— vérifiez le découpage Rs/P0 entre machines (chevauchement possible).")
        merged = merged[~dupes]

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    merged.to_csv(out_path, index=False)

    print("\n=== Résumé ===")
    print(f"Fichiers fusionnés    : {len(files)} / 40")
    print(f"Lignes avant dédup    : {n_before}")
    print(f"Lignes finales        : {len(merged)}  (attendu : {EXPECTED_TOTAL_ROWS})")
    print(f"Colonnes              : {len(merged.columns)}")
    print(f"-> {out_path}")

    if len(files) != 40:
        print(f"[Warning] {40 - len(files)} machine(s) manquante(s) — dataset incomplet.")
    if len(merged) != EXPECTED_TOTAL_ROWS:
        print(f"[Warning] total final != {EXPECTED_TOTAL_ROWS} attendu.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="./csv",
                         help="dossier contenant machine_00/dataset.csv ... machine_39/dataset.csv")
    parser.add_argument("--out", default="./csv/dataset_final.csv")
    args = parser.parse_args()
    merge(args.root, args.out)
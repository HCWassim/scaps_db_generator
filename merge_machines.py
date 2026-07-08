"""
merge_machines.py

À exécuter UNE FOIS que vous avez rapatrié les dossiers csv/machine_00/ ...
csv/machine_39/ (chacun contenant iv.csv et qe.csv) depuis les 40 PC vers une
seule machine centrale.

Concatène tous les iv.csv entre eux et tous les qe.csv entre eux, en ne
gardant l'en-tête qu'une seule fois, puis écrit le résultat aux chemins
CSV_IV_PATH / CSV_QE_PATH attendus par dataset_generator.py.

Après ce script, relancez simplement votre dataset_generator.py existant
(inchangé) pour produire le dataset.csv final.

Usage :
    python merge_machines.py --root ./csv --out-iv ./csv/iv_final.csv --out-qe ./csv/qe_final.csv
"""

import argparse
import glob
import os
import pandas as pd


def merge_csvs(pattern: str, output_path: str) -> int:
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"[Warning] aucun fichier trouvé pour le motif : {pattern}")
        return 0

    frames = []
    total_rows = 0
    for f in files:
        try:
            df = pd.read_csv(f)
        except Exception as e:
            print(f"[Warning] impossible de lire {f} ({e}), fichier ignoré")
            continue
        frames.append(df)
        total_rows += len(df)
        print(f"  {f} : {len(df)} lignes")

    if not frames:
        print(f"[Warning] rien à fusionner pour {pattern}")
        return 0

    merged = pd.concat(frames, ignore_index=True)

    n_before = len(merged)
    merged = merged.drop_duplicates()
    n_after = len(merged)
    if n_before != n_after:
        print(f"  -> {n_before - n_after} doublon(s) supprimé(s) "
              f"(vérifiez qu'aucune machine n'a traité la même plage 2 fois)")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    merged.to_csv(output_path, index=False)
    print(f"-> {output_path} : {len(merged)} lignes écrites\n")
    return len(merged)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="./csv",
                         help="dossier contenant machine_00/, machine_01/, ... rapatriés des 40 PC")
    parser.add_argument("--out-iv", default="./csv/iv_final.csv")
    parser.add_argument("--out-qe", default="./csv/qe_final.csv")
    args = parser.parse_args()

    print("Fusion des fichiers IV...")
    n_iv = merge_csvs(os.path.join(args.root, "machine_*", "iv.csv"), args.out_iv)

    print("Fusion des fichiers QE...")
    n_qe = merge_csvs(os.path.join(args.root, "machine_*", "qe.csv"), args.out_qe)

    print("=== Résumé ===")
    print(f"Courbes IV fusionnées : {n_iv}  (attendu : 6 553 600)")
    print(f"Courbes QE fusionnées : {n_qe}  (attendu : 4 915 200)")
    print(f"Total                 : {n_iv + n_qe}  (attendu : 11 468 800)")
    print("\nPointez ensuite OUTPUT_CSV_IV_PATH / OUTPUT_CSV_QE_PATH de votre .env "
          "central vers ces deux fichiers avant de relancer dataset_generator.py.")
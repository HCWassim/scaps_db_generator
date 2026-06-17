from config import CSV_IV_PATH, CSV_QE_PATH
import pandas as pd

import numpy as np
from pathlib import Path
 
# Chemins 
OUTPUT_PATH  = Path("./csv/dataset.csv")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
 
# Colonnes utiles
I_COLS      = [f"I{i}"      for i in range(1, 86)]   # I1 … I85
QE_COLS     = [f"QE{i}"     for i in range(1, 62)]   # QE1 … QE61
IV_EXTRA    = ["Voc", "Jsc", "FF", "eta", "V_MPP", "J_MPP"]
SHARED_KEYS = ["N_A", "N_t", "mu_h"]
COND_COLS   = ["T", "intensity"]
ID_COL      = ["ID_def"]
 
# Colonnes à extraire de chaque fichier
IV_KEEP  = I_COLS  + IV_EXTRA + COND_COLS + ID_COL + SHARED_KEYS
QE_KEEP  = QE_COLS + COND_COLS + ID_COL + SHARED_KEYS
 
# Définition des cas 
CASES = {
    "A": {"T": 300, "intensity": 100},
    "B": {"T": 300, "intensity": 10},
    "C": {"T": 280, "intensity": 100},
    "D": {"T": 300, "intensity": 0},
}
CASES_WITH_QE = {"A", "B", "C"}   # D n'a pas de courbe QE
 
# Lecture 
print(f"Lecture de {CSV_IV_PATH} …")
iv_df = pd.read_csv(CSV_IV_PATH)
 
print(f"Lecture de {CSV_QE_PATH} …")
qe_df = pd.read_csv(CSV_QE_PATH)
 
# Nettoyage : assurer les bons types pour les clés de jointure et de filtre
for df in (iv_df, qe_df):
    df["N_A"]       = pd.to_numeric(df["N_A"],       errors="coerce")
    df["N_t"]       = pd.to_numeric(df["N_t"],       errors="coerce")
    df["mu_h"]      = pd.to_numeric(df["mu_h"],      errors="coerce")
    df["T"]         = pd.to_numeric(df["T"],         errors="coerce")
    df["intensity"] = pd.to_numeric(df["intensity"], errors="coerce")
 
print(f"  IV  : {len(iv_df)} lignes")
print(f"  QE  : {len(qe_df)} lignes")
 
# Récupérer les groupes de paramètres uniques
# On se base sur les paramètres présents dans iv_df (4 cas × N groupes)
param_groups = iv_df[SHARED_KEYS].drop_duplicates().reset_index(drop=True)
print(f"\n{len(param_groups)} groupe(s) de paramètres physiques détecté(s) :")
print(param_groups.to_string(index=False))
 
# Construction du dataset
all_rows = []
 
for _, params in param_groups.iterrows():
    mask_params_iv = (
        (iv_df["N_A"]  == params["N_A"]) &
        (iv_df["N_t"]  == params["N_t"]) &
        (iv_df["mu_h"] == params["mu_h"])
    )
    mask_params_qe = (
        (qe_df["N_A"]  == params["N_A"]) &
        (qe_df["N_t"]  == params["N_t"]) &
        (qe_df["mu_h"] == params["mu_h"])
    )
 
    row_dict = {}
    valid = True
 
    for case_name, cond in CASES.items():
        # Courbe IV
        mask_iv = mask_params_iv & (
            (iv_df["T"]         == cond["T"]) &
            (iv_df["intensity"] == cond["intensity"])
        )
        iv_rows = iv_df[mask_iv]
 
        if len(iv_rows) == 0:
            print(f"  ⚠  Cas {case_name} introuvable dans IV pour {params.to_dict()} — ligne ignorée")
            valid = False
            break
        if len(iv_rows) > 1:
            print(f"  ⚠  Cas {case_name} : {len(iv_rows)} lignes IV trouvées (première utilisée)")
 
        iv_row = iv_rows.iloc[0]
 
        # Colonnes I1…I85
        for col in I_COLS:
            row_dict[f"{case_name}_{col}"] = iv_row[col]
 
        # QE pour les cas A, B, C
        if case_name in CASES_WITH_QE:
            mask_qe = mask_params_qe & (
                (qe_df["T"]         == cond["T"]) &
                (qe_df["intensity"] == cond["intensity"])
            )
            qe_rows = qe_df[mask_qe]
 
            if len(qe_rows) == 0:
                print(f"  ⚠  Cas {case_name} introuvable dans QE pour {params.to_dict()} — ligne ignorée")
                valid = False
                break
            if len(qe_rows) > 1:
                print(f"  ⚠  Cas {case_name} : {len(qe_rows)} lignes QE trouvées (première utilisée)")
 
            qe_row = qe_rows.iloc[0]
            for col in QE_COLS:
                row_dict[f"{case_name}_{col}"] = qe_row[col]
 
        # Colonnes scalaires IV
        for col in IV_EXTRA:
            row_dict[f"{case_name}_{col}"] = iv_row[col]
 
        row_dict[f"{case_name}_T"]         = iv_row["T"]
        row_dict[f"{case_name}_intensity"] = iv_row["intensity"]
        row_dict[f"{case_name}_ID_def"]    = iv_row["ID_def"]
 
    if not valid:
        continue
 
    # Paramètres physiques partagés (une seule fois en fin de ligne)
    for col in SHARED_KEYS:
        row_dict[col] = params[col]
 
    all_rows.append(row_dict)
 
# Assemblage et export
if not all_rows:
    print("\nAucune ligne valide produite — vérifiez les fichiers sources.")
else:
    # Construire l'ordre exact des colonnes tel que spécifié
    ordered_cols = []
    for case_name, cond in CASES.items():
        for col in I_COLS:
            ordered_cols.append(f"{case_name}_{col}")
        if case_name in CASES_WITH_QE:
            for col in QE_COLS:
                ordered_cols.append(f"{case_name}_{col}")
        for col in IV_EXTRA:
            ordered_cols.append(f"{case_name}_{col}")
        ordered_cols += [
            f"{case_name}_T",
            f"{case_name}_intensity",
            f"{case_name}_ID_def",
        ]
    ordered_cols += SHARED_KEYS
 
    result_df = pd.DataFrame(all_rows, columns=ordered_cols)
    result_df.to_csv(OUTPUT_PATH, index=False)
 
    print(f"\nDataset généré : {OUTPUT_PATH}")
    print(f"   {len(result_df)} ligne(s), {len(result_df.columns)} colonnes")
    print(f"\nPremières colonnes : {list(result_df.columns[:10])}")
    print(f"Dernières colonnes : {list(result_df.columns[-5:])}")
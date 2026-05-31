# from config import CSV_IV_PATH, CSV_QE_PATH
# import pandas as pd
# import numpy as np
# from pathlib import Path
 
# # Chemins 
# OUTPUT_PATH  = Path("./csv/dataset.csv")
# OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
 
# # Colonnes utiles
# I_COLS      = [f"I{i}"      for i in range(1, 86)]   # I1 … I85
# QE_COLS     = [f"QE{i}"     for i in range(1, 62)]   # QE1 … QE61
# IV_EXTRA    = ["Voc", "Jsc", "FF", "eta", "V_MPP", "J_MPP"]
# SHARED_KEYS = ["N_A", "N_t", "mu_h"]
# COND_COLS   = ["T", "intensity"]
# ID_COL      = ["ID_def"]
 
# # Colonnes à extraire de chaque fichier
# IV_KEEP  = I_COLS  + IV_EXTRA + COND_COLS + ID_COL + SHARED_KEYS
# QE_KEEP  = QE_COLS + COND_COLS + ID_COL + SHARED_KEYS
 
# # Définition des cas 
# CASES = {
#     "A": {"T": 300, "intensity": 100},
#     "B": {"T": 300, "intensity": 10},
#     "C": {"T": 280, "intensity": 100},
#     "D": {"T": 300, "intensity": 0},
# }
# CASES_WITH_QE = {"A", "B", "C"}   # D n'a pas de courbe QE
 
# # Lecture 
# print(f"Lecture de {CSV_IV_PATH} …")
# iv_df = pd.read_csv(CSV_IV_PATH)
 
# print(f"Lecture de {CSV_QE_PATH} …")
# qe_df = pd.read_csv(CSV_QE_PATH)
 
# # Nettoyage : assurer les bons types pour les clés de jointure et de filtre
# for df in (iv_df, qe_df):
#     df["N_A"]       = pd.to_numeric(df["N_A"],       errors="coerce")
#     df["N_t"]       = pd.to_numeric(df["N_t"],       errors="coerce")
#     df["mu_h"]      = pd.to_numeric(df["mu_h"],      errors="coerce")
#     df["T"]         = pd.to_numeric(df["T"],         errors="coerce")
#     df["intensity"] = pd.to_numeric(df["intensity"], errors="coerce")
 
# print(f"  IV  : {len(iv_df)} lignes")
# print(f"  QE  : {len(qe_df)} lignes")
 
# all_params = iv_df[SHARED_KEYS]
# nb_initial = len(all_params)

# # Récupérer les groupes de paramètres uniques
# # On se base sur les paramètres présents dans iv_df (4 cas × N groupes)
# param_groups = iv_df[SHARED_KEYS].drop_duplicates().reset_index(drop=True)
# nb_unique = len(param_groups)

# nb_doublons_elimines = nb_initial - nb_unique

# print(f"\n[Étape 1 - Clés physiques]")
# print(f"  - Combinaisons totales lues : {nb_initial}")
# print(f"  - Groupes uniques conservés : {nb_unique}")
# print(f"  - Doublons supprimés        : {nb_doublons_elimines}")

# # print(f"\n{len(param_groups)} groupe(s) de paramètres physiques détecté(s) :")
# # print(param_groups.to_string(index=False))
 
# # Construction du dataset
# all_rows = []
 
# for _, params in param_groups.iterrows():
#     mask_params_iv = (
#         (iv_df["N_A"]  == params["N_A"]) &
#         (iv_df["N_t"]  == params["N_t"]) &
#         (iv_df["mu_h"] == params["mu_h"])
#     )
#     mask_params_qe = (
#         (qe_df["N_A"]  == params["N_A"]) &
#         (qe_df["N_t"]  == params["N_t"]) &
#         (qe_df["mu_h"] == params["mu_h"])
#     )
 
#     row_dict = {}
#     valid = True
 
#     for case_name, cond in CASES.items():
#         # Courbe IV
#         mask_iv = mask_params_iv & (
#             (iv_df["T"]         == cond["T"]) &
#             (iv_df["intensity"] == cond["intensity"])
#         )
#         iv_rows = iv_df[mask_iv]
 
#         if len(iv_rows) == 0:
#             print(f"  ⚠  Cas {case_name} introuvable dans IV pour {params.to_dict()} — ligne ignorée")
#             valid = False
#             break
#         if len(iv_rows) > 1:
#             pass
#             # print(f"  ⚠  Cas {case_name} : {len(iv_rows)} lignes IV trouvées (première utilisée)")
 
#         iv_row = iv_rows.iloc[0]
 
#         # Colonnes I1…I85
#         for col in I_COLS:
#             row_dict[f"{case_name}_{col}"] = iv_row[col]
 
#         # QE pour les cas A, B, C
#         if case_name in CASES_WITH_QE:
#             mask_qe = mask_params_qe & (
#                 (qe_df["T"]         == cond["T"]) &
#                 (qe_df["intensity"] == cond["intensity"])
#             )
#             qe_rows = qe_df[mask_qe]
 
#             if len(qe_rows) == 0:
#                 print(f"  ⚠  Cas {case_name} introuvable dans QE pour {params.to_dict()} — ligne ignorée")
#                 valid = False
#                 break
#             if len(qe_rows) > 1:
#                 pass
#                 # print(f"  ⚠  Cas {case_name} : {len(qe_rows)} lignes QE trouvées (première utilisée)")
 
#             qe_row = qe_rows.iloc[0]
#             for col in QE_COLS:
#                 row_dict[f"{case_name}_{col}"] = qe_row[col]
 
#         # Colonnes scalaires IV
#         for col in IV_EXTRA:
#             row_dict[f"{case_name}_{col}"] = iv_row[col]
 
#         row_dict[f"{case_name}_T"]         = iv_row["T"]
#         row_dict[f"{case_name}_intensity"] = iv_row["intensity"]
#         row_dict[f"{case_name}_ID_def"]    = iv_row["ID_def"]
 
#     if not valid:
#         continue
 
#     # Paramètres physiques partagés (une seule fois en fin de ligne)
#     for col in SHARED_KEYS:
#         row_dict[col] = params[col]
 
#     all_rows.append(row_dict)
 
# # Assemblage et export
# if not all_rows:
#     print("\nAucune ligne valide produite — vérifiez les fichiers sources.")
# else:
#     # Construire l'ordre exact des colonnes tel que spécifié
#     ordered_cols = []
#     for case_name, cond in CASES.items():
#         for col in I_COLS:
#             ordered_cols.append(f"{case_name}_{col}")
#         if case_name in CASES_WITH_QE:
#             for col in QE_COLS:
#                 ordered_cols.append(f"{case_name}_{col}")
#         for col in IV_EXTRA:
#             ordered_cols.append(f"{case_name}_{col}")
#         ordered_cols += [
#             f"{case_name}_T",
#             f"{case_name}_intensity",
#             f"{case_name}_ID_def",
#         ]
#     ordered_cols += SHARED_KEYS
 
#     result_df = pd.DataFrame(all_rows, columns=ordered_cols)
#     result_df.to_csv(OUTPUT_PATH, index=False)
 
#     print(f"\nDataset généré : {OUTPUT_PATH}")
#     print(f"   {len(result_df)} ligne(s), {len(result_df.columns)} colonnes")
#     print(f"\nPremières colonnes : {list(result_df.columns[:10])}")
#     print(f"Dernières colonnes : {list(result_df.columns[-5:])}")
 
"""
merge_iv_qe.py
--------------
Fusionne les courbes IV (iv_curve.csv) et les efficacités quantiques (qe_curve.csv)
en un seul fichier CSV structuré par groupe de paramètres (N_A, N_t, mu_h).

Pour chaque groupe, on crée 4 colonnes préfixées A, B, C, D selon :
  A : T=300, intensity=100
  B : T=300, intensity=10
  C : T=280, intensity=100
  D : T=300, intensity=0
"""

from pathlib import Path
import pandas as pd
import numpy as np
from config import CSV_IV_PATH, CSV_QE_PATH

# ── Chemins ──────────────────────────────────────────────────────────────────
OUTPUT_PATH  = Path("./csv/dataset.csv")

# ── Colonnes à conserver ──────────────────────────────────────────────────────
KEY_COLS   = ["N_A", "N_t", "mu_h"]                      # clés de regroupement
KEY_COLS_PLUS = ["N_A", "N_t", "mu_h", "T", "intensity"]
I_COLS     = [f"I{i}"  for i in range(1, 86)]            # I1 … I85
QE_COLS    = [f"QE{i}" for i in range(1, 62)]            # QE1 … QE61
SCALAR_IV  = ["Voc", "Jsc", "FF", "eta", "V_MPP", "J_MPP", "T", "intensity", "ID_def"]

# Définition des 4 cas (préfixe → filtre)
CASES = {
    "A": {"T": 300.0, "intensity": 100},
    "B": {"T": 300.0, "intensity": 10},
    "C": {"T": 280.0, "intensity": 100},
    "D": {"T": 300.0, "intensity": 0},
}

# Cas sans QE (intensity=0 → pas d'illumination)
CASES_NO_QE = {"D"}

# ── Lecture des données ───────────────────────────────────────────────────────
print("Lecture de iv_curve.csv …")
df_iv = pd.read_csv(CSV_IV_PATH)
print(f"  {len(df_iv)} lignes, {len(df_iv.columns)} colonnes")

print("Lecture de qe_curve.csv …")
df_qe = pd.read_csv(CSV_QE_PATH)
print(f"  {len(df_qe)} lignes, {len(df_qe.columns)} colonnes")

# ── Arrondi des clés pour éviter les écarts numériques ───────────────────────
for df in (df_iv, df_qe):
    df["T"] = df["T"].round(2)
    df["intensity"] = df["intensity"].round(6)

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_row(df: pd.DataFrame, key_vals: dict, case_filter: dict):
    """Retourne la première ligne correspondant aux clés + filtre de cas."""
    mask = pd.Series(True, index=df.index)
    for col, val in {**key_vals, **case_filter}.items():
        mask &= np.isclose(df[col].astype(float), float(val), rtol=1e-5, atol=1e-5)
    rows = df[mask]
    return rows.iloc[0] if not rows.empty else None

# ── Groupes uniques (N_A, N_t, mu_h) ─────────────────────────────────────────
groups_iv = df_iv[KEY_COLS].drop_duplicates()
groups_qe = df_qe[KEY_COLS].drop_duplicates()
groups = pd.merge(groups_iv, groups_qe, on=KEY_COLS).drop_duplicates().reset_index(drop=True)
print(f"\n{len(groups)} groupe(s) (N_A, N_t, mu_h) trouvé(s).")

# ── Ordre des colonnes de sortie ──────────────────────────────────────────────
output_cols = []
for prefix in CASES:
    output_cols += [f"{prefix}_{c}" for c in I_COLS]
    if prefix not in CASES_NO_QE:
        output_cols += [f"{prefix}_{c}" for c in QE_COLS]
    output_cols += [f"{prefix}_{c}" for c in SCALAR_IV]
output_cols += KEY_COLS

# ── Construction du dataset ───────────────────────────────────────────────────
rows_out = []
missing_report = []

for _, grp in groups.iterrows():
    key_vals = {col: grp[col] for col in KEY_COLS}
    row_dict = {}

    for prefix, case_filter in CASES.items():
        iv_row = get_row(df_iv, key_vals, case_filter)
        qe_row = get_row(df_qe, key_vals, case_filter) if prefix not in CASES_NO_QE else None

        if iv_row is None:
            missing_report.append(
                f"  ⚠  IV manquant  : {key_vals} | cas {prefix} {case_filter}"
            )
        if prefix not in CASES_NO_QE and qe_row is None:
            missing_report.append(
                f"  ⚠  QE manquant  : {key_vals} | cas {prefix} {case_filter}"
            )

        # Courants I1…I85
        for c in I_COLS:
            row_dict[f"{prefix}_{c}"] = iv_row[c] if iv_row is not None else np.nan

        # QE1…QE61 (sauf cas sans illumination)
        if prefix not in CASES_NO_QE:
            for c in QE_COLS:
                row_dict[f"{prefix}_{c}"] = qe_row[c] if qe_row is not None else np.nan

        # Scalaires IV
        for c in SCALAR_IV:
            row_dict[f"{prefix}_{c}"] = iv_row[c] if iv_row is not None else np.nan

    # Paramètres communs
    for c in KEY_COLS:
        row_dict[c] = grp[c]

    rows_out.append(row_dict)

if missing_report:
    print("\nAvertissements :")
    for m in missing_report:
        print(m)
else:
    print("Aucune donnée manquante détectée.")

df_out = pd.DataFrame(rows_out, columns=output_cols)
print(f"\nDataset final : {len(df_out)} lignes × {len(df_out.columns)} colonnes")

# ── Sauvegarde ────────────────────────────────────────────────────────────────
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
df_out.to_csv(OUTPUT_PATH, index=False)
print(f"Fichier sauvegardé → {OUTPUT_PATH}")
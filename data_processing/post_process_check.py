"""
Vérification de la robustesse du post-traitement des courbes IV.

3 vérifications :
  1. Superposition      : la courbe interpolée colle à la courbe tronquée d'origine
  2. Impact de Rs        : la courbe avec Rs diffère de la courbe sans Rs (mêmes
                            paramètres physiques), sur [0.5 V, 1.2 V]
  3. Sensibilité aux bornes de Rs : Rs=0.5 Ω vs Rs=10 Ω produisent des courbes
                            visiblement différentes sur [-0.5 V, 1.2 V]
"""

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

from pipeline.config import CSV_IV_NO_RS_RSH_PATH

RAW_PATH = './csv/iv_curve.csv'
PROCESSED_PATH = './csv/iv_curve_processed.csv'

V_LO_FULL, V_HI_FULL = -0.5, 1.2   # plage finale complète
V_LO_VERIF2, V_HI_VERIF2 = 0.5, 1.2  # plage imposée pour la vérif. 2

# Clé physique = tout sauf Rs (et les résultats dérivés Voc/Jsc/FF/eta/V_MPP/J_MPP)
PARAM_KEY = ['N_A', 'N_t', 'mu_h', 'intensity', 'T']

VCOLS = [f'V{i}' for i in range(1, 86)]
ICOLS = [f'I{i}' for i in range(1, 86)]


def truncate(V, I):
    """Même règle de troncature que le script de pré-traitement :
    on garde tout jusqu'au premier point strictement > 1.2 V (inclus)."""
    above = np.where(V > V_HI_FULL)[0]
    cutoff = above[0] if len(above) else len(V) - 1
    return V[:cutoff + 1], I[:cutoff + 1]


# ---------------------------------------------------------------------------
# Vérification 1 : Superposition (courbe interpolée vs courbe tronquée)
# ---------------------------------------------------------------------------
def verif1_superposition(raw_path=RAW_PATH, processed_path=PROCESSED_PATH,
                          rtol=1e-2, atol=1e-9):
    raw = pd.read_csv(raw_path)
    proc = pd.read_csv(processed_path)

    max_rel_err = 0.0
    failures = []

    for r in range(len(raw)):
        V = raw.loc[r, VCOLS].values.astype(float)
        I = raw.loc[r, ICOLS].values.astype(float)
        Vt, It = truncate(V, I)

        # interpolateur de référence (identique à celui du pré-traitement)
        f = PchipInterpolator(Vt, It)

        # on ne compare que sur le domaine couvert par la courbe tronquée
        Vp = proc.loc[r, VCOLS].values.astype(float)
        Ip = proc.loc[r, ICOLS].values.astype(float)
        mask = (Vp >= Vt.min()) & (Vp <= Vt.max())

        I_ref = f(Vp[mask])
        err = np.abs(I_ref - Ip[mask])
        rel_err = err / np.maximum(np.abs(I_ref), atol)

        if rel_err.max() > max_rel_err:
            max_rel_err = rel_err.max()
        if rel_err.max() > rtol:
            failures.append(r)

    ok = len(failures) == 0
    print(f"[Verif 1] erreur relative max observée : {max_rel_err:.2e} "
          f"(tolérance {rtol:.0e}) -> {'OK' if ok else 'ECHEC'}")
    if failures:
        print(f"  Lignes en échec : {failures[:10]}{'...' if len(failures) > 10 else ''}")
    return ok


# ---------------------------------------------------------------------------
# Vérification 2 : Impact de Rs (courbe avec Rs vs courbe sans Rs, [0.5,1.2] V)
# ---------------------------------------------------------------------------
def verif2_impact_rs(processed_path=PROCESSED_PATH,
                      no_rs_path=CSV_IV_NO_RS_RSH_PATH,
                      min_diff=1e-6):
    with_rs = pd.read_csv(processed_path)
    no_rs = pd.read_csv(no_rs_path)

    # cible commune de tension (sous-ensemble de la grille déjà interpolée)
    sample_V = with_rs.loc[0, VCOLS].values.astype(float)
    target = sample_V[(sample_V >= V_LO_VERIF2) & (sample_V <= V_HI_VERIF2)]

    results = []
    for _, row_wrs in with_rs.iterrows():
        # on cherche la courbe sans Rs avec les mêmes paramètres physiques
        match = no_rs
        for k in PARAM_KEY:
            if k in no_rs.columns:
                match = match[np.isclose(match[k], row_wrs[k])]
        if match.empty:
            continue
        ref = match.iloc[0]

        I_wrs = np.interp(target, row_wrs[VCOLS].values.astype(float),
                           row_wrs[ICOLS].values.astype(float))
        I_no_rs = np.interp(target, ref[VCOLS].values.astype(float),
                             ref[ICOLS].values.astype(float))

        max_abs_diff = np.abs(I_wrs - I_no_rs).max()
        results.append(max_abs_diff)

    if not results:
        print("[Verif 2] Aucune correspondance trouvée avec le fichier sans Rs "
              "(vérifier PARAM_KEY / colonnes communes).")
        return False

    results = np.array(results)
    ok = bool((results > min_diff).all())
    print(f"[Verif 2] écart max |I_avec_Rs - I_sans_Rs| sur [0.5,1.2] V : "
          f"min={results.min():.3e}, max={results.max():.3e} -> "
          f"{'OK (courbes distinctes)' if ok else 'ECHEC (courbes confondues)'}")
    return ok


# ---------------------------------------------------------------------------
# Vérification 3 : Sensibilité aux bornes de Rs (Rs=0.5 Ω vs Rs=10 Ω)
# ---------------------------------------------------------------------------
def verif3_sensibilite_rs(processed_path=PROCESSED_PATH,
                           rs_min=0.5, rs_max=10.0, min_diff=1e-6):
    df = pd.read_csv(processed_path)

    other_params = [k for k in PARAM_KEY if k in df.columns]
    groups = df.groupby(other_params)

    diffs = []
    for _, g in groups:
        row_min = g[np.isclose(g['Rs'], rs_min)]
        row_max = g[np.isclose(g['Rs'], rs_max)]
        if row_min.empty or row_max.empty:
            continue
        row_min, row_max = row_min.iloc[0], row_max.iloc[0]

        I_min = row_min[ICOLS].values.astype(float)
        I_max = row_max[ICOLS].values.astype(float)
        diffs.append(np.abs(I_min - I_max).max())

    if not diffs:
        print(f"[Verif 3] Aucune paire (Rs={rs_min}, Rs={rs_max}) trouvée pour "
              "les mêmes paramètres physiques.")
        return False

    diffs = np.array(diffs)
    ok = bool((diffs > min_diff).all())
    print(f"[Verif 3] écart max |I(Rs={rs_min}) - I(Rs={rs_max})| sur "
          f"[-0.5,1.2] V : min={diffs.min():.3e}, max={diffs.max():.3e} -> "
          f"{'OK (effet visible)' if ok else 'ECHEC (effet non détecté)'}")
    return ok


if __name__ == '__main__':
    print("=== Vérifications de robustesse du post-traitement IV ===\n")
    verif1_superposition()
    print()
    verif2_impact_rs()
    print()
    verif3_sensibilite_rs(rs_min=0.5, rs_max=10.0)
"""
machine_split.py

Découpage automatique de l'espace des paramètres SCAPS (Rs x P0 x P1 x P2 x P3)
pour répartition sur N machines physiques, sans Docker/K8s/multi-réseau :
chaque PC exécute ce module localement avec sa propre variable d'environnement
MACHINE_ID et ne travaille que sur SA portion de l'espace de paramètres.

Principe (adapté de vos fonctions split_interval / chunk_intervals déjà existantes) :

1) Répartition inter-machines (40 blocs) :
   - Rs   (10 steps) découpé en RS_SPLIT = 5 blocs de 2 steps  -> exact, aucun reste
   - P0   (16 steps) découpé en P0_SPLIT = 8 blocs de 2 steps  -> exact, aucun reste
   - RS_SPLIT * P0_SPLIT = 40 = N_MACHINES
   - P1, P2, P3 restent en intégralité sur CHAQUE machine.
   - machine_id (0..39)  ->  rs_idx, p0_idx = divmod(machine_id, P0_SPLIT)
   - combinaisons/machine = 2 * 2 * 16 * 8 * 8 = 4096  (= 163 840 / 40, exact)

2) Répartition intra-machine (sessions SCAPS) :
   - P1 (16 steps, laissé entier à l'étape 1) est ensuite découpé en
     P1_SESSION_SPLIT = 8 sessions de 2 steps -> exact, aucun reste.
   - combinaisons/session = 2(Rs) * 2(P0) * 2(P1) * 8(P2) * 8(P3) = 512
     -> dans la fourchette 200-1000 demandée, très en dessous du plafond 2000.
   - Une machine fait donc 8 sessions par entrée SETTINGS, soit
     40 (SETTINGS) * 8 (sessions) = 320 appels SCAPS batch au total.

Si vous changez un jour les STEPS dans config.py, relancez simplement
`python machine_split.py` : le script vérifie que la répartition reste
exacte et vous avertit sinon (voir print_plan()).
"""

from outil.interval import split_interval
from pipeline import config as cfg

# --- Paramètres de répartition (modifiables si vous changez le nb de machines) ---
RS_SPLIT = 5              # sous-blocs de Rs -> un par ligne de la grille machine
P0_SPLIT = 8              # sous-blocs de dopage -> une par colonne de la grille machine
P1_SESSION_SPLIT = 8      # sous-sessions de densité de défauts, à l'intérieur d'une machine

N_MACHINES = RS_SPLIT * P0_SPLIT  # 40


def combos_in(batch_parameters):
    """Nombre de combinaisons (= nombre de courbes IV) produites par un jeu de
    paramètres batch (liste de dicts issus de generate_batch_parameter)."""
    total = 1
    for p in batch_parameters:
        total *= p["steps"]
    return total


def get_machine_parameters(machine_id: int,
                            rs_split: int = RS_SPLIT,
                            p0_split: int = P0_SPLIT,
                            p1_session_split: int = P1_SESSION_SPLIT):
    """
    Retourne la liste des jeux de paramètres batch (sessions) qu'une machine
    donnée doit exécuter. Chaque élément de la liste retournée est un
    BATCH_PARAMETERS au même format que celui produit dans config.py
    (liste [RS, P0, P1, P2, P3]), prêt à être passé à run_batch().

    :param machine_id: identifiant de la machine, 0 <= machine_id < rs_split*p0_split
    """
    n_machines = rs_split * p0_split
    if not (0 <= machine_id < n_machines):
        raise ValueError(
            f"machine_id doit être compris entre 0 et {n_machines - 1} (reçu {machine_id})"
        )

    rs_blocs = split_interval(cfg.RS_FROM, cfg.RS_TO, cfg.RS_STEPS, rs_split)
    p0_blocs = split_interval(cfg.DOPAGE_FROM, cfg.DOPAGE_TO, cfg.DOPAGE_STEPS, p0_split)
    p1_blocs = split_interval(
        cfg.DEFAULT_DENSITY_VOLUME_FROM, cfg.DEFAULT_DENSITY_VOLUME_TO,
        cfg.DEFAULT_DENSITY_VOLUME_STEPS, p1_session_split
    )

    rs_idx, p0_idx = divmod(machine_id, p0_split)
    rs_bloc = rs_blocs[rs_idx]
    p0_bloc = p0_blocs[p0_idx]

    RS = cfg.generate_batch_parameter(
        cfg.RS_LABEL1, cfg.RS_LABEL2, cfg.RS_LABEL3, cfg.RS_LABEL4,
        rs_bloc["from"], rs_bloc["to"], rs_bloc["steps"]
    )
    P0 = cfg.generate_batch_parameter(
        cfg.P0_LABEL1, cfg.P0_LABEL2, cfg.P0_LABEL3, cfg.P0_LABEL4,
        p0_bloc["from"], p0_bloc["to"], p0_bloc["steps"]
    )
    # P2 et P3 restent entiers sur chaque machine
    P2 = cfg.generate_batch_parameter(
        cfg.P2_LABEL1, cfg.P2_LABEL2, cfg.P2_LABEL3, cfg.P2_LABEL4,
        cfg.HOLE_FROM, cfg.HOLE_TO, cfg.HOLE_STEPS
    )
    P3 = cfg.generate_batch_parameter(
        cfg.P3_LABEL1, cfg.P3_LABEL2, cfg.P3_LABEL3, cfg.P3_LABEL4,
        cfg.ELECTRON_FROM, cfg.ELECTRON_TO, cfg.ELECTRON_STEPS
    )

    sessions = []
    for p1_bloc in p1_blocs:
        P1 = cfg.generate_batch_parameter(
            cfg.P1_LABEL1, cfg.P1_LABEL2, cfg.P1_LABEL3, cfg.P1_LABEL4,
            p1_bloc["from"], p1_bloc["to"], p1_bloc["steps"]
        )
        sessions.append([RS, P0, P1, P2, P3])

    return sessions


def print_plan():
    """Affiche un résumé de la répartition sur les 40 machines pour vérification
    avant déploiement (aucune connexion SCAPS requise, calcul pur)."""
    n_settings = len(cfg.SETTINGS)
    n_light = sum(1 for _, intensity, _ in cfg.SETTINGS if intensity)
    n_dark = n_settings - n_light

    total_iv = total_qe = 0
    combos_par_machine = None

    for machine_id in range(N_MACHINES):
        sessions = get_machine_parameters(machine_id)
        combos_session = combos_in(sessions[0])
        combos_machine = combos_session * len(sessions)
        if combos_par_machine is None:
            combos_par_machine = combos_machine
        elif combos_machine != combos_par_machine:
            print(f"[Warning] machine {machine_id} déséquilibrée : "
                  f"{combos_machine} combos vs {combos_par_machine} ailleurs")

        iv_machine = combos_machine * n_settings
        qe_machine = combos_machine * n_light
        total_iv += iv_machine
        total_qe += qe_machine

    print(f"N_MACHINES            : {N_MACHINES} (RS_SPLIT={RS_SPLIT} x P0_SPLIT={P0_SPLIT})")
    print(f"Combinaisons/session  : {combos_session}")
    print(f"Sessions/machine      : {len(sessions)}  (P1_SESSION_SPLIT={P1_SESSION_SPLIT})")
    print(f"Combinaisons/machine  : {combos_machine}")
    print(f"Appels SCAPS/machine  : {len(sessions) * n_settings}  "
          f"({len(sessions)} sessions x {n_settings} entrées SETTINGS)")
    print(f"SETTINGS: {n_settings} entrées ({n_light} light -> IV+QE, {n_dark} dark -> IV seul)")
    print(f"Courbes IV/machine    : {combos_machine * n_settings}")
    print(f"Courbes QE/machine    : {combos_machine * n_light}")
    print(f"Courbes/machine (tot) : {combos_machine * n_settings + combos_machine * n_light}")
    print(f"---")
    print(f"TOTAL IV (40 machines): {total_iv}")
    print(f"TOTAL QE (40 machines): {total_qe}")
    print(f"TOTAL courbes         : {total_iv + total_qe}")


if __name__ == "__main__":
    print_plan()
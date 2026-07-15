# """
# machine_split.py

# Découpage automatique de l'espace des paramètres SCAPS (Rs x P0 x P1 x P2 x P3)
# pour répartition sur N machines physiques, sans Docker/K8s/multi-réseau :
# chaque PC exécute ce module localement avec sa propre variable d'environnement
# MACHINE_ID et ne travaille que sur SA portion de l'espace de paramètres.

# Principe (adapté de vos fonctions split_interval / chunk_intervals déjà existantes) :

# 1) Répartition inter-machines (40 blocs) :
#    - Rs   (10 steps) découpé en RS_SPLIT = 5 blocs de 2 steps  -> exact, aucun reste
#    - P0   (16 steps) découpé en P0_SPLIT = 8 blocs de 2 steps  -> exact, aucun reste
#    - RS_SPLIT * P0_SPLIT = 40 = N_MACHINES
#    - P1, P2, P3 restent en intégralité sur CHAQUE machine.
#    - machine_id (0..39)  ->  rs_idx, p0_idx = divmod(machine_id, P0_SPLIT)
#    - combinaisons/machine = 2 * 2 * 16 * 8 * 8 = 4096  (= 163 840 / 40, exact)

# 2) Répartition intra-machine (sessions SCAPS) :
#    - P1 (16 steps, laissé entier à l'étape 1) est ensuite découpé en
#      P1_SESSION_SPLIT = 8 sessions de 2 steps -> exact, aucun reste.
#    - combinaisons/session = 2(Rs) * 2(P0) * 2(P1) * 8(P2) * 8(P3) = 512
#      -> dans la fourchette 200-1000 demandée, très en dessous du plafond 2000.
#    - Une machine fait donc 8 sessions par entrée SETTINGS, soit
#      40 (SETTINGS) * 8 (sessions) = 320 appels SCAPS batch au total.

# Si vous changez un jour les STEPS dans config.py, relancez simplement
# `python machine_split.py` : le script vérifie que la répartition reste
# exacte et vous avertit sinon (voir print_plan()).
# """

# from outil.interval import split_interval
# from pipeline import config as cfg

# # --- Paramètres de répartition (modifiables si vous changez le nb de machines) ---
# RS_SPLIT = 5              # sous-blocs de Rs -> un par ligne de la grille machine
# P0_SPLIT = 8              # sous-blocs de dopage -> une par colonne de la grille machine
# P1_SESSION_SPLIT = 8      # sous-sessions de densité de défauts, à l'intérieur d'une machine

# N_MACHINES = RS_SPLIT * P0_SPLIT  # 40


# def combos_in(batch_parameters):
#     """Nombre de combinaisons (= nombre de courbes IV) produites par un jeu de
#     paramètres batch (liste de dicts issus de generate_batch_parameter)."""
#     total = 1
#     for p in batch_parameters:
#         total *= p["steps"]
#     return total


# def get_machine_parameters(machine_id: int,
#                             rs_split: int = RS_SPLIT,
#                             p0_split: int = P0_SPLIT,
#                             p1_session_split: int = P1_SESSION_SPLIT):
#     """
#     Retourne la liste des jeux de paramètres batch (sessions) qu'une machine
#     donnée doit exécuter. Chaque élément de la liste retournée est un
#     BATCH_PARAMETERS au même format que celui produit dans config.py
#     (liste [RS, P0, P1, P2, P3]), prêt à être passé à run_batch().

#     :param machine_id: identifiant de la machine, 0 <= machine_id < rs_split*p0_split
#     """
#     n_machines = rs_split * p0_split
#     if not (0 <= machine_id < n_machines):
#         raise ValueError(
#             f"machine_id doit être compris entre 0 et {n_machines - 1} (reçu {machine_id})"
#         )

#     rs_blocs = split_interval(cfg.RS_FROM, cfg.RS_TO, cfg.RS_STEPS, rs_split)
#     p0_blocs = split_interval(cfg.DOPAGE_FROM, cfg.DOPAGE_TO, cfg.DOPAGE_STEPS, p0_split)
#     p1_blocs = split_interval(
#         cfg.DEFAULT_DENSITY_VOLUME_FROM, cfg.DEFAULT_DENSITY_VOLUME_TO,
#         cfg.DEFAULT_DENSITY_VOLUME_STEPS, p1_session_split
#     )

#     rs_idx, p0_idx = divmod(machine_id, p0_split)
#     rs_bloc = rs_blocs[rs_idx]
#     p0_bloc = p0_blocs[p0_idx]

#     RS = cfg.generate_batch_parameter(
#         cfg.RS_LABEL1, cfg.RS_LABEL2, cfg.RS_LABEL3, cfg.RS_LABEL4,
#         rs_bloc["from"], rs_bloc["to"], rs_bloc["steps"]
#     )
#     P0 = cfg.generate_batch_parameter(
#         cfg.P0_LABEL1, cfg.P0_LABEL2, cfg.P0_LABEL3, cfg.P0_LABEL4,
#         p0_bloc["from"], p0_bloc["to"], p0_bloc["steps"]
#     )
#     # P2 et P3 restent entiers sur chaque machine
#     P2 = cfg.generate_batch_parameter(
#         cfg.P2_LABEL1, cfg.P2_LABEL2, cfg.P2_LABEL3, cfg.P2_LABEL4,
#         cfg.HOLE_FROM, cfg.HOLE_TO, cfg.HOLE_STEPS
#     )
#     P3 = cfg.generate_batch_parameter(
#         cfg.P3_LABEL1, cfg.P3_LABEL2, cfg.P3_LABEL3, cfg.P3_LABEL4,
#         cfg.ELECTRON_FROM, cfg.ELECTRON_TO, cfg.ELECTRON_STEPS
#     )

#     sessions = []
#     for p1_bloc in p1_blocs:
#         P1 = cfg.generate_batch_parameter(
#             cfg.P1_LABEL1, cfg.P1_LABEL2, cfg.P1_LABEL3, cfg.P1_LABEL4,
#             p1_bloc["from"], p1_bloc["to"], p1_bloc["steps"]
#         )
#         sessions.append([RS, P0, P1, P2, P3])

#     return sessions


# def print_plan():
#     """Affiche un résumé de la répartition sur les 40 machines pour vérification
#     avant déploiement (aucune connexion SCAPS requise, calcul pur)."""
#     n_settings = len(cfg.SETTINGS)
#     n_light = sum(1 for _, intensity, _ in cfg.SETTINGS if intensity)
#     n_dark = n_settings - n_light

#     total_iv = total_qe = 0
#     combos_par_machine = None

#     for machine_id in range(N_MACHINES):
#         sessions = get_machine_parameters(machine_id)
#         combos_session = combos_in(sessions[0])
#         combos_machine = combos_session * len(sessions)
#         if combos_par_machine is None:
#             combos_par_machine = combos_machine
#         elif combos_machine != combos_par_machine:
#             print(f"[Warning] machine {machine_id} déséquilibrée : "
#                   f"{combos_machine} combos vs {combos_par_machine} ailleurs")

#         iv_machine = combos_machine * n_settings
#         qe_machine = combos_machine * n_light
#         total_iv += iv_machine
#         total_qe += qe_machine

#     print(f"N_MACHINES            : {N_MACHINES} (RS_SPLIT={RS_SPLIT} x P0_SPLIT={P0_SPLIT})")
#     print(f"Combinaisons/session  : {combos_session}")
#     print(f"Sessions/machine      : {len(sessions)}  (P1_SESSION_SPLIT={P1_SESSION_SPLIT})")
#     print(f"Combinaisons/machine  : {combos_machine}")
#     print(f"Appels SCAPS/machine  : {len(sessions) * n_settings}  "
#           f"({len(sessions)} sessions x {n_settings} entrées SETTINGS)")
#     print(f"SETTINGS: {n_settings} entrées ({n_light} light -> IV+QE, {n_dark} dark -> IV seul)")
#     print(f"Courbes IV/machine    : {combos_machine * n_settings}")
#     print(f"Courbes QE/machine    : {combos_machine * n_light}")
#     print(f"Courbes/machine (tot) : {combos_machine * n_settings + combos_machine * n_light}")
#     print(f"---")
#     print(f"TOTAL IV (40 machines): {total_iv}")
#     print(f"TOTAL QE (40 machines): {total_qe}")
#     print(f"TOTAL courbes         : {total_iv + total_qe}")


# if __name__ == "__main__":
#     print_plan()

"""
machine_split.py (v2 — auto-adaptatif)

Contrairement à la v1 (RS_SPLIT=5, P0_SPLIT=8 codés en dur, qui ne
fonctionnaient QUE pour STEPS = 10/16/16/8/8), cette version recherche
automatiquement, à partir des STEPS actuels de config.py, le plus grand
nombre de machines <= N_MACHINES_TARGET atteignable par une division
PROPRE (sans reste) de l'espace Rs x P0 x P1 x P2 x P3.

Pourquoi une recherche automatique et pas un calcul en dur :
- Avec STEPS = 10,16,16,8,8 (v1)  -> 40 est atteignable exactement.
- Avec STEPS = 6,12,12,6,6 (v2)   -> 40 n'est PAS atteignable proprement
  (aucune de ces 5 valeurs n'a de diviseur commun avec 5, or 40 = 2^3 x 5).
  Le meilleur découpage propre est 36 machines à 864 combinaisons chacune.
- Si vous rechangez les STEPS demain, ce module recalcule automatiquement
  le meilleur découpage possible, au lieu de silencieusement planter ou
  produire un déséquilibre non détecté entre machines.

Politique adoptée pour les machines physiques "en trop" (ex: 4 PC sur 40
si le meilleur découpage propre est 36) : elles sont marquées SPARE et
n'ont rien à calculer par défaut (à utiliser en secours si une des 36
machines tombe en panne, ou pour relancer des sessions en échec). Voir
print_plan() pour le détail, et la docstring de get_machine_parameters()
pour l'option avancée qui les met à contribution.
"""

from itertools import product as iproduct

import numpy as np

from outil.interval import split_interval
from pipeline import config as cfg

N_MACHINES_TARGET = 40          # nombre de PC physiques disponibles
SESSION_MIN, SESSION_MAX = 200, 1000   # fourchette cible de combinaisons/appel SCAPS
SESSION_HARD_CAP = 2000

DIMENSIONS = ["RS", "P0", "P1", "P2", "P3", "P4"]


def _dim_specs():
    """Relit config.py à chaque appel (pas de cache) pour que ce module
    reste correct même si vous modifiez config.py sans relancer Python."""
    return {
        "RS": dict(from_val=cfg.RS_FROM, to_val=cfg.RS_TO, steps=cfg.RS_STEPS,
                   label1=cfg.RS_LABEL1, label2=cfg.RS_LABEL2, label3=cfg.RS_LABEL3,
                   label4=cfg.RS_LABEL4, log=cfg.RS_LOG),
        "P0": dict(from_val=cfg.DOPAGE_FROM, to_val=cfg.DOPAGE_TO, steps=cfg.DOPAGE_STEPS,
                   label1=cfg.P0_LABEL1, label2=cfg.P0_LABEL2, label3=cfg.P0_LABEL3,
                   label4=cfg.P0_LABEL4, log=cfg.P0_LOG),
        "P1": dict(from_val=cfg.DEFAULT_DENSITY_VOLUME_FROM, to_val=cfg.DEFAULT_DENSITY_VOLUME_TO,
                   steps=cfg.DEFAULT_DENSITY_VOLUME_STEPS,
                   label1=cfg.P1_LABEL1, label2=cfg.P1_LABEL2, label3=cfg.P1_LABEL3,
                   label4=cfg.P1_LABEL4, log=cfg.P1_LOG),
        "P2": dict(from_val=cfg.HOLE_FROM, to_val=cfg.HOLE_TO, steps=cfg.HOLE_STEPS,
                   label1=cfg.P2_LABEL1, label2=cfg.P2_LABEL2, label3=cfg.P2_LABEL3,
                   label4=cfg.P2_LABEL4, log=cfg.P2_LOG),
        "P3": dict(from_val=cfg.ELECTRON_FROM, to_val=cfg.ELECTRON_TO, steps=cfg.ELECTRON_STEPS,
                   label1=cfg.P3_LABEL1, label2=cfg.P3_LABEL2, label3=cfg.P3_LABEL3,
                   label4=cfg.P3_LABEL4, log=cfg.P3_LOG),
        "P4": dict(from_val=cfg.TOTAL_DEFECT_DENSITY_FROM, to_val=cfg.TOTAL_DEFECT_DENSITY_TO,
                   steps=cfg.TOTAL_DEFECT_DENSITY_STEPS,
                   label1=cfg.P4_LABEL1, label2=cfg.P4_LABEL2, label3=cfg.P4_LABEL3,
                   label4=cfg.P4_LABEL4, log=cfg.P4_LOG),
    }


def _clean_divisors(steps, max_n):
    """Diviseurs de `steps` qui sont <= max_n (= steps // 2, contrainte de
    split_interval : >= 2 steps par sous-intervalle). Un split par un
    diviseur propre garantit AUCUN reste (tous les blocs de taille égale)."""
    return [d for d in range(1, max_n + 1) if steps % d == 0]


def compute_split_plan(n_machines_target=N_MACHINES_TARGET):
    """
    Cherche, parmi toutes les combinaisons de divisions propres de chaque
    dimension, celle dont le produit (= nb de machines actives) est le plus
    grand possible sans dépasser n_machines_target.

    Retourne (split_counts, active_machines, spare_machines) où
    split_counts est un dict {dim: nb_de_blocs} (1 = dimension non divisée).
    """
    specs = _dim_specs()
    options = {d: _clean_divisors(specs[d]["steps"], specs[d]["steps"] // 2) for d in DIMENSIONS}

    best_product = 1
    best_combo = {d: 1 for d in DIMENSIONS}
    for combo in iproduct(*[options[d] for d in DIMENSIONS]):
        prod = 1
        for c in combo:
            prod *= c
        if prod <= n_machines_target and prod > best_product:
            best_product = prod
            best_combo = dict(zip(DIMENSIONS, combo))

    active = best_product
    spare = n_machines_target - active
    return best_combo, active, spare


def _combos_per_machine(split_counts):
    specs = _dim_specs()
    total = 1
    for d in DIMENSIONS:
        total *= specs[d]["steps"]
    active = 1
    for c in split_counts.values():
        active *= c
    return total // active  # exact (division propre garantie par construction)


def _compute_session_split(combos_machine, free_dims_steps):
    """
    Cherche, parmi les dimensions ENCORE ENTIÈRES au niveau machine
    (free_dims_steps = {dim: steps}), la combinaison de diviseurs propres
    (un par dimension, 1 = non subdivisée) qui ramène combos_machine/produit
    dans la fourchette visée, en essayant plusieurs dimensions à la fois si
    une seule ne suffit pas (contrairement à la v2 qui ne regardait qu'une
    dimension et pouvait dépasser SESSION_HARD_CAP sans le détecter).

    Stratégie, par ordre de préférence :
      1) le plus petit produit qui ramène combos/session <= SESSION_MAX
         (maximise la taille de session sans la dépasser -> minimise le
         nombre d'appels SCAPS).
      2) à défaut, le plus grand produit qui ramène combos/session
         <= SESSION_HARD_CAP.
      3) si même le découpage maximal dépasse SESSION_HARD_CAP, on le
         retourne quand même mais capped=True est levé pour que l'appelant
         puisse alerter (ne doit normalement jamais arriver si les STEPS
         sont raisonnables).

    Retourne (split_counts: {dim:int}, session_size: int, capped: bool)
    """
    if combos_machine <= SESSION_MAX:
        return {}, combos_machine, False

    dims = list(free_dims_steps.keys())
    options = {d: _clean_divisors(free_dims_steps[d], free_dims_steps[d] // 2) for d in dims}

    best_ideal = None      # (produit, split) le plus petit produit satisfaisant SESSION_MAX
    best_hardcap = None    # (produit, split) le plus grand produit satisfaisant SESSION_HARD_CAP

    for combo in iproduct(*[options[d] for d in dims]):
        prod = 1
        for c in combo:
            prod *= c
        session_size = combos_machine // prod

        if session_size <= SESSION_MAX:
            if best_ideal is None or prod < best_ideal[0]:
                best_ideal = (prod, dict(zip(dims, combo)))
        if session_size <= SESSION_HARD_CAP:
            if best_hardcap is None or prod > best_hardcap[0]:
                best_hardcap = (prod, dict(zip(dims, combo)))

    if best_ideal is not None:
        prod, split = best_ideal
        return split, combos_machine // prod, False

    if best_hardcap is not None:
        prod, split = best_hardcap
        return split, combos_machine // prod, False

    # Aucune combinaison de divisions propres ne suffit à passer sous le
    # plafond dur : on prend la plus fine possible (produit maximal) et on
    # remonte capped=True pour que l'appelant alerte clairement.
    max_combo = {d: options[d][-1] for d in dims}
    prod = 1
    for v in max_combo.values():
        prod *= v
    return max_combo, combos_machine // prod, True


def get_machine_parameters(machine_id: int, n_machines_target: int = N_MACHINES_TARGET):
    """
    Retourne la liste des sessions (jeux de paramètres batch
    [RS,P0,P1,P2,P3,P4]) qu'une machine donnée doit exécuter.

    - machine_id < nb de machines "actives" (cf. compute_split_plan) : la
      machine reçoit un bloc rectangulaire disjoint de l'espace de
      paramètres, subdivisé en sessions (potentiellement sur PLUSIEURS
      dimensions à la fois, cf. _compute_session_split) pour que chaque
      appel SCAPS reste si possible dans [SESSION_MIN, SESSION_MAX], et au
      pire sous SESSION_HARD_CAP.
    - machine_id >= nb de machines actives : machine SPARE, retourne une
      liste vide.

    Lève un avertissement (print) si même le découpage le plus fin possible
    dépasse SESSION_HARD_CAP : dans ce cas, augmentez SESSION_HARD_CAP en
    connaissance de cause, ou revoyez les STEPS pour donner plus de prise
    aux dimensions non utilisées par le découpage machine.
    """
    split_counts, active, spare = compute_split_plan(n_machines_target)

    if not (0 <= machine_id < n_machines_target):
        raise ValueError(f"machine_id doit être entre 0 et {n_machines_target - 1} (reçu {machine_id})")

    if machine_id >= active:
        return []  # machine spare : rien à faire par défaut

    specs = _dim_specs()

    # blocs machine par dimension (division propre garantie par construction)
    machine_blocs = {}
    for d in DIMENSIONS:
        n = split_counts[d]
        if n == 1:
            machine_blocs[d] = [{"from": specs[d]["from_val"], "to": specs[d]["to_val"], "steps": specs[d]["steps"]}]
        else:
            machine_blocs[d] = split_interval(specs[d]["from_val"], specs[d]["to_val"], specs[d]["steps"], n)

    shape = tuple(split_counts[d] for d in DIMENSIONS)
    idx = np.unravel_index(machine_id, shape)
    chosen_bloc = {d: machine_blocs[d][idx[i]] for i, d in enumerate(DIMENSIONS)}

    combos_machine = 1
    for d in DIMENSIONS:
        combos_machine *= chosen_bloc[d]["steps"]

    # dimensions encore entières au niveau machine = candidates pour la session
    free_dims_steps = {d: chosen_bloc[d]["steps"] for d in DIMENSIONS if split_counts[d] == 1}

    session_split, session_size, capped = _compute_session_split(combos_machine, free_dims_steps)

    if capped:
        print(f"[ATTENTION] machine {machine_id} : même le découpage le plus fin donne "
              f"{session_size} combos/session, au-dessus de SESSION_HARD_CAP={SESSION_HARD_CAP}. "
              f"Revoyez les STEPS (donnez plus de diviseurs aux dimensions non utilisées par "
              f"le découpage 40-machines) ou augmentez SESSION_HARD_CAP en connaissance de cause.")

    # sous-blocs de session, un par dimension utilisée pour la session
    session_sub_blocs = {}
    for d, n in session_split.items():
        if n == 1:
            session_sub_blocs[d] = [chosen_bloc[d]]
        else:
            session_sub_blocs[d] = split_interval(chosen_bloc[d]["from"], chosen_bloc[d]["to"],
                                                    chosen_bloc[d]["steps"], n)

    session_dims = [d for d in session_split if session_split[d] > 1]

    sessions = []
    if not session_dims:
        combos_iter = [chosen_bloc]
    else:
        combos_iter = []
        for combo in iproduct(*[session_sub_blocs[d] for d in session_dims]):
            b = dict(chosen_bloc)
            for d, sub in zip(session_dims, combo):
                b[d] = sub
            combos_iter.append(b)

    for b in combos_iter:
        RS = cfg.generate_batch_parameter(specs["RS"]["label1"], specs["RS"]["label2"], specs["RS"]["label3"],
                                           specs["RS"]["label4"], specs["RS"]["log"],
                                           b["RS"]["from"], b["RS"]["to"], b["RS"]["steps"])
        P0 = cfg.generate_batch_parameter(specs["P0"]["label1"], specs["P0"]["label2"], specs["P0"]["label3"],
                                           specs["P0"]["label4"], specs["P0"]["log"],
                                           b["P0"]["from"], b["P0"]["to"], b["P0"]["steps"])
        P1 = cfg.generate_batch_parameter(specs["P1"]["label1"], specs["P1"]["label2"], specs["P1"]["label3"],
                                           specs["P1"]["label4"], specs["P1"]["log"],
                                           b["P1"]["from"], b["P1"]["to"], b["P1"]["steps"])
        P2 = cfg.generate_batch_parameter(specs["P2"]["label1"], specs["P2"]["label2"], specs["P2"]["label3"],
                                           specs["P2"]["label4"], specs["P2"]["log"],
                                           b["P2"]["from"], b["P2"]["to"], b["P2"]["steps"])
        P3 = cfg.generate_batch_parameter(specs["P3"]["label1"], specs["P3"]["label2"], specs["P3"]["label3"],
                                           specs["P3"]["label4"], specs["P3"]["log"],
                                           b["P3"]["from"], b["P3"]["to"], b["P3"]["steps"])
        P4 = cfg.generate_batch_parameter(specs["P4"]["label1"], specs["P4"]["label2"], specs["P4"]["label3"],
                                           specs["P4"]["label4"], specs["P4"]["log"],
                                           b["P4"]["from"], b["P4"]["to"], b["P4"]["steps"])
        sessions.append([RS, P0, P1, P2, P3, P4])

    return sessions


def combos_in(batch_parameters):
    total = 1
    for p in batch_parameters:
        total *= p["steps"]
    return total


def print_plan():
    split_counts, active, spare = compute_split_plan()
    combos_machine = _combos_per_machine(split_counts)
    n_settings = len(cfg.SETTINGS)
    n_light = sum(1 for _, intensity, _ in cfg.SETTINGS if intensity)

    total_combos = combos_machine * active

    print(f"STEPS actuels          : { {d: _dim_specs()[d]['steps'] for d in DIMENSIONS} }")
    print(f"Total combinaisons     : {total_combos}")
    print(f"N_MACHINES_TARGET      : {N_MACHINES_TARGET}")
    print(f"Découpage retenu       : {split_counts}  (produit = {active} machines actives)")
    print(f"Machines SPARE         : {spare}  (machine_id {active}..{N_MACHINES_TARGET - 1})")
    print(f"Combinaisons/machine   : {combos_machine}")

    sessions0 = get_machine_parameters(0)
    print(f"Sessions/machine       : {len(sessions0)}  "
          f"(combos/session = {combos_in(sessions0[0]) if sessions0 else 0})")
    print(f"Appels SCAPS/machine   : {len(sessions0) * n_settings}")
    print(f"SETTINGS               : {n_settings} entrées ({n_light} light, {n_settings - n_light} dark)")
    print(f"Courbes IV/machine     : {combos_machine * n_settings}")
    print(f"Courbes QE/machine     : {combos_machine * n_light}")
    print(f"Courbes/machine (tot)  : {combos_machine * n_settings + combos_machine * n_light}")
    print(f"---")
    print(f"TOTAL IV  ({active} machines) : {combos_machine * n_settings * active}")
    print(f"TOTAL QE  ({active} machines) : {combos_machine * n_light * active}")
    print(f"TOTAL courbes                : {(combos_machine * n_settings + combos_machine * n_light) * active}")

    if spare:
        print(f"\n[Info] {spare} machine(s) physique(s) sur {N_MACHINES_TARGET} n'ont pas de bloc "
              f"assigné (aucune division propre de l'espace actuel ne tombe pile sur "
              f"{N_MACHINES_TARGET}). Elles peuvent servir de secours (relance de sessions "
              f"en échec) ou rester inactives. Dites-le-moi si vous voulez qu'elles soient "
              f"mises à contribution automatiquement (ex: partager la boucle SETTINGS avec "
              f"{spare} des machines actives pour un équilibrage parfait sur les 40).")


if __name__ == "__main__":
    print_plan()
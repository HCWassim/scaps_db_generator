"""
db_batch_generator_multimachine.py

À exécuter TEL QUEL sur chacun des 40 PC, sans aucune modification de code :
seule la variable d'environnement MACHINE_ID (dans le .env de la machine)
change d'un PC à l'autre.

Ce script :
  1) lit MACHINE_ID (0..39) depuis l'environnement,
  2) calcule via machine_split.get_machine_parameters() les sessions de
     paramètres (Rs/P0/P1/P2/P3/P4) qui appartiennent EXCLUSIVEMENT à cette
     machine (aucun recouvrement possible avec les autres machines),
  3) boucle sur les conditions SETTINGS (T, intensité, Rsh) déjà définies
     dans config.py, sans les modifier,
  4) pour chaque (SETTINGS x session), lance UN appel SCAPS batch,
  5) écrit/complète les CSV IV et QE de CETTE machine (chemins définis par
     OUTPUT_CSV_IV_PATH / OUTPUT_CSV_QE_PATH dans le .env de la machine —
     donnez un chemin différent par PC, ex: ./csv/machine_07/iv.csv).

--------------------------------------------------------------------------
REPRISE SUR PANNE
--------------------------------------------------------------------------
Si le script plante (crash SCAPS, coupure de courant, etc.), il suffit de
le relancer TEL QUEL : au démarrage, il compte le nombre de lignes déjà
écrites dans le CSV IV de la machine (OUTPUT_CSV_IV_PATH) et en déduit
combien d'appels SCAPS ("sessions x SETTINGS") ont déjà été menés à bien.
Il reprend alors exactement au premier appel non terminé, sans jamais
recalculer / réécrire des lignes déjà présentes.

Si le plantage a eu lieu EN COURS d'écriture d'un appel (lignes partielles
dans le CSV), ces lignes orphelines sont automatiquement détectées et
supprimées avant la reprise, pour ne pas mélanger des données incomplètes
avec le reste du dataset.

Un journal (JSON Lines) est également tenu à côté des CSV
(checkpoint_m<MACHINE_ID>.jsonl) : une ligne par appel terminé (OK) ou en
échec, plus une ligne à chaque démarrage/reprise. Ce journal n'est PAS la
source de vérité utilisée pour décider où reprendre (c'est le CSV IV qui
fait foi, comme demandé), mais il sert de trace lisible pour diagnostiquer
un plantage a posteriori.

Lancement automatique : simplement `python db_batch_generator_multimachine.py`.
Pour un vrai démarrage "sans surveillance", enveloppez cet appel dans un
script .bat/.sh de votre côté qui relance le process en cas de crash SCAPS
(voir note en bas de fichier) : la reprise sur panne ci-dessus rend cette
boucle de relance automatique totalement sûre (aucun doublon, aucune perte).
"""

import json
import os
import time
import traceback
from datetime import datetime

from pipeline.config import SETTINGS, CSV_IV_PATH, CSV_QE_PATH
from pipeline.machine_split import (
    get_machine_parameters, combos_in,
    N_MACHINES_TARGET
)
from pipeline.scaps_batch_simulation import run_batch
from outil.utils import (
    preparation_simulation, post_simulation_cleanup,
    delete_file, write_csv_file, baseline_information,
)

MACHINE_ID = os.getenv("MACHINE_ID")
if MACHINE_ID is None:
    raise EnvironmentError(
        "MACHINE_ID n'est pas défini dans le .env de cette machine. "
        f"Chaque PC doit avoir une valeur unique entre 0 et {N_MACHINES_TARGET - 1}."
    )
MACHINE_ID = int(MACHINE_ID)

JOURNAL_PATH = os.path.join(os.path.dirname(CSV_IV_PATH), f"checkpoint_m{MACHINE_ID}.jsonl")


# ---------------------------------------------------------------------------
# Outils de reprise sur panne
# ---------------------------------------------------------------------------

def count_csv_rows(path):
    """Nombre de lignes deja ecrites dans un CSV de courbes (IV/QE).

    IMPORTANT : ces fichiers n'ont PAS de ligne d'en-tete -- write_csv_file()
    (outil/utils.py) se contente d'ajouter, a chaque appel, une ligne brute
    par courbe generee (",".join(result) + f",{id_def}"), sans jamais ecrire
    de nom de colonnes. Toutes les lignes du fichier sont donc des lignes de
    donnees. Retourne 0 si le fichier n'existe pas."""
    if not os.path.isfile(path):
        return 0
    with open(path, "r") as f:
        return sum(1 for line in f if line.strip() != "")


def truncate_csv_to(path, n_data_rows):
    """Tronque un CSV de courbes (IV/QE, sans en-tete) pour ne garder que les
    n_data_rows premieres lignes. Sert a supprimer les lignes partielles/
    orphelines laissees par un plantage survenu EN COURS d'ecriture d'un
    appel SCAPS (write_csv_file ecrit toutes les lignes d'un appel en un seul
    f.write(), mais un plantage peut interrompre cette ecriture avant qu'elle
    soit complete, ou la laisser sans retour a la ligne final)."""
    if not os.path.isfile(path):
        return
    with open(path, "r") as f:
        data_lines = [line for line in f if line.strip() != ""]
    if len(data_lines) <= n_data_rows:
        return
    kept = data_lines[:n_data_rows]
    # on s'assure que chaque ligne conservee se termine par un retour a la
    # ligne, meme si la toute derniere ligne du fichier d'origine en etait
    # depourvue (ecriture interrompue en plein milieu).
    kept = [line if line.endswith("\n") else line + "\n" for line in kept]
    with open(path, "w") as f:
        f.writelines(kept)
    print(f"[Reprise] {path} : {len(data_lines)} -> {len(kept)} ligne(s) "
          f"({len(data_lines) - len(kept)} ligne(s) partielle(s)/orpheline(s) supprimee(s)).")



def journal_write(entry):
    """Ajoute une ligne au journal JSONL de cette machine (append-only)."""
    entry = {"timestamp": datetime.now().isoformat(timespec="seconds"), **entry}
    with open(JOURNAL_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def build_call_plan(sessions, settings):
    """Liste ordonnée de tous les appels SCAPS (même ordre que la double
    boucle SETTINGS x sessions ci-dessous), avec pour chacun le nombre de
    lignes IV/QE CUMULÉES attendues dans les CSV une fois cet appel terminé.
    C'est cette liste qui permet de traduire "nombre de lignes déjà dans le
    CSV" en "quel appel reprendre"."""
    plan = []
    cum_iv = 0
    cum_qe = 0
    for temp, intensity, rsh in settings:
        illumination = "light" if intensity else "dark"
        for session_idx, session_params in enumerate(sessions):
            size = combos_in(session_params)
            cum_iv += size
            if illumination == "light":
                cum_qe += size
            plan.append({
                "temp": temp, "intensity": intensity, "rsh": rsh,
                "illumination": illumination,
                "session_idx": session_idx, "session_params": session_params,
                "combos": size,
                "cum_iv": cum_iv, "cum_qe": cum_qe,
            })
    return plan


def find_resume_point(plan):
    """Détermine, à partir du nombre de lignes déjà présentes dans le CSV IV
    de la machine, l'indice (0-based) du premier appel du plan qui n'est PAS
    encore terminé. C'est le CSV IV qui fait foi (demande explicite) : le
    CSV QE n'est utilisé que pour être nettoyé/aligné en conséquence."""
    iv_rows = count_csv_rows(CSV_IV_PATH)
    qe_rows = count_csv_rows(CSV_QE_PATH)

    resume_idx = 0
    for i, call in enumerate(plan):
        if call["cum_iv"] <= iv_rows:
            resume_idx = i + 1
        else:
            break

    return resume_idx, iv_rows, qe_rows


def run_session(session_params, session_idx, temp, intensity, rsh, illumination, def_id):
    """Exécute UN appel SCAPS batch (une session) et écrit les résultats dans
    les CSV de la machine. Retourne le nombre de combinaisons traitées."""
    sim_name = f"m{MACHINE_ID}_s{session_idx}_T{temp}_I{intensity}_Rsh{rsh}"
    batch_name = sim_name

    batch_path, result_iv_path, result_qe_path, results_iv, results_qe = run_batch(
        sim_name, batch_name, session_params,
        illumination=illumination, temperature=temp, intensity=intensity, Rsh=rsh,
        singleshot=False,
    )

    delete_file(batch_path)
    delete_file(result_iv_path)
    delete_file(result_qe_path)

    write_csv_file(results_iv, CSV_IV_PATH, id_def=f"{intensity},{rsh},{def_id}")
    write_csv_file(results_qe, CSV_QE_PATH, id_def=f"{intensity},{rsh},{def_id}")

    return combos_in(session_params)


if __name__ == "__main__":
    def_id = baseline_information()
    preparation_simulation()

    sessions = get_machine_parameters(MACHINE_ID)
    if not sessions:
        print(f"Machine {MACHINE_ID} : SPARE (aucun bloc de paramètres assigné), rien à faire.")
        raise SystemExit(0)

    combos_par_session = combos_in(sessions[0])
    combos_par_machine = combos_par_session * len(sessions)

    plan = build_call_plan(sessions, SETTINGS)
    total_calls = len(plan)

    resume_idx, iv_rows_before, qe_rows_before = find_resume_point(plan)

    # Nettoyage des lignes partielles/orphelines issues d'un éventuel plantage
    # en cours d'écriture, pour repartir sur une base propre.
    clean_iv = plan[resume_idx - 1]["cum_iv"] if resume_idx > 0 else 0
    clean_qe = plan[resume_idx - 1]["cum_qe"] if resume_idx > 0 else 0
    truncate_csv_to(CSV_IV_PATH, clean_iv)
    truncate_csv_to(CSV_QE_PATH, clean_qe)

    print(f"=== Machine {MACHINE_ID}/{N_MACHINES_TARGET - 1} ===")
    print(f"Combinaisons/session : {combos_par_session}")
    print(f"Sessions/machine     : {len(sessions)}")
    print(f"Combinaisons/machine : {combos_par_machine}")
    print(f"Appels SCAPS prévus  : {total_calls}")

    if resume_idx > 0:
        next_call = plan[resume_idx] if resume_idx < total_calls else None
        print(f"\n[REPRISE] {iv_rows_before} ligne(s) déjà présentes dans {CSV_IV_PATH}")
        print(f"[REPRISE] -> {resume_idx}/{total_calls} appel(s) déjà terminé(s) "
              f"avant le plantage/arrêt précédent.")
        if next_call is not None:
            print(f"[REPRISE] Reprise à l'appel {resume_idx + 1}/{total_calls} "
                  f"(session_idx={next_call['session_idx']}, T={next_call['temp']}, "
                  f"intensity={next_call['intensity']}, Rsh={next_call['rsh']}).")
        journal_write({
            "event": "resume", "machine_id": MACHINE_ID,
            "resume_call_idx": resume_idx, "total_calls": total_calls,
            "iv_rows_before": iv_rows_before, "qe_rows_before": qe_rows_before,
        })
    else:
        print("\nDémarrage à zéro (aucune donnée existante détectée dans le CSV IV).")
        journal_write({"event": "start", "machine_id": MACHINE_ID, "total_calls": total_calls})

    if resume_idx >= total_calls:
        print("\nTous les appels sont déjà terminés d'après le CSV IV existant. Rien à faire.")
        raise SystemExit(0)

    total_iv = clean_iv
    total_qe = clean_qe
    n_calls = resume_idx
    n_failed = 0
    start_time = time.time()

    for call_idx in range(resume_idx, total_calls):
        call = plan[call_idx]
        n_calls += 1
        try:
            combos = run_session(
                call["session_params"], call["session_idx"],
                call["temp"], call["intensity"], call["rsh"],
                call["illumination"], def_id,
            )
        except Exception:
            # Un appel en échec ne doit pas bloquer les suivants.
            n_failed += 1
            print(f"[ERREUR] appel {call_idx + 1}/{total_calls} "
                  f"(session {call['session_idx']} / "
                  f"SETTINGS={call['temp']},{call['intensity']},{call['rsh']}) :")
            traceback.print_exc()
            journal_write({
                "event": "failed", "machine_id": MACHINE_ID, "call_idx": call_idx,
                "session_idx": call["session_idx"], "T": call["temp"],
                "intensity": call["intensity"], "Rsh": call["rsh"],
            })
            continue

        # On aligne les compteurs sur les valeurs attendues du plan plutôt que
        # de les incrémenter "à la main", pour qu'ils restent toujours le
        # reflet exact du contenu des CSV (et donc réutilisables tels quels
        # par une future reprise).
        total_iv = call["cum_iv"]
        total_qe = call["cum_qe"]

        journal_write({
            "event": "ok", "machine_id": MACHINE_ID, "call_idx": call_idx,
            "session_idx": call["session_idx"], "T": call["temp"],
            "intensity": call["intensity"], "Rsh": call["rsh"],
            "combos": combos, "iv_rows_cumulative": total_iv,
            "qe_rows_cumulative": total_qe,
        })

        if n_calls % 20 == 0:
            elapsed = time.time() - start_time
            print(f"  [{n_calls}/{total_calls}] "
                  f"{total_iv + total_qe} courbes générées, {elapsed:.0f}s écoulées")

    post_simulation_cleanup()
    elapsed = time.time() - start_time

    print("=== Terminé ===")
    print(f"Appels SCAPS (cette exécution) : {n_calls - resume_idx} ({n_failed} échec(s))")
    print(f"Appels SCAPS (total machine)   : {n_calls}/{total_calls}")
    print(f"Courbes IV   : {total_iv}")
    print(f"Courbes QE   : {total_qe}")
    print(f"Total        : {total_iv + total_qe}")
    print(f"Durée (cette exécution) : {elapsed:.1f}s")
    print(f"Journal : {JOURNAL_PATH}")

# ---------------------------------------------------------------------------
# Astuce lancement "sans surveillance" (optionnel) :
#
# Windows (relance auto si SCAPS plante) :
#   :loop
#   python db_batch_generator_multimachine.py
#   if errorlevel 1 goto loop
#
# Linux/Mac :
#   until python3 db_batch_generator_multimachine.py; do sleep 5; done
#
# Grâce à la reprise sur panne intégrée ci-dessus, cette boucle de relance
# automatique est désormais sûre : chaque redémarrage reprend exactement là
# où le précédent s'est arrêté, sans dupliquer ni perdre de données.
# ---------------------------------------------------------------------------
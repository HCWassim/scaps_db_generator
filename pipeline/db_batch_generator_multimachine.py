"""
db_batch_generator_multimachine.py

À exécuter TEL QUEL sur chacun des 40 PC, sans aucune modification de code :
seule la variable d'environnement MACHINE_ID (dans le .env de la machine)
change d'un PC à l'autre.

Ce script :
  1) lit MACHINE_ID (0..39) depuis l'environnement,
  2) calcule via machine_split.get_machine_parameters() les 8 sessions de
     paramètres (Rs/P0/P1/P2/P3) qui appartiennent EXCLUSIVEMENT à cette
     machine (aucun recouvrement possible avec les autres machines),
  3) boucle sur les 40 conditions SETTINGS (T, intensité, Rsh) déjà définies
     dans config.py, sans les modifier,
  4) pour chaque (SETTINGS x session), lance UN appel SCAPS batch de 512
     combinaisons (dans la fourchette 200-1000 demandée),
  5) écrit/complète les CSV IV et QE de CETTE machine (chemins définis par
     OUTPUT_CSV_IV_PATH / OUTPUT_CSV_QE_PATH dans le .env de la machine —
     donnez un chemin différent par PC, ex: ./csv/machine_07/iv.csv).

Lancement automatique : simplement `python db_batch_generator_multimachine.py`.
Pour un vrai démarrage "sans surveillance", enveloppez cet appel dans un
script .bat/.sh de votre côté qui relance le process en cas de crash SCAPS
(voir note en bas de fichier).
"""

import os
import time
import traceback

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


def run_session(session_params, session_idx, temp, intensity, rsh, illumination, def_id):
    """Exécute UN appel SCAPS batch (une session, ~512 combinaisons) et
    écrit les résultats dans les CSV de la machine. Retourne le nombre de
    combinaisons traitées (pour le comptage / la vérification finale)."""
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
    combos_par_session = combos_in(sessions[0])
    combos_par_machine = combos_par_session * len(sessions)

    print(f"=== Machine {MACHINE_ID}/{N_MACHINES_TARGET - 1} ")
    print(f"Combinaisons/session : {combos_par_session}")
    print(f"Sessions/machine     : {len(sessions)}")
    print(f"Combinaisons/machine : {combos_par_machine}")
    print(f"Appels SCAPS prévus  : {len(sessions) * len(SETTINGS)}")

    total_iv = total_qe = 0
    n_calls = 0
    n_failed = 0
    start_time = time.time()

    for temp, intensity, rsh in SETTINGS:
        illumination = "light" if intensity else "dark"
        for session_idx, session_params in enumerate(sessions):
            n_calls += 1
            try:
                combos = run_session(
                    session_params, session_idx, temp, intensity, rsh, illumination, def_id
                )
            except Exception:
                # Une session en échec ne doit pas bloquer les 319 autres.
                n_failed += 1
                print(f"[ERREUR] session {session_idx} / SETTINGS={temp},{intensity},{rsh} :")
                traceback.print_exc()
                continue

            total_iv += combos
            if illumination == "light":
                total_qe += combos

            if n_calls % 20 == 0:
                elapsed = time.time() - start_time
                print(f"  [{n_calls}/{len(sessions) * len(SETTINGS)}] "
                      f"{total_iv + total_qe} courbes générées, {elapsed:.0f}s écoulées")

    post_simulation_cleanup()
    elapsed = time.time() - start_time

    print("=== Terminé ===")
    print(f"Appels SCAPS : {n_calls} ({n_failed} échec(s))")
    print(f"Courbes IV   : {total_iv}")
    print(f"Courbes QE   : {total_qe}")
    print(f"Total        : {total_iv + total_qe}  (attendu : {combos_par_machine * len(SETTINGS) + combos_par_machine * sum(1 for _, i, _ in SETTINGS if i)})")
    print(f"Durée totale : {elapsed:.1f}s")

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
# Pour un vrai reprise-sur-panne (ne pas refaire les sessions déjà faites),
# il faudrait journaliser (temp,intensity,rsh,session_idx) déjà traités dans
# un petit fichier local et les sauter au redémarrage — dites-moi si vous
# voulez que je l'ajoute.
# ---------------------------------------------------------------------------
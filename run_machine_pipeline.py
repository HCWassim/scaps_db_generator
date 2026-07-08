"""
run_machine_pipeline.py

Enchaîne automatiquement, sur UNE machine, les 3 étapes du pipeline dans
l'ordre :

  1) pipeline.db_batch_generator_multimachine  -> génère les courbes brutes
     IV/QE (CSV_IV_PATH, CSV_QE_PATH) pour la portion de paramètres propre
     à cette machine (MACHINE_ID)
  2) data_process.py                            -> interpole les IV sur la
     grille V fixe à 85 points (CSV_IV_PROCESSED_PATH)
  3) dataset_generator.py                       -> agrège IV+QE en un
     dataset.csv local de 40 960 lignes (./csv/dataset.csv)

C'est LE script à lancer sur chacun des 40 PC (après avoir configuré son
.env avec MACHINE_ID et les chemins de sortie). Il s'arrête au premier
échec pour ne pas enchaîner une étape sur des données invalides.

Usage :
    python run_machine_pipeline.py
"""

import subprocess
import sys
import time

STEPS = [
    ("1/3 - Génération SCAPS (IV/QE bruts)", [sys.executable, "-m", "pipeline.db_batch_generator_multimachine"]),
    ("2/3 - Interpolation IV (PCHIP, grille 85 points)", [sys.executable, "data_process.py"]),
    ("3/3 - Agrégation dataset.csv (40 960 lignes attendues)", [sys.executable, "dataset_generator.py"]),
]

if __name__ == "__main__":
    pipeline_start = time.time()

    for label, cmd in STEPS:
        print(f"\n=== {label} ===")
        t0 = time.time()
        result = subprocess.run(cmd)
        elapsed = time.time() - t0

        if result.returncode != 0:
            print(f"\n[ERREUR] échec à l'étape « {label} » "
                  f"(code retour {result.returncode}) après {elapsed:.1f}s.")
            print("Arrêt du pipeline : les étapes suivantes ne sont pas lancées "
                  "pour éviter de traiter des données incomplètes/invalides.")
            sys.exit(result.returncode)

        print(f"-> terminé en {elapsed:.1f}s")

    total_elapsed = time.time() - pipeline_start
    print(f"\n=== Pipeline complet terminé sur cette machine en {total_elapsed / 60:.1f} min ===")
    print("Fichier final local : ./csv/dataset.csv (40 960 lignes attendues)")
    print("Copiez ce fichier vers csv/machine_XX/dataset.csv sur la machine centrale,")
    print("puis lancez merge_datasets.py une fois les 40 machines terminées.")
"""
generate_machine_envs.py

Génère un aperçu prêt à copier-coller des lignes à ajouter dans le .env de
CHACUN des 40 PC. Chaque PC garde son .env existant (SCAPS_EXE_PATH,
BASELINE_DIR, etc.) et y ajoute seulement les lignes qui changent d'une
machine à l'autre : MACHINE_ID et les chemins de sortie CSV.

Usage :
    python generate_machine_envs.py > machine_envs.txt

Puis ouvrez machine_envs.txt : le bloc "=== MACHINE 07 ===" correspond au
PC numéro 7, à coller dans son .env.
"""

N_MACHINES = 40

for machine_id in range(N_MACHINES):
    mid = f"{machine_id:02d}"
    print(f"=== MACHINE {mid} ===")
    print(f"MACHINE_ID={machine_id}")
    print(f'OUTPUT_CSV_IV_PATH="./csv/machine_{machine_id}/iv_curve.csv"')
    print(f'OUTPUT_CSV_IV_PROCESSED_PATH="./csv/machine_{machine_id}/iv_curve_processed.csv"')
    print(f'OUTPUT_CSV_QE_PATH="./csv/machine_{machine_id}/qe_curve.csv"')
    print(f'CSV_DATASET_PATH="./csv/machine_{machine_id}/dataset.csv"')
    print()

# Note : les chemins ci-dessus sont volontairement IDENTIQUES sur les 40 PC
# (chaque machine physique a son propre disque, donc pas de collision).
# Seul MACHINE_ID change réellement d'une machine à l'autre — c'est lui qui
# pilote quelle portion de l'espace de paramètres est traitée.
#
# C'est seulement au moment de RAPATRIER les résultats vers une machine
# centrale qu'il faut les ranger dans des dossiers distincts :
#   machine_00/dataset.csv, machine_01/dataset.csv, ..., machine_39/dataset.csv
# (copiez le ./csv/dataset.csv de chaque PC dans le dossier correspondant,
# cf. merge_datasets.py).
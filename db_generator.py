import subprocess
import os

SCAPS_PATH = r"C:\Scaps3312\scaps3312.exe"
SCRIPT_PATH = os.path.abspath(r".\scripts")
SCRIPT_NAME = "tst_script.script"
BASELINE_PATH = os.path.abspath(r".\baseline\CIGS_graded_outdoor.def")

os.makedirs(SCRIPT_PATH, exist_ok=True)

def run_scaps_simulation(script_path, script_name):
    script_content = (
        f'load definitionfile CdTe-base.def\n'
        f'load spectrumfile AM1_5G 1 sun.spe\n'
        f'action light\n'
        f'action iv.checkaction\n'
        f'calculate\n'
        f'get iv xy\n'
        f'save results.iv simu.iv\n'
        f'set quitscript.quitSCAPS\n'
    )

    full_script_path = os.path.join(script_path, script_name)
    with open(full_script_path, 'w') as script_file:
        script_file.write(script_content)

    try:
        print(f"Exécution de SCAPS avec le script : {full_script_path}")
        SCAPS_DIR = os.path.dirname(SCAPS_PATH)
        subprocess.run([SCAPS_PATH, full_script_path], cwd=SCAPS_DIR, check=True)
        print("Simulation terminée")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de SCAPS : {e}")

# print(os.path.exists(r"C:\Program Files (x86)\Scaps3312\results\simu.iv"))  # doit afficher True lais affiche False
# print(BASELINE_PATH)

run_scaps_simulation(SCRIPT_PATH, SCRIPT_NAME)

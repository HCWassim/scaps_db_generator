import subprocess
import os
import shutil

SCAPS_PATH = r"C:\Scaps3312\scaps3312.exe"
SCRIPT_PATH = os.path.abspath(r".\scripts")
SCRIPT_NAME = "iv_curve_generation.script"
BASELINE_PATH = os.path.abspath(r".\baseline\CIGS_graded_outdoor.def")
BASELINE_NAME = "CIGS_graded_outdoor.def"
DEF_PATH = r"C:\Scaps3312\def"
CSV_PATH = os.path.abspath(r".\csv\iv_curve.csv")
SIMULATION_NAME = "simulation.iv"
RESULTS_PATH = r"C:\Scaps3312\results"

os.makedirs(SCRIPT_PATH, exist_ok=True)
os.makedirs(os.path.dirname(BASELINE_PATH), exist_ok=True)
os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)


def run_scaps_simulation(baseline, simulation_name, script_path = SCRIPT_PATH, script_name = SCRIPT_NAME):
    """
    exécute la simulation de scaps en utilisant le script généré
    :param baseline: chemin vers le fichier .def à utiliser pour la simulation
    :param simulation_name: nom du fichier de résultat de la simulation
    :param script_path: chemin vers le dossier où le script sera créé
    :param script_name: nom du fichier script
    """
    script_content = (
        f'load definitionfile {baseline}\n'
        f'load spectrumfile AM1_5G 1 sun.spe\n'
        f'action light\n'
        f'action iv.checkaction\n'
        f'calculate\n'
        f'save results.iv {simulation_name}\n'
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
    except subprocess.CalledProcessError:
        pass


def baseline_scaps_insertion(source, destination):
    """
    copie le fichier .def dans le dossier baseline puis le colle dans le dossier def de scaps
    :param source: chemin vers le fichier .def à copier
    :param destination: chemin vers le dossier def de scaps 
    """
    if not os.path.isfile(source):
        print(f"Le fichier {source} n'existe pas.")
        return
    shutil.copy2(source, destination)


def baseline_scaps_extraction(file_path):
    """
    supprime le fichier .def qui a été collé dans le dossier def de scaps après l'avoir utilisé pour la simulation
    :param file_path: chemin vers le fichier .def à supprimer 
    """
    if os.path.isfile(file_path):
        os.remove(file_path)
    else :
        print(f"Le fichier {file_path} n'existe pas.")


def get_iv_file_content(iv_file_path):
    """
    """
    valuable_information_1 = False
    valuable_information_2 = False
    csv_data = []
    with open(iv_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            clean_line = line.strip()
            if clean_line.startswith("v(V)") and "jtot(mA/cm2)" in clean_line:
                valuable_information_1 = True
                continue
            elif clean_line.startswith("solar cell parameters deduced from calculated IV-curve:") :
                valuable_information_2 = True
                continue
            elif valuable_information_1 and clean_line.split() and not valuable_information_2:
                iv_point = clean_line.split()
                csv_data.append(iv_point[0])
                csv_data.append(iv_point[1])
            elif valuable_information_2 and clean_line.split() :
                iv_info = clean_line.split()
                csv_data.append(iv_info[2])
    csv_line = ",".join(csv_data)
    csv_line += "\n"
    with open(CSV_PATH, 'a') as f :
        f.write(csv_line)

def run(baseline, simulation_name, source, destination):
    """
    exécute la simulation de scaps en utilisant le fichier .def de base, puis copie le fichier .def à tester dans le dossier def de scaps, exécute la simulation de scaps à nouveau, puis supprime le fichier .def à tester du dossier def de scaps
    :param baseline: chemin vers le fichier .def de base à utiliser pour la première simulation
    :param simulation_name: nom du fichier de résultat de la simulation
    :param source: chemin vers le fichier .def à copier
    :param destination: chemin vers le dossier def de scaps 
    """
    baseline_scaps_insertion(source, destination)
    run_scaps_simulation(baseline, simulation_name)
    baseline_scaps_extraction(destination)
    get_iv_file_content(os.path.join(RESULTS_PATH, simulation_name))

run(BASELINE_NAME, SIMULATION_NAME, BASELINE_PATH, os.path.join(DEF_PATH, BASELINE_NAME))
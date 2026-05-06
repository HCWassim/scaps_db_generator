import subprocess
import os
from dotenv import load_dotenv
import shutil

load_dotenv()

# chemin scaps :
SCAPS_PATH = os.getenv("SCAPS_EXE_PATH")
DEF_PATH = os.getenv("SCAPS_DEF_DIR")
RESULTS_PATH = os.getenv("SCAPS_RESULTS_DIR")

# chemin relatif :
SCRIPT_PATH = os.path.abspath(os.getenv("SCRIPTS_DIR"))
SCRIPT_NAME = os.getenv("SCRIPT_NAME")
BASELINE_DIR = os.path.abspath(os.getenv("BASELINE_DIR"))
BASELINE_NAME = os.getenv("BASELINE_FILENAME")
BASELINE_PATH = os.path.join(BASELINE_DIR, BASELINE_NAME)
CSV_PATH = os.path.abspath(os.getenv("OUTPUT_CSV_PATH"))
V_CSV_PATH = os.path.abspath(os.getenv("V_CSV_PATH"))
SIMULATION_NAME = os.getenv("SIMULATION_FILENAME")


os.makedirs(SCRIPT_PATH, exist_ok=True)
os.makedirs(os.path.dirname(BASELINE_PATH), exist_ok=True)
os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
os.makedirs(os.path.dirname(V_CSV_PATH), exist_ok=True)


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


def get_iv_file_content(iv_file_path, v_path_file = None, save_v = False):
    """
    récupère les informations d'un fichier .iv généré par scaps et les écrit dans un fichier .csv
    :param iv_file_path: chemin vers le fichier .iv à lire
    :param v_path_file: chemin vers le fichier .v à lire
    :param save_v: booléen indiquant si les valeurs de tension doivent être sauvegardées dans v_path_file
    """
    
    valuable_information_1 = False
    valuable_information_2 = False
    
    csv_data = []
    v_data = []
    
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
                if save_v and v_path_file is not None:
                    v_data.append(iv_point[1])
            elif valuable_information_2 and clean_line.split() :
                iv_info = clean_line.split()
                csv_data.append(iv_info[2])
    
    # enregistrement d'une mesure IV
    csv_iv_line = ",".join(csv_data)
    csv_iv_line += "\n"       
    with open(CSV_PATH, 'a') as f :
        f.write(csv_iv_line)
    
    # enregistrement de la tension dans un fichier séparé pour éviter la redondance : 
    if save_v and v_path_file is not None:
        print(f"Nombre de points IV + 6 paramètres: {len(csv_data)}, Nombre de tensions : {len(v_data)}")
        csv_v_line = ",".join(v_data)
        with open(v_path_file, 'w') as f:
            f.write(csv_v_line)

def run(save_v = False):
    """
    exécute la simulation de scaps en utilisant le fichier .def de base, puis copie le fichier .def à tester dans le dossier def de scaps, exécute la simulation de scaps à nouveau, puis supprime le fichier .def à tester du dossier def de scaps
    :param save_v: booléen indiquant si les valeurs de tension doivent être sauvegardées dans un fichier séparé pour éviter la redondance dans le fichier iv_curve.csv
    """
    destination = os.path.join(DEF_PATH, BASELINE_NAME)
    baseline_scaps_insertion(BASELINE_PATH, destination)
    run_scaps_simulation(BASELINE_NAME, SIMULATION_NAME)
    baseline_scaps_extraction(destination)
    if save_v:
        get_iv_file_content(os.path.join(RESULTS_PATH, SIMULATION_NAME), v_path_file = V_CSV_PATH, save_v = True)
    else:
        get_iv_file_content(os.path.join(RESULTS_PATH, SIMULATION_NAME))

run()
import os
import time
import shutil
import subprocess
import psutil
import multiprocessing
from config import SCRIPT_PATH, SCAPS_PATH, DEF_PATH, BASELINE_NAME_V2, BASELINE_PATH_V2, CSV_DEF_PATH
from parser import parse_def_file

def scaps_execution(script_name, script_content):
    """
    Gestion de l'exécution de SCAPS à partir d'un script donné
    avec optimisation de la priorité CPU (Windows).
    """
    full_script_path = os.path.join(SCRIPT_PATH, script_name)
    with open(full_script_path, 'w') as script_file:
        script_file.write(script_content)
        
    try:
        print(f"Exécution de SCAPS avec le script : {full_script_path}")
        SCAPS_DIR = os.path.dirname(SCAPS_PATH)
        
        # 1. Lancement non-bloquant de SCAPS
        # stdout/stderr branchés sur DEVNULL suppriment les ralentissements liés à l'affichage console
        process = subprocess.Popen(
            [SCAPS_PATH, full_script_path], 
            cwd=SCAPS_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # 2. Attribution immédiate de la priorité Haute sous Windows
        try:
            p = psutil.Process(process.pid)
            p.nice(psutil.HIGH_PRIORITY_CLASS)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Le processus a pu se terminer instantanément ou les droits sont restreints
            pass

        # 3. On attend que SCAPS termine sa simulation
        return_code = process.wait()
        
        if return_code != 0:
            print(f"SCAPS a retourné un code d'erreur : {return_code}")
        else:
            print("Simulation terminée")
            
    except Exception as e:
        print(f"Erreur lors de l'exécution de SCAPS : {e}")
        
    # Nettoyage du script de commande
    if os.path.isfile(full_script_path):
        os.remove(full_script_path)
    else:
        print(f"Le script {full_script_path} n'existe pas et ne peut pas être supprimé.")


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


def delete_file(file_path):
    """
    supprime le fichier .def qui a été collé dans le dossier def de scaps après l'avoir utilisé pour la simulation
    :param file_path: chemin vers le fichier .def à supprimer 
    """
    if os.path.isfile(file_path):
        os.remove(file_path)
    else :
        print(f"Le fichier {file_path} n'existe pas.")


def preparation_simulation():
    """
    prépare l'environnement de simulation
    """
    destination = os.path.join(DEF_PATH, BASELINE_NAME_V2)
    baseline_scaps_insertion(BASELINE_PATH_V2, destination)


def post_simulation_cleanup():
    """
    nettoie l'environnement de simulation
    """
    destination = os.path.join(DEF_PATH, BASELINE_NAME_V2)
    delete_file(destination)


def run_multiprocess(process_task, parameters):
    """
    Exécute un batch de simulations en parallèle
    :param process_task: fonction à exécuter pour chaque ensemble de paramètres
    :param parameters: liste de paramètres à traiter
    :return: liste des résultats de chaque exécution
    """
    preparation_simulation()
    start_time = time.time()
    print("Lancement du batch de simulations...")

    with multiprocessing.Pool() as pool:
        outputs = pool.map(process_task, parameters)
    
    end_time = time.time()
    print(f"Temps de traitement : {end_time - start_time:.2f} secondes")
    
    return outputs


def write_csv_file(results, path, id_def=None) :
    csv_line = ""
    for result in results :
        if id_def is not None :
            csv_line += ",".join(result) + f",{id_def}" + "\n"
        else :
            csv_line += ",".join(result) + "\n"
    with open(path, 'a') as f:
        f.write(csv_line)


def baseline_information(baseline_path=BASELINE_PATH_V2, systemic_writing=False):
    """
    Cette fonction : 
    - récupère les paramètres physiques de la baseline,
    - détermine le nombre de lignes du fichier def_parameters.csv
        - dans le cas où le fichier est vide, la fonction écrit le nom des paramètres physiques puis la valeur des paramètres
        - dans le cas où le fichier contient des données, la fonction écrit une nouvelle ligne avec la valeur des paramètres
    - retourne le nombre de lignes du fichier def_parameters.csv
    """
    nom_parametres, parametres_physique = parse_def_file(baseline_path)
    with open(CSV_DEF_PATH, 'r') as f:
        nbr_line = sum(1 for _ in f)
    if nbr_line == 0 :
        write_csv_file([nom_parametres], CSV_DEF_PATH)
        write_csv_file([parametres_physique], CSV_DEF_PATH)
        nbr_line += 2
    if systemic_writing:
        write_csv_file([parametres_physique], CSV_DEF_PATH)
        nbr_line += 1

    return nbr_line
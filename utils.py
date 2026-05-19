import os
import time
import shutil
import subprocess
import multiprocessing
from config import SCRIPT_PATH, SCAPS_PATH, DEF_PATH, BASELINE_NAME, BASELINE_PATH

def scaps_execution(script_name, script_content) :
    """
    Gestion de l'exécution de SCAPS à partir d'un script donné
    :param script_name: nom du script à créer pour l'exécution de SCAPS
    :param script_content: contenu du script à créer pour l'exécution de SCAPS
    """
    full_script_path = os.path.join(SCRIPT_PATH, script_name)
    with open(full_script_path, 'w') as script_file:
        script_file.write(script_content)
    try :
        print(f"Exécution de SCAPS avec le script : {full_script_path}")
        SCAPS_DIR = os.path.dirname(SCAPS_PATH)
        subprocess.run([SCAPS_PATH, full_script_path], cwd=SCAPS_DIR, check=True)
        print("Simulation terminée")
    except subprocess.CalledProcessError:
        pass
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
    destination = os.path.join(DEF_PATH, BASELINE_NAME)
    baseline_scaps_insertion(BASELINE_PATH, destination)


def post_simulation_cleanup():
    """
    nettoie l'environnement de simulation
    """
    destination = os.path.join(DEF_PATH, BASELINE_NAME)
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

def write_csv_file(results, path) :
    csv_line = ""
    for result in results :
        csv_line += ",".join(result) + "\n"
    with open(path, 'a') as f:
        f.write(csv_line)
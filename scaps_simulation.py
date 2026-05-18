import os
from utils import scaps_execution
from config import RESULTS_PATH, SCRIPT_NAME, BASELINE_NAME, V_CSV_PATH, SIMULATION_NAME


def run_scaps_simulation(default_density_surface, default_density_volume, thickness,  baseline, simulation_name):
    """
    exécute la simulation de scaps en utilisant le script généré
    :param default_density: densité de défauts par défaut
    :param default_density_volume: densité de défauts dans le volume
    :param thickness: épaisseur de la couche
    :param baseline: chemin vers le fichier .def à utiliser pour la simulation
    :param simulation_name: nom du fichier de résultat de la simulation
    """

    script_content = (
        f'load definitionfile {baseline}\n'
        f'load spectrumfile AM1_5G 1 sun.spe\n'
        f'action light\n'
        f'action iv.checkaction\n'
        f'set interface1.IFdefect1.Ntotal {default_density_surface}\n'
        f'set layer1.defect1.Ntotal {default_density_volume}\n'
        f'set layer2.thickness {thickness}\n'
        f'calculate\n'
        f'save results.iv {simulation_name}\n'
        f'set quitscript.quitSCAPS\n'
    )

    script_name = f"{SCRIPT_NAME}_{default_density_surface}_{default_density_volume}_{thickness}.script"
    scaps_execution(script_name, script_content)


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
    return csv_iv_line


def run(default_density_surface = 5e14, default_density_volume = 5e15, thickness = 1.5e-2, save_v = False):
    """
    exécute la simulation de scaps en utilisant le fichier .def de base, puis copie le fichier .def à tester dans le dossier def de scaps, exécute la simulation de scaps à nouveau, puis supprime le fichier .def à tester du dossier def de scaps
    :param default_density_surface: densité de défauts à la surface par défaut
    :param default_density_volume: densité de défauts dans le volume
    :param thickness: épaisseur de la couche
    :param save_v: booléen indiquant si les valeurs de tension doivent être sauvegardées dans un fichier séparé pour éviter la redondance dans le fichier iv_curve.csv
    """
    simulation_name = f"{SIMULATION_NAME}_{default_density_surface}_{default_density_volume}_{thickness}.iv"
    run_scaps_simulation(default_density_surface, default_density_volume, thickness, BASELINE_NAME, simulation_name)
    if save_v:
        result_line = get_iv_file_content(os.path.join(RESULTS_PATH, simulation_name), v_path_file = V_CSV_PATH, save_v = True)
    else:
        result_line = get_iv_file_content(os.path.join(RESULTS_PATH, simulation_name))
    
    # nettoyage iv file :
    if os.path.isfile(os.path.join(RESULTS_PATH, simulation_name)):
        os.remove(os.path.join(RESULTS_PATH, simulation_name))
    else :
        print(f"Le fichier {os.path.join(RESULTS_PATH, simulation_name)} n'existe pas et ne peut pas être supprimé.")

    return result_line
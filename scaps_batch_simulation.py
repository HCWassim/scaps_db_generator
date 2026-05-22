import os
from parser import parse_iv_file, parse_qe_file
from utils import scaps_execution
from config import SCRIPT_NAME, BASELINE_NAME_V2, BATCH_PATH, RESULTS_PATH

def generate_sbf_file(parameters, batch_name):
    """
    génère un fichier .sbf correspondant à un fichier de batch scaps
    :param parameters: liste de dictionnaires contenant les paramètres du batch
    :param batch_name: nom du fichier de batch à générer
    """
    header = "batch display mode = not suppressed\n"
    blocks = [
        f"\n"
        f"Batch parameter {i} :\n"
        f"Label 1 : {param['label1']}\n"
        f"Label 2 : {param['label2']}\n"
        f"Label 3 : {param['label3']}\n"
        f"Label 4 : {param['label4']}\n"
        f"simultaneous :  0\n"
        f"values from a list :  0\n"
        f"logarithmic variation :  0\n"
        f"startvalue :   {param['startvalue']}\n"
        f"stopvalue :   {param['stopvalue']}\n"
        f"number of steps :   {param['steps']}\n"
        for i, param in enumerate(parameters)
    ]
    script_content = header + "".join(blocks) + "\n"
    batch_file_name = f"{batch_name}.sbf"
    full_batch_file_path = os.path.join(BATCH_PATH, batch_file_name)
    with open(full_batch_file_path, 'w') as batch_file:
        batch_file.write(script_content)
    if os.path.isfile(full_batch_file_path):
        return True
    else:
        return False


def run_scaps_batch_simulation(simulation_name, batch_name, illumination="light", temperature=300, intensity=100):
    """
    exécute la simulation de scaps en utilisant le script généré
    :param simulation_name: nom du fichier de résultat de la simulation
    """
    if illumination not in ["light", "dark"]:
        raise ValueError("L'illumination doit être 'light' ou 'dark'.")
    qe = 1 if illumination == "light" else 0

    script_content = (
        # chargement des fichiers pour la simulation
        f'load definitionfile {BASELINE_NAME_V2}\n'
        f'load spectrumfile AM1_5G 1 sun.spe\n'
        f'load batchsettingsfile {batch_name}.sbf\n'

        # mise en place des settings IV
        f'action {illumination}\n'
        f'action iv.checkaction 1\n'
        f'action iv.startV -0.5\n'
        f'action iv.stopV 1.2\n'
        f'action iv.points 85\n'

        # mise en place des settings de la courbe IV :
        f'action workingpoint.temperature {temperature}\n'
        f'action intensity.T {intensity}\n'

        # mise en place des settings EQE :
        f'action qe.checkaction {qe}\n'
        # f'action qe.startlambda 300\n'
        # f'action qe.stoplambda 900\n'
        # f'action qe.points 85\n'

        # valeur des paramètres fixes
        f'set external.Rs 1E-30\n' # résistance série
        # f'set layer1.Eg 1.55\n' # bandgap
        
        # obtention des résultats
        f'calculate batch\n'

        f'save results.iv batch_{simulation_name}.iv\n'
        f'save results.qe batch_{simulation_name}.qe\n'
        f'set quitscript.quitSCAPS\n'
    )

    script_name = f"{simulation_name}_{SCRIPT_NAME}_batch.script"
    scaps_execution(script_name, script_content)


def run_batch(simulation_name, batch_name, batch_parameters, illumination="light", temperature=80, intensity=100):
    generate_sbf_file(batch_parameters, batch_name)
    run_scaps_batch_simulation(simulation_name, batch_name, illumination, temperature, intensity)
    full_batch_path = os.path.join(BATCH_PATH, f"{batch_name}.sbf")
    full_results_iv_path = os.path.join(RESULTS_PATH, f"batch_{simulation_name}.iv")
    full_results_qe_path = os.path.join(RESULTS_PATH, f"batch_{simulation_name}.qe")
    results_iv = parse_iv_file(full_results_iv_path)
    results_qe = parse_qe_file(full_results_qe_path)
    return full_batch_path, full_results_iv_path, full_results_qe_path, results_iv, results_qe
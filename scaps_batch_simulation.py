import re
import os
from utils import scaps_execution
from config import SCRIPT_NAME, BASELINE_NAME, BATCH_PATH, RESULTS_PATH, CSV_PATH

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


def run_scaps_batch_simulation(simulation_name, batch_name):
    """
    exécute la simulation de scaps en utilisant le script généré
    :param simulation_name: nom du fichier de résultat de la simulation
    """

    script_content = (
        # chargement des fichiers pour la simulation
        f'load definitionfile {BASELINE_NAME}\n'
        f'load spectrumfile AM1_5G 1 sun.spe\n'
        f'load batchsettingsfile {batch_name}.sbf\n'
        
        # mise en place des settings
        f'action light\n'
        f'action iv.checkaction\n'        
        
        # obtention des résultats
        f'calculate batch\n'

        f'save results.iv batch_{simulation_name}.iv\n'
        f'set quitscript.quitSCAPS\n'
    )

    script_name = f"{simulation_name}_{SCRIPT_NAME}_batch.script"
    scaps_execution(script_name, script_content)


def parse_iv_file(filepath: str) -> list[list[str]]:
    """
    Parse a SCAPS .iv batch file.
 
    Returns a list of rows, one per simulation. Each row is:
        [v0, v1, ..., vN, i0, i1, ..., iN, Voc, Jsc, FF, eta, V_MPP, J_MPP]
    All values are kept as strings (no float conversion).
    """
    # Data lines: first two columns are voltage and current, tab-separated
    iv_re = re.compile(
        r'^\s*(-?\d+\.\d+(?:[eE][+-]?\d+)?)'   # v(V) — first column
        r'[\t ]+'                                 # separator
        r'(-?\d+\.\d+(?:[eE][+-]?\d+)?)'         # jtot — second column
    )
    # Parameters: "Voc =\t    0.765559\tVolt"
    param_re = {
        'Voc':   re.compile(r'^Voc\s*=\s*(-?\d+\.\d+(?:[eE][+-]?\d+)?)'),
        'Jsc':   re.compile(r'^Jsc\s*=\s*(-?\d+\.\d+(?:[eE][+-]?\d+)?)'),
        'FF':    re.compile(r'^FF\s*=\s*(-?\d+\.\d+(?:[eE][+-]?\d+)?)'),
        'eta':   re.compile(r'^eta\s*=\s*(-?\d+\.\d+(?:[eE][+-]?\d+)?)'),
        'V_MPP': re.compile(r'^V_MPP\s*=\s*(-?\d+\.\d+(?:[eE][+-]?\d+)?)'),
        'J_MPP': re.compile(r'^J_MPP\s*=\s*(-?\d+\.\d+(?:[eE][+-]?\d+)?)'),
    }
    header_re = re.compile(r'^\s*v\(V\)[\t ]')
 
    results = []
 
    current_voltages: list[str] = []
    current_currents: list[str] = []
    current_params: dict[str, str] = {}
    in_iv_table = False
 
    def flush():
        """Save current simulation if complete."""
        if current_voltages and len(current_params) == 6:
            row = (
                current_voltages
                + current_currents
                + [current_params[k] for k in ('Voc', 'Jsc', 'FF', 'eta', 'V_MPP', 'J_MPP')]
            )
            results.append(row)
 
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            stripped = line.strip()
 
            # Detect start of IV table header → flush previous simulation and reset
            if header_re.match(line):
                if current_voltages or current_params:
                    flush()
                current_voltages = []
                current_currents = []
                current_params = {}
                in_iv_table = True
                continue
 
            # Collect IV data points
            if in_iv_table:
                # Skip blank lines (file has a blank line right after the header)
                if stripped == '':
                    continue
                m = iv_re.match(line)
                if m:
                    current_voltages.append(m.group(1))
                    current_currents.append(m.group(2))
                    continue
                else:
                    # Non-data, non-blank line ends the IV table
                    in_iv_table = False
 
            # Collect solar cell parameters
            for key, pattern in param_re.items():
                m = pattern.match(stripped)
                if m:
                    current_params[key] = m.group(1)
                    break
 
    # Flush last simulation
    flush()
    return results


def run_batch(simulation_name, batch_name, batch_parameters):
    generate_sbf_file(batch_parameters, batch_name)
    run_scaps_batch_simulation(simulation_name, batch_name)
    full_batch_path = os.path.join(BATCH_PATH, f"{batch_name}.sbf")
    full_results_path = os.path.join(RESULTS_PATH, f"batch_{simulation_name}.iv")
    results = parse_iv_file(full_results_path)
    return full_batch_path, full_results_path, results


def write_csv_file(results) :
    csv_line = ""
    for result in results :
        csv_line += ",".join(result) + "\n"
    with open(CSV_PATH, 'a') as f:
        f.write(csv_line)
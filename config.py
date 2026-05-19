import os
from dotenv import load_dotenv
from interval import split_interval

load_dotenv()

# chemin scaps :
SCAPS_PATH = os.getenv("SCAPS_EXE_PATH")
DEF_PATH = os.getenv("SCAPS_DEF_DIR")
RESULTS_PATH = os.getenv("SCAPS_RESULTS_DIR")
BATCH_PATH = os.getenv("SCAPS_BATCH_DIR")

# chemin relatif :
SCRIPT_PATH = os.path.abspath(os.getenv("SCRIPTS_DIR"))
SCRIPT_NAME = os.getenv("SCRIPT_NAME")
BASELINE_DIR = os.path.abspath(os.getenv("BASELINE_DIR"))
BASELINE_NAME = os.getenv("BASELINE_FILENAME")
BASELINE_PATH = os.path.join(BASELINE_DIR, BASELINE_NAME)
CSV_IV_PATH = os.path.abspath(os.getenv("OUTPUT_CSV_IV_PATH"))
CSV_QE_PATH = os.path.abspath(os.getenv("OUTPUT_CSV_QE_PATH"))
CSV_DEF_PATH = os.path.abspath(os.getenv("OUTPUT_CSV_DEF_PATH"))
SIMULATION_NAME = os.getenv("SIMULATION_FILENAME")

CORE = os.cpu_count() or 4

# Dopage :
P0_LABEL1 = "layer 1"
P0_LABEL2 = "NA"
P0_LABEL3 = "nihil"
P0_LABEL4 = "nihil"
DOPAGE_FROM = 1E15
DOPAGE_TO = 1E17
DOPAGE_STEPS = 2

# Densité de défaut :
P1_LABEL1 = "layer 1"
P1_LABEL2 = "defect 1"
P1_LABEL3 = "Nt total"
P1_LABEL4 = "nihil"
DEFAULT_DENSITY_VOLUME_FROM = 5E17
DEFAULT_DENSITY_VOLUME_TO = 5E18
DEFAULT_DENSITY_VOLUME_STEPS = 2

# Hole mobility :
P2_LABEL1 = "layer 1"
P2_LABEL2 = "mu p"
P2_LABEL3 = "nihil"
P2_LABEL4 = "pure A material"
HOLE_FROM = 1E1
HOLE_TO = 3E1
HOLE_STEPS = 2

def generate_batch_parameter(label1, label2, label3, label4, from_val, to_val, steps):
    return {
        "label1": label1,
        "label2": label2,
        "label3": label3,
        "label4": label4,
        "startvalue": from_val,
        "stopvalue": to_val,
        "steps": steps
    }


divided_intervals = split_interval(DOPAGE_FROM, DOPAGE_TO, DOPAGE_STEPS, CORE)

# Subdivision de P0 en CORE sous intervalles:
BATCH_PARAMETERS = []
P1 = generate_batch_parameter(P1_LABEL1, P1_LABEL2, P1_LABEL3, P1_LABEL4, DEFAULT_DENSITY_VOLUME_FROM, DEFAULT_DENSITY_VOLUME_TO, DEFAULT_DENSITY_VOLUME_STEPS)
P2 = generate_batch_parameter(P2_LABEL1, P2_LABEL2, P2_LABEL3, P2_LABEL4, HOLE_FROM, HOLE_TO, HOLE_STEPS)
for interval in divided_intervals:
    P0_subdivide = generate_batch_parameter(P0_LABEL1, P0_LABEL2, P0_LABEL3, P0_LABEL4, interval["from"], interval["to"], interval["steps"])
    BATCH_PARAMETERS.append([P0_subdivide, P1, P2])
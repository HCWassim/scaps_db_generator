import os
from dotenv import load_dotenv
from utils import split_interval

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
CSV_PATH = os.path.abspath(os.getenv("OUTPUT_CSV_PATH"))
V_CSV_PATH = os.path.abspath(os.getenv("V_CSV_PATH"))
SIMULATION_NAME = os.getenv("SIMULATION_FILENAME")

CORE = os.cpu_count() or 4

# paramètres physique :
P0_LABEL1 = "interface 1"
P0_LABEL2 = "interface defect 1"
P0_LABEL3 = "IF Nt total"
P0_LABEL4 = "nihil"
DEFAULT_DENSITY_SURFACE_FROM = 5e14
DEFAULT_DENSITY_SURFACE_TO = 5e15
DEFAULT_DENSITY_SURFACE_STEPS = 10

P1_LABEL1 = "layer 1"
P1_LABEL2 = "defect 1"
P1_LABEL3 = "Nt total"
P1_LABEL4 = "nihil"
DEFAULT_DENSITY_VOLUME_FROM = 5e15
DEFAULT_DENSITY_VOLUME_TO = 5e17
DEFAULT_DENSITY_VOLUME_STEPS = 2

P2_LABEL1 = "layer 2"
P2_LABEL2 = "thickness"
P2_LABEL3 = "nihil"
P2_LABEL4 = "nihil"
THICKNESS_FROM = 1.5E-2
THICKNESS_TO = 1.5E-1
THICKNESS_STEPS = 2

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


divided_intervals = split_interval(DEFAULT_DENSITY_SURFACE_FROM, DEFAULT_DENSITY_SURFACE_TO, DEFAULT_DENSITY_SURFACE_STEPS, CORE)

# Subdivision de P0 en CORE sous intervalles:
BATCH_PARAMETERS = []
P1 = generate_batch_parameter(P1_LABEL1, P1_LABEL2, P1_LABEL3, P1_LABEL4, DEFAULT_DENSITY_VOLUME_FROM, DEFAULT_DENSITY_VOLUME_TO, DEFAULT_DENSITY_VOLUME_STEPS)
P2 = generate_batch_parameter(P2_LABEL1, P2_LABEL2, P2_LABEL3, P2_LABEL4, THICKNESS_FROM, THICKNESS_TO, THICKNESS_STEPS)
for interval in divided_intervals:
    P0_subdivide = generate_batch_parameter(P0_LABEL1, P0_LABEL2, P0_LABEL3, P0_LABEL4, interval["from"], interval["to"], interval["steps"])
    BATCH_PARAMETERS.append([P0_subdivide, P1, P2])
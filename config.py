import os
from dotenv import load_dotenv
from interval import split_interval, chunk_intervals
from itertools import product

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
BASELINE_NAME_V2 = os.getenv("BASELINE_FILENAME_V2")
BASELINE_PATH = os.path.join(BASELINE_DIR, BASELINE_NAME)
BASELINE_PATH_V2 = os.path.join(BASELINE_DIR, BASELINE_NAME_V2)
CSV_IV_PATH = os.path.abspath(os.getenv("OUTPUT_CSV_IV_PATH"))
CSV_QE_PATH = os.path.abspath(os.getenv("OUTPUT_CSV_QE_PATH"))
CSV_DEF_PATH = os.path.abspath(os.getenv("OUTPUT_CSV_DEF_PATH"))
SIMULATION_NAME = os.getenv("SIMULATION_FILENAME")

CORE = os.cpu_count() or 4
BLOC = 5 # varie de 0 à 7

# Dopage :
P0_LABEL1 = "layer 1"
P0_LABEL2 = "NA"
P0_LABEL3 = "nihil"
P0_LABEL4 = "nihil"
DOPAGE_FROM = 1E15
DOPAGE_TO = 1E17
DOPAGE_STEPS = 24 # 24 ce soir

# Densité de défaut :
P1_LABEL1 = "layer 1"
P1_LABEL2 = "defect 1"
P1_LABEL3 = "Nt total"
P1_LABEL4 = "nihil"
DEFAULT_DENSITY_VOLUME_FROM = 1E15 # vérifier la conversion cm^3 -> m^3
DEFAULT_DENSITY_VOLUME_TO = 1E17
DEFAULT_DENSITY_VOLUME_STEPS = 24

# Hole mobility :
P2_LABEL1 = "layer 1"
P2_LABEL2 = "mu p"
P2_LABEL3 = "nihil"
P2_LABEL4 = "pure A material"
HOLE_FROM = 1E1
HOLE_TO = 4E1
HOLE_STEPS = 24

# Electron mobility :
P3_LABEL1 = "layer 1"
P3_LABEL2 = "mu n"
P3_LABEL3 = "nihil"
P3_LABEL4 = "pure A material"
ELECTRON_FROM = 8E1
ELECTRON_TO = 1.2E2
ELECTRON_STEPS = 2


def combinaison_settings(*settings):
    return list(product(*settings))


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

# P0 - Dopage
divided_intervals_p0 = split_interval(DOPAGE_FROM, DOPAGE_TO, DOPAGE_STEPS, CORE)
multiples_blocs_de_calcul = chunk_intervals(divided_intervals_p0, n=8)
blocs_de_calcul = multiples_blocs_de_calcul[BLOC][0]

# P1 - Densité de défaut
divided_intervals_p1 = split_interval(DEFAULT_DENSITY_VOLUME_FROM, DEFAULT_DENSITY_VOLUME_TO, DEFAULT_DENSITY_VOLUME_STEPS, CORE)


BATCH_PARAMETERS = []
P0 = generate_batch_parameter(P0_LABEL1, P0_LABEL2, P0_LABEL3, P0_LABEL4, blocs_de_calcul["from"], blocs_de_calcul["to"], blocs_de_calcul["steps"])
P1 = generate_batch_parameter(P1_LABEL1, P1_LABEL2, P1_LABEL3, P1_LABEL4, DEFAULT_DENSITY_VOLUME_FROM, DEFAULT_DENSITY_VOLUME_TO, DEFAULT_DENSITY_VOLUME_STEPS)
P2 = generate_batch_parameter(P2_LABEL1, P2_LABEL2, P2_LABEL3, P2_LABEL4, HOLE_FROM, HOLE_TO, HOLE_STEPS)
P3 = generate_batch_parameter(P3_LABEL1, P3_LABEL2, P3_LABEL3, P3_LABEL4, ELECTRON_FROM, ELECTRON_TO, ELECTRON_STEPS)

# cas pour multiprocess :
for interval in divided_intervals_p1:
    P1_subdivide = generate_batch_parameter(P1_LABEL1, P1_LABEL2, P1_LABEL3, P1_LABEL4, interval["from"], interval["to"], interval["steps"])
    BATCH_PARAMETERS.append([P0, P1_subdivide, P2])

# cas pour singleprocess :
# P0 = generate_batch_parameter(P0_LABEL1, P0_LABEL2, P0_LABEL3, P0_LABEL4, DOPAGE_FROM, DOPAGE_TO, DOPAGE_STEPS)
# BATCH_PARAMETERS.append([P0, P1, P2])

# SETTINGS = combinaison_settings([300, 200], [100, 10, 1]) # Température (K) x Intensité (% de 1 sun)
SETTINGS = [(300, 100), (280, 100), (300, 10)] # Température (K) x Intensité (% de 1 sun) #,
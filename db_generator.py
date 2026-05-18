import itertools
from scaps_simulation import run
from utils import post_simulation_cleanup, run_multiprocess
from config import DEFAULT_DENSITY_SURFACE_FROM, DEFAULT_DENSITY_SURFACE_TO, DEFAULT_DENSITY_SURFACE_STEPS, DEFAULT_DENSITY_VOLUME_FROM, DEFAULT_DENSITY_VOLUME_TO, DEFAULT_DENSITY_VOLUME_STEPS, THICKNESS_FROM, THICKNESS_TO, THICKNESS_STEPS, CSV_PATH


def generate_batch_values(from_val, to_val, steps) :
    """
    génère une liste de valeurs allant de from_val à to_val en steps étapes
    :param from_val: valeur de départ
    :param to_val: valeur de fin
    :param steps: nombre d'étapes
    :return: liste de valeurs au format scientifique avec 3 décimales
    """
    num_points = steps
    
    return [
        f"{from_val + i * (to_val - from_val) / steps:.3e}" 
        for i in range(num_points)
    ]


def generate_batch() :
    lst_DD_surface = generate_batch_values(DEFAULT_DENSITY_SURFACE_FROM, DEFAULT_DENSITY_SURFACE_TO, DEFAULT_DENSITY_SURFACE_STEPS)
    lst_DD_volume = generate_batch_values(DEFAULT_DENSITY_VOLUME_FROM, DEFAULT_DENSITY_VOLUME_TO, DEFAULT_DENSITY_VOLUME_STEPS)
    lst_thickness = generate_batch_values(THICKNESS_FROM, THICKNESS_TO, THICKNESS_STEPS)
    return list(itertools.product(lst_DD_surface, lst_DD_volume, lst_thickness))


def run_and_return(parameters):
    return parameters[0], run(parameters[0], parameters[1], parameters[2])


if __name__ == "__main__":
    parameters = generate_batch()
    results = run_multiprocess(run_and_return, parameters)

    # Écriture CSV séquentielle, dans l'ordre, sans race condition
    results.sort(key=lambda x: float(x[0]))  # tri par densité
    with open(CSV_PATH, 'a') as f:
        for density, line in results:
            if line:
                f.write(line)
    print("fin du batch de simulation")
    post_simulation_cleanup()
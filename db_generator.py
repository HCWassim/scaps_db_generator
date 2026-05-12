import time
import itertools
import multiprocessing
from scaps_simulation import run, preparation_simulation, post_simulation_cleanup
from config import DEFAULT_DENSITY_SURFACE_FROM, DEFAULT_DENSITY_SURFACE_TO, DEFAULT_DENSITY_SURFACE_STEPS, DEFAULT_DENSITY_VOLUME_FROM, DEFAULT_DENSITY_VOLUME_TO, DEFAULT_DENSITY_VOLUME_STEPS, THICKNESS_FROM, THICKNESS_TO, THICKNESS_STEPS
from config import CSV_PATH


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
    preparation_simulation()
    parameters = generate_batch()

    start_time = time.time()
    print("Lancement du batch de simulations...")

    with multiprocessing.Pool() as pool:
        results = pool.map(run_and_return, parameters)

    end_time = time.time()
    print(f"Temps de traitement : {end_time - start_time:.2f} secondes")

    # Écriture CSV séquentielle, dans l'ordre, sans race condition
    results.sort(key=lambda x: float(x[0]))  # tri par densité
    with open(CSV_PATH, 'a') as f:
        for density, line in results:
            if line:
                f.write(line)

    print("fin du batch de simulation")
    post_simulation_cleanup()
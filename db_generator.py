import multiprocessing
from scaps_simulation import run, preparation_simulation, post_simulation_cleanup, CSV_PATH

DEFAULT_DENSITY_FROM = 5e14
DEFAULT_DENSITY_TO = 5e15
DEFAULT_DENSITY_STEPS = 10

def generate_batch() :
    """
    génère un batch de simulation en faisant varier la densité de défauts de DEFAULT_DENSITY_FROM à DEFAULT_DENSITY_TO en DEFAULT_DENSITY_STEPS étapes
    """
    num_points = DEFAULT_DENSITY_STEPS + 1
    
    return [
        f"{DEFAULT_DENSITY_FROM + i * (DEFAULT_DENSITY_TO - DEFAULT_DENSITY_FROM) / DEFAULT_DENSITY_STEPS:.3e}" 
        for i in range(num_points)
    ]


def run_and_return(density):
    return density, run(density)


if __name__ == "__main__":
    preparation_simulation()
    densities = generate_batch()

    print("Lancement du batch de simulations...")
    with multiprocessing.Pool() as pool:
        results = pool.map(run_and_return, densities)

    # Écriture CSV séquentielle, dans l'ordre, sans race condition
    results.sort(key=lambda x: float(x[0]))  # tri par densité
    with open(CSV_PATH, 'a') as f:
        for density, line in results:
            if line:
                f.write(line)

    print("fin du batch de simulation")
    post_simulation_cleanup()

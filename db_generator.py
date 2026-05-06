from concurrent.futures import ProcessPoolExecutor
from scaps_simulation import run, preparation_simulation, post_simulation_cleanup

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
    # with ProcessPoolExecutor() as executor:
    #     executor.map(run, densities)
    # print("Fin du batch de simulations.")

if __name__ == "__main__":
    preparation_simulation()
    densities = generate_batch()
    for density in densities:
        run(density)
    post_simulation_cleanup()

import time
import multiprocessing
from scaps_simulation import preparation_simulation, post_simulation_cleanup
from config import BATCH_PARAMETERS
from scaps_batch_simulation import run_batch, write_csv_file

def run_and_return(parameters):
    return run_batch(f"simu_{parameters["startvalue"]}", f"batch_{parameters["startvalue"]}", parameters)

if __name__ == "__main__":
    preparation_simulation()
    
    start_time = time.time()
    print("Lancement du batch de simulations...")

    with multiprocessing.Pool() as pool:
        results = pool.map(run_and_return, BATCH_PARAMETERS)
    
    end_time = time.time()
    print(f"Temps de traitement : {end_time - start_time:.2f} secondes")

    for result in results:
        write_csv_file(result)

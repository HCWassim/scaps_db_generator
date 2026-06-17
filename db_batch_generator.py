from config import BATCH_PARAMETERS, CSV_IV_PATH, CSV_QE_PATH, SETTINGS
from utils import post_simulation_cleanup, delete_file, run_multiprocess, write_csv_file, baseline_information
from scaps_batch_simulation import run_batch
from functools import partial
import time


def run_and_return(parameters, illumination="light", temperature=300, intensity=100):
    return run_batch(f"simu_{parameters[2]['startvalue']}", 
                     f"batch_{parameters[2]['startvalue']}", 
                     parameters, illumination, temperature, intensity)


def full_process(process_task, id_def=None):
    outputs = run_multiprocess(process_task, BATCH_PARAMETERS)
    for batch_path, result_iv_path, result_qe_path, results_iv, results_qe in outputs:
        delete_file(batch_path)
        delete_file(result_iv_path)
        delete_file(result_qe_path)
        write_csv_file(results_iv, CSV_IV_PATH, id_def=id_def)
        write_csv_file(results_qe, CSV_QE_PATH, id_def=id_def)
    
    post_simulation_cleanup()


if __name__ == "__main__":

    def_id = baseline_information()

    start_time = time.time()

    # génération de l'ensemble des cas :
    # for temp, intensity in SETTINGS:
    #     process_task = partial(run_and_return, illumination="light", temperature=temp, intensity=intensity)
    #     full_process(process_task, id_def=f"{intensity},{def_id}")

    # process_task_dark_1 = partial(run_and_return, illumination="dark", temperature=300, intensity=0)
    # full_process(process_task_dark_1, id_def=f"0,{def_id}")

    # génération d'un cas particulier :
    process_task = partial(run_and_return, illumination="light", temperature=300, intensity=100)
    full_process(process_task, id_def=f"0,{def_id}")

    end_time = time.time()
    print(f"Temps de traitement : {end_time - start_time:.2f} secondes")

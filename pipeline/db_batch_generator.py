from pipeline.config import BATCH_PARAMETERS, CSV_IV_PATH, CSV_QE_PATH, SETTINGS
from utils.utils import preparation_simulation, post_simulation_cleanup, delete_file, run_multiprocess, write_csv_file, baseline_information
from pipeline.scaps_batch_simulation import run_batch
from functools import partial
import time

singleshot = False # True pour exécuter en mode single shot, False pour exécuter en mode multiprocess

def run_and_return(parameters, illumination="light", temperature=300, intensity=100, Rsh=1E2, singleshot=False):
    return run_batch(f"simu_{parameters[0]['startvalue']}", 
                     f"batch_{parameters[0]['startvalue']}", 
                     parameters, illumination, temperature, intensity, Rsh, singleshot)


def full_process_multi(process_task, id_def=None):
    outputs = run_multiprocess(process_task, BATCH_PARAMETERS)
    for batch_path, result_iv_path, result_qe_path, results_iv, results_qe in outputs:
        delete_file(batch_path)
        delete_file(result_iv_path)
        delete_file(result_qe_path)
        write_csv_file(results_iv, CSV_IV_PATH, id_def=id_def)
        write_csv_file(results_qe, CSV_QE_PATH, id_def=id_def)
    
    post_simulation_cleanup()


def full_process_single(batch_output, id_def=None):
    batch_path, result_iv_path, result_qe_path, results_iv, results_qe = batch_output
    delete_file(batch_path)
    delete_file(result_iv_path)
    delete_file(result_qe_path)
    write_csv_file(results_iv, CSV_IV_PATH, id_def=id_def)
    write_csv_file(results_qe, CSV_QE_PATH, id_def=id_def)


if __name__ == "__main__":
    def_id = baseline_information()

    start_time = time.time()
    # cas en singleshot :
    if singleshot :
        preparation_simulation()
        batch_output = run_batch(
            f"singleshot_simu_{BATCH_PARAMETERS[0][0]['startvalue']}", 
            f"batch_{BATCH_PARAMETERS[0][0]['startvalue']}",
            BATCH_PARAMETERS[0], illumination="light", temperature=300, intensity=100, Rsh=1E2, singleshot=True
        )
        full_process_single(batch_output, id_def=f"100,{1E2},{def_id}")

        batch_output = run_batch(
            f"singleshot_simu_{BATCH_PARAMETERS[0][0]['startvalue']}", 
            f"batch_{BATCH_PARAMETERS[0][0]['startvalue']}",
            BATCH_PARAMETERS[0], illumination="light", temperature=300, intensity=100, Rsh=1E5, singleshot=True
        )
        full_process_single(batch_output, id_def=f"100,{1E5},{def_id}")
        post_simulation_cleanup()
    # cas en multiprocess :
    else :
        # génération de l'ensemble des cas :
        for temp, intensity, rsh in SETTINGS:
            if intensity :
                process_task = partial(run_and_return, illumination="light", temperature=temp, intensity=intensity, Rsh=rsh, singleshot=False)
            else :
                process_task = partial(run_and_return, illumination="dark", temperature=temp, intensity=intensity, Rsh=rsh, singleshot=False)
            full_process_multi(process_task, id_def=f"{intensity},{rsh},{def_id}")

    end_time = time.time()
    print(f"Temps de traitement : {end_time - start_time:.2f} secondes")

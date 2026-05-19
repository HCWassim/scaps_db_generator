from config import BATCH_PARAMETERS, CSV_IV_PATH, CSV_QE_PATH
from utils import post_simulation_cleanup, delete_file, run_multiprocess, write_csv_file
from scaps_batch_simulation import run_batch

def run_and_return(parameters):
    return run_batch(f"simu_{parameters[0]['startvalue']}", f"batch_{parameters[0]['startvalue']}", parameters)

if __name__ == "__main__":
    outputs = run_multiprocess(run_and_return, BATCH_PARAMETERS)

    for batch_path, result_iv_path, result_qe_path, results_iv, results_qe in outputs:
        delete_file(batch_path)
        delete_file(result_iv_path)
        delete_file(result_qe_path)
        write_csv_file(results_iv, CSV_IV_PATH)
        write_csv_file(results_qe, CSV_QE_PATH)

    post_simulation_cleanup()
from config import BATCH_PARAMETERS
from utils import post_simulation_cleanup, delete_file, run_multiprocess
from scaps_batch_simulation import run_batch, write_csv_file

def run_and_return(parameters):
    return run_batch(f"simu_{parameters[0]['startvalue']}", f"batch_{parameters[0]['startvalue']}", parameters)

if __name__ == "__main__":
    outputs = run_multiprocess(run_and_return, BATCH_PARAMETERS)

    for batch_path, result_path, results in outputs:
        delete_file(batch_path)
        delete_file(result_path)
        write_csv_file(results)
    
    post_simulation_cleanup()

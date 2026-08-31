import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pipeline.config import CSV_DATASET_FINAL_PATH, PARQUET_DATASET_FINAL_PATH

def create_parquet_dataset_from_csv():
    """
    Creates a Parquet dataset from the CSV dataset specified in the configuration.
    """
    df = pd.read_csv(CSV_DATASET_FINAL_PATH)
    parquet_table = pa.Table.from_pandas(df)
    pq.write_table(parquet_table, PARQUET_DATASET_FINAL_PATH)

if __name__ == "__main__":
    create_parquet_dataset_from_csv()

import pandas as pd

df = pd.read_csv(r"./csv/qe_curve.csv")

print(df.shape)
print(df["T"])
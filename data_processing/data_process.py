import pandas as pd
import numpy as np
from scipy.interpolate import PchipInterpolator
from pipeline.config import CSV_IV_PATH, CSV_IV_PROCESSED_PATH, CSV_IV_NO_RS_RSH_PATH

INPUT = CSV_IV_PATH
OUTPUT = CSV_IV_PROCESSED_PATH

TARGET_V = np.array([
-0.500000,-0.479762,-0.459524,-0.439286,-0.419048,-0.398810,-0.378571,-0.358333,-0.338095,-0.317857,
-0.297619,-0.277381,-0.257143,-0.236905,-0.216667,-0.196429,-0.176190,-0.155952,-0.135714,-0.115476,
-0.095238,-0.075000,-0.054762,-0.034524,-0.014286,0.005952,0.026190,0.046429,0.066667,0.086905,
0.107143,0.127381,0.147619,0.167857,0.188095,0.208333,0.228571,0.248810,0.269048,0.289286,
0.309524,0.329762,0.350000,0.370238,0.390476,0.410714,0.430952,0.451190,0.471429,0.491667,
0.511905,0.532143,0.552381,0.572619,0.592857,0.613095,0.633333,0.653571,0.673810,0.694048,
0.714286,0.734524,0.754762,0.775000,0.795238,0.815476,0.835714,0.855952,0.876190,0.896429,
0.916667,0.936905,0.957143,0.977381,0.997619,1.017857,1.038095,1.058333,1.078571,1.098810,
1.119048,1.139286,1.159524,1.179762,1.200000
])
assert len(TARGET_V) == 85, len(TARGET_V)

df = pd.read_csv(INPUT)
n = len(df)

Vcols = [f'V{i}' for i in range(1, 86)]
Icols = [f'I{i}' for i in range(1, 86)]
meta_cols = [c for c in df.columns if c not in Vcols + Icols]

I_out = np.zeros((n, 85))
trunc_lengths = np.zeros(n, dtype=int)

for r in range(n):
    V = df.loc[r, Vcols].values.astype(float)
    I = df.loc[r, Icols].values.astype(float)

    # Truncation: keep up to and including the first V strictly greater than 1.2
    above = np.where(V > 1.2)[0]
    if len(above) == 0:
        cutoff = len(V) - 1  # no aberrant tail, keep all
    else:
        cutoff = above[0]   # include first point above 1.2, drop everything after

    Vt = V[:cutoff + 1]
    It = I[:cutoff + 1]
    trunc_lengths[r] = len(Vt)

    # PCHIP: shape-preserving cubic Hermite interpolation, well suited to IV curves
    # (monotonic-ish, no Runge oscillation like a global cubic spline could introduce
    # near the exponential knee of the diode curve)
    interpolator = PchipInterpolator(Vt, It)
    I_out[r, :] = interpolator(TARGET_V)

# Build output dataframe: new V columns (identical target grid for every row),
# new interpolated I columns, plus all original metadata (physical parameters)
out = pd.DataFrame(index=df.index)
for j, c in enumerate(Vcols):
    out[c] = TARGET_V[j]
for j, c in enumerate(Icols):
    out[c] = I_out[:, j]
for c in meta_cols:
    out[c] = df[c]

out.to_csv(OUTPUT, index=False)

print('Rows processed:', n)
print('Truncated length stats: min={}, max={}, mean={:.1f}'.format(
    trunc_lengths.min(), trunc_lengths.max(), trunc_lengths.mean()))
print('Saved to', OUTPUT)
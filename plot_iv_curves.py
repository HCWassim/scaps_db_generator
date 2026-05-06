import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np


V = pd.read_csv("./csv/V.csv", header=None).values.flatten()[:41]
J = pd.read_csv("./csv/iv_curve.csv", header=None).iloc[:, :41]

print(f"Tension V : {len(V)} points")
print(f"Courbes J : {len(J)} courbes x {J.shape[1]} points")

fig, ax = plt.subplots(figsize=(10, 6))
colors = cm.viridis(np.linspace(0, 1, len(J)))

for i, (_, row) in enumerate(J.iterrows()):
    ax.plot(V, row.values, color=colors[i], linewidth=1.2, label=f"Courbe {i+1}")

ax.set_xlabel("Tension V (V)", fontsize=13)
ax.set_ylabel("Densité de courant J (mA/cm²)", fontsize=13)
ax.set_title("Courbes I-V", fontsize=15, fontweight="bold")
ax.grid(True, linestyle="--", alpha=0.5)
ax.axhline(0, color="black", linewidth=0.8)
ax.axvline(0, color="black", linewidth=0.8)

if len(J) <= 15:
    ax.legend(loc="best", fontsize=8, ncol=2)
else:
    sm = plt.cm.ScalarMappable(cmap="viridis", norm=plt.Normalize(1, len(J)))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label("Indice de courbe", fontsize=11)

plt.tight_layout()
plt.show()
print("Graphe sauvegardé : iv_curves.png")
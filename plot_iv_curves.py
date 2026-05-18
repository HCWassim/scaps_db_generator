import os
import matplotlib.pyplot as plt
import numpy as np


def plot_iv_curves(chemin_fichier, n_points=None):
    """
    Charge un fichier CSV et superpose toutes ses lignes sur un seul graphique I-V.

    Chaque ligne doit suivre le format :
    [v0, ..., vN-1, i0, ..., iN-1, Voc, Jsc, FF, eta, V_MPP, J_MPP]

    Parameters:
    -----------
    chemin_fichier : str
        Le chemin vers votre fichier .csv
    n_points : int or None
        Nombre de points de mesure. Si None, déduit automatiquement depuis (len - 6) // 2.
    """
    donnees = np.loadtxt(chemin_fichier, delimiter=',', ndmin=2)

    fig, ax = plt.subplots(figsize=(10, 7))

    for idx, ligne in enumerate(donnees):
        # Déduction automatique du nombre de points si non spécifié
        n = n_points if n_points is not None else (len(ligne) - 6) // 2

        V = ligne[:n]
        I = ligne[n : 2 * n]
        indicateurs = ligne[2 * n:]  # [Voc, Jsc, FF, eta, V_MPP, J_MPP]

        if idx < 10 :
            if len(indicateurs) >= 4:
                Voc, Jsc, FF, eta = indicateurs[:4]
                label_courbe = f"Sim {idx+1} ($\\eta$ = {eta:.1f} %, $V_{{oc}}$ = {Voc:.3f} V)"
            else:
                label_courbe = f"Sim {idx+1}"

            ax.plot(V, I, '-', linewidth=2, label=label_courbe)

    ax.set_xlabel('Tension $V$ (V)', fontsize=11)
    ax.set_ylabel('Densité de courant $J$ (mA/cm²)', fontsize=11)
    ax.set_title('Superposition des caractéristiques I-V', fontsize=13, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='best', fontsize=9.5)
    plt.tight_layout()

    nom_image = "./img/superposition_courbes_iv.png"
    os.makedirs(os.path.dirname(nom_image), exist_ok=True)
    fig.savefig(nom_image, dpi=300)
    plt.show()
    plt.close(fig)

    print(f"Graphique sauvegardé ({len(donnees)} courbe(s)) : {nom_image}")


plot_iv_curves(r"./csv/iv_curve.csv")
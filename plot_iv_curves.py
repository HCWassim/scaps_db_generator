import os
import matplotlib.pyplot as plt
import numpy as np


def plot_iv_curves(chemin_fichier, n_points=None):
    """Charge un fichier CSV et superpose toutes ses lignes sur un seul graphique I-V.

    Chaque ligne doit suivre le format :
    [v0, ..., vN-1, i0, ..., iN-1, Voc, Jsc, FF, eta, V_MPP, J_MPP, T, N_A, N_t, mu_h]

    Parameters:
    -----------
    chemin_fichier : str
        Le chemin vers votre fichier .csv
    n_points : int or None
        Nombre de points de mesure. Si None, déduit automatiquement en retirant
        les 6 métriques IV et les 4 paramètres physiques (total de 10 valeurs).
    """
    donnees = np.loadtxt(chemin_fichier, delimiter=",", ndmin=2)

    # Fenêtre élargie pour accueillir la légende détaillée sur le côté
    fig, ax = plt.subplots(figsize=(11, 7))

    for idx, ligne in enumerate(donnees):
        # Déduction du nombre de points : on retire les 6 indicateurs IV + 5 physiques + 1 id = 12
        n = n_points if n_points is not None else (len(ligne) - 13) // 2

        V = ligne[:n]
        I = ligne[n : 2 * n]

        # Récupération des 4 derniers éléments de la ligne complète
        param_physiques = ligne[-6:]

        if idx < 10:
            if len(ligne) >= (2 * n) + 4:
                T, N_A, N_t, mu_h,_,_ = param_physiques
                # Label combinant le numéro de simulation et les paramètres physiques
                label_courbe = (
                    f"Sim {idx+1} ($T$={T:.0f}K, "
                    f"$N_A$={N_A:.1e}, "
                    f"$N_t$={N_t:.1e}, "
                    f"$\\mu_h$={mu_h:.1f})"
                )
            else:
                label_courbe = f"Sim {idx+1}"

            ax.plot(V, I, "-", linewidth=2, label=label_courbe)
        else:
            # Courbes au-delà de 10 : tracées discrètement sans surcharger la légende
            ax.plot(V, I, "-", linewidth=1, alpha=0.5)

    # Configuration du graphique
    ax.set_xlabel("Tension $V$ (V)", fontsize=11)
    ax.set_ylabel("Densité de courant $J$ (mA/cm²)", fontsize=11)
    ax.set_title(
        "Superposition des caractéristiques I-V", fontsize=13, fontweight="bold"
    )
    ax.grid(True, linestyle=":", alpha=0.6)

    # Positionnement de la légende à l'extérieur droit pour éviter les superpositions
    if len(donnees) > 1:
        ax.legend(
            loc="upper left",
            bbox_to_anchor=(1.02, 1),
            fontsize=9,
            borderaxespad=0,
        )

    plt.tight_layout()

    nom_image = "./img/superposition_courbes_iv.png"
    os.makedirs(os.path.dirname(nom_image), exist_ok=True)
    # bbox_inches='tight' est crucial ici pour ne pas couper la légende externe à l'export
    fig.savefig(nom_image, dpi=300, bbox_inches="tight")
    plt.show()
    plt.close(fig)

    print(f"Graphique sauvegardé ({len(donnees)} courbe(s)) : {nom_image}")


plot_iv_curves(r"./csv/iv_curve.csv")
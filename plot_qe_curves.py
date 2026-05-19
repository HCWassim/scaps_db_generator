import os
import matplotlib.pyplot as plt
import numpy as np


def plot_qe_curves(chemin_fichier, n_points=61):
    """Charge un fichier CSV et superpose toutes ses lignes sur un seul graphique QE.

    Chaque ligne doit suivre le format :
    [lambda0, ..., lambdaN-1, qe0, ..., qeN-1, T, N_A, N_t, mu_h, id_def]

    Parameters:
    -----------
    chemin_fichier : str
        Le chemin vers votre fichier .csv
    n_points : int
        Nombre de points de mesure (longueurs d'onde). Par défaut 61.
    """
    donnees = np.loadtxt(chemin_fichier, delimiter=",", ndmin=2)

    fig, ax = plt.subplots(figsize=(11, 7))  # Légèrement élargi pour la légende

    for idx, ligne in enumerate(donnees):
        # Extraction des données spectrales
        wavelengths = ligne[:n_points]
        qe_values = ligne[n_points : 2 * n_points]

        # Les 5 derniers paramètres de la ligne
        indicateurs = ligne[-5:]

        if idx < 10:
            if len(ligne) >= (2 * n_points) + 5:
                T, N_A, N_t, mu_h, _ = indicateurs
                # Formatage de la légende avec les symboles physiques en LaTeX
                label_courbe = (
                    f"Sim {idx+1} ($T$={T:.0f}K, "
                    f"$N_A$={N_A:.1e}, "
                    f"$N_t$={N_t:.1e}, "
                    f"$\\mu_h$={mu_h:.1f}, "
                )
            else:
                label_courbe = f"Sim {idx+1}"

            ax.plot(
                wavelengths, qe_values, "-", linewidth=2, label=label_courbe
            )
        else:
            # Courbes au-delà de 10 : tracées en transparence sans encombrer la légende
            ax.plot(wavelengths, qe_values, "-", linewidth=1, alpha=0.5)

    # Configuration du graphique
    ax.set_xlabel("Longueur d'onde $\lambda$ (nm)", fontsize=11)
    ax.set_ylabel("QE (%)", fontsize=11)
    ax.set_title(
        "Efficacité Quantique (QE)", fontsize=13, fontweight="bold"
    )
    ax.grid(True, linestyle=":", alpha=0.6)

    # Affichage de la légende à droite si elle contient beaucoup d'informations
    if len(donnees) > 1:
        ax.legend(
            loc="upper left",
            bbox_to_anchor=(1.02, 1),
            fontsize=9,
            borderaxespad=0,
        )

    plt.tight_layout()

    # Sauvegarde de l'image
    nom_image = "./img/superposition_courbes_qe.png"
    os.makedirs(os.path.dirname(nom_image), exist_ok=True)
    fig.savefig(nom_image, dpi=300, bbox_inches="tight")
    plt.show()
    plt.close(fig)

    print(f"Graphique sauvegardé ({len(donnees)} courbe(s)) : {nom_image}")


# Appel de la fonction
plot_qe_curves(r"./csv/qe_curve.csv")
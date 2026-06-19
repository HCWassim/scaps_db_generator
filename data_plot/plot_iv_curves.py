import os
import matplotlib.pyplot as plt
import numpy as np
import csv

def verifier_coherence_csv(chemin_fichier):
    lignes_valides = 0
    lignes_invalides = 0
    erreurs = []

    try:
        with open(chemin_fichier, mode="r", encoding="utf-8") as fichier:
            # reader permet de lire le CSV ligne par ligne sous forme de liste
            lecteur = csv.reader(fichier)

            # On récupère l'en-tête et on compte ses colonnes
            try:
                en_tete = next(lecteur)
                nb_colonnes_reference = len(en_tete)
            except StopIteration:
                print("Le fichier CSV est vide.")
                return

            # Vérification des lignes suivantes (le lecteur commence à la ligne 2)
            # lecteur.line_num donne le vrai numéro de ligne dans le fichier
            for ligne in lecteur:
                # Si la ligne est vide, on passe (optionnel, selon tes besoins)
                if not ligne:
                    continue

                if len(ligne) == nb_colonnes_reference:
                    lignes_valides += 1
                else:
                    lignes_invalides += 1
                    erreurs.append(
                        f"Ligne {lecteur.line_num} : {len(ligne)} colonnes (attendu : {nb_colonnes_reference})"
                    )

        # Affichage des résultats
        print("--- Résultat de la vérification ---")
        print(f"Nombre de colonnes attendu (en-tête) : {nb_colonnes_reference}")
        print(f"Nombre de lignes conformes : {lignes_valides}")
        print(f"Nombre de lignes incorrectes : {lignes_invalides}")

        if lignes_invalides > 0:
            print("\nDétail des anomalies (10 premières max) :")
            for erreur in erreurs[:10]:
                print(f"  - {erreur}")

    except FileNotFoundError:
        print(f"Erreur : Le fichier '{chemin_fichier}' est introuvable.")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")


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
    donnees = np.loadtxt(chemin_fichier, delimiter=",", ndmin=2, skiprows=1)

    # Fenêtre élargie pour accueillir la légende détaillée sur le côté
    fig, ax = plt.subplots(figsize=(11, 7))

    for idx, ligne in enumerate(donnees):
        # Déduction du nombre de points : on retire les 6 indicateurs IV + 8 physiques + 1 id = 15
        n = n_points if n_points is not None else (len(ligne) - 15) // 2

        V = ligne[:n]
        I = ligne[n : 2 * n]

        # Récupération des 4 derniers éléments de la ligne complète
        param_physiques = ligne[-9:]

        if idx < 5:
            if len(ligne) >= (2 * n) + 4:
                T, _, N_A, N_t, mu_h, mu_n, _, _, _ = param_physiques
                # Label combinant le numéro de simulation et les paramètres physiques
                label_courbe = (
                    f"Sim {idx+1} ($T$={T:.0f}K, "
                    f"$N_A$={N_A:.1e}, "
                    f"$N_t$={N_t:.1e}, "
                    f"$\\mu_h$={mu_h:.1f}, "
                    f"$\\mu_n$={mu_n:.1f})"
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


plot_iv_curves(r"./csv/iv_curve_processed.csv")
# verifier_coherence_csv(r"./csv/iv_curve.csv")
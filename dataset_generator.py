import pandas as pd

df = pd.read_csv(r"./csv/iv_curve.csv")

# 2. Définir les colonnes clés et les colonnes à déployer
colonnes_cles = ['N_A', 'N_t', 'mu_h']

# Récupérer automatiquement toutes les autres colonnes à déployer (I1..I85, Voc, Jsc, etc.)
# On exclut simplement les 3 clés du reste du tableau
colonnes_a_deployer = [col for col in df.columns if col not in colonnes_cles]

# 3. Filtrer pour ne garder QUE les groupes qui ont des doublons
# Si un groupe est unique, il n'a pas besoin d'être numéroté _1, _2...
df_doublons = df[df.duplicated(subset=colonnes_cles, keep=False)].copy()

# 4. Créer le compteur de ligne pour chaque groupe (le suffixe _1, _2, etc.)
# 'cumcount() + 1' va donner 1 pour la première occurrence, 2 pour la deuxième, etc.
df_doublons['suffixe'] = df_doublons.groupby(colonnes_cles).cumcount() + 1

# 5. Pivoter le tableau
# On passe d'un format long (lignes) à un format large (colonnes)
df_pivote = df_doublons.pivot(
    index=colonnes_cles, 
    columns='suffixe', 
    values=colonnes_a_deployer
)

# 6. Nettoyer les noms des colonnes
# Après le pivot, Pandas crée un double niveau de colonnes (ex: ('Voc', 1)).
# Ce code aplatit cela en 'Voc_1', 'I1_1', etc.
df_pivote.columns = [f"{col[0]}_{col[1]}" for col in df_pivote.columns]

# 7. Réindexer pour que les clés redeviennent des colonnes normales et non des index
df_final = df_pivote.reset_index()

# 8. Sauvegarder le résultat
df_final.to_csv(r'./csv/dataset.csv', index=False, sep=',')

print(f"Opération réussie. Le fichier final contient {len(df_final)} lignes uniques.")
print(f"Colonnes générées : {list(df_final.columns[:10])} ... [coupé pour affichage]")
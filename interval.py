def format_sci(value: float) -> str:
    """Formate un float en notation scientifique style SCAPS (ex: 5.000E+14)"""
    formatted = f"{value:.3E}"
    # Normalise l'exposant : E+4 → E+04, E-4 → E-04
    mantissa, exp = formatted.split("E")
    sign = exp[0]
    digits = exp[1:].zfill(2)
    return f"{mantissa}E{sign}{digits}"


def split_interval(from_val: float, to_val: float, steps: int, n: int) -> list[dict]:
    """
    Découpe un intervalle [from_val, to_val] en n sous-intervalles
    sans chevauchement de bornes (chaque point n'est simulé qu'une fois).

    Contrainte : chaque sous-intervalle doit avoir au minimum 2 steps.
    Si n est trop grand pour satisfaire cette contrainte, n est réduit.

    Args:
        from_val : valeur de départ
        to_val   : valeur de fin
        steps    : nombre de steps total
        n        : nombre de sous-intervalles souhaité (= nb de cœurs)

    Returns:
        Liste de dicts {'from', 'to', 'steps'} pour chaque sous-intervalle
    """

    # Contrainte : chaque sous-intervalle doit avoir au moins 2 steps
    max_n = steps // 2
    if max_n < 1:
        raise ValueError(
            f"Impossible de créer des sous-intervalles : steps={steps} doit être >= 2."
        )
    if n > max_n:
        print(f"[Warning] n={n} réduit à {max_n} pour garantir >= 2 steps par sous-intervalle.")
        n = max_n

    # Taille d'un step en unité réelle
    step_size = (to_val - from_val) / (steps - 1)

    # Répartition des steps en n parts aussi égales que possible
    base_steps = steps // n
    remainder  = steps % n

    intervals = []
    current_from = from_val

    for i in range(n):
        sub_steps = base_steps + (1 if i < remainder else 0)

        # CORRIGÉ : bornes incluses → (sub_steps - 1) pas entre from et to
        sub_to = current_from + (sub_steps - 1) * step_size

        # Arrondi propre sur le dernier intervalle (évite les flottants résiduels)
        if i == n - 1:
            sub_to = to_val

        intervals.append({
            "from":  format_sci(current_from),
            "to":    format_sci(sub_to),
            "steps": sub_steps
        })

        # CORRIGÉ : le sous-intervalle suivant commence un step APRÈS la borne de fin
        current_from = sub_to + step_size

    # Assertion de sécurité : vérifie l'absence de chevauchement
    froms = [iv["from"] for iv in intervals]
    tos   = [iv["to"]   for iv in intervals]
    all_bounds = froms + tos
    assert len(all_bounds) == len(set(all_bounds)), \
        "[split_interval] Chevauchement détecté entre sous-intervalles !"

    return intervals


def chunk_intervals(intervals: list, n: int) -> list[list]:
    """
    Sépare une liste d'intervalles en 'n' sous-listes de taille équitable.
    """
    total_elements = len(intervals)
    if n > total_elements:
        print(f"[Warning] Impossible de diviser en {n} blocs car il n'y a que {total_elements} éléments. Réduction à {total_elements} blocs.")
        n = total_elements

    # Calcul de la taille de base de chaque bloc et du reste
    base_size = total_elements // n
    remainder = total_elements % n

    chunks = []
    start_idx = 0
    
    for i in range(n):
        # On distribue le reste équitablement (+1 élément pour les premiers blocs si nécessaire)
        current_size = base_size + (1 if i < remainder else 0)
        end_idx = start_idx + current_size
        
        # On extrait la sous-liste
        chunks.append(intervals[start_idx:end_idx])
        start_idx = end_idx
        
    return chunks
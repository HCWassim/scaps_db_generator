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
    Découpe un intervalle [from_val, to_val] en n sous-intervalles.
    
    Contrainte : chaque sous-intervalle doit avoir au minimum 2 steps.
    Si n est trop grand pour satisfaire cette contrainte, n est réduit automatiquement.
    
    Args:
        from_val : valeur de départ
        to_val   : valeur de fin
        steps    : nombre de steps total
        n        : nombre de sous-intervalles souhaité
    
    Returns:
        Liste de dicts avec les clés 'from', 'to', 'steps' pour chaque sous-intervalle
    """
    # Contrainte : chaque sous-intervalle doit avoir au moins 2 steps
    # => n ne peut pas dépasser steps // 2
    max_n = steps // 2
    if max_n < 1:
        raise ValueError(f"Impossible de créer des sous-intervalles : steps={steps} doit être >= 2.")
    
    if n > max_n:
        print(f"[Warning] n={n} réduit à {max_n} pour garantir >= 2 steps par sous-intervalle.")
        n = max_n

    # Répartition des steps en n parts aussi égales que possible
    # Les "steps restants" sont distribués 1 par 1 sur les premiers sous-intervalles
    base_steps = steps // n
    remainder  = steps % n

    intervals = []
    step_size = (to_val - from_val) / steps  # taille d'un step en unité réelle

    current_from = from_val

    for i in range(n):
        sub_steps = base_steps + (1 if i < remainder else 0)
        sub_to    = current_from + sub_steps * step_size

        # Arrondi propre pour le dernier intervalle (évite les flottants résiduels)
        if i == n - 1:
            sub_to = to_val

        intervals.append({
            "from":  format_sci(current_from),
            "to":    format_sci(sub_to),
            "steps": sub_steps
        })
        current_from = sub_to

    return intervals
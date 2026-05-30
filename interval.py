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
    Découpe [from_val, to_val] en n sous-intervalles ancrés sur la grille
    entière de l'intervalle original.

    Les bornes sont calculées comme from_val + idx * step_size,
    ce qui garantit que les valeurs générées tombent exactement sur
    les mêmes points que la simulation originale.

    Contrainte : chaque sous-intervalle a au minimum 2 steps.
    """
    max_n = steps // 2
    if max_n < 1:
        raise ValueError(f"Impossible : steps={steps} doit être >= 2.")

    if n > max_n:
        print(f"[Warning] n={n} réduit à {max_n} pour garantir >= 2 steps par sous-intervalle.")
        n = max_n

    base_steps = steps // n
    remainder  = steps % n
    step_size  = (to_val - from_val) / steps  # pas de la grille de référence

    # Indices de rupture sur la grille entière (valeurs entières)
    breakpoints = [0]
    for i in range(n):
        sub_steps = base_steps + (1 if i < remainder else 0)
        breakpoints.append(breakpoints[-1] + sub_steps)
    # breakpoints[-1] == steps par construction

    intervals = []
    for i in range(n):
        idx_from  = breakpoints[i]
        idx_to    = breakpoints[i + 1]
        sub_steps = idx_to - idx_from

        # Bornes ancrées sur la grille — même calcul que SCAPS
        sub_from = from_val + idx_from * step_size
        sub_to   = from_val + idx_to   * step_size

        # Épingle exacte les extrémités globales (évite tout résidu flottant)
        if idx_from == 0:
            sub_from = from_val
        if idx_to == steps:
            sub_to = to_val

        intervals.append({
            "from":  format_sci(sub_from),
            "to":    format_sci(sub_to),
            "steps": sub_steps
        })

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
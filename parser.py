import re
from typing import Tuple


def parse_iv_file(
    filepath: str,
    save_voltages: bool = True,
    save_currents: bool = True,
) -> list[list[str]]:
    iv_re = re.compile(
        r'^\s*(-?\d+\.\d+(?:[eE][+-]?\d+)?)'
        r'[\t ]+'
        r'(-?\d+\.\d+(?:[eE][+-]?\d+)?)'
    )
    param_re = {
        'Voc':   re.compile(r'^Voc\s*=\s*(-?\d+\.\d+(?:[eE][+-]?\d+)?)'),
        'Jsc':   re.compile(r'^Jsc\s*=\s*(-?\d+\.\d+(?:[eE][+-]?\d+)?)'),
        'FF':    re.compile(r'^FF\s*=\s*(-?\d+\.\d+(?:[eE][+-]?\d+)?)'),
        'eta':   re.compile(r'^eta\s*=\s*(-?\d+\.\d+(?:[eE][+-]?\d+)?)'),
        'V_MPP': re.compile(r'^V_MPP\s*=\s*(-?\d+\.\d+(?:[eE][+-]?\d+)?)'),
        'J_MPP': re.compile(r'^J_MPP\s*=\s*(-?\d+\.\d+(?:[eE][+-]?\d+)?)'),
    }
    header_re      = re.compile(r'^\s*v\(V\)[\t ]')
    temperature_re = re.compile(r'^Temperature\s+(-?\d+\.\d+(?:[eE][+-]?\d+)?)\s+K')
    batch_param_re = re.compile(r'^(.+?)\s*:\s*(-?\d+\.\d+(?:[eE][+-]?\d+)?)\s*$')
    batch_section_re = re.compile(r'^\*\*Batch parameters\*\*')

    results = []

    # Variables "tampon" : remplies AVANT l'en-tête du tableau
    pending_temperature: str       = ''
    pending_batch_params: list[str] = []
    in_batch_section = False

    # Variables "courantes" : transférées depuis le tampon au moment de l'en-tête
    current_voltages: list[str]    = []
    current_currents: list[str]    = []
    current_params: dict[str, str] = {}
    current_temperature: str       = ''
    current_batch_params: list[str] = []
    in_iv_table = False

    def flush():
        if current_voltages and len(current_params) == 6:
            row = (
                (current_voltages if save_voltages else [])
                + (current_currents if save_currents else [])
                + [current_params[k] for k in ('Voc', 'Jsc', 'FF', 'eta', 'V_MPP', 'J_MPP')]
                + [current_temperature]
                + current_batch_params
            )
            results.append(row)

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            stripped = line.strip()

            # Température → tampon
            m = temperature_re.match(stripped)
            if m:
                pending_temperature = m.group(1)
                continue

            # Début section batch
            if batch_section_re.match(stripped):
                in_batch_section = True
                pending_batch_params = []   # reset du tampon à chaque nouvelle section
                continue

            # Lecture batch params → tampon
            if in_batch_section:
                if stripped == '':
                    in_batch_section = False
                    continue
                m = batch_param_re.match(stripped)
                if m:
                    pending_batch_params.append(m.group(2))
                    continue

            # En-tête tableau : flush simulation précédente,
            # puis transfert du tampon vers les variables courantes
            if header_re.match(line):
                flush()
                current_voltages     = []
                current_currents     = []
                current_params       = {}
                current_temperature  = pending_temperature
                current_batch_params = pending_batch_params
                pending_temperature  = ''
                pending_batch_params = []
                in_iv_table          = True
                in_batch_section     = False
                continue

            if in_iv_table:
                if stripped == '':
                    continue
                m = iv_re.match(line)
                if m:
                    current_voltages.append(m.group(1))
                    current_currents.append(m.group(2))
                    continue
                else:
                    in_iv_table = False

            for key, pattern in param_re.items():
                m = pattern.match(stripped)
                if m:
                    current_params[key] = m.group(1)
                    break

    flush()
    return results


def parse_qe_file(filepath: str) -> list[list[str]]:
    """
    Parse a SCAPS .qe batch file.

    Returns a list of rows, one per simulation. Each row is:
        [lambda_1, ..., lambda_N, QE_1, ..., QE_N, Temperature,
         batch_param_1, ..., batch_param_M]

    All values are kept as strings (no float conversion).

    Parameters
    ----------
    filepath : str
        Path to the .qe batch file.
    """
    # Ligne de données : "   300.000000   1.358917e+01   4.133257"
    # On ne garde que lambda (col 1) et QE (col 2), on ignore l'énergie (col 3)
    qe_re = re.compile(
        r'^\s*(\d+\.\d+(?:[eE][+-]?\d+)?)'          # lambda
        r'[\t ]+'
        r'(-?\d+\.\d+(?:[eE][+-]?\d+)?)'             # QE
        r'[\t ]+'
        r'-?\d+\.\d+(?:[eE][+-]?\d+)?'               # énergie (ignorée)
        r'\s*$'
    )
    header_re        = re.compile(r'^\s*lambda\(nm\)[\t ]')
    temperature_re   = re.compile(r'^Temperature\s+(-?\d+\.\d+(?:[eE][+-]?\d+)?)\s+K')
    batch_section_re = re.compile(r'^\*\*Batch parameters\*\*')
    batch_param_re   = re.compile(r'^(.+?)\s*:\s*(-?\d+\.\d+(?:[eE][+-]?\d+)?)\s*$')

    results = []

    # Tampons : remplis AVANT l'en-tête du tableau
    pending_temperature: str        = ''
    pending_batch_params: list[str] = []
    in_batch_section = False

    # Variables courantes : transférées depuis le tampon au moment de l'en-tête
    current_lambdas: list[str] = []
    current_qes: list[str]     = []
    current_temperature: str        = ''
    current_batch_params: list[str] = []
    in_qe_table = False

    def flush():
        if current_lambdas:
            row = (
                current_lambdas
                + current_qes
                + [current_temperature]
                + current_batch_params
            )
            results.append(row)

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            stripped = line.strip()

            # Température → tampon
            m = temperature_re.match(stripped)
            if m:
                pending_temperature = m.group(1)
                continue

            # Début section batch
            if batch_section_re.match(stripped):
                in_batch_section = True
                pending_batch_params = []
                continue

            # Lecture batch params → tampon
            if in_batch_section:
                if stripped == '':
                    in_batch_section = False
                    continue
                m = batch_param_re.match(stripped)
                if m:
                    pending_batch_params.append(m.group(2))
                    continue

            # En-tête tableau : flush simulation précédente,
            # puis transfert tampon → courant
            if header_re.match(line):
                flush()
                current_lambdas      = []
                current_qes          = []
                current_temperature  = pending_temperature
                current_batch_params = pending_batch_params
                pending_temperature  = ''
                pending_batch_params = []
                in_qe_table          = True
                in_batch_section     = False
                continue

            # Données QE
            if in_qe_table:
                if stripped == '':
                    continue
                m = qe_re.match(line)
                if m:
                    current_lambdas.append(m.group(1))
                    current_qes.append(m.group(2))
                    continue
                else:
                    in_qe_table = False

    flush()
    return results


# def parse_def_file(filepath: str) -> Tuple[list[str], list[str]]:
#     """
#     Parse a SCAPS .def problem definition file.

#     Returns
#     -------
#     names : list[str]
#         Parameter names of the form "<context>_<param>"
#         e.g. "CIGS graded_Eg_1", "CIGS graded_Eg_2", "CdS_d", ...

#         For multi-value (graded) lines, two entries are created:
#             "<context>_<param>_1"  (6th numerical value, pure-A endpoint)
#             "<context>_<param>_2"  (7th numerical value, pure-B endpoint)
#         If both values are identical, only one entry "<context>_<param>" is added.

#         For scalar lines a single entry "<context>_<param>" is added.

#     values : list[str]
#         Corresponding values (strings, no float conversion).
#     """

#     # ------------------------------------------------------------------
#     # Helpers
#     # ------------------------------------------------------------------
#     NUM = r'-?\d+[\d.]*(?:[eE][+-]?\d+)?'          # any float/sci number

#     # Multi-value line: key + TAB/spaces + exactly 7 floats + 2 int flags
#     # Groups: (1) key, then 7 captured numbers, then 2 flag ints
#     multi_re = re.compile(
#         r'^([A-Za-z][^:\n]*?)\s*:\s+'              # key
#         r'(' + NUM + r')'                           # val 1
#         r'(?:[\t ]+(' + NUM + r')){1}'              # val 2
#         r'(?:[\t ]+(' + NUM + r')){1}'              # val 3
#         r'(?:[\t ]+(' + NUM + r')){1}'              # val 4
#         r'(?:[\t ]+(' + NUM + r')){1}'              # val 5
#         r'(?:[\t ]+(' + NUM + r')){1}'              # val 6  ← keep
#         r'(?:[\t ]+(' + NUM + r')){1}'              # val 7  ← keep
#         r'(?:[\t ]+\d+){2}'                         # 2 integer flags
#         r'(?:\s+\[.*?\])?'                          # optional unit
#         r'\s*$'
#     )

#     # Scalar line: key : single_value [optional unit / comment]
#     scalar_re = re.compile(
#         r'^([A-Za-z][^:\n]*?)\s*:\s*'
#         r'(' + NUM + r')'
#         r'(?:\s+\[.*?\])?'
#         r'(?:\s+.*)?$'
#     )

#     # Lines / blocks to skip entirely
#     skip_patterns = [
#         re.compile(p, re.IGNORECASE) for p in [
#             r'^>',
#             r'^\s*$',
#             r'^convergence\s*$',
#             r'^back contact\s*$',
#             r'^front contact\s*$',
#             r'^layer\s*$',
#             r'^working point\s*$',
#             r'^interface properties\s*$',
#             r'^interface recombination\s*$',
#             r'^srhrecombination\s*$',
#             r'^profile\s*:',
#             r'^leveltype\s*:',
#             r'^energy distribution\s*:',
#             r'^absorptionmodel',
#             r'^absorption model',
#             r'^absorption pure',
#             r'^pure B material',
#             r'^A\s*:',
#             r'^B\s*:',
#         ]
#     ]

#     # Block / context markers
#     layer_block_re   = re.compile(r'^layer\s*$')
#     srh_block_re     = re.compile(r'^srhrecombination\s*$')
#     iface_prop_re    = re.compile(r'^interface properties\s*$')
#     iface_rec_re     = re.compile(r'^interface recombination\s*$')
#     back_contact_re  = re.compile(r'^back contact\s*$')
#     front_contact_re = re.compile(r'^front contact\s*$')
#     working_point_re = re.compile(r'^working point\s*$')
#     layer_name_re    = re.compile(r'^name\s*:\s*(.+)')
#     iface_name_re    = re.compile(r'^interfacename\s*:\s*(.*)')

#     # ------------------------------------------------------------------
#     # State
#     # ------------------------------------------------------------------
#     names:  list[str] = []
#     values: list[str] = []

#     context       = 'global'
#     current_layer = ''
#     defect_count  = 0
#     iface_count   = 0

#     def add(param: str, value: str):
#         names.append(f"{context}_{param}")
#         values.append(value)

#     def should_skip(s: str) -> bool:
#         return any(p.match(s) for p in skip_patterns)

#     # ------------------------------------------------------------------
#     # Parse
#     # ------------------------------------------------------------------
#     with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
#         lines = f.readlines()

#     for raw in lines:
#         stripped = raw.strip()

#         # ---- block transitions -------------------------------------------
#         if layer_block_re.match(stripped):
#             defect_count = 0
#             context = '__pending_layer__'
#             continue

#         if srh_block_re.match(stripped):
#             defect_count += 1
#             context = f"{current_layer}_defect{defect_count}"
#             continue

#         if iface_prop_re.match(stripped):
#             iface_count += 1
#             context = f"interface{iface_count}"
#             continue

#         if iface_rec_re.match(stripped):
#             context = f"interface{iface_count}_recombination"
#             continue

#         if back_contact_re.match(stripped):
#             context = 'back_contact'
#             continue

#         if front_contact_re.match(stripped):
#             context = 'front_contact'
#             continue

#         if working_point_re.match(stripped):
#             context = 'working_point'
#             continue

#         # ---- layer / interface names ------------------------------------
#         m = layer_name_re.match(stripped)
#         if m and context == '__pending_layer__':
#             current_layer = m.group(1).strip()
#             context = current_layer
#             continue

#         m = iface_name_re.match(stripped)
#         if m:
#             label = m.group(1).strip()
#             base  = f"interface{iface_count}"
#             context = f"{base}_{label}" if label else base
#             continue

#         # ---- skip unwanted lines ----------------------------------------
#         if should_skip(stripped):
#             continue

#         # ---- multi-value (graded) line — keep values 6 and 7 -----------
#         m = multi_re.match(stripped)
#         if m:
#             key  = m.group(1).strip()
#             val6 = m.group(6)
#             val7 = m.group(7)
#             if val6 == val7:
#                 # No grading: both endpoints identical → single entry
#                 add(key, val6)
#             else:
#                 add(f"{key}_1", val6)
#                 add(f"{key}_2", val7)
#             continue

#         # ---- scalar line ------------------------------------------------
#         m = scalar_re.match(stripped)
#         if m:
#             add(m.group(1).strip(), m.group(2))
#             continue

#     return names, values


def parse_def_file(filepath: str) -> Tuple[list[str], list[str]]:
    """
    Parse a SCAPS .def problem definition file.

    Returns
    -------
    names : list[str]
        Parameter names of the form "<context>_<param>"
        For graded multi-value lines where val6 != val7:
            "<context>_<param>_1"  (6th value)
            "<context>_<param>_2"  (7th value)
        If both are identical, a single "<context>_<param>" is added.
    values : list[str]
        Corresponding values (strings, no float conversion).
    """

    NUM = r'-?\d+[\d.]*(?:[eE][+-]?\d+)?'
    NUM_re = re.compile(NUM)

    # Détecte une ligne multi-valeurs : clé + 7 floats + 2 flags entiers
    multi_detect_re = re.compile(
        r'^([A-Za-z][^:\n]*?)\s*:\s+'
        r'(?:' + NUM + r'[\t ]+){6}'
        + NUM +
        r'(?:[\t ]+\d+){2}'
        r'(?:\s+\[.*?\])?\s*$'
    )

    # Scalaire : clé + une seule valeur
    scalar_re = re.compile(
        r'^([A-Za-z][^:\n]*?)\s*:\s*'
        r'(' + NUM + r')'
        r'(?:\s+\[.*?\])?'
        r'(?:\s+.*)?$'
    )

    skip_patterns = [
        re.compile(p, re.IGNORECASE) for p in [
            r'^>',
            r'^\s*$',
            r'^convergence\s*$',
            r'^back contact\s*$',
            r'^front contact\s*$',
            r'^layer\s*$',
            r'^working point\s*$',
            r'^interface properties\s*$',
            r'^interface recombination\s*$',
            r'^srhrecombination\s*$',
            r'^profile\s*:',
            r'^leveltype\s*:',
            r'^energy distribution\s*:',
            r'^absorptionmodel',
            r'^absorption model',
            r'^absorption pure',
            r'^pure B material',
            r'^A\s*:',
            r'^B\s*:',
        ]
    ]

    layer_block_re   = re.compile(r'^layer\s*$')
    srh_block_re     = re.compile(r'^srhrecombination\s*$')
    iface_prop_re    = re.compile(r'^interface properties\s*$')
    iface_rec_re     = re.compile(r'^interface recombination\s*$')
    back_contact_re  = re.compile(r'^back contact\s*$')
    front_contact_re = re.compile(r'^front contact\s*$')
    working_point_re = re.compile(r'^working point\s*$')
    layer_name_re    = re.compile(r'^name\s*:\s*(.+)')
    iface_name_re    = re.compile(r'^interfacename\s*:\s*(.*)')

    names:  list[str] = []
    values: list[str] = []

    context       = 'global'
    current_layer = ''
    defect_count  = 0
    iface_count   = 0

    def add(param: str, value: str):
        names.append(f"{context}_{param}")
        values.append(value)

    def should_skip(s: str) -> bool:
        return any(p.match(s) for p in skip_patterns)

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    for raw in lines:
        stripped = raw.strip()

        if layer_block_re.match(stripped):
            defect_count = 0
            context = '__pending_layer__'
            continue

        if srh_block_re.match(stripped):
            defect_count += 1
            context = f"{current_layer}_defect{defect_count}"
            continue

        if iface_prop_re.match(stripped):
            iface_count += 1
            context = f"interface{iface_count}"
            continue

        if iface_rec_re.match(stripped):
            context = f"interface{iface_count}_recombination"
            continue

        if back_contact_re.match(stripped):
            context = 'back_contact'
            continue

        if front_contact_re.match(stripped):
            context = 'front_contact'
            continue

        if working_point_re.match(stripped):
            context = 'working_point'
            continue

        m = layer_name_re.match(stripped)
        if m and context == '__pending_layer__':
            current_layer = m.group(1).strip()
            context = current_layer
            continue

        m = iface_name_re.match(stripped)
        if m:
            label = m.group(1).strip()
            base  = f"interface{iface_count}"
            context = f"{base}_{label}" if label else base
            continue

        if should_skip(stripped):
            continue

        # ---- multi-value (graded) line ----------------------------------
        m = multi_detect_re.match(stripped)
        if m:
            key = m.group(1).strip()
            after_colon = stripped[stripped.index(':') + 1:]
            all_vals = NUM_re.findall(after_colon)
            val6 = all_vals[5]  # 6ème valeur (index 5)
            val7 = all_vals[6]  # 7ème valeur (index 6)
            if val6 == val7:
                add(key, val6)
            else:
                add(f"{key}_1", val6)
                add(f"{key}_2", val7)
            continue

        # ---- scalar line ------------------------------------------------
        m = scalar_re.match(stripped)
        if m:
            add(m.group(1).strip(), m.group(2))
            continue

    return names, values


# names, values = parse_def_file(r"./baseline/CIGS_graded_v2.def")

# for i in range(len(names)):
#     print(f"{names[i]} = {values[i]}")
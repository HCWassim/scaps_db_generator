import re

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
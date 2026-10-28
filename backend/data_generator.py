"""Geração de notas fiscais simuladas: um conjunto que segue a Lei de Benford
e outro que simula notas fiscais alteradas/fabricadas manualmente."""

import numpy as np
import pandas as pd

from .benford import BENFORD_EXPECTED

_SCALES = [10, 100, 1000, 10000]
# escala 10 tem peso baixo: valores muito pequenos arredondados a 2 casas decimais
# têm poucos dígitos significativos, o que distorce artificialmente a análise do 3º/4º dígito
_SCALE_WEIGHTS = [0.05, 0.30, 0.40, 0.25]


def generate_compliant_invoices(n: int = 800, seed: int = 42) -> pd.DataFrame:
    """Gera notas fiscais cujos valores seguem a Lei de Benford (baixo desvio)."""
    rng = np.random.default_rng(seed)
    digits = np.arange(1, 10)
    probs = np.array([BENFORD_EXPECTED[d] for d in digits])

    rows = []
    for i in range(n):
        d = rng.choice(digits, p=probs)
        scale = rng.choice(_SCALES, p=_SCALE_WEIGHTS)
        frac = rng.random()
        valor = round((d + frac) * scale / 10, 2)
        rows.append({"numero_nf": f"NF-{10000 + i}", "valor": valor})

    return pd.DataFrame(rows)


def generate_altered_invoices(n: int = 800, seed: int = 7) -> pd.DataFrame:
    """Gera notas fiscais com indícios de manipulação: distribuição de
    primeiro dígito quase uniforme, valores redondos e repetição de valores —
    padrões típicos de números fabricados manualmente."""
    rng = np.random.default_rng(seed)
    digits = np.arange(1, 10)
    # distribuição quase uniforme, fugindo do padrão natural da Lei de Benford
    probs = np.array([0.07, 0.09, 0.10, 0.11, 0.13, 0.13, 0.12, 0.13, 0.12])
    probs = probs / probs.sum()

    rows = []
    used_values = []
    for i in range(n):
        if used_values and rng.random() < 0.18:
            valor = float(rng.choice(used_values))
        else:
            d = rng.choice(digits, p=probs)
            scale = rng.choice(_SCALES, p=_SCALE_WEIGHTS)
            frac = rng.random()
            valor = round((d + frac) * scale / 10, 2)
            if rng.random() < 0.35:
                valor = round(valor) + rng.choice([0.0, 0.90, 0.99])

        used_values.append(valor)
        rows.append({"numero_nf": f"NF-{20000 + i}", "valor": round(valor, 2)})

    return pd.DataFrame(rows)

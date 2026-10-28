"""Lógica da Lei de Benford: distribuição esperada, extração de dígitos e métricas de desvio.

Suporta análise do 1º ao 4º dígito significativo, conforme a generalização
da Lei de Benford para múltiplas posições de dígito."""

import numpy as np

BENFORD_EXPECTED = {d: np.log10(1 + 1 / d) for d in range(1, 10)}

MAX_POSITION = 4


def _normalize_mantissa(value: float) -> float:
    """Normaliza um valor para a faixa [1, 10), preservando seus dígitos significativos."""
    value = abs(value)
    if value == 0:
        return 0.0
    while value < 1:
        value *= 10
    while value >= 10:
        value /= 10
    return value


def digit_at_position(value: float, position: int = 1) -> int:
    """Retorna o dígito significativo na posição indicada (1 = primeiro dígito,
    2 = segundo dígito, e assim por diante)."""
    m = _normalize_mantissa(value)
    if m == 0:
        return 0
    # round mitiga erro de ponto flutuante (ex.: 2.9999999998 em vez de 3.0)
    scaled = round(m * 10 ** (position - 1), 9)
    return int(scaled) % 10


def first_digit(value: float) -> int:
    """Retorna o primeiro dígito significativo de um número."""
    return digit_at_position(value, 1)


def second_digit(value: float) -> int:
    """Retorna o segundo dígito significativo de um número."""
    return digit_at_position(value, 2)


def digit_distribution(values, position: int = 1):
    """Conta a frequência do dígito na posição indicada (1º a 4º) de uma lista/série de valores."""
    digit_range = range(1, 10) if position == 1 else range(0, 10)
    counts = {d: 0 for d in digit_range}
    for v in values:
        d = digit_at_position(v, position)
        if d in counts:
            counts[d] += 1
    total = sum(counts.values())
    observed_pct = {d: (counts[d] / total * 100 if total else 0) for d in digit_range}
    return counts, observed_pct


def expected_distribution(position: int = 1):
    """Distribuição percentual esperada pela Lei de Benford para a posição de dígito indicada.

    Posição 1: dígitos 1-9. Posições 2-4: dígitos 0-9, somando a probabilidade
    sobre todas as combinações possíveis dos dígitos anteriores.
    """
    if position == 1:
        return {d: BENFORD_EXPECTED[d] * 100 for d in range(1, 10)}

    m_start = 10 ** (position - 2)
    m_end = 10 ** (position - 1) - 1

    expected = {}
    for d in range(0, 10):
        prob = sum(np.log10(1 + 1 / (10 * m + d)) for m in range(m_start, m_end + 1))
        expected[d] = prob * 100
    return expected


def deviation_metrics(observed_pct, expected_pct):
    """Calcula desvio padrão, desvio absoluto médio (MAD) e qui-quadrado entre observado e esperado."""
    digits = sorted(expected_pct.keys())
    diffs = [observed_pct[d] - expected_pct[d] for d in digits]
    std_dev = float(np.std(diffs))
    mad = float(np.mean(np.abs(diffs)))
    chi_square = sum(
        ((observed_pct[d] - expected_pct[d]) ** 2) / expected_pct[d] for d in digits
    )
    return {"std_dev": std_dev, "mad": mad, "chi_square": chi_square}

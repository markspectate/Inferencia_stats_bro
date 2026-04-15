from __future__ import annotations

import math
from typing import Sequence


def normalizar_muestra(muestra: Sequence[float], minimo: int = 2) -> list[float]:
    try:
        valores = [float(valor) for valor in muestra]
    except (TypeError, ValueError) as exc:
        raise ValueError("La muestra contiene valores no numericos.") from exc

    if len(valores) < minimo:
        raise ValueError(f"La muestra debe tener al menos {minimo} observaciones.")

    if any(not math.isfinite(valor) for valor in valores):
        raise ValueError("La muestra no puede contener valores infinitos o indefinidos.")

    return valores


def validar_confianza(confianza: float) -> float:
    try:
        valor = float(confianza)
    except (TypeError, ValueError) as exc:
        raise ValueError("El nivel de confianza debe ser numerico.") from exc

    if not math.isfinite(valor):
        raise ValueError("El nivel de confianza debe ser un numero finito.")

    if not (0 < valor < 1):
        raise ValueError("El nivel de confianza debe estar entre 0 y 1.")

    return valor

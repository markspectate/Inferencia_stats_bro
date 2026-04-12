from dataclasses import dataclass
import math
from typing import Sequence

from scipy import stats


@dataclass(frozen=True)
class ResultadoICMedia:
    muestra: list[float]
    n: int
    gl: int
    media: float
    desvio: float
    confianza: float
    alpha: float
    t_critico: float
    error_estandar: float
    ic_inf: float
    ic_sup: float


def calcular_ic_media(muestra: Sequence[float], confianza: float) -> ResultadoICMedia:
    n = len(muestra)
    gl = n - 1
    media = stats.tmean(muestra)
    desvio = stats.tstd(muestra)
    alpha = 1 - confianza
    t_critico = stats.t.ppf(1 - alpha / 2, gl)

    error_estandar = desvio / math.sqrt(n)
    ic_inf = media - t_critico * error_estandar
    ic_sup = media + t_critico * error_estandar

    return ResultadoICMedia(
        muestra=list(muestra),
        n=n,
        gl=gl,
        media=media,
        desvio=desvio,
        confianza=confianza,
        alpha=alpha,
        t_critico=t_critico,
        error_estandar=error_estandar,
        ic_inf=ic_inf,
        ic_sup=ic_sup,
    )


def formatear_resultado_ic_media(resultado: ResultadoICMedia) -> str:
    texto = []
    texto.append("MEDIA EN POBLACIONES NORMALES CON VARIANZA DESCONOCIDA")
    texto.append("-" * 70)
    texto.append(f"Muestra: {resultado.muestra}")
    texto.append(f"n = {resultado.n}")
    texto.append(f"g.l. = {resultado.gl}")
    texto.append(f"Media muestral = {resultado.media:.6f}")
    texto.append(f"Desvio muestral = {resultado.desvio:.6f}")
    texto.append(f"Nivel de confianza = {resultado.confianza:.4f}")
    texto.append(f"Alpha = {resultado.alpha:.4f}")
    texto.append(f"t critico = {resultado.t_critico:.6f}")
    texto.append(f"Error estandar = {resultado.error_estandar:.6f}")
    texto.append("")
    texto.append("Forma del intervalo:")
    texto.append("mu in (x_bar - t * s/sqrt(n), x_bar + t * s/sqrt(n))")
    texto.append(
        f"mu in ({resultado.media:.6f} - {resultado.t_critico:.6f} * "
        f"{resultado.desvio:.6f}/{math.sqrt(resultado.n):.6f}, "
        f"{resultado.media:.6f} + {resultado.t_critico:.6f} * "
        f"{resultado.desvio:.6f}/{math.sqrt(resultado.n):.6f})"
    )
    texto.append("")
    texto.append(f"IC para mu = ({resultado.ic_inf:.6f}, {resultado.ic_sup:.6f})")

    return "\n".join(texto)


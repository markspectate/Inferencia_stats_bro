from dataclasses import dataclass
import math
from typing import Sequence

from scipy import stats

from calculos.validaciones import normalizar_muestra, validar_confianza


@dataclass(frozen=True)
class ResultadoICVarianza:
    muestra: list[float]
    n: int
    gl: int
    media: float
    desvio: float
    varianza_muestral: float
    confianza: float
    alpha: float
    chi2_izq: float
    chi2_der: float
    ic_var_inf: float
    ic_var_sup: float
    ic_desv_inf: float
    ic_desv_sup: float


def calcular_ic_varianza(muestra: Sequence[float], confianza: float) -> ResultadoICVarianza:
    valores = normalizar_muestra(muestra)
    confianza = validar_confianza(confianza)

    n = len(valores)
    gl = n - 1
    media = stats.tmean(valores)
    desvio = stats.tstd(valores)
    varianza_muestral = stats.tvar(valores)
    alpha = 1 - confianza

    chi2_izq = stats.chi2.ppf(alpha / 2, df=gl)
    chi2_der = stats.chi2.ppf(1 - alpha / 2, df=gl)

    ic_var_inf = (gl * varianza_muestral) / chi2_der
    ic_var_sup = (gl * varianza_muestral) / chi2_izq
    ic_desv_inf = math.sqrt(ic_var_inf)
    ic_desv_sup = math.sqrt(ic_var_sup)

    return ResultadoICVarianza(
        muestra=valores,
        n=n,
        gl=gl,
        media=media,
        desvio=desvio,
        varianza_muestral=varianza_muestral,
        confianza=confianza,
        alpha=alpha,
        chi2_izq=chi2_izq,
        chi2_der=chi2_der,
        ic_var_inf=ic_var_inf,
        ic_var_sup=ic_var_sup,
        ic_desv_inf=ic_desv_inf,
        ic_desv_sup=ic_desv_sup,
    )


def formatear_resultado_ic_varianza(resultado: ResultadoICVarianza) -> str:
    texto = []
    texto.append("VARIANZA EN POBLACIONES NORMALES CON MEDIA DESCONOCIDA")
    texto.append("-" * 70)
    texto.append(f"Muestra: {resultado.muestra}")
    texto.append(f"n = {resultado.n}")
    texto.append(f"g.l. = {resultado.gl}")
    texto.append(f"Media muestral = {resultado.media:.6f}")
    texto.append(f"Varianza muestral = {resultado.varianza_muestral:.6f}")
    texto.append(f"Desvio muestral = {resultado.desvio:.6f}")
    texto.append(f"Nivel de confianza = {resultado.confianza:.4f}")
    texto.append(f"Alpha = {resultado.alpha:.4f}")
    texto.append(f"Chi2 izquierdo = {resultado.chi2_izq:.6f}")
    texto.append(f"Chi2 derecho = {resultado.chi2_der:.6f}")
    texto.append("")
    texto.append("Forma del intervalo:")
    texto.append("sigma^2 in ( (n-1)s^2 / chi2_(1-alpha/2), (n-1)s^2 / chi2_(alpha/2) )")
    texto.append(
        f"sigma^2 in (({resultado.gl} * {resultado.varianza_muestral:.6f}) / "
        f"{resultado.chi2_der:.6f}, ({resultado.gl} * {resultado.varianza_muestral:.6f}) / "
        f"{resultado.chi2_izq:.6f})"
    )
    texto.append("")
    texto.append(f"IC para sigma^2 = ({resultado.ic_var_inf:.6f}, {resultado.ic_var_sup:.6f})")
    texto.append(f"IC para sigma = ({resultado.ic_desv_inf:.6f}, {resultado.ic_desv_sup:.6f})")

    return "\n".join(texto)

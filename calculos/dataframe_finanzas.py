from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from scipy import stats


class DependenciaDataFrameError(RuntimeError):
    """Se dispara cuando faltan librerias para trabajar con DataFrames reales."""


@dataclass(frozen=True)
class MuestraCotizacion:
    ticker: str
    columna: str
    fechas: list[str]
    valores: list[float]
    fecha_inicio: str
    fecha_fin: str
    dias_solicitados: int


@dataclass(frozen=True)
class ResultadoICDataFrame:
    n: int
    gl: int
    media: float
    varianza: float
    desvio: float
    confianza: float
    alpha: float
    t_critico: float
    chi2_izq: float
    chi2_der: float
    ic_media_inf: float
    ic_media_sup: float
    ic_var_inf: float
    ic_var_sup: float
    ic_desv_inf: float
    ic_desv_sup: float


def _importar_librerias_dataframe():
    try:
        import yfinance as yf  # type: ignore
    except ModuleNotFoundError as exc:
        raise DependenciaDataFrameError(
            "Falta la libreria 'yfinance'. Instalala con: pip install yfinance pandas"
        ) from exc

    return yf


def _seleccionar_serie_cierre(df, ticker: str, columna_preferida: str):
    if getattr(df.columns, "nlevels", 1) > 1:
        candidatas = [columna_preferida, "Close", "Adj Close"]
        for nombre in candidatas:
            if (nombre, ticker) in df.columns:
                return df[(nombre, ticker)], nombre

        primer_nivel = set(df.columns.get_level_values(0))
        for nombre in candidatas:
            if nombre in primer_nivel:
                subset = df[nombre]
                if hasattr(subset, "columns") and ticker in subset.columns:
                    return subset[ticker], nombre
                if hasattr(subset, "iloc"):
                    return subset.iloc[:, 0], nombre
        raise ValueError("No se encontró una columna de cierre válida en el DataFrame descargado.")

    candidatas = [columna_preferida, "Close", "Adj Close"]
    for nombre in candidatas:
        if nombre in df.columns:
            return df[nombre], nombre
    raise ValueError("El DataFrame descargado no contiene columnas de cierre esperadas.")


def descargar_muestra_cotizaciones(ticker: str, dias: int, columna: str = "Close") -> MuestraCotizacion:
    yf = _importar_librerias_dataframe()

    ticker_limpio = ticker.strip().upper()
    if not ticker_limpio:
        raise ValueError("Debes indicar un ticker, por ejemplo AAPL.")
    if dias < 2:
        raise ValueError("La cantidad de dias debe ser al menos 2.")

    # Se pide una ventana mayor para cubrir feriados/fines de semana y despues recortar.
    dias_descarga = max(dias * 3, dias + 45)
    df = yf.download(
        ticker_limpio,
        period=f"{dias_descarga}d",
        interval="1d",
        auto_adjust=False,
        progress=False,
    )

    if df is None or df.empty:
        raise ValueError(f"No se pudieron descargar cotizaciones para {ticker_limpio}.")

    serie_base, columna_utilizada = _seleccionar_serie_cierre(df, ticker_limpio, columna)
    serie = serie_base.dropna().tail(dias)
    if len(serie) < 2:
        raise ValueError(
            f"Solo se encontraron {len(serie)} observaciones para {ticker_limpio}; se requieren al menos 2."
        )

    fechas = [idx.strftime("%Y-%m-%d") for idx in serie.index.to_pydatetime()]
    valores = [float(v) for v in serie.tolist()]

    return MuestraCotizacion(
        ticker=ticker_limpio,
        columna=columna_utilizada,
        fechas=fechas,
        valores=valores,
        fecha_inicio=fechas[0],
        fecha_fin=fechas[-1],
        dias_solicitados=dias,
    )


def calcular_ic_desde_muestra(valores: Sequence[float], confianza: float) -> ResultadoICDataFrame:
    n = len(valores)
    if n < 2:
        raise ValueError("La muestra debe tener al menos 2 observaciones.")
    if not (0 < confianza < 1):
        raise ValueError("El nivel de confianza debe estar entre 0 y 1.")

    gl = n - 1
    media = stats.tmean(valores)
    varianza = stats.tvar(valores)
    desvio = stats.tstd(valores)
    alpha = 1 - confianza

    t_critico = stats.t.ppf(1 - alpha / 2, gl)
    error_estandar = desvio / math.sqrt(n)
    ic_media_inf = media - t_critico * error_estandar
    ic_media_sup = media + t_critico * error_estandar

    chi2_izq = stats.chi2.ppf(alpha / 2, df=gl)
    chi2_der = stats.chi2.ppf(1 - alpha / 2, df=gl)
    ic_var_inf = (gl * varianza) / chi2_der
    ic_var_sup = (gl * varianza) / chi2_izq
    ic_desv_inf = math.sqrt(ic_var_inf)
    ic_desv_sup = math.sqrt(ic_var_sup)

    return ResultadoICDataFrame(
        n=n,
        gl=gl,
        media=media,
        varianza=varianza,
        desvio=desvio,
        confianza=confianza,
        alpha=alpha,
        t_critico=t_critico,
        chi2_izq=chi2_izq,
        chi2_der=chi2_der,
        ic_media_inf=ic_media_inf,
        ic_media_sup=ic_media_sup,
        ic_var_inf=ic_var_inf,
        ic_var_sup=ic_var_sup,
        ic_desv_inf=ic_desv_inf,
        ic_desv_sup=ic_desv_sup,
    )


def formatear_resultado_dataframe(muestra: MuestraCotizacion, resultado: ResultadoICDataFrame) -> str:
    texto = []
    texto.append("CALCULO CON DATAFRAME REAL (COTIZACIONES)")
    texto.append("-" * 70)
    texto.append(f"Ticker = {muestra.ticker}")
    texto.append(f"Columna usada = {muestra.columna}")
    texto.append(f"Rango de fechas = {muestra.fecha_inicio} a {muestra.fecha_fin}")
    texto.append(f"Observaciones usadas (n) = {resultado.n}")
    texto.append(f"Confianza = {resultado.confianza:.4f} | alpha = {resultado.alpha:.4f}")
    texto.append("")
    texto.append("Estimadores muestrales:")
    texto.append(f"Media = {resultado.media:.6f}")
    texto.append(f"Varianza = {resultado.varianza:.6f}")
    texto.append(f"Desvio = {resultado.desvio:.6f}")
    texto.append("")
    texto.append("Intervalo de confianza para la media (t de Student):")
    texto.append(f"IC(mu) = ({resultado.ic_media_inf:.6f}, {resultado.ic_media_sup:.6f})")
    texto.append("")
    texto.append("Intervalo de confianza para la varianza (Chi-cuadrado):")
    texto.append(f"IC(sigma^2) = ({resultado.ic_var_inf:.6f}, {resultado.ic_var_sup:.6f})")
    texto.append(f"IC(sigma) = ({resultado.ic_desv_inf:.6f}, {resultado.ic_desv_sup:.6f})")

    return "\n".join(texto)

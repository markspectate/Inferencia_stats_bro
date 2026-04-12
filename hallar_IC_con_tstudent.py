#este codigo lo utilizare para la resolcion de mis incisos de estadistica


# UTILIZACION: MEDIA EN POBLACIONES NORMALES CON VARIANZA DESCONOCIDA
print("MEDIA EN POBLACIONES NORMALES CON VARIANZA DESCONOCIDA")
from scipy import stats
import math

muestra = [12, 15, 14, 10, 13, 16, 11]

n = len(muestra)
gl = n - 1
media = stats.tmean(muestra)
desvio = stats.tstd(muestra)

confianza = 0.95
alpha = 1 - confianza
t_critico = stats.t.ppf(1 - alpha/2, gl)

ic_inf = media - t_critico * desvio / math.sqrt(n)
ic_sup = media + t_critico * desvio / math.sqrt(n)

print(f"n = {n}")
print(f"g.l. = {gl}")
print(f"media muestral = {media:.4f}")
print(f"desvío muestral = {desvio:.4f}")
print(f"\n\nEl IC Con los datos tiene la forma: ",media,"-",t_critico,"* (",desvio,"/",math.sqrt(n),")", "< u < ",media, "+",t_critico, "* (",desvio, "/",math.sqrt(n), ")")

print(f"IC 95% para μ = ({ic_inf:.4f}, {ic_sup:.4f})")


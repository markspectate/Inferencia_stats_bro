from scipy import stats
import math
import numpy as np

print("Varianza en poblaciones normales con media desconocida", "\n", "----------------------------------------------------------------")


muestra = [70, 47, 42, 51, 56, 71, 75, 61, 62]

n = len(muestra)
gl = n - 1
varianza_muestral = stats.tvar(muestra)
desvio = stats.tstd(muestra)
media = stats.tmean(muestra)
print("***** A CONTINUACION, LOS ESTIMADORES DE LA RESPECTIVA MUESTRA*****")
print(" Con una media de: ",media,"\n", "La varianza muestral es: ",varianza_muestral,"\n Luego el desvio es: ",desvio)


confianza = 0.95
alpha = 1 - confianza

## NUESTRA V.A Chi-Cuadrado estandarizada
chi2_izq = stats.chi2.ppf(alpha / 2, df=gl)  #utilizada para limite superior
chi2_der = stats.chi2.ppf(1 - alpha / 2, df=gl) #Utilzada para limite inferior

print(f"\n\n\nCon una confianza de: ",confianza, f"entonces nuestro alpha sera: {alpha}")
print(f"El valor de nuestro estimador estandar en el Limite Inferior del IC es: {chi2_der}")
print(f"El valor de nuestro estimador estandar en el Limite Superior del IC es: {chi2_izq}")


ic_var_inf = (gl * varianza_muestral) / chi2_der
ic_var_sup = (gl * varianza_muestral) / chi2_izq

ic_desv_inf = math.sqrt(ic_var_inf)
ic_desv_sup = math.sqrt(ic_var_sup)

print(f"IC del 95% para σ²: ({ic_var_inf:.4f}, {ic_var_sup:.4f})")
# print(f"IC del 95% para σ: ({ic_desv_inf:.4f}, {ic_desv_sup:.4f})")
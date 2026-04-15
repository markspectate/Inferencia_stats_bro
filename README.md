# Inferencia Stats Bro

Aplicación de escritorio para estadística inferencial, construida con Python y PySide6 (Qt). Permite calcular intervalos de confianza con visualización gráfica y consultar demostraciones matemáticas paso a paso.

---

## Tabla de contenidos

- [Descripción general](#descripción-general)
- [Tecnologías](#tecnologías)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Instalación](#instalación)
- [Uso](#uso)
- [Módulos](#módulos)
  - [aplicacion_estadistica.py](#aplicacion_estadisticapy)
  - [intervalos_confianza_page.py](#intervalos_confianza_pagepy)
  - [anexo_demostraciones.py](#anexo_demostracionespy)
  - [calculos/](#calculos)
- [Scripts de prototipo](#scripts-de-prototipo)

---

## Descripción general

La aplicación tiene dos secciones principales accesibles desde la barra de navegación superior:

1. **Intervalos de confianza** — Ingresás una muestra numérica y un nivel de confianza, y la app calcula el intervalo de confianza para la media (t de Student) o para la varianza/desvío (Chi-Cuadrado). Los resultados se muestran con notación matemática renderizada y se acompañan de gráficos de la distribución de la muestra.

2. **Anexo Demostraciones** — Explorador de demostraciones matemáticas organizadas por unidad temática. Cada demostración presenta el desarrollo paso a paso con fórmulas LaTeX renderizadas vía MathJax (requiere `QtWebEngineWidgets`) o en modo texto de respaldo.

---

## Tecnologías

| Librería | Versión mínima | Rol |
|---|---|---|
| Python | 3.14 | Lenguaje base |
| PySide6 | 6.11 | Interfaz gráfica (Qt) |
| matplotlib | 3.10 | Gráficos y renderizado de expresiones matemáticas |
| numpy | 2.4 | Operaciones numéricas sobre arrays |
| scipy | 1.17 | Distribuciones estadísticas (t, Chi², PPF) |
| PySide6.QtWebEngineWidgets | (incluido en PySide6) | Renderizado MathJax en el Anexo (opcional) |

---

## Estructura del proyecto

```
Inferencia_stats_bro/
│
├── aplicacion_estadistica.py      # Ventana principal (QMainWindow) y navegación
├── intervalos_confianza_page.py   # Página de cálculo de intervalos de confianza
├── anexo_demostraciones.py        # Página del anexo con demostraciones matemáticas
│
├── calculos/                      # Paquete de lógica estadística pura
│   ├── __init__.py
│   ├── t_student.py               # IC para la media (t de Student)
│   ├── chi_cuadrado.py            # IC para la varianza (Chi-Cuadrado)
│   └── validaciones.py            # Validación de entrada (muestra y confianza)
│
├── gui_paraChiC_y_Tstu.py         # Punto de entrada de la aplicación
│
├── hallar_IC_con_tstudent.py      # Script prototipo (CLI) — t de Student
├── hallar_IC_con_ChiCuadrado.py   # Script prototipo (CLI) — Chi-Cuadrado
│
├── requirements.txt               # Dependencias del proyecto
└── .venv/                         # Entorno virtual
```

---

## Instalación

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd Inferencia_stats_bro

# Crear y activar el entorno virtual
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### requirements.txt

```
PySide6>=6.11
matplotlib>=3.10
numpy>=2.4
scipy>=1.17
```

---

## Uso

```bash
python gui_paraChiC_y_Tstu.py
# o alternativamente:
python aplicacion_estadistica.py
```

La ventana abre en la sección **Intervalos de confianza** por defecto. La navegación superior permite cambiar de sección.

---

## Módulos

### `aplicacion_estadistica.py`

Clase principal: `PlataformaEstadistica(QMainWindow)`

- Configura la ventana (1320×860 px, mínimo 1120×720).
- Construye la barra de navegación superior con dos botones:
  - `"Intervalos de confianza"` → `QPushButton` → muestra `IntervalosConfianzaPage`
  - `"Anexo Demostraciones"` → `QToolButton` con menú desplegable → muestra `AnexoDemostracionesWidget` en la unidad seleccionada
- Usa un `QStackedWidget` para alternar entre las dos páginas.
- Resalta el botón activo con propiedad CSS `active="true"`.

---

### `intervalos_confianza_page.py`

Clase: `IntervalosConfianzaPage(QWidget)`

Layout en dos paneles (`QSplitter` horizontal):

**Panel izquierdo:**
- Selector de tipo de cálculo: `Media (t de Student)` / `Varianza (Chi-Cuadrado)`
- Campo de nivel de confianza (default: `0.95`)
- Área de texto para ingresar la muestra separada por comas
- Botones: `Confirmar muestra manual`, `Limpiar`, `Ejemplo media`, `Ejemplo varianza`
- Panel de resultados con renderizado matemático usando `matplotlib` como canvas de figuras LaTeX

**Panel derecho:**
- Gráfico de serie de observaciones (puntos sobre línea)
- Histograma de densidad con curva normal ajustada superpuesta

**Flujo de cálculo:**
```
obtener_muestra() → normalizar_muestra()
obtener_confianza() → validar_confianza()
        ↓
calcular_ic_media() o calcular_ic_varianza()   ← módulo calculos/
        ↓
_renderizar_resultado_matematico()   ← genera figura matplotlib con LaTeX
_actualizar_grafico_muestra()        ← actualiza los dos gráficos
```

**Degradación graceful:** si `matplotlib` no está disponible, el resultado se muestra en un `QPlainTextEdit` de texto plano.

---

### `anexo_demostraciones.py`

Clase: `AnexoDemostracionesWidget(QWidget)`

Explorador de demostraciones matemáticas organizadas en unidades temáticas.

**Unidades disponibles:**

| ID | Nombre |
|---|---|
| `va_continuas` | V.A Continuas |
| `va_bidimensionales` | V.A Bidimensionales |
| `muestreo` | Muestreo |

Cada unidad contiene múltiples demostraciones. Ejemplo de demostraciones en `va_continuas`:
- Normal: demostración completa de parámetros (E[X] = μ, Var(X) = σ²)
- Gamma: demostración completa de parámetros

**Estructura de una demostración:**
```python
{
    "id": "normal_parametros",
    "nombre_menu": "Normal: demostracion completa de parametros",
    "titulo": "...",
    "bloques": [
        ("titulo", "Distribucion Normal"),
        ("subtitulo", "Paso 1: ..."),
        ("math", r"$...$"),          # LaTeX
        ("texto", "Explicacion..."),
        ("propiedad", "Propiedad usada: ..."),
        ("resultado", r"$\boxed{...}$"),
        ("espacio", ""),
    ]
}
```

**Tipos de bloque soportados:** `titulo`, `subtitulo`, `texto`, `propiedad`, `math`, `resultado`, `espacio`

**Renderizado:**
- Con `QtWebEngineWidgets`: HTML + MathJax (renderizado de alta calidad)
- Sin `QtWebEngineWidgets`: `QPlainTextEdit` en modo texto de respaldo

**Validación al inicio:** `_validar_demostraciones()` verifica la estructura de todos los datos antes de iniciar la UI, lanzando `ValueError` descriptivo si algo está mal formado.

---

### `calculos/`

Paquete de lógica estadística pura, sin dependencias de UI.

#### `calculos/t_student.py`

```python
calcular_ic_media(muestra: Sequence[float], confianza: float) -> ResultadoICMedia
```

Calcula el intervalo de confianza para la **media** en poblaciones normales con varianza desconocida.

Fórmula:
```
IC_μ = ( x̄ - t_{1-α/2, ν} · s/√n ,  x̄ + t_{1-α/2, ν} · s/√n )
```

Campos del resultado (`ResultadoICMedia`, dataclass frozen):
`muestra`, `n`, `gl`, `media`, `desvio`, `confianza`, `alpha`, `t_critico`, `error_estandar`, `ic_inf`, `ic_sup`

---

#### `calculos/chi_cuadrado.py`

```python
calcular_ic_varianza(muestra: Sequence[float], confianza: float) -> ResultadoICVarianza
```

Calcula el intervalo de confianza para la **varianza** en poblaciones normales con media desconocida.

Fórmula:
```
IC_σ² = ( (n-1)s² / χ²_{1-α/2, ν} ,  (n-1)s² / χ²_{α/2, ν} )
IC_σ  = ( √IC_σ²_inf ,  √IC_σ²_sup )
```

Campos del resultado (`ResultadoICVarianza`, dataclass frozen):
`muestra`, `n`, `gl`, `media`, `desvio`, `varianza_muestral`, `confianza`, `alpha`, `chi2_izq`, `chi2_der`, `ic_var_inf`, `ic_var_sup`, `ic_desv_inf`, `ic_desv_sup`

Ambos módulos también exponen funciones `formatear_resultado_*()` que devuelven un string con el desarrollo en texto plano.

---

#### `calculos/validaciones.py`

```python
normalizar_muestra(muestra: Sequence[float], minimo: int = 2) -> list[float]
```
- Convierte todos los valores a `float`
- Verifica que haya al menos `minimo` observaciones
- Rechaza valores `inf` o `nan`

```python
validar_confianza(confianza: float) -> float
```
- Verifica que sea numérico, finito y en el rango `(0, 1)` estricto

Ambas lanzan `ValueError` con mensajes descriptivos en caso de error.

---

## Scripts de prototipo

Estos archivos son los scripts de línea de comandos originales, previos a la interfaz gráfica. Ya no se usan activamente pero documentan el razonamiento inicial.

| Archivo | Descripción |
|---|---|
| `hallar_IC_con_tstudent.py` | Calcula IC para la media con muestra hardcodeada `[12, 15, 14, 10, 13, 16, 11]`, confianza 0.95 |
| `hallar_IC_con_ChiCuadrado.py` | Calcula IC para la varianza con muestra `[70, 47, 42, 51, 56, 71, 75, 61, 62]`, confianza 0.95 |

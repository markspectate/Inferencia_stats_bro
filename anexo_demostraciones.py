from __future__ import annotations

from html import escape

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QPlainTextEdit,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except Exception:
    QWebEngineView = None


TIPOS_BLOQUE_DEMO = {"titulo", "subtitulo", "texto", "propiedad", "math", "resultado", "espacio"}


class AnexoDemostracionesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("AnexoRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.demostraciones = self._cargar_demostraciones()
        self._validar_demostraciones()
        self.unidad_actual: str | None = None

        self.lista_demos: QTreeWidget | None = None
        self.titulo_demo_label: QLabel | None = None
        self.demo_web: QWebEngineView | None = None
        self.demo_texto: QPlainTextEdit | None = None

        self._aplicar_estilo()
        self._construir_interfaz()

    def _aplicar_estilo(self):
        self.setStyleSheet(
            """
            QWidget#AnexoRoot {
                background: #ece9d8;
            }
            QWidget#AnexoRoot QWidget {
                color: #111111;
                font-family: "Segoe UI", "Tahoma", Arial, sans-serif;
                font-size: 13px;
            }
            QLabel#AnexoTitulo {
                font-size: 28px;
                font-weight: 700;
                color: #1f3854;
            }
            QLabel#DemoSeleccion {
                font-size: 18px;
                font-weight: 600;
                color: #1f3854;
            }
            QGroupBox {
                background: #f7f5ee;
                border: 1px solid #b8b6ac;
                border-radius: 3px;
                margin-top: 18px;
                padding: 24px 16px 16px 16px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 14px;
                top: 0px;
                padding: 0 6px;
                color: #1f3854;
                background: #f7f5ee;
                font-size: 14px;
                font-weight: 700;
            }
            QGroupBox#GrupoDesarrollo::title {
                font-size: 14px;
            }
            QTreeWidget {
                background: #ffffff;
                border: 1px solid #9da1a8;
                border-radius: 3px;
                padding: 6px;
            }
            QTreeWidget::item {
                min-height: 34px;
                border-radius: 3px;
                padding: 3px 6px;
            }
            QTreeWidget::item:selected {
                background: #d1e4f8;
                color: #153a60;
            }
            QTreeWidget::item:hover {
                background: #ebeff5;
            }
            QPlainTextEdit {
                background: #ffffff;
                border: 1px solid #9da1a8;
                border-radius: 3px;
                padding: 12px;
                color: #111111;
            }
            QWebEngineView {
                border: 1px solid #9da1a8;
                border-radius: 3px;
                background: #ffffff;
            }
            QSplitter::handle {
                background: transparent;
                width: 24px;
            }
            """
        )

    def _construir_interfaz(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(24, 20, 24, 22)
        raiz.setSpacing(20)

        encabezado = QVBoxLayout()
        titulo = QLabel("Anexo Demostraciones")
        titulo.setObjectName("AnexoTitulo")
        encabezado.addWidget(titulo)
        raiz.addLayout(encabezado)

        divisor = QSplitter(Qt.Orientation.Horizontal)
        divisor.setChildrenCollapsible(False)
        divisor.addWidget(self._construir_panel_lista())
        divisor.addWidget(self._construir_panel_documento())
        divisor.setSizes([420, 960])
        raiz.addWidget(divisor, stretch=1)

    def _construir_panel_lista(self):
        panel = QGroupBox("Demostraciones de la unidad")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 24, 16, 16)

        self.lista_demos = QTreeWidget()
        self.lista_demos.setHeaderHidden(True)
        self.lista_demos.itemSelectionChanged.connect(self._al_cambiar_demostracion)
        layout.addWidget(self.lista_demos)
        return panel

    def _construir_panel_documento(self):
        panel = QGroupBox("Desarrollo matematico")
        panel.setObjectName("GrupoDesarrollo")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 24, 16, 16)
        layout.setSpacing(18)

        self.titulo_demo_label = QLabel("Selecciona una demostracion.")
        self.titulo_demo_label.setObjectName("DemoSeleccion")
        layout.addWidget(self.titulo_demo_label)

        if QWebEngineView is not None:
            self.demo_web = QWebEngineView()
            self.demo_web.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
            layout.addWidget(self.demo_web, stretch=1)
            return panel

        self.demo_texto = QPlainTextEdit()
        self.demo_texto.setReadOnly(True)
        layout.addWidget(self.demo_texto, stretch=1)
        return panel

    def _validar_demostraciones(self):
        for unidad_id, unidad_data in self.demostraciones.items():
            if "nombre" not in unidad_data or "demostraciones" not in unidad_data:
                raise ValueError(f"La unidad '{unidad_id}' no tiene la estructura esperada.")

            ids_vistos = set()
            for demo in unidad_data["demostraciones"]:
                for clave in ("id", "nombre_menu", "titulo", "bloques"):
                    if clave not in demo:
                        raise ValueError(f"La demostracion de '{unidad_id}' no define '{clave}'.")

                demo_id = demo["id"]
                if demo_id in ids_vistos:
                    raise ValueError(f"La unidad '{unidad_id}' tiene una demostracion duplicada: '{demo_id}'.")
                ids_vistos.add(demo_id)

                for bloque in demo["bloques"]:
                    if not isinstance(bloque, tuple) or len(bloque) != 2:
                        raise ValueError(f"La demostracion '{demo_id}' tiene un bloque mal formado.")

                    tipo, contenido = bloque
                    if tipo not in TIPOS_BLOQUE_DEMO:
                        raise ValueError(f"La demostracion '{demo_id}' usa un tipo de bloque no soportado: '{tipo}'.")

                    if not isinstance(contenido, str):
                        raise ValueError(f"La demostracion '{demo_id}' contiene un bloque no textual.")

                    if tipo in {"texto", "propiedad"} and contenido.count("$") % 2 != 0:
                        raise ValueError(f"La demostracion '{demo_id}' tiene delimitadores LaTeX incompletos.")

    def obtener_unidades_menu(self) -> list[tuple[str, str]]:
        return [(unidad_id, unidad_data["nombre"]) for unidad_id, unidad_data in self.demostraciones.items()]

    def set_unidad(self, unidad_id: str):
        if unidad_id not in self.demostraciones:
            return
        self.unidad_actual = unidad_id
        unidad = self.demostraciones[unidad_id]

        if self.lista_demos is None:
            return

        self.lista_demos.clear()
        for demo in unidad["demostraciones"]:
            item = QTreeWidgetItem([demo["nombre_menu"]])
            item.setData(0, Qt.ItemDataRole.UserRole, demo["id"])
            self.lista_demos.addTopLevelItem(item)

        if self.lista_demos.topLevelItemCount() > 0:
            primer = self.lista_demos.topLevelItem(0)
            self.lista_demos.setCurrentItem(primer)
            self._mostrar_demostracion(primer.data(0, Qt.ItemDataRole.UserRole))

    def _al_cambiar_demostracion(self):
        if self.lista_demos is None:
            return
        seleccion = self.lista_demos.selectedItems()
        if not seleccion:
            return
        demo_id = seleccion[0].data(0, Qt.ItemDataRole.UserRole)
        if demo_id is None:
            return
        self._mostrar_demostracion(demo_id)

    def _buscar_demostracion(self, demo_id: str):
        if self.unidad_actual is None:
            return None
        unidad = self.demostraciones[self.unidad_actual]
        for demo in unidad["demostraciones"]:
            if demo["id"] == demo_id:
                return demo
        return None

    def _mostrar_demostracion(self, demo_id: str):
        demo = self._buscar_demostracion(demo_id)
        if demo is None:
            return

        if self.titulo_demo_label is not None:
            self.titulo_demo_label.setText(demo["titulo"])

        bloques = demo["bloques"]
        texto_respaldo = self._bloques_a_texto(bloques)
        self._renderizar_documento(bloques, texto_respaldo)

    def _bloques_a_texto(self, bloques):
        lineas = []
        for tipo, contenido in bloques:
            if tipo == "espacio":
                lineas.append("")
                continue
            if tipo in {"math", "resultado"} and contenido.startswith("$") and contenido.endswith("$"):
                lineas.append(contenido[1:-1])
                continue
            lineas.append(contenido)
        return "\n".join(lineas)

    def _formatear_inline_math(self, texto: str) -> str:
        partes = texto.split("$")
        if len(partes) == 1:
            return escape(texto)

        render = []
        for indice, parte in enumerate(partes):
            if indice % 2 == 0:
                render.append(escape(parte))
            else:
                render.append(rf"\({escape(parte)}\)")
        return "".join(render)

    def _extraer_latex(self, contenido: str) -> str:
        expresion = contenido.strip()
        if expresion.startswith("$") and expresion.endswith("$") and len(expresion) >= 2:
            return expresion[1:-1].strip()
        return expresion

    def _bloques_a_html(self, bloques) -> str:
        piezas = []
        for tipo, contenido in bloques:
            if tipo == "espacio":
                piezas.append('<div class="spacer"></div>')
                continue
            if tipo == "titulo":
                piezas.append(f'<h2 class="sec-title">{escape(contenido)}</h2>')
                continue
            if tipo == "subtitulo":
                piezas.append(f'<h3 class="step-title">{escape(contenido)}</h3>')
                continue
            if tipo == "texto":
                piezas.append(f'<p class="body">{self._formatear_inline_math(contenido)}</p>')
                continue
            if tipo == "propiedad":
                piezas.append(f'<p class="property">{self._formatear_inline_math(contenido)}</p>')
                continue
            if tipo == "math":
                expr = escape(self._extraer_latex(contenido))
                piezas.append(f'<div class="equation">\\[{expr}\\]</div>')
                continue
            if tipo == "resultado":
                expr = escape(self._extraer_latex(contenido))
                piezas.append(f'<div class="resultado">\\[{expr}\\]</div>')
                continue
            piezas.append(f'<p class="body">{self._formatear_inline_math(contenido)}</p>')

        cuerpo = "\n".join(piezas)
        return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      background: #ffffff;
      color: #111111;
    }}
    body {{
      font-family: "Times New Roman", Georgia, serif;
      line-height: 2.0;
    }}
    .paper {{
      max-width: 980px;
      margin: 0 auto;
      padding: 34px 46px 52px 46px;
    }}
    .sec-title {{
      margin: 0 0 20px 0;
      font-size: 2.15rem;
      font-weight: 700;
      line-height: 1.35;
    }}
    .step-title {{
      margin: 38px 0 14px 0;
      font-size: 1.55rem;
      font-weight: 700;
      line-height: 1.4;
    }}
    .body {{
      margin: 0 0 18px 0;
      font-size: 1.2rem;
      line-height: 2.0;
    }}
    .equation {{
      margin: 18px 0 30px 0;
      font-size: 1.25rem;
      line-height: 2.2;
    }}
    .property {{
      margin: 12px 0 28px 0;
      padding-left: 12px;
      border-left: 2px solid #111111;
      font-size: 1.14rem;
      font-style: italic;
      line-height: 2.0;
    }}
    .resultado {{
      margin: 24px 0 36px 0;
      padding: 14px 18px;
      border: 1px solid #111111;
      font-size: 1.28rem;
      line-height: 2.2;
      background: #ffffff;
    }}
    .spacer {{
      height: 20px;
    }}
  </style>
  <script>
    window.MathJax = {{
      tex: {{
        inlineMath: [['\\\\(', '\\\\)']],
        displayMath: [['\\\\[', '\\\\]']],
        processEscapes: true
      }},
      svg: {{
        fontCache: 'global'
      }}
    }};
  </script>
  <script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
</head>
<body>
  <main class="paper">
    {cuerpo}
  </main>
</body>
</html>
"""

    def _renderizar_documento(self, bloques, texto_respaldo: str):
        if self.demo_web is not None:
            self.demo_web.setHtml(self._bloques_a_html(bloques))
            return

        if self.demo_texto is not None:
            self.demo_texto.setPlainText(texto_respaldo)

    def _cargar_demostraciones(self):
        return {
            "va_continuas": {
                "nombre": "V.A Continuas",
                "demostraciones": [
                    {
                        "id": "normal_parametros",
                        "nombre_menu": "Normal: demostracion completa de parametros",
                        "titulo": "V.A Continuas | Normal (demostracion completa)",
                        "bloques": [
                            ("titulo", "Distribucion Normal"),
                            ("subtitulo", "Modelo"),
                            (
                                "math",
                                r"$X\sim N(\mu,\sigma^2),\qquad "
                                r"f_X(x)=\frac{1}{\sqrt{2\pi}\sigma}\exp\left(-\frac{(x-\mu)^2}{2\sigma^2}\right)$",
                            ),
                            ("texto", "Objetivo: probar que $E[X]=\\mu$ y $Var(X)=\\sigma^2$."),
                            ("espacio", ""),
                            ("subtitulo", "Paso 1: Estandarizacion"),
                            ("math", r"$Z=\frac{X-\mu}{\sigma}\;\Longrightarrow\; X=\mu+\sigma Z,\qquad Z\sim N(0,1)$"),
                            ("propiedad", "Propiedad usada: transformacion afin de una variable normal."),
                            ("espacio", ""),
                            ("subtitulo", "Paso 2: Esperanza"),
                            ("math", r"$E[X]=\int_{-\infty}^{\infty}x\,f_X(x)\,dx$"),
                            ("math", r"$=\int_{-\infty}^{\infty}(\mu+\sigma z)\,\phi(z)\,dz$"),
                            ("math", r"$=\mu\int_{-\infty}^{\infty}\phi(z)\,dz+\sigma\int_{-\infty}^{\infty}z\phi(z)\,dz$"),
                            ("math", r"$=\mu\cdot 1+\sigma\cdot 0=\mu$"),
                            (
                                "propiedad",
                                "Propiedad usada: $\\phi(z)$ es par y $z\\phi(z)$ es impar, "
                                "por eso su integral en $(-\\infty,\\infty)$ es cero.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Paso 3: Varianza"),
                            ("math", r"$Var(X)=E[(X-\mu)^2]=E[(\sigma Z)^2]=\sigma^2E[Z^2]$"),
                            ("math", r"$E[Z^2]=1\quad\Rightarrow\quad Var(X)=\sigma^2$"),
                            (
                                "propiedad",
                                "Propiedad usada: $Var(a+bY)=b^2Var(Y)$ y para $Z\\sim N(0,1)$ vale $Var(Z)=1$.",
                            ),
                            ("resultado", r"$\boxed{E[X]=\mu,\qquad Var(X)=\sigma^2}$"),
                        ],
                    },
                    {
                        "id": "gamma_parametros",
                        "nombre_menu": "Gamma: demostracion completa de parametros",
                        "titulo": "V.A Continuas | Gamma (demostracion completa)",
                        "bloques": [
                            ("titulo", "Distribucion Gamma"),
                            ("subtitulo", "Modelo"),
                            (
                                "math",
                                r"$X\sim\Gamma(\alpha,\theta),\quad \alpha>0,\;\theta>0,\qquad "
                                r"f_X(x)=\frac{1}{\Gamma(\alpha)\theta^\alpha}x^{\alpha-1}e^{-x/\theta},\;x>0$",
                            ),
                            ("texto", "Objetivo: demostrar que $E[X]=\\alpha\\theta$ y $Var(X)=\\alpha\\theta^2$."),
                            ("espacio", ""),
                            ("subtitulo", "Paso 1: Esperanza"),
                            (
                                "math",
                                r"$E[X]=\int_0^\infty x f_X(x)\,dx="
                                r"\frac{1}{\Gamma(\alpha)\theta^\alpha}\int_0^\infty x^\alpha e^{-x/\theta}\,dx$",
                            ),
                            ("math", r"$u=\frac{x}{\theta}\Rightarrow x=\theta u,\;dx=\theta\,du$"),
                            (
                                "math",
                                r"$E[X]=\frac{1}{\Gamma(\alpha)\theta^\alpha}\int_0^\infty(\theta u)^\alpha e^{-u}\theta\,du"
                                r"=\theta\frac{\Gamma(\alpha+1)}{\Gamma(\alpha)}=\alpha\theta$",
                            ),
                            ("propiedad", "Propiedad usada: recurrencia de gamma, $\\Gamma(s+1)=s\\Gamma(s)$."),
                            ("espacio", ""),
                            ("subtitulo", "Paso 2: Segundo momento"),
                            (
                                "math",
                                r"$E[X^2]=\frac{1}{\Gamma(\alpha)\theta^\alpha}\int_0^\infty x^{\alpha+1}e^{-x/\theta}\,dx$",
                            ),
                            ("math", r"$u=\frac{x}{\theta}\Rightarrow E[X^2]=\theta^2\frac{\Gamma(\alpha+2)}{\Gamma(\alpha)}$"),
                            ("math", r"$E[X^2]=\theta^2\alpha(\alpha+1)$"),
                            (
                                "propiedad",
                                "Propiedad usada: recurrencia de gamma aplicada dos veces para simplificar el cociente.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Paso 3: Varianza"),
                            ("math", r"$Var(X)=E[X^2]-E[X]^2$"),
                            ("math", r"$Var(X)=\theta^2\alpha(\alpha+1)-(\alpha\theta)^2=\alpha\theta^2$"),
                            ("resultado", r"$\boxed{E[X]=\alpha\theta,\qquad Var(X)=\alpha\theta^2}$"),
                        ],
                    },
                    {
                        "id": "exponencial_parametros",
                        "nombre_menu": "Exponencial: demostracion completa de parametros",
                        "titulo": "V.A Continuas | Exponencial (demostracion completa)",
                        "bloques": [
                            ("titulo", "Distribucion Exponencial"),
                            ("subtitulo", "Modelo"),
                            ("math", r"$X\sim Exp(\lambda),\quad \lambda>0,\qquad f_X(x)=\lambda e^{-\lambda x},\;x\ge 0$"),
                            ("texto", "Objetivo: demostrar que $E[X]=\\frac{1}{\\lambda}$ y $Var(X)=\\frac{1}{\\lambda^2}$."),
                            ("espacio", ""),
                            ("subtitulo", "Paso 1: Esperanza por integracion por partes"),
                            ("math", r"$E[X]=\int_0^\infty x\lambda e^{-\lambda x}\,dx$"),
                            ("math", r"$u=x,\;dv=\lambda e^{-\lambda x}dx\;\Rightarrow\;du=dx,\;v=-e^{-\lambda x}$"),
                            ("math", r"$E[X]=\left[-xe^{-\lambda x}\right]_0^\infty+\int_0^\infty e^{-\lambda x}\,dx$"),
                            ("math", r"$E[X]=0+\left[-\frac{1}{\lambda}e^{-\lambda x}\right]_0^\infty=\frac{1}{\lambda}$"),
                            (
                                "propiedad",
                                "Propiedad usada: limite $xe^{-\\lambda x}\\to 0$ cuando $x\\to\\infty$ y "
                                "regla de integracion por partes.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Paso 2: Segundo momento"),
                            ("math", r"$E[X^2]=\int_0^\infty x^2\lambda e^{-\lambda x}\,dx$"),
                            ("math", r"$u=x^2,\;dv=\lambda e^{-\lambda x}dx\;\Rightarrow\;du=2x\,dx,\;v=-e^{-\lambda x}$"),
                            ("math", r"$E[X^2]=\left[-x^2e^{-\lambda x}\right]_0^\infty+2\int_0^\infty xe^{-\lambda x}\,dx$"),
                            ("math", r"$\int_0^\infty xe^{-\lambda x}\,dx=\frac{1}{\lambda^2}\quad\Rightarrow\quad E[X^2]=\frac{2}{\lambda^2}$"),
                            (
                                "propiedad",
                                "Propiedad usada: del paso anterior se obtiene "
                                "$E[X]=\\lambda\\int_0^\\infty xe^{-\\lambda x}dx=\\frac{1}{\\lambda}$.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Paso 3: Varianza"),
                            ("math", r"$Var(X)=E[X^2]-E[X]^2=\frac{2}{\lambda^2}-\left(\frac{1}{\lambda}\right)^2$"),
                            ("resultado", r"$\boxed{E[X]=\frac{1}{\lambda},\qquad Var(X)=\frac{1}{\lambda^2}}$"),
                        ],
                    },
                    {
                        "id": "beta_parametros",
                        "nombre_menu": "Beta: demostracion completa de parametros",
                        "titulo": "V.A Continuas | Beta (demostracion completa)",
                        "bloques": [
                            ("titulo", "Distribucion Beta"),
                            ("subtitulo", "Modelo"),
                            (
                                "math",
                                r"$X\sim Beta(\alpha,\beta),\quad \alpha,\beta>0,\qquad "
                                r"f_X(x)=\frac{x^{\alpha-1}(1-x)^{\beta-1}}{B(\alpha,\beta)},\;0<x<1$",
                            ),
                            (
                                "texto",
                                "Objetivo: demostrar que $E[X]=\\frac{\\alpha}{\\alpha+\\beta}$ y "
                                "$Var(X)=\\frac{\\alpha\\beta}{(\\alpha+\\beta)^2(\\alpha+\\beta+1)}$.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Paso 1: Esperanza"),
                            (
                                "math",
                                r"$E[X]=\frac{1}{B(\alpha,\beta)}\int_0^1 x^\alpha(1-x)^{\beta-1}\,dx"
                                r"=\frac{B(\alpha+1,\beta)}{B(\alpha,\beta)}$",
                            ),
                            (
                                "math",
                                r"$E[X]=\frac{\Gamma(\alpha+1)\Gamma(\beta)}{\Gamma(\alpha+\beta+1)}"
                                r"\frac{\Gamma(\alpha+\beta)}{\Gamma(\alpha)\Gamma(\beta)}"
                                r"=\frac{\alpha}{\alpha+\beta}$",
                            ),
                            (
                                "propiedad",
                                "Propiedad usada: relacion beta-gamma "
                                "$B(p,q)=\\frac{\\Gamma(p)\\Gamma(q)}{\\Gamma(p+q)}$.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Paso 2: Segundo momento"),
                            (
                                "math",
                                r"$E[X^2]=\frac{1}{B(\alpha,\beta)}\int_0^1 x^{\alpha+1}(1-x)^{\beta-1}\,dx"
                                r"=\frac{B(\alpha+2,\beta)}{B(\alpha,\beta)}$",
                            ),
                            (
                                "math",
                                r"$E[X^2]=\frac{\alpha(\alpha+1)}{(\alpha+\beta)(\alpha+\beta+1)}$",
                            ),
                            (
                                "propiedad",
                                "Propiedad usada: simplificacion de cocientes con "
                                "$\\Gamma(s+1)=s\\Gamma(s)$.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Paso 3: Varianza"),
                            ("math", r"$Var(X)=E[X^2]-E[X]^2$"),
                            (
                                "math",
                                r"$Var(X)=\frac{\alpha(\alpha+1)}{(\alpha+\beta)(\alpha+\beta+1)}"
                                r"-\frac{\alpha^2}{(\alpha+\beta)^2}$",
                            ),
                            (
                                "math",
                                r"$Var(X)=\frac{\alpha\beta}{(\alpha+\beta)^2(\alpha+\beta+1)}$",
                            ),
                            (
                                "resultado",
                                r"$\boxed{E[X]=\frac{\alpha}{\alpha+\beta},\qquad "
                                r"Var(X)=\frac{\alpha\beta}{(\alpha+\beta)^2(\alpha+\beta+1)}}$",
                            ),
                        ],
                    },
                    {
                        "id": "uniforme_parametros",
                        "nombre_menu": "Uniforme: demostracion completa de parametros",
                        "titulo": "V.A Continuas | Uniforme (demostracion completa)",
                        "bloques": [
                            ("titulo", "Distribucion Uniforme"),
                            ("subtitulo", "Modelo"),
                            ("math", r"$X\sim U(a,b),\quad a<b,\qquad f_X(x)=\frac{1}{b-a},\;a<x<b$"),
                            ("texto", "Objetivo: demostrar que $E[X]=\\frac{a+b}{2}$ y $Var(X)=\\frac{(b-a)^2}{12}$."),
                            ("espacio", ""),
                            ("subtitulo", "Paso 1: Esperanza"),
                            ("math", r"$E[X]=\int_a^b x\frac{1}{b-a}\,dx=\frac{1}{b-a}\left[\frac{x^2}{2}\right]_a^b$"),
                            ("math", r"$E[X]=\frac{b^2-a^2}{2(b-a)}=\frac{(b-a)(b+a)}{2(b-a)}=\frac{a+b}{2}$"),
                            ("propiedad", "Propiedad usada: factorizacion $b^2-a^2=(b-a)(b+a)$."),
                            ("espacio", ""),
                            ("subtitulo", "Paso 2: Segundo momento"),
                            ("math", r"$E[X^2]=\int_a^b x^2\frac{1}{b-a}\,dx=\frac{1}{b-a}\left[\frac{x^3}{3}\right]_a^b$"),
                            ("math", r"$E[X^2]=\frac{b^3-a^3}{3(b-a)}=\frac{a^2+ab+b^2}{3}$"),
                            ("propiedad", "Propiedad usada: identidad $b^3-a^3=(b-a)(a^2+ab+b^2)$."),
                            ("espacio", ""),
                            ("subtitulo", "Paso 3: Varianza"),
                            ("math", r"$Var(X)=E[X^2]-E[X]^2=\frac{a^2+ab+b^2}{3}-\left(\frac{a+b}{2}\right)^2$"),
                            (
                                "math",
                                r"$Var(X)=\frac{4a^2+4ab+4b^2-3a^2-6ab-3b^2}{12}=\frac{(b-a)^2}{12}$",
                            ),
                            ("resultado", r"$\boxed{E[X]=\frac{a+b}{2},\qquad Var(X)=\frac{(b-a)^2}{12}}$"),
                        ],
                    },
                ],
            },
            "va_bidimensionales": {
                "nombre": "V.A Bidimensionales",
                "demostraciones": [
                    {
                        "id": "bidimensional_probabilidad_conjunta",
                        "nombre_menu": "Funcion de probabilidad conjunta",
                        "titulo": "V.A Bidimensionales | Funcion de probabilidad conjunta",
                        "bloques": [
                            ("titulo", "Funcion de probabilidad/densidad conjunta"),
                            ("subtitulo", "Enfoque general"),
                            (
                                "texto",
                                r"Esta unidad sigue el enfoque clasico de estadistica matematica usado en la bibliografia de Canavos y Novales: "
                                r"primero se define la estructura conjunta y luego se obtienen marginales, momentos y medidas de dependencia.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Caso discreto: funcion de probabilidad conjunta"),
                            ("math", r"$p_{X,Y}(x_i,y_j)=P(X=x_i,\;Y=y_j)$"),
                            ("math", r"$p_{X,Y}(x_i,y_j)\ge 0,\qquad \sum_i\sum_j p_{X,Y}(x_i,y_j)=1$"),
                            (
                                "math",
                                r"$P((X,Y)\in A)=\sum_{(x_i,y_j)\in A}p_{X,Y}(x_i,y_j)$",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Marginales derivadas de la conjunta"),
                            ("math", r"$p_X(x_i)=\sum_j p_{X,Y}(x_i,y_j),\qquad p_Y(y_j)=\sum_i p_{X,Y}(x_i,y_j)$"),
                            (
                                "propiedad",
                                r"Propiedad usada: regla de particion de eventos, sumando sobre todos los valores posibles de la otra variable.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Independencia en el caso discreto"),
                            (
                                "math",
                                r"$X\perp Y\quad\Longleftrightarrow\quad p_{X,Y}(x_i,y_j)=p_X(x_i)p_Y(y_j)\;\;\forall i,j$",
                            ),
                            (
                                "texto",
                                r"Si la factorizacion falla para un solo par $(x_i,y_j)$, no hay independencia.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Caso continuo: densidad conjunta"),
                            ("math", r"$f_{X,Y}(x,y)\ge 0,\qquad \int_{-\infty}^{\infty}\int_{-\infty}^{\infty}f_{X,Y}(x,y)\,dx\,dy=1$"),
                            (
                                "math",
                                r"$P((X,Y)\in A)=\iint_A f_{X,Y}(x,y)\,dx\,dy$",
                            ),
                            ("math", r"$f_X(x)=\int_{-\infty}^{\infty}f_{X,Y}(x,y)\,dy,\qquad f_Y(y)=\int_{-\infty}^{\infty}f_{X,Y}(x,y)\,dx$"),
                            (
                                "math",
                                r"$X\perp Y\quad\Longleftrightarrow\quad f_{X,Y}(x,y)=f_X(x)f_Y(y)$",
                            ),
                            (
                                "resultado",
                                r"$\boxed{\text{La funcion conjunta contiene toda la informacion probabilistica del par }(X,Y).}$",
                            ),
                        ],
                    },
                    {
                        "id": "bidimensional_distribucion_conjunta",
                        "nombre_menu": "Funcion de distribucion conjunta",
                        "titulo": "V.A Bidimensionales | Funcion de distribucion conjunta",
                        "bloques": [
                            ("titulo", "Funcion de distribucion conjunta"),
                            ("subtitulo", "Definicion"),
                            (
                                "math",
                                r"$F_{X,Y}(x,y)=P(X\le x,\;Y\le y)$",
                            ),
                            ("math", r"$0\le F_{X,Y}(x,y)\le 1$"),
                            (
                                "math",
                                r"F_{X,Y}(x_1,y)\le F_{X,Y}(x_2,y)\;\text{si }x_1\le x_2,\qquad "
                                r"F_{X,Y}(x,y_1)\le F_{X,Y}(x,y_2)\;\text{si }y_1\le y_2",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Probabilidad de rectangulos"),
                            (
                                "math",
                                r"$P(x_1<X\le x_2,\;y_1<Y\le y_2)="
                                r"F_{X,Y}(x_2,y_2)-F_{X,Y}(x_1,y_2)-F_{X,Y}(x_2,y_1)+F_{X,Y}(x_1,y_1)$",
                            ),
                            (
                                "propiedad",
                                r"Propiedad usada: inclusion-exclusion en eventos del tipo $\{X\le x,\;Y\le y\}$.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Recuperacion de la conjunta desde F"),
                            (
                                "math",
                                r"\text{Discreto: }\;p_{X,Y}(x_i,y_j)=\Delta_x\Delta_yF_{X,Y}(x_i,y_j)",
                            ),
                            (
                                "math",
                                r"\text{Continuo: }\;f_{X,Y}(x,y)=\frac{\partial^2}{\partial x\,\partial y}F_{X,Y}(x,y)\quad\text{(si existe)}",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Marginales e independencia via F"),
                            (
                                "math",
                                r"$F_X(x)=\lim_{y\to\infty}F_{X,Y}(x,y),\qquad F_Y(y)=\lim_{x\to\infty}F_{X,Y}(x,y)$",
                            ),
                            (
                                "math",
                                r"$X\perp Y\quad\Longleftrightarrow\quad F_{X,Y}(x,y)=F_X(x)F_Y(y)\;\;\forall x,y$",
                            ),
                            (
                                "resultado",
                                r"$\boxed{F_{X,Y}\text{ permite calcular cualquier probabilidad rectangular y reconstruir la ley conjunta.}}$",
                            ),
                        ],
                    },
                    {
                        "id": "bidimensional_valor_esperado",
                        "nombre_menu": "Valor esperado conjunto",
                        "titulo": "V.A Bidimensionales | Valor esperado",
                        "bloques": [
                            ("titulo", "Valor esperado en variables bidimensionales"),
                            ("subtitulo", "Definicion para funciones de dos variables"),
                            (
                                "math",
                                r"$E[g(X,Y)]=\sum_i\sum_j g(x_i,y_j)p_{X,Y}(x_i,y_j)\quad\text{(discreto)}$",
                            ),
                            (
                                "math",
                                r"$E[g(X,Y)]=\iint g(x,y)f_{X,Y}(x,y)\,dx\,dy\quad\text{(continuo)}$",
                            ),
                            (
                                "propiedad",
                                r"Condicion de existencia: $E[|g(X,Y)|]<\infty$.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Momentos principales"),
                            ("math", r"$E[X]=E[g(X,Y)]\text{ con }g(x,y)=x$"),
                            ("math", r"$E[Y]=E[g(X,Y)]\text{ con }g(x,y)=y$"),
                            ("math", r"$E[XY]=E[g(X,Y)]\text{ con }g(x,y)=xy$"),
                            ("math", r"$E[X^2],\;E[Y^2]\text{ analogamente}$"),
                            ("espacio", ""),
                            ("subtitulo", "Linealidad"),
                            ("math", r"$E[aX+bY+c]=aE[X]+bE[Y]+c$"),
                            (
                                "math",
                                r"$E[X+Y]=E[X]+E[Y]\quad\text{(si existen los dos esperados)}$",
                            ),
                            (
                                "propiedad",
                                r"La linealidad no requiere independencia.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Esperanza condicional y ley de la esperanza total"),
                            (
                                "math",
                                r"$E[X]=E\!\left(E[X\mid Y]\right),\qquad E[Y]=E\!\left(E[Y\mid X]\right)$",
                            ),
                            (
                                "texto",
                                r"Estas identidades conectan el analisis bidimensional con modelos de regresion y prediccion.",
                            ),
                            (
                                "resultado",
                                r"$\boxed{E[g(X,Y)]\text{ es la herramienta central para construir momentos y medir dependencia.}}$",
                            ),
                        ],
                    },
                    {
                        "id": "bidimensional_covarianza",
                        "nombre_menu": "Covarianza",
                        "titulo": "V.A Bidimensionales | Covarianza",
                        "bloques": [
                            ("titulo", "Covarianza"),
                            ("subtitulo", "Definicion y formula equivalente"),
                            (
                                "math",
                                r"$Cov(X,Y)=E[(X-E[X])(Y-E[Y])]$",
                            ),
                            (
                                "math",
                                r"$Cov(X,Y)=E[XY]-E[X]E[Y]$",
                            ),
                            (
                                "propiedad",
                                r"Se obtiene expandiendo el producto y aplicando linealidad de la esperanza.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Propiedades algebraicas"),
                            ("math", r"$Cov(X,Y)=Cov(Y,X)$"),
                            ("math", r"$Cov(X,X)=Var(X)$"),
                            ("math", r"$Cov(aX+b,\;cY+d)=ac\,Cov(X,Y)$"),
                            (
                                "math",
                                r"$Cov(X,Y+Z)=Cov(X,Y)+Cov(X,Z)$",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Independencia"),
                            (
                                "math",
                                r"$X\perp Y\quad\Longrightarrow\quad E[XY]=E[X]E[Y]\quad\Longrightarrow\quad Cov(X,Y)=0$",
                            ),
                            (
                                "texto",
                                r"La implicacion inversa no es cierta en general.",
                            ),
                            (
                                "math",
                                r"\text{Ejemplo: }X\sim U(-1,1),\;Y=X^2\;\Rightarrow\;Cov(X,Y)=E[X^3]-E[X]E[X^2]=0\;\text{pero }X,Y\text{ no son independientes.}",
                            ),
                            (
                                "resultado",
                                r"$\boxed{Cov(X,Y)\text{ mide dependencia lineal, no dependencia completa.}}$",
                            ),
                        ],
                    },
                    {
                        "id": "bidimensional_varianza",
                        "nombre_menu": "Varianza y combinaciones lineales",
                        "titulo": "V.A Bidimensionales | Varianza",
                        "bloques": [
                            ("titulo", "Varianza en contexto bidimensional"),
                            ("subtitulo", "Identidad fundamental"),
                            (
                                "math",
                                r"$Var(aX+bY)=a^2Var(X)+b^2Var(Y)+2ab\,Cov(X,Y)$",
                            ),
                            ("subtitulo", "Demostracion"),
                            (
                                "math",
                                r"$Var(aX+bY)=E\!\left[\left((aX+bY)-E[aX+bY]\right)^2\right]$",
                            ),
                            (
                                "math",
                                r"$=E\!\left[\left(a(X-E[X])+b(Y-E[Y])\right)^2\right]$",
                            ),
                            (
                                "math",
                                r"$=a^2E[(X-E[X])^2]+b^2E[(Y-E[Y])^2]+2abE[(X-E[X])(Y-E[Y])]$",
                            ),
                            (
                                "math",
                                r"$=a^2Var(X)+b^2Var(Y)+2abCov(X,Y)$",
                            ),
                            (
                                "propiedad",
                                r"Propiedad usada: expansion del cuadrado y linealidad de la esperanza.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Casos particulares"),
                            ("math", r"$Var(X+Y)=Var(X)+Var(Y)+2Cov(X,Y)$"),
                            ("math", r"$Var(X-Y)=Var(X)+Var(Y)-2Cov(X,Y)$"),
                            ("math", r"$X\perp Y\Rightarrow Var(X+Y)=Var(X)+Var(Y)$"),
                            (
                                "math",
                                r"$Var(\bar X_n)=\frac{1}{n^2}\sum_{i=1}^{n}\sum_{j=1}^{n}Cov(X_i,X_j)$",
                            ),
                            (
                                "texto",
                                r"La ultima expresion muestra que la dependencia entre observaciones modifica directamente la precision de promedios.",
                            ),
                            (
                                "resultado",
                                r"$\boxed{\text{La covarianza es el termino que corrige la suma simple de varianzas.}}$",
                            ),
                        ],
                    },
                    {
                        "id": "bidimensional_correlacion",
                        "nombre_menu": "Coeficiente de correlacion",
                        "titulo": "V.A Bidimensionales | Coeficiente de correlacion",
                        "bloques": [
                            ("titulo", "Coeficiente de correlacion"),
                            ("subtitulo", "Definicion"),
                            (
                                "math",
                                r"$\rho_{X,Y}=\frac{Cov(X,Y)}{\sigma_X\sigma_Y},\qquad \sigma_X=\sqrt{Var(X)},\;\sigma_Y=\sqrt{Var(Y)}$",
                            ),
                            (
                                "texto",
                                r"Es una version adimensional de la covarianza y permite comparar intensidad de relacion lineal entre escalas distintas.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Cota de magnitud"),
                            (
                                "math",
                                r"$|Cov(X,Y)|\le \sqrt{Var(X)Var(Y)}\quad\text{(Cauchy-Schwarz)}$",
                            ),
                            (
                                "math",
                                r"$\Rightarrow\quad |\rho_{X,Y}|\le 1$",
                            ),
                            (
                                "propiedad",
                                r"Igualdad $|\rho|=1$ si y solo si existe relacion lineal exacta $P(Y=a+bX)=1$ con $b\neq 0$.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Interpretacion y limites"),
                            ("math", r"$\rho>0$: asociacion lineal creciente,\quad $\rho<0$: decreciente,\quad $\rho=0$: no linealidad global"),
                            (
                                "math",
                                r"$\rho=0\;\not\Rightarrow\;X\perp Y$",
                            ),
                            (
                                "texto",
                                r"Correlacion nula descarta dependencia lineal global, pero puede existir dependencia no lineal.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Invariancia afim"),
                            (
                                "math",
                                r"$Corr(aX+b,\;cY+d)=\operatorname{sgn}(ac)\,Corr(X,Y)$",
                            ),
                            (
                                "math",
                                r"$a,c>0\Rightarrow Corr(aX+b,\;cY+d)=Corr(X,Y)$",
                            ),
                            (
                                "resultado",
                                r"$\boxed{\rho\text{ resume la dependencia lineal estandarizada entre }X\text{ e }Y.}$",
                            ),
                        ],
                    },
                ],
            },
            "muestreo": {
                "nombre": "Muestreo",
                "demostraciones": [
                    {
                        "id": "muestreo_estimadores_basicos",
                        "nombre_menu": "Estimadores: media, varianza y desvio",
                        "titulo": "Muestreo | Formulas y derivaciones de estimadores",
                        "bloques": [
                            ("titulo", "Estimadores muestrales basicos"),
                            ("subtitulo", "Marco de trabajo"),
                            (
                                "math",
                                r"$X_1,\ldots,X_n \overset{iid}{\sim} F,\qquad "
                                r"E[X_i]=\mu,\qquad Var(X_i)=\sigma^2<\infty$",
                            ),
                            (
                                "texto",
                                r"Un estimador es una estadistica: funcion de la muestra que no depende de parametros desconocidos. "
                                r"La estimacion es el valor numerico del estimador al observar una muestra concreta.",
                            ),
                            ("math", r"$\hat\theta=T(X_1,\ldots,X_n)$"),
                            ("espacio", ""),
                            ("subtitulo", "Media muestral"),
                            ("math", r"$\bar X=\frac{1}{n}\sum_{i=1}^{n}X_i$"),
                            ("math", r"$E[\bar X]=\frac{1}{n}\sum_{i=1}^{n}E[X_i]=\mu$"),
                            ("math", r"$Var(\bar X)=\frac{1}{n^2}\sum_{i=1}^{n}Var(X_i)=\frac{\sigma^2}{n}$"),
                            ("math", r"$MSE(\bar X)=Var(\bar X)+Bias(\bar X)^2=\frac{\sigma^2}{n}$"),
                            (
                                "propiedad",
                                r"Propiedades usadas: linealidad de la esperanza e independencia para sumar varianzas.",
                            ),
                            ("resultado", r"$\boxed{\bar X\text{ es insesgado para }\mu,\qquad Var(\bar X)=\sigma^2/n}$"),
                            ("espacio", ""),
                            ("subtitulo", "Varianza muestral"),
                            ("math", r"$S^2=\frac{1}{n-1}\sum_{i=1}^{n}(X_i-\bar X)^2$"),
                            (
                                "math",
                                r"$\sum_{i=1}^{n}(X_i-\bar X)^2=\sum_{i=1}^{n}\left((X_i-\mu)-(\bar X-\mu)\right)^2$",
                            ),
                            (
                                "math",
                                r"$\sum_{i=1}^{n}(X_i-\bar X)^2=\sum_{i=1}^{n}(X_i-\mu)^2-n(\bar X-\mu)^2$",
                            ),
                            ("math", r"$E\left[\sum_{i=1}^{n}(X_i-\bar X)^2\right]=n\sigma^2-n\frac{\sigma^2}{n}=(n-1)\sigma^2$"),
                            ("math", r"$E[S^2]=\sigma^2$"),
                            ("math", r"$\tilde S^2=\frac{1}{n}\sum_{i=1}^{n}(X_i-\bar X)^2\quad\Rightarrow\quad E[\tilde S^2]=\frac{n-1}{n}\sigma^2$"),
                            (
                                "propiedad",
                                r"Propiedad usada: descomposicion de suma de cuadrados y que el termino cruzado suma cero.",
                            ),
                            ("resultado", r"$\boxed{S^2\text{ es insesgado para }\sigma^2}$"),
                            ("espacio", ""),
                            ("subtitulo", "Desvio muestral"),
                            ("math", r"$S=\sqrt{S^2}=\sqrt{\frac{1}{n-1}\sum_{i=1}^{n}(X_i-\bar X)^2}$"),
                            (
                                "texto",
                                r"En general el desvio muestral no es insesgado. La raiz cuadrada introduce sesgo porque es una transformacion no lineal.",
                            ),
                            (
                                "math",
                                r"$E[S]\le \sqrt{E[S^2]}=\sigma$",
                            ),
                            (
                                "math",
                                r"$X_i\sim N(\mu,\sigma^2)\quad\Rightarrow\quad E[S]=c_4(n)\sigma,\qquad 0<c_4(n)<1$",
                            ),
                            (
                                "math",
                                r"$c_4(n)=\sqrt{\frac{2}{n-1}}\frac{\Gamma(n/2)}{\Gamma((n-1)/2)}$",
                            ),
                            ("math", r"$S \xrightarrow{p}\sigma$"),
                            (
                                "propiedad",
                                r"Propiedad usada: Jensen para el sesgo y transformacion continua para la consistencia.",
                            ),
                            ("resultado", r"$\boxed{S\text{ es consistente para }\sigma}$"),
                        ],
                    },
                    {
                        "id": "muestreo_distribuciones_estimadores",
                        "nombre_menu": "Distribuciones de los estimadores",
                        "titulo": "Muestreo | Distribuciones exactas y asintoticas",
                        "bloques": [
                            ("titulo", "Distribuciones de los estimadores"),
                            ("subtitulo", "Media muestral bajo normalidad"),
                            ("math", r"$X_i\sim N(\mu,\sigma^2)\quad\Rightarrow\quad \sum_{i=1}^{n}X_i\sim N(n\mu,n\sigma^2)$"),
                            ("math", r"$\bar X=\frac{1}{n}\sum_{i=1}^{n}X_i\sim N\left(\mu,\frac{\sigma^2}{n}\right)$"),
                            ("math", r"$Z=\frac{\bar X-\mu}{\sigma/\sqrt n}\sim N(0,1)$"),
                            (
                                "propiedad",
                                r"Propiedad usada: estabilidad de la familia normal bajo combinaciones lineales.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Media muestral sin normalidad exacta"),
                            (
                                "math",
                                r"$\frac{\sqrt n(\bar X-\mu)}{\sigma}\xrightarrow{d}N(0,1)$",
                            ),
                            (
                                "texto",
                                r"Esta aproximacion es central en inferencia: si $n$ es grande y la varianza poblacional es finita, "
                                r"$\bar X$ se comporta aproximadamente como una normal centrada en $\mu$.",
                            ),
                            (
                                "math",
                                r"$\sup_x\left|P\left(\frac{\sqrt n(\bar X-\mu)}{\sigma}\le x\right)-\Phi(x)\right|\le "
                                r"\frac{C\,E[|X-\mu|^3]}{\sigma^3\sqrt n}$",
                            ),
                            (
                                "propiedad",
                                r"Cota de Berry-Esseen: mide la velocidad de aproximacion normal si existe momento cubico.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Varianza muestral bajo normalidad"),
                            (
                                "math",
                                r"$X_i\sim N(\mu,\sigma^2)\quad\Rightarrow\quad "
                                r"\frac{(n-1)S^2}{\sigma^2}\sim \chi^2_{n-1}$",
                            ),
                            (
                                "math",
                                r"$S^2 \sim \frac{\sigma^2}{n-1}\chi^2_{n-1}$",
                            ),
                            (
                                "math",
                                r"$E[S^2]=\sigma^2,\qquad Var(S^2)=\frac{2\sigma^4}{n-1}$",
                            ),
                            (
                                "propiedad",
                                r"Propiedad usada: descomposicion normal de la suma de cuadrados y perdida de un grado de libertad al estimar $\mu$ con $\bar X$.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Desvio muestral bajo normalidad"),
                            ("math", r"$S=\sigma\sqrt{\frac{\chi^2_{n-1}}{n-1}}$"),
                            (
                                "math",
                                r"$E[S]=c_4(n)\sigma,\qquad c_4(n)=\sqrt{\frac{2}{n-1}}\frac{\Gamma(n/2)}{\Gamma((n-1)/2)}$",
                            ),
                            (
                                "texto",
                                r"La distribucion de $S$ se obtiene transformando una chi-cuadrado. "
                                r"No es normal en muestras pequenas, aunque se concentra alrededor de $\sigma$ cuando $n$ crece.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Resultado t de Student"),
                            (
                                "math",
                                r"$Z=\frac{\bar X-\mu}{\sigma/\sqrt n}\sim N(0,1),\qquad "
                                r"U=\frac{(n-1)S^2}{\sigma^2}\sim\chi^2_{n-1},\qquad Z\perp U$",
                            ),
                            (
                                "math",
                                r"$T=\frac{\bar X-\mu}{S/\sqrt n}\sim t_{n-1}$",
                            ),
                            (
                                "texto",
                                r"Este resultado conecta la media y el desvio muestral: al reemplazar $\sigma$ por $S$, "
                                r"la normal estandarizada pasa a una distribucion t con $n-1$ grados de libertad.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Varianza y desvio sin normalidad exacta"),
                            (
                                "math",
                                r"$\sqrt n(S^2-\sigma^2)\xrightarrow{d}N(0,\mu_4-\sigma^4),\qquad "
                                r"\mu_4=E[(X-\mu)^4]$",
                            ),
                            (
                                "math",
                                r"$\sqrt n(S-\sigma)\xrightarrow{d}N\left(0,\frac{\mu_4-\sigma^4}{4\sigma^2}\right)$",
                            ),
                            (
                                "propiedad",
                                r"Propiedad usada: aproximacion asintotica y metodo delta aplicado a la transformacion $g(x)=\sqrt{x}$.",
                            ),
                            (
                                "resultado",
                                r"$\boxed{\text{La distribucion de cada estimador depende del supuesto poblacional y del tamano muestral.}}$",
                            ),
                        ],
                    },
                    {
                        "id": "muestreo_tcl_estimadores",
                        "nombre_menu": "Teorema Central del Limite y estimadores",
                        "titulo": "Muestreo | Teorema Central del Limite",
                        "bloques": [
                            ("titulo", "Teorema Central del Limite"),
                            ("subtitulo", "Enunciado"),
                            (
                                "math",
                                r"$X_1,\ldots,X_n \overset{iid}{\sim}F,\qquad E[X_i]=\mu,\qquad Var(X_i)=\sigma^2<\infty$",
                            ),
                            (
                                "math",
                                r"$\frac{\sum_{i=1}^{n}X_i-n\mu}{\sigma\sqrt n}\xrightarrow{d}N(0,1)$",
                            ),
                            (
                                "math",
                                r"$\frac{\sqrt n(\bar X-\mu)}{\sigma}\xrightarrow{d}N(0,1)$",
                            ),
                            (
                                "texto",
                                r"El teorema afirma que la suma estandarizada, y por lo tanto la media muestral estandarizada, "
                                r"tiende en distribucion a una normal estandar cuando el tamano muestral crece.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Demostracion por funcion caracteristica"),
                            ("math", r"$Y_i=\frac{X_i-\mu}{\sigma},\qquad E[Y_i]=0,\qquad Var(Y_i)=1,\qquad Z_n=\frac{1}{\sqrt n}\sum_{i=1}^{n}Y_i$"),
                            (
                                "math",
                                r"$\varphi_{Z_n}(t)=\left(\varphi_Y\left(\frac{t}{\sqrt n}\right)\right)^n$",
                            ),
                            (
                                "math",
                                r"$\varphi_Y(u)=1-\frac{u^2}{2}+o(u^2)\quad\text{cuando }u\to0$",
                            ),
                            (
                                "math",
                                r"$\varphi_Y\left(\frac{t}{\sqrt n}\right)=1-\frac{t^2}{2n}+o\left(\frac{1}{n}\right)$",
                            ),
                            (
                                "math",
                                r"$\varphi_{Z_n}(t)=\left(1-\frac{t^2}{2n}+o\left(\frac{1}{n}\right)\right)^n\to e^{-t^2/2}$",
                            ),
                            (
                                "propiedad",
                                r"Propiedad usada: expansion de segundo orden y teorema de continuidad de Levy.",
                            ),
                            (
                                "resultado",
                                r"$\boxed{Z_n\xrightarrow{d}N(0,1)}$",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Relacion con estimadores"),
                            (
                                "math",
                                r"$\bar X \approx N\left(\mu,\frac{\sigma^2}{n}\right)$",
                            ),
                            (
                                "math",
                                r"$\frac{\bar X-\mu}{S/\sqrt n}\approx N(0,1)\quad\text{si }n\text{ es grande}$",
                            ),
                            (
                                "math",
                                r"$\frac{\bar X-\mu}{S/\sqrt n}\xrightarrow{d}N(0,1)$",
                            ),
                            (
                                "texto",
                                r"En terminos de estimacion, el TCL explica por que la media muestral es la base de tantos intervalos de confianza y tests: "
                                r"su error de estimacion se reduce a escala $1/\sqrt n$ y su forma aproximada es normal.",
                            ),
                            (
                                "math",
                                r"$P\left(\bar X-z_{\alpha/2}\frac{S}{\sqrt n}\le\mu\le \bar X+z_{\alpha/2}\frac{S}{\sqrt n}\right)\approx 1-\alpha$",
                            ),
                            (
                                "resultado",
                                r"$\boxed{\bar X-\mu=O_p(n^{-1/2})}$",
                            ),
                        ],
                    },
                    {
                        "id": "muestreo_lgn_chebyshev",
                        "nombre_menu": "Ley de Grandes Numeros y Chebyshev",
                        "titulo": "Muestreo | Ley de Grandes Numeros y Chebyshev",
                        "bloques": [
                            ("titulo", "Ley de Grandes Numeros y desigualdad de Chebyshev"),
                            ("subtitulo", "Desigualdad de Chebyshev"),
                            (
                                "math",
                                r"$P(|Y-E[Y]|\ge \varepsilon)\le \frac{Var(Y)}{\varepsilon^2},\qquad \varepsilon>0$",
                            ),
                            (
                                "math",
                                r"$P((Y-E[Y])^2\ge \varepsilon^2)\le \frac{E[(Y-E[Y])^2]}{\varepsilon^2}$",
                            ),
                            (
                                "texto",
                                r"Chebyshev da una cota general de probabilidad usando solo la varianza. "
                                r"No exige normalidad ni conocer la forma completa de la distribucion.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Aplicacion a la media muestral"),
                            (
                                "math",
                                r"$E[\bar X]=\mu,\qquad Var(\bar X)=\frac{\sigma^2}{n}$",
                            ),
                            (
                                "math",
                                r"$P(|\bar X-\mu|\ge \varepsilon)\le \frac{\sigma^2}{n\varepsilon^2}$",
                            ),
                            (
                                "math",
                                r"$\lim_{n\to\infty}P(|\bar X-\mu|\ge \varepsilon)=0$",
                            ),
                            (
                                "resultado",
                                r"$\boxed{\bar X\xrightarrow{p}\mu}$",
                            ),
                            (
                                "propiedad",
                                r"Propiedad usada: Chebyshev aplicada a $Y=\bar X$ y limite cuando $n\to\infty$.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Ley de los Grandes Numeros"),
                            (
                                "texto",
                                r"La Ley de los Grandes Numeros formaliza la idea de estabilidad muestral: al aumentar $n$, "
                                r"la media muestral se aproxima a la media poblacional en probabilidad.",
                            ),
                            (
                                "math",
                                r"$\bar X\xrightarrow{p}\mu$",
                            ),
                            (
                                "texto",
                                r"La version anterior es la ley debil. Bajo condiciones mas fuertes se obtiene convergencia casi segura, "
                                r"es decir, $\bar X\to\mu$ con probabilidad uno.",
                            ),
                            (
                                "math",
                                r"$P\left(\lim_{n\to\infty}\bar X=\mu\right)=1$",
                            ),
                            (
                                "propiedad",
                                r"La convergencia casi segura implica convergencia en probabilidad, pero no al reves.",
                            ),
                            ("espacio", ""),
                            ("subtitulo", "Relacion con estimadores"),
                            (
                                "texto",
                                r"Para estimacion, la LGN justifica la consistencia de la media muestral: al repetir el muestreo con tamanos cada vez mayores, "
                                r"el estimador se concentra alrededor del parametro que intenta estimar.",
                            ),
                            (
                                "math",
                                r"$\bar X\xrightarrow{p}\mu,\qquad S^2\xrightarrow{p}\sigma^2,\qquad S\xrightarrow{p}\sigma$",
                            ),
                            (
                                "math",
                                r"$P(|\bar X-\mu|>\varepsilon)\le \frac{\sigma^2}{n\varepsilon^2}=O(n^{-1})$",
                            ),
                            (
                                "propiedad",
                                r"Propiedad usada: consistencia y teorema de transformacion continua para pasar de $S^2$ a $S$.",
                            ),
                            (
                                "resultado",
                                r"$\boxed{\text{Chebyshev controla el error; la LGN garantiza consistencia; el TCL describe la forma aproximada del error.}}$",
                            ),
                        ],
                    },
                ],
            },
        }

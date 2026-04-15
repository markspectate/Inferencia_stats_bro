from __future__ import annotations

import math
import textwrap

import numpy as np
from scipy import stats

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

try:
    import matplotlib as mpl
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.lines import Line2D

    mpl.rcParams["mathtext.fontset"] = "cm"
except Exception:
    FigureCanvas = None
    Figure = None
    Line2D = None

from calculos.chi_cuadrado import calcular_ic_varianza
from calculos.t_student import calcular_ic_media
from calculos.validaciones import normalizar_muestra, validar_confianza


class IntervalosConfianzaPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("IntervalosPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.tipo_calculo = "media"

        self.confianza_input = QLineEdit("0.95")
        self.texto_muestra = QPlainTextEdit("70, 47, 42, 51, 56, 71, 75, 61, 62")

        self.resultados_scroll: QScrollArea | None = None
        self.resultados_host: QWidget | None = None
        self.resultados_layout: QVBoxLayout | None = None
        self.resultados_texto: QPlainTextEdit | None = None
        self.canvas_grafico = None
        self.fig = None
        self.ax_serie = None
        self.ax_hist = None
        self.linea_division = None

        self._aplicar_estilo()
        self._construir_interfaz()
        self._actualizar_grafico_muestra(self.obtener_muestra())

    def _aplicar_estilo(self):
        self.setStyleSheet(
            """
            QWidget#IntervalosPage {
                background: #ece9d8;
            }
            QWidget#IntervalosPage QWidget {
                color: #1b1b1b;
                font-family: "Segoe UI", "Tahoma", Arial, sans-serif;
                font-size: 13px;
            }
            QWidget#IntervalosPage QLabel#Titulo {
                font-size: 28px;
                font-weight: 700;
                color: #1f3854;
                letter-spacing: 0px;
            }
            QWidget#IntervalosPage QLabel#Subtitulo,
            QWidget#IntervalosPage QLabel#Ayuda {
                color: #575757;
            }
            QWidget#IntervalosPage QGroupBox {
                background: #f7f5ee;
                border: 1px solid #b8b6ac;
                border-radius: 3px;
                margin-top: 14px;
                padding: 16px 12px 12px 12px;
                font-weight: 600;
            }
            QWidget#IntervalosPage QGroupBox::title {
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
            QWidget#IntervalosPage QLineEdit,
            QWidget#IntervalosPage QPlainTextEdit {
                background: #ffffff;
                border: 1px solid #9da1a8;
                border-radius: 3px;
                padding: 8px 10px;
                selection-background-color: #cfe4fa;
            }
            QWidget#IntervalosPage QLineEdit {
                min-height: 24px;
            }
            QWidget#IntervalosPage QPlainTextEdit {
                min-height: 56px;
            }
            QWidget#IntervalosPage QLineEdit:focus,
            QWidget#IntervalosPage QPlainTextEdit:focus {
                border: 1px solid #5d88b4;
                background: #ffffff;
            }
            QWidget#IntervalosPage QPushButton {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff,
                    stop: 1 #dbdbdb
                );
                border: 1px solid #9b9b9b;
                border-radius: 3px;
                min-height: 24px;
                padding: 9px 14px;
                font-weight: 600;
            }
            QWidget#IntervalosPage QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff,
                    stop: 1 #e6e6e6
                );
            }
            QWidget#IntervalosPage QPushButton:pressed {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #d7d7d7,
                    stop: 1 #f3f3f3
                );
            }
            QWidget#IntervalosPage QPushButton#Principal {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ebf5ff,
                    stop: 1 #bcd8f5
                );
                border-color: #6b91b8;
                color: #123b63;
            }
            QWidget#IntervalosPage QPushButton#Principal:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f2f8ff,
                    stop: 1 #cbe2fa
                );
            }
            QWidget#IntervalosPage QRadioButton {
                spacing: 8px;
                min-height: 26px;
                padding: 5px 0;
            }
            QWidget#IntervalosPage QRadioButton::indicator {
                width: 15px;
                height: 15px;
                border-radius: 7px;
                border: 1px solid #8d8d8d;
                background: #ffffff;
            }
            QWidget#IntervalosPage QRadioButton::indicator:checked {
                border: 4px solid #3f7fb9;
                background: #ffffff;
            }
            QWidget#IntervalosPage QScrollArea {
                border: 0;
                background: transparent;
            }
            QWidget#IntervalosPage QSplitter::handle {
                background: transparent;
                width: 24px;
            }
            """
        )

    def _construir_interfaz(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(30, 26, 30, 30)
        raiz.setSpacing(24)
        raiz.addLayout(self._construir_encabezado())

        divisor = QSplitter(Qt.Orientation.Horizontal)
        divisor.setChildrenCollapsible(False)
        divisor.addWidget(self._construir_panel_izquierdo())
        divisor.addWidget(self._construir_panel_derecho())
        divisor.setSizes([680, 660])
        raiz.addWidget(divisor, stretch=1)

    def _construir_encabezado(self):
        fila = QHBoxLayout()
        fila.setSpacing(22)

        textos = QVBoxLayout()
        titulo = QLabel("Intervalos de confianza")
        titulo.setObjectName("Titulo")
        subtitulo = QLabel("Muestra manual para calcular intervalos de confianza de media, varianza y desvio.")
        subtitulo.setObjectName("Subtitulo")
        textos.addWidget(titulo)
        textos.addWidget(subtitulo)
        fila.addLayout(textos, stretch=1)

        return fila

    def _construir_panel_izquierdo(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        layout.addWidget(self._construir_caja_configuracion())
        layout.addWidget(self._construir_caja_muestra())
        layout.addLayout(self._construir_botones_accion())
        layout.addWidget(self._construir_caja_resultados(), stretch=2)

        return panel

    def _construir_panel_derecho(self):
        panel = QWidget()
        panel.setMinimumWidth(572)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        caja_grafico = QGroupBox("Distribucion de la muestra")
        grafico_layout = QVBoxLayout(caja_grafico)
        grafico_layout.setContentsMargins(10, 16, 10, 10)
        self._construir_panel_grafico(grafico_layout)
        layout.addWidget(caja_grafico, stretch=1)

        return panel

    def _construir_caja_configuracion(self):
        caja = QGroupBox("Configuracion del ejercicio")
        caja.setMinimumHeight(148)
        layout = QVBoxLayout(caja)
        layout.setSpacing(12)

        fila_tipo = QHBoxLayout()
        etiqueta_tipo = QLabel("Tipo de calculo:")
        etiqueta_tipo.setFixedWidth(150)
        fila_tipo.addWidget(etiqueta_tipo, alignment=Qt.AlignmentFlag.AlignTop)
        radios = QVBoxLayout()
        self.radio_media = QRadioButton("Media (t de Student)")
        self.radio_varianza = QRadioButton("Varianza (Chi Cuadrado)")
        self.radio_media.setChecked(True)

        self.tipo_button_group = QButtonGroup(self)
        self.tipo_button_group.addButton(self.radio_media)
        self.tipo_button_group.addButton(self.radio_varianza)
        self.radio_media.toggled.connect(lambda activo: activo and self.seleccionar_tipo("media"))
        self.radio_varianza.toggled.connect(lambda activo: activo and self.seleccionar_tipo("varianza"))

        radios.addWidget(self.radio_media)
        radios.addWidget(self.radio_varianza)
        fila_tipo.addLayout(radios)
        fila_tipo.addStretch(1)
        layout.addLayout(fila_tipo)

        fila_confianza = QHBoxLayout()
        etiqueta_confianza = QLabel("Nivel de confianza:")
        etiqueta_confianza.setFixedWidth(150)
        fila_confianza.addWidget(etiqueta_confianza)
        self.confianza_input.setMaximumWidth(140)
        fila_confianza.addWidget(self.confianza_input)
        ayuda = QLabel("Usa valores como 0.90, 0.95 o 0.99.")
        ayuda.setObjectName("Ayuda")
        fila_confianza.addWidget(ayuda)
        fila_confianza.addStretch(1)
        layout.addLayout(fila_confianza)

        return caja

    def _construir_caja_muestra(self):
        caja = QGroupBox("Datos de la muestra manual")
        caja.setMinimumHeight(130)
        layout = QVBoxLayout(caja)
        layout.setSpacing(8)

        etiqueta = QLabel("Datos separados por comas:")
        layout.addWidget(etiqueta)

        self.texto_muestra.setMinimumHeight(58)
        self.texto_muestra.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.texto_muestra)

        return caja

    def _construir_botones_accion(self):
        fila = QHBoxLayout()
        fila.setContentsMargins(0, 6, 0, 6)
        fila.setSpacing(14)

        boton_calcular = QPushButton("Confirmar muestra manual")
        boton_calcular.setObjectName("Principal")
        boton_calcular.clicked.connect(self.calcular)
        fila.addWidget(boton_calcular)

        boton_limpiar = QPushButton("Limpiar")
        boton_limpiar.clicked.connect(self.limpiar)
        fila.addWidget(boton_limpiar)

        boton_media = QPushButton("Ejemplo media")
        boton_media.clicked.connect(self.cargar_ejemplo_media)
        fila.addWidget(boton_media)

        boton_varianza = QPushButton("Ejemplo varianza")
        boton_varianza.clicked.connect(self.cargar_ejemplo_varianza)
        fila.addWidget(boton_varianza)
        fila.addStretch(1)

        return fila

    def _construir_caja_resultados(self):
        caja = QGroupBox("Resultados")
        layout = QVBoxLayout(caja)
        layout.setContentsMargins(10, 14, 10, 10)

        if FigureCanvas is None or Figure is None:
            self.resultados_texto = QPlainTextEdit()
            self.resultados_texto.setReadOnly(True)
            layout.addWidget(self.resultados_texto)
        else:
            self.resultados_scroll = QScrollArea()
            self.resultados_scroll.setWidgetResizable(True)
            self.resultados_scroll.setMinimumHeight(220)
            self.resultados_host = QWidget()
            self.resultados_host.setStyleSheet("background: #ffffff;")
            self.resultados_layout = QVBoxLayout(self.resultados_host)
            self.resultados_layout.setContentsMargins(4, 4, 4, 4)
            self.resultados_layout.setSpacing(6)
            self.resultados_scroll.setWidget(self.resultados_host)
            layout.addWidget(self.resultados_scroll)

        self._mostrar_resultado_inicial()
        return caja

    def _construir_panel_grafico(self, layout: QVBoxLayout):
        if FigureCanvas is None or Figure is None:
            aviso = QLabel("No se pudo cargar matplotlib.\nInstala matplotlib para ver el grafico.")
            aviso.setObjectName("Ayuda")
            aviso.setAlignment(Qt.AlignmentFlag.AlignCenter)
            aviso.setWordWrap(True)
            layout.addWidget(aviso, stretch=1)
            return

        self.fig = Figure(figsize=(6.0, 6.8), dpi=100)
        self.fig.patch.set_facecolor("#ffffff")
        self.ax_serie = self.fig.add_subplot(211)
        self.ax_hist = self.fig.add_subplot(212)
        self.canvas_grafico = FigureCanvas(self.fig)
        self.canvas_grafico.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas_grafico.setMinimumHeight(470)
        layout.addWidget(self.canvas_grafico)

        self._ajustar_layout_graficos()
        self._dibujar_grafico_vacio()

    def _ajustar_layout_graficos(self):
        if self.fig is None:
            return
        self.fig.subplots_adjust(left=0.11, right=0.97, top=0.95, bottom=0.08, hspace=0.82)
        if Line2D is None:
            return
        if self.linea_division is None:
            self.linea_division = Line2D(
                [0.07, 0.97],
                [0.50, 0.50],
                transform=self.fig.transFigure,
                color="#000000",
                linewidth=1.2,
            )
            self.fig.add_artist(self.linea_division)

    def seleccionar_tipo(self, tipo: str):
        self.tipo_calculo = tipo
        if tipo == "media" and not self.radio_media.isChecked():
            self.radio_media.setChecked(True)
        if tipo == "varianza" and not self.radio_varianza.isChecked():
            self.radio_varianza.setChecked(True)

    def obtener_muestra(self):
        contenido = self.texto_muestra.toPlainText().strip()
        if not contenido:
            raise ValueError("Debes ingresar una muestra.")

        try:
            muestra = [float(x.strip()) for x in contenido.replace("\n", ",").split(",") if x.strip()]
        except ValueError as exc:
            raise ValueError("La muestra contiene valores no numericos.") from exc

        return normalizar_muestra(muestra)

    def obtener_confianza(self):
        try:
            confianza = float(self.confianza_input.text().strip())
        except ValueError as exc:
            raise ValueError("El nivel de confianza debe ser numerico.") from exc

        return validar_confianza(confianza)

    def calcular(self):
        try:
            muestra = self.obtener_muestra()
            confianza = self.obtener_confianza()
            if self.tipo_calculo == "media":
                resultado_obj = calcular_ic_media(muestra, confianza)
                self._mostrar_resultado_media(muestra, resultado_obj)
            else:
                resultado_obj = calcular_ic_varianza(muestra, confianza)
                self._mostrar_resultado_varianza(muestra, resultado_obj)

            self._actualizar_grafico_muestra(muestra)
        except Exception as exc:
            self._mostrar_error("Error", str(exc))

    def limpiar(self):
        self.texto_muestra.clear()
        self._mostrar_resultado_inicial()
        self._dibujar_grafico_vacio()

    def cargar_ejemplo_media(self):
        self.seleccionar_tipo("media")
        self.confianza_input.setText("0.95")
        self.texto_muestra.setPlainText("12, 15, 14, 10, 13, 16, 11")
        self._actualizar_grafico_muestra(self.obtener_muestra())

    def cargar_ejemplo_varianza(self):
        self.seleccionar_tipo("varianza")
        self.confianza_input.setText("0.95")
        self.texto_muestra.setPlainText("70, 47, 42, 51, 56, 71, 75, 61, 62")
        self._actualizar_grafico_muestra(self.obtener_muestra())

    def _mostrar_error(self, titulo: str, mensaje: str):
        QMessageBox.critical(self, titulo, mensaje)

    def _limpiar_panel_resultados(self):
        if self.resultados_texto is not None:
            self.resultados_texto.clear()
            return
        if self.resultados_layout is None:
            return

        while self.resultados_layout.count():
            item = self.resultados_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _mostrar_resultado_inicial(self):
        mensaje = "Las expresiones matematicas apareceran aqui despues de ejecutar un calculo."
        if self.resultados_texto is not None:
            self.resultados_texto.setPlainText(mensaje)
            return

        self._limpiar_panel_resultados()
        etiqueta = QLabel(mensaje)
        etiqueta.setObjectName("Ayuda")
        etiqueta.setWordWrap(True)
        etiqueta.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        etiqueta.setContentsMargins(18, 18, 18, 18)
        if self.resultados_layout is not None:
            self.resultados_layout.addWidget(etiqueta)
            self.resultados_layout.addStretch(1)

    def _crear_items_resultado(self, bloques):
        items = []
        altura_total = 28
        for tipo, contenido in bloques:
            if tipo == "espacio":
                items.append((tipo, "", 0, 16))
                altura_total += 16
                continue

            if tipo == "titulo":
                items.append((tipo, contenido, 16, 34))
                altura_total += 34
                continue

            if tipo == "subtitulo":
                items.append((tipo, contenido, 12.5, 28))
                altura_total += 28
                continue

            if tipo == "texto":
                lineas = textwrap.wrap(contenido, width=76) or [contenido]
                for linea in lineas:
                    items.append((tipo, linea, 10.5, 22))
                    altura_total += 22
                continue

            if tipo == "resultado":
                items.append((tipo, contenido, 15.5, 46))
                altura_total += 46
                continue

            items.append((tipo, contenido, 14, 42))
            altura_total += 42

        return items, max(altura_total + 16, 420)

    def _renderizar_resultado_matematico(self, bloques, texto_respaldo: str):
        if FigureCanvas is None or Figure is None or self.resultados_layout is None:
            if self.resultados_texto is not None:
                self.resultados_texto.setPlainText(texto_respaldo)
            return

        ancho_disponible = 0
        if self.resultados_scroll is not None:
            ancho_disponible = self.resultados_scroll.viewport().width()
        ancho_px = max(ancho_disponible - 32, 620)
        items, altura_px = self._crear_items_resultado(bloques)

        figura = Figure(figsize=(ancho_px / 110, altura_px / 110), dpi=110)
        figura.patch.set_facecolor("white")
        eje = figura.add_subplot(111)
        figura.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
        eje.axis("off")

        y_actual = altura_px - 18
        for tipo, contenido, tamano, paso in items:
            if tipo == "espacio":
                y_actual -= paso
                continue

            y_rel = y_actual / altura_px
            comunes = {
                "transform": eje.transAxes,
                "ha": "left",
                "va": "top",
            }

            if tipo == "titulo":
                eje.text(
                    0.02,
                    y_rel,
                    contenido,
                    fontsize=tamano,
                    fontfamily="serif",
                    fontweight="bold",
                    color="#1d1d1f",
                    **comunes,
                )
            elif tipo == "subtitulo":
                eje.text(
                    0.02,
                    y_rel,
                    contenido,
                    fontsize=tamano,
                    fontfamily="serif",
                    fontweight="bold",
                    color="#1d1d1f",
                    **comunes,
                )
            elif tipo == "texto":
                eje.text(0.02, y_rel, contenido, fontsize=tamano, fontfamily="serif", color="#424245", **comunes)
            elif tipo == "resultado":
                eje.text(0.02, y_rel, contenido, fontsize=tamano, color="#1d1d1f", **comunes)
            else:
                eje.text(0.02, y_rel, contenido, fontsize=tamano, color="#1d1d1f", **comunes)

            y_actual -= paso

        self._limpiar_panel_resultados()
        canvas = FigureCanvas(figura)
        canvas.draw()
        canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        canvas.setFixedHeight(altura_px)
        self.resultados_layout.addWidget(canvas)
        self.resultados_layout.addStretch(1)

        if self.resultados_scroll is not None:
            self.resultados_scroll.verticalScrollBar().setValue(0)

    def _mostrar_resultado_media(self, muestra, resultado):
        muestra_texto = ", ".join(f"{valor:g}" for valor in muestra)
        bloques = [
            ("titulo", "Intervalo de confianza para la media"),
            ("texto", f"Muestra manual: {muestra_texto}"),
            ("texto", "Poblacion normal con varianza desconocida."),
            ("espacio", ""),
            ("subtitulo", "Parametros muestrales"),
            ("math", rf"$n = {resultado.n},\quad \nu = {resultado.gl}$"),
            ("math", rf"$\bar{{x}} = {resultado.media:.6f},\quad s = {resultado.desvio:.6f}$"),
            ("math", rf"$\alpha = {resultado.alpha:.4f},\quad t_{{1-\alpha/2,\nu}} = {resultado.t_critico:.6f}$"),
            ("espacio", ""),
            ("subtitulo", "Forma del intervalo"),
            (
                "math",
                r"$IC_{\mu} = \left(\bar{x} - t_{1-\alpha/2,\nu}\frac{s}{\sqrt{n}},\; "
                r"\bar{x} + t_{1-\alpha/2,\nu}\frac{s}{\sqrt{n}}\right)$",
            ),
            (
                "math",
                rf"$IC_{{\mu}} = \left({resultado.media:.6f} - {resultado.t_critico:.6f}"
                rf"\frac{{{resultado.desvio:.6f}}}{{\sqrt{{{resultado.n}}}}},\; "
                rf"{resultado.media:.6f} + {resultado.t_critico:.6f}"
                rf"\frac{{{resultado.desvio:.6f}}}{{\sqrt{{{resultado.n}}}}}\right)$",
            ),
            ("espacio", ""),
            ("subtitulo", "Resultado"),
            ("resultado", rf"$IC_{{\mu}} = \left({resultado.ic_inf:.6f},\; {resultado.ic_sup:.6f}\right)$"),
        ]
        self._renderizar_resultado_matematico(
            bloques,
            f"IC para mu = ({resultado.ic_inf:.6f}, {resultado.ic_sup:.6f})",
        )

    def _mostrar_resultado_varianza(self, muestra, resultado):
        muestra_texto = ", ".join(f"{valor:g}" for valor in muestra)
        bloques = [
            ("titulo", "Intervalo de confianza para la varianza"),
            ("texto", f"Muestra manual: {muestra_texto}"),
            ("texto", "Poblacion normal con media desconocida."),
            ("espacio", ""),
            ("subtitulo", "Parametros muestrales"),
            ("math", rf"$n = {resultado.n},\quad \nu = {resultado.gl}$"),
            (
                "math",
                rf"$\bar{{x}} = {resultado.media:.6f},\quad s^2 = {resultado.varianza_muestral:.6f},"
                rf"\quad s = {resultado.desvio:.6f}$",
            ),
            (
                "math",
                rf"$\alpha = {resultado.alpha:.4f},\quad \chi^2_{{\alpha/2,\nu}} = "
                rf"{resultado.chi2_izq:.6f},\quad \chi^2_{{1-\alpha/2,\nu}} = {resultado.chi2_der:.6f}$",
            ),
            ("espacio", ""),
            ("subtitulo", "Forma del intervalo"),
            (
                "math",
                r"$IC_{\sigma^2} = \left(\frac{\nu s^2}{\chi^2_{1-\alpha/2,\nu}},\; "
                r"\frac{\nu s^2}{\chi^2_{\alpha/2,\nu}}\right)$",
            ),
            ("espacio", ""),
            ("subtitulo", "Resultado"),
            (
                "resultado",
                rf"$IC_{{\sigma^2}} = \left({resultado.ic_var_inf:.6f},\; {resultado.ic_var_sup:.6f}\right)$",
            ),
            (
                "resultado",
                rf"$IC_{{\sigma}} = \left({resultado.ic_desv_inf:.6f},\; {resultado.ic_desv_sup:.6f}\right)$",
            ),
        ]
        self._renderizar_resultado_matematico(
            bloques,
            f"IC para sigma^2 = ({resultado.ic_var_inf:.6f}, {resultado.ic_var_sup:.6f})\n"
            f"IC para sigma = ({resultado.ic_desv_inf:.6f}, {resultado.ic_desv_sup:.6f})",
        )

    def _dibujar_grafico_vacio(self):
        if self.canvas_grafico is None or self.ax_serie is None or self.ax_hist is None or self.fig is None:
            return

        self.ax_serie.clear()
        self.ax_hist.clear()

        self.ax_serie.set_title("Serie de la muestra")
        self.ax_serie.text(0.5, 0.5, "Sin muestra calculada", ha="center", va="center", transform=self.ax_serie.transAxes)
        self.ax_serie.set_xticks([])
        self.ax_serie.set_yticks([])

        self.ax_hist.set_title("Histograma de la muestra")
        self.ax_hist.text(0.5, 0.5, "Sin muestra calculada", ha="center", va="center", transform=self.ax_hist.transAxes)
        self.ax_hist.set_xticks([])
        self.ax_hist.set_yticks([])

        self._ajustar_layout_graficos()
        self.canvas_grafico.draw_idle()

    def _actualizar_grafico_muestra(self, muestra):
        if self.canvas_grafico is None or self.ax_serie is None or self.ax_hist is None or self.fig is None:
            return

        valores = np.array(muestra, dtype=float)
        x = np.arange(1, len(valores) + 1)

        self.ax_serie.clear()
        self.ax_serie.plot(
            x,
            valores,
            color="#111111",
            marker="o",
            linewidth=1.8,
            markersize=3.8,
            markerfacecolor="#f0c419",
            markeredgecolor="#111111",
        )
        self.ax_serie.set_title(f"Serie de observaciones (n={len(valores)})")
        self.ax_serie.set_xlabel("Observacion")
        self.ax_serie.set_ylabel("Valor")
        self.ax_serie.grid(alpha=0.2)

        self.ax_hist.clear()
        bins = min(20, max(8, int(math.sqrt(len(valores)))))
        self.ax_hist.hist(valores, bins=bins, density=True, color="#bfbfbf", edgecolor="#111111", alpha=0.85)

        desvio = np.std(valores, ddof=1)
        if desvio > 0:
            x_pdf = np.linspace(valores.min(), valores.max(), 300)
            y_pdf = stats.norm.pdf(x_pdf, loc=valores.mean(), scale=desvio)
            self.ax_hist.plot(x_pdf, y_pdf, color="#f0c419", linewidth=2.2, label="Normal ajustada")
            self.ax_hist.legend(loc="best", fontsize=8)

        self.ax_hist.set_title("Histograma de la muestra")
        self.ax_hist.set_xlabel("Valor")
        self.ax_hist.set_ylabel("Densidad")
        self.ax_hist.grid(alpha=0.2)

        self._ajustar_layout_graficos()
        self.canvas_grafico.draw_idle()

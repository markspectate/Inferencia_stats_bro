from __future__ import annotations

import math
import sys
import textwrap

import numpy as np
from scipy import stats

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
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

    mpl.rcParams["mathtext.fontset"] = "cm"
except Exception:
    mpl = None
    FigureCanvas = None
    Figure = None

from calculos.chi_cuadrado import calcular_ic_varianza
from calculos.dataframe_finanzas import (
    DependenciaDataFrameError,
    calcular_ic_desde_muestra,
    descargar_muestra_cotizaciones,
)
from calculos.t_student import calcular_ic_media


class AppEstadistica(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Intervalos de confianza - Estadistica")
        self.resize(1240, 780)
        self.setMinimumSize(1040, 700)

        self.contador_ejercicios = 0
        self.tipo_calculo = "media"

        self.confianza_input = QLineEdit("0.95")
        self.ticker_input = QLineEdit("AAPL")
        self.dias_dataframe_input = QLineEdit("120")
        self.texto_muestra = QPlainTextEdit("70, 47, 42, 51, 56, 71, 75, 61, 62")

        self.estado_tipo_label: QLabel | None = None
        self.label_contador: QLabel | None = None
        self.resultados_scroll: QScrollArea | None = None
        self.resultados_host: QWidget | None = None
        self.resultados_layout: QVBoxLayout | None = None
        self.resultados_texto: QPlainTextEdit | None = None
        self.canvas_grafico = None
        self.fig = None
        self.ax_serie = None
        self.ax_hist = None

        self._aplicar_estilo()
        self._construir_interfaz()

    def _aplicar_estilo(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background: #f5f5f7;
            }
            QWidget {
                color: #1d1d1f;
                font-family: "SF Pro Text", "Segoe UI", Arial, sans-serif;
                font-size: 14px;
            }
            QLabel#Titulo {
                font-size: 28px;
                font-weight: 700;
                letter-spacing: 0px;
            }
            QLabel#Subtitulo,
            QLabel#Ayuda {
                color: #6e6e73;
            }
            QLabel#TipoActual {
                color: #0071e3;
                font-weight: 600;
            }
            QLabel#Contador {
                font-size: 42px;
                font-weight: 700;
                color: #1d1d1f;
            }
            QGroupBox {
                background: #ffffff;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                margin-top: 14px;
                padding: 20px 14px 14px 14px;
                font-weight: 650;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 14px;
                top: 0px;
                padding: 0 6px;
                color: #1d1d1f;
                background: #ffffff;
            }
            QLineEdit,
            QPlainTextEdit {
                background: #fbfbfd;
                border: 1px solid #c7c7cc;
                border-radius: 8px;
                padding: 8px 10px;
                selection-background-color: #0071e3;
            }
            QLineEdit {
                min-height: 24px;
            }
            QPlainTextEdit {
                min-height: 70px;
            }
            QLineEdit:focus,
            QPlainTextEdit:focus {
                border: 1px solid #0071e3;
                background: #ffffff;
            }
            QPushButton {
                background: #ffffff;
                border: 1px solid #c7c7cc;
                border-radius: 8px;
                min-height: 22px;
                padding: 9px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #f2f2f4;
            }
            QPushButton:pressed {
                background: #e9e9ed;
            }
            QPushButton#Principal {
                background: #0071e3;
                border-color: #0071e3;
                color: white;
            }
            QPushButton#Principal:hover {
                background: #0077ed;
            }
            QPushButton#Suave {
                background: #f8f8fa;
            }
            QRadioButton {
                spacing: 8px;
                min-height: 24px;
                padding: 4px 0;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 1px solid #8e8e93;
                background: #ffffff;
            }
            QRadioButton::indicator:checked {
                border: 5px solid #0071e3;
                background: #ffffff;
            }
            QScrollArea {
                border: 0;
                background: transparent;
            }
            QSplitter::handle {
                background: transparent;
                width: 18px;
            }
            QMenu {
                background: white;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 18px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background: #e8f2ff;
                color: #1d1d1f;
            }
            """
        )

    def _construir_interfaz(self):
        central = QWidget()
        raiz = QVBoxLayout(central)
        raiz.setContentsMargins(20, 18, 20, 20)
        raiz.setSpacing(16)
        self.setCentralWidget(central)

        raiz.addLayout(self._construir_encabezado())

        divisor = QSplitter(Qt.Orientation.Horizontal)
        divisor.setChildrenCollapsible(False)
        divisor.addWidget(self._construir_panel_izquierdo())
        divisor.addWidget(self._construir_panel_derecho())
        divisor.setSizes([720, 500])
        raiz.addWidget(divisor, stretch=1)

    def _construir_encabezado(self):
        fila = QHBoxLayout()
        fila.setSpacing(16)

        textos = QVBoxLayout()
        titulo = QLabel("Intervalos de confianza")
        titulo.setObjectName("Titulo")
        subtitulo = QLabel("Muestra manual y cotizaciones reales para media, varianza y desvio.")
        subtitulo.setObjectName("Subtitulo")
        textos.addWidget(titulo)
        textos.addWidget(subtitulo)
        fila.addLayout(textos, stretch=1)

        self.estado_tipo_label = QLabel(self._texto_tipo_seleccionado())
        self.estado_tipo_label.setObjectName("TipoActual")
        self.estado_tipo_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        fila.addWidget(self.estado_tipo_label)

        selector = QPushButton("Cambiar calculo")
        selector.setObjectName("Suave")
        menu = QMenu(selector)
        accion_media = QAction("IC de media (T de Student)", self)
        accion_varianza = QAction("IC de varianza (Chi Cuadrado)", self)
        accion_media.triggered.connect(lambda: self.seleccionar_tipo("media"))
        accion_varianza.triggered.connect(lambda: self.seleccionar_tipo("varianza"))
        menu.addAction(accion_media)
        menu.addAction(accion_varianza)
        selector.setMenu(menu)
        fila.addWidget(selector)

        return fila

    def _construir_panel_izquierdo(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._construir_caja_configuracion())
        layout.addWidget(self._construir_caja_muestra())
        layout.addWidget(self._construir_caja_dataframe())
        layout.addLayout(self._construir_botones_accion())
        layout.addWidget(self._construir_caja_resultados(), stretch=1)

        return panel

    def _construir_panel_derecho(self):
        panel = QWidget()
        panel.setMinimumWidth(410)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        caja_contador = QGroupBox("Ejercicios del dia")
        contador_layout = QVBoxLayout(caja_contador)
        contador_layout.setSpacing(8)

        self.label_contador = QLabel("0")
        self.label_contador.setObjectName("Contador")
        self.label_contador.setAlignment(Qt.AlignmentFlag.AlignCenter)
        contador_layout.addWidget(self.label_contador)

        texto_contador = QLabel("Se incrementa cuando un calculo termina correctamente.")
        texto_contador.setObjectName("Ayuda")
        texto_contador.setWordWrap(True)
        texto_contador.setAlignment(Qt.AlignmentFlag.AlignCenter)
        contador_layout.addWidget(texto_contador)

        boton_reiniciar = QPushButton("Reiniciar contador")
        boton_reiniciar.clicked.connect(self.reiniciar_contador)
        contador_layout.addWidget(boton_reiniciar)
        layout.addWidget(caja_contador)

        caja_grafico = QGroupBox("Distribucion de la muestra")
        grafico_layout = QVBoxLayout(caja_grafico)
        grafico_layout.setContentsMargins(12, 18, 12, 12)
        self._construir_panel_grafico(grafico_layout)
        layout.addWidget(caja_grafico, stretch=1)

        return panel

    def _construir_caja_configuracion(self):
        caja = QGroupBox("Configuracion del ejercicio")
        caja.setMinimumHeight(150)
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

        self.texto_muestra.setMinimumHeight(76)
        self.texto_muestra.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.texto_muestra)

        return caja

    def _construir_caja_dataframe(self):
        caja = QGroupBox("Calculo con DataFrame real")
        caja.setMinimumHeight(125)
        layout = QVBoxLayout(caja)
        layout.setSpacing(10)

        fila_inputs = QHBoxLayout()
        fila_inputs.setSpacing(10)
        fila_inputs.addWidget(QLabel("Ticker:"))
        self.ticker_input.setMaximumWidth(140)
        fila_inputs.addWidget(self.ticker_input)

        fila_inputs.addWidget(QLabel("Cantidad de dias:"))
        self.dias_dataframe_input.setMaximumWidth(100)
        fila_inputs.addWidget(self.dias_dataframe_input)
        fila_inputs.addStretch(1)
        layout.addLayout(fila_inputs)

        boton = QPushButton("Calcular con cotizaciones")
        boton.setObjectName("Principal")
        boton.setMinimumWidth(220)
        boton.clicked.connect(self.calcular_con_dataframe)
        layout.addWidget(boton, alignment=Qt.AlignmentFlag.AlignLeft)

        return caja

    def _construir_botones_accion(self):
        fila = QHBoxLayout()
        fila.setSpacing(10)

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
        layout.setContentsMargins(10, 18, 10, 10)

        if FigureCanvas is None or Figure is None:
            self.resultados_texto = QPlainTextEdit()
            self.resultados_texto.setReadOnly(True)
            layout.addWidget(self.resultados_texto)
        else:
            self.resultados_scroll = QScrollArea()
            self.resultados_scroll.setWidgetResizable(True)
            self.resultados_host = QWidget()
            self.resultados_host.setStyleSheet("background: #ffffff;")
            self.resultados_layout = QVBoxLayout(self.resultados_host)
            self.resultados_layout.setContentsMargins(4, 4, 4, 4)
            self.resultados_layout.setSpacing(0)
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

        self.fig = Figure(figsize=(4.6, 5.2), dpi=100)
        self.fig.patch.set_facecolor("#ffffff")
        self.ax_serie = self.fig.add_subplot(211)
        self.ax_hist = self.fig.add_subplot(212)
        self.canvas_grafico = FigureCanvas(self.fig)
        self.canvas_grafico.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.canvas_grafico)

        self._dibujar_grafico_vacio()

    def seleccionar_tipo(self, tipo: str):
        self.tipo_calculo = tipo
        if tipo == "media" and not self.radio_media.isChecked():
            self.radio_media.setChecked(True)
        if tipo == "varianza" and not self.radio_varianza.isChecked():
            self.radio_varianza.setChecked(True)
        if self.estado_tipo_label is not None:
            self.estado_tipo_label.setText(self._texto_tipo_seleccionado())

    def _texto_tipo_seleccionado(self):
        if self.tipo_calculo == "media":
            return "Seleccion actual: T de Student"
        return "Seleccion actual: Chi Cuadrado"

    def obtener_muestra(self):
        contenido = self.texto_muestra.toPlainText().strip()
        if not contenido:
            raise ValueError("Debes ingresar una muestra.")

        try:
            muestra = [float(x.strip()) for x in contenido.replace("\n", ",").split(",") if x.strip()]
        except ValueError as exc:
            raise ValueError("La muestra contiene valores no numericos.") from exc

        if len(muestra) < 2:
            raise ValueError("La muestra debe tener al menos 2 observaciones.")

        return muestra

    def obtener_confianza(self):
        try:
            confianza = float(self.confianza_input.text().strip())
        except ValueError as exc:
            raise ValueError("El nivel de confianza debe ser numerico.") from exc

        if not (0 < confianza < 1):
            raise ValueError("El nivel de confianza debe estar entre 0 y 1.")

        return confianza

    def obtener_dias_dataframe(self):
        try:
            dias = int(self.dias_dataframe_input.text().strip())
        except ValueError as exc:
            raise ValueError("La cantidad de dias debe ser un entero.") from exc

        if dias < 2:
            raise ValueError("La cantidad de dias debe ser mayor o igual a 2.")
        if dias > 2000:
            raise ValueError("Por ahora se permite como maximo 2000 dias.")

        return dias

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

            self._incrementar_contador()
        except Exception as exc:
            self._mostrar_error("Error", str(exc))

    def calcular_con_dataframe(self):
        try:
            ticker = self.ticker_input.text().strip().upper()
            dias = self.obtener_dias_dataframe()
            confianza = self.obtener_confianza()

            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                muestra_df = descargar_muestra_cotizaciones(ticker=ticker, dias=dias, columna="Close")
                resultado_df = calcular_ic_desde_muestra(muestra_df.valores, confianza)
            finally:
                QApplication.restoreOverrideCursor()

            self._mostrar_resultado_dataframe(muestra_df, resultado_df)
            self._actualizar_grafico_distribucion(muestra_df)
            self._incrementar_contador()
        except DependenciaDataFrameError as exc:
            self._mostrar_error("Dependencias faltantes", str(exc))
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

    def cargar_ejemplo_varianza(self):
        self.seleccionar_tipo("varianza")
        self.confianza_input.setText("0.95")
        self.texto_muestra.setPlainText("70, 47, 42, 51, 56, 71, 75, 61, 62")

    def reiniciar_contador(self):
        self.contador_ejercicios = 0
        if self.label_contador is not None:
            self.label_contador.setText("0")

    def _incrementar_contador(self):
        self.contador_ejercicios += 1
        if self.label_contador is not None:
            self.label_contador.setText(str(self.contador_ejercicios))

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
                    color="#0071e3",
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

    def _mostrar_resultado_dataframe(self, muestra_df, resultado_df):
        bloques = [
            ("titulo", "Estimacion con cotizaciones reales"),
            ("texto", f"Ticker: {muestra_df.ticker} | Columna: {muestra_df.columna}"),
            ("texto", f"Rango: {muestra_df.fecha_inicio} a {muestra_df.fecha_fin} | Observaciones: {resultado_df.n}"),
            ("espacio", ""),
            ("subtitulo", "Estimadores"),
            ("math", rf"$n = {resultado_df.n},\quad \nu = {resultado_df.gl},\quad \alpha = {resultado_df.alpha:.4f}$"),
            (
                "math",
                rf"$\hat{{\mu}} = {resultado_df.media:.6f},\quad \hat{{\sigma}}^2 = "
                rf"{resultado_df.varianza:.6f},\quad \hat{{\sigma}} = {resultado_df.desvio:.6f}$",
            ),
            ("espacio", ""),
            ("subtitulo", "Intervalos de confianza"),
            (
                "resultado",
                rf"$IC_{{\mu}} = \left({resultado_df.ic_media_inf:.6f},\; {resultado_df.ic_media_sup:.6f}\right)$",
            ),
            (
                "resultado",
                rf"$IC_{{\sigma^2}} = \left({resultado_df.ic_var_inf:.6f},\; {resultado_df.ic_var_sup:.6f}\right)$",
            ),
            (
                "resultado",
                rf"$IC_{{\sigma}} = \left({resultado_df.ic_desv_inf:.6f},\; {resultado_df.ic_desv_sup:.6f}\right)$",
            ),
        ]
        self._renderizar_resultado_matematico(
            bloques,
            f"IC(mu)=({resultado_df.ic_media_inf:.6f}, {resultado_df.ic_media_sup:.6f})\n"
            f"IC(sigma^2)=({resultado_df.ic_var_inf:.6f}, {resultado_df.ic_var_sup:.6f})\n"
            f"IC(sigma)=({resultado_df.ic_desv_inf:.6f}, {resultado_df.ic_desv_sup:.6f})",
        )

    def _dibujar_grafico_vacio(self):
        if self.canvas_grafico is None or self.ax_serie is None or self.ax_hist is None or self.fig is None:
            return

        self.ax_serie.clear()
        self.ax_hist.clear()

        self.ax_serie.set_title("Serie temporal")
        self.ax_serie.text(0.5, 0.5, "Sin datos descargados", ha="center", va="center", transform=self.ax_serie.transAxes)
        self.ax_serie.set_xticks([])
        self.ax_serie.set_yticks([])

        self.ax_hist.set_title("Histograma")
        self.ax_hist.text(0.5, 0.5, "Sin datos descargados", ha="center", va="center", transform=self.ax_hist.transAxes)
        self.ax_hist.set_xticks([])
        self.ax_hist.set_yticks([])

        self.fig.tight_layout(pad=1.3)
        self.canvas_grafico.draw_idle()

    def _actualizar_grafico_distribucion(self, muestra):
        if self.canvas_grafico is None or self.ax_serie is None or self.ax_hist is None or self.fig is None:
            return

        valores = np.array(muestra.valores, dtype=float)
        x = np.arange(1, len(valores) + 1)

        self.ax_serie.clear()
        self.ax_serie.plot(x, valores, color="#0071e3", marker="o", linewidth=1.8, markersize=3.5)
        self.ax_serie.set_title(f"{muestra.ticker}: {muestra.fecha_inicio} a {muestra.fecha_fin}")
        self.ax_serie.set_xlabel("Observacion")
        self.ax_serie.set_ylabel("Cierre")
        self.ax_serie.grid(alpha=0.2)

        self.ax_hist.clear()
        bins = min(20, max(8, int(math.sqrt(len(valores)))))
        self.ax_hist.hist(valores, bins=bins, density=True, color="#34c759", edgecolor="#0b6b2d", alpha=0.68)

        desvio = np.std(valores, ddof=1)
        if desvio > 0:
            x_pdf = np.linspace(valores.min(), valores.max(), 300)
            y_pdf = stats.norm.pdf(x_pdf, loc=valores.mean(), scale=desvio)
            self.ax_hist.plot(x_pdf, y_pdf, color="#ff3b30", linewidth=2, label="Normal ajustada")
            self.ax_hist.legend(loc="best", fontsize=8)

        self.ax_hist.set_title("Distribucion de precios")
        self.ax_hist.set_xlabel("Precio de cierre")
        self.ax_hist.set_ylabel("Densidad")
        self.ax_hist.grid(alpha=0.2)

        self.fig.tight_layout(pad=1.3)
        self.canvas_grafico.draw_idle()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Intervalos de confianza")
    window = AppEstadistica()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

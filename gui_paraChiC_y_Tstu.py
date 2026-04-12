import math
import textwrap
import tkinter as tk
from tkinter import messagebox, ttk

import numpy as np
from scipy import stats

try:
    import matplotlib as mpl
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    mpl.rcParams["mathtext.fontset"] = "cm"
except Exception:
    mpl = None
    FigureCanvasTkAgg = None
    Figure = None

from calculos.chi_cuadrado import calcular_ic_varianza
from calculos.dataframe_finanzas import (
    DependenciaDataFrameError,
    calcular_ic_desde_muestra,
    descargar_muestra_cotizaciones,
)
from calculos.t_student import calcular_ic_media


class AppEstadistica:
    def __init__(self, root):
        self.root = root
        self.root.title("Intervalos de confianza - Estadística")
        self.root.geometry("1240x760")
        self.root.minsize(1100, 700)

        self.contador_ejercicios = 0

        self.estilo = ttk.Style()
        try:
            self.estilo.theme_use("clam")
        except tk.TclError:
            pass

        self.estilo.configure("Titulo.TLabel", font=("Arial", 18, "bold"))
        self.estilo.configure("Subtitulo.TLabel", font=("Arial", 11))
        self.estilo.configure("Caja.TLabelframe", padding=12)
        self.estilo.configure("Caja.TLabelframe.Label", font=("Arial", 11, "bold"))
        self.estilo.configure("Boton.TButton", font=("Arial", 11, "bold"), padding=8)
        self.estilo.configure("Contador.TLabel", font=("Arial", 24, "bold"))
        self.estilo.configure("Nav.TLabel", font=("Arial", 20, "bold"), foreground="#0C4A6E")
        self.estilo.configure("NavInfo.TLabel", font=("Arial", 20), foreground="#475569")

        self.tipo_calculo = tk.StringVar(value="media")
        self.confianza_var = tk.StringVar(value="0.95")
        self.muestra_var = tk.StringVar(value="70, 47, 42, 51, 56, 71, 75, 61, 62")
        self.ticker_var = tk.StringVar(value="AAPL")
        self.dias_dataframe_var = tk.StringVar(value="120")
        self.tipo_calculo.trace_add("write", self._al_cambiar_tipo_calculo)

        self.menu_dataframe = None
        self._cerrar_menu_job = None

        self.canvas_grafico = None
        self.fig = None
        self.ax_serie = None
        self.ax_hist = None
        self.resultados_canvas = None
        self.resultados_scrollbar = None
        self.resultados_frame = None
        self.resultados_window = None
        self.resultado_canvas = None
        self.resultado_figura = None
        self.resultados_texto = None

        self._construir_interfaz()

    def _construir_interfaz(self):
        contenedor = ttk.Frame(self.root, padding=16)
        contenedor.pack(fill="both", expand=True)

        barra_nav = ttk.Frame(contenedor)
        barra_nav.pack(fill="x", pady=(0, 12))

        self.boton_nav_dataframe = ttk.Label(
            barra_nav,
            text="Calculo con DataFrames",
            style="Nav.TLabel",
            cursor="hand2",
        )
        self.boton_nav_dataframe.pack(side="left")

        self.estado_tipo_label = ttk.Label(
            barra_nav,
            text=self._texto_tipo_seleccionado(),
            style="NavInfo.TLabel",
        )
        self.estado_tipo_label.pack(side="left", padx=(14, 0))

        self._construir_menu_dataframe()

        encabezado = ttk.Frame(contenedor)
        encabezado.pack(fill="x", pady=(0, 12))

        ttk.Label(
            encabezado,
            text="Intervalos de confianza en poblaciones normales",
            style="Titulo.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            encabezado,
            text="Incluye muestra manual o cotizaciones reales (DataFrame) para estimar media, varianza y desvio.",
            style="Subtitulo.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        cuerpo = ttk.Frame(contenedor)
        cuerpo.pack(fill="both", expand=True)

        panel_izquierdo = ttk.Frame(cuerpo)
        panel_izquierdo.pack(side="left", fill="both", expand=True)

        panel_derecho = ttk.Frame(cuerpo, width=600)
        panel_derecho.pack(side="right", fill="both", padx=(50, 0))
        panel_derecho.pack_propagate(False)

        caja_config = ttk.LabelFrame(panel_izquierdo, text="Configuración del ejercicio", style="Caja.TLabelframe")
        caja_config.pack(fill="x", pady=(0, 12))

        ttk.Label(caja_config, text="Tipo de cálculo:").grid(row=0, column=0, sticky="w", pady=(0, 8))
        fila_radios = ttk.Frame(caja_config)
        fila_radios.grid(row=0, column=1, sticky="w", pady=(0, 8))

        ttk.Radiobutton(
            fila_radios,
            text="IC para la media (σ² desconocida)",
            variable=self.tipo_calculo,
            value="media",
        ).pack(anchor="w")
        ttk.Radiobutton(
            fila_radios,
            text="IC para la varianza (μ desconocida)",
            variable=self.tipo_calculo,
            value="varianza",
        ).pack(anchor="w", pady=(4, 0))

        ttk.Label(caja_config, text="Nivel de confianza:").grid(row=1, column=0, sticky="w", pady=8)
        entrada_confianza = ttk.Entry(caja_config, textvariable=self.confianza_var, width=12)
        entrada_confianza.grid(row=1, column=1, sticky="w", pady=8)

        ttk.Label(
            caja_config,
            text="Usá valores como 0.90, 0.95 o 0.99",
            foreground="#444",
        ).grid(row=2, column=1, sticky="w")

        caja_muestra = ttk.LabelFrame(panel_izquierdo, text="Datos de la muestra manual", style="Caja.TLabelframe")
        caja_muestra.pack(fill="both", expand=False, pady=(0, 12))

        ttk.Label(caja_muestra, text="Ingresá los datos separados por comas:").pack(anchor="w", pady=(0, 8))
        self.texto_muestra = tk.Text(caja_muestra, height=5, wrap="word", font=("Consolas", 11))
        self.texto_muestra.pack(fill="x", expand=True)
        self.texto_muestra.insert("1.0", self.muestra_var.get())

        caja_dataframe = ttk.LabelFrame(panel_izquierdo, text="Calculo con DataFrame real", style="Caja.TLabelframe")
        caja_dataframe.pack(fill="x", pady=(0, 12))

        ttk.Label(caja_dataframe, text="Ticker:").grid(row=0, column=0, sticky="w")
        ttk.Entry(caja_dataframe, textvariable=self.ticker_var, width=14).grid(row=0, column=1, sticky="w", padx=(6, 16))

        ttk.Label(caja_dataframe, text="Cantidad de días:").grid(row=0, column=2, sticky="w")
        ttk.Entry(caja_dataframe, textvariable=self.dias_dataframe_var, width=10).grid(row=0, column=3, sticky="w", padx=(6, 0))

        ttk.Button(
            caja_dataframe,
            text="Descargar cotizaciones y calcular IC",
            style="Boton.TButton",
            command=self.calcular_con_dataframe,
        ).grid(row=1, column=0, columnspan=4, sticky="w", pady=(10, 0))

        ttk.Label(
            caja_dataframe,
            text="Ejemplo: AAPL con 120 días de cierre.",
            foreground="#444",
        ).grid(row=2, column=0, columnspan=4, sticky="w", pady=(8, 0))

        botones = ttk.Frame(panel_izquierdo)
        botones.pack(fill="x", pady=(0, 12))

        ttk.Button(botones, text="Confirmar muestra manual", style="Boton.TButton", command=self.calcular).pack(side="left")
        ttk.Button(botones, text="Limpiar", command=self.limpiar).pack(side="left", padx=(10, 0))
        ttk.Button(botones, text="Cargar ejemplo media", command=self.cargar_ejemplo_media).pack(side="left", padx=(10, 0))
        ttk.Button(botones, text="Cargar ejemplo varianza", command=self.cargar_ejemplo_varianza).pack(
            side="left", padx=(10, 0)
        )

        caja_resultados = ttk.LabelFrame(panel_izquierdo, text="Resultados", style="Caja.TLabelframe")
        caja_resultados.pack(fill="both", expand=True)
        self._construir_panel_resultados(caja_resultados)

        caja_contador = ttk.LabelFrame(panel_derecho, text="Ejercicios del día", style="Caja.TLabelframe")
        caja_contador.pack(fill="x")

        self.label_contador = ttk.Label(caja_contador, text="0", style="Contador.TLabel", anchor="center")
        self.label_contador.pack(fill="x", pady=(6, 2))

        ttk.Label(
            caja_contador,
            text="Se incrementa cada vez que un cálculo termina correctamente.",
            wraplength=320,
            justify="center",
        ).pack(pady=(0, 8))

        ttk.Button(panel_derecho, text="Reiniciar contador", command=self.reiniciar_contador).pack(fill="x", pady=(10, 12))

        caja_grafico = ttk.LabelFrame(panel_derecho, text="Distribución de la muestra (DataFrame)", style="Caja.TLabelframe")
        caja_grafico.pack(fill="both", expand=True)
        self._construir_panel_grafico(caja_grafico)

    def _construir_menu_dataframe(self):
        self.menu_dataframe = tk.Menu(self.root, tearoff=0)
        self.menu_dataframe.add_command(
            label="IC de media (T de Student)",
            command=lambda: self.seleccionar_tipo_desde_menu("media"),
        )
        self.menu_dataframe.add_command(
            label="IC de varianza (Chi Cuadrado)",
            command=lambda: self.seleccionar_tipo_desde_menu("varianza"),
        )

        self.boton_nav_dataframe.bind("<Enter>", self._mostrar_menu_dataframe)
        self.boton_nav_dataframe.bind("<Leave>", self._programar_cierre_menu_dataframe)
        self.boton_nav_dataframe.bind("<Button-1>", self._mostrar_menu_dataframe)

        self.menu_dataframe.bind("<Enter>", self._cancelar_cierre_menu_dataframe)
        self.menu_dataframe.bind("<Leave>", self._programar_cierre_menu_dataframe)

    def _mostrar_menu_dataframe(self, _event=None):
        self._cancelar_cierre_menu_dataframe()
        x = self.boton_nav_dataframe.winfo_rootx()
        y = self.boton_nav_dataframe.winfo_rooty() + self.boton_nav_dataframe.winfo_height()
        self.menu_dataframe.post(x, y)

    def _programar_cierre_menu_dataframe(self, _event=None):
        self._cancelar_cierre_menu_dataframe()
        self._cerrar_menu_job = self.root.after(180, self._ocultar_menu_dataframe)

    def _cancelar_cierre_menu_dataframe(self, _event=None):
        if self._cerrar_menu_job is not None:
            self.root.after_cancel(self._cerrar_menu_job)
            self._cerrar_menu_job = None

    def _ocultar_menu_dataframe(self):
        try:
            self.menu_dataframe.unpost()
        except tk.TclError:
            pass
        self._cerrar_menu_job = None

    def _construir_panel_grafico(self, parent):
        if FigureCanvasTkAgg is None or Figure is None:
            ttk.Label(
                parent,
                text="No se pudo cargar matplotlib.\nInstalá matplotlib para ver el gráfico.",
                justify="center",
                wraplength=300,
            ).pack(fill="both", expand=True, padx=10, pady=10)
            return

        self.fig = Figure(figsize=(4.0, 5.4), dpi=100)
        self.ax_serie = self.fig.add_subplot(211)
        self.ax_hist = self.fig.add_subplot(212)
        self.canvas_grafico = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas_grafico.get_tk_widget().pack(fill="both", expand=True)

        self._dibujar_grafico_vacio()

    def _construir_panel_resultados(self, parent):
        if FigureCanvasTkAgg is None or Figure is None:
            self.resultados_texto = tk.Text(parent, height=18, wrap="word", font=("Consolas", 11))
            self.resultados_texto.pack(fill="both", expand=True)
            barra = ttk.Scrollbar(self.resultados_texto, orient="vertical", command=self.resultados_texto.yview)
            self.resultados_texto.configure(yscrollcommand=barra.set)
            barra.pack(side="right", fill="y")
            self._mostrar_resultado_inicial()
            return

        self.resultados_canvas = tk.Canvas(parent, highlightthickness=0, bd=0, background="white")
        self.resultados_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.resultados_canvas.yview)
        self.resultados_canvas.configure(yscrollcommand=self.resultados_scrollbar.set)
        self.resultados_canvas.pack(side="left", fill="both", expand=True)
        self.resultados_scrollbar.pack(side="right", fill="y")

        self.resultados_frame = tk.Frame(self.resultados_canvas, bg="white")
        self.resultados_window = self.resultados_canvas.create_window((0, 0), window=self.resultados_frame, anchor="nw")
        self.resultados_frame.bind("<Configure>", self._actualizar_scroll_resultados)
        self.resultados_canvas.bind("<Configure>", self._ajustar_ancho_resultados)

        self._mostrar_resultado_inicial()

    def _actualizar_scroll_resultados(self, _event=None):
        if self.resultados_canvas is not None:
            self.resultados_canvas.configure(scrollregion=self.resultados_canvas.bbox("all"))

    def _ajustar_ancho_resultados(self, event):
        if self.resultados_canvas is not None and self.resultados_window is not None:
            self.resultados_canvas.itemconfigure(self.resultados_window, width=event.width)

    def _limpiar_panel_resultados(self):
        if self.resultados_texto is not None:
            self.resultados_texto.delete("1.0", "end")
            return

        if self.resultados_frame is None:
            return

        for widget in self.resultados_frame.winfo_children():
            widget.destroy()

        self.resultado_canvas = None
        self.resultado_figura = None
        self._actualizar_scroll_resultados()

    def _mostrar_resultado_inicial(self):
        mensaje = "Las expresiones matematicas apareceran aqui despues de ejecutar un calculo."
        if self.resultados_texto is not None:
            self.resultados_texto.delete("1.0", "end")
            self.resultados_texto.insert("1.0", mensaje)
            return

        self._limpiar_panel_resultados()
        etiqueta = tk.Label(
            self.resultados_frame,
            text=mensaje,
            bg="white",
            fg="#475569",
            font=("Arial", 12, "italic"),
            justify="left",
            anchor="nw",
            padx=18,
            pady=18,
        )
        etiqueta.pack(fill="both", expand=True)
        self._actualizar_scroll_resultados()

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

    def _renderizar_resultado_matematico(self, bloques, texto_respaldo):
        if FigureCanvasTkAgg is None or Figure is None or self.resultados_frame is None:
            if self.resultados_texto is not None:
                self.resultados_texto.delete("1.0", "end")
                self.resultados_texto.insert("1.0", texto_respaldo)
            return

        self.root.update_idletasks()
        ancho_disponible = self.resultados_canvas.winfo_width() if self.resultados_canvas is not None else 0
        ancho_px = max(ancho_disponible - 24, 500)
        items, altura_px = self._crear_items_resultado(bloques)

        figura = Figure(figsize=(ancho_px / 110, altura_px / 110), dpi=110)
        figura.patch.set_facecolor("white")
        eje = figura.add_subplot(111)
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
                eje.text(0.02, y_rel, contenido, fontsize=tamano, fontfamily="serif", fontweight="bold", color="#0F172A", **comunes)
            elif tipo == "subtitulo":
                eje.text(0.02, y_rel, contenido, fontsize=tamano, fontfamily="serif", fontweight="bold", color="#1D4ED8", **comunes)
            elif tipo == "texto":
                eje.text(0.02, y_rel, contenido, fontsize=tamano, fontfamily="serif", color="#334155", **comunes)
            elif tipo == "resultado":
                eje.text(0.02, y_rel, contenido, fontsize=tamano, color="#111827", **comunes)
            else:
                eje.text(0.02, y_rel, contenido, fontsize=tamano, color="#111827", **comunes)

            y_actual -= paso

        self._limpiar_panel_resultados()
        self.resultado_figura = figura
        self.resultado_canvas = FigureCanvasTkAgg(figura, master=self.resultados_frame)
        self.resultado_canvas.draw()
        self.resultado_canvas.get_tk_widget().pack(fill="x", expand=True, padx=8, pady=8)
        self._actualizar_scroll_resultados()
        if self.resultados_canvas is not None:
            self.resultados_canvas.yview_moveto(0)

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
            ("math", r"$IC_{\mu} = \left(\bar{x} - t_{1-\alpha/2,\nu}\frac{s}{\sqrt{n}},\; \bar{x} + t_{1-\alpha/2,\nu}\frac{s}{\sqrt{n}}\right)$"),
            ("math", rf"$IC_{{\mu}} = \left({resultado.media:.6f} - {resultado.t_critico:.6f}\frac{{{resultado.desvio:.6f}}}{{\sqrt{{{resultado.n}}}}},\; {resultado.media:.6f} + {resultado.t_critico:.6f}\frac{{{resultado.desvio:.6f}}}{{\sqrt{{{resultado.n}}}}}\right)$"),
            ("espacio", ""),
            ("subtitulo", "Resultado"),
            ("resultado", rf"$IC_{{\mu}} = \left({resultado.ic_inf:.6f},\; {resultado.ic_sup:.6f}\right)$"),
        ]
        self._renderizar_resultado_matematico(bloques, f"IC para mu = ({resultado.ic_inf:.6f}, {resultado.ic_sup:.6f})")

    def _mostrar_resultado_varianza(self, muestra, resultado):
        muestra_texto = ", ".join(f"{valor:g}" for valor in muestra)
        bloques = [
            ("titulo", "Intervalo de confianza para la varianza"),
            ("texto", f"Muestra manual: {muestra_texto}"),
            ("texto", "Poblacion normal con media desconocida."),
            ("espacio", ""),
            ("subtitulo", "Parametros muestrales"),
            ("math", rf"$n = {resultado.n},\quad \nu = {resultado.gl}$"),
            ("math", rf"$\bar{{x}} = {resultado.media:.6f},\quad s^2 = {resultado.varianza_muestral:.6f},\quad s = {resultado.desvio:.6f}$"),
            ("math", rf"$\alpha = {resultado.alpha:.4f},\quad \chi^2_{{\alpha/2,\nu}} = {resultado.chi2_izq:.6f},\quad \chi^2_{{1-\alpha/2,\nu}} = {resultado.chi2_der:.6f}$"),
            ("espacio", ""),
            ("subtitulo", "Forma del intervalo"),
            ("math", r"$IC_{\sigma^2} = \left(\frac{\nu s^2}{\chi^2_{1-\alpha/2,\nu}},\; \frac{\nu s^2}{\chi^2_{\alpha/2,\nu}}\right)$"),
            ("espacio", ""),
            ("subtitulo", "Resultado"),
            ("resultado", rf"$IC_{{\sigma^2}} = \left({resultado.ic_var_inf:.6f},\; {resultado.ic_var_sup:.6f}\right)$"),
            ("resultado", rf"$IC_{{\sigma}} = \left({resultado.ic_desv_inf:.6f},\; {resultado.ic_desv_sup:.6f}\right)$"),
        ]
        self._renderizar_resultado_matematico(
            bloques,
            f"IC para sigma^2 = ({resultado.ic_var_inf:.6f}, {resultado.ic_var_sup:.6f})\nIC para sigma = ({resultado.ic_desv_inf:.6f}, {resultado.ic_desv_sup:.6f})",
        )

    def _mostrar_resultado_dataframe(self, muestra_df, resultado_df):
        bloques = [
            ("titulo", "Estimacion con cotizaciones reales"),
            ("texto", f"Ticker: {muestra_df.ticker} | Columna: {muestra_df.columna}"),
            ("texto", f"Rango: {muestra_df.fecha_inicio} a {muestra_df.fecha_fin} | Observaciones: {resultado_df.n}"),
            ("espacio", ""),
            ("subtitulo", "Estimadores"),
            ("math", rf"$n = {resultado_df.n},\quad \nu = {resultado_df.gl},\quad \alpha = {resultado_df.alpha:.4f}$"),
            ("math", rf"$\hat{{\mu}} = {resultado_df.media:.6f},\quad \hat{{\sigma}}^2 = {resultado_df.varianza:.6f},\quad \hat{{\sigma}} = {resultado_df.desvio:.6f}$"),
            ("espacio", ""),
            ("subtitulo", "Intervalos de confianza"),
            ("resultado", rf"$IC_{{\mu}} = \left({resultado_df.ic_media_inf:.6f},\; {resultado_df.ic_media_sup:.6f}\right)$"),
            ("resultado", rf"$IC_{{\sigma^2}} = \left({resultado_df.ic_var_inf:.6f},\; {resultado_df.ic_var_sup:.6f}\right)$"),
            ("resultado", rf"$IC_{{\sigma}} = \left({resultado_df.ic_desv_inf:.6f},\; {resultado_df.ic_desv_sup:.6f}\right)$"),
        ]
        self._renderizar_resultado_matematico(
            bloques,
            f"IC(mu)=({resultado_df.ic_media_inf:.6f}, {resultado_df.ic_media_sup:.6f})\nIC(sigma^2)=({resultado_df.ic_var_inf:.6f}, {resultado_df.ic_var_sup:.6f})\nIC(sigma)=({resultado_df.ic_desv_inf:.6f}, {resultado_df.ic_desv_sup:.6f})",
        )

    def _dibujar_grafico_vacio(self):
        if self.canvas_grafico is None:
            return

        self.ax_serie.clear()
        self.ax_hist.clear()

        self.ax_serie.set_title("Serie temporal")
        self.ax_serie.text(0.5, 0.5, "Sin datos descargados", ha="center", va="center", transform=self.ax_serie.transAxes)
        self.ax_serie.set_xticks([])
        self.ax_serie.set_yticks([])

        self.ax_hist.set_title("Histograma de distribución")
        self.ax_hist.text(0.5, 0.5, "Sin datos descargados", ha="center", va="center", transform=self.ax_hist.transAxes)
        self.ax_hist.set_xticks([])
        self.ax_hist.set_yticks([])

        self.fig.tight_layout(pad=1.3)
        self.canvas_grafico.draw_idle()

    def _actualizar_grafico_distribucion(self, muestra):
        if self.canvas_grafico is None:
            return

        valores = np.array(muestra.valores, dtype=float)
        x = np.arange(1, len(valores) + 1)

        self.ax_serie.clear()
        self.ax_serie.plot(x, valores, color="#0C4A6E", marker="o", linewidth=1.8, markersize=3.5)
        self.ax_serie.set_title(f"{muestra.ticker}: {muestra.fecha_inicio} a {muestra.fecha_fin}")
        self.ax_serie.set_xlabel("Observación")
        self.ax_serie.set_ylabel("Cierre")
        self.ax_serie.grid(alpha=0.2)

        self.ax_hist.clear()
        bins = min(20, max(8, int(math.sqrt(len(valores)))))
        self.ax_hist.hist(valores, bins=bins, density=True, color="#60A5FA", edgecolor="#1E3A8A", alpha=0.75)

        desvio = np.std(valores, ddof=1)
        if desvio > 0:
            x_pdf = np.linspace(valores.min(), valores.max(), 300)
            y_pdf = stats.norm.pdf(x_pdf, loc=valores.mean(), scale=desvio)
            self.ax_hist.plot(x_pdf, y_pdf, color="#DC2626", linewidth=2, label="Normal ajustada")
            self.ax_hist.legend(loc="best", fontsize=8)

        self.ax_hist.set_title("Distribución de precios")
        self.ax_hist.set_xlabel("Precio de cierre")
        self.ax_hist.set_ylabel("Densidad")
        self.ax_hist.grid(alpha=0.2)

        self.fig.tight_layout(pad=1.3)
        self.canvas_grafico.draw_idle()

    def seleccionar_tipo_desde_menu(self, tipo):
        self.tipo_calculo.set(tipo)
        self._ocultar_menu_dataframe()

    def _texto_tipo_seleccionado(self):
        if self.tipo_calculo.get() == "media":
            return "Seleccion actual: T de Student"
        return "Seleccion actual: Chi Cuadrado"

    def _al_cambiar_tipo_calculo(self, *_):
        if hasattr(self, "estado_tipo_label"):
            self.estado_tipo_label.config(text=self._texto_tipo_seleccionado())

    def obtener_muestra(self):
        contenido = self.texto_muestra.get("1.0", "end").strip()
        if not contenido:
            raise ValueError("Debés ingresar una muestra.")

        try:
            muestra = [float(x.strip()) for x in contenido.replace("\n", ",").split(",") if x.strip()]
        except ValueError as exc:
            raise ValueError("La muestra contiene valores no numéricos.") from exc

        if len(muestra) < 2:
            raise ValueError("La muestra debe tener al menos 2 observaciones.")

        return muestra

    def obtener_confianza(self):
        try:
            confianza = float(self.confianza_var.get().strip())
        except ValueError as exc:
            raise ValueError("El nivel de confianza debe ser numérico.") from exc

        if not (0 < confianza < 1):
            raise ValueError("El nivel de confianza debe estar entre 0 y 1.")

        return confianza

    def obtener_dias_dataframe(self):
        try:
            dias = int(self.dias_dataframe_var.get().strip())
        except ValueError as exc:
            raise ValueError("La cantidad de días debe ser un entero.") from exc

        if dias < 2:
            raise ValueError("La cantidad de días debe ser mayor o igual a 2.")
        if dias > 2000:
            raise ValueError("Por ahora se permite como máximo 2000 días.")

        return dias

    def calcular(self):
        try:
            muestra = self.obtener_muestra()
            confianza = self.obtener_confianza()
            if self.tipo_calculo.get() == "media":
                resultado_obj = calcular_ic_media(muestra, confianza)
                self._mostrar_resultado_media(muestra, resultado_obj)
            else:
                resultado_obj = calcular_ic_varianza(muestra, confianza)
                self._mostrar_resultado_varianza(muestra, resultado_obj)

            self.contador_ejercicios += 1
            self.label_contador.config(text=str(self.contador_ejercicios))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def calcular_con_dataframe(self):
        try:
            ticker = self.ticker_var.get().strip().upper()
            dias = self.obtener_dias_dataframe()
            confianza = self.obtener_confianza()

            muestra_df = descargar_muestra_cotizaciones(ticker=ticker, dias=dias, columna="Close")
            resultado_df = calcular_ic_desde_muestra(muestra_df.valores, confianza)
            self._mostrar_resultado_dataframe(muestra_df, resultado_df)
            self._actualizar_grafico_distribucion(muestra_df)

            self.contador_ejercicios += 1
            self.label_contador.config(text=str(self.contador_ejercicios))
        except DependenciaDataFrameError as exc:
            messagebox.showerror("Dependencias faltantes", str(exc))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def limpiar(self):
        self.texto_muestra.delete("1.0", "end")
        self._mostrar_resultado_inicial()
        self._dibujar_grafico_vacio()

    def cargar_ejemplo_media(self):
        self.tipo_calculo.set("media")
        self.confianza_var.set("0.95")
        self.texto_muestra.delete("1.0", "end")
        self.texto_muestra.insert("1.0", "12, 15, 14, 10, 13, 16, 11")

    def cargar_ejemplo_varianza(self):
        self.tipo_calculo.set("varianza")
        self.confianza_var.set("0.95")
        self.texto_muestra.delete("1.0", "end")
        self.texto_muestra.insert("1.0", "70, 47, 42, 51, 56, 71, 75, 61, 62")

    def reiniciar_contador(self):
        self.contador_ejercicios = 0
        self.label_contador.config(text="0")


if __name__ == "__main__":
    root = tk.Tk()
    app = AppEstadistica(root)
    root.mainloop()

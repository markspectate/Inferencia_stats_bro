from __future__ import annotations

import sys

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QMenu,
    QPushButton,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from anexo_demostraciones import AnexoDemostracionesWidget
from intervalos_confianza_page import IntervalosConfianzaPage


class PlataformaEstadistica(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plataforma Estadistica")
        self.resize(1320, 860)
        self.setMinimumSize(1120, 720)

        self.page_intervalos = IntervalosConfianzaPage()
        self.page_anexo = AnexoDemostracionesWidget()

        self.stack: QStackedWidget | None = None
        self.boton_intervalos: QPushButton | None = None
        self.boton_anexo: QToolButton | None = None

        self._aplicar_estilo()
        self._construir_interfaz()
        self._mostrar_intervalos()

    def _aplicar_estilo(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background: #ece9d8;
                color: #1b1b1b;
                font-family: "Segoe UI", "Tahoma", Arial, sans-serif;
                font-size: 13px;
            }
            QFrame#TopNav {
                background: #f2f0e8;
                border: none;
                border-bottom: 1px solid #c8c5ba;
                border-radius: 0px;
            }
            QPushButton#NavButton,
            QToolButton#NavDrop {
                background: transparent;
                color: #3a3a3a;
                border: none;
                border-bottom: 2px solid transparent;
                border-radius: 0px;
                padding: 9px 16px;
                font-weight: 600;
                min-height: 26px;
            }
            QPushButton#NavButton:hover,
            QToolButton#NavDrop:hover {
                background: #e6e3d8;
                color: #1b1b1b;
            }
            QPushButton#NavButton[active="true"],
            QToolButton#NavDrop[active="true"] {
                background: transparent;
                border-bottom: 2px solid #2e6da4;
                color: #123a61;
            }
            QMenu {
                background: #f7f4ea;
                border: 1px solid #9f9f9f;
                border-radius: 3px;
                padding: 6px;
                color: #1b1b1b;
            }
            QMenu::item {
                padding: 9px 16px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background: #cfe4fa;
                color: #123a61;
            }
            """
        )

    def _construir_interfaz(self):
        central = QWidget()
        raiz = QVBoxLayout(central)
        raiz.setContentsMargins(30, 24, 30, 26)
        raiz.setSpacing(20)
        self.setCentralWidget(central)

        barra = QFrame()
        barra.setObjectName("TopNav")
        barra_layout = QHBoxLayout(barra)
        barra_layout.setContentsMargins(14, 12, 14, 12)
        barra_layout.setSpacing(14)

        self.boton_intervalos = QPushButton("Intervalos de confianza")
        self.boton_intervalos.setObjectName("NavButton")
        self.boton_intervalos.clicked.connect(self._mostrar_intervalos)
        barra_layout.addWidget(self.boton_intervalos)

        self.boton_anexo = QToolButton()
        self.boton_anexo.setObjectName("NavDrop")
        self.boton_anexo.setText("Anexo Demostraciones")
        self.boton_anexo.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.boton_anexo.setMenu(self._construir_menu_unidades())
        barra_layout.addWidget(self.boton_anexo)
        barra_layout.addStretch(1)

        raiz.addWidget(barra, stretch=0)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.page_intervalos)
        self.stack.addWidget(self.page_anexo)
        raiz.addWidget(self.stack, stretch=1)

    def _construir_menu_unidades(self):
        menu = QMenu(self)
        for unidad_id, nombre in self.page_anexo.obtener_unidades_menu():
            accion = QAction(nombre, self)
            accion.triggered.connect(lambda _checked=False, uid=unidad_id: self._mostrar_anexo(uid))
            menu.addAction(accion)
        return menu

    def _actualizar_estado_nav(self, vista: str):
        if self.boton_intervalos is None or self.boton_anexo is None:
            return

        self.boton_intervalos.setProperty("active", vista == "intervalos")
        self.boton_anexo.setProperty("active", vista == "anexo")
        for boton in (self.boton_intervalos, self.boton_anexo):
            boton.style().unpolish(boton)
            boton.style().polish(boton)
            boton.update()

    def _mostrar_intervalos(self):
        if self.stack is None:
            return
        self.stack.setCurrentWidget(self.page_intervalos)
        self._actualizar_estado_nav("intervalos")

    def _mostrar_anexo(self, unidad_id: str):
        if self.stack is None:
            return
        self.page_anexo.set_unidad(unidad_id)
        self.stack.setCurrentWidget(self.page_anexo)
        self._actualizar_estado_nav("anexo")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Plataforma Estadistica")
    window = PlataformaEstadistica()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

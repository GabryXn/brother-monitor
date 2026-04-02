# tray.py
from __future__ import annotations
import time

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter
from PyQt6.QtCore import Qt

from printer_client import PrinterData

LEVEL_INFO = QSystemTrayIcon.MessageIcon.Information
LEVEL_WARN = QSystemTrayIcon.MessageIcon.Warning
LEVEL_CRIT = QSystemTrayIcon.MessageIcon.Critical


def _make_icon(color: str) -> QIcon:
    """Genera un'icona circolare del colore dato senza file esterni."""
    px = QPixmap(22, 22)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(2, 2, 18, 18)
    p.end()
    return QIcon(px)


class BrotherTray(QSystemTrayIcon):
    DEBOUNCE_SECS = 3600  # 60 minuti

    def __init__(self, window, parent=None):
        # Le icone vengono create qui, dopo che QApplication esiste
        self._icon_ok   = _make_icon("#4caf50")
        self._icon_warn = _make_icon("#ff9800")
        self._icon_err  = _make_icon("#f44336")

        super().__init__(self._icon_ok, parent)
        self.window = window
        self._last_notified: dict[str, float] = {}

        menu = QMenu()
        self._act_open    = menu.addAction("Apri Monitor Brother")
        self._act_status  = menu.addAction("Stato: —")
        self._act_status.setEnabled(False)
        menu.addSeparator()
        self._act_refresh = menu.addAction("Aggiorna ora")  # wired by caller
        menu.addSeparator()
        menu.addAction("Esci").triggered.connect(QApplication.quit)
        self.setContextMenu(menu)

        self._act_open.triggered.connect(self._show_window)
        self.activated.connect(self._on_activated)
        self.setToolTip("Brother Monitor — DCP-L2550DN")

    # ------------------------------------------------------------------ #

    def _show_window(self) -> None:
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.window.isVisible():
                self.window.hide()
            else:
                self._show_window()

    # ------------------------------------------------------------------ #

    def update_status(self, data: PrinterData) -> None:
        _label = {"idle": "Pronto", "sleep": "Risparmio",
                  "printing": "Stampa in corso...",
                  "error": "Errore", "offline": "Offline"}
        self._act_status.setText(f"Stato: {_label.get(data.status, data.status)}")

        if data.status in ("error", "offline"):
            self.setIcon(self._icon_err)
        elif (data.toner_pct < 15) or (data.drum_pct < 10):
            self.setIcon(self._icon_warn)
        else:
            self.setIcon(self._icon_ok)

        self.setToolTip(
            f"Brother DCP-L2550DN  •  "
            f"Toner: {data.toner_pct}%  •  Tamburo: {data.drum_pct}%"
        )

    def notify(self, key: str, title: str, message: str,
               level: QSystemTrayIcon.MessageIcon = LEVEL_WARN) -> None:
        now = time.monotonic()
        if now - self._last_notified.get(key, float("-inf")) < self.DEBOUNCE_SECS:
            return
        self._last_notified[key] = now
        self.showMessage(title, message, level, 6000)

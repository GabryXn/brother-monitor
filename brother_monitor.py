#!/usr/bin/env python3
# brother_monitor.py
from __future__ import annotations
import sys
import os
from datetime import datetime

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QSettings, Qt

from main_window import MainWindow
from tray import BrotherTray, LEVEL_WARN, LEVEL_CRIT
from printer_client import PrinterClient, PrinterData

APP_NAME = "brother-monitor"
ORG_NAME  = "gabry"


def _check_notifications(tray: BrotherTray, data: PrinterData,
                          settings: QSettings) -> None:
    if not settings.value("notifications/enabled", True, type=bool):
        return
    toner_thresh = settings.value("notifications/toner_threshold", 20, type=int)
    drum_thresh  = settings.value("notifications/drum_threshold",  15, type=int)

    if data.status == "offline":
        tray.notify("offline", "Stampante offline",
                    "La stampante non è raggiungibile.", LEVEL_CRIT)
    elif data.status == "error":
        tray.notify("error", "Errore stampante",
                    f"Errore: {data.status_detail or 'sconosciuto'}", LEVEL_CRIT)

    if data.status not in ("offline", "error"):
        if data.toner_pct < toner_thresh:
            tray.notify("toner", "Toner in esaurimento",
                        f"Toner al {data.toner_pct}% — considera la sostituzione.",
                        LEVEL_WARN)
        if data.drum_pct < drum_thresh:
            tray.notify("drum", "Tamburo in esaurimento",
                        f"Tamburo all'{data.drum_pct}% — considera la sostituzione.",
                        LEVEL_WARN)


def main() -> None:
    # Forza piattaforma xcb (X11) su KDE se non già impostata
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setQuitOnLastWindowClosed(False)   # resta nel tray dopo chiusura finestra

    settings = QSettings(
        QSettings.Format.IniFormat,
        QSettings.Scope.UserScope,
        ORG_NAME, APP_NAME,
    )

    client = PrinterClient()
    window = MainWindow(settings)
    tray   = BrotherTray(window)
    tray.show()

    def do_refresh() -> None:
        data = client.fetch()
        ts   = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        window.update_data(data, ts)
        tray.update_status(data)
        _check_notifications(tray, data, settings)

    # Pulsante "Aggiorna ora" nella finestra
    window.refresh_requested.connect(do_refresh)
    # Voce "Aggiorna ora" nel menu tray
    tray._act_refresh.triggered.connect(do_refresh)

    # Timer di polling
    poll_timer = QTimer()
    poll_timer.timeout.connect(do_refresh)
    interval_sec = settings.value("polling/interval_sec", 60, type=int)
    poll_timer.start(interval_sec * 1000)

    # Aggiorna il timer quando cambiano le impostazioni
    window.refresh_interval_changed.connect(
        lambda secs: poll_timer.setInterval(secs * 1000))

    # Fetch iniziale
    do_refresh()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

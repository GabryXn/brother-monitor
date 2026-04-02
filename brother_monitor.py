#!/usr/bin/env python3
# brother_monitor.py
from __future__ import annotations
import sys
import os
from datetime import datetime

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from config import load_config, save_config, AppConfig
from drivers.base import PrinterData
from drivers.brother_http import BrotherHTTPDriver
from history import HistoryDB
from main_window import MainWindow
from tray import BrotherTray, LEVEL_WARN, LEVEL_CRIT

APP_NAME = "printer-monitor"
ORG_NAME = "gabry"


def _make_driver(printer_cfg):
    if printer_cfg.driver == "brother_http":
        return BrotherHTTPDriver(base_url=printer_cfg.url)
    if printer_cfg.driver == "snmp":
        from drivers.snmp import SNMPDriver
        return SNMPDriver(host=printer_cfg.host, community=printer_cfg.community)
    raise ValueError(f"Unknown driver: {printer_cfg.driver!r}")


def _check_notifications(tray: BrotherTray, data: PrinterData,
                          printer_cfg, printer_name: str) -> None:
    n = printer_cfg.notifications
    if not n.enabled:
        return
    if data.status == "offline":
        tray.notify(f"{printer_name}:offline",
                    f"{printer_name} — offline",
                    "La stampante non è raggiungibile.", LEVEL_CRIT)
    elif data.status == "error":
        tray.notify(f"{printer_name}:error",
                    f"{printer_name} — errore",
                    f"Errore: {data.status_detail or 'sconosciuto'}", LEVEL_CRIT)
    if data.status not in ("offline", "error"):
        if data.toner_pct < n.toner_threshold:
            tray.notify(f"{printer_name}:toner",
                        f"{printer_name} — toner in esaurimento",
                        f"Toner al {data.toner_pct}% — considera la sostituzione.",
                        LEVEL_WARN)
        if data.drum_pct < n.drum_threshold:
            tray.notify(f"{printer_name}:drum",
                        f"{printer_name} — tamburo in esaurimento",
                        f"Tamburo all'{data.drum_pct}% — considera la sostituzione.",
                        LEVEL_WARN)


def main() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setQuitOnLastWindowClosed(False)

    cfg = load_config()

    # Use first printer for single-printer mode (Task 7 will extend to multi)
    printer_cfg = cfg.printers[0]
    driver = _make_driver(printer_cfg)

    window = MainWindow(cfg, printer_cfg)
    tray   = BrotherTray(window)
    tray.show()
    history_db = HistoryDB()

    def do_refresh() -> None:
        data = driver.fetch()
        ts   = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        window.update_data(data, ts)
        tray.update_status(data, printer_cfg.name)
        _check_notifications(tray, data, printer_cfg, printer_cfg.name)
        history_db.record(printer_cfg.name, data)
        window.update_history(history_db.get_recent(printer_cfg.name, limit=200))

    window.refresh_requested.connect(do_refresh)
    tray._act_refresh.triggered.connect(do_refresh)

    poll_timer = QTimer()
    poll_timer.timeout.connect(do_refresh)
    poll_timer.start(printer_cfg.polling_interval_sec * 1000)

    window.refresh_interval_changed.connect(
        lambda secs: poll_timer.setInterval(secs * 1000))

    window.config_saved.connect(lambda new_cfg: save_config(new_cfg))

    window.clear_history_requested.connect(
        lambda: history_db.clear(printer_cfg.name))

    do_refresh()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

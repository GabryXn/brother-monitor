# main_window.py
from __future__ import annotations
import subprocess
import webbrowser
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QSlider,
    QCheckBox, QComboBox, QGroupBox, QFormLayout, QHeaderView,
    QScrollArea, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, QSettings, pyqtSignal

from widgets import CircularGauge
from printer_client import PrinterData

AUTOSTART_PATH = Path.home() / ".config/autostart/brother-monitor.desktop"
AUTOSTART_CONTENT = """\
[Desktop Entry]
Type=Application
Name=Brother Monitor
Exec=/usr/local/bin/brother-monitor
Icon=printer
Comment=Monitoraggio stampante Brother DCP-L2550DN
X-KDE-autostart-enabled=true
"""

_STATUS_COLOR = {
    "idle":     "#4caf50",
    "sleep":    "#2196f3",
    "printing": "#ff9800",
    "error":    "#f44336",
    "offline":  "#9e9e9e",
}
_STATUS_LABEL = {
    "idle":     "Pronto",
    "sleep":    "Risparmio energetico",
    "printing": "Stampa in corso",
    "error":    "Errore",
    "offline":  "Non raggiungibile",
}


class MainWindow(QMainWindow):
    refresh_requested = pyqtSignal()
    refresh_interval_changed = pyqtSignal(int)   # secondi

    def __init__(self, settings: QSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Brother Monitor — DCP-L2550DN")
        self.setMinimumSize(520, 520)

        tabs = QTabWidget()
        tabs.addTab(self._build_status_tab(),   "Stato")
        tabs.addTab(self._build_stats_tab(),    "Statistiche")
        tabs.addTab(self._build_settings_tab(), "Impostazioni")
        self.setCentralWidget(tabs)

    # ------------------------------------------------------------------ #
    #  Tab Stato                                                           #
    # ------------------------------------------------------------------ #

    def _build_status_tab(self) -> QWidget:
        widget = QWidget()
        root = QVBoxLayout(widget)
        root.setSpacing(10)
        root.setContentsMargins(16, 16, 16, 12)

        # Header --------------------------------------------------------
        self.lbl_model = QLabel("Brother DCP-L2550DN")
        self.lbl_model.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.lbl_serial = QLabel("S/N: —  |  Firmware: —  |  RAM: — MB")
        self.lbl_serial.setStyleSheet("color: gray; font-size: 10px;")

        self.lbl_status = QLabel("Offline")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setFixedHeight(26)
        self.lbl_status.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._set_status_style("offline")

        hdr = QHBoxLayout()
        hdr_text = QVBoxLayout()
        hdr_text.addWidget(self.lbl_model)
        hdr_text.addWidget(self.lbl_serial)
        hdr.addLayout(hdr_text)
        hdr.addStretch()
        hdr.addWidget(self.lbl_status)
        root.addLayout(hdr)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(line)

        # Gauges --------------------------------------------------------
        self.gauge_toner = CircularGauge("Toner")
        self.gauge_drum  = CircularGauge("Tamburo")
        gauges = QHBoxLayout()
        gauges.addStretch()
        gauges.addWidget(self.gauge_toner)
        gauges.addSpacing(60)
        gauges.addWidget(self.gauge_drum)
        gauges.addStretch()
        root.addLayout(gauges)
        root.addStretch()

        # Footer --------------------------------------------------------
        self.lbl_updated = QLabel("Ultimo aggiornamento: —")
        self.lbl_updated.setStyleSheet("color: gray; font-size: 10px;")
        btn_refresh = QPushButton("Aggiorna ora")
        btn_refresh.setObjectName("btn_refresh")
        btn_refresh.clicked.connect(self.refresh_requested)
        footer = QHBoxLayout()
        footer.addWidget(self.lbl_updated)
        footer.addStretch()
        footer.addWidget(btn_refresh)
        root.addLayout(footer)

        return widget

    def _set_status_style(self, status: str) -> None:
        color = _STATUS_COLOR.get(status, "#9e9e9e")
        self.lbl_status.setStyleSheet(
            f"background:{color}; color:white; border-radius:4px;"
            "padding:2px 12px; font-weight:bold; font-size:11px;"
        )

    # ------------------------------------------------------------------ #
    #  Tab Statistiche                                                     #
    # ------------------------------------------------------------------ #

    def _build_stats_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        # Pagine
        pg = QGroupBox("Pagine stampate")
        pf = QFormLayout(pg)
        self.lbl_pages_total  = QLabel("—")
        self.lbl_pages_duplex = QLabel("—")
        self.lbl_pages_copy   = QLabel("—")
        self.lbl_pages_scan   = QLabel("—")
        self.lbl_coverage     = QLabel("—")
        pf.addRow("Totale:",               self.lbl_pages_total)
        pf.addRow("Fronte/retro:",         self.lbl_pages_duplex)
        pf.addRow("Copie:",                self.lbl_pages_copy)
        pf.addRow("Scansioni:",            self.lbl_pages_scan)
        pf.addRow("Copertura media toner:", self.lbl_coverage)
        layout.addWidget(pg)

        # Info dispositivo
        dev = QGroupBox("Informazioni dispositivo")
        df = QFormLayout(dev)
        self.lbl_dev_serial   = QLabel("—")
        self.lbl_dev_firmware = QLabel("—")
        self.lbl_dev_memory   = QLabel("—")
        df.addRow("Numero seriale:", self.lbl_dev_serial)
        df.addRow("Firmware:",       self.lbl_dev_firmware)
        df.addRow("Memoria:",        self.lbl_dev_memory)
        layout.addWidget(dev)

        # Inceppamenti
        jg = QGroupBox("Inceppamenti carta")
        jf = QFormLayout(jg)
        self.lbl_jams_total  = QLabel("—")
        self.lbl_jams_tray1  = QLabel("—")
        self.lbl_jams_inside = QLabel("—")
        self.lbl_jams_rear   = QLabel("—")
        jf.addRow("Totale:",        self.lbl_jams_total)
        jf.addRow("Vassoio 1:",     self.lbl_jams_tray1)
        jf.addRow("Interno:",       self.lbl_jams_inside)
        jf.addRow("Posteriore:",    self.lbl_jams_rear)
        layout.addWidget(jg)

        # Sostituzioni
        rg = QGroupBox("Sostituzioni componenti")
        rf = QFormLayout(rg)
        self.lbl_replace_toner = QLabel("—")
        self.lbl_replace_drum  = QLabel("—")
        rf.addRow("Toner sostituiti:",  self.lbl_replace_toner)
        rf.addRow("Tamburi sostituiti:", self.lbl_replace_drum)
        layout.addWidget(rg)

        # Storico errori
        eg = QGroupBox("Storico errori (ultimi 10)")
        el = QVBoxLayout(eg)
        self.tbl_errors = QTableWidget(0, 2)
        self.tbl_errors.setHorizontalHeaderLabels(["Errore", "Pag."])
        self.tbl_errors.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        self.tbl_errors.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_errors.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_errors.setAlternatingRowColors(True)
        self.tbl_errors.setFixedHeight(200)
        el.addWidget(self.tbl_errors)
        layout.addWidget(eg)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    # ------------------------------------------------------------------ #
    #  Tab Impostazioni                                                    #
    # ------------------------------------------------------------------ #

    def _build_settings_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        # Notifiche
        ng = QGroupBox("Notifiche")
        nf = QFormLayout(ng)

        self.chk_notifications = QCheckBox("Abilita notifiche")
        self.chk_notifications.setChecked(
            self.settings.value("notifications/enabled", True, type=bool))
        nf.addRow(self.chk_notifications)

        self.slider_toner = QSlider(Qt.Orientation.Horizontal)
        self.slider_toner.setRange(5, 50)
        self.slider_toner.setValue(
            self.settings.value("notifications/toner_threshold", 20, type=int))
        self.lbl_toner_thresh = QLabel(f"{self.slider_toner.value()}%")
        self.slider_toner.valueChanged.connect(
            lambda v: self.lbl_toner_thresh.setText(f"{v}%"))
        t_row = QHBoxLayout()
        t_row.addWidget(self.slider_toner)
        t_row.addWidget(self.lbl_toner_thresh)
        nf.addRow("Soglia toner:", t_row)

        self.slider_drum = QSlider(Qt.Orientation.Horizontal)
        self.slider_drum.setRange(5, 30)
        self.slider_drum.setValue(
            self.settings.value("notifications/drum_threshold", 15, type=int))
        self.lbl_drum_thresh = QLabel(f"{self.slider_drum.value()}%")
        self.slider_drum.valueChanged.connect(
            lambda v: self.lbl_drum_thresh.setText(f"{v}%"))
        d_row = QHBoxLayout()
        d_row.addWidget(self.slider_drum)
        d_row.addWidget(self.lbl_drum_thresh)
        nf.addRow("Soglia tamburo:", d_row)
        layout.addWidget(ng)

        # Polling
        pg = QGroupBox("Aggiornamento automatico")
        pf = QFormLayout(pg)
        self.combo_interval = QComboBox()
        self.combo_interval.addItems(["30 secondi", "1 minuto", "5 minuti"])
        interval = self.settings.value("polling/interval_sec", 60, type=int)
        self.combo_interval.setCurrentIndex({30: 0, 60: 1, 300: 2}.get(interval, 1))
        pf.addRow("Intervallo:", self.combo_interval)
        layout.addWidget(pg)

        # Sistema
        sg = QGroupBox("Sistema")
        sl = QVBoxLayout(sg)
        self.chk_autostart = QCheckBox("Avvia automaticamente al login")
        self.chk_autostart.setChecked(AUTOSTART_PATH.exists())
        self.chk_autostart.toggled.connect(self._toggle_autostart)
        sl.addWidget(self.chk_autostart)
        layout.addWidget(sg)

        # Azioni
        ag = QGroupBox("Azioni")
        al = QVBoxLayout(ag)
        btn_web = QPushButton("Apri interfaccia web Brother")
        btn_web.clicked.connect(
            lambda: webbrowser.open("http://localhost:60000/general/status.html"))
        btn_test = QPushButton("Stampa pagina di prova")
        btn_test.clicked.connect(self._print_test_page)
        al.addWidget(btn_web)
        al.addWidget(btn_test)
        layout.addWidget(ag)

        # Salva
        btn_save = QPushButton("Salva impostazioni")
        btn_save.setObjectName("btn_save")
        btn_save.clicked.connect(self._save_settings)
        layout.addWidget(btn_save)
        layout.addStretch()

        return widget

    # ------------------------------------------------------------------ #
    #  Azioni                                                              #
    # ------------------------------------------------------------------ #

    def _toggle_autostart(self, enabled: bool) -> None:
        AUTOSTART_PATH.parent.mkdir(parents=True, exist_ok=True)
        if enabled:
            AUTOSTART_PATH.write_text(AUTOSTART_CONTENT)
        else:
            AUTOSTART_PATH.unlink(missing_ok=True)

    def _print_test_page(self) -> None:
        subprocess.Popen([
            "lp", "-d", "Brother_DCP_L2550DN",
            "-o", "media=A4",
            "-o", "fit-to-page",
            "/usr/share/cups/data/testprint",
        ])

    def _save_settings(self) -> None:
        self.settings.setValue("notifications/enabled",
                               self.chk_notifications.isChecked())
        self.settings.setValue("notifications/toner_threshold",
                               self.slider_toner.value())
        self.settings.setValue("notifications/drum_threshold",
                               self.slider_drum.value())
        secs = {0: 30, 1: 60, 2: 300}[self.combo_interval.currentIndex()]
        self.settings.setValue("polling/interval_sec", secs)
        self.settings.sync()
        self.refresh_interval_changed.emit(secs)

    # ------------------------------------------------------------------ #
    #  Update UI con dati stampante                                        #
    # ------------------------------------------------------------------ #

    def update_data(self, data: PrinterData, timestamp: str) -> None:
        # Tab Stato
        if data.model:
            self.lbl_model.setText(data.model)
        info_parts = []
        if data.serial:
            info_parts.append(f"S/N: {data.serial}")
        if data.firmware:
            info_parts.append(f"Firmware: {data.firmware}")
        if data.memory_mb:
            info_parts.append(f"RAM: {data.memory_mb} MB")
        self.lbl_serial.setText("  |  ".join(info_parts) if info_parts else "S/N: —")

        label = _STATUS_LABEL.get(data.status,
                                   data.status_detail or data.status.capitalize())
        self.lbl_status.setText(label)
        self._set_status_style(data.status)

        self.gauge_toner.set_value(data.toner_pct)
        self.gauge_drum.set_value(data.drum_pct)
        self.lbl_updated.setText(f"Ultimo aggiornamento: {timestamp}")

        # Tab Statistiche
        self.lbl_pages_total.setText(str(data.page_count))
        self.lbl_coverage.setText(f"{data.avg_coverage:.2f}%")
        ps = data.page_stats
        self.lbl_pages_duplex.setText(str(ps.get("duplex", "—")))
        self.lbl_pages_copy.setText(str(ps.get("copy", "—")))
        self.lbl_pages_scan.setText(str(ps.get("scan", "—")))

        if data.serial:
            self.lbl_dev_serial.setText(data.serial)
        if data.firmware:
            self.lbl_dev_firmware.setText(data.firmware)
        if data.memory_mb:
            self.lbl_dev_memory.setText(f"{data.memory_mb} MB")

        j = data.jams
        self.lbl_jams_total.setText(str(j.get("total", 0)))
        self.lbl_jams_tray1.setText(str(j.get("tray1", 0)))
        self.lbl_jams_inside.setText(str(j.get("inside", 0)))
        self.lbl_jams_rear.setText(str(j.get("rear", 0)))

        rc = data.replace_counts
        self.lbl_replace_toner.setText(str(rc.get("toner", 0)))
        self.lbl_replace_drum.setText(str(rc.get("drum", 0)))

        self.tbl_errors.setRowCount(len(data.errors))
        for i, err in enumerate(data.errors):
            self.tbl_errors.setItem(i, 0, QTableWidgetItem(err.get("desc", "")))
            self.tbl_errors.setItem(i, 1, QTableWidgetItem(str(err.get("page", 0))))

    def closeEvent(self, event) -> None:
        # X nasconde la finestra, il processo resta nel tray
        event.ignore()
        self.hide()

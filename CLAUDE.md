# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync --dev

# Run all tests (headless, no display needed)
uv run pytest

# Run a single test file
uv run pytest tests/test_brother_http_driver.py

# Run a single test by name
uv run pytest tests/test_brother_http_driver.py::test_parse_info_toner_drum

# Run the application
uv run python brother_monitor.py

# Install system-wide
bash install.sh
```

## Architecture

The app is a **PyQt6 system tray monitor** for network printers. It polls printers via HTTP (Brother web interface) or SNMP and shows status in a tray icon and optional window.

**Data flow:**
1. Each `PrinterDriver.fetch()` returns a `PrinterData` dataclass.
2. `brother_monitor.py` owns one `QTimer` per printer and wires: driver → `MainWindow.update_data()` + `BrotherTray.update_all_statuses()` + `_check_notifications()`

**Key modules:**
- `drivers/base.py` — `PrinterDriver` ABC and `PrinterData` dataclass. No Qt dependency.
- `drivers/brother_http.py` — scrapes the Brother printer's built-in web UI via HTTP.
- `drivers/snmp.py` — polls printers via SNMP OIDs.
- `config.py` — YAML config at `~/.config/printer-monitor/config.yaml`. `load_config` / `save_config`.
- `history.py` — `HistoryDB`: SQLite storage for per-printer readings.
- `tray.py` — `BrotherTray(QSystemTrayIcon)`: SVG tray icon, tray menu, debounced desktop notifications (1 per key per 60 min).
- `main_window.py` — `MainWindow(QMainWindow)`: 4-tab window (Stato/Statistiche/Storico/Impostazioni). Emits `refresh_requested`, `refresh_interval_changed`, `config_saved`, `printer_selected`, `clear_history_requested`.
- `widgets.py` — `CircularGauge(QWidget)`: custom-painted arc gauge for toner/drum percentages.
- `brother_monitor.py` — entry point; creates `QApplication` and connects signals.

**Tests** use `pytest-qt` with `QT_QPA_PLATFORM=offscreen` (set in `conftest.py`). Drivers are tested by mocking HTTP responses. `tmp_path` fixture used for config and DB tests.

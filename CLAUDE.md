# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests (headless, no display needed)
pytest

# Run a single test file
pytest tests/test_printer_client.py

# Run a single test by name
pytest tests/test_printer_client.py::test_parse_info_toner_drum

# Run the application
python brother_monitor.py

# Install system-wide (copies files to /usr/local/lib/brother-monitor)
bash install.sh
```

## Architecture

The app is a **PyQt6 system tray monitor** for a Brother DCP-L2550DN printer. It polls the printer's built-in web interface (proxied at `http://localhost:60000`) and shows status in a tray icon and optional window.

**Data flow:**
1. `PrinterClient.fetch()` (in `printer_client.py`) makes two HTTP GET requests to the printer's web UI:
   - `/general/information.html?kind=item` → parsed by `_parse_info()` for device info, toner/drum %, counters, jams, errors
   - `/general/status.html` → parsed by `_parse_status()` for current status (`idle`/`sleep`/`printing`/`error`/`offline`)
2. `brother_monitor.py` (the entry point) owns a `QTimer` for polling and wires everything together: `PrinterClient` → `MainWindow.update_data()` + `BrotherTray.update_status()` + `_check_notifications()`

**Key modules:**
- `printer_client.py` — pure data layer; `PrinterData` dataclass + HTML scraping via BeautifulSoup/regex. No Qt dependency.
- `tray.py` — `BrotherTray(QSystemTrayIcon)`: colored dot icons generated programmatically (no external image files), tray menu, and debounced desktop notifications (1 notification per key per 60 min).
- `main_window.py` — `MainWindow(QMainWindow)`: 3-tab window (Stato/Statistiche/Impostazioni). Emits `refresh_requested` signal and `refresh_interval_changed` signal. Closing the window hides it rather than quitting.
- `widgets.py` — `CircularGauge(QWidget)`: custom-painted arc gauge for toner/drum percentages.
- `brother_monitor.py` — entry point; creates `QApplication`, `QSettings` (INI format at `~/.config/gabry/brother-monitor.ini`), and connects signals between components.

**Settings keys** (stored via `QSettings`):
- `notifications/enabled` (bool, default True)
- `notifications/toner_threshold` (int %, default 20)
- `notifications/drum_threshold` (int %, default 15)
- `polling/interval_sec` (int, default 60)

**Tests** use `pytest-qt` with `QT_QPA_PLATFORM=offscreen` (set in `conftest.py`). HTML fixtures in `conftest.py` are modeled after the real printer's output. `PrinterClient` is tested by mocking `requests.get`.

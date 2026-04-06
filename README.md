# Printer Monitor

A **PyQt6 system tray application** for monitoring Brother printers (and other network printers via SNMP). Shows toner/drum levels, print counters, and current status with desktop notifications.

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- System tray icon with color-coded status (green/yellow/red)
- Real-time toner and drum percentage gauges
- Print counter history with SQLite storage
- Desktop notifications when consumables run low
- Multi-printer support (add as many printers as you need)
- Two driver backends: **Brother HTTP** (web interface scraping) and **SNMP**
- Configurable polling interval and notification thresholds per printer

## Requirements

- Linux with a graphical session (X11 or Wayland via XWayland)
- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

### Quick install (system-wide)

```bash
git clone https://github.com/GabryXn/brother-monitor.git
cd brother-monitor
bash install.sh
```

This installs to `/usr/local/lib/printer-monitor` and adds a `printer-monitor` binary to your `$PATH`. It also sets up an XDG autostart entry and a systemd user service.

### Development setup

```bash
git clone https://github.com/GabryXn/brother-monitor.git
cd brother-monitor
uv sync --dev
uv run python brother_monitor.py
```

## Configuration

On first launch, a default config is created at `~/.config/printer-monitor/config.yaml`.

Example config:

```yaml
printers:
  - name: Brother DCP-L2550DN
    driver: brother_http
    url: http://localhost:60000
    cups_printer: Brother_DCP_L2550DN
    polling_interval_sec: 60
    notifications:
      enabled: true
      toner_threshold: 20   # notify when toner drops below this %
      drum_threshold: 15    # notify when drum drops below this %

  - name: Office Printer
    driver: snmp
    host: 192.168.1.50
    community: public
    polling_interval_sec: 120
    notifications:
      enabled: true
      toner_threshold: 10
      drum_threshold: 10
```

### Brother HTTP driver

Used for Brother printers connected via USB and exposed through `ipp-usb` (typically at `http://localhost:60000`). Scrapes the printer's built-in web interface.

### SNMP driver

Used for network printers that expose consumable data via SNMP. Set `host` to the printer's IP and `community` to the SNMP community string (usually `public`).

## Running tests

```bash
uv run pytest
```

Tests run headless (no display required) via `QT_QPA_PLATFORM=offscreen`.

## Project structure

```
brother_monitor.py   — entry point, wires Qt components together
config.py            — YAML config loader/saver
history.py           — SQLite history storage
tray.py              — system tray icon and notifications
main_window.py       — main 3-tab window (Status / Stats / Settings)
widgets.py           — CircularGauge custom widget
drivers/
  base.py            — PrinterDriver ABC and PrinterData dataclass
  brother_http.py    — Brother web interface scraper
  snmp.py            — SNMP polling driver
tests/               — pytest test suite
```

## License

[MIT](LICENSE)

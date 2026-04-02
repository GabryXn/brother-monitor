#!/bin/bash
set -e

INSTALL_DIR="/usr/local/lib/printer-monitor"
BIN_PATH="/usr/local/bin/printer-monitor"

echo "==> Installazione Printer Monitor..."

sudo mkdir -p "$INSTALL_DIR"
sudo cp -- brother_monitor.py config.py history.py \
           main_window.py tray.py widgets.py "$INSTALL_DIR/"
sudo cp -r drivers "$INSTALL_DIR/"

sudo tee "$BIN_PATH" > /dev/null << 'EOF'
#!/bin/bash
export PYTHONPATH="/usr/local/lib/printer-monitor:$PYTHONPATH"
exec python3 /usr/local/lib/printer-monitor/brother_monitor.py "$@"
EOF
sudo chmod +x "$BIN_PATH"

AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
cat > "$AUTOSTART_DIR/printer-monitor.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Printer Monitor
Exec=$BIN_PATH
Icon=printer
Comment=Monitoraggio stampanti di rete
X-KDE-autostart-enabled=true
EOF

echo "==> Installazione completata."
echo "    Avvia con: printer-monitor"
echo "    Si avvierà automaticamente al prossimo login KDE."

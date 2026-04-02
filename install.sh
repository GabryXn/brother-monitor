#!/bin/bash
set -e

INSTALL_DIR="/usr/local/lib/brother-monitor"
BIN_PATH="/usr/local/bin/brother-monitor"

echo "==> Installazione Brother Monitor..."

sudo mkdir -p "$INSTALL_DIR"
sudo cp -- brother_monitor.py printer_client.py main_window.py tray.py widgets.py \
     "$INSTALL_DIR/"

# Script wrapper che imposta il PYTHONPATH corretto
sudo tee "$BIN_PATH" > /dev/null << 'EOF'
#!/bin/bash
export PYTHONPATH="/usr/local/lib/brother-monitor:$PYTHONPATH"
exec python3 /usr/local/lib/brother-monitor/brother_monitor.py "$@"
EOF
sudo chmod +x "$BIN_PATH"

# Autostart KDE per l'utente corrente
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
cat > "$AUTOSTART_DIR/brother-monitor.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Brother Monitor
Exec=$BIN_PATH
Icon=printer
Comment=Monitoraggio stampante Brother DCP-L2550DN
X-KDE-autostart-enabled=true
EOF

echo "==> Installazione completata."
echo "    Avvia con: brother-monitor"
echo "    Si avvierà automaticamente al prossimo login KDE."

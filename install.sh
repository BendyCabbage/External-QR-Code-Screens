#!/bin/bash
#
# Hyper Karting QR Display - Setup Script
# Run this script on a fresh Raspberry Pi OS installation
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SERVER_DIR="$SCRIPT_DIR"
INSTALL_DIR="/opt/qr-display"
SERVICE_NAME="qr-display"

echo "============================================"
echo "  Hyper Karting QR Display - Setup"
echo "============================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER="${SUDO_USER:-$USER}"
ACTUAL_HOME=$(getent passwd "$ACTUAL_USER" | cut -d: -f6)

echo "[1/5] Installing system dependencies..."
apt-get update
apt-get install -y --no-install-recommends \
    python3-pip \
    python3-venv \
    chromium-browser \
    unclutter

echo ""
echo "[2/5] Setting up application directory..."
mkdir -p "$INSTALL_DIR"
cp "$SERVER_DIR/app.py" "$SERVER_DIR/logo.svg" "$SERVER_DIR/requirements.txt" "$INSTALL_DIR/"

echo ""
echo "[3/5] Creating Python virtual environment and installing packages..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

echo ""
echo "[4/5] Creating systemd service for the server..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Hyper Karting QR Display Server
After=network.target

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python app.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ${SERVICE_NAME}.service
systemctl start ${SERVICE_NAME}.service

echo ""
echo "[5/5] Configuring kiosk mode autostart..."

# Create autostart directory if it doesn't exist
AUTOSTART_DIR="$ACTUAL_HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

# Create the kiosk launcher script
cat > "$INSTALL_DIR/kiosk.sh" << 'EOF'
#!/bin/bash

# Wait for the server to be ready
sleep 5

# Hide the mouse cursor
unclutter -idle 0 &

# Disable screen blanking/power saving
xset s off
xset s noblank
xset -dpms

# Launch Chromium in kiosk mode
chromium-browser \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-restore-session-state \
    --no-first-run \
    --start-fullscreen \
    --autoplay-policy=no-user-gesture-required \
    http://localhost:8080
EOF

chmod +x "$INSTALL_DIR/kiosk.sh"

# Create autostart desktop entry
cat > "$AUTOSTART_DIR/qr-display-kiosk.desktop" << EOF
[Desktop Entry]
Type=Application
Name=QR Display Kiosk
Exec=$INSTALL_DIR/kiosk.sh
X-GNOME-Autostart-enabled=true
EOF

chown -R "$ACTUAL_USER:$ACTUAL_USER" "$AUTOSTART_DIR"

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "The QR display server is now running on port 8080."
echo ""
echo "To update the QR code, send a POST request:"
echo "  curl -X POST http://<pi-ip>:8080/update_qr \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"booking_number\": \"BK123\", \"booking_name\": \"John\"}'"
echo ""
echo "To reset to the logo:"
echo "  curl -X POST http://<pi-ip>:8080/reset"
echo ""
echo "Reboot the Pi to start the kiosk display:"
echo "  sudo reboot"
echo ""

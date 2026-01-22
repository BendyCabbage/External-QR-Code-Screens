# Hyper Karting QR Display

A Raspberry Pi-based QR code display system for customer check-in. Each Pi runs a local server that displays a fullscreen QR code when triggered via HTTP API.

## Features

- **Fullscreen kiosk display** - Black background with QR code and optional booking name
- **Real-time updates** - QR code updates within seconds via WebSocket
- **Auto-start on boot** - Chromium launches in kiosk mode automatically
- **Simple HTTP API** - Easy integration with booking systems
- **Stateless** - Returns to logo on reboot (no persistence)

## Display Layout (1080x1920 vertical)

**Default state:** Hyper Karting logo centered on black background

**Active state:** Booking name (top) + QR code (center) on black background

---

## Quick Start

### Prerequisites

- Raspberry Pi (3B+ or newer recommended)
- Raspberry Pi OS with Desktop
- Display configured for vertical orientation (1080x1920)
- Network connection

### Installation

1. Clone or copy this repository to the Pi:
   ```bash
   git clone <repo-url> ~/qr-display-pi
   cd ~/qr-display-pi
   ```

2. Run the setup script:
   ```bash
   sudo ./setup/install.sh
   ```

3. Reboot to start the kiosk:
   ```bash
   sudo reboot
   ```

That's it! The Pi will boot into a fullscreen display showing the Hyper Karting logo.

---

## API Reference

### Update QR Code

**Endpoint:** `POST /update_qr`

**Request:**
```json
{
    "booking_number": "BK987654321",
    "booking_name": "Josh"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `booking_number` | string | Yes | Booking reference (appended to URL) |
| `booking_name` | string | No | Customer name to display above QR |

**Success Response (200):**
```json
{
    "status": "success",
    "url_generated": "https://portal.hyperkarting.com.au/registration/BK987654321"
}
```

**Error Response (400):**
```json
{
    "status": "error",
    "message": "Missing 'booking_number' in request body"
}
```

**Example:**
```bash
curl -X POST http://192.168.1.100:8080/update_qr \
     -H "Content-Type: application/json" \
     -d '{"booking_number": "BK987654321", "booking_name": "Josh"}'
```

---

### Reset Display

**Endpoint:** `POST /reset`

Returns the display to the default logo state.

**Example:**
```bash
curl -X POST http://192.168.1.100:8080/reset
```

---

### Health Check

**Endpoint:** `GET /health`

Returns server status. Useful for monitoring.

**Example:**
```bash
curl http://192.168.1.100:8080/health
```

---

## File Structure

```
qr-display-pi/
├── server/
│   ├── app.py              # Flask server with API endpoints
│   ├── requirements.txt    # Python dependencies
│   └── templates/
│       └── display.html    # Fullscreen display page
├── setup/
│   ├── install.sh          # Automated setup script
│   └── uninstall.sh        # Clean removal script
└── README.md
```

---

## Management

### Service Commands

```bash
# Check status
sudo systemctl status qr-display

# Restart server
sudo systemctl restart qr-display

# View logs
sudo journalctl -u qr-display -f
```

### Uninstall

```bash
sudo ./setup/uninstall.sh
```

---

## Troubleshooting

### QR code not updating
- Check the server is running: `sudo systemctl status qr-display`
- Verify network connectivity to the Pi
- Check server logs: `sudo journalctl -u qr-display -f`

### Kiosk not starting on boot
- Ensure the desktop environment is installed (not Lite OS)
- Check autostart file exists: `ls ~/.config/autostart/`
- Manually test: `/opt/qr-display/kiosk.sh`

### Display not vertical
- Screen rotation is not handled by this setup
- Configure via `raspi-config` or `/boot/config.txt`

---

## Network Discovery

To find your Pi's IP address:
```bash
hostname -I
```

Or scan your network:
```bash
nmap -sn 192.168.1.0/24
```

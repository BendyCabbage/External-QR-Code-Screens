#!/usr/bin/env python3
"""
QR Code Display Server for Raspberry Pi
Serves a fullscreen display and accepts booking updates via API
"""

from pathlib import Path
from flask import Flask, request, jsonify

app = Flask(__name__)

# Current state (not persisted)
current_booking = {
    "booking_number": None,
    "booking_name": None
}

BASE_URL = "https://portal.hyperkarting.com.au/registration/"

# Load SVG logo from file
LOGO_SVG = (Path(__file__).parent / "logo.svg").read_text()


def generate_html(show_qr=False, booking_name=None, booking_number=None, qr_url=None):
    """Generate the display HTML with current state baked in"""

    if show_qr and qr_url:
        # QR code display
        name_html = f'<div id="booking-name">{booking_name}\'s Booking</div>' if booking_name else ''
        content = f'''
        <div id="qr-container">
            {name_html}
            <div id="qr-code"></div>
        </div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
        <script>
            new QRCode(document.getElementById('qr-code'), {{
                text: '{qr_url}',
                width: 700,
                height: 700,
                colorDark: '#000000',
                colorLight: '#ffffff',
                correctLevel: QRCode.CorrectLevel.H
            }});
            setInterval(function() {{
                fetch('/state').then(r => r.json()).then(function(data) {{
                    var current = '{booking_number or ""}';

                    var newVal = data.booking_number || '';
                    if (newVal !== current) location.reload();
                }});
            }}, 3000);
        </script>'''
    else:
        # Logo display (default)
        content = f'''
        <div id="logo-container">
            {LOGO_SVG}
        </div>
        <script>
            setInterval(function() {{
                fetch('/state').then(r => r.json()).then(function(data) {{
                    if (data.booking_number) location.reload();
                }});
            }}, 3000);
        </script>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hyper Karting Check-In</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        html, body {{
            width: 100%;
            height: 100%;
            overflow: hidden;
            background-color: #000;
            font-family: 'Montserrat', sans-serif;
        }}

        .container {{
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 40px;
        }}

        #logo-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            height: 100%;
        }}

        #logo-container svg {{
            width: 70%;
            max-width: 600px;
            height: auto;
        }}

        #qr-container {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            width: 100%;
            height: 100%;
            gap: 80px;
        }}

        #booking-name {{
            font-family: 'Montserrat', sans-serif;
            font-size: 75px;
            font-weight: 700;
            color: #fff;
            text-align: center;
            letter-spacing: 3px;
            line-height: 1.1;
            max-width: 90%;
            word-wrap: break-word;
        }}

        #qr-code {{
            background: #fff;
            padding: 40px;
            border-radius: 24px;
            box-shadow: 0 8px 32px rgba(255, 255, 255, 0.1);
        }}

        #qr-code canvas,
        #qr-code img {{
            display: block;
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>'''


@app.route("/")
def display():
    """Serve the fullscreen display page"""
    if current_booking["booking_number"]:
        url = f"{BASE_URL}{current_booking['booking_number']}"
        return generate_html(
            show_qr=True,
            booking_name=current_booking["booking_name"],
            booking_number=current_booking["booking_number"],
            qr_url=url
        )
    return generate_html()


@app.route("/update_qr", methods=["POST"])
def update_qr():
    """
    Update the displayed QR code

    Expected JSON body:
    {
        "booking_number": "BK987654321",
        "booking_name": "Josh"  // Optional
    }
    """
    data = request.get_json()

    if not data or "booking_number" not in data:
        return jsonify({
            "status": "error",
            "message": "Missing 'booking_number' in request body"
        }), 400

    booking_number = data["booking_number"]
    booking_name = data.get("booking_name")  # Optional

    # Update current state
    current_booking["booking_number"] = booking_number
    current_booking["booking_name"] = booking_name

    # Generate the full URL
    url_generated = f"{BASE_URL}{booking_number}"

    return jsonify({
        "status": "success",
        "url_generated": url_generated
    }), 200


@app.route("/reset", methods=["POST"])
def reset_display():
    """Reset display back to logo"""
    current_booking["booking_number"] = None
    current_booking["booking_name"] = None

    return jsonify({"status": "success", "message": "Display reset to logo"}), 200


@app.route("/state", methods=["GET"])
def state():
    """Return current booking state for polling"""
    return jsonify(current_booking), 200


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

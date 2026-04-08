"""
╔═══════════════════════════════════════════════════════╗
║           QR CODE GENERATOR  —  Flask App             ║
║  Autor : Iván Roldán Heredia                          ║
║  GitHub: github.com/iivanrld                          ║
╚═══════════════════════════════════════════════════════╝

Uso:
    pip install -r requirements.txt
    python app.py
    → El navegador se abre automáticamente en http://localhost:5000
"""

import io
import base64
import threading
import webbrowser

import qrcode
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)

# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────

def ensure_url_scheme(url: str) -> str:
    """
    Garantiza que la URL lleve esquema https://.
    De este modo la cámara abre el enlace directamente
    en lugar de lanzar una búsqueda en Google.
    """
    url = url.strip()
    if url and not url.lower().startswith(("http://", "https://", "ftp://")):
        url = "https://" + url
    return url


def build_vcard(name: str, phone: str, email: str,
                org: str = "", url: str = "") -> str:
    """Genera un bloque vCard 3.0 para el modo Contacto."""
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"FN:{name}",
        f"TEL:{phone}",
        f"EMAIL:{email}",
    ]
    if org:
        lines.append(f"ORG:{org}")
    if url:
        lines.append(f"URL:{url}")
    lines.append("END:VCARD")
    return "\n".join(lines)


def generate_qr_b64(data: str,
                    fill_color: str = "#00ff9f",
                    back_color: str = "#0a0a12") -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


# ──────────────────────────────────────────────────────────
# Rutas
# ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data     = request.get_json(silent=True) or {}
    qr_type  = data.get("type", "url")
    fg       = data.get("color",   "#00ff9f")
    bg       = data.get("bgcolor", "#0a0a12")

    try:
        if qr_type == "url":
            raw = data.get("url", "").strip()
            if not raw:
                return jsonify({"error": "Introduce una URL"}), 400
            content = ensure_url_scheme(raw)

        elif qr_type == "text":
            content = data.get("text", "").strip()
            if not content:
                return jsonify({"error": "El texto está vacío"}), 400

        elif qr_type == "contact":
            name  = data.get("name",  "").strip()
            phone = data.get("phone", "").strip()
            if not name or not phone:
                return jsonify({"error": "Nombre y teléfono son obligatorios"}), 400
            content = build_vcard(
                name, phone,
                data.get("email", ""),
                data.get("org",   ""),
                data.get("url",   ""),
            )
        else:
            return jsonify({"error": "Tipo no válido"}), 400

        img_b64 = generate_qr_b64(content, fg, bg)
        return jsonify({"image": img_b64, "data": content})

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/download", methods=["POST"])
def download():
    data    = request.get_json(silent=True) or {}
    img_b64 = data.get("image", "")
    if not img_b64:
        return jsonify({"error": "Sin imagen"}), 400

    buf = io.BytesIO(base64.b64decode(img_b64))
    buf.seek(0)
    return send_file(buf, mimetype="image/png",
                     as_attachment=True, download_name="qr_code.png")


# ──────────────────────────────────────────────────────────
# Inicio
# ──────────────────────────────────────────────────────────

def open_browser():
    webbrowser.open("http://localhost:5000")


if __name__ == "__main__":
    # Abre el navegador 1 segundo después de que Flask arranque
    threading.Timer(1.0, open_browser).start()
    print("\n  ◆ QR Generator arrancando en http://localhost:5000\n")
    app.run(debug=False, port=5000)

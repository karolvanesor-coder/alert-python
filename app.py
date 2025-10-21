from flask import Flask, request
from playsound import playsound
import threading
import subprocess
import sys
import os

app = Flask(__name__)

# --- CONFIGURACIÓN DE ALERTAS ---
ALERT_CONFIG = {
    "CPU": {
        "sound": "./sound/alert.mp3",
        "gif": "./gif/alert.gif"
    },
    "MEMORIA": {
        "sound": "./sound/alert1.mp3",
        "gif": "./gif/alert1.gif"
    },
    "DISCO": {
        "sound": "./sound/alert2.mp3",
        "gif": "./gif/alert2.gif",
        "warn_sound": "./sound/warn.mp3",   # sonido preventivo
        "warn_gif": "./gif/warn.gif"        # gif preventivo
    }
}

DEFAULT_SOUND = "./sound/alert.mp3"
DEFAULT_GIF = "./gif/alert.gif"

# --- MOSTRAR GIF POPUP ---
def show_gif_popup(gif_path, duration=5, message="⚠️ Alerta sin mensaje", border_color="red"):
    subprocess.Popen([sys.executable, "./interface/popup.py", gif_path, str(duration), message, border_color])

# --- WEBHOOK DATADOG ---
@app.route("/datadog-webhook", methods=["POST"])
def datadog_webhook():
    data = request.json
    print("📩 Webhook recibido:", data)

    raw_tags = data.get("tags", "")
    host = data.get("host", "Desconocido")
    alert_type = str(data.get("alert_type", "alert")).lower()  # puede venir 'warn' o 'alert'

    # Normalizar tags
    if isinstance(raw_tags, str):
        tags = [t.strip().upper() for t in raw_tags.split(",") if t.strip()]
    else:
        tags = [str(t).upper() for t in raw_tags]
    print("✅ Tags procesados:", tags)

    selected_tag = next((tag for tag in tags if tag in ALERT_CONFIG), None)

    # --- FILTRO: SOLO WARNINGS DE DISCO ---
    if "warn" in alert_type and selected_tag != "DISCO":
        print(f"⚠️ Alerta WARN ignorada (solo se aceptan warnings de DISCO). Tag recibido: {selected_tag}")
        return {"status": "ignored", "reason": "solo warnings de DISCO"}, 200

    # --- DETERMINAR SONIDO, GIF Y COLOR ---
    if selected_tag:
        config = ALERT_CONFIG[selected_tag]

        if "warn" in alert_type:
            border_color = "yellow"
            titulo = "⚠️ ALERTA PREVENTIVA"
            sound_file = config.get("warn_sound", DEFAULT_SOUND)
            gif_file = config.get("warn_gif", DEFAULT_GIF)
        else:
            border_color = "red"
            titulo = "🚨 ALERTA CRÍTICA"
            sound_file = config.get("sound", DEFAULT_SOUND)
            gif_file = config.get("gif", DEFAULT_GIF)

        message = f"{titulo}\n🔹 {selected_tag}\nHost: {host}"
        print(f"🚨 Disparando alerta ({alert_type}) por TAG: {selected_tag} desde {host}")
    else:
        border_color = "red"
        sound_file = DEFAULT_SOUND
        gif_file = DEFAULT_GIF
        message = f"🚨 ALERTA DESCONOCIDA\nHost: {host}"
        print("⚠️ Alerta sin tag conocido.")

    # --- EJECUTAR ALERTA ---
    threading.Thread(target=playsound, args=(sound_file,), daemon=True).start()
    threading.Thread(target=show_gif_popup, args=(gif_file, 6, message, border_color), daemon=True).start()

    print(f"🎵 Sonido: {sound_file} | 🖼️ GIF: {gif_file} | 🟡 Color: {border_color.upper()}")
    return {"status": "ok", "tag": selected_tag, "color": border_color}, 200


if __name__ == "__main__":
    print("Flask escuchando en http://127.0.0.1:5006")
    app.run(port=5006, debug=True)

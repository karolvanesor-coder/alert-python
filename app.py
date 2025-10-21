from flask import Flask, request
from playsound import playsound
import threading
import subprocess
import sys
import os

app = Flask(__name__)

# Configuración base
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
        "gif": "./gif/alert2.gif"
    }
}

DEFAULT_SOUND = "./sound/alert.mp3"
DEFAULT_GIF = "./gif/alert.gif"

# Popup independiente
def show_gif_popup(gif_path, duration=4, message="⚠️ Alerta sin mensaje", border_color="red"):
    subprocess.Popen([sys.executable, "./interface/popup.py", gif_path, str(duration), message, border_color])

@app.route("/datadog-webhook", methods=["POST"])
def datadog_webhook():
    data = request.json
    print("📩 Webhook recibido:", data)

    raw_tags = data.get("tags", "")
    host = data.get("host", "Desconocido")
    alert_type = str(data.get("alert_type", "alert")).lower()  # "warn" o "alert"

    # Normalizar tags
    if isinstance(raw_tags, str):
        tags = [t.strip().upper() for t in raw_tags.split(",") if t.strip()]
    else:
        tags = [str(t).upper() for t in raw_tags]
    print("✅ Tags procesados:", tags)

    selected_tag = next((tag for tag in tags if tag in ALERT_CONFIG), None)

    # --- 🔸 FILTRO PERSONALIZADO SOLO PARA WARNING DE DISCO ---
    if "warn" in alert_type and selected_tag != "DISCO":
        print(f"⚠️ Alerta WARN ignorada (solo se aceptan warnings de DISCO). Tag recibido: {selected_tag}")
        return {"status": "ignored", "reason": "solo warnings de DISCO"}, 200

    # Determinar color y mensaje
    if "warn" in alert_type:
        border_color = "yellow"
        titulo = "⚠️ ALERTA PREVENTIVA"
        emoji = ""
        gif_file = "./gif/warn.gif"  # usa tu gif especial para warning
    else:
        border_color = "red"
        titulo = "🚨 ALERTA CRÍTICA"
        emoji = ""
        gif_file = None  # se definirá abajo

    if selected_tag:
        base_sound = ALERT_CONFIG[selected_tag]["sound"]
        base_gif = ALERT_CONFIG[selected_tag]["gif"]
        if not gif_file:  # usa el normal si no hay warn.gif asignado
            gif_file = base_gif
        message = f"{titulo}\n{emoji} {selected_tag}\nHost: {host}"
        print(f"🚨 Disparando alerta ({alert_type}) por TAG: {selected_tag} desde {host}")
    else:
        base_sound = DEFAULT_SOUND
        if not gif_file:
            gif_file = DEFAULT_GIF
        message = f"{titulo}\n⚠️ Alerta por defecto\nHost: {host}"
        print("⚠️ Ningún tag coincide, alerta por defecto")

    # Reproducir sonido
    threading.Thread(target=playsound, args=(base_sound,), daemon=True).start()

    # Mostrar popup
    threading.Thread(target=show_gif_popup, args=(gif_file, 6, message, border_color), daemon=True).start()

    print(f"🟡 Color asignado: {border_color.upper()} | Sonido: {base_sound}")
    return {"status": "ok", "tags_recibidos": tags, "host": host, "color": border_color}, 200

if __name__ == "__main__":
    print("Flask escuchando en http://127.0.0.1:5006")
    app.run(port=5006, debug=True)

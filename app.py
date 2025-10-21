from flask import Flask, request
from playsound import playsound
import threading
import subprocess
import sys

app = Flask(__name__)

# Diccionario de configuración: tag -> sonido y GIF
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

# Valores por defecto
DEFAULT_SOUND = "./sound/alert.mp3"
DEFAULT_GIF = "./gif/alert.gif"

# Lanzar ventana GIF en proceso independiente con mensaje y color
def show_gif_popup(gif_path, duration=4, message="⚠️ Alerta sin mensaje", border_color="red"):
    subprocess.Popen([sys.executable, "./interface/popup.py", gif_path, str(duration), message, border_color])

@app.route("/datadog-webhook", methods=["POST"])
def datadog_webhook():
    data = request.json
    print("📩 Webhook recibido:", data)

    # Extraer datos
    raw_tags = data.get("tags", "")
    host = data.get("host", "Desconocido")
    alert_type = str(data.get("alert_type", "alert")).lower()  # 👈 capturamos tipo de alerta

    # Determinar color según tipo
    if "warn" in alert_type:
        border_color = "yellow"
    else:
        border_color = "red"

    # Normalizar tags
    if isinstance(raw_tags, str):
        tags = [t.strip().upper() for t in raw_tags.split(",") if t.strip()]
    else:
        tags = [str(t).upper() for t in raw_tags]

    print("✅ Tags procesados:", tags)

    # Buscar primer tag válido
    selected_tag = next((tag for tag in tags if tag in ALERT_CONFIG), None)

    if selected_tag:
        sound_file = ALERT_CONFIG[selected_tag]["sound"]
        gif_file = ALERT_CONFIG[selected_tag]["gif"]
        message = f"🚨 {selected_tag}\nHost: {host}"
        print(f"🚨 Disparando alerta por TAG: {selected_tag} desde {host}")
    else:
        sound_file = DEFAULT_SOUND
        gif_file = DEFAULT_GIF
        message = f"⚠️ Alerta por defecto\nHost: {host}"
        print(f"⚠️ Ningún tag coincide, alerta por defecto desde {host}")

    # Reproducir sonido
    threading.Thread(target=playsound, args=(sound_file,), daemon=True).start()

    # Mostrar popup con mensaje y color
    threading.Thread(target=show_gif_popup, args=(gif_file, 6, message, border_color), daemon=True).start()

    print(f"🟡 Color asignado: {border_color.upper()}")
    return {"status": "ok", "tags_recibidos": tags, "host": host, "color": border_color}, 200

if __name__ == "__main__":
    print("Flask escuchando en http://127.0.0.1:5006")
    app.run(port=5006, debug=True)

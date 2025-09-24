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

# Valores por defecto si no coincide ningún tag
DEFAULT_SOUND = "./sound/alert.mp3"
DEFAULT_GIF = "./gif/alert.gif"

# Lanzar ventana GIF en proceso independiente
def show_gif_popup(gif_path, duration=4):
    subprocess.Popen([sys.executable, "./interface/popup.py", gif_path, str(duration)])

@app.route("/datadog-webhook", methods=["POST"])
def datadog_webhook():
    data = request.json
    tags = data.get("tags", [])
    print("📩 Webhook recibido:", data)

    # Buscar primer tag que exista en nuestra configuración
    selected_tag = next((tag for tag in tags if tag in ALERT_CONFIG), None)

    if selected_tag:
        sound_file = ALERT_CONFIG[selected_tag]["sound"]
        gif_file = ALERT_CONFIG[selected_tag]["gif"]
    else:
        sound_file = DEFAULT_SOUND
        gif_file = DEFAULT_GIF

    # Reproducir sonido en hilo aparte
    threading.Thread(target=playsound, args=(sound_file,), daemon=True).start()

    # Mostrar GIF en proceso aparte
    threading.Thread(target=show_gif_popup, args=(gif_file, 8), daemon=True).start()

    return {"status": "ok"}, 200

if __name__ == "__main__":
    print("Flask escuchando en http://127.0.0.1:5006")
    app.run(port=5006, debug=True)

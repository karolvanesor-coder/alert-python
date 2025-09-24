from flask import Flask, request
from playsound import playsound
from plyer import notification  # 🔔 Notificaciones del sistema
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

# Mostrar notificación del sistema
def show_notification(title, message):
    try:
        notification.notify(
            title=title,
            message=message,
            timeout=8  # segundos
        )
    except Exception as e:
        print(f"⚠️ Error mostrando notificación: {e}")

@app.route("/datadog-webhook", methods=["POST"])
def datadog_webhook():
    data = request.json
    print("📩 Webhook recibido:", data)

    # Extraer título y cuerpo del evento
    event_title = data.get("title", "Evento Datadog")
    event_body = data.get("body", "Sin detalles")

    raw_tags = data.get("tags", [])

    # Normalizar: puede ser lista o string
    if isinstance(raw_tags, str):
        tags = [t.strip().upper() for t in raw_tags.split(",") if t.strip()]
    else:
        tags = [str(t).upper() for t in raw_tags]

    print("✅ Tags procesados:", tags)

    # Buscar primer tag que coincida
    selected_tag = next((tag for tag in tags if tag in ALERT_CONFIG), None)

    if selected_tag:
        sound_file = ALERT_CONFIG[selected_tag]["sound"]
        gif_file = ALERT_CONFIG[selected_tag]["gif"]
        print(f"🚨 Disparando alerta por TAG: {selected_tag}")
    else:
        sound_file = DEFAULT_SOUND
        gif_file = DEFAULT_GIF
        print("⚠️ Ningún tag coincide, usando alerta por defecto")

    # 🔔 Notificación del sistema
    notif_title = f"🚨 Alerta {selected_tag or 'GENÉRICA'}"
    notif_message = f"{event_title}\n{event_body}"
    threading.Thread(target=show_notification, args=(notif_title, notif_message), daemon=True).start()

    # Reproducir sonido en hilo aparte
    threading.Thread(target=playsound, args=(sound_file,), daemon=True).start()

    # Mostrar GIF en proceso aparte
    threading.Thread(target=show_gif_popup, args=(gif_file, 6), daemon=True).start()

    return {"status": "ok", "tags_recibidos": tags}, 200

if __name__ == "__main__":
    print("Flask escuchando en http://127.0.0.1:5006")
    app.run(port=5006, debug=True)

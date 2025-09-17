from flask import Flask, request
from playsound import playsound
import threading
import subprocess

app = Flask(__name__)

# Función para mostrar alerta visual nativa en macOS
def show_alert(title, message):
    script = f'display notification "{message}" with title "{title}"'
    subprocess.run(["osascript", "-e", script])

# Ruta para recibir el webhook de Datadog
@app.route("/datadog-webhook", methods=["POST"])
def datadog_webhook():
    data = request.json
    print("📩 Webhook recibido:", data)

    # Extraer información básica
    event_title = data.get("title", "Alerta sin título")
    event_msg = data.get("body", "Sin detalles")

    # Reproducir sonido en un hilo aparte
    threading.Thread(target=playsound, args=("alert.mp3",), daemon=True).start()

    # Mostrar alerta visual en un hilo aparte
    threading.Thread(target=show_alert, args=(event_title, event_msg), daemon=True).start()

    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(port=5006, debug=True)

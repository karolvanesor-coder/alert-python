from flask import Flask, request
from playsound import playsound
import threading
import subprocess

app = Flask(__name__)

# Función para mostrar alerta visual en macOS
def show_alert():
    script = 'display notification "Tienes una alerta" with title "🚨 ALERTA DATADOG 🚨"'
    subprocess.run(["osascript", "-e", script])

# Ruta para recibir el webhook de Datadog
@app.route("/datadog-webhook", methods=["POST"])
def datadog_webhook():
    data = request.json
    print("📩 Webhook recibido:", data)  # Se imprime en consola todo el JSON

    # 🔊 Reproducir sonido en un hilo aparte
    threading.Thread(target=playsound, args=("alert.mp3",), daemon=True).start()

    # 📢 Mostrar alerta visual genérica
    threading.Thread(target=show_alert, daemon=True).start()

    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(port=5006, debug=True)

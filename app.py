from flask import Flask, request
from playsound import playsound
import threading
import subprocess
import sys

app = Flask(__name__)

# 🚀 Lanzar ventana GIF en proceso independiente
def show_gif_popup(gif_path, duration=4):
    subprocess.Popen([sys.executable, "popup.py", gif_path, str(duration)])

@app.route("/datadog-webhook", methods=["POST"])
def datadog_webhook():
    data = request.json
    print("📩 Webhook recibido:", data)

    # 🔊 Sonido en hilo aparte
    threading.Thread(target=playsound, args=("alert.mp3",), daemon=True).start()

    # 🖼️ Lanzar ventana popup en proceso aparte
    threading.Thread(target=show_gif_popup, args=("alert.gif", 10), daemon=True).start()

    return {"status": "ok"}, 200

if __name__ == "__main__":
    print("🚀 Flask escuchando en http://127.0.0.1:5006")
    app.run(port=5006, debug=True)

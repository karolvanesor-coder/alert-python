from flask import Flask, request
from playsound import playsound
import threading
import subprocess
import tkinter as tk
import time

app = Flask(__name__)

# Función para mostrar alerta visual nativa en macOS
def show_alert(title, message):
    script = f'display notification "{message}" with title "{title}"'
    subprocess.run(["osascript", "-e", script])

# Función animación explosión en ventana
def explosion_animation(title, message):
    root = tk.Tk()
    root.title(title)
    root.configure(bg="black")

    canvas = tk.Canvas(root, width=400, height=400, bg="black")
    canvas.pack()

    text = canvas.create_text(
        200, 200,
        text=message,
        fill="white",
        font=("Helvetica", 16, "bold")
    )

    # Animar círculos explosivos
    for r in range(10, 200, 10):
        color = "red" if r % 20 == 0 else "yellow"
        canvas.create_oval(200-r, 200-r, 200+r, 200+r, outline=color, width=3)
        root.update()
        time.sleep(0.05)

    root.mainloop()

# Ruta para recibir el webhook de Datadog
@app.route("/datadog-webhook", methods=["POST"])
def datadog_webhook():
    data = request.json
    print("📩 Webhook recibido:", data)

    # Extraer información básica
    event_title = data.get("title", "Alerta sin título")
    event_msg = data.get("body", "Sin detalles")

    # 🔊 Reproducir sonido en un hilo aparte
    threading.Thread(target=playsound, args=("alert.mp3",), daemon=True).start()

    # 📢 Mostrar alerta visual en un hilo aparte
    threading.Thread(target=show_alert, args=(event_title, event_msg), daemon=True).start()

    # 💥 Lanzar animación explosiva en un hilo aparte
    threading.Thread(target=explosion_animation, args=(event_title, event_msg), daemon=True).start()

    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(port=5005, debug=True)

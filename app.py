from flask import Flask, request
from playsound import playsound
import threading
import subprocess
import tkinter as tk
import time

app = Flask(__name__)

# 🔔 Notificación nativa en macOS
def show_alert(title, message):
    script = f'display notification "{message}" with title "{title}"'
    subprocess.run(["osascript", "-e", script])

# 📊 Ventana gráfica (animación simple)
def show_graph(title, message):
    root = tk.Tk()
    root.title(title)
    root.configure(bg="black")

    canvas = tk.Canvas(root, width=400, height=400, bg="black")
    canvas.pack()

    canvas.create_text(
        200, 200,
        text=message,
        fill="white",
        font=("Helvetica", 16, "bold")
    )

    # Animación de círculos concéntricos
    for r in range(20, 200, 20):
        color = "red" if r % 40 == 0 else "yellow"
        canvas.create_oval(200-r, 200-r, 200+r, 200+r, outline=color, width=3)
        root.update()
        time.sleep(0.05)

    root.mainloop()

# 🚀 Webhook de Datadog
@app.route("/datadog-webhook", methods=["POST"])
def datadog_webhook():
    data = request.json
    print("📩 Webhook recibido:", data)

    # Info básica
    event_title = data.get("title", "Alerta sin título")
    event_msg = data.get("body", "Sin detalles")

    # ✅ Sonido (igual al primer code, no tocado)
    threading.Thread(target=playsound, args=("alert.mp3",), daemon=True).start()

    # ✅ Notificación (igual al primer code, no tocado)
    threading.Thread(target=show_alert, args=(event_title, event_msg), daemon=True).start()

    # ➕ Gráfico agregado
    threading.Thread(target=show_graph, args=(event_title, event_msg), daemon=True).start()

    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(port=5005, debug=True)

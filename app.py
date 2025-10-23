from flask import Flask, request
from playsound import playsound
import threading
import subprocess
import sys
import requests

app = Flask(__name__)

# Configuración base para alertas críticas (rojas)
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

# WhatsApp Cloud API
WHATSAPP_TOKEN = "EAAWr2FNDoE4BP0j1kke6ouKD8jbZBL3sIRkXve1CbczxyO69n82GzfFhRvphD04WCKDlcENQJRR2GRuHsXEQlp4UKvVGWoptRexkEbKChymiBkNZAmfsjMh86SR1hFFOU182Y8vRAkX5zivTmnjkTI4jvJ3S6sDDz2dQjwwRE1pvV8xp4P6xn8JYfTTAZDZD"
WHATSAPP_NUMBER_ID = "847870818407171"  # ID de tu número de WhatsApp Business
WHATSAPP_TO_NUMBER = "573026298197"      # Número de destinatario (sin +)

# Mostrar popup
def show_gif_popup(gif_path, duration=4, message="⚠️ Alerta sin mensaje", border_color="red"):
    subprocess.Popen([sys.executable, "./interface/popup.py", gif_path, str(duration), message, border_color])

# Enviar mensaje por WhatsApp Cloud API
def send_whatsapp_alert_api(message):
    url = f"https://graph.facebook.com/v22.0/{WHATSAPP_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": WHATSAPP_TO_NUMBER,
        "type": "template",
        "template": {
            "name": "hello_world",   # Nombre de tu plantilla
            "language": {"code": "en_US"},
            "components": [{"type": "body", "parameters": [{"type": "text", "text": message}]}]
        }
    }
    try:
        r = requests.post(url, headers=headers, json=payload)
        if r.status_code == 200:
            print("✅ Mensaje enviado a WhatsApp correctamente")
        else:
            print("⚠️ Error al enviar WhatsApp:", r.status_code, r.text)
    except Exception as e:
        print("❌ Error de conexión:", e)

@app.route("/datadog-webhook", methods=["POST"])
def datadog_webhook():
    data = request.json
    print("📩 Webhook recibido:", data)

    raw_tags = data.get("tags", "")
    host = data.get("host", "Desconocido")
    alert_type = str(data.get("alert_type", "alert")).lower()

    # Normalizar tags
    if isinstance(raw_tags, str):
        tags = [t.strip().upper() for t in raw_tags.split(",") if t.strip()]
    else:
        tags = [str(t).upper() for t in raw_tags]
    print("✅ Tags procesados:", tags)

    selected_tag = next((tag for tag in tags if tag in ALERT_CONFIG), None)

    # --- Lógica especial: solo DISCO tiene warning amarillo ---
    if selected_tag == "DISCO" and "warn" in alert_type:
        border_color = "yellow"
        sound_file = "./sound/alert-warn.mp3"
        gif_file = "./gif/warn.gif"
        titulo = "⚠️ ALERTA PREVENTIVA"
        emoji = "🟡"
        message = f"{titulo}\n{emoji} {selected_tag or 'SIN TAG'}\nHost: {host}"
        print("🟡 Alerta preventiva de DISCO detectada")

        # Enviar mensaje de WhatsApp Cloud API en hilo aparte
        threading.Thread(target=send_whatsapp_alert_api, args=(message,), daemon=True).start()
    else:
        border_color = "red"
        titulo = "🚨 ALERTA CRÍTICA"
        emoji = "🔴"
        if selected_tag:
            sound_file = ALERT_CONFIG[selected_tag]["sound"]
            gif_file = ALERT_CONFIG[selected_tag]["gif"]
        else:
            sound_file = DEFAULT_SOUND
            gif_file = DEFAULT_GIF
        message = f"{titulo}\n{emoji} {selected_tag or 'SIN TAG'}\nHost: {host}"

    # Reproducir sonido
    threading.Thread(target=playsound, args=(sound_file,), daemon=True).start()

    # Mostrar popup
    threading.Thread(target=show_gif_popup, args=(gif_file, 6, message, border_color), daemon=True).start()

    print(f"🎵 Sonido: {sound_file} | 🎞 GIF: {gif_file} | 🎨 Color: {border_color}")
    return {"status": "ok", "tags_recibidos": tags, "host": host, "color": border_color}, 200

if __name__ == "__main__":
    print("Flask escuchando en http://127.0.0.1:5006")
    app.run(port=5006, debug=True)

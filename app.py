from flask import Flask, request
from playsound import playsound
import threading
import subprocess
import sys
import requests
import json

app = Flask(__name__)

# -------------------------------
# ⚙️ Configuración de alertas
# -------------------------------
ALERT_CONFIG = {
    "CPU": {"sound": "./sound/alert.mp3", "gif": "./gif/alert.gif"},
    "MEMORIA": {"sound": "./sound/alert1.mp3", "gif": "./gif/alert1.gif"},
    "DISCO": {"sound": "./sound/alert2.mp3", "gif": "./gif/alert2.gif"}
}

DEFAULT_SOUND = "./sound/alert.mp3"
DEFAULT_GIF = "./gif/alert.gif"

# -------------------------------
# 💬 Configuración WhatsApp Cloud API
# -------------------------------
WHATSAPP_TOKEN = "EAAWr2FNDoE4BPylAk01jG7cvYSGSxirB26uCv03hhU6oLqtATASZBn05ZA5sQ4176soEwBPg4hIP5dX7CgaiJHwZBqPsbY4cq9oaZB5DyFzcWYuPgZBZBt8PZCmoMZCq8J7ajVEBdtMnOndbZAkl6fBegZC7M2v9HmUmYzi9ZBIbera7mVmNHso769fEv3rw1RrHwZDZD"
WHATSAPP_NUMBER_ID = "847870818407171"
WHATSAPP_TO_NUMBER = "573026298197"

# 💬 Configuración Telegram Bot
TELEGRAM_TOKEN = "8341737855:AAFRvmJIiLzKWl-Vzq1NhkzVvdtP544n8zo"
TELEGRAM_CHAT_IDS = [
    "1515649395", #karol
    "399817462"   #marcos
    ]

# -------------------------------
# 🖼 Mostrar Popup
# -------------------------------
def show_gif_popup(gif_path, duration=4, message="⚠️ Alerta sin mensaje", border_color="red"):
    try:
        subprocess.Popen([sys.executable, "./interface/popup.py", gif_path, str(duration), message, border_color])
    except Exception as e:
        print("⚠️ Error al mostrar popup:", e)

# -------------------------------
# 📲 Enviar alerta por WhatsApp (plantilla)
# -------------------------------
def send_whatsapp_template(host_name):
    """Envía una alerta preventiva usando plantilla aprobada"""
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
            "name": "alerta_preventiva_disco",  
            "language": {"code": "es_CO"},      
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": host_name,
                            "parameter_name": "server_name"  #nombre de la variable en plantilla
                        }
                    ]
                }
            ]
        }
    }

    try:
        r = requests.post(url, headers=headers, json=payload)
        if r.status_code == 200:
            print("✅ WhatsApp (plantilla) enviado correctamente")
        else:
            print(f"⚠️ Error al enviar WhatsApp: {r.status_code} → {r.text}")
    except Exception as e:
        print("❌ Error al conectar con WhatsApp:", e)

# -------------------------------
# 📩 Enviar alerta a Telegram
# -------------------------------

# nombre del bot wn telegram: alerta_preventiva_disco_bo 

def send_telegram_message(message):
    """Envía mensaje al chat de Telegram"""
    for chat_id in TELEGRAM_CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            r = requests.post(url, json=payload)
            if r.status_code == 200:
                print(f"✅ Telegram enviado correctamente a {chat_id}")
            else:
                print(f"⚠️ Error al enviar Telegram a {chat_id}: {r.status_code} → {r.text}")
        except Exception as e:
            print("❌ Error al conectar con Telegram:", e)

# -------------------------------
# 📡 Webhook de Datadog
# -------------------------------
@app.route("/datadog-webhook", methods=["POST"])
def datadog_webhook():
    data = request.json or {}
    print("\n📩 Webhook recibido:\n", json.dumps(data, indent=2, ensure_ascii=False))

    raw_tags = data.get("tags", [])
    host = data.get("host", "Desconocido")
    alert_type = str(data.get("alert_type", "alert")).lower()

    tags = [t.strip().upper() for t in raw_tags] if isinstance(raw_tags, list) else \
           [t.strip().upper() for t in str(raw_tags).split(",") if t.strip()]

    selected_tag = next((tag for tag in tags if tag in ALERT_CONFIG), None)

    # 🟡 Solo enviar WhatsApp para disco preventivo
    if selected_tag == "DISCO" and "warn" in alert_type:
        border_color = "yellow"
        sound_file = "./sound/alert-warn.mp3"
        gif_file = "./gif/warn.gif"
        message = f"⚠️ ALERTA PREVENTIVA DE DISCO 🟡\nHost: {host}\nVerifica el espacio en disco lo antes posible."

        print("🟡 Alerta preventiva detectada - enviando plantilla WhatsApp...")
        threading.Thread(target=send_whatsapp_template, args=(host,), daemon=True).start()

        print("🟡 Alerta preventiva detectada - enviando plantilla Telegram...")
        threading.Thread(target=send_telegram_message, args=(message,), daemon=True).start()

    else:
        border_color = "red"
        sound_file = ALERT_CONFIG.get(selected_tag, {}).get("sound", DEFAULT_SOUND)
        gif_file = ALERT_CONFIG.get(selected_tag, {}).get("gif", DEFAULT_GIF)
        message = f"🚨 ALERTA CRÍTICA 🔴\nTipo: {selected_tag or 'SIN TAG'}\nHost: {host}"

    threading.Thread(target=playsound, args=(sound_file,), daemon=True).start()
    threading.Thread(target=show_gif_popup, args=(gif_file, 6, message, border_color), daemon=True).start()

    return {"status": "ok", "tags": tags, "host": host}, 200

# -------------------------------
# 🚀 Inicio
# -------------------------------
if __name__ == "__main__":
    print("🚀 Flask escuchando en http://127.0.0.1:5006")
    app.run(host="0.0.0.0", port=5006, debug=True)


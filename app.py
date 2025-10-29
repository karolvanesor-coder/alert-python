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
    "DISCO": {"sound": "./sound/alert2.mp3", "gif": "./gif/alert2.gif"},
    "ALERTDB": {"sound": "./sound/alertdb.mp3", "gif": "./gif/alertdb.gif"},
    "ALERTMQ": {"sound": "./sound/alert-disponibilidad.mp3", "gif": "./gif/alertdisponibilidad.gif"},
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
    "-4983450099"  # ID del grupo de Telegram
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
                        {"type": "text", "text": host_name, "parameter_name": "server_name"}
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
def send_telegram_message(message):
    """Envía mensaje al chat de Telegram"""
    for chat_id in TELEGRAM_CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
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
    title = str(data.get("title", "")).upper()

    tags = [t.strip().upper() for t in raw_tags] if isinstance(raw_tags, list) else \
           [t.strip().upper() for t in str(raw_tags).split(",") if t.strip()]

    selected_tag = next((tag for tag in tags if tag in ALERT_CONFIG), None)

    # 🟡 Alerta preventiva de disco (warning)
    if selected_tag == "DISCO" and "warn" in alert_type:
        border_color = "yellow"
        sound_file = "./sound/alert-warn.mp3"
        gif_file = "./gif/warn.gif"
        message = f"⚠️ ALERTA PREVENTIVA DE DISCO \nHost: {host}\nVerifica el espacio en disco lo antes posible."

        print("🟡 Enviando WhatsApp y Telegram para alerta preventiva...")
        threading.Thread(target=send_whatsapp_template, args=(host,), daemon=True).start()
        threading.Thread(target=send_telegram_message, args=(message,), daemon=True).start()

     # 🟠 Alerta naranja: RabbitMQ
    elif "ALERTMQ" in tags or "RABBITMQ" in title:
        border_color = "orange"
        sound_file = "./sound/alert-disponibilidad.mp3"
        gif_file = "./gif/alertdisponibilidad.gif"
        tipo_alerta = "Consumidores por cola RabbitMQ"

        message = f"🟠 ALERTA RABBITMQ\nTipo: {tipo_alerta}"
        print("🟠 Enviando Telegram para alerta RabbitMQ...")
        threading.Thread(target=send_telegram_message, args=(message,), daemon=True).start()

# 🟣 Alerta morada: Bloqueos por sesiones DB
elif "ALERTDB" in tags or "DATABASE" in title:
    border_color = "purple"
    sound_file = "./sound/alertdb.mp3"
    gif_file = "./gif/alertdb.gif"
    tipo_alerta = "Bloqueos por sesiones DB"

    # 🧩 Extraer la instancia del JSON del webhook
    group_data = data.get("group", "") or data.get("event", {}).get("group", "")
    instancia = str(group_data).replace("database_hostname:", "").strip() or "Desconocido"

    # 🌎 Detección del país según la instancia
    if "colombia" in instancia.lower():
        pais = "🇨🇴 Colombia"
    elif "mexico" in instancia.lower():
        pais = "🇲🇽 México"
    elif "chile" in instancia.lower():
        pais = "🇨🇱 Chile"
    elif "ecuador" in instancia.lower():
        pais = "🇪🇨 Ecuador"
    elif "panama" in instancia.lower():
        pais = "🇵🇦 Panamá"
    elif "paraguay" in instancia.lower():
        pais = "🇵🇾 Paraguay"
    elif "peru" in instancia.lower():
        pais = "🇵🇪 Perú"
    elif "produit" in instancia.lower():
        pais = "🏭 Produit"
    else:
        pais = "🌍 Desconocido"

    # 🧠 Detectar si es un nodo especial (reader, ms, etc.)
    extra_info = ""
    if "reader" in instancia.lower():
        extra_info = "🔹 *Nodo Reader*"
    elif "ms" in instancia.lower():
        extra_info = "🔹 *Microservicio*"

    # 💬 Mensaje Telegram
    message = (
        f"🟣 *ALERTA BLOQUEOS DB*\n"
        f"📍 *Instancia:* `{instancia}`\n"
        f"🌎 *País:* {pais}\n"
        f"{extra_info}\n"
        f"⚙️ *Tipo:* {tipo_alerta}"
    )

    print("🟣 Enviando Telegram para alerta de bloqueos DB...")
    threading.Thread(target=send_telegram_message, args=(message,), daemon=True).start()


    # 🔴 Resto de alertas críticas
    else:
        border_color = "red"
        sound_file = ALERT_CONFIG.get(selected_tag, {}).get("sound", DEFAULT_SOUND)
        gif_file = ALERT_CONFIG.get(selected_tag, {}).get("gif", DEFAULT_GIF)
        message = f"🚨 ALERTA CRÍTICA \nTipo: {selected_tag or 'SIN TAG'}\nHost: {host}"

    # Ejecutar sonido y popup
    threading.Thread(target=playsound, args=(sound_file,), daemon=True).start()
    threading.Thread(target=show_gif_popup, args=(gif_file, 6, message, border_color), daemon=True).start()

    return {"status": "ok", "tags": tags, "host": host}, 200

# -------------------------------
# 🚀 Inicio
# -------------------------------
if __name__ == "__main__":
    print("🚀 Flask escuchando en http://127.0.0.1:5006")
    app.run(host="0.0.0.0", port=5006, debug=True)

from flask import Flask, request
from playsound import playsound
import threading
import subprocess
import sys
import requests
import json
import time
from queue import Queue

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
    "MEMORIAMQ": {"sound": "./sound/alertmem.mp3", "gif": "./gif/alertmem.gif"},
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
    "-4983450099"
]

# ======================================================
# 🧠 SISTEMA DE COLA DE ALERTAS (sincroniza GIF + texto)
# ======================================================
alert_queue = Queue()
alert_lock = threading.Lock()

def process_alert_queue():
    """Procesa las alertas en orden para que los GIFs y cuadros no se solapen"""
    while True:
        gif_file, duration, message, border_color = alert_queue.get()
        try:
            print(f"🚨 Mostrando alerta sincronizada: {message[:60]}...")
            show_popup_pair(gif_file, duration, message, border_color)
            time.sleep(duration + 0.5)
        finally:
            alert_queue.task_done()

threading.Thread(target=process_alert_queue, daemon=True).start()

def enqueue_alert(gif_file, duration, message, border_color):
    """Agrega una alerta a la cola"""
    alert_queue.put((gif_file, duration, message, border_color))

def show_popup_pair(gif_file, duration, message, border_color):
    """Ejecuta el popup con GIF y mensaje sincronizados"""
    subprocess.Popen(
        [sys.executable, "./interface/popup.py", gif_file, str(duration), message, border_color],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

# -------------------------------
# 📲 Enviar WhatsApp (plantilla)
# -------------------------------
def send_whatsapp_template(host_name):
    url = f"https://graph.facebook.com/v22.0/{WHATSAPP_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": WHATSAPP_TO_NUMBER,
        "type": "template",
        "template": {
            "name": "alerta_preventiva_disco",
            "language": {"code": "es_CO"},
            "components": [{
                "type": "body",
                "parameters": [{"type": "text", "text": host_name}]
            }]
        }
    }
    try:
        r = requests.post(url, headers=headers, json=payload)
        print("✅ WhatsApp enviado correctamente" if r.status_code == 200 else f"⚠️ Error WhatsApp: {r.text}")
    except Exception as e:
        print("❌ Error WhatsApp:", e)

# -------------------------------
# 📩 Enviar Telegram
# -------------------------------
def send_telegram_message(message):
    for chat_id in TELEGRAM_CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        try:
            r = requests.post(url, json=payload)
            print(f"✅ Telegram enviado a {chat_id}" if r.status_code == 200 else f"⚠️ Error Telegram: {r.text}")
        except Exception as e:
            print("❌ Error Telegram:", e)

# -------------------------------
# 📡 Webhook principal
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

    # 🟡 Alerta preventiva de disco
    if selected_tag == "DISCO" and "warn" in alert_type:
        border_color = "yellow"
        sound_file = "./sound/alert-warn.mp3"
        gif_file = "./gif/warn.gif"
        message = f"⚠️ ALERTA PREVENTIVA DE DISCO \nHost: {host}\nVerifica el espacio en disco."

        threading.Thread(target=send_whatsapp_template, args=(host,), daemon=True).start()
        threading.Thread(target=send_telegram_message, args=(message,), daemon=True).start()
        enqueue_alert(gif_file, 6, message, border_color)

    # 🔴 Memoria RabbitMQ
    elif "MEMORIAMQ" in tags or "MEMORIAMQ" in title:
        import re, textwrap
        border_color = "#FF0000"
        gif_file = "./gif/alertmem.gif"
        sound_file = "./sound/alertmem.mp3"
        event = data.get("event", {})
        group = event.get("group", "") or data.get("group", "")
        status_msg = data.get("status", "Sin información adicional")

        match = re.search(r"(rabbitmq_queue[:=][\w\-\._]+)", str(group))
        if not match:
            match = re.search(r"(rabbitmq_queue[:=][\w\-\._]+)", str(data.get("tags", "")))
        queue_name = match.group(1) if match else "rabbitmq_queue:Desconocido"
        host = data.get("host") or queue_name

        message = (
            f"🚨 *ALERTA MEMORIA RABBITMQ*\n"
            f"🖥️ Host: {host}\n"
            f"💾 Estado: {status_msg}\n"
            f"Verifica uso de memoria en el nodo."
        )
        message_wrapped = "\n".join(textwrap.wrap(message, width=60))

        threading.Thread(target=send_telegram_message, args=(message_wrapped,), daemon=True).start()
        enqueue_alert(gif_file, 6, message_wrapped, border_color)

    # 🟠 RabbitMQ consumidores
    elif "ALERTMQ" in tags or "RABBITMQ" in title:
        import re, textwrap
        border_color = "orange"
        gif_file = "./gif/alertdisponibilidad.gif"
        sound_file = "./sound/alert-disponibilidad.mp3"
        event = data.get("event", {})
        group = event.get("group", "") or data.get("group", "")
        status_msg = data.get("status", "Sin información adicional")

        match = re.search(r"(rabbitmq_queue[:=][\w\-\._]+)", str(group))
        if not match:
            match = re.search(r"(rabbitmq_queue[:=][\w\-\._]+)", str(data.get("tags", "")))
        queue_name = match.group(1) if match else "rabbitmq_queue:Desconocido"
        host = data.get("host") or queue_name

        message = (
            f"🟠 ALERTA RABBITMQ - CONSUMIDORES POR COLA\n"
            f"🖥️ Host: {host}\n"
            f"📉 Estado: {status_msg}\n"
            f"Verifica que haya consumidores activos."
        )
        message_wrapped = "\n".join(textwrap.wrap(message, width=60))

        threading.Thread(target=send_telegram_message, args=(message_wrapped,), daemon=True).start()
        enqueue_alert(gif_file, 6, message_wrapped, border_color)

    # 🟣 Bloqueos DB
    elif "ALERTDB" in tags or "DATABASE" in title:
        import re, textwrap
        border_color = "purple"
        gif_file = "./gif/alertdb.gif"
        sound_file = "./sound/alertdb.mp3"
        tipo_alerta = "Bloqueos por sesiones DB"
        event = data.get("event", {})
        group = event.get("group", "") or data.get("group", "")
        title = event.get("title", "") or data.get("title", "")

        hostname = "Desconocido"
        match = re.search(r"([\w-]+\.cluster[\w\.-]+\.amazonaws\.com)", group or title)
        if match:
            hostname = match.group(1)

        country_map = {
            "colombia": "🇨🇴 Colombia",
            "mexico": "🇲🇽 México",
            "chile": "🇨🇱 Chile",
            "ecuador": "🇪🇨 Ecuador",
            "panama": "🇵🇦 Panamá",
            "paraguay": "🇵🇾 Paraguay",
            "peru": "🇵🇪 Perú",
        }
        pais_detectado = next((v for k, v in country_map.items() if k in hostname.lower()), "🌎 No identificado")

        message = (
            f"🟣 ALERTA BLOQUEOS DB\n"
            f"{pais_detectado}\n"
            f"🖥️ Host: {hostname}\n"
            f"💾 Tipo: {tipo_alerta}"
        )

        threading.Thread(target=send_telegram_message, args=(message,), daemon=True).start()
        enqueue_alert(gif_file, 6, message, border_color)

    # 🔴 Resto de alertas
    else:
        border_color = "red"
        sound_file = ALERT_CONFIG.get(selected_tag, {}).get("sound", DEFAULT_SOUND)
        gif_file = ALERT_CONFIG.get(selected_tag, {}).get("gif", DEFAULT_GIF)
        message = f"🚨 ALERTA CRÍTICA \nTipo: {selected_tag or 'SIN TAG'}\nHost: {host}"
        enqueue_alert(gif_file, 6, message, border_color)

    threading.Thread(target=playsound, args=(sound_file,), daemon=True).start()
    return {"status": "ok", "tags": tags, "host": host}, 200

# -------------------------------
# 🚀 Inicio
# -------------------------------
if __name__ == "__main__":
    print("🚀 Flask escuchando en http://127.0.0.1:5006")
    app.run(host="0.0.0.0", port=5006, debug=True)

from flask import Flask, request
from dotenv import load_dotenv
import requests
import os
import json
import textwrap

load_dotenv()

app = Flask(__name__)

# ======================================================
#  VARIABLES DE ENTORNO (OBLIGATORIO EN CLOUD)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_IDS = os.getenv("TELEGRAM_CHAT_IDS", "").split(",")

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_NUMBER_ID = os.getenv("WHATSAPP_NUMBER_ID")
WHATSAPP_TO_NUMBER = os.getenv("WHATSAPP_TO_NUMBER")

print("TELEGRAM_TOKEN:", TELEGRAM_TOKEN)
print("TELEGRAM_CHAT_IDS:", TELEGRAM_CHAT_IDS)

GOOGLE_CHAT_WEBHOOK = os.getenv("GOOGLE_CHAT_WEBHOOK")

# -------------------------------
#  Enviar Google Chat 
# -------------------------------

def send_google_chat_message(message: str):
    payload = {
        "text": message
    }

    try:
        r = requests.post(GOOGLE_CHAT_WEBHOOK, json=payload, timeout=5)
        if r.status_code == 200:
            print("✅ Google Chat enviado correctamente")
        else:
            print(f"⚠️ Error Google Chat: {r.text}")
    except Exception as e:
        print("❌ Error Google Chat:", e)

# ======================================================
# TELEGRAM
# ======================================================

def send_telegram_message(message: str):
    for chat_id in TELEGRAM_CHAT_IDS:
        if not chat_id:
            continue

        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message
        }

        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print("❌ Telegram error:", e)


# ======================================================
#  WEBHOOK DATADOG
# ======================================================

@app.route("/datadog-webhook", methods=["POST"])
def datadog_webhook():
    data = request.json or {}

    tags = [t.upper() for t in data.get("tags", [])]
    host = data.get("host", "Desconocido")
    status = data.get("status", "Sin información")
    alert_type = str(data.get("alert_type", "")).lower()

    print("📩 Webhook recibido:", json.dumps(data, indent=2, ensure_ascii=False))

    # ------------------------
    # 🔴 CPU
    # ------------------------
    if "CPU" in tags:
        msg = f"🔴 ALERTA CPU\n🖥️ Host: {host}\n📉 Estado: {status}"
        send_telegram_message("\n".join(textwrap.wrap(msg, 60)))

    # ------------------------
    # 🔵 MEMORIA
    # ------------------------
    if "MEMORIA" in tags:
        msg = f"🔵 ALERTA MEMORIA\n🖥️ Host: {host}\n📉 Estado: {status}"
        send_telegram_message("\n".join(textwrap.wrap(msg, 60)))

    # ------------------------
    # 🟣 DISCO
    # ------------------------
    if "DISCO" in tags:
        msg = f"🟣 ALERTA DISCO\n🖥️ Host: {host}\n📉 Estado: {status}"
        send_telegram_message("\n".join(textwrap.wrap(msg, 60)))

        # Preventiva
        if "warn" in alert_type:
            send_whatsapp_template(host)

    # ------------------------
    # 🟡 PHP-FPM
    # ------------------------
    if "PHPFPM" in tags:
        msg = f"🟡 ALERTA PHP-FPM\n🖥️ Host: {host}\n📉 Estado: {status}"
        send_telegram_message("\n".join(textwrap.wrap(msg, 60)))

    return {"status": "ok"}, 200

# ======================================================
#  START
# ======================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5007)

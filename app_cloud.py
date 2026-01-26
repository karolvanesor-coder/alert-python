from flask import Flask, request
from dotenv import load_dotenv
import requests
import os
import json
import textwrap
import re

load_dotenv()
app = Flask(__name__)

# ======================================================
# VARIABLES DE ENTORNO
# ======================================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_IDS = os.getenv("TELEGRAM_CHAT_IDS", "").split(",")
GOOGLE_CHAT_WEBHOOK = os.getenv("GOOGLE_CHAT_WEBHOOK")

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
# GOOGLE CHAT
# ======================================================

def send_google_chat_message(message: str):
    if not GOOGLE_CHAT_WEBHOOK:
        return

    try:
        requests.post(
            GOOGLE_CHAT_WEBHOOK,
            json={"text": message},
            timeout=5
        )
    except Exception as e:
        print("❌ Google Chat error:", e)

# ======================================================
# ENVÍO UNIFICADO
# ======================================================

def send_alert(message: str):
    message_wrapped = "\n".join(textwrap.wrap(message, 60))
    send_telegram_message(message_wrapped)
    send_google_chat_message(message_wrapped)

# ======================================================
# WEBHOOK DATADOG
# ======================================================

@app.route("/datadog-webhook", methods=["POST"])
def datadog_webhook():
    data = request.json or {}
    print("📩 Webhook recibido:\n", json.dumps(data, indent=2, ensure_ascii=False))

    raw_tags = data.get("tags", [])
    tags = [t.strip().upper() for t in raw_tags] if isinstance(raw_tags, list) else []
    host = data.get("host", "Desconocido")
    status = data.get("status", "Sin información")
    alert_type = str(data.get("alert_type", "")).lower()
    title = str(data.get("title", "")).upper()
    group = data.get("group", "") or ""

    alert_triggered = False

    # --------------------------------------------------
    # 🔴 CPU
    # --------------------------------------------------
    if "CPU" in tags:
        send_alert(
            f"🔴 ALERTA CPU\n"
            f"🖥️ Host: {host}\n"
            f"📉 Estado: {status}"
        )
        alert_triggered = True

    # --------------------------------------------------
    # 🔵 MEMORIA
    # --------------------------------------------------
    if "MEMORIA" in tags:
        send_alert(
            f"🔵 ALERTA MEMORIA\n"
            f"🖥️ Host: {host}\n"
            f"📉 Estado: {status}"
        )
        alert_triggered = True

    # --------------------------------------------------
    # 🟣 DISCO
    # --------------------------------------------------
    if "DISCO" in tags:
        send_alert(
            f"🟣 ALERTA DISCO\n"
            f"🖥️ Host: {host}\n"
            f"📉 Estado: {status}"
        )
        alert_triggered = True

        if "warn" in alert_type:
            send_alert(
                f"⚠️ ALERTA PREVENTIVA DE DISCO\n"
                f"🖥️ Host: {host}\n"
                f"Revisar espacio en disco"
            )

    # --------------------------------------------------
    # 🟡 PHP-FPM
    # --------------------------------------------------
    if "PHPFPM" in tags:
        send_alert(
            f"🟡 ALERTA PHP-FPM\n"
            f"🖥️ Host: {host}\n"
            f"📉 Estado: {status}"
        )
        alert_triggered = True

    # --------------------------------------------------
    # 🟠 RABBITMQ CONSUMIDORES
    # --------------------------------------------------
    if "ALERTMQ" in tags or "RABBITMQ" in title:
        send_alert(
            f"🟠 ALERTA RABBITMQ\n"
            f"🖥️ Host: {host}\n"
            f"📉 Estado: {status}"
        )
        alert_triggered = True

    # --------------------------------------------------
    # 🔶 MENSAJES EN COLA
    # --------------------------------------------------
    if "ALERTQUEUE" in tags:
        send_alert(
            f"🔶 ALERTA MENSAJES EN COLA\n"
            f"🖥️ Host: {host}\n"
            f"📉 Estado: {status}"
        )
        alert_triggered = True

    # --------------------------------------------------
    # 🟣 BLOQUEOS DB
    # --------------------------------------------------
    if "ALERTDB" in tags:
        hostname = "Desconocido"
        m = re.search(r"([\w\.-]+\.amazonaws\.com)", group)
        if m:
            hostname = m.group(1)

        send_alert(
            f"🟣 ALERTA BLOQUEOS DB\n"
            f"🖥️ Host: {hostname}\n"
            f"📉 Estado: {status}"
        )
        alert_triggered = True

    # --------------------------------------------------
    # 🔴 CPU DB
    # --------------------------------------------------
    if "CPUDB" in tags:
        send_alert(
            f"🔴 ALERTA CPU DB\n"
            f"🖥️ Host: {host}\n"
            f"📉 Estado: {status}"
        )
        alert_triggered = True

    # --------------------------------------------------
    # 🔵 CONEXIONES DB
    # --------------------------------------------------
    if "CONNDB" in tags:
        send_alert(
            f"🔵 ALERTA CONEXIONES DB\n"
            f"🖥️ Host: {host}\n"
            f"📉 Estado: {status}"
        )
        alert_triggered = True

    # --------------------------------------------------
    # 🟠 SUPERVISOR
    # --------------------------------------------------
    if "SUPERVISOR" in tags:
        send_alert(
            f"🟠 ALERTA SUPERVISOR\n"
            f"🖥️ Host: {host}\n"
            f"📉 Estado: {status}"
        )
        alert_triggered = True

    # --------------------------------------------------
    # 🚨 FALLBACK
    # --------------------------------------------------
    if not alert_triggered:
        send_alert(
            f"🚨 ALERTA SIN TAG RECONOCIDO\n"
            f"🖥️ Host: {host}\n"
            f"📉 Estado: {status}"
        )

    return {"status": "ok"}, 200

# ======================================================
# START
# ======================================================

if __name__ == "__main__":
    print("🚀 Webhook Datadog CLOUD activo")
    app.run(host="0.0.0.0", port=5007)

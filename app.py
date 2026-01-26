from flask import Flask, request
from playsound import playsound
import threading
import subprocess
import sys
import requests
import json
import time
from queue import Queue
import re
import textwrap
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# -------------------------------
# Configuración de alertas
# -------------------------------

ALERT_CONFIG = {
    "CPU": {"sound": "./sound/cpu.mp3", "gif": "./gif/alert.gif"},
    "MEMORIA": {"sound": "./sound/memoria.mp3", "gif": "./gif/alert1.gif"},
    "DISCO": {"sound": "./sound/disco.mp3", "gif": "./gif/alert2.gif"},
    "ALERTDB": {"sound": "./sound/alertdb.mp3", "gif": "./gif/alertdb.gif"},
    "ALERTMQ": {"sound": "./sound/disponibilidad.mp3", "gif": "./gif/alertdisponibilidad.gif"},
    "ALERTQUEUE": {"sound": "./sound/alertqueue.mp3", "gif": "./gif/alertqueue.gif"},
    "MEMORIAMQ": {"sound": "./sound/alertmem.mp3", "gif": "./gif/alertmem.gif"},
    "CPUDB": {"sound": "./sound/alertcpudb.mp3", "gif": "./gif/alertcpudb.gif"},
    "CONNDB": {"sound": "./sound/alertconndb.mp3", "gif": "./gif/alertconndb.gif"},
    "SUPERVISOR": {"sound": "./sound/supervisor.mp3", "gif": "./gif/supervisor.gif"},
    "PHPFPM": {"sound": "./sound/fpm.mp3", "gif": "./gif/fpm.gif"},
}

DEFAULT_SOUND = "./sound/alert.mp3"
DEFAULT_GIF = "./gif/alert.gif"

# -------------------------------
# Configuración desde ENV
# -------------------------------

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_IDS = os.getenv("TELEGRAM_CHAT_IDS", "").split(",")

GOOGLE_CHAT_WEBHOOK = os.getenv("GOOGLE_CHAT_WEBHOOK")

# ======================================================
# SISTEMA DE COLA DE ALERTAS (sincroniza GIF + texto)
# ======================================================

alert_queue = Queue()

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
#  Enviar Telegram
# -------------------------------

def send_telegram_message(message):
    for chat_id in TELEGRAM_CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message
        }
        try:
            r = requests.post(url, json=payload)
            print(f"✅ Telegram enviado a {chat_id}" if r.status_code == 200 else f"⚠️ Error Telegram: {r.text}")
        except Exception as e:
            print("❌ Error Telegram:", e)

# -------------------------------
#  Enviar Google Chat 
# -------------------------------

def send_google_chat_message(message: str):
    if not GOOGLE_CHAT_WEBHOOK:
        print("⚠️ GOOGLE_CHAT_WEBHOOK no definido")
        return

    payload = {"text": message}

    try:
        r = requests.post(
            GOOGLE_CHAT_WEBHOOK,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )

        print("📨 Google Chat status:", r.status_code)

        if r.status_code != 200:
            print("❌ Google Chat error:", r.text)

    except Exception as e:
        print("❌ Google Chat exception:", e)

# -------------------------------
#  Webhook principal
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

    # Inicializar con valores predeterminados para la alerta final
    border_color = "red"
    sound_file = DEFAULT_SOUND
    gif_file = DEFAULT_GIF
    message = f"🚨 ALERTA CRÍTICA \nTipo: {selected_tag or 'SIN TAG'}\nHost: {host}"
    
    alert_triggered = False # Flag para saber si se ha manejado la alerta

    # Asegurar que group existe para las siguientes comprobaciones
    group = data.get("group", "") or ""

    # 🔴 ALERTA CPU
    if "CPU" in tags:
        cfg = ALERT_CONFIG.get("CPU", {})
        border_color = "red"
        sound_file = cfg.get("sound", DEFAULT_SOUND)
        gif_file = cfg.get("gif", DEFAULT_GIF)

        status_msg = data.get("status", "Sin información adicional")
        
        message = (
            f"🔴 ALERTA CPU\n"
            f"🖥️ Host: {host}"
        )
        message_wrapped = "\n".join(textwrap.wrap(message, width=60))
        threading.Thread(target=send_telegram_message, args=(message_wrapped,), daemon=True).start()
        threading.Thread(target=send_google_chat_message,args=(message_wrapped,),daemon=True).start()

        alert_triggered = True

    # 🔵 ALERTA MEMORIA
    if "MEMORIA" in tags:
        cfg = ALERT_CONFIG.get("MEMORIA", {})
        border_color = "blue"
        sound_file = cfg.get("sound", DEFAULT_SOUND)
        gif_file = cfg.get("gif", DEFAULT_GIF)

        status_msg = data.get("status", "Sin información adicional")

        message = (
            f"🔵 ALERTA MEMORIA\n"
            f"🖥️ Host: {host}"
        )
        message_wrapped = "\n".join(textwrap.wrap(message, width=60))
        threading.Thread(target=send_telegram_message, args=(message_wrapped,), daemon=True).start()
        threading.Thread(target=send_google_chat_message,args=(message_wrapped,),daemon=True).start()

        alert_triggered = True

    # 🟣 ALERTA DISCO
    if "DISCO" in tags:
        cfg = ALERT_CONFIG.get("DISCO", {})
        border_color = "purple"
        sound_file = cfg.get("sound", DEFAULT_SOUND)
        gif_file = cfg.get("gif", DEFAULT_GIF)

        status_msg = data.get("status", "Sin información adicional")

        message = (
            f"🟣 ALERTA DISCO\n"
            f"🖥️ Host: {host}"
        )
        message_wrapped = "\n".join(textwrap.wrap(message, width=60))
        threading.Thread(target=send_telegram_message, args=(message_wrapped,), daemon=True).start()
        threading.Thread(target=send_google_chat_message,args=(message_wrapped,),daemon=True).start()

        alert_triggered = True

    # 🟡 Alerta preventiva de disco
    if selected_tag == "DISCO" and "warn" in alert_type:
        border_color = "yellow"
        sound_file = "./sound/alert-warn.mp3"
        gif_file = "./gif/warn.gif"

        message = (
            f"⚠️ ALERTA PREVENTIVA DE DISCO\n"
            f"🖥️ Host: {host}\n"
            f"Verifica el espacio en disco."
        )

        message_wrapped = "\n".join(textwrap.wrap(message, width=60))

        threading.Thread(
            target=send_telegram_message,
            args=(message_wrapped,),
            daemon=True
        ).start()

        threading.Thread(
            target=send_google_chat_message,
            args=(message_wrapped,),
            daemon=True
        ).start()

        alert_triggered = True

    # 🔴 Memoria RabbitMQ
    if "MEMORIAMQ" in tags:
        border_color = "#FF0000"
        gif_file = "./gif/alertmem.gif"
        sound_file = "./sound/alertmem.mp3"

        event = data.get("event", {})
        group_mq = event.get("group", "") or data.get("group", "")
        status_msg = data.get("status", "Sin información adicional")

        match = re.search(r"(rabbitmq_queue[:=][\w\-\._]+)", str(group_mq))
        if not match:
            match = re.search(r"(rabbitmq_queue[:=][\w\-\._]+)", str(data.get("tags", "")))
        queue_name = match.group(1) if match else "rabbitmq_queue:Desconocido"

        host = data.get("host") or queue_name

        message = (
            f"🚨 ALERTA MEMORIA RABBITMQ\n"
            f"🖥️ Host: {host}\n"
            f"📉 Estado: {status_msg}\n"
        )

        message_wrapped = "\n".join(textwrap.wrap(message, width=60))
        threading.Thread(target=send_telegram_message, args=(message_wrapped,), daemon=True).start()
        threading.Thread(target=send_google_chat_message,args=(message_wrapped,),daemon=True).start()

        alert_triggered = True

    # 🟠 RabbitMQ consumidores por cola
    if "ALERTMQ" in tags or "RABBITMQ" in title:
        border_color = "orange"
        gif_file = "./gif/alertdisponibilidad.gif"
        sound_file = "./sound/disponibilidad.mp3"
        event = data.get("event", {})
        group_mq = event.get("group", "") or data.get("group", "")
        status_msg = data.get("status", "Sin información adicional")

        match = re.search(r"(rabbitmq_queue[:=][\w\-\._]+)", str(group_mq))
        if not match:
            match = re.search(r"(rabbitmq_queue[:=][\w\-\._]+)", str(data.get("tags", "")))
        queue_name = match.group(1) if match else "rabbitmq_queue:Desconocido"
        host = data.get("host") or queue_name

        message = (
            f"🟠 ALERTA RABBITMQ - CONSUMIDORES POR COLA\n"
            f"🖥️ Host: {host}\n"
            f"📉 Estado: {status_msg}"
        )
        message_wrapped = "\n".join(textwrap.wrap(message, width=60))

        threading.Thread(target=send_telegram_message, args=(message_wrapped,), daemon=True).start()
        threading.Thread(target=send_google_chat_message,args=(message_wrapped,),daemon=True).start()

        alert_triggered = True

    # 🟧 Mensajes pendientes en colas RabbitMQ
    if "ALERTQUEUE" in tags:
        border_color = "orange"
        gif_file = "./gif/alertqueue.gif"
        sound_file = "./sound/alertqueue.mp3"

        event = data.get("event", {})
        group_mq = event.get("group", "") or data.get("group", "")
        status_msg = data.get("status", "Sin información adicional")

        match = re.search(r"(rabbitmq_queue[:=][\w\-\._]+)", str(group_mq))
        if not match:
            match = re.search(r"(rabbitmq_queue[:=][\w\-\._]+)", str(data.get("tags", "")))
        queue_name = match.group(1) if match else "rabbitmq_queue:Desconocido"
        host = data.get("host") or queue_name

        message = (
            f"🔶 ALERTA RABBITMQ - MENSAJES EN COLA\n"
            f"🖥️ Host: {host}\n"
            f"📉 Estado: {status_msg}"
        )
        message_wrapped = "\n".join(textwrap.wrap(message, width=60))

        threading.Thread(target=send_telegram_message, args=(message_wrapped,), daemon=True).start()
        threading.Thread(target=send_google_chat_message,args=(message_wrapped,),daemon=True).start()

        alert_triggered = True

    # 🟣 Cola específica tracking_pull_queue_co
    if "QUEUECO" in tags:
        border_color = "purple"
        gif_file = "./gif/alertqueue.gif"
        sound_file = "./sound/alertqueue.mp3"

        status_msg = data.get("status", "Sin información adicional")
        event = data.get("event", {})
        group_mq = event.get("group", "") or data.get("group", "")

        match = re.search(r"(rabbitmq_queue[:=][\w\-\._]+)", str(group_mq))
        if not match:
            match = re.search(
                r"(rabbitmq_queue[:=][\w\-\._]+)",
                str(data.get("tags", ""))
            )

        queue_name = match.group(1) if match else "rabbitmq_queue:tracking_pull_queue_co"

        message = (
            f"🟣 ALERTA RABBITMQ - TRACKING PULL CO\n"
            f"🖥️ Host: {host}\n"
            f"📉 Estado: {status_msg}"
        )

        message_wrapped = "\n".join(textwrap.wrap(message, width=60))

        # 📤 Canales
        threading.Thread(
            target=send_telegram_message,
            args=(message_wrapped,),
            daemon=True
        ).start()

        threading.Thread(
            target=send_google_chat_message,
            args=(message_wrapped,),
            daemon=True
        ).start()

        # ⚑ marcar alerta como manejada
        alert_triggered = True

    # 🟣 Bloqueos DB
    if "ALERTDB" in tags:
        border_color = "purple"
        gif_file = "./gif/alertdb.gif"
        sound_file = "./sound/alertdb.mp3"
        tipo_alerta = "Bloqueos por sesiones DB"
        event = data.get("event", {})
        group_db = event.get("group", "") or data.get("group", "")
        title_db = event.get("title", "") or data.get("title", "")

        hostname = "Desconocido"
        match = re.search(r"([\w-]+\.cluster[\w\.-]+\.amazonaws\.com)", group_db or title_db)
        if not match:
            match = re.search(r"([\w\.-]+\.rds\.amazonaws\.com)", group_db or title_db)
        
        if match:
            hostname = match.group(1)

        country_map = {
            "colombia": "🇨🇴 Colombia", "mexico": "🇲🇽 México", "chile": "🇨🇱 Chile",
            "ecuador": "🇪🇨 Ecuador", "panama": "🇵🇦 Panamá", "paraguay": "🇵🇾 Paraguay",
            "peru": "🇵🇪 Perú",
        }
        pais_detectado = next((v for k, v in country_map.items() if k in hostname.lower()), "País No identificado")

        message = (
            f"🟣 ALERTA BLOQUEOS DB\n"
            f"🌎 {pais_detectado}\n"
            f"🖥️ Host: {hostname}\n"
            f"💾 Tipo: {tipo_alerta}"
        )
        
        message_wrapped = "\n".join(textwrap.wrap(message, width=60))
        threading.Thread(target=send_telegram_message, args=(message_wrapped,), daemon=True).start()
        threading.Thread(target=send_google_chat_message,args=(message_wrapped,),daemon=True).start()

        alert_triggered = True

    # 🔴 Alerta de alto uso de CPU en Base de Datos
    if "CPUDB" in tags:
        border_color = "#FF4500"
        gif_file = "./gif/alertcpudb.gif"
        sound_file = "./sound/alertcpudb.mp3"

        status_msg = data.get("status", "Sin información adicional")
        title = data.get("title", "")
        group = data.get("group", "")

        # ---------------------------------------
        # 🔍 EXTRAER hostname y nombre
        # ---------------------------------------
        hostname = "Desconocido"
        dbname = "Desconocido"

        m1 = re.search(r"hostname:([\w\.-]+)", group)
        if m1:
            hostname = m1.group(1)

        m2 = re.search(r"name:([\w\.-]+)", group)
        if m2:
            dbname = m2.group(1)

        if hostname == "Desconocido":
            m3 = re.search(r"([\w-]+\.cluster[\w\.-]+\.amazonaws\.com)", group or title)
            if m3:
                hostname = m3.group(1)

        if hostname == "Desconocido":
            m4 = re.search(r"([\w\.-]+\.rds\.amazonaws\.com)", group or title)
            if m4:
                hostname = m4.group(1)

        # ---------------------------------------
        # 📍 detectar país
        # ---------------------------------------
        country_map = {
            "colombia": "🇨🇴 Colombia", "mexico": "🇲🇽 México", "chile": "🇨🇱 Chile",
            "ecuador": "🇪🇨 Ecuador", "panama": "🇵🇦 Panamá", "paraguay": "🇵🇾 Paraguay",
            "peru": "🇵🇪 Perú", "guatemala": "🇬🇹 Guatemala", "espana": "🇪🇸 España",
        }
        pais_detectado = next((v for k, v in country_map.items() if k in hostname.lower()), "País No identificado")

        message = (
            f"🔴 ALERTA CPU ALTA EN DB\n"
            f"🌎 {pais_detectado}\n"
            f"🖥️ Host: {hostname}\n"
            f"📉 Estado: {status_msg}"
        )

        message_wrapped = "\n".join(textwrap.wrap(message, width=60))

        threading.Thread(target=send_telegram_message, args=(message_wrapped,), daemon=True).start()
        threading.Thread(target=send_google_chat_message,args=(message_wrapped,),daemon=True).start()

        alert_triggered = True

    # 🔵 Alerta de uso alto de conexiones en Base de Datos
    if "CONNDB" in tags:
        border_color = "#1E90FF"
        gif_file = "./gif/alertconndb.gif"
        sound_file = "./sound/alertconndb.mp3"

        status_msg = data.get("status", "Sin información adicional")
        title = data.get("title", "")
        group = data.get("group", "")

        # ---------------------------------------
        #  EXTRAER hostname
        # ---------------------------------------
        hostname = "Desconocido"

        m1 = re.search(r"hostname:([\w\.-]+)", group)
        if m1:
            hostname = m1.group(1)

        if hostname == "Desconocido":
            m2 = re.search(r"([\w-]+\.cluster[\w\.-]+\.amazonaws\.com)", group or title)
            if m2:
                hostname = m2.group(1)

        if hostname == "Desconocido":
            m3 = re.search(r"([\w\.-]+\.rds\.amazonaws\.com)", group or title)
            if m3:
                hostname = m3.group(1)

        # ---------------------------------------
        #  detectar país
        # ---------------------------------------
        country_map = {
            "colombia": "🇨🇴 Colombia", "mexico": "🇲🇽 México", "chile": "🇨🇱 Chile",
            "ecuador": "🇪🇨 Ecuador", "panama": "🇵🇦 Panamá", "paraguay": "🇵🇾 Paraguay",
            "peru": "🇵🇪 Perú", "guatemala": "🇬🇹 Guatemala", "espana": "🇪🇸 España",
        }
        pais_detectado = next((v for k, v in country_map.items() if k in hostname.lower()), "País No identificado")

        # ---------------------------------------
        # 📄 MENSAJE
        # ---------------------------------------
        message = (
            f"🔵 ALERTA CONEXIONES ALTAS EN DB\n"
            f"🌎 {pais_detectado}\n"
            f"🖥️ Host: {hostname}  "
            f"📉 Estado: {status_msg}"
        )

        message_wrapped = "\n".join(textwrap.wrap(message, width=60))

        #  Telegram
        threading.Thread(target=send_telegram_message, args=(message_wrapped,), daemon=True).start()
        threading.Thread(target=send_google_chat_message,args=(message_wrapped,),daemon=True).start()

        alert_triggered = True

   # 🔴 Alerta supervisor
   if "SUPERVISOR" in tags:
        border_color = "blue"
        gif_file = "./gif/supervisor.gif"
        sound_file = "./sound/supervisor.mp3"

        status_msg = data.get("status", "Sin información adicional")
        title = data.get("title", "")
        group = data.get("group", "")
        tags_str = data.get("tags", "")

        # ---------------------------------------
        #  EXTRAER info relevante
        # ---------------------------------------
        hostname = "Desconocido"
        supervisord_server = "Desconocido"

        # ✅ Primero buscar en group
        m1 = re.search(r"host:([\w\.-]+)", group)
        m2 = re.search(r"supervisord_server:([\w\.-]+)", group)

        # ✅ Si no aparece → buscar en tags
        if not m1:
            m1 = re.search(r"host:([\w\.-]+)", tags_str)
        if not m2:
            m2 = re.search(r"supervisord_server:([\w\.-]+)", tags_str)

        if m1:
            hostname = m1.group(1)
        if m2:
            supervisord_server = m2.group(1)

        # ---------------------------------------
        #  detectar país por hostname
        # ---------------------------------------
        country_map = {
            "colombia": "🇨🇴 Colombia", "mexico": "🇲🇽 México", "chile": "🇨🇱 Chile",
            "ecuador": "🇪🇨 Ecuador", "panama": "🇵🇦 Panamá", "paraguay": "🇵🇾 Paraguay",
            "peru": "🇵🇪 Perú", "guatemala": "🇬🇹 Guatemala", "espana": "🇪🇸 España",
        }
        pais_detectado = next((v for k, v in country_map.items() if k in hostname.lower()), "País No identificado")

        # ---------------------------------------
        #  Build message
        # ---------------------------------------
        message = (
            "🟠 SUPERVISOR \n"
            f"🌎 {pais_detectado}\n"
            f"🖥️ Host: {hostname}\n"
            f"📦 Supervisor: {supervisord_server}\n"
            f"📉 Estado: {status_msg}"
        )

        message_wrapped = "\n".join(textwrap.wrap(message, width=60))
        threading.Thread(target=send_telegram_message, args=(message_wrapped,), daemon=True).start()
        threading.Thread(target=send_google_chat_message,args=(message_wrapped,),daemon=True).start()

        alert_triggered = True

    # 🟡 ALERTA PHP-FPM
    if "PHPFPM" in tags:
        cfg = ALERT_CONFIG.get("PHPFPM", {})
        border_color = "gold"
        sound_file = cfg.get("sound", DEFAULT_SOUND)
        gif_file = cfg.get("gif", DEFAULT_GIF)

        status_msg = data.get("status", "Sin información")
        message = (
            f"🟡 ALERTA PHP-FPM\n"
            f"🖥️ Host: {host}\n"
            f"📉 Estado: {status_msg}"
        )

        message_wrapped = "\n".join(textwrap.wrap(message, width=60))

        # 📤 Canales
        threading.Thread(
            target=send_telegram_message,
            args=(message_wrapped,),
            daemon=True
        ).start()

        threading.Thread(
            target=send_google_chat_message,
            args=(message_wrapped,),
            daemon=True
        ).start()

        # ⚑ marcar alerta como manejada
        alert_triggered = True

    # 🔴 Resto de alertas críticas (si tienen un tag reconocido)
    if selected_tag is not None and not alert_triggered:
        border_color = "red"
        sound_file = ALERT_CONFIG.get(selected_tag, {}).get("sound", DEFAULT_SOUND)
        gif_file = ALERT_CONFIG.get(selected_tag, {}).get("gif", DEFAULT_GIF)

        message = (
            f"🚨 ALERTA CRÍTICA\n"
            f"🖥️ Host: {host}\n"
            f"📌 Tipo: {selected_tag}"
        )

        alert_triggered = True


    # 📥 Encolar popup + 🔊 sonido
    # (solo una vez, aunque lleguen varias alertas juntas)
    if alert_triggered:
        enqueue_alert(gif_file, 6, message, border_color)

        threading.Thread(
            target=playsound,
            args=(sound_file,),
            daemon=True
        ).start()

    return {"status": "ok", "tags": tags, "host": host}, 200

# -------------------------------
# Inicio
# -------------------------------
if __name__ == "__main__":
    print("🚀 Flask escuchando en http://127.0.0.1:5006")
    app.run(host="0.0.0.0", port=5006, debug=True)
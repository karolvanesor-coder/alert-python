# Datadog Local Alerts (Sound + Animation + Notification)

Este proyecto permite recibir **webhooks de Datadog** en tu computadora local y mostrar alertas:  
- **Sonoras** (archivo `alert.mp3`)  
- **Gráficas con animación de explosión** (`tkinter`)  
- **Notificaciones nativas en macOS** (`osascript`)  

---

##  Requisitos

- Python 3.9+  
- macOS (para las notificaciones nativas)  
- [ngrok](https://ngrok.com/) (para exponer tu servidor local a Datadog)  

Instala las dependencias:  

```bash
pip install -r requirements.txt

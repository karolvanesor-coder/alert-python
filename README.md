Datadog Local Alerts

Visual · Sound · Local Notification

Este proyecto permite recibir alertas de Datadog en un entorno local mediante webhooks, y mostrarlas de forma inmediata, visual y sonora en el equipo del operador.

Está diseñado para escenarios de monitoreo activo, NOC, soporte técnico o demos de observabilidad, donde una alerta crítica no debe pasar desapercibida.

Funcionalidades

Recepción de webhooks desde Datadog

Reproducción de sonido local (alert.mp3)

Popup visual animado (GIF + efectos gráficos)

Ejecución completamente local

Exposición segura del servidor con ngrok

Configuración simple y desacoplada

Arquitectura general

Datadog Monitor
→ Webhook HTTPS
→ ngrok
→ Servidor Flask local (Python)
→ Lógica de alerta
→ Popup visual + sonido

Requisitos

- Python 3.9+
- pip
- ngrok (binario)
- macOS (para notificaciones nativas)


Python 3.9 o superior

Sistema operativo con entorno gráfico

Cuenta activa en Datadog

ngrok instalado

Descarga ngrok desde:
https://ngrok.com/

Instalación
1. Clonar el repositorio
git clone <url-del-repositorio>
cd datadog-local-alerts

2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

(En Windows: venv\Scripts\activate)

3. Instalar dependencias
pip install -r requirements.txt

Ejecución del proyecto
1. Iniciar el servidor local
python app.py


El servidor quedará escuchando en:

http://localhost:5006

2. Exponer el servidor con ngrok

En otra terminal:

ngrok http 5006


ngrok mostrará una URL pública similar a:

https://82b16472ab3b.ngrok-free.app

3. Configurar el webhook en Datadog

En Datadog:

Ir a Integrations → Webhooks

Crear un nuevo webhook

URL:

https://<url-ngrok>/datadog-webhook


Ejemplo:

https://82b16472ab3b.ngrok-free.app/datadog-webhook


Método: POST

Content-Type: application/json

Flujo de funcionamiento

Un monitor de Datadog entra en estado ALERT

Datadog envía un webhook al endpoint configurado

ngrok redirige la petición a tu máquina local

Flask procesa el evento

Se dispara:

Sonido de alerta

Popup visual animado

Mensaje informativo

Personalización

Cambiar el sonido: reemplazar alert.mp3

Cambiar animación: usar otro GIF

Ajustar duración, tamaño o estilos del popup

Adaptar colores según severidad (warning / critical)

Uso recomendado

Monitoreo en tiempo real

Salas de operaciones (NOC)

Demos de observabilidad

Alertas críticas de infraestructura

Entornos donde una alerta debe ser visible y audible

Notas importantes

ngrok gratuito genera URLs temporales (cambian al reiniciar)

El proyecto está pensado para uso local, no productivo

Mantén ngrok y el servidor activos para recibir alertas
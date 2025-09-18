//esta test es para mac
curl -X POST http://127.0.0.1:5005/datadog-webhook \
-H "Content-Type: application/json" \
-d '{"title":"Prueba Explosión","body":"Se activó la alarma con imagen"}'
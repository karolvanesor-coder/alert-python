curl -X POST http://127.0.0.1:5006/datadog-webhook \
-H "Content-Type: application/json" \
-d '{"title":"Prueba Explosión","body":"Se activó la alarma con imagen"}'

//MEMORIA
curl -X POST http://127.0.0.1:5006/datadog-webhook \
-H "Content-Type: application/json" \
-d '{"title":"Prueba MEMORIA","body":"Se activó la alarma MEMORIA","tags":["MEMORIA"]}'

// CPU
curl -X POST http://127.0.0.1:5006/datadog-webhook \
-H "Content-Type: application/json" \
-d '{"title":"Prueba CPU","body":"Se activó la alarma CPU","tags":["CPU"]}'

// DISCO
curl -X POST http://127.0.0.1:5006/datadog-webhook \
-H "Content-Type: application/json" \
-d '{"title":"Prueba DISCO","body":"Se activó la alarma DISCO","tags":["DISCO"]}'

//CON PROCENTAJE WARNING
curl -X POST http://127.0.0.1:5006/datadog-webhook \
-H "Content-Type: application/json" \
-d '{"title":"Prueba DISCO WARNING","body":"Disco al 85%","tags":["DISCO"],"alert_type":"warning"}'

// CORRER EN CONJUNTO LAS 3 EN MAC LA TEST
ython3 tests/test_webhooks.py
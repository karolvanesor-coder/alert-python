import requests
r = requests.post("http://127.0.0.1:5006/datadog-webhook", json={"title":"Prueba","body":"Mensaje de test"})
print(r.status_code, r.text)
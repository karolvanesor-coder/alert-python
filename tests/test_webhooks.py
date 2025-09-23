import requests
import json

BASE_URL = "http://127.0.0.1:5006/datadog-webhook"

# Casos de prueba con tags distintos
test_cases = [
    {
        "title": "Prueba CPU",
        "body": "Se activó la alarma CPU",
        "tags": ["CPU"]
    },
    {
        "title": "Prueba MEMORIA",
        "body": "Se activó la alarma MEMORIA",
        "tags": ["MEMORIA"]
    },
    {
        "title": "DISCO",
        "body": "Se activó la alarma DISCO",
        "tags": ["DISCO"]
    }
]

def run_tests():
    for case in test_cases:
        print(f"\n  Enviando prueba: {case['title']}")
        response = requests.post(
            BASE_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(case)
        )
        print("➡️ Respuesta del servidor:", response.json())

if __name__ == "__main__":
    run_tests()

import requests

try:
    ip = requests.get("https://api.ipify.org?format=json").json().get("ip")
    print(f"Meu IP público atual é: {ip}")
except Exception as e:
    print(f"Erro ao obter IP: {e}")

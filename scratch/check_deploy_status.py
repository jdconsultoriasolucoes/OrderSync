import requests
import json
import time

DEV_TOKEN = "rnd_yYt6JBdSK7IEHnUQ6ANaWdPzB684"
SERVICE_ID = "srv-d1m38ondiees7391tn7g"
DEPLOY_ID = "dep-d9k6pcijnfac739t72ig"

headers = {"Authorization": f"Bearer {DEV_TOKEN}", "Accept": "application/json"}

for i in range(15):
    res = requests.get(f"https://api.render.com/v1/services/{SERVICE_ID}/deploys/{DEPLOY_ID}", headers=headers)
    if res.status_code == 200:
        dep = res.json().get("deploy", {})
        status = dep.get("status")
        print(f"[{i+1}/15] Status do Deploy do Frontend DEV: {status}")
        if status == "live":
            print("🎉 DEPLOY DO FRONTEND CONCLUÍDO COM SUCESSO! STATUS: LIVE")
            break
        elif status in ("build_failed", "update_failed", "canceled"):
            print(f"❌ DEPLOY FALHOU! Status: {status}")
            break
    else:
        print(f"Erro na API: {res.status_code} - {res.text}")
    time.sleep(4)

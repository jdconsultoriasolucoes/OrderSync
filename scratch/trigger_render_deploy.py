import requests
import json
import time

DEV_TOKEN = "rnd_yYt6JBdSK7IEHnUQ6ANaWdPzB684"
headers = {"Authorization": f"Bearer {DEV_TOKEN}", "Accept": "application/json", "Content-Type": "application/json"}

# 1. Find static site service or web service in DEV
res = requests.get("https://api.render.com/v1/services", headers=headers)
services = res.json()

for s_wrap in services:
    s = s_wrap["service"]
    s_id = s["id"]
    s_name = s["name"]
    s_type = s["type"]
    branch = s.get("branch", "")
    print(f"Service: {s_name} (ID: {s_id}, Type: {s_type}, Branch: {branch})")
    
    if branch == "dev" or "front" in s_name.lower() or "dev" in s_name.lower():
        print(f"Triggering deploy for {s_name}...")
        dep_res = requests.post(f"https://api.render.com/v1/services/{s_id}/deploys", headers=headers, json={"clearCache": "clear"})
        print(f"Deploy trigger result: {dep_res.status_code} - {dep_res.text[:200]}")

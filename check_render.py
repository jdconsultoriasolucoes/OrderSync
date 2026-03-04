import requests

def fetch_render_info(env_name, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    print(f"\n={'='*50}")
    print(f"FETCHING RENDER INFO FOR: {env_name.upper()}")
    
    try:
        res = requests.get("https://api.render.com/v1/services", headers=headers, params={"limit": 10})
        if res.status_code != 200:
            print(f"Failed to fetch services for {env_name}: {res.status_code} - {res.text}")
            return
            
        services = res.json()
        if not services:
            print(f"No services found for token {env_name}")
            return
            
        for s in services:
            srv = s["service"]
            srv_id = srv["id"]
            name = srv["name"]
            type_srv = srv["type"]
            branch = srv.get("branch", "N/A")
            print(f"\n--- Service: {name} (ID: {srv_id}, Type: {type_srv}, Branch: {branch}) ---")
            
            env_res = requests.get(f"https://api.render.com/v1/services/{srv_id}/env-vars", headers=headers)
            if env_res.status_code == 200:
                print("  Environment Variables:")
                env_vars = env_res.json()
                for i, ev_wrap in enumerate(env_vars):
                    ev = ev_wrap["envVar"]
                    val = ev.get("value", "")
                    print(f"    {ev['key']}: {val}")
            else:
                print(f"  Error fetching env vars: {env_res.status_code}")
                
            dep_res = requests.get(f"https://api.render.com/v1/services/{srv_id}/deploys", headers=headers, params={"limit": 1})
            if dep_res.status_code == 200:
                deploys = dep_res.json()
                if deploys:
                    dep = deploys[0]["deploy"]
                    print(f"  Latest Deploy: {dep.get('id')} - Commit: {dep.get('commit')} - Status: {dep.get('status')}")
    except Exception as e:
        print(f"Error fetching for {env_name}: {e}")

tokens = {
    "prod": "rnd_OkB6sCYcFSLW1Ql60qeRYxsSJfyQ",
    "dev": "rnd_yYt6JBdSK7IEHnUQ6ANaWdPzB684"
}

for name, tok in tokens.items():
    fetch_render_info(name, tok)


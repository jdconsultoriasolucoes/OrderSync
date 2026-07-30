import requests
import json

tokens = {
    "PROD": "rnd_OkB6sCYcFSLW1Ql60qeRYxsSJfyQ",
    "DEV": "rnd_yYt6JBdSK7IEHnUQ6ANaWdPzB684"
}

for env, token in tokens.items():
    print(f"\n==================== RENDER POSTGRES INFO: {env} ====================")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    # List postgres instances
    res = requests.get("https://api.render.com/v1/postgres", headers=headers)
    if res.status_code == 200:
        dbs = res.json()
        print(f"Total Postgres DBs found: {len(dbs)}")
        for item in dbs:
            pg = item.get("postgres", item)
            pg_id = pg.get("id")
            name = pg.get("name")
            status = pg.get("status")
            version = pg.get("version")
            print(f"\nDB Name: {name} | ID: {pg_id} | Status: {status} | Postgres Version: {version}")
            
            # Fetch details for this DB
            detail_res = requests.get(f"https://api.render.com/v1/postgres/{pg_id}", headers=headers)
            if detail_res.status_code == 200:
                dt = detail_res.json()
                print(json.dumps(dt, indent=2))
            else:
                print(f"Detail error: {detail_res.status_code} - {detail_res.text}")
    else:
        print(f"Error fetching postgres list: {res.status_code} - {res.text}")

import os

match = "https://ordersync-backend-edjq.onrender.com"
replace = "https://ordersync-backend-59d2.onrender.com"
root_dir = r"e:\OrderSync\frontend\public"

print(f"Replacing '{match}' with '{replace}' in {root_dir}...")

count = 0
for root, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith((".js", ".html", ".json", ".css")):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                if match in content:
                    print(f"Modifying: {path}")
                    new_content = content.replace(match, replace)
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    count += 1
            except Exception as e:
                print(f"Error reading/writing {path}: {e}")

print(f"Done. Modified {count} files.")

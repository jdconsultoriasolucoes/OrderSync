# backend/show_reqs.py
with open("requirements.txt", "r") as f:
    print("📦 Conteúdo do requirements.txt:")
    print(f.read())
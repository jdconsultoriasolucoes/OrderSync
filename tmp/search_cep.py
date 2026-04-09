import os

search_dir = "e:/OrderSync/frontend/src"
for root, dirs, files in os.walk(search_dir):
    for dir in ['.git', 'node_modules', '.next', 'dist', 'build']:
        if dir in dirs:
            dirs.remove(dir)
    for file in files:
        if file.endswith(('.js', '.jsx', '.ts', '.tsx', '.py', '.html')):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        if 'viacep' in line.lower() or 'cep' in line.lower() or 'cidade' in line.lower():
                            print(f"{file_path}:{i+1}:{line.strip()[:100]}")
            except Exception as e:
                pass

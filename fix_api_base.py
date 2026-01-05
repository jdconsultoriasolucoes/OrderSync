import os

files_to_fix = [
    r"e:\OrderSync\frontend\public\tabela_preco\tabela_preco.js",
    r"e:\OrderSync\frontend\public\tabela_preco\pedido_cliente.js",
    r"e:\OrderSync\frontend\public\tabela_preco\listar_tabelas.js",
    r"e:\OrderSync\frontend\public\tabela_preco\criacao_tabela_preco.js",
    r"e:\OrderSync\frontend\public\produto\produto.js",
    r"e:\OrderSync\frontend\public\pedido\pedido.js"
]

for path in files_to_fix:
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        modified = False
        new_lines = []
        for line in lines:
            if line.strip().startswith("const API_BASE =") or line.strip().startswith('const API_BASE ='):
                # Check if already commented
                if not line.strip().startswith("//"):
                    print(f"Commenting out API_BASE in {path}")
                    new_lines.append("// " + line)
                    modified = True
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        if modified:
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
    except Exception as e:
        print(f"Error processing {path}: {e}")

print("Done.")

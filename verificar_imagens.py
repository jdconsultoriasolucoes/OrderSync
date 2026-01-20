#!/usr/bin/env python3
"""
Script para verificar quais imagens estão faltando no manual.
"""

import os
import re
from pathlib import Path

def encontrar_imagens_no_markdown(md_file):
    """
    Encontra todas as referências de imagens no arquivo Markdown.
    """
    imagens_encontradas = []
    
    with open(md_file, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Procurar padrão ![texto](caminho/imagem.png)
    padrao = r'!\[.*?\]\((.*?)\)'
    matches = re.findall(padrao, conteudo)
    
    for match in matches:
        if match.startswith('imagens/'):
            imagens_encontradas.append(match)
    
    return imagens_encontradas

def verificar_imagens():
    """
    Verifica quais imagens estão presentes e quais faltam.
    """
    md_file = "MANUAL_USUARIO_ORDERSYNC.md"
    imagens_dir = "imagens"
    
    print("=" * 60)
    print("Verificador de Imagens do Manual")
    print("=" * 60)
    print()
    
    if not os.path.exists(md_file):
        print(f"❌ Arquivo não encontrado: {md_file}")
        return
    
    # Encontrar todas as imagens referenciadas
    print("Analisando manual...")
    imagens_referenciadas = encontrar_imagens_no_markdown(md_file)
    
    print(f"[OK] Encontradas {len(imagens_referenciadas)} referencias de imagens no manual")
    print()
    
    # Verificar quais existem
    imagens_presentes = []
    imagens_faltando = []
    
    for img_path in imagens_referenciadas:
        caminho_completo = os.path.join(os.path.dirname(md_file), img_path)
        if os.path.exists(caminho_completo):
            imagens_presentes.append(img_path)
        else:
            imagens_faltando.append(img_path)
    
    # Mostrar resultados
    print("=" * 60)
    print("RESULTADO DA VERIFICACAO")
    print("=" * 60)
    print()
    
    print(f"[OK] Imagens presentes: {len(imagens_presentes)}/{len(imagens_referenciadas)}")
    if imagens_presentes:
        print("\n   Imagens encontradas:")
        for img in imagens_presentes:
            print(f"   [OK] {img}")
    
    print()
    print(f"[FALTANDO] Imagens faltando: {len(imagens_faltando)}/{len(imagens_referenciadas)}")
    if imagens_faltando:
        print("\n   Imagens que precisam ser capturadas:")
        for i, img in enumerate(imagens_faltando, 1):
            nome_arquivo = os.path.basename(img)
            print(f"   {i}. {nome_arquivo}")
            print(f"      Caminho: {img}")
    
    print()
    print("=" * 60)
    
    if imagens_faltando:
        print()
        print("PROXIMOS PASSOS:")
        print()
        print("1. Abra o arquivo: imagens/README_IMAGENS.md")
        print("2. Siga as instrucoes para capturar cada screenshot")
        print("3. Salve as imagens na pasta 'imagens/' com os nomes exatos listados acima")
        print("4. Execute este script novamente para verificar")
        print("5. Depois, gere o PDF novamente")
        print()
    else:
        print()
        print("[SUCESSO] Todas as imagens estao presentes!")
        print("   Voce pode gerar o PDF com imagens agora.")
        print()
    
    # Criar lista de imagens faltando em arquivo
    if imagens_faltando:
        with open("imagens/IMAGENS_FALTANDO.txt", "w", encoding="utf-8") as f:
            f.write("Lista de Imagens que Precisam ser Capturadas\n")
            f.write("=" * 60 + "\n\n")
            for i, img in enumerate(imagens_faltando, 1):
                nome = os.path.basename(img)
                f.write(f"{i}. {nome}\n")
                f.write(f"   Caminho completo: {img}\n\n")
        print("[INFO] Lista salva em: imagens/IMAGENS_FALTANDO.txt")
        print()

if __name__ == "__main__":
    verificar_imagens()

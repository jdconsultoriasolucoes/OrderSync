# 📸 Sobre as Imagens do Manual

## Situação Atual

✅ **O que está pronto:**
- Manual Markdown completo com referências às imagens
- Script para gerar PDF
- Guia detalhado de quais screenshots capturar (`imagens/README_IMAGENS.md`)
- Script verificador de imagens (`verificar_imagens.py`)

❌ **O que está faltando:**
- As **16 imagens reais** (screenshots) ainda não foram capturadas
- Por isso o PDF foi gerado **sem imagens**

## Por que o PDF não tem imagens?

O arquivo `README_IMAGENS.md` na pasta `imagens/` é apenas um **guia de instruções** sobre quais screenshots você precisa capturar. Ele **não contém as imagens reais**.

As imagens precisam ser:
1. **Capturadas manualmente** usando ferramentas de screenshot
2. **Salvas na pasta `imagens/`** com os nomes exatos especificados
3. **Depois disso**, o PDF será gerado com as imagens incluídas

## Como resolver?

### Opção 1: Capturar as Imagens Agora (Recomendado)

1. **Execute o verificador** para ver quais imagens faltam:
   ```bash
   python verificar_imagens.py
   ```

2. **Abra o guia** de screenshots:
   - Abra o arquivo: `imagens/README_IMAGENS.md`
   - Ele contém instruções detalhadas de cada screenshot

3. **Capture cada screenshot**:
   - Use a ferramenta de captura do Windows (Win + Shift + S)
   - Ou use ferramentas como Snipping Tool, Lightshot, ShareX
   - Salve na pasta `imagens/` com o nome exato (ex: `01-tela-login.png`)

4. **Verifique novamente**:
   ```bash
   python verificar_imagens.py
   ```

5. **Gere o PDF novamente**:
   ```bash
   python gerar_pdf_manual_alternativo.py
   ```

### Opção 2: Gerar PDF Sem Imagens (Temporário)

O PDF já foi gerado, mas **sem as imagens**. Ele contém avisos indicando onde as imagens deveriam estar.

Você pode:
- Usar o PDF atual (sem imagens) enquanto captura os screenshots
- Depois gerar novamente quando tiver as imagens

### Opção 3: Usar Placeholders (Temporário)

Se quiser, posso criar imagens placeholder (quadrados cinzas com texto) para você ver como ficaria o PDF com imagens. Mas o ideal é usar screenshots reais.

## Lista de Imagens Necessárias

Execute este comando para ver a lista completa:

```bash
python verificar_imagens.py
```

Ou abra o arquivo gerado: `imagens/IMAGENS_FALTANDO.txt`

**Resumo:** São 16 imagens no total:
1. Tela de login
2. Recuperação de senha
3. Reset de senha
4. Menu principal
5. Lista de pedidos
6. Detalhes do pedido
7. Criar tabela (dados básicos)
8. Buscar produtos
9. Gerar link
10. Link gerado
11. Pedido do cliente (visualização pública)
12. Cadastro de produto
13. Cadastro de cliente
14. Cadastro de usuário
15. Configuração SMTP
16. Configuração de mensagens

## Dicas para Capturar Screenshots

1. **Use dados fictícios** - Nunca capture dados reais de clientes
2. **Resolução alta** - Capture em 1920x1080 ou superior
3. **Nomes exatos** - Use exatamente os nomes listados (ex: `01-tela-login.png`)
4. **Formato PNG** - Salve como PNG para melhor qualidade
5. **Limpe a tela** - Feche abas e janelas desnecessárias antes de capturar

## Verificação Rápida

Para verificar rapidamente quais imagens você já tem:

```bash
dir imagens\*.png
```

Ou abra a pasta `imagens/` no Windows Explorer e veja quais arquivos PNG existem.

## Próximos Passos

1. ✅ Execute `python verificar_imagens.py` (já feito)
2. 📸 Capture os 16 screenshots seguindo o guia
3. ✅ Execute `python verificar_imagens.py` novamente para confirmar
4. 📄 Execute `python gerar_pdf_manual_alternativo.py` para gerar PDF com imagens

---

**Dúvidas?** Consulte `imagens/README_IMAGENS.md` para instruções detalhadas de cada screenshot.

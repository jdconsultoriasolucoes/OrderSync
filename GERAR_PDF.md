# Como Gerar PDF do Manual

Este guia explica como converter o manual Markdown para PDF, incluindo as imagens.

## 📋 Pré-requisitos

### Opção 1: Usando ReportLab (Recomendado para Windows)

1. **Instalar Python** (se ainda não tiver):
   - Baixe em: https://www.python.org/downloads/
   - Marque a opção "Add Python to PATH" durante a instalação

2. **Instalar bibliotecas**:
   ```bash
   pip install reportlab markdown
   ```

### Opção 2: Usando WeasyPrint (Alternativa)

1. **Instalar Python** (se ainda não tiver)

2. **Instalar GTK+ para Windows**:
   - Baixe em: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
   - Execute o instalador

3. **Instalar bibliotecas**:
   ```bash
   pip install weasyprint markdown
   ```

---

## 🚀 Como Gerar o PDF

### Método 1: Script Automático (Recomendado)

1. **Abra o terminal/PowerShell** na pasta do projeto:
   ```bash
   cd E:\OrderSync
   ```

2. **Execute o script**:
   ```bash
   # Opção A: Usando ReportLab (mais compatível)
   python gerar_pdf_manual_alternativo.py
   
   # Opção B: Usando WeasyPrint (se instalou GTK+)
   python gerar_pdf_manual.py
   ```

3. **Aguarde a conclusão** - O PDF será gerado como `MANUAL_USUARIO_ORDERSYNC.pdf`

### Método 2: Usando Pandoc (Alternativa Simples)

Se você tem o Pandoc instalado:

```bash
pandoc MANUAL_USUARIO_ORDERSYNC.md -o MANUAL_USUARIO_ORDERSYNC.pdf --pdf-engine=wkhtmltopdf
```

**Instalar Pandoc:**
- Windows: https://pandoc.org/installing.html
- Ou via Chocolatey: `choco install pandoc`

### Método 3: Online (Sem Instalação)

1. **Converter Markdown para HTML primeiro:**
   - Use: https://dillinger.io/ ou https://stackedit.io/
   - Cole o conteúdo do manual
   - Exporte como HTML

2. **Converter HTML para PDF:**
   - Abra o HTML no navegador
   - Use Ctrl+P (Imprimir)
   - Salvar como PDF

---

## 📸 Sobre as Imagens

**Importante:** As imagens precisam estar na pasta `imagens/` antes de gerar o PDF.

- Se as imagens **não existirem**, o PDF será gerado sem elas (com texto indicando que a imagem não foi encontrada)
- Se as imagens **existirem**, elas serão incluídas automaticamente no PDF

**Para incluir imagens:**
1. Capture os screenshots seguindo o guia em `imagens/README_IMAGENS.md`
2. Salve as imagens na pasta `imagens/` com os nomes corretos
3. Execute o script novamente

---

## 🔧 Solução de Problemas

### Erro: "pip não é reconhecido"
- Certifique-se de que Python está instalado e no PATH
- Tente usar: `python -m pip install reportlab markdown`

### Erro: "módulo não encontrado"
- Instale as dependências: `pip install reportlab markdown`

### Erro: "GTK+ não encontrado" (WeasyPrint)
- Use o script alternativo com ReportLab: `gerar_pdf_manual_alternativo.py`
- Ou instale GTK+ (veja pré-requisitos)

### PDF gerado sem imagens
- Verifique se as imagens estão na pasta `imagens/`
- Verifique se os nomes dos arquivos estão corretos
- Veja `imagens/README_IMAGENS.md` para lista completa

### PDF com formatação estranha
- O script tenta manter a formatação, mas pode haver diferenças
- Para melhor resultado, use WeasyPrint (se possível)
- Ou ajuste os estilos no script Python

---

## 📝 Personalização

Você pode personalizar o PDF editando os scripts:

- **Cores e fontes:** Edite as variáveis de estilo no script
- **Tamanho da página:** Altere `pagesize=A4` para Letter, etc.
- **Margens:** Ajuste `rightMargin`, `leftMargin`, etc.

---

## ✅ Checklist

Antes de gerar o PDF:

- [ ] Python instalado
- [ ] Bibliotecas instaladas (`pip install reportlab markdown`)
- [ ] Arquivo `MANUAL_USUARIO_ORDERSYNC.md` existe
- [ ] (Opcional) Imagens na pasta `imagens/`
- [ ] Script de geração no mesmo diretório

---

## 📄 Resultado

Após executar o script com sucesso, você terá:

- `MANUAL_USUARIO_ORDERSYNC.pdf` - Manual completo em PDF
- Pronto para impressão ou distribuição digital

---

**Dúvidas?** Consulte a documentação das bibliotecas:
- ReportLab: https://www.reportlab.com/docs/
- WeasyPrint: https://weasyprint.org/
- Markdown: https://python-markdown.github.io/

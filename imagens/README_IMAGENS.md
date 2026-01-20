# Guia de Screenshots para o Manual do Usuário

Este documento lista todas as imagens necessárias para o manual do usuário do OrderSync.

## Estrutura de Pastas

Todas as imagens devem ser salvas na pasta `imagens/` com os nomes especificados abaixo.

**Formato recomendado:** PNG ou JPG  
**Resolução recomendada:** 1920x1080 ou superior (para qualidade)  
**Tamanho máximo:** 500KB por imagem (otimizar se necessário)

---

## Lista de Imagens Necessárias

### 1. Autenticação e Acesso

#### `01-tela-login.png`
**Descrição:** Tela de login do sistema  
**O que capturar:**
- Campo de e-mail
- Campo de senha
- Botão "Entrar"
- Link "Esqueci minha senha"
- Logo do sistema (se houver)

**Dicas:**
- Use dados fictícios nos campos (ex: "usuario@exemplo.com")
- Certifique-se de que a interface está completa e visível

---

#### `02-recuperacao-senha.png`
**Descrição:** Tela para solicitar recuperação de senha  
**O que capturar:**
- Campo de e-mail
- Botão "Enviar" ou "Solicitar"
- Mensagem explicativa
- Botão "Voltar" para login

---

#### `03-reset-senha.png`
**Descrição:** Tela para definir nova senha após clicar no link do e-mail  
**O que capturar:**
- Campo "Nova Senha"
- Campo "Confirmar Senha"
- Botão "Redefinir Senha"
- Indicação de força da senha (se houver)

---

### 2. Navegação

#### `04-menu-principal.png`
**Descrição:** Menu lateral (sidebar) do sistema após login  
**O que capturar:**
- Menu completo com todas as opções:
  - Pedidos
  - Tabelas de Preço
  - Produtos
  - Clientes
  - Fornecedores
  - Usuários (se admin)
  - Configurações de E-mail (se admin)
- Item ativo destacado
- Logo/header do sistema

**Dicas:**
- Mostre o menu expandido
- Destaque visualmente o item ativo

---

### 3. Módulo de Pedidos

#### `05-lista-pedidos.png`
**Descrição:** Tela de listagem de pedidos com filtros  
**O que capturar:**
- Tabela com lista de pedidos (colunas: número, data, cliente, valor, status)
- Filtros no topo:
  - Status
  - Cliente
  - Data inicial/final
  - Fornecedor
- Botão "Buscar" ou "Filtrar"
- Paginação na parte inferior
- Botões de ação (Ver, Editar, etc.)

**Dicas:**
- Mostre pelo menos 3-5 pedidos na lista
- Destaque os filtros visíveis

---

#### `06-detalhes-pedido.png`
**Descrição:** Tela de detalhes completos de um pedido  
**O que capturar:**
- Informações do cliente (nome, código, contato)
- Tabela de preço usada
- Lista de produtos com:
  - Código
  - Descrição
  - Quantidade
  - Preço unitário
  - Subtotal
- Valores totais (subtotal, frete, total)
- Status atual
- Datas (criação, confirmação)
- Botões de ação (Alterar Status, Confirmar, Cancelar)

**Dicas:**
- Mostre um pedido completo com vários produtos
- Destaque o status atual

---

### 4. Módulo de Tabelas de Preço

#### `07-criar-tabela-basico.png`
**Descrição:** Tela inicial para criar nova tabela de preço  
**O que capturar:**
- Campos do formulário:
  - Nome da Tabela
  - Fornecedor (select)
  - Código do Cliente
  - Cliente
- Botão "Adicionar Produtos" ou "Buscar Produtos"
- Botões "Salvar" e "Cancelar"

---

#### `08-buscar-produtos.png`
**Descrição:** Tela de busca e seleção de produtos para a tabela  
**O que capturar:**
- Campo de busca
- Filtros (Grupo/Marca, Fornecedor)
- Lista de produtos com:
  - Código
  - Descrição
  - Embalagem
  - Preço
- Botão "Adicionar" em cada produto
- Paginação
- Botão "Voltar" ou "Continuar"

**Dicas:**
- Mostre vários produtos na lista
- Destaque um produto sendo adicionado

---

#### `09-gerar-link.png`
**Descrição:** Tela de geração de link com opções de configuração  
**O que capturar:**
- Checkbox "Incluir frete"
- Campo "Data prevista de entrega" (date picker)
- Botão "Gerar Link"
- Informações sobre validade do link (se houver)

---

#### `10-link-gerado.png`
**Descrição:** Link gerado com opção de copiar  
**O que capturar:**
- Link completo exibido (ex: `https://ordersync.com/p/abc123xyz`)
- Botão "Copiar" ou ícone de copiar
- Data de expiração
- Mensagem de sucesso
- Botão "Fechar" ou "Voltar"

---

#### `11-pedido-cliente.png`
**Descrição:** Como o cliente vê a tabela de preços no link público  
**O que capturar:**
- Visualização pública (sem menu administrativo)
- Lista de produtos com:
  - Descrição
  - Embalagem
  - Preço
  - Campo de quantidade
- Informações de contato
- Botão "Confirmar Pedido"
- Total calculado dinamicamente

**Dicas:**
- Mostre a interface do ponto de vista do cliente
- Destaque os campos de quantidade preenchidos

---

### 5. Módulo de Produtos

#### `12-cadastro-produto.png`
**Descrição:** Formulário de cadastro de novo produto  
**O que capturar:**
- Campos principais:
  - Código
  - Nome/Descrição
  - Status
  - Tipo
  - Fornecedor
  - Marca
  - Família
- Campos de estoque e embalagem
- Campos de preço
- Campos de impostos
- Botões "Salvar" e "Cancelar"

**Dicas:**
- Mostre o formulário completo (pode ser necessário scroll)
- Destaque campos obrigatórios (se houver indicação visual)

---

### 6. Módulo de Clientes

#### `13-cadastro-cliente.png`
**Descrição:** Formulário de cadastro de novo cliente  
**O que capturar:**
- Campos:
  - Código da Empresa
  - Razão Social
  - Nome Fantasia
  - CNPJ/CPF
  - E-mail
  - Telefone
  - Endereço completo
  - Contato
  - Observações
- Botões "Salvar" e "Cancelar"

---

### 7. Módulo de Usuários (Admin)

#### `14-cadastro-usuario.png`
**Descrição:** Formulário de cadastro de novo usuário (apenas administradores)  
**O que capturar:**
- Campos:
  - Nome
  - E-mail
  - Senha
  - Função (select: Admin, Gerente, Vendedor)
  - Checkbox "Ativo"
- Botões "Salvar" e "Cancelar"

---

### 8. Configurações de E-mail (Admin)

#### `15-config-smtp.png`
**Descrição:** Tela de configuração do servidor SMTP  
**O que capturar:**
- Campos:
  - Servidor (Host)
  - Porta
  - Usuário
  - Senha (campo oculto)
  - Checkbox "Usar TLS"
- Botão "Salvar"
- Botão "Testar Conexão"
- Mensagem de teste (se houver)

---

#### `16-config-mensagens.png`
**Descrição:** Tela de configuração de templates de e-mail  
**O que capturar:**
- Campos:
  - Destinatário Interno
  - Assunto Padrão
  - Corpo da Mensagem (editor HTML ou textarea)
  - Checkbox "Enviar para Cliente"
- Botão "Salvar"
- Preview da mensagem (se houver)

---

## Dicas Gerais para Captura de Screenshots

### Preparação
1. **Limpe a tela:** Feche abas e janelas desnecessárias
2. **Use dados fictícios:** Nunca capture dados reais de clientes ou informações sensíveis
3. **Resolução:** Use resolução alta (1920x1080 ou superior)
4. **Navegador:** Use um navegador moderno (Chrome, Firefox, Edge)

### Durante a Captura
1. **Capture a tela completa:** Inclua todos os elementos visíveis
2. **Evite informações sensíveis:** Use dados de exemplo
3. **Destaque elementos importantes:** Use setas ou caixas (se necessário, edite depois)
4. **Consistência:** Mantenha o mesmo estilo visual em todas as imagens

### Pós-Processamento
1. **Redimensione se necessário:** Mantenha proporção, mas otimize tamanho
2. **Adicione anotações:** Use setas ou caixas para destacar elementos (opcional)
3. **Comprima:** Use ferramentas de compressão para reduzir tamanho sem perder qualidade
4. **Nomeie corretamente:** Use exatamente os nomes especificados acima

### Ferramentas Recomendadas
- **Captura:** Snipping Tool (Windows), Screenshot (Mac), Lightshot, ShareX
- **Edição:** Paint, GIMP, Photoshop, Canva
- **Compressão:** TinyPNG, ImageOptim, Squoosh

---

## Checklist de Verificação

Antes de finalizar, verifique:

- [ ] Todas as 16 imagens foram capturadas
- [ ] Nomes dos arquivos estão corretos (exatamente como listado)
- [ ] Imagens estão na pasta `imagens/`
- [ ] Não há informações sensíveis nas imagens
- [ ] Todas as imagens estão legíveis e nítidas
- [ ] Tamanho dos arquivos está otimizado (< 500KB cada)
- [ ] Formato é PNG ou JPG
- [ ] As imagens correspondem às descrições do manual

---

## Notas Importantes

- **Privacidade:** Nunca capture dados reais de clientes, e-mails reais ou informações confidenciais
- **Atualização:** Se a interface do sistema mudar, atualize as imagens correspondentes
- **Acessibilidade:** Certifique-se de que as imagens são claras mesmo para usuários com dificuldades visuais
- **Versões:** Mantenha versões antigas das imagens caso precise fazer rollback

---

**Última atualização:** 2024

# Manual Técnico - OrderSync

**Versão:** 1.0  
**Data:** 2024  
**Público-alvo:** Desenvolvedores, TI, Suporte Técnico, Auditoria

---

## 1. Visão Técnica Geral

### 1.1 Objetivo do Sistema

OrderSync é um ERP web para gestão de pedidos B2B, focado em:
- Criação e gestão de tabelas de preços personalizadas por cliente
- Geração de links públicos para clientes realizarem pedidos
- Gestão completa do ciclo de vida de pedidos (criação, confirmação, cancelamento)
- Integração com sistema de e-mail para notificações
- Gestão de produtos, clientes, fornecedores e usuários

### 1.2 Stack Tecnológica

**Backend:**
- **Framework:** FastAPI 0.110.0+
- **Linguagem:** Python 3.11.9
- **ORM:** SQLAlchemy 2.0.30+
- **Banco de Dados:** PostgreSQL (via Render)
- **Autenticação:** JWT (python-jose) com OAuth2
- **Criptografia:** bcrypt 3.2.2 (passlib)
- **Geração de PDF:** ReportLab 4.0+
- **Parser PDF:** pdfplumber 0.11.6
- **Servidor ASGI:** Uvicorn (standard)

**Frontend:**
- **Build Tool:** Vite 4.5.0
- **Framework:** React 18.2.0
- **HTTP Client:** Axios
- **Roteamento:** React Router DOM
- **Arquitetura:** SPA (Single Page Application) com arquivos estáticos

**Infraestrutura:**
- **Hosting:** Render.com
- **Banco:** PostgreSQL (Render managed)
- **Deploy:** Automático via Git (render.yaml)

### 1.3 Ambientes

**Desenvolvimento:**
- Backend: `http://localhost:8000` (ou porta configurada)
- Frontend: `http://localhost:5500` ou `http://localhost:3000`
- Banco: PostgreSQL local ou Render (via DATABASE_URL)

**Homologação:**
- Backend: `https://ordersync-backend-*.onrender.com`
- Frontend: `https://ordersync-frontend-*.onrender.com` ou `https://ordersync-*.onrender.com`
- Banco: PostgreSQL (Render managed)

**Produção:**
- Backend: `https://ordersync-backend-59d2.onrender.com` (conforme config.json)
- Frontend: `https://ordersync-qwc1.onrender.com` ou `https://ordersync-y7kg.onrender.com`
- Banco: PostgreSQL (Render managed, produção)

**Variáveis de Ambiente Críticas:**
- `DATABASE_URL`: String de conexão PostgreSQL (fornecida pelo Render)
- `SECRET_KEY`: Chave para assinatura JWT (gerar com `openssl rand -hex 32`)
- `ADMIN_PASSWORD`: Senha inicial do usuário admin (padrão: "admin123")
- `ENVIRONMENT`: "development" ou "production" (afeta nível de detalhe em erros)

---

## 2. Arquitetura do Sistema

### 2.1 Diagrama Lógico (Descrição Textual)

```
┌─────────────────┐
│   Frontend      │
│   (React/Vite)  │
│   Static Files  │
└────────┬────────┘
         │ HTTPS/REST
         │ Bearer Token (JWT)
         ▼
┌─────────────────┐
│   Backend       │
│   (FastAPI)     │
│   Port 10000    │
└────────┬────────┘
         │ SQLAlchemy ORM
         │ Connection Pool
         ▼
┌─────────────────┐
│   PostgreSQL    │
│   (Render DB)   │
└─────────────────┘

Fluxo de Autenticação:
1. POST /token → valida credenciais → retorna JWT
2. Requests subsequentes: Header "Authorization: Bearer <token>"
3. Middleware get_current_user valida token e injeta UsuarioModel

Fluxo de Link Público:
1. POST /link_pedido/gerar → cria código único → retorna /p/{code}
2. GET /p/{code} → serve HTML público (sem autenticação)
3. Cliente acessa HTML → JavaScript carrega dados via /link_pedido/resolver
4. Cliente confirma → POST /api/pedidos/confirmar → cria PedidoModel
```

### 2.2 Componentes Principais

**Backend (`backend/`):**
- `main.py`: Entry point, configuração FastAPI, middlewares, CORS, rotas
- `database.py`: Engine SQLAlchemy, SessionLocal, configuração de timezone
- `core/`: Segurança (JWT, bcrypt), dependências (get_current_user, get_db)
- `models/`: Modelos SQLAlchemy (UsuarioModel, PedidoModel, TabelaPreco, etc.)
- `routers/`: Endpoints REST organizados por domínio
- `services/`: Lógica de negócio isolada dos routers
- `schemas/`: Validação Pydantic (entrada/saída)
- `utils/`: Funções auxiliares (cálculos, validações)

**Frontend (`frontend/`):**
- `public/`: Arquivos estáticos HTML/CSS/JS organizados por módulo
- `src/`: Componentes React (se houver)
- `vite.config.js`: Configuração do build
- `package.json`: Dependências Node.js

**Estrutura de Rotas Backend:**
- `/token`: Autenticação (POST para login, forgot-password, reset-password)
- `/api/pedidos`: CRUD de pedidos, listagem, confirmação, mudança de status
- `/tabela_preco`: Criação, edição, listagem de tabelas de preço
- `/link_pedido`: Geração e resolução de links públicos
- `/cliente`: CRUD de clientes
- `/produto`: CRUD de produtos, importação de PDF
- `/usuario`: Gestão de usuários
- `/fornecedor`: Gestão de fornecedores
- `/admin/config_email`: Configuração SMTP e templates de e-mail
- `/fiscal`: Endpoints fiscais
- `/listas`: Listagens auxiliares
- `/p/{code}`: Rota pública para links de pedido

### 2.3 Integrações Externas

**Render PostgreSQL:**
- Conexão via `DATABASE_URL` (string de conexão completa)
- Pool de conexões com `pool_pre_ping=True` (evita "server closed connection")
- Timezone configurado para `America/Sao_Paulo` via event listener

**SMTP (E-mail):**
- Configurável via `/admin/config_email`
- Suporta TLS/SSL
- Teste de conexão disponível em `/admin/config_email/test_smtp`
- Envio automático em eventos de pedido (confirmação, cancelamento)

**Sistema de Arquivos:**
- Frontend servido como arquivos estáticos via FastAPI StaticFiles
- PDFs gerados em memória (ReportLab) e retornados como Response
- Upload de PDFs de lista de preços para importação de produtos

---

## 3. Gestão de Acesso e Segurança

### 3.1 Autenticação

**Mecanismo:** OAuth2 Password Flow com JWT

**Fluxo:**
1. Cliente envia credenciais via `POST /token` (form-data: username=email, password=senha)
2. Backend valida email (case-insensitive) e senha (bcrypt)
3. Verifica se usuário está ativo (`ativo=True`)
4. Gera JWT com payload: `{"sub": email, "role": funcao, "exp": timestamp}`
5. Retorna token no formato: `{"access_token": "...", "token_type": "bearer", "funcao": "...", "nome": "..."}`

**Validação de Token:**
- Middleware `get_current_user` (em `core/deps.py`)
- Decodifica JWT usando `SECRET_KEY` e algoritmo `HS256`
- Extrai email do payload (`sub`)
- Busca usuário no banco
- Injeta `UsuarioModel` na dependência

**Expiração:**
- Token padrão: 30 minutos (`ACCESS_TOKEN_EXPIRE_MINUTES`)
- Token de reset de senha: 15 minutos (`RESET_TOKEN_EXPIRE_MINUTES`)

**Recuperação de Senha:**
1. `POST /token/forgot-password` → gera token específico (`scope: "reset_password"`)
2. Envia e-mail com link contendo token
3. Cliente acessa link → `POST /token/reset-password` com token e nova senha
4. Valida token e atualiza `senha_hash` no banco

### 3.2 Autorização e Perfis

**Perfis de Usuário (`funcao`):**
- `admin`: Acesso total (CRUD de usuários, configurações)
- `gerente`: Acesso amplo (gestão de pedidos, tabelas)
- `vendedor`: Acesso restrito (criação de tabelas, visualização de pedidos)

**Implementação:**
- Perfis armazenados em `UsuarioModel.funcao`
- Validação de perfil feita manualmente nos endpoints (ex: `if current_user.funcao != "admin"`)
- Não há sistema de RBAC automatizado (implementação manual por endpoint)

**Campos de Auditoria:**
- `criado_por`: Email do usuário que criou o registro
- `atualizado_por`: Email do usuário que atualizou
- `criado_em` / `atualizado_em`: Timestamps automáticos

### 3.3 Criptografia

**Senhas:**
- Hash: bcrypt (via passlib)
- Rounds: Padrão do bcrypt (10 rounds)
- Função: `get_password_hash()` / `verify_password()` em `core/security.py`

**JWT:**
- Algoritmo: HS256
- Chave: `SECRET_KEY` (variável de ambiente, mínimo 32 bytes hex)
- Payload: `{"sub": email, "role": funcao, "exp": timestamp}`

**Comunicação:**
- HTTPS obrigatório em produção (Render fornece SSL)
- CORS configurado para origens específicas (regex: `ordersync.*\.onrender\.com`)

### 3.4 Logs e Auditoria

**Logging:**
- Biblioteca: `logging` padrão Python
- Nível: INFO (configurável via `logging.basicConfig`)
- Logger específico: `ordersync.errors` para erros 5xx

**Middleware de Erros:**
- Captura exceções não tratadas
- Gera `error_id` (UUID hex 8 chars)
- Loga traceback completo
- Retorna erro genérico em produção, detalhado em desenvolvimento
- Header `x-error-id` para rastreamento

**Auditoria de Dados:**
- Timestamps automáticos: `created_at`, `updated_at`, `data_criacao`, `data_atualizacao`
- Rastreamento de usuário: `criado_por`, `atualizado_por`
- Histórico de status de pedidos: `tb_pedido_status_eventos` (assumido)

---

## 4. Banco de Dados

### 4.1 Modelo Lógico

**Tabelas Principais:**

1. **t_usuario**
   - `id` (BigInteger, PK)
   - `email` (String, unique, index)
   - `senha_hash` (String)
   - `nome` (String)
   - `funcao` (String: admin/gerente/vendedor)
   - `ativo` (Boolean)
   - `reset_senha_obrigatorio` (Boolean)
   - `data_criacao`, `data_atualizacao` (DateTime)

2. **tb_tabela_preco**
   - `id_linha` (Integer, PK, autoincrement)
   - `id_tabela` (Integer, index) - agrupa linhas da mesma tabela
   - `nome_tabela` (Text)
   - `fornecedor` (Text)
   - `codigo_cliente`, `cliente` (Text)
   - `codigo_produto_supra`, `descricao_produto`, `embalagem` (Text)
   - `peso_liquido` (Numeric 9,3)
   - `valor_produto`, `comissao_aplicada`, `ajuste_pagamento` (Numeric)
   - `markup`, `valor_final_markup`, `valor_s_frete_markup` (Numeric)
   - `valor_frete_aplicado`, `frete_kg` (Numeric)
   - `valor_frete`, `valor_s_frete` (Numeric)
   - `grupo`, `departamento` (Text)
   - `ipi`, `icms_st`, `iva_st` (Numeric)
   - `calcula_st` (Boolean)
   - `ativo` (Boolean)
   - `criado_em`, `editado_em`, `deletado_em` (DateTime)
   - `criacao_usuario`, `alteracao_usuario` (Text)
   - Constraint: `UNIQUE(id_tabela, codigo_produto_supra)`

3. **tb_pedidos**
   - `id_pedido` (BigInteger, PK)
   - `tabela_preco_id` (BigInteger) - FK implícita para tb_tabela_preco
   - `tabela_preco_nome` (String) - snapshot
   - `codigo_cliente`, `cliente` (String)
   - `contato_nome`, `contato_email`, `contato_fone` (String)
   - `total_pedido`, `frete_total`, `peso_total_kg` (Float)
   - `status` (String)
   - `usar_valor_com_frete` (Boolean)
   - `fornecedor` (String)
   - `validade_ate` (DateTime)
   - `validade_dias` (Integer)
   - `observacoes` (Text)
   - `link_url` (String)
   - `link_primeiro_acesso_em` (DateTime)
   - `link_status` (String)
   - `created_at`, `atualizado_em`, `confirmado_em`, `cancelado_em` (DateTime)
   - `cancelado_motivo` (String)

4. **tb_pedido_link**
   - `code` (String 32, PK, index) - código único do link
   - `tabela_id` (Integer) - FK para tb_tabela_preco.id_tabela
   - `com_frete` (Boolean)
   - `data_prevista` (Date)
   - `expires_at` (DateTime timezone)
   - `uses`, `max_uses` (Integer)
   - `created_at` (DateTime timezone)
   - `codigo_cliente` (String 80)
   - `first_access_at`, `last_access_at` (DateTime timezone)
   - `link_url` (String 512)
   - `criado_por` (String)

5. **t_cadastro_produto_v2**
   - `id` (BigInteger, PK)
   - `codigo_supra` (Text, unique)
   - `status_produto` (Text)
   - `nome_produto` (Text)
   - `tipo_giro`, `tipo` (Text)
   - `estoque_disponivel`, `estoque_ideal` (Integer)
   - `unidade`, `unidade_anterior` (Text)
   - `peso`, `peso_bruto` (Numeric 12,3)
   - `embalagem_venda`, `unidade_embalagem` (Text/Integer)
   - `codigo_ean`, `codigo_embalagem`, `ncm` (Text)
   - `fornecedor`, `filhos` (Text/Integer)
   - `familia`, `marca` (Text)
   - `preco`, `preco_anterior`, `preco_tonelada`, `preco_tonelada_anterior` (Numeric 14,4)
   - `validade_tabela`, `validade_tabela_anterior` (Date)
   - `desconto_valor_tonelada` (Numeric 14,4)
   - `data_desconto_inicio`, `data_desconto_fim` (Date)
   - `preco_final` (Numeric 14,4) - calculado por trigger
   - `created_at`, `updated_at` (DateTime timezone)
   - `criado_por`, `atualizado_por` (Text)

6. **t_imposto_v2**
   - `id` (BigInteger, PK)
   - `produto_id` (BigInteger, FK para t_cadastro_produto_v2.id, CASCADE, unique)
   - `ipi`, `icms`, `iva_st`, `cbs`, `ibs` (Numeric)

7. **tb_config_email_smtp**
   - `id` (Integer, PK)
   - `host` (String)
   - `port` (Integer)
   - `usuario` (String)
   - `senha` (String) - armazenada em texto (criptografar em produção)
   - `use_tls` (Boolean)
   - `atualizado_por` (String)

8. **tb_config_email_mensagem**
   - `id` (Integer, PK)
   - `destinatario_interno` (String)
   - `assunto_padrao` (String)
   - `corpo_html` (Text)
   - `enviar_para_cliente` (Boolean)
   - `atualizado_por` (String)

**Views:**
- `v_produto_v2_preco`: View agregada de produtos com preços (assumida)

### 4.2 Relacionamentos

- `tb_pedidos.tabela_preco_id` → `tb_tabela_preco.id_tabela` (FK implícita)
- `tb_pedido_link.tabela_id` → `tb_tabela_preco.id_tabela` (FK implícita)
- `t_imposto_v2.produto_id` → `t_cadastro_produto_v2.id` (FK explícita, CASCADE)

### 4.3 Regras de Integridade

- **Unique Constraints:**
  - `t_usuario.email` (único)
  - `tb_tabela_preco(id_tabela, codigo_produto_supra)` (único por tabela)
  - `t_cadastro_produto_v2.codigo_supra` (único)
  - `t_imposto_v2.produto_id` (1:1 com produto)

- **Foreign Keys:**
  - `t_imposto_v2.produto_id` → CASCADE DELETE
  - Outras FKs são implícitas (validação em aplicação)

- **Validações de Aplicação:**
  - Email válido (validação básica)
  - Senha não vazia
  - Valores numéricos não negativos (quando aplicável)
  - Datas válidas (validação Pydantic)

---

## 5. Descrição Técnica dos Módulos

### 5.1 Módulo de Autenticação (`routers/auth.py`)

**Responsabilidade Técnica:**
- Gerenciar ciclo de vida de tokens JWT
- Validar credenciais e retornar tokens de acesso
- Processar recuperação e reset de senha

**Serviços Envolvidos:**
- `core/security.py`: `verify_password()`, `get_password_hash()`, `create_access_token()`
- `services/email_service.py`: `enviar_email_recuperacao_senha()`

**Fluxo Técnico:**

**Login (`POST /token`):**
1. Recebe `OAuth2PasswordRequestForm` (username=email, password)
2. Busca usuário por email (case-insensitive)
3. Valida senha com `verify_password()`
4. Verifica `ativo=True`
5. Gera JWT com `create_access_token()` (expiração: 30 min)
6. Retorna token + metadados (funcao, nome, reset_senha_obrigatorio)

**Forgot Password (`POST /token/forgot-password`):**
1. Recebe email
2. Busca usuário (se não existe, retorna 200 para não vazar)
3. Gera token específico com `scope: "reset_password"` (expiração: 15 min)
4. Monta URL do frontend com token
5. Envia e-mail via `enviar_email_recuperacao_senha()`
6. Retorna 200 sempre (segurança)

**Reset Password (`POST /token/reset-password`):**
1. Recebe token + nova senha
2. Decodifica JWT e valida `scope == "reset_password"`
3. Busca usuário por email do payload
4. Atualiza `senha_hash` com `get_password_hash()`
5. Commit no banco

**Regras de Negócio:**
- Usuário inativo não pode fazer login
- Token de reset expira em 15 minutos
- Senha deve ser hasheada antes de salvar

**Validações e Exceções:**
- `HTTPException 401`: Credenciais inválidas
- `HTTPException 400`: Token inválido/expirado, usuário inativo
- `HTTPException 404`: Usuário não encontrado (reset)

**Pontos Críticos:**
- `SECRET_KEY` deve ser forte (32+ bytes)
- Token de reset deve ter scope específico
- E-mail de recuperação pode falhar silenciosamente (logar erro)

---

### 5.2 Módulo de Tabelas de Preço (`routers/tabela_preco.py`)

**Responsabilidade Técnica:**
- Criar, editar, listar tabelas de preço personalizadas
- Calcular valores com markup, comissão, frete, impostos
- Filtrar produtos para inclusão em tabelas

**Serviços Envolvidos:**
- `services/tabela_preco.py`: `calcular_valores_dos_produtos()`, `create_tabela()`, `update_tabela()`
- `utils/calc_validade_dia.py`: `dias_restantes()`, `classificar_status()`

**Fluxo Técnico:**

**Criação de Tabela (`POST /tabela_preco`):**
1. Recebe `TabelaSalvar` (nome, fornecedor, cliente, produtos[], parâmetros de cálculo)
2. Valida dados (Pydantic)
3. Calcula valores por produto via `calcular_valores_dos_produtos()`:
   - Aplica comissão (%)
   - Aplica ajuste de pagamento (R$)
   - Calcula markup (%)
   - Calcula frete (R$/kg * peso)
   - Calcula impostos (IPI, ICMS-ST, IVA-ST)
   - Gera valores finais (com/sem frete)
4. Persiste linhas em `tb_tabela_preco` (uma linha por produto)
5. Retorna tabela completa com produtos calculados

**Listagem (`GET /tabela_preco`):**
1. Query SQL com filtros (fornecedor, cliente, ativo)
2. Agrupa por `id_tabela`
3. Retorna lista paginada

**Filtro de Produtos (`GET /tabela_preco/produtos_filtro`):**
1. Query em `v_produto_v2_preco`
2. Filtros: grupo (marca), fornecedor, busca textual (código, nome, grupo, unidade)
3. Paginação (page, page_size)
4. Retorna produtos disponíveis para adicionar à tabela

**Regras de Negócio:**
- Produto único por tabela (constraint UNIQUE)
- Valores calculados: `valor_final = valor_base * (1 + markup/100) + frete`
- Frete calculado por peso: `frete = peso_kg * frete_kg`
- Impostos aplicados sobre valor base
- Tabela pode ser ativada/desativada (`ativo`)

**Validações e Exceções:**
- `HTTPException 400`: Dados inválidos, produto duplicado
- `HTTPException 404`: Tabela não encontrada
- `SQLAlchemyError`: Erro de integridade (produto duplicado)

**Pontos Críticos:**
- Cálculos financeiros devem usar `Decimal` ou `Numeric` (não Float)
- Validação de produtos duplicados antes de inserir
- Performance em tabelas com muitos produtos (considerar batch insert)

---

### 5.3 Módulo de Pedidos (`routers/pedidos.py`)

**Responsabilidade Técnica:**
- CRUD de pedidos
- Listagem paginada com filtros
- Mudança de status com auditoria
- Confirmação de pedido via link público

**Serviços Envolvidos:**
- `services/pedidos.py`: SQLs de listagem, contagem, resumo, itens
- `services/pedido_confirmacao_service.py`: `criar_pedido_confirmado()`
- `services/email_service.py`: `enviar_email_notificacao()`

**Fluxo Técnico:**

**Listagem (`GET /api/pedidos`):**
1. Query SQL complexa (`LISTAGEM_SQL`) com JOINs:
   - `tb_pedidos` + `tb_pedido_link` + `tb_tabela_preco` (agregação)
2. Filtros: status, cliente, data_inicio, data_fim, fornecedor
3. Paginação (page, pageSize)
4. Ordenação: data_pedido DESC
5. Retorna `ListagemResponse` (data[], page, pageSize, total)

**Resumo de Pedido (`GET /api/pedidos/{id_pedido}/resumo`):**
1. Query SQL (`RESUMO_SQL`) busca dados do pedido
2. Query SQL (`ITENS_JSON_SQL`) busca itens (JSON agregado)
3. Monta `PedidoResumo` com itens parseados
4. Retorna objeto completo

**Confirmação (`POST /api/pedidos/confirmar`):**
1. Recebe `ConfirmarPedidoRequest` (tabela_id, contato, itens[])
2. Valida tabela existe e link válido (se aplicável)
3. Calcula totais (peso, frete, valor)
4. Cria `PedidoModel` com status "CONFIRMADO"
5. Cria linhas de itens (assumido: `tb_pedido_itens`)
6. Atualiza `tb_pedido_link` (marca como usado, `first_access_at`)
7. Envia e-mail de notificação (se configurado)
8. Retorna pedido criado

**Mudança de Status (`PUT /api/pedidos/{id_pedido}/status`):**
1. Recebe `StatusChangeBody` (para, motivo, user_id)
2. Valida status destino existe e é válido
3. Atualiza `tb_pedidos.status`
4. Insere evento em `tb_pedido_status_eventos` (auditoria)
5. Se cancelado: preenche `cancelado_em`, `cancelado_motivo`
6. Se confirmado: preenche `confirmado_em`
7. Retorna status atualizado

**Regras de Negócio:**
- Pedido criado via link público inicia com status "ABERTO"
- Confirmação muda status para "CONFIRMADO"
- Cancelamento requer motivo
- Status transitam por estados definidos em `tb_pedido_status` (assumido)

**Validações e Exceções:**
- `HTTPException 404`: Pedido não encontrado
- `HTTPException 400`: Status inválido, dados incompletos
- Validação de itens: quantidade > 0, produto existe

**Pontos Críticos:**
- Transações: confirmação deve ser atômica (pedido + itens + link)
- Performance: listagem com muitos pedidos (índices em `created_at`, `status`)
- E-mail pode falhar (não deve quebrar confirmação)

---

### 5.4 Módulo de Links de Pedido (`routers/link_pedido.py`)

**Responsabilidade Técnica:**
- Gerar códigos únicos para links públicos
- Resolver códigos e retornar dados da tabela
- Servir HTML público para clientes

**Serviços Envolvidos:**
- `services/link_pedido.py`: `gerar_link_code()`, `resolver_code()`
- `utils/calc_validade_dia.py`: `calcular_expires_at_global()`

**Fluxo Técnico:**

**Geração (`POST /link_pedido/gerar`):**
1. Recebe `tabela_id`, `com_frete`, `data_prevista`, `codigo_cliente`
2. Gera código único: `secrets.token_urlsafe(12)[:16]` (16 chars URL-safe)
3. Calcula `expires_at` via `calcular_expires_at_global()` (configuração global)
4. Cria `PedidoLink` no banco
5. Monta URL pública: `{origin}/p/{code}`
6. Atualiza `link_url` e `criado_por`
7. Retorna URL + metadados

**Resolução (`GET /link_pedido/resolver`):**
1. Recebe `code` (query param)
2. Busca `PedidoLink` por código
3. Valida expiração (`expires_at < now`)
4. Atualiza contadores (`uses++`, `last_access_at`, `first_access_at` se primeiro acesso)
5. Retorna dados da tabela + metadados do link

**Servir HTML (`GET /p/{code}`):**
1. Recebe código da URL
2. Valida arquivo `pedido_cliente.html` existe
3. Retorna `FileResponse` com headers:
   - `X-Robots-Tag: noindex, nofollow`
   - `Cache-Control: no-store`
4. HTML carrega JavaScript que chama `/link_pedido/resolver` para obter dados

**Regras de Negócio:**
- Link expira conforme configuração global (dias)
- Link pode ter limite de usos (`max_uses`)
- Primeiro acesso registra `first_access_at`
- Link expirado ainda retorna dados (para visualização)

**Validações e Exceções:**
- `HTTPException 404`: Link não encontrado
- Link expirado retorna `is_expired: true` (não é erro)

**Pontos Críticos:**
- Código deve ser único (colisão improvável com 16 chars)
- Expiração baseada em configuração global (não por tabela)
- HTML público não requer autenticação (segurança via código único)

---

### 5.5 Módulo de Produtos (`routers/produto.py`)

**Responsabilidade Técnica:**
- CRUD de produtos
- Importação de PDF de lista de preços
- Geração de relatórios PDF
- Filtros e busca avançada

**Serviços Envolvidos:**
- `services/produto_pdf.py`: CRUD, `importar_pdf_para_produto()`, `get_product_options()`
- `services/produto_pdf_data.py`: `parse_lista_precos()` (parser PDF)
- `services/produto_relatorio.py`: `gerar_pdf_relatorio_lista()`

**Fluxo Técnico:**

**Listagem (`GET /api/produto`):**
1. Query em `t_cadastro_produto_v2` com JOIN em `t_imposto_v2`
2. Filtros: `q` (busca textual), `status`, `familia`, `vigencia`
3. Paginação (page, pageSize)
4. Retorna `ProdutoV2Out[]`

**Criação (`POST /api/produto`):**
1. Recebe `ProdutoCreatePayload` (produto + imposto opcional)
2. Valida `codigo_supra` único
3. Cria `ProdutoV2` + `ImpostoV2` (se fornecido)
4. Retorna produto criado

**Importação PDF (`POST /api/produto/importar-pdf`):**
1. Recebe `UploadFile` (PDF)
2. Extrai texto via `pdfplumber`
3. Parse com `parse_lista_precos()` (regex/parsing customizado)
4. Para cada produto encontrado:
   - Busca ou cria `ProdutoV2`
   - Atualiza preço, validade, impostos
   - Cria snapshot de preço anterior se mudou
5. Retorna resumo (produtos importados, atualizados, erros)

**Relatório PDF (`GET /api/produto/relatorio-lista`):**
1. Recebe `fornecedor`, `lista` (query params)
2. Gera PDF via `gerar_pdf_relatorio_lista()` (ReportLab)
3. Retorna `Response` com `media_type: application/pdf`

**Regras de Negócio:**
- `codigo_supra` único (constraint)
- Preço anterior é snapshot quando preço muda
- `preco_final` calculado por trigger (considera desconto por tonelada)
- Produto pode ter status: ATIVO, INATIVO, etc.

**Validações e Exceções:**
- `HTTPException 400`: Código duplicado, dados inválidos
- `HTTPException 404`: Produto não encontrado
- Erro de parsing PDF: loga e continua (não quebra importação)

**Pontos Críticos:**
- Parser PDF depende do formato da lista (pode quebrar se formato mudar)
- Importação em lote pode ser lenta (considerar async/background job)
- Relatório PDF pode ser pesado (considerar streaming)

---

### 5.6 Módulo de Clientes (`routers/cliente.py`)

**Responsabilidade Técnica:**
- CRUD de clientes
- Busca e listagem

**Serviços Envolvidos:**
- `services/cliente.py`: `listar_clientes()`, `obter_cliente()`, `criar_cliente()`, `atualizar_cliente()`, `deletar_cliente()`

**Fluxo Técnico:**

**Listagem (`GET /cliente`):**
1. Query em tabela de clientes (assumida: `tb_cliente` ou similar)
2. Retorna `ClienteCompleto[]`

**Busca (`GET /cliente/{codigo_da_empresa}`):**
1. Busca por código único
2. Retorna `ClienteCompleto` ou 404

**Criação (`POST /cliente`):**
1. Recebe `ClienteCompleto`
2. Valida dados (Pydantic)
3. Preenche `criado_por` com `current_user.email`
4. Persiste no banco
5. Retorna cliente criado

**Atualização (`PUT /cliente/{codigo_da_empresa}`):**
1. Recebe `ClienteCompleto`
2. Busca cliente existente
3. Atualiza campos
4. Preenche `atualizado_por` com `current_user.email`
5. Retorna cliente atualizado

**Exclusão (`DELETE /cliente/{codigo_da_empresa}`):**
1. Busca cliente
2. Soft delete ou hard delete (depende da implementação)
3. Retorna sucesso

**Regras de Negócio:**
- Código da empresa único
- Auditoria: `criado_por`, `atualizado_por`

**Validações e Exceções:**
- `HTTPException 404`: Cliente não encontrado
- Validação Pydantic: campos obrigatórios

**Pontos Críticos:**
- Exclusão pode ter impacto em pedidos (verificar FKs)

---

### 5.7 Módulo de Configuração de E-mail (`routers/admin_config_email.py`)

**Responsabilidade Técnica:**
- Configurar SMTP (host, porta, credenciais, TLS)
- Configurar templates de mensagem (assunto, corpo HTML)
- Testar conexão SMTP

**Serviços Envolvidos:**
- `services/email_service.py`: `_abrir_conexao()`, `enviar_email_notificacao()`

**Fluxo Técnico:**

**Configurar SMTP (`PUT /admin/config_email/smtp`):**
1. Recebe `ConfigSMTPUpdate` (host, port, usuario, senha, use_tls)
2. Valida dados
3. Atualiza ou cria `ConfigEmailSMTP` (id=1, singleton)
4. Preenche `atualizado_por`
5. Retorna configuração

**Configurar Mensagem (`PUT /admin/config_email/mensagem`):**
1. Recebe `ConfigEmailMensagemBase` (destinatario_interno, assunto_padrao, corpo_html, enviar_para_cliente)
2. Atualiza ou cria `ConfigEmailMensagem` (id=1, singleton)
3. Retorna configuração

**Testar SMTP (`POST /admin/config_email/test_smtp`):**
1. Busca configuração SMTP
2. Tenta conectar via `smtplib.SMTP` (TLS se `use_tls=True`)
3. Autentica com credenciais
4. Retorna sucesso/erro

**Regras de Negócio:**
- Configuração é singleton (id=1)
- Senha armazenada em texto (criptografar em produção)
- Template HTML pode ter variáveis: `{{pedido_id}}`, etc.

**Validações e Exceções:**
- `HTTPException 400`: Dados inválidos, conexão SMTP falhou
- Validação de porta (1-65535)

**Pontos Críticos:**
- Senha em texto plano (risco de segurança)
- Teste SMTP pode falhar por firewall/network
- Template HTML deve ser sanitizado (prevenir XSS)

---

## 6. APIs e Integrações

### 6.1 Endpoints Principais

**Autenticação:**
- `POST /token` - Login (retorna JWT)
- `POST /token/forgot-password` - Solicitar reset de senha
- `POST /token/reset-password` - Resetar senha com token

**Pedidos:**
- `GET /api/pedidos` - Listar pedidos (paginação, filtros)
- `GET /api/pedidos/{id_pedido}/resumo` - Detalhes do pedido
- `POST /api/pedidos/confirmar` - Confirmar pedido (público ou autenticado)
- `PUT /api/pedidos/{id_pedido}/status` - Mudar status
- `GET /api/pedidos/status` - Listar status disponíveis

**Tabelas de Preço:**
- `GET /tabela_preco` - Listar tabelas
- `POST /tabela_preco` - Criar tabela
- `PUT /tabela_preco/{id_tabela}` - Atualizar tabela
- `GET /tabela_preco/produtos_filtro` - Filtrar produtos para tabela
- `GET /tabela_preco/meta/validade_global` - Configuração de validade

**Links:**
- `POST /link_pedido/gerar` - Gerar link público (requer auth)
- `GET /link_pedido/resolver?code=...` - Resolver código (público)
- `GET /p/{code}` - Servir HTML público

**Produtos:**
- `GET /api/produto` - Listar produtos
- `POST /api/produto` - Criar produto
- `PUT /api/produto/{id}` - Atualizar produto
- `DELETE /api/produto/{id}` - Deletar produto
- `POST /api/produto/importar-pdf` - Importar PDF
- `GET /api/produto/relatorio-lista` - Relatório PDF
- `GET /api/produto/opcoes` - Opções de filtros

**Clientes:**
- `GET /cliente` - Listar clientes
- `GET /cliente/{codigo}` - Buscar cliente
- `POST /cliente` - Criar cliente
- `PUT /cliente/{codigo}` - Atualizar cliente
- `DELETE /cliente/{codigo}` - Deletar cliente

**Admin:**
- `GET /admin/config_email/smtp` - Obter config SMTP
- `PUT /admin/config_email/smtp` - Atualizar config SMTP
- `GET /admin/config_email/mensagem` - Obter config mensagem
- `PUT /admin/config_email/mensagem` - Atualizar config mensagem
- `POST /admin/config_email/test_smtp` - Testar SMTP

### 6.2 Métodos HTTP

- `GET`: Leitura (listagem, busca, resumo)
- `POST`: Criação (pedidos, produtos, links)
- `PUT`: Atualização completa (substitui recurso)
- `DELETE`: Exclusão

**Nota:** Não há `PATCH` (usar `PUT` para atualizações parciais).

### 6.3 Parâmetros

**Query Parameters Comuns:**
- `page`: Número da página (default: 1)
- `pageSize` / `page_size`: Itens por página (default: 25, max: 1000)
- `q`: Busca textual
- `status`: Filtro de status
- `fornecedor`: Filtro de fornecedor
- `cliente`: Filtro de cliente
- `data_inicio`, `data_fim`: Filtro de datas (ISO 8601)

**Path Parameters:**
- `{id_pedido}`: ID do pedido (BigInteger)
- `{id_tabela}`: ID da tabela (Integer)
- `{codigo}`: Código do cliente/produto (String)
- `{code}`: Código do link (String 16 chars)

### 6.4 Payloads de Entrada e Saída

**Exemplo: Login (`POST /token`):**
```json
// Entrada (form-data):
username: "admin@ordersync.com"
password: "senha123"

// Saída:
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "funcao": "admin",
  "nome": "Admin",
  "reset_senha_obrigatorio": false
}
```

**Exemplo: Criar Tabela (`POST /tabela_preco`):**
```json
// Entrada:
{
  "nome_tabela": "Tabela Cliente X",
  "fornecedor": "Fornecedor Y",
  "codigo_cliente": "CLI001",
  "cliente": "Cliente X",
  "produtos": [
    {
      "codigo_produto_supra": "PROD001",
      "descricao_produto": "Produto A",
      "embalagem": "SACO",
      "peso_liquido": 25.0,
      "valor_produto": 100.00
    }
  ],
  "parametros": {
    "comissao_percentual": 5.0,
    "ajuste_pagamento": 0.0,
    "markup_percentual": 10.0,
    "frete_kg": 0.50
  }
}

// Saída: TabelaPrecoCompleta (com valores calculados)
```

**Exemplo: Listar Pedidos (`GET /api/pedidos`):**
```json
// Saída:
{
  "data": [
    {
      "numero_pedido": 123,
      "data_pedido": "2024-01-15T10:30:00",
      "cliente_nome": "Cliente X",
      "valor_total": 1500.00,
      "status_codigo": "CONFIRMADO"
    }
  ],
  "page": 1,
  "pageSize": 25,
  "total": 100
}
```

### 6.5 Códigos de Resposta

- `200 OK`: Sucesso
- `201 Created`: Recurso criado (se aplicável)
- `400 Bad Request`: Dados inválidos, validação falhou
- `401 Unauthorized`: Token inválido/expirado, não autenticado
- `403 Forbidden`: Sem permissão (não implementado explicitamente)
- `404 Not Found`: Recurso não encontrado
- `500 Internal Server Error`: Erro do servidor
- `422 Unprocessable Entity`: Erro de validação Pydantic

**Headers Especiais:**
- `x-error-id`: ID do erro (para rastreamento)
- `x-cors-debug`: Debug CORS
- `Authorization: Bearer <token>`: Token JWT (requerido em rotas protegidas)

---

## 7. Processos Assíncronos e Automações

### 7.1 Jobs

**Não há jobs agendados implementados.** Possíveis melhorias:
- Limpeza de links expirados
- Envio de relatórios periódicos
- Sincronização de produtos externos

### 7.2 Rotinas Agendadas

**Não há rotinas agendadas.** Sugestões:
- Backup automático do banco (Render pode fornecer)
- Validação de validade de tabelas
- Notificações de pedidos pendentes

### 7.3 Filas e Eventos

**Não há sistema de filas.** Processamento é síncrono:
- Envio de e-mail é síncrono (pode travar request)
- Geração de PDF é síncrona
- Importação de PDF é síncrona

**Melhorias Sugeridas:**
- Implementar fila (Redis/RabbitMQ) para e-mails
- Background jobs para importação de PDF
- Webhooks para eventos (confirmação de pedido)

---

## 8. Deploy e Versionamento

### 8.1 Pipeline

**Render.com (Automático):**
1. Push para branch `main` (ou branch configurada)
2. Render detecta `render.yaml`
3. Executa `buildCommand`: `pip install -r requirements.txt`
4. Executa `startCommand`: `uvicorn main:app --host 0.0.0.0 --port 10000`
5. Health check automático
6. Deploy ativo

**Arquivo `render.yaml`:**
```yaml
services:
  - type: web
    name: ordersync-backend
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port 10000
    env: python
    plan: free
    autoDeploy: true
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.9
```

### 8.2 Estratégia de Versionamento

**Não há versionamento de API explícito.** Endpoints não têm prefixo `/v1/`.

**Sugestões:**
- Adicionar versionamento: `/api/v1/...`
- Semver para releases (tags Git)
- Changelog mantido manualmente

### 8.3 Rollback

**Render.com:**
- Dashboard permite rollback para deploy anterior
- Histórico de deploys disponível
- Rollback manual via UI ou CLI

**Processo:**
1. Acessar dashboard Render
2. Selecionar serviço
3. Clicar em "Rollback" no deploy desejado
4. Confirmar rollback

---

## 9. Monitoramento e Troubleshooting

### 9.1 Logs

**Backend:**
- Logs padrão Python (`logging`)
- Logger específico: `ordersync.errors` (erros 5xx)
- Render fornece visualização de logs no dashboard
- Nível: INFO (configurável)

**Formato de Log:**
```
ERROR ordersync.errors: 5xx: POST /api/pedidos?page=1 -> 500
ERROR ordersync.errors: EXC a1b2c3d4: POST /api/pedidos?page=1\nTraceback...
```

**Frontend:**
- Logs do navegador (console.log)
- Não há sistema de log centralizado

### 9.2 Métricas

**Render.com fornece:**
- CPU usage
- Memory usage
- Request count
- Response time (p50, p95, p99)

**Não há métricas customizadas implementadas.**

### 9.3 Erros Comuns e Soluções

**Erro: "server closed the connection unexpectedly"**
- **Causa:** Pool de conexões PostgreSQL expirou
- **Solução:** `pool_pre_ping=True` já configurado em `database.py`
- **Prevenção:** Monitorar pool size, ajustar `pool_size` se necessário

**Erro: "Token inválido ou expirado"**
- **Causa:** Token JWT expirado (30 min) ou `SECRET_KEY` mudou
- **Solução:** Fazer login novamente
- **Prevenção:** Implementar refresh token

**Erro: "Link não encontrado" (404)**
- **Causa:** Código inválido ou link deletado
- **Solução:** Verificar código, checar `tb_pedido_link`
- **Prevenção:** Validar código antes de gerar link

**Erro: "Produto duplicado" (IntegrityError)**
- **Causa:** Tentativa de adicionar produto já existente na tabela
- **Solução:** Validar antes de inserir, ou atualizar existente
- **Prevenção:** Query antes de insert

**Erro: CORS bloqueado**
- **Causa:** Origin não permitida
- **Solução:** Verificar `ALLOWED_ORIGINS` ou regex em `main.py`
- **Prevenção:** Adicionar origin ao CORS

**Erro: E-mail não enviado**
- **Causa:** SMTP configurado incorretamente, firewall, credenciais inválidas
- **Solução:** Testar via `/admin/config_email/test_smtp`
- **Prevenção:** Validar config SMTP antes de salvar

---

## 10. Boas Práticas Técnicas

### 10.1 Código

- **Separação de responsabilidades:** Routers apenas roteiam, lógica em services
- **Validação:** Pydantic schemas para entrada/saída
- **Transações:** Usar `db.commit()` explicitamente, `try/except` para rollback
- **Error handling:** Sempre retornar HTTPException com código apropriado
- **Logging:** Logar erros com contexto (método, path, query)

### 10.2 Segurança

- **Senhas:** Sempre usar bcrypt, nunca texto plano
- **JWT:** `SECRET_KEY` forte (32+ bytes), não commitar no Git
- **SQL Injection:** Usar SQLAlchemy ORM ou `text()` com bindparams
- **XSS:** Sanitizar HTML em templates de e-mail
- **CORS:** Restringir origins, não usar `*` com credenciais

### 10.3 Performance

- **Queries:** Usar índices (email, id_tabela, codigo_supra)
- **Paginação:** Sempre paginar listagens grandes
- **Connection Pool:** Configurar `pool_size` adequado
- **Caching:** Considerar Redis para dados frequentes (não implementado)

### 10.4 Manutenibilidade

- **Documentação:** Docstrings em funções complexas
- **Nomes:** Variáveis e funções descritivas
- **Estrutura:** Organizar por domínio (routers/, services/, models/)
- **Testes:** Implementar testes unitários e de integração (não há testes atualmente)

---

**Fim do Manual Técnico**

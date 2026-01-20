# Manual do Usuário - OrderSync

**Versão:** 1.0  
**Data:** 2024  
**Público-alvo:** Usuários finais (vendedores, gerentes, administradores)

---

## 📸 Sobre as Imagens

Este manual contém referências a imagens (screenshots) que ilustram as telas e funcionalidades do sistema. As imagens estão localizadas na pasta `imagens/` e ajudam a visualizar:

- Telas principais do sistema
- Formulários de cadastro
- Processos passo a passo
- Exemplos práticos de uso

**Nota:** Se as imagens não estiverem disponíveis, você ainda pode seguir o manual usando apenas as instruções textuais. As imagens são complementares e facilitam a compreensão.

---

## 1. Apresentação do Sistema

### 1.1 O que é o OrderSync

OrderSync é um sistema web para gerenciar pedidos de clientes de forma simples e organizada. Com ele, você pode:

- Criar tabelas de preços personalizadas para cada cliente
- Enviar links para clientes fazerem pedidos online
- Acompanhar o status de todos os pedidos
- Gerenciar produtos, clientes e fornecedores
- Receber notificações por e-mail quando pedidos são confirmados

### 1.2 Para que serve

O OrderSync foi criado para facilitar o trabalho de vendedores e equipes comerciais que precisam:

- Enviar listas de preços atualizadas para clientes
- Permitir que clientes façam pedidos diretamente pelo sistema
- Controlar o fluxo de pedidos desde a criação até a confirmação
- Organizar informações de produtos e clientes em um só lugar

---

## 2. Primeiro Acesso

### 2.1 Login

![Tela de Login](imagens/01-tela-login.png)
*Figura 1: Tela de login do OrderSync*

**Como fazer login:**

1. Acesse o site do OrderSync no seu navegador
2. Na tela de login, digite seu **e-mail** no campo "E-mail"
3. Digite sua **senha** no campo "Senha"
4. Clique no botão **"Entrar"**

**Dica:** Se você esqueceu sua senha, veja a seção "Recuperação de senha" abaixo.

**Primeiro acesso (usuário admin):**
- E-mail: `admin@ordersync.com`
- Senha: `admin123` (altere após o primeiro login)

### 2.2 Recuperação de Senha

![Tela de Recuperação de Senha](imagens/02-recuperacao-senha.png)
*Figura 2: Tela para solicitar recuperação de senha*

**Se você esqueceu sua senha:**

1. Na tela de login, clique em **"Esqueci minha senha"** ou **"Esqueceu a senha?"**
2. Digite seu e-mail cadastrado no sistema
3. Clique em **"Enviar"**
4. Você receberá um e-mail com um link para redefinir sua senha
5. Clique no link do e-mail (ele expira em 15 minutos)

![Tela de Redefinição de Senha](imagens/03-reset-senha.png)
*Figura 3: Tela para definir nova senha*

6. Digite sua nova senha duas vezes para confirmar
7. Clique em **"Redefinir senha"**
8. Faça login novamente com a nova senha

**Problemas comuns:**
- **Não recebeu o e-mail?** Verifique a caixa de spam ou lixeira
- **Link expirou?** Solicite um novo link de recuperação
- **E-mail não encontrado?** Entre em contato com o administrador do sistema

---

## 3. Visão Geral da Navegação

### 3.1 Menus

![Menu Principal](imagens/04-menu-principal.png)
*Figura 4: Menu lateral (sidebar) do sistema*

Após fazer login, você verá um menu lateral (sidebar) com as seguintes opções:

- **Pedidos:** Ver e gerenciar todos os pedidos
- **Tabelas de Preço:** Criar e editar tabelas de preços
- **Produtos:** Cadastrar e gerenciar produtos
- **Clientes:** Cadastrar e gerenciar clientes
- **Fornecedores:** Gerenciar fornecedores
- **Usuários:** (Apenas administradores) Gerenciar usuários do sistema
- **Configurações de E-mail:** (Apenas administradores) Configurar envio de e-mails

**Como usar o menu:**
- Clique em qualquer item do menu para abrir a página correspondente
- O item ativo fica destacado
- Em telas menores, o menu pode estar oculto - clique no ícone de menu (☰) para abrir

### 3.2 Botões Principais

**Botões comuns em várias telas:**

- **Salvar / Criar:** Salva as informações que você preencheu
- **Cancelar:** Descarta as alterações e volta para a tela anterior
- **Editar:** Permite modificar um registro existente
- **Excluir:** Remove um registro (confirmação pode ser solicitada)
- **Buscar / Filtrar:** Busca registros por nome, código, etc.
- **Gerar Link:** Cria um link para enviar ao cliente
- **Confirmar:** Confirma uma ação (ex: confirmar pedido)
- **Imprimir / PDF:** Gera um arquivo para impressão

**Cores dos botões:**
- **Azul / Primário:** Ações principais (Salvar, Confirmar)
- **Cinza / Secundário:** Ações secundárias (Cancelar, Voltar)
- **Vermelho:** Ações destrutivas (Excluir, Cancelar pedido)

---

## 4. Passo a Passo por Módulo

### 4.1 Módulo de Pedidos

**O que você pode fazer:**
- Ver todos os pedidos criados
- Filtrar pedidos por status, cliente, data
- Ver detalhes completos de um pedido
- Alterar o status de um pedido
- Confirmar ou cancelar pedidos

**Como listar pedidos:**

![Lista de Pedidos](imagens/05-lista-pedidos.png)
*Figura 5: Tela de listagem de pedidos com filtros*

1. Clique em **"Pedidos"** no menu lateral
2. Você verá uma lista com todos os pedidos
3. Use os filtros no topo para buscar:
   - **Status:** Selecione um status (Aberto, Confirmado, Cancelado, etc.)
   - **Cliente:** Digite o nome ou código do cliente
   - **Data inicial / Data final:** Selecione o período
   - **Fornecedor:** Selecione um fornecedor
4. Clique em **"Buscar"** ou **"Filtrar"** para aplicar os filtros
5. Use as setas ou números na parte inferior para navegar entre páginas

**Como ver detalhes de um pedido:**

![Detalhes do Pedido](imagens/06-detalhes-pedido.png)
*Figura 6: Tela de detalhes completos de um pedido*

1. Na lista de pedidos, clique no **número do pedido** ou no botão **"Ver"**
2. Você verá todas as informações:
   - Dados do cliente e contato
   - Tabela de preço usada
   - Lista de produtos com quantidades e valores
   - Valor total do pedido
   - Status atual
   - Data de criação e confirmação (se houver)
3. Para voltar, clique em **"Voltar"** ou use o menu

**Como alterar o status de um pedido:**

1. Abra os detalhes do pedido
2. Clique no botão **"Alterar Status"** ou **"Mudar Status"**
3. Selecione o novo status no menu suspenso
4. Se necessário, digite um motivo (especialmente para cancelamentos)
5. Clique em **"Confirmar"** ou **"Salvar"**

**Status disponíveis:**
- **Aberto:** Pedido criado, aguardando confirmação
- **Confirmado:** Pedido confirmado pelo cliente ou vendedor
- **Cancelado:** Pedido cancelado (motivo obrigatório)
- **Em Processamento:** Pedido sendo processado
- **Enviado:** Pedido enviado para o cliente
- **Finalizado:** Pedido concluído

**Como confirmar um pedido:**

1. Abra os detalhes do pedido
2. Verifique se todas as informações estão corretas
3. Clique no botão **"Confirmar Pedido"**
4. O status mudará para "Confirmado" automaticamente
5. Um e-mail de notificação será enviado (se configurado)

**Como cancelar um pedido:**

1. Abra os detalhes do pedido
2. Clique no botão **"Cancelar Pedido"**
3. Digite o motivo do cancelamento (obrigatório)
4. Clique em **"Confirmar Cancelamento"**
5. O pedido será marcado como cancelado

**Campos explicados:**
- **Número do Pedido:** Identificador único do pedido
- **Cliente:** Nome do cliente que fez o pedido
- **Código do Cliente:** Código interno do cliente
- **Contato:** Nome, e-mail e telefone do contato
- **Tabela de Preço:** Nome da tabela de preços usada
- **Fornecedor:** Fornecedor dos produtos
- **Valor Total:** Soma de todos os produtos + frete
- **Status:** Estado atual do pedido
- **Data de Criação:** Quando o pedido foi criado
- **Data de Confirmação:** Quando foi confirmado (se aplicável)

**Exemplos práticos:**

**Exemplo 1: Buscar pedidos do mês**
1. Acesse "Pedidos"
2. Em "Data inicial", selecione o primeiro dia do mês
3. Em "Data final", selecione o último dia do mês
4. Clique em "Buscar"
5. Você verá apenas os pedidos desse período

**Exemplo 2: Ver pedidos pendentes**
1. Acesse "Pedidos"
2. Em "Status", selecione "Aberto"
3. Clique em "Buscar"
4. Você verá todos os pedidos aguardando confirmação

**Erros comuns e como resolver:**

- **"Nenhum pedido encontrado"**
  - Verifique se os filtros estão corretos
  - Tente remover alguns filtros e buscar novamente

- **"Erro ao carregar pedidos"**
  - Verifique sua conexão com a internet
  - Recarregue a página (F5)
  - Se persistir, entre em contato com o suporte

- **"Não consigo alterar o status"**
  - Verifique se você tem permissão (alguns status podem ter restrições)
  - Certifique-se de que o pedido não está em um estado que bloqueia a mudança

**Boas práticas:**
- Sempre verifique os detalhes antes de confirmar um pedido
- Ao cancelar, sempre informe um motivo claro
- Use os filtros para encontrar pedidos rapidamente
- Mantenha o status atualizado para facilitar o acompanhamento

---

### 4.2 Módulo de Tabelas de Preço

**O que você pode fazer:**
- Criar tabelas de preços personalizadas para clientes
- Adicionar produtos às tabelas
- Calcular valores com comissão, markup e frete
- Editar tabelas existentes
- Gerar links para enviar aos clientes

**Como criar uma nova tabela de preço:**

![Criação de Tabela - Dados Básicos](imagens/07-criar-tabela-basico.png)
*Figura 7: Tela inicial para criar nova tabela de preço*

1. Clique em **"Tabelas de Preço"** no menu
2. Clique no botão **"Nova Tabela"** ou **"Criar Tabela"**
3. Preencha os dados básicos:
   - **Nome da Tabela:** Dê um nome descritivo (ex: "Tabela Cliente X - Janeiro 2024")
   - **Fornecedor:** Selecione o fornecedor
   - **Código do Cliente:** Digite o código do cliente (se houver)
   - **Cliente:** Digite o nome do cliente
4. Clique em **"Adicionar Produtos"** ou **"Buscar Produtos"**

![Busca de Produtos](imagens/08-buscar-produtos.png)
*Figura 8: Tela de busca e seleção de produtos para a tabela*
5. Na busca de produtos, você pode:
   - **Buscar por código:** Digite o código do produto
   - **Buscar por nome:** Digite parte do nome
   - **Filtrar por grupo/marca:** Selecione uma marca
   - **Filtrar por fornecedor:** Selecione um fornecedor
6. Para cada produto encontrado, clique em **"Adicionar"** ou **"Incluir"**
7. Após adicionar produtos, configure os parâmetros de cálculo:
   - **Comissão (%):** Percentual de comissão sobre o valor base
   - **Ajuste de Pagamento (R$):** Valor fixo a adicionar/subtrair
   - **Markup (%):** Percentual de margem sobre o valor
   - **Frete por kg (R$):** Valor do frete por quilograma
8. Clique em **"Calcular Valores"** para ver os valores finais
9. Revise os valores calculados
10. Clique em **"Salvar Tabela"** ou **"Criar"**

**Como editar uma tabela existente:**

1. Na lista de tabelas, encontre a tabela desejada
2. Clique no botão **"Editar"** ou no nome da tabela
3. Você pode:
   - Alterar dados básicos (nome, cliente, etc.)
   - Adicionar novos produtos
   - Remover produtos (clique em "Excluir" ao lado do produto)
   - Alterar parâmetros de cálculo
4. Após fazer alterações, clique em **"Salvar"** ou **"Atualizar"**

**Como gerar um link para o cliente:**

![Geração de Link](imagens/09-gerar-link.png)
*Figura 9: Tela de geração de link com opções de configuração*

1. Abra a tabela de preço desejada
2. Clique no botão **"Gerar Link"** ou **"Criar Link"**
3. Configure as opções:
   - **Incluir frete:** Marque se o cliente deve ver valores com frete
   - **Data prevista de entrega:** Selecione uma data (opcional)
4. Clique em **"Gerar Link"**
5. O sistema criará um link único (ex: `https://ordersync.com/p/abc123xyz`)
6. Copie o link (clique em "Copiar" ou selecione e pressione Ctrl+C)
7. Envie o link para o cliente por e-mail, WhatsApp, etc.

![Link Gerado](imagens/10-link-gerado.png)
*Figura 10: Link gerado com opção de copiar*

**Como listar tabelas:**

1. Acesse "Tabelas de Preço"
2. Você verá uma lista com todas as tabelas
3. Use os filtros para buscar:
   - **Fornecedor:** Selecione um fornecedor
   - **Cliente:** Digite o nome do cliente
   - **Ativo:** Mostrar apenas tabelas ativas ou todas
4. Clique em **"Buscar"** para aplicar filtros

**Campos explicados:**
- **Nome da Tabela:** Identificação da tabela (use nomes descritivos)
- **Fornecedor:** Empresa que fornece os produtos
- **Cliente:** Cliente para quem a tabela é destinada
- **Código do Produto:** Código único do produto
- **Descrição:** Nome completo do produto
- **Embalagem:** Tipo de embalagem (Saco, Caixa, Fardo, etc.)
- **Peso Líquido:** Peso do produto em quilogramas
- **Valor Base:** Preço do produto antes dos cálculos
- **Comissão:** Percentual aplicado sobre o valor base
- **Markup:** Percentual de margem aplicado
- **Frete:** Valor do frete calculado pelo peso
- **Valor Final:** Preço final que o cliente verá (com todos os cálculos)

**Exemplos práticos:**

**Exemplo 1: Criar tabela com 10 produtos**
1. Crie uma nova tabela com dados do cliente
2. Na busca de produtos, filtre por fornecedor
3. Adicione 10 produtos clicando em "Adicionar" para cada um
4. Configure comissão de 5% e markup de 10%
5. Configure frete de R$ 0,50 por kg
6. Clique em "Calcular" e revise os valores
7. Salve a tabela

**Exemplo 2: Enviar link atualizado para cliente**
1. Abra a tabela do cliente
2. Adicione novos produtos ou ajuste valores
3. Salve as alterações
4. Clique em "Gerar Link"
5. Copie o novo link e envie ao cliente

**Erros comuns e como resolver:**

- **"Produto já existe na tabela"**
  - Cada produto só pode aparecer uma vez por tabela
  - Se precisar alterar, edite o produto existente em vez de adicionar novamente

- **"Erro ao calcular valores"**
  - Verifique se todos os campos numéricos estão preenchidos corretamente
  - Certifique-se de que os percentuais são números válidos (ex: 5.0 para 5%)

- **"Link não funciona"**
  - Verifique se o link foi copiado completamente
  - Links expiram após um período (geralmente alguns dias)
  - Gere um novo link se necessário

- **"Não consigo adicionar produtos"**
  - Verifique se os produtos estão cadastrados no sistema
  - Use a busca para encontrar produtos
  - Se o produto não existe, cadastre-o primeiro em "Produtos"

**Boas práticas:**
- Use nomes descritivos para tabelas (inclua cliente e data)
- Revise os valores calculados antes de salvar
- Gere um novo link sempre que atualizar a tabela
- Mantenha tabelas antigas para histórico (não exclua, apenas desative)

---

### 4.3 Módulo de Produtos

**O que você pode fazer:**
- Cadastrar novos produtos
- Editar produtos existentes
- Buscar produtos por código ou nome
- Importar produtos de um arquivo PDF
- Ver informações detalhadas de cada produto

**Como cadastrar um novo produto:**

![Cadastro de Produto](imagens/12-cadastro-produto.png)
*Figura 12: Formulário de cadastro de novo produto*

1. Clique em **"Produtos"** no menu
2. Clique no botão **"Novo Produto"** ou **"Cadastrar Produto"**
3. Preencha os dados básicos:
   - **Código:** Código único do produto (obrigatório)
   - **Nome/Descrição:** Nome completo do produto
   - **Status:** Selecione "Ativo" ou "Inativo"
   - **Tipo:** Selecione o tipo (Insumos, Pet, etc.)
   - **Fornecedor:** Selecione o fornecedor
   - **Marca:** Digite a marca do produto
   - **Família:** Selecione a família/categoria
4. Preencha dados de estoque e embalagem:
   - **Unidade:** Unidade de venda (ex: KG, UN, CX)
   - **Embalagem de Venda:** Tipo de embalagem
   - **Peso Líquido:** Peso em quilogramas
   - **Estoque Disponível:** Quantidade em estoque
5. Preencha dados de preço:
   - **Preço:** Valor do produto
   - **Preço por Tonelada:** Se aplicável
   - **Validade da Tabela:** Data de validade do preço
6. Preencha impostos (se necessário):
   - **IPI:** Percentual de IPI
   - **ICMS:** Percentual de ICMS
   - **IVA-ST:** Percentual de IVA-ST
7. Clique em **"Salvar"** ou **"Criar Produto"**

**Como buscar produtos:**

1. Na tela de produtos, use a barra de busca no topo
2. Digite:
   - Código do produto, ou
   - Parte do nome do produto, ou
   - Marca ou fornecedor
3. Pressione Enter ou clique em **"Buscar"**
4. Use os filtros laterais para refinar:
   - **Status:** Ativo, Inativo, Todos
   - **Família:** Selecione uma categoria
   - **Fornecedor:** Selecione um fornecedor
   - **Vigência:** Produtos com validade próxima

**Como editar um produto:**

1. Na lista de produtos, encontre o produto desejado
2. Clique no botão **"Editar"** ou no nome do produto
3. Altere os campos necessários
4. Clique em **"Salvar"** ou **"Atualizar"**

**Como importar produtos de PDF:**

1. Acesse "Produtos"
2. Clique no botão **"Importar PDF"** ou **"Importar Lista"**
3. Clique em **"Selecionar Arquivo"** ou **"Escolher Arquivo"**
4. Selecione o arquivo PDF da lista de preços
5. Clique em **"Importar"** ou **"Enviar"**
6. Aguarde o processamento (pode levar alguns segundos)
7. O sistema mostrará quantos produtos foram importados ou atualizados
8. Revise os produtos importados na lista

**Campos explicados:**
- **Código:** Identificador único (não pode repetir)
- **Nome:** Descrição completa do produto
- **Status:** Se o produto está ativo ou inativo
- **Tipo:** Categoria geral (Insumos, Pet, etc.)
- **Fornecedor:** Empresa que fornece o produto
- **Marca:** Marca do produto
- **Família:** Categoria específica
- **Unidade:** Como o produto é vendido (KG, UN, CX, etc.)
- **Peso Líquido:** Peso em quilogramas
- **Preço:** Valor atual do produto
- **Validade da Tabela:** Até quando o preço é válido
- **IPI/ICMS/IVA-ST:** Percentuais de impostos

**Exemplos práticos:**

**Exemplo 1: Cadastrar produto simples**
1. Acesse "Produtos" → "Novo Produto"
2. Código: "PROD001"
3. Nome: "Ração Premium para Cães 15kg"
4. Fornecedor: "Fornecedor X"
5. Marca: "Marca Y"
6. Unidade: "SACO"
7. Peso: 15.0 kg
8. Preço: R$ 120,00
9. Salve

**Exemplo 2: Buscar produtos de uma marca**
1. Acesse "Produtos"
2. Na busca, digite o nome da marca
3. Ou use o filtro "Marca" no lado esquerdo
4. Você verá apenas produtos dessa marca

**Erros comuns e como resolver:**

- **"Código já existe"**
  - Cada produto precisa de um código único
  - Use um código diferente ou edite o produto existente

- **"Erro ao importar PDF"**
  - Verifique se o arquivo é um PDF válido
  - O formato do PDF pode não ser compatível
  - Tente cadastrar manualmente se a importação falhar

- **"Produto não encontrado"**
  - Verifique a ortografia da busca
  - Tente buscar por parte do nome
  - Use os filtros para refinar a busca

**Boas práticas:**
- Use códigos padronizados (ex: sempre maiúsculas, formato consistente)
- Mantenha os preços atualizados
- Marque produtos inativos em vez de excluí-los
- Revise produtos importados de PDF antes de usar

---

### 4.4 Módulo de Clientes

**O que você pode fazer:**
- Cadastrar novos clientes
- Editar informações de clientes
- Buscar clientes por nome ou código
- Ver histórico de pedidos do cliente

**Como cadastrar um novo cliente:**

![Cadastro de Cliente](imagens/13-cadastro-cliente.png)
*Figura 13: Formulário de cadastro de novo cliente*

1. Clique em **"Clientes"** no menu
2. Clique no botão **"Novo Cliente"** ou **"Cadastrar Cliente"**
3. Preencha os dados:
   - **Código da Empresa:** Código único do cliente (obrigatório)
   - **Nome/Razão Social:** Nome completo da empresa
   - **Nome Fantasia:** Nome comercial (se diferente)
   - **CNPJ/CPF:** Documento de identificação
   - **E-mail:** E-mail principal
   - **Telefone:** Telefone de contato
   - **Endereço:** Logradouro, número, complemento
   - **Cidade, Estado, CEP:** Dados de localização
   - **Contato:** Nome da pessoa de contato
   - **Observações:** Informações adicionais
4. Clique em **"Salvar"** ou **"Criar Cliente"**

**Como buscar clientes:**

1. Na tela de clientes, use a barra de busca
2. Digite:
   - Código do cliente, ou
   - Nome da empresa, ou
   - CNPJ
3. Pressione Enter ou clique em **"Buscar"**

**Como editar um cliente:**

1. Na lista de clientes, encontre o cliente
2. Clique no botão **"Editar"** ou no nome do cliente
3. Altere os campos necessários
4. Clique em **"Salvar"** ou **"Atualizar"**

**Campos explicados:**
- **Código da Empresa:** Identificador único (use um padrão consistente)
- **Razão Social:** Nome oficial da empresa
- **Nome Fantasia:** Nome usado comercialmente
- **CNPJ/CPF:** Documento para identificação fiscal
- **E-mail:** Para envio de links e notificações
- **Telefone:** Para contato direto
- **Endereço:** Localização completa
- **Contato:** Pessoa responsável pelo pedido

**Exemplos práticos:**

**Exemplo 1: Cadastrar cliente completo**
1. Acesse "Clientes" → "Novo Cliente"
2. Código: "CLI001"
3. Razão Social: "Empresa ABC Ltda"
4. CNPJ: "12.345.678/0001-90"
5. E-mail: "contato@empresaabc.com.br"
6. Telefone: "(11) 99999-9999"
7. Endereço completo
8. Contato: "João Silva"
9. Salve

**Erros comuns e como resolver:**

- **"Código já existe"**
  - Use um código diferente ou edite o cliente existente

- **"E-mail inválido"**
  - Verifique se o e-mail está no formato correto (ex: nome@dominio.com)

**Boas práticas:**
- Mantenha os dados atualizados
- Use códigos padronizados
- Preencha todos os campos importantes para facilitar a comunicação

---

### 4.5 Módulo de Links de Pedido

**O que você pode fazer:**
- Gerar links únicos para enviar aos clientes
- Ver quando o cliente acessou o link
- Acompanhar se o link foi usado para fazer pedido

**Como gerar um link:**

1. Acesse uma **Tabela de Preço** (veja seção 4.2)
2. Clique no botão **"Gerar Link"**
3. Configure:
   - **Incluir frete:** Marque se o cliente deve ver valores com frete
   - **Data prevista:** Selecione uma data de entrega (opcional)
4. Clique em **"Gerar"**
5. Copie o link gerado
6. Envie o link para o cliente

**O que o cliente vê no link:**

![Visualização do Cliente](imagens/11-pedido-cliente.png)
*Figura 11: Como o cliente vê a tabela de preços no link público*

Quando o cliente acessa o link, ele vê:
- Lista de produtos da tabela de preço
- Preços calculados
- Campos para preencher quantidades
- Informações de contato
- Botão para confirmar o pedido

**Como acompanhar o uso do link:**

1. Após gerar o link, você pode ver:
   - **Data de criação:** Quando o link foi criado
   - **Data de expiração:** Quando o link expira
   - **Primeiro acesso:** Quando o cliente acessou pela primeira vez
   - **Último acesso:** Última vez que foi acessado
   - **Status:** Se foi usado para fazer pedido

2. Essas informações aparecem nos detalhes da tabela de preço ou na lista de pedidos

**Campos explicados:**
- **Link:** URL única que você envia ao cliente
- **Expira em:** Data e hora em que o link deixa de funcionar
- **Primeiro acesso:** Quando o cliente abriu o link pela primeira vez
- **Status:** Aberto (não usado), Confirmado (pedido feito), Expirado

**Exemplos práticos:**

**Exemplo 1: Enviar link por e-mail**
1. Gere o link da tabela de preço
2. Copie o link
3. Abra seu cliente de e-mail
4. Cole o link na mensagem
5. Adicione uma mensagem explicando que o cliente pode fazer o pedido pelo link
6. Envie o e-mail

**Exemplo 2: Enviar link por WhatsApp**
1. Gere o link
2. Copie o link
3. Abra o WhatsApp
4. Envie o link para o cliente
5. Explique que ele pode fazer o pedido pelo link

**Erros comuns e como resolver:**

- **"Link expirado"**
  - Links têm validade limitada
  - Gere um novo link se necessário

- **"Cliente não consegue acessar"**
  - Verifique se o link foi copiado completamente
  - Certifique-se de que o cliente tem acesso à internet
  - Tente gerar um novo link

**Boas práticas:**
- Gere um novo link sempre que atualizar a tabela de preços
- Informe ao cliente sobre a data de expiração
- Acompanhe quando o cliente acessa o link
- Envie lembretes se o cliente não acessar em alguns dias

---

### 4.6 Módulo de Usuários (Apenas Administradores)

**O que você pode fazer:**
- Criar novos usuários
- Editar informações de usuários
- Desativar ou ativar usuários
- Redefinir senhas

**Como criar um novo usuário:**

![Cadastro de Usuário](imagens/14-cadastro-usuario.png)
*Figura 14: Formulário de cadastro de novo usuário (apenas administradores)*

1. Clique em **"Usuários"** no menu (apenas administradores veem esta opção)
2. Clique em **"Novo Usuário"**
3. Preencha:
   - **Nome:** Nome completo do usuário
   - **E-mail:** E-mail único (será usado para login)
   - **Senha:** Senha inicial (o usuário pode alterar depois)
   - **Função:** Selecione (Admin, Gerente, Vendedor)
   - **Ativo:** Marque para ativar o usuário
4. Clique em **"Salvar"** ou **"Criar"**

**Como editar um usuário:**

1. Na lista de usuários, encontre o usuário
2. Clique em **"Editar"**
3. Altere os campos necessários
4. Clique em **"Salvar"**

**Como desativar um usuário:**

1. Abra os detalhes do usuário
2. Desmarque a opção **"Ativo"**
3. Salve
4. O usuário não conseguirá mais fazer login

**Funções disponíveis:**
- **Admin:** Acesso total ao sistema
- **Gerente:** Acesso amplo (pode gerenciar pedidos e tabelas)
- **Vendedor:** Acesso básico (pode criar tabelas e ver pedidos)

**Boas práticas:**
- Use e-mails corporativos para cadastrar usuários
- Defina senhas seguras inicialmente
- Desative usuários que saíram da empresa em vez de excluí-los
- Revise periodicamente a lista de usuários ativos

---

### 4.7 Módulo de Configurações de E-mail (Apenas Administradores)

**O que você pode fazer:**
- Configurar servidor de e-mail (SMTP)
- Criar templates de mensagens
- Testar envio de e-mails

**Como configurar o servidor de e-mail:**

![Configuração SMTP](imagens/15-config-smtp.png)
*Figura 15: Tela de configuração do servidor SMTP*

1. Clique em **"Configurações de E-mail"** no menu
2. Vá para a aba **"Configurações SMTP"**
3. Preencha:
   - **Servidor (Host):** Ex: smtp.gmail.com
   - **Porta:** Ex: 587 (TLS) ou 465 (SSL)
   - **Usuário:** Seu e-mail
   - **Senha:** Senha do e-mail ou senha de aplicativo
   - **Usar TLS:** Marque se o servidor usa TLS
4. Clique em **"Salvar"**
5. Clique em **"Testar Conexão"** para verificar se está funcionando

**Como configurar mensagens:**

![Configuração de Mensagens](imagens/16-config-mensagens.png)
*Figura 16: Tela de configuração de templates de e-mail*

1. Vá para a aba **"Mensagens"**
2. Preencha:
   - **Destinatário Interno:** E-mail que receberá notificações
   - **Assunto Padrão:** Assunto dos e-mails (pode usar {{pedido_id}})
   - **Corpo da Mensagem:** Template HTML da mensagem
   - **Enviar para Cliente:** Marque se deseja enviar e-mail ao cliente também
3. Clique em **"Salvar"**

**Como testar o envio:**

1. Após configurar SMTP, clique em **"Testar Conexão"**
2. O sistema tentará conectar ao servidor
3. Se funcionar, você verá "Conexão bem-sucedida"
4. Se falhar, verifique as configurações e tente novamente

**Dicas importantes:**
- Para Gmail, use "Senha de App" em vez da senha normal
- Porta 587 geralmente usa TLS
- Porta 465 geralmente usa SSL
- Teste sempre após configurar

**Erros comuns:**
- **"Não foi possível conectar"**
  - Verifique o servidor e a porta
  - Certifique-se de que o firewall permite a conexão

- **"Autenticação falhou"**
  - Verifique usuário e senha
  - Para Gmail, use senha de aplicativo

---

## 5. Perguntas Frequentes (FAQ)

### 5.1 Login e Acesso

**P: Esqueci minha senha. O que fazer?**
R: Clique em "Esqueci minha senha" na tela de login, digite seu e-mail e siga as instruções do e-mail recebido.

**P: Não consigo fazer login.**
R: Verifique se o e-mail e senha estão corretos. Certifique-se de que não há espaços extras. Se persistir, entre em contato com o administrador.

**P: Meu usuário foi desativado.**
R: Entre em contato com o administrador do sistema para reativar sua conta.

### 5.2 Pedidos

**P: Como cancelar um pedido já confirmado?**
R: Abra os detalhes do pedido, clique em "Alterar Status", selecione "Cancelado" e informe o motivo.

**P: Posso editar um pedido depois de criado?**
R: Depende do status. Pedidos confirmados geralmente não podem ser editados. Entre em contato com o suporte se precisar fazer alterações.

**P: Como ver todos os pedidos de um cliente?**
R: Na lista de pedidos, use o filtro "Cliente" e digite o nome ou código do cliente.

### 5.3 Tabelas de Preço

**P: Posso ter mais de uma tabela para o mesmo cliente?**
R: Sim, você pode criar quantas tabelas precisar. Use nomes descritivos para diferenciá-las.

**P: Como atualizar os preços de uma tabela?**
R: Abra a tabela, clique em "Editar", altere os valores ou parâmetros de cálculo e salve. Gere um novo link se necessário.

**P: O link expirou. O que fazer?**
R: Gere um novo link a partir da tabela de preço atualizada.

### 5.4 Produtos

**P: Como importar muitos produtos de uma vez?**
R: Use a função "Importar PDF" se você tem uma lista em PDF. Caso contrário, cadastre manualmente ou entre em contato com o suporte para importação em lote.

**P: Posso excluir um produto?**
R: É melhor marcar como "Inativo" em vez de excluir, para manter o histórico.

### 5.5 Links

**P: Quantos links posso gerar?**
R: Não há limite. Você pode gerar quantos links precisar.

**P: O cliente não recebeu o link.**
R: Verifique se o e-mail foi enviado corretamente. Você pode copiar o link e enviar manualmente por outro meio (WhatsApp, etc.).

**P: O link não abre no celular do cliente.**
R: Certifique-se de que o cliente tem acesso à internet e que o link foi copiado completamente. Tente gerar um novo link.

### 5.6 Geral

**P: Os dados são salvos automaticamente?**
R: Não. Sempre clique em "Salvar" após fazer alterações.

**P: Posso usar o sistema no celular?**
R: Sim, o sistema é responsivo e funciona em dispositivos móveis. Algumas funcionalidades podem ser mais fáceis no computador.

**P: Como imprimir uma tabela ou pedido?**
R: Use o botão "Imprimir" ou "PDF" quando disponível. Você também pode usar a função de impressão do navegador (Ctrl+P).

**P: Preciso de ajuda adicional.**
R: Entre em contato com o administrador do sistema ou com o suporte técnico.

---

## 6. Boas Práticas de Uso

### 6.1 Organização

- **Use nomes descritivos:** Para tabelas, produtos e clientes, use nomes claros e consistentes
- **Mantenha dados atualizados:** Revise e atualize informações regularmente
- **Organize por datas:** Inclua datas nos nomes de tabelas para facilitar a organização

### 6.2 Segurança

- **Proteja sua senha:** Não compartilhe sua senha com outras pessoas
- **Faça logout:** Sempre faça logout ao usar computadores compartilhados
- **Altere a senha periodicamente:** Mude sua senha regularmente

### 6.3 Eficiência

- **Use filtros:** Aproveite os filtros para encontrar informações rapidamente
- **Salve frequentemente:** Não deixe para salvar no final - salve conforme avança
- **Use atalhos:** Aprenda os atalhos de teclado quando disponíveis

### 6.4 Comunicação

- **Envie links atualizados:** Sempre gere um novo link quando atualizar uma tabela
- **Informe prazos:** Avise os clientes sobre a validade dos links
- **Acompanhe acessos:** Verifique quando os clientes acessam os links

---

**Fim do Manual do Usuário**

**Última atualização:** 2024

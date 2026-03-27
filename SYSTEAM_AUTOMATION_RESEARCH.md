# Pesquisa de Automação: Systeam

Este documento registra as descobertas técnicas realizadas para a automação do preenchimento de pedidos no site da Systeam (https://systeam.com.br/#/login).

## 1. Estrutura e Tecnologia
- **Framework**: Single Page Application (SPA) em **React**.
- **Componentes de UI**: Utiliza Material UI e padrões de componentes assíncronos (ex: `react-select`).
- **Comportamento**: Carregamento dinâmico de dados via rede ao interagir com campos (clientes, estabelecimentos, condições de pagamento).

## 2. Fluxo de Automação Analisado

### Login (2 Etapas)
1.  Inserir E-mail (`178799@alisul.com.br`).
2.  Clicar em "PRÓXIMO".
3.  Inserir Senha (`Alisul#178799`).
4.  Clicar em "ENTRAR".

### Navegação até o Pedido
- Caminho: `Menu Lateral` -> `Pedido Representante` -> Aba `Clientes` -> Botão `Novo Pedido`.

### Preenchimento do Formulário ("Novo Pedido")
- **Campos de Seleção (ComboBox)**: Campos como "Cliente" e "Estabelecimento" exigem:
    1.  Digitar parte do nome/código.
    2.  Aguardar a resposta da rede (spinner/autocomplete).
    3.  Clicar no item desejado na lista suspensa.
- **Campos com Busca (Modais/Lupa)**: Campos como "Condição de Pagamento" e "Lista de Preço" abrem janelas pop-up internas. A automação deve:
    1.  Clicar no ícone da lupa.
    2.  No modal que abrir, preencher o campo de busca.
    3.  Selecionar a linha correta na tabela de resultados.
    4.  Confirmar a seleção.

## 3. Recomendações Técnicas

### Ferramentas
- **Playwright (Python)**: Recomendado pela facilidade de lidar com SPAs e execução em segundo plano (headless).
- **Modo Headless**: A automação pode (e deve) rodar sem interface gráfica no servidor (Render), integrada ao seu `worker.py`.

### Estratégias de Código
- **Esperas Explícitas**: Sempre aguardar o desaparecimento de spinners ("Aguarde...") antes de interagir com o próximo campo.
- **Seletores**: Utilizar seletores baseados em atributos ARIA, classes de formulário (`form-control`) ou placeholders, evitando coordenadas de tela.
- **Mapeamento de Dados**: Criar um mapeamento entre os campos do OrderSync e os seletores do Systeam.

## 4. Próximos Passos Sugeridos
1.  Instalar Playwright no ambiente do OrderSync.
2.  Criar o serviço `backend/services/systeam_service.py`.
3.  Implementar o script base de login e preenchimento de cabeçalho.
4.  Expandir para a inclusão de itens do pedido (produtos).

---
*Pesquisa realizada em 27/03/2026.*

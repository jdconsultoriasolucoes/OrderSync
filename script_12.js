// Função genérica para preencher selects
        function preencherSelect(endpoint, idElemento) {
          const api = window.API_BASE || "http://127.0.0.1:8000";
          fetch(`${api}/listas/${endpoint}`)
            .then((response) => response.json())
            .then((data) => {
              const select = document.getElementById(idElemento);
              if (!select) return;

              data.forEach((item) => {
                const option = document.createElement("option");
                
                if (endpoint === "rota") {
                  // Se o backend retornou "2 - SÃO PAULO", valor é "2" e texto é "2 - SÃO PAULO"
                  const parts = item.split(" - ");
                  option.value = parts[0].trim();
                  option.text = item;
                } else {
                  option.value = item;
                  option.text = item;
                }

                select.appendChild(option);
              });
            })
            .catch((error) => {
              console.error(`Erro ao carregar lista ${endpoint}:`, error);
            });
        }

        function carregarVendedores() {
          const api = window.API_BASE || "http://127.0.0.1:8000";
          const token = window.Auth ? window.Auth.getToken() : localStorage.getItem('ordersync_token');
          const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

          fetch(`${api}/vendedores/`, { headers })
            .then(res => res.json())
            .then(data => {
              const select = document.getElementById("vendedor_ElaboracaoCadastro");
              if (!select) return;
              
              const valAtual = select.value;
              select.innerHTML = '<option value="">Selecione</option>';
              data.forEach(v => {
                const opt = document.createElement("option");
                opt.value = v.nome;
                opt.text = v.nome;
                select.appendChild(opt);
              });
              
              if (valAtual) {
                let exists = Array.from(select.options).some(o => o.value === valAtual);
                if (!exists) {
                  const opt = document.createElement('option');
                  opt.value = valAtual;
                  opt.text = valAtual;
                  select.appendChild(opt);
                }
                select.value = valAtual;
              }
            })
            .catch(err => console.error("Erro ao carregar vendedores:", err));
        }

        // Chamada ao carregar a página
        window.onload = () => {
          preencherSelect("situacao", "situacao");
          preencherSelect("status_cadastro", "status_cadastro");
          preencherSelect("tipos_cliente", "tipo_cliente");
          preencherSelect("atividade_principal", "atividade_principal");
          preencherSelect("rota", "rota_principal_EnderecoEntrega");
          preencherSelect("tipo_venda", "tipo_venda");
          preencherSelect("tipo_compra", "tipo_compra");
          preencherSelect("ramo_de_atividade", "ramo_de_atividade");
          preencherSelect("tipo_venda", "tipo_venda_prazo_ou_vista_ElaboracaoCadastro");
          preencherSelect("tipos_cliente", "classificacao_ElaboracaoCadastro");
          carregarVendedores();
          carregarFornecedoresProdutos();
          carregarOpcoesReferencia();
          carregarOpcoesPlantel();
        };

        function carregarFornecedoresProdutos() {
          const api = window.API_BASE || "http://127.0.0.1:8000";
          const token = window.Auth ? window.Auth.getToken() : localStorage.getItem('ordersync_token');
          const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

          fetch(`${api}/listas/fornecedores_produtos`, { headers })
            .then(res => res.json())
            .then(data => {
              const select = document.getElementById("local_carregamento_ElaboracaoCadastro");
              if (!select) return;
              
              const valAtual = select.value;
              select.innerHTML = '<option value="">Selecione</option>';
              data.forEach(f => {
                const opt = document.createElement("option");
                opt.value = f;
                opt.text = f;
                select.appendChild(opt);
              });
              
              if (valAtual) {
                let exists = Array.from(select.options).some(o => o.value === valAtual);
                if (!exists) {
                   const opt = document.createElement('option');
                   opt.value = valAtual;
                   opt.text = valAtual;
                   select.appendChild(opt);
                }
                select.value = valAtual;
              }
            })
            .catch(err => console.error("Erro ao carregar fornecedores de produtos:", err));
        }
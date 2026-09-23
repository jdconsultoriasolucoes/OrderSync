// --- State Management ---
        // Modes: 'INITIAL', 'SELECTED', 'EDITING'
        function setViewState(mode) {
          window._currentViewState = mode;
          const btnListar = document.getElementById("btn-listar");
          const btnNovo = document.getElementById("btn-novo");
          const btnEditar = document.getElementById("btn-editar");
          const btnExcluir = document.getElementById("btn-excluir");
          const btnVoltar = document.getElementById("btn-voltar");
          const btnSalvar = document.getElementById("btn-salvar");
          const btnCancelar = document.getElementById("btn-cancelar");
          const btnExpExcel = document.getElementById("btn-export-excel");
          const btnExpRecadastro = document.getElementById("btn-export-recadastro");
          const btnExpPdf = document.getElementById("btn-export-pdf");

          // Helper to show/hide
          const show = (el) => el && (el.style.display = "inline-block");
          const hide = (el) => el && (el.style.display = "none");

          // Disable/Enable form
          const disableForm = (disabled) => {
            const formInputs = document.querySelectorAll("#formCliente input, #formCliente select, #formCliente textarea, #formCliente button.btn-add-item, #formCliente button.btn-remover-item");
            formInputs.forEach(input => {
              input.disabled = disabled;
              if (input.tagName === 'BUTTON') {
                input.style.pointerEvents = disabled ? 'none' : 'auto';
                input.style.opacity = disabled ? '0.5' : '1';
              }
            });
          };

          if (mode === 'INITIAL') {
            show(btnListar);
            show(btnNovo);
            hide(btnEditar);
            hide(btnExcluir);
            hide(btnVoltar);
            hide(btnSalvar);
            hide(btnCancelar);
            hide(btnExpExcel);
            hide(btnExpRecadastro);
            hide(btnExpPdf);
            disableForm(true);
            // Clear form logic typically handles resetting ID to ""
          } else if (mode === 'SELECTED') {
            show(btnListar);
            hide(btnNovo);
            show(btnEditar);
            show(btnExcluir);
            show(btnVoltar);
            hide(btnSalvar);
            hide(btnCancelar);
            show(btnExpExcel);
            show(btnExpRecadastro);
            hide(btnExpPdf); 
            disableForm(true);
          } else if (mode === 'EDITING' || mode === 'CREATING') {
            hide(btnListar);
            hide(btnNovo);
            hide(btnEditar);
            hide(btnExcluir);
            // hide(btnVoltar); // Usually hidden during edit
            show(btnSalvar);
            show(btnCancelar);
            hide(btnExpExcel);
            hide(btnExpRecadastro);
            hide(btnExpPdf);
            disableForm(false);
          }
        }

        function novoCliente() {
          limparErros();
          document.getElementById("formCliente").reset();
          document.getElementById("id").value = "";
          document.getElementById("ativo").checked = true;
          setViewState('CREATING');
          inicializarListasVazias();
        }

        function voltarEstadoInicial() {
          limparErros();
          document.getElementById("formCliente").reset();
          document.getElementById("id").value = "";
          setViewState('INITIAL');
          inicializarListasVazias();
        }

        function inicializarListasVazias() {
          renderizarLista('indicacoes', 5, []);
          renderizarLista('grupos_economicos', 3, []);
          renderizarLista('referencias_comerciais', 3, []);
          renderizarLista('referencias_bancarias', 3, []);
          renderizarLista('bens_imoveis', 3, []);
          renderizarLista('bens_moveis', 3, []);
          renderizarLista('veiculos_terceiros', 2, []);
          renderizarLista('planteis_animais', 3, []);
          // Auto-preencher campos de Comissão Dispet dinamicamente via profile
          const DISPET_DEFAULT = window._dispetDefault || "";
          const insumosFld = document.getElementById('insumos_ElaboracaoCadastro');
          const petFld     = document.getElementById('pet_ElaboracaoCadastro');
          if (insumosFld && !insumosFld.value) insumosFld.value = DISPET_DEFAULT;
          if (petFld     && !petFld.value)     petFld.value     = DISPET_DEFAULT;
          const chkPet = document.getElementById("comissao_pet_dispet_flag");
          if (chkPet) chkPet.checked = true;
          const chkInsumos = document.getElementById("comissao_insumos_dispet_flag");
          if (chkInsumos) chkInsumos.checked = true;
        }

        function limparErros() {
          document.querySelectorAll('.field-error').forEach(el => el.classList.remove('field-error'));
          document.querySelectorAll('.error-message').forEach(el => el.remove());
          const globalError = document.getElementById('global-error-container');
          if (globalError) globalError.style.display = 'none';
        }

        function marcarErro(campoId, mensagem) {
          const el = document.getElementById(campoId);
          if (el) {
            el.classList.add('field-error');
            const msg = document.createElement('span');
            msg.className = 'error-message';
            msg.textContent = mensagem;
            el.parentNode.appendChild(msg);
          }
        }

        function validarFormulario() {
          limparErros();
          let valido = true;
          let mensagens = [];

          // 1. Nome do Cliente
          const nome = document.getElementById('nome_cliente');
          if (!nome || !nome.value.trim()) {
            marcarErro('nome_cliente', 'O nome do cliente é obrigatório.');
            valido = false;
            mensagens.push("Preencha o nome do cliente.");
          }

          // 2. CPF ou CNPJ (Regra: exatamente um)
          const cpf = document.getElementById('cpf').value.trim();
          const cnpj = document.getElementById('cnpj').value.trim();
          
          if (!cpf && !cnpj) {
            marcarErro('cpf', 'Preencha o CPF ou o CNPJ.');
            marcarErro('cnpj', 'Preencha o CPF ou o CNPJ.');
            valido = false;
            mensagens.push("É necessário informar o CPF ou o CNPJ.");
          } else if (cpf && cnpj) {
            marcarErro('cpf', 'Preencha apenas um: CPF ou CNPJ.');
            marcarErro('cnpj', 'Preencha apenas um: CPF ou CNPJ.');
            valido = false;
            mensagens.push("Preencha apenas um documento: ou o CPF ou o CNPJ (nunca ambos).");
          }

          if (!valido) {
            const container = document.getElementById('global-error-container');
            const msgEl = document.getElementById('global-error-message');
            if (container && msgEl) {
              msgEl.textContent = mensagens[0]; // Mostra a primeira mensagem no topo
              container.style.display = 'flex';
              container.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
          }

          return valido;
        }


        function salvarCliente() {
          if (!validarFormulario()) return;

          const id = document.getElementById("id").value;
          const cliente = obterDadosFormulario();

          if (id) cliente.cadastrocliente.id = parseInt(id);

          const api = window.API_BASE || "http://127.0.0.1:8000";
          const url = id ? `${api}/cliente/${id}` : `${api}/cliente`;
          const metodo = id ? 'put' : 'post';

          const token = window.Auth ? window.Auth.getToken() : localStorage.getItem('ordersync_token');

          if (!token) {
            alert("Sessão expirada. Faça login novamente.");
            window.Auth.logout();
            return;
          }

          console.log("Saving client with token:", token.substring(0, 10) + "...");

          axios[metodo](url, cliente, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          })
            .then((res) => {
              window.ErrorUtils.showSuccess('Salvo', 'Cliente salvo com sucesso!');
              if (res.data && res.data.cadastrocliente && res.data.cadastrocliente.id) {
                preencherFormularioCliente(res.data);
              } else {
                novoCliente();
              }
            })
            .catch(erro => {
              limparErros();
              if (erro.response && erro.response.status === 401) {
                window.ErrorUtils.showError("Não Autorizado", "Sessão inválida ou expirada. Redirecionando para login.");
                setTimeout(() => { window.Auth.logout(); }, 2000);
              } else {
                window.ErrorUtils.handleApiError(erro);
              }
            });
        }

        function excluirCliente() {
          const id = document.getElementById("id").value;
          if (!id) {
            alert("Nenhum cliente selecionado para excluir.");
            return;
          }

          if (!confirm("Tem certeza que deseja excluir este cliente?")) return;

          const api = window.API_BASE || "http://127.0.0.1:8000";
          const token = window.Auth ? window.Auth.getToken() : localStorage.getItem('ordersync_token');

          if (!token) {
            alert("Sessão expirada. Faça login novamente.");
            return;
          }

          // Fix: Use ID instead of codigo_da_empresa, as backend expects ID in path (despite param name)
          axios.delete(`${api}/cliente/${id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          })

            .then(() => {
              alert("Cliente excluído com sucesso!");
              voltarEstadoInicial();
            })
            .catch(erro => {
              console.error(erro);
              alert("Erro ao excluir cliente.");
            });
        }

        function editarCliente() {
          setViewState('EDITING');
          // Habilita edição se necessário, ou apenas foca no primeiro campo
          document.getElementById("nome_cliente").focus();
        }

        function cancelarEdicao() {
          if (confirm("Deseja cancelar a edição? Os dados não salvos serão perdidos.")) {
            const id = document.getElementById("id").value;
            if (id) {
              // If we were editing an existing client, revert to Selected state
              // Ideally re-fetch or just disable form. For now, disable form.
              setViewState('SELECTED');
              // Optional: Reload data to revert unsaved changes in DOM inputs
              // loadCliente(id); // If we had such function readily available
            } else {
              // If creating new, go back to initial
              voltarEstadoInicial();
            }
          }
        }

        function listarClientes() {
          window.location.href = "listar_clientes.html";
        }

        async function exportarSupra(format) {
          const idInput = document.getElementById("id");
          const id = idInput ? idInput.value : "";
          
          if (!id) {
            alert("Salve o cliente primeiro para poder exportar.");
            return;
          }

          const api = window.API_BASE || "http://127.0.0.1:8000";
          const token = window.Auth ? window.Auth.getToken() : localStorage.getItem('ordersync_token');
          
          try {
            const response = await fetch(`${api}/cliente/${id}/exportar-supra?format=${format}`, {
              headers: {
                'Authorization': `Bearer ${token}`
              }
            });

            if (!response.ok) {
              const errorData = await response.json();
              throw new Error(errorData.detail || "Erro ao gerar exportação.");
            }

            if (format === 'pdf') {
              // Impressão nativa silenciosa (Client-Side)
              const htmlStr = await response.text();
              const iframe = document.createElement('iframe');
              iframe.style.display = 'none';
              document.body.appendChild(iframe);
              
              iframe.contentDocument.open();
              iframe.contentDocument.write(`
                <html>
                  <head>
                    <style>
                      @media print {
                         @page { margin: 0.5cm; size: A4 portrait; }
                         body { 
                             -webkit-print-color-adjust: exact; 
                             print-color-adjust: exact; 
                             margin: 0; 
                             padding: 0; 
                             zoom: 0.65; 
                         }
                         table {
                             max-width: 100% !important;
                         }
                      }
                    </style>
                  </head>
                  <body>
                    ${htmlStr}
                    <script>
                      window.onload = function() {
                          setTimeout(function() {
                              window.print();
                          }, 500);
                      };
                    <\/script>
                  </body>
                </html>
              `);
              iframe.contentDocument.close();

              // Remove o iframe da memória após a ação
              setTimeout(() => {
                  if (document.body.contains(iframe)) {
                      document.body.removeChild(iframe);
                  }
              }, 60000); 

            } else {
              // Download normal de arquivo para Excel
              const blob = await response.blob();
              const url = window.URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              // Extrair nome do arquivo do header Content-Disposition do servidor
              const disposition = response.headers.get('Content-Disposition');
              let filename = `cliente_${id}.xlsx`;
              if (disposition) {
                const match = disposition.match(/filename="?(.+?)"?$/);
                if (match && match[1]) filename = match[1];
              }
              a.download = filename;
              document.body.appendChild(a);
              a.click();
              window.URL.revokeObjectURL(url);
              a.remove();
            }
          } catch (error) {
            console.error("Erro na exportação:", error);
            alert("Erro ao exportar: " + error.message);
          }
        }

        async function exportarRecadastro(format = 'xlsx') {
          const idInput = document.getElementById("id");
          const id = idInput ? idInput.value : "";
          
          if (!id) {
            alert("Salve o cliente primeiro para poder exportar a Ficha Recadastro.");
            return;
          }

          const api = window.API_BASE || "http://127.0.0.1:8000";
          const token = window.Auth ? window.Auth.getToken() : localStorage.getItem('ordersync_token');
          
          try {
            const response = await fetch(`${api}/cliente/${id}/exportar-recadastro?format=${format}`, {
              headers: {
                'Authorization': `Bearer ${token}`
              }
            });

            if (!response.ok) {
              const errorData = await response.json();
              throw new Error(errorData.detail || "Erro ao gerar Ficha Recadastro.");
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            const disposition = response.headers.get('Content-Disposition');
            let filename = `Recadastro_Cliente_${id}.xlsx`;
            if (disposition) {
              const match = disposition.match(/filename="?(.+?)"?$/);
              if (match && match[1]) filename = match[1];
            }
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
          } catch (error) {
            console.error("Erro na exportação do Recadastro:", error);
            alert("Erro ao exportar Ficha Recadastro: " + error.message);
          }
        }

        // Limpar erro visual quando o usuário volta a digitar no campo
        document.addEventListener('input', (e) => {
          if (e.target.classList.contains('field-error')) {
            e.target.classList.remove('field-error');
            const msg = e.target.parentNode.querySelector('.error-message');
            if (msg) msg.remove();
          }
        });

        // On load event: Carrega canais e verifica cliente selecionado vindo da listagem
        document.addEventListener('DOMContentLoaded', () => {
          const api = window.API_BASE || "http://127.0.0.1:8000";
          const token = window.Auth ? window.Auth.getToken() : localStorage.getItem('ordersync_token');

          const carregarTela = () => {
            // 1. Sempre carrega as opções do select de Canal de Venda
            carregarOpcoesCanal().then(() => {
              // 2. Depois verifica se há cliente selecionado para preencher
              const selectedClientId = localStorage.getItem('Ordersync_ClienteSelecionadoIdListar');
              if (selectedClientId) {
                localStorage.removeItem('Ordersync_ClienteSelecionadoIdListar');
                if (token) {
                  axios.get(`${api}/cliente/${selectedClientId}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                  })
                    .then(res => {
                      if (res.data) {
                        if (typeof preencherFormularioCliente === "function") {
                          preencherFormularioCliente(res.data);
                        } else if (typeof window.preencherFormulario === "function") {
                          window.preencherFormulario(res.data);
                        } else {
                          console.warn("Função de preenchimento não encontrada, dados obtidos:", res.data);
                        }
                      }
                    })
                    .catch(err => console.error("Erro ao carregar cliente selecionado:", err));
                }
              } else {
                // Se não há cliente para carregar, inicializa as listas vazias e define a tela como INITIAL
                inicializarListasVazias();
                setViewState('INITIAL');
              }
            });
          };

          if (token) {
            axios.get(`${api}/profile-config/`, { headers: { 'Authorization': `Bearer ${token}` } })
              .then(res => {
                const conf = res.data;
                let text = "";
                if (conf.razao_social) text += conf.razao_social.toUpperCase();
                if (conf.codigo_representante) {
                    text += (text ? " - CÓDIGO " : "CÓDIGO ") + conf.codigo_representante;
                }
                window._dispetDefault = text;
              })
              .catch(err => {
                console.error("Erro ao carregar profile config:", err);
              })
              .finally(() => {
                carregarTela();
              });
          } else {
            carregarTela();
          }
        });

        // ---- Automação de Canal de Venda por Tipo de Cliente ----
        // Dispara após o DOM estar pronto e os canais carregados
        document.addEventListener('DOMContentLoaded', () => {
          const tipoClienteSel = document.getElementById('tipo_cliente');
          if (!tipoClienteSel) return;

          tipoClienteSel.addEventListener('change', () => {
            autopreencherCanais(tipoClienteSel.value);
            // ---- Replicar para aba Elaboração ----
            const selElab = document.getElementById('classificacao_ElaboracaoCadastro');
            if (selElab) selElab.value = tipoClienteSel.value;
          });
        });

        // ---- Replicação do Tipo de Venda ----
        document.addEventListener('DOMContentLoaded', () => {
          const tipoVendaSel = document.getElementById('tipo_venda');
          if (!tipoVendaSel) return;

          tipoVendaSel.addEventListener('change', () => {
            const selElab = document.getElementById('tipo_venda_prazo_ou_vista_ElaboracaoCadastro');
            if (selElab) selElab.value = tipoVendaSel.value;
          });
        });

        // ---- Replicação do Limite de Crédito entre abas ----
        document.addEventListener('DOMContentLoaded', () => {
          const limCadastro = document.getElementById('limite_credito');
          const limElab = document.getElementById('limite_credito_ElaboracaoCadastro');

          // Máscara monetária BR com IMask (formato: 1.234,56)
          const maskOpts = {
            mask: Number,
            scale: 2,
            thousandsSeparator: '.',
            padFractionalZeros: true,
            normalizeZeros: true,
            radix: ',',
            mapToRadix: ['.'],
            min: 0,
            max: 999999999.99
          };

          if (limCadastro) {
              window.maskCadastro = IMask(limCadastro, maskOpts);
              limCadastro.maskInstance = window.maskCadastro;
          }
          if (limElab) {
              window.maskElabor = IMask(limElab, maskOpts);
              limElab.maskInstance = window.maskElabor;
          }

          // Sincronização bidirecional
          if (limCadastro && limElab) {
            limCadastro.addEventListener('input', () => {
              if (window.maskCadastro && window.maskElabor) {
                window.maskElabor.unmaskedValue = window.maskCadastro.unmaskedValue;
              }
            });
            limElab.addEventListener('input', () => {
              if (window.maskElabor && window.maskCadastro) {
                window.maskCadastro.unmaskedValue = window.maskElabor.unmaskedValue;
              }
            });
          }
        });

        function autopreencherCanais(tipoCliente) {
          if (!tipoCliente) return;

          const tipo = tipoCliente.toLowerCase()
            .normalize('NFD').replace(/[\u0300-\u036f]/g, '');

          // Matriz de regras: tipo -> { pet_frost, insumos }
          // Pet/Frost: canal_pet e canal_frost recebem o mesmo canal
          let canalPetFrost = null;
          let canalInsumos  = null;

          const isRevenda = tipo.includes('revend') || tipo.includes('lojist') || tipo.includes('atacad');
          const isConsumidor = tipo.includes('consumid') || tipo.includes('produtor') || tipo.includes('rural');

          if (isRevenda) {
            canalPetFrost = '39';
            canalInsumos  = '38';
          } else if (isConsumidor) {
            canalPetFrost = '12';
            canalInsumos  = '11';
          } else {
            return; // Tipo não reconhecido — não altera os canais
          }

          // Função auxiliar para selecionar a opção cujo value inicia com o código
          function selecionarCanal(selectId, codigo) {
            const sel = document.getElementById(selectId);
            if (!sel) return;
            // Busca opção cujo value == codigo ou começa com "codigo -"
            let encontrado = false;
            for (const opt of sel.options) {
              const v = String(opt.value).trim();
              if (v === codigo || v.startsWith(codigo + ' ') || v.startsWith(codigo + '-')) {
                sel.value = opt.value;
                encontrado = true;
                break;
              }
            }
            if (!encontrado) console.warn(`Canal ${codigo} não encontrado em #${selectId}`);
          }

          selecionarCanal('canal_pet_ElaboracaoCadastro',    canalPetFrost);
          selecionarCanal('canal_frost_ElaboracaoCadastro',  canalPetFrost);
          selecionarCanal('canal_insumos_ElaboracaoCadastro', canalInsumos);
        }


        function obterDadosFormulario() {
          return {
            cadastrocliente: {
              // Se o ID for vazio, envia 0 para validar como int no backend
              id: parseInt(document.getElementById("id")?.value || 0),
              codigo_da_empresa: document.getElementById("codigo_da_empresa")?.value || "",
              ativo: document.getElementById("ativo")?.checked || false,
              tipo_pessoa: document.getElementById("tipo_pessoa")?.value || "",
              tipo_cliente: document.getElementById("tipo_cliente")?.value || "",
              tipo_venda: document.getElementById("tipo_venda")?.value || "",
              tipo_compra: document.getElementById("tipo_compra")?.value || "",
              limite_credito: window.maskCadastro && !isNaN(window.maskCadastro.typedValue) ? Number(window.maskCadastro.typedValue) : (parseFloat((document.getElementById("limite_credito")?.value || "0").replace(/\./g, '').replace(',', '.')) || 0),
              nome_cliente: document.getElementById("nome_cliente")?.value || "",
              nome_fantasia: document.getElementById("nome_fantasia")?.value || "",
              cnpj: document.getElementById("cnpj")?.value || "",
              inscricao_estadual: document.getElementById("inscricao_estadual")?.value || "",
              cpf: document.getElementById("cpf")?.value || "",
              situacao: document.getElementById("situacao")?.value || "",
              status_cadastro: document.getElementById("status_cadastro")?.value || "",
              indicacao_cliente: null,  // legado; dado real em indicacoes_clientes
              ramo_de_atividade: document.getElementById("ramo_de_atividade")?.value || "",
              ramo_de_atividade: document.getElementById("ramo_de_atividade")?.value || "",
              atividade_principal: document.getElementById("atividade_principal")?.value || "",
              cadastro_markup: parseFloat(document.getElementById("cadastro_markup")?.value || 0),
              periodo_de_compra: document.getElementById("periodo_de_compra")?.value || ""
            },
            responsavel_compras: {
              nome_responsavel: document.getElementById("nome_responsavel")?.value || "",
              celular_responsavel: document.getElementById("celular_responsavel")?.value || "",
              telefone_fixo_responsavel: document.getElementById("telefone_fixo_responsavel")?.value || "",
              email_resposavel: document.getElementById("email_resposavel")?.value || "",
              data_nascimento_resposavel: document.getElementById("data_nascimento_resposavel")?.value || "",
              observacoes_responsavel: document.getElementById("observacoes_responsavel")?.value || "",
              filial_resposavel: document.getElementById("filial_resposavel")?.value || ""
            },
            endereco_faturamento: {
              endereco_faturamento: document.getElementById("endereco_faturamento")?.value || "",
              bairro_faturamento: document.getElementById("bairro_faturamento")?.value || "",
              cep_faturamento: document.getElementById("cep_faturamento")?.value || "",
              localizacao_faturamento: document.getElementById("localizacao_faturamento")?.value || "",
              municipio_faturamento: document.getElementById("municipio_faturamento")?.value || "",
              estado_faturamento: document.getElementById("estado_faturamento")?.value || "",
              email_danfe_faturamento: document.getElementById("email_danfe_faturamento")?.value || "",
              
            },
            representante_legal: {
              nome_RepresentanteLegal: document.getElementById("nome_RepresentanteLegal")?.value || "",
              celular_RepresentanteLegal: document.getElementById("celular_RepresentanteLegal")?.value || "",
              email_RepresentanteLegal: document.getElementById("email_RepresentanteLegal")?.value || "",
              data_nascimento_RepresentanteLegal: document.getElementById("data_nascimento_RepresentanteLegal")?.value || "",
              observacoes_RepresentanteLegal: document.getElementById("observacoes_RepresentanteLegal")?.value || ""
            },
            endereco_entrega: {
              endereco_EnderecoEntrega: document.getElementById("endereco_EnderecoEntrega")?.value || "",
              bairro_EnderecoEntrega: document.getElementById("bairro_EnderecoEntrega")?.value || "",
              cep_EnderecoEntrega: document.getElementById("cep_EnderecoEntrega")?.value || "",
              localizacao_EnderecoEntrega: document.getElementById("localizacao_EnderecoEntrega")?.value || "",
              municipio_EnderecoEntrega: document.getElementById("municipio_EnderecoEntrega")?.value || "",
              estado_EnderecoEntrega: document.getElementById("estado_EnderecoEntrega")?.value || "",
              rota_principal_EnderecoEntrega: document.getElementById("rota_principal_EnderecoEntrega")?.value || "",
              rota_de_aproximacao_EnderecoEntrega: document.getElementById("rota_de_aproximacao_EnderecoEntrega")?.value || "",
              observacao_motorista_EnderecoEntrega: document.getElementById("observacao_motorista_EnderecoEntrega")?.value || "",
              tipo_entrega_EnderecoEntrega: document.getElementById("tipo_entrega_EnderecoEntrega")?.value || ""
            },
            responsavel_recebimento: {
              nome_ResponsavelRecebimento: document.getElementById("nome_ResponsavelRecebimento")?.value || "",
              celular_ResponsavelRecebimento: document.getElementById("celular_ResponsavelRecebimento")?.value || "",
              email_ResponsavelRecebimento: document.getElementById("email_ResponsavelRecebimento")?.value || "",
              data_nascimento_ResponsavelRecebimento: document.getElementById("data_nascimento_ResponsavelRecebimento")?.value || "",
              observacoes_ResponsavelRecebimento: document.getElementById("observacoes_ResponsavelRecebimento")?.value || ""
            },
            endereco_cobranca: {
              endereco_EnderecoCobranca: document.getElementById("endereco_EnderecoCobranca")?.value || "",
              bairro_EnderecoCobranca: document.getElementById("bairro_EnderecoCobranca")?.value || "",
              cep_EnderecoCobranca: document.getElementById("cep_EnderecoCobranca")?.value || "",
              localizacao_EnderecoCobranca: document.getElementById("localizacao_EnderecoCobranca")?.value || "",
              municipio_EnderecoCobranca: document.getElementById("municipio_EnderecoCobranca")?.value || "",
              estado_EnderecoCobranca: document.getElementById("estado_EnderecoCobranca")?.value || ""
            },
            responsavel_cobranca: {
              nome_ResponsavelCobranca: document.getElementById("nome_ResponsavelCobranca")?.value || "",
              celular_ResponsavelCobranca: document.getElementById("celular_ResponsavelCobranca")?.value || "",
              email_ResponsavelCobranca: document.getElementById("email_ResponsavelCobranca")?.value || "",
              data_nascimento_ResponsavelCobranca: document.getElementById("data_nascimento_ResponsavelCobranca")?.value || "",
              observacoes_ResponsavelCobranca: document.getElementById("observacoes_ResponsavelCobranca")?.value || ""
            },
            dados_ultimas_compras: {
              numero_danfe_Compras: document.getElementById("numero_danfe_Compras")?.value || "",
              emissao_Compras: document.getElementById("emissao_Compras")?.value || "",
              valor_total_Compras: parseFloat(document.getElementById("valor_total_Compras")?.value || 0),
              valor_frete_Compras: parseFloat(document.getElementById("valor_frete_Compras")?.value || 0),
              valor_frete_padrao_Compras: parseFloat(document.getElementById("valor_frete_padrao_Compras")?.value || 0),
              valor_ultimo_frete_to_Compras: parseFloat(document.getElementById("valor_ultimo_frete_to_Compras")?.value || 0),
              lista_tabela_Compras: document.getElementById("lista_tabela_Compras")?.value || "",
              condicoes_pagamento_Compras: document.getElementById("condicoes_pagamento_Compras")?.value || "",
              cliente_calcula_st_Compras: document.getElementById("cliente_calcula_st_Compras")?.value || "",
              prazo_medio_compra_Compras: document.getElementById("prazo_medio_compra_Compras")?.value || "",
              previsao_proxima_compra_Compras: document.getElementById("previsao_proxima_compra_Compras")?.value || ""
            },
            observacoes_nao_compra: {
              observacoes_Compras: document.getElementById("observacoes_Compras")?.value || ""
            },
            dados_elaboracao_cadastro: {
              classificacao_ElaboracaoCadastro: document.getElementById("classificacao_ElaboracaoCadastro")?.value || "",
              tipo_venda_prazo_ou_vista_ElaboracaoCadastro: document.getElementById("tipo_venda_prazo_ou_vista_ElaboracaoCadastro")?.value || "",
              limite_credito_ElaboracaoCadastro: window.maskElabor && !isNaN(window.maskElabor.typedValue) ? Number(window.maskElabor.typedValue) : (parseFloat((document.getElementById("limite_credito_ElaboracaoCadastro")?.value || "0").replace(/\./g, '').replace(',', '.')) || 0),
              data_vencimento_ElaboracaoCadastro: document.getElementById("data_vencimento_ElaboracaoCadastro")?.value || "",
              vendedor_ElaboracaoCadastro: document.getElementById("vendedor_ElaboracaoCadastro")?.value || "",
              gerente_insumos_ElaboracaoCadastro: document.getElementById("gerente_insumos_ElaboracaoCadastro")?.value || "",
              gerente_pet_ElaboracaoCadastro: document.getElementById("gerente_pet_ElaboracaoCadastro")?.value || "",
              pre_posto_ElaboracaoCadastro: document.getElementById("pre_posto_ElaboracaoCadastro")?.value || "",
              local_carregamento_ElaboracaoCadastro: document.getElementById("local_carregamento_ElaboracaoCadastro")?.value || "",
              placa_veiculo_ElaboracaoCadastro: (coletarLista('bens_moveis')[0]?.placa || ""),
              proprietario_veiculo_ElaboracaoCadastro: (coletarLista('bens_moveis')[0]?.proprietario || "")
            },
            // Listas dinâmicas (JSONB)
            indicacoes_clientes: coletarLista('indicacoes'),
            grupos_economicos:    coletarLista('grupos_economicos'),
            referencias_comerciais: coletarLista('referencias_comerciais'),
            referencias_bancarias:  coletarLista('referencias_bancarias'),
            bens_imoveis:  coletarLista('bens_imoveis'),
            bens_moveis:   coletarLista('bens_moveis'),
            planteis_animais: coletarLista('planteis_animais'),
            supervisores: {
              codigo_insumo_ElaboracaoCadastro: document.getElementById("codigo_insumo_ElaboracaoCadastro")?.value || "",
              nome_insumos_ElaboracaoCadastro: document.getElementById("nome_insumos_ElaboracaoCadastro")?.value || "",
              codigo_pet_ElaboracaoCadastro: document.getElementById("codigo_pet_ElaboracaoCadastro")?.value || "",
              nome_pet_ElaboracaoCadastro: document.getElementById("nome_pet_ElaboracaoCadastro")?.value || ""
            },
            comissao_dispet: {
              insumos_ElaboracaoCadastro: document.getElementById("insumos_ElaboracaoCadastro")?.value || "",
              pet_ElaboracaoCadastro: document.getElementById("pet_ElaboracaoCadastro")?.value || "",
              observacoes_ElaboracaoCadastro: document.getElementById("observacoes_ElaboracaoCadastro")?.value || "",
              comissao_pet_dispet_flag: document.getElementById("comissao_pet_dispet_flag")?.checked ?? true,
              comissao_insumos_dispet_flag: document.getElementById("comissao_insumos_dispet_flag")?.checked ?? true
            },
            canal_venda_cliente: {
              canal_pet_ElaboracaoCadastro:     document.getElementById("canal_pet_ElaboracaoCadastro")?.value || "",
              canal_frost_ElaboracaoCadastro:   document.getElementById("canal_frost_ElaboracaoCadastro")?.value || "",
              canal_insumos_ElaboracaoCadastro: document.getElementById("canal_insumos_ElaboracaoCadastro")?.value || ""
            },
            outras_informacoes: {
              observacao: document.getElementById("outras_observacoes")?.value || "",
              veiculos_terceiros: coletarLista('veiculos_terceiros')
            }
          };
        }

        // =========================================================
        //  SISTEMA DE LISTAS DINÂMICAS (JSONB)
        // =========================================================

        // Definição dos campos de cada seção dinâmica
        const TEMPLATE_CAMPOS = {
          indicacoes: {
            gridClass: 'form-grid-1col',
            fields: [
              { key: 'valor', label: 'Indicação', type: 'text' }
            ]
          },
          grupos_economicos: {
            gridClass: 'form-grid-2col',
            fields: [
              { key: 'codigo', label: 'Código Cliente (Buscar)', type: 'lookup_cliente' },
              { key: 'nome',   label: 'Nome Empresarial', type: 'text', attributes: { readonly: true } }
            ]
          },
          referencias_comerciais: {
            gridClass: 'form-grid-2col',
            fields: [
              { key: 'empresa',  label: 'Empresa',  type: 'text', attributes: { readonly: true } },
              { key: 'cidade',   label: 'Cidade',   type: 'text', attributes: { readonly: true } },
              { key: 'telefone', label: 'Telefone', type: 'text', attributes: { readonly: true } },
              { key: 'contato',  label: 'Contato',  type: 'text', attributes: { readonly: true } }
            ]
          },
          referencias_bancarias: {
            gridClass: 'form-grid-2col',
            fields: [
              { key: 'banco',           label: 'Banco',           type: 'text' },
              { key: 'agencia',         label: 'Agência',         type: 'text' },
              { key: 'conta_corrente',  label: 'Conta Corrente',  type: 'text' },
              { key: 'gerente',         label: 'Gerente',         type: 'text' },
              { key: 'contato_gerente', label: 'Contato Gerente', type: 'text' }
            ]
          },
          veiculos_terceiros: {
            gridClass: 'form-grid-3col',
            fields: [
              { key: 'nome_terceiro', label: 'Nome do Terceiro', type: 'text' },
              { key: 'veiculo',       label: 'Veículo (Modelo)', type: 'text' },
              { key: 'placa',         label: 'Placa',            type: 'text' }
            ]
          },
          bens_imoveis: {
            gridClass: 'form-grid-3col',
            fields: [
              { key: 'imovel',      label: 'Imóvel',       type: 'text' },
              { key: 'localizacao', label: 'Localização',  type: 'text' },
              { key: 'area',        label: 'Área',          type: 'text' },
              { key: 'valor',       label: 'Valor (R$)',    type: 'text', attributes: { placeholder: 'R$ 0,00' } },
              { key: 'hipotecado',  label: 'Hipotecado',   type: 'select', options: ['', 'Sim', 'Não'] }
            ]
          },
          bens_moveis: {
            gridClass: 'form-grid-3col',
            fields: [
              { key: 'marca',        label: 'Marca',                    type: 'text' },
              { key: 'modelo',       label: 'Modelo',                   type: 'text' },
              { key: 'valor',        label: 'Valor (R$)',               type: 'text', attributes: { placeholder: 'R$ 0,00' } },
              { key: 'alienado',     label: 'Alienado',                 type: 'select', options: ['', 'Sim', 'Não'] },
              { key: 'placa',        label: 'Placa do Veículo',         type: 'text', attributes: { placeholder: 'AAA-0000', oninput: "this.value = this.value.toUpperCase()" } },
              { key: 'proprietario', label: 'Proprietário do Veículo',  type: 'text' }
            ]
          },
          planteis_animais: {
            gridClass: 'form-grid-4col',
            fields: [
              { key: 'especie',          label: 'Espécie',           type: 'select_plantel' },
              { key: 'numero_de_animais',label: 'Número de Animais', type: 'number' },
              { key: 'consumo_diario',   label: 'Consumo Diário (kg)',type: 'number', attributes: { oninput: "calcConsumoMensal(this)" } },
              { key: 'consumo_mensal',   label: 'Consumo Mensal (kg)',type: 'number', attributes: { readonly: true } }
            ]
          }
        };

        function criarBlocoItem(secao, index, dados = {}) {
          const config = TEMPLATE_CAMPOS[secao];
          const campos = config.fields;
          const bloco = document.createElement('div');
          bloco.className = 'item-dinamico-bloco';
          bloco.dataset.index = index;

          // Grid de campos
          const grid = document.createElement('div');
          grid.className = config.gridClass || 'form-grid-2col';
          grid.style.flex = '1';

          campos.forEach(campo => {
            const wrapper = document.createElement('div');
            wrapper.style.position = 'relative'; // For lookup
            const label = document.createElement('label');
            label.textContent = campo.label + ':';
            
            let input;
            let resultsDiv = null;
            
            if (campo.type === 'select' || campo.type === 'select_referencia' || campo.type === 'select_plantel') {
              input = document.createElement('select');
              
              let listOptions = campo.options || [];
              if (campo.type === 'select_referencia' && window._listaReferencias) {
                  listOptions = window._listaReferencias.map(r => ({
                      value: r.empresa,
                      label: `${r.empresa}${r.contato ? ' - ' + r.contato : ''}`
                  }));
              } else if (campo.type === 'select_plantel' && window._listaPlantel) {
                  listOptions = window._listaPlantel.map(p => p.plantel_animais);
              }
              
              const defaultOpt = document.createElement('option');
              defaultOpt.value = '';
              defaultOpt.textContent = '-- Selecione --';
              input.appendChild(defaultOpt);

              listOptions.forEach(optVal => {
                if(!optVal) return;
                const opt = document.createElement('option');
                if (typeof optVal === 'object') {
                    opt.value = optVal.value;
                    opt.textContent = optVal.label;
                } else {
                    opt.value = optVal;
                    opt.textContent = optVal;
                }
                input.appendChild(opt);
              });
              
              if (campo.type === 'select_referencia') {
                input.classList.add('select-referencia');
                input.onchange = function() { preencherDadosReferencia(this); };
              } else if (campo.type === 'select_plantel') {
                input.classList.add('select-plantel');
              }
            } else if (campo.type === 'lookup_cliente') {
              input = document.createElement('input');
              input.type = 'text';
              input.placeholder = "Digite e aguarde...";
              input.oninput = function() { buscarClienteLookup(this); };
              input.onblur = function() { setTimeout(() => { if (resultsDiv) resultsDiv.style.display = 'none'; }, 200); };
              
              resultsDiv = document.createElement('div');
              resultsDiv.className = 'lookup-results';
              resultsDiv.style.display = 'none';
            } else {
              input = document.createElement('input');
              input.type = campo.type || 'text';
              if (campo.type === 'number') input.step = '0.01';
            }
            
            if (campo.attributes) {
               Object.keys(campo.attributes).forEach(attr => {
                  if (attr.startsWith('on')) {
                     input.setAttribute(attr, campo.attributes[attr]);
                  } else {
                     input[attr] = campo.attributes[attr];
                  }
               });
            }
            
            input.dataset.key = campo.key;
            const savedVal = dados[campo.key] ?? '';
            
            if (input.tagName === 'SELECT' && savedVal) {
                let exists = Array.from(input.options).some(opt => opt.value === String(savedVal));
                if (!exists) {
                    const opt = document.createElement('option');
                    opt.value = savedVal;
                    opt.textContent = savedVal;
                    input.appendChild(opt);
                }
            }
            input.value = savedVal;
            
            if (secao === 'referencias_comerciais') {
              input.style.cursor = 'pointer';
              input.style.backgroundColor = '#fff';
              input.placeholder = 'Clique para buscar...';
              input.style.transition = 'border-color 0.15s, box-shadow 0.15s';
              
              input.addEventListener('mouseenter', function() {
                if (!this.disabled) {
                  this.style.borderColor = 'var(--os-primary, #2563eb)';
                  this.style.boxShadow = '0 0 0 3px var(--os-primary-ring, rgba(37, 99, 235, 0.15))';
                }
              });
              input.addEventListener('mouseleave', function() {
                if (!this.disabled) {
                  this.style.borderColor = '';
                  this.style.boxShadow = '';
                }
              });
              
              input.addEventListener('click', function() {
                if (!this.disabled) {
                  abrirModalReferencia(this);
                }
              });
            }
            
            wrapper.appendChild(label);
            wrapper.appendChild(input);
            if (resultsDiv) wrapper.appendChild(resultsDiv);
            grid.appendChild(wrapper);
          });

          // Botão remover
          const btnRemover = document.createElement('button');
          btnRemover.type = 'button';
          btnRemover.className = 'btn-remover-item';
          btnRemover.title = 'Remover';
          btnRemover.innerHTML = '&#128465;';
          btnRemover.onclick = () => removerItem(secao, bloco);

          bloco.appendChild(grid);
          bloco.appendChild(btnRemover);

          // Aplicar máscaras aos novos campos se necessário
          setTimeout(() => {
            const telInput = bloco.querySelector('input[data-key="telefone"]');
            if (telInput) applyPhoneMask(telInput);
            
            const contatoInput = bloco.querySelector('input[data-key="contato_gerente"]');
            if (contatoInput) applyPhoneMask(contatoInput);

            // Máscara de Moeda para campos de valor
            const valorInput = bloco.querySelector('input[data-key="valor"]');
            if (valorInput) {
              valorInput.maskInstance = IMask(valorInput, {
                mask: 'R$ num',
                blocks: {
                  num: {
                    mask: Number,
                    thousandsSeparator: '.',
                    padFractionalZeros: true,
                    radix: ',',
                    mapToRadix: ['.']
                  }
                }
              });
            }
          }, 0);

          return bloco;
        }

        function applyPhoneMask(el) {
          if (!el || !window.IMask) return;
          IMask(el, {
            mask: [
              { mask: '(00) 0000-0000' },
              { mask: '(00) 00000-0000' }
            ]
          });
        }

        function atualizarContador(secao) {
          const container = document.getElementById(`container-${secao}`);
          const contador = document.getElementById(`contador-${secao}`);
          if (!container || !contador) return;
          
          let total = container.querySelectorAll('.item-dinamico-bloco').length;
          if (secao === 'referencias_comerciais') {
            // Conta apenas os blocos onde a empresa foi de fato preenchida
            total = Array.from(container.querySelectorAll('.item-dinamico-bloco'))
              .filter(b => b.querySelector('input[data-key="empresa"]')?.value?.trim()).length;
          }
          
          const limite = (secao === 'indicacoes') ? 5 : (secao === 'veiculos_terceiros') ? 2 : 3;
          contador.textContent = `(${total}/${limite})`;
        }

        function adicionarItem(secao, limite) {
          const container = document.getElementById(`container-${secao}`);
          const btnAdd = document.getElementById(`btn-add-${secao}`);
          if (!container) return;
          const atual = container.querySelectorAll('.item-dinamico-bloco').length;
          if (atual >= limite) {
            alert(`Limite máximo de ${limite} ${secao === 'indicacoes' ? 'indicações' : 'itens'} atingido.`);
            return;
          }
          const bloco = criarBlocoItem(secao, atual);
          container.appendChild(bloco);
          // Oculta botão se atingiu o limite
          if (btnAdd && container.querySelectorAll('.item-dinamico-bloco').length >= limite) {
            btnAdd.style.opacity = '0.5';
          }
          atualizarContador(secao);
        }

        function removerItem(secao, bloco) {
          const container = document.getElementById(`container-${secao}`);
          const btnAdd = document.getElementById(`btn-add-${secao}`);
          bloco.remove();
          
          // Se for referências comerciais e ficou sem nenhum bloco, restaura 1 bloco vazio padrão
          if (secao === 'referencias_comerciais' && container.querySelectorAll('.item-dinamico-bloco').length === 0) {
            adicionarItem('referencias_comerciais', 3);
          }
          
          if (btnAdd) btnAdd.style.opacity = '1';
          atualizarContador(secao);
        }

        function coletarLista(secao) {
          const container = document.getElementById(`container-${secao}`);
          if (!container) return [];
          const blocos = container.querySelectorAll('.item-dinamico-bloco');
          const result = [];
          blocos.forEach(bloco => {
            const inputs = bloco.querySelectorAll('input, select');
            if (secao === 'indicacoes') {
              const val = inputs[0]?.value?.trim();
              if (val) result.push(val);
            } else {
              const obj = {};
              let temValor = false;
              inputs.forEach(inp => {
                const key = inp.dataset.key;
                let val;
                
                if (inp.maskInstance && (key === 'valor' || key.includes('limite'))) {
                    let tv = inp.maskInstance.typedValue;
                    val = (tv === '' || tv === null || tv === undefined) ? null : Number(tv);
                } else {
                    val = (inp.type === 'number' || inp.tagName === 'SELECT') ? (inp.value || null) : (inp.value?.trim() || null);
                    if (inp.type === 'number' && val !== null) val = Number(val);
                }
                
                obj[key] = val;
                if (val !== null && val !== '') temValor = true;
              });
              if (temValor) result.push(obj);
            }
          });
          return result;
        }

        function renderizarLista(secao, limite, dados) {
          const container = document.getElementById(`container-${secao}`);
          const btnAdd = document.getElementById(`btn-add-${secao}`);
          if (!container) return;
          container.innerHTML = '';
          
          if (!dados || dados.length === 0) {
            // Se não houver dados, abre 1 bloco vazio por padrão
            adicionarItem(secao, limite);
          } else {
            dados.forEach((item, i) => {
              const blocoData = (secao === 'indicacoes') ? { valor: item } : item;
              container.appendChild(criarBlocoItem(secao, i, blocoData));
            });
          }

          if (btnAdd) {
            btnAdd.style.opacity = container.querySelectorAll('.item-dinamico-bloco').length >= limite ? '0.5' : '1';
          }
          atualizarContador(secao);

          // Sincroniza o estado de habilitação dos novos campos com o estado da tela
          const isReadOnly = (window._currentViewState === 'INITIAL' || window._currentViewState === 'SELECTED' || !window._currentViewState);
          const novosInputs = container.querySelectorAll("input, select, textarea, button.btn-remover-item");
          novosInputs.forEach(input => {
            input.disabled = isReadOnly;
            if (input.tagName === 'BUTTON') {
              input.style.pointerEvents = isReadOnly ? 'none' : 'auto';
              input.style.opacity = isReadOnly ? '0.5' : '1';
            }
          });
        }



        function preencherFormularioCliente(cliente) {
          const dados = cliente || {};

          // Helper para evitar erros se o elemento não existir
          const setVal = (id, val) => {
            const el = document.getElementById(id);
            if (el) {
              if (el.tagName === 'SELECT' && val) {
                let exists = Array.from(el.options).some(opt => opt.value === String(val));
                if (!exists) {
                  const opt = document.createElement('option');
                  opt.value = val;
                  opt.text = val;
                  el.appendChild(opt);
                }
              }
              
              // Campos monetários e numéricos usam typedValue para evitar parsing problemático
              let hasMask = !!el.maskInstance;
              if (id === 'limite_credito' || id === 'limite_credito_ElaboracaoCadastro' || id === 'cadastro_markup' || id.includes('valor_')) {
                if (hasMask) {
                    el.maskInstance.typedValue = parseFloat(val) || 0;
                } else {
                    el.value = val ?? "";
                }
              } else if (hasMask) {
                // Outros campos (como CEP, CPF) usam value string
                el.maskInstance.value = String(val ?? "");
              } else {
                el.value = val ?? "";
              }

              if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                // SÓ dispara o evento input se NÃO tiver máscara, senão o IMask lê o valor formatado 
                // e aplica o mapToRadix novamente, destruindo o número (ex: "5.000,00" -> "5,000,00" -> "5,00")
                if (!hasMask) {
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                }
              } else if (el.tagName === 'SELECT') {
                el.dispatchEvent(new Event('change', { bubbles: true }));
              }
            }
          };
          const setCheck = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.checked = val;
          };

          // Bloco: cadastrocliente
          const c = dados.cadastrocliente || {};
          setVal("id", c.id || "");
          setVal("codigo_da_empresa", c.codigo_da_empresa || "");
          setCheck("ativo", c.ativo ?? true);
          setVal("tipo_pessoa", c.tipo_pessoa || "");
          setVal("tipo_cliente", c.tipo_cliente || "");
          setVal("tipo_venda", c.tipo_venda || "");
          setVal("tipo_compra", c.tipo_compra || "");
          // Limite de crédito: passa o valor bruto, a máscara formata
          setVal("limite_credito", c.limite_credito || "");
          setVal("nome_cliente", c.nome_cliente || "");
          setVal("nome_fantasia", c.nome_fantasia || "");
          setVal("cnpj", c.cnpj || "");
          setVal("inscricao_estadual", c.inscricao_estadual || "");
          setVal("cpf", c.cpf || "");
          setVal("situacao", c.situacao || "");
          setVal("status_cadastro", c.status_cadastro || "");
          // indicacoes_clientes é renderizado via renderizarLista() mais abaixo
          setVal("ramo_de_atividade", c.ramo_de_atividade || "");
          setVal("atividade_principal", c.atividade_principal || "");
          setVal("cadastro_markup", c.cadastro_markup || "");
          setVal("periodo_de_compra", c.periodo_de_compra || "");

          // Bloco: responsavel_compras
          const rc = dados.responsavel_compras || {};
          setVal("nome_responsavel", rc.nome_responsavel || "");
          setVal("celular_responsavel", rc.celular_responsavel || "");
          setVal("telefone_fixo_responsavel", rc.telefone_fixo_responsavel || "");
          setVal("email_resposavel", rc.email_resposavel || "");
          setVal("data_nascimento_resposavel", rc.data_nascimento_resposavel || "");
          setVal("observacoes_responsavel", rc.observacoes_responsavel || "");
          setVal("filial_resposavel", rc.filial_resposavel || "");

          // Bloco: endereco_faturamento
          const ef = dados.endereco_faturamento || {};
          setVal("endereco_faturamento", ef.endereco_faturamento || "");
          setVal("bairro_faturamento", ef.bairro_faturamento || "");
          setVal("cep_faturamento", ef.cep_faturamento || "");
          setVal("localizacao_faturamento", ef.localizacao_faturamento || "");
          setVal("municipio_faturamento", ef.municipio_faturamento || "");
          setVal("estado_faturamento", ef.estado_faturamento || "");
          setVal("email_danfe_faturamento", ef.email_danfe_faturamento || "");
          

          // Bloco: representante_legal
          const rl = dados.representante_legal || {};
          setVal("nome_RepresentanteLegal", rl.nome_RepresentanteLegal || "");
          setVal("celular_RepresentanteLegal", rl.celular_RepresentanteLegal || "");
          setVal("email_RepresentanteLegal", rl.email_RepresentanteLegal || "");
          setVal("data_nascimento_RepresentanteLegal", rl.data_nascimento_RepresentanteLegal || "");
          setVal("observacoes_RepresentanteLegal", rl.observacoes_RepresentanteLegal || "");

          // Bloco: endereco_entrega
          const ee = dados.endereco_entrega || {};
          setVal("endereco_EnderecoEntrega", ee.endereco_EnderecoEntrega || "");
          setVal("bairro_EnderecoEntrega", ee.bairro_EnderecoEntrega || "");
          setVal("cep_EnderecoEntrega", ee.cep_EnderecoEntrega || "");
          setVal("localizacao_EnderecoEntrega", ee.localizacao_EnderecoEntrega || "");
          setVal("municipio_EnderecoEntrega", ee.municipio_EnderecoEntrega || "");
          setVal("estado_EnderecoEntrega", ee.estado_EnderecoEntrega || "");
          setVal("rota_principal_EnderecoEntrega", ee.rota_principal_EnderecoEntrega || "");
          setVal("rota_de_aproximacao_EnderecoEntrega", ee.rota_de_aproximacao_EnderecoEntrega || "");
          setVal("observacao_motorista_EnderecoEntrega", ee.observacao_motorista_EnderecoEntrega || "");
          setVal("tipo_entrega_EnderecoEntrega", ee.tipo_entrega_EnderecoEntrega || "");

          // Bloco: responsavel_recebimento
          const rr = dados.responsavel_recebimento || {};
          setVal("nome_ResponsavelRecebimento", rr.nome_ResponsavelRecebimento || "");
          setVal("celular_ResponsavelRecebimento", rr.celular_ResponsavelRecebimento || "");
          setVal("email_ResponsavelRecebimento", rr.email_ResponsavelRecebimento || "");
          setVal("data_nascimento_ResponsavelRecebimento", rr.data_nascimento_ResponsavelRecebimento || "");
          setVal("observacoes_ResponsavelRecebimento", rr.observacoes_ResponsavelRecebimento || "");

          // Bloco: endereco_cobranca
          const ec = dados.endereco_cobranca || {};
          setVal("endereco_EnderecoCobranca", ec.endereco_EnderecoCobranca || "");
          setVal("bairro_EnderecoCobranca", ec.bairro_EnderecoCobranca || "");
          setVal("cep_EnderecoCobranca", ec.cep_EnderecoCobranca || "");
          setVal("localizacao_EnderecoCobranca", ec.localizacao_EnderecoCobranca || "");
          setVal("municipio_EnderecoCobranca", ec.municipio_EnderecoCobranca || "");
          setVal("estado_EnderecoCobranca", ec.estado_EnderecoCobranca || "");

          // Bloco: responsavel_cobranca
          const rcob = dados.responsavel_cobranca || {};
          setVal("nome_ResponsavelCobranca", rcob.nome_ResponsavelCobranca || "");
          setVal("celular_ResponsavelCobranca", rcob.celular_ResponsavelCobranca || "");
          setVal("email_ResponsavelCobranca", rcob.email_ResponsavelCobranca || "");
          setVal("data_nascimento_ResponsavelCobranca", rcob.data_nascimento_ResponsavelCobranca || "");
          setVal("observacoes_ResponsavelCobranca", rcob.observacoes_ResponsavelCobranca || "");

          // Bloco: dados_ultimas_compras
          const comp = dados.dados_ultimas_compras || {};
          setVal("numero_danfe_Compras", comp.numero_danfe_Compras || "");
          setVal("emissao_Compras", comp.emissao_Compras || "");
          setVal("valor_total_Compras", comp.valor_total_Compras || "");
          setVal("valor_frete_Compras", comp.valor_frete_Compras || "");
          setVal("valor_frete_padrao_Compras", comp.valor_frete_padrao_Compras || "");
          setVal("valor_ultimo_frete_to_Compras", comp.valor_ultimo_frete_to_Compras || "");
          setVal("lista_tabela_Compras", comp.lista_tabela_Compras || "");
          setVal("condicoes_pagamento_Compras", comp.condicoes_pagamento_Compras || "");
          setVal("cliente_calcula_st_Compras", comp.cliente_calcula_st_Compras || "");
          setVal("prazo_medio_compra_Compras", comp.prazo_medio_compra_Compras || "");
          setVal("previsao_proxima_compra_Compras", comp.previsao_proxima_compra_Compras || "");

          // Bloco: observacoes_nao_compra
          const obs = dados.observacoes_nao_compra || {};
          setVal("observacoes_Compras", obs.observacoes_Compras || "");

          // Bloco: dados_elaboracao_cadastro
          const ed = dados.dados_elaboracao_cadastro || {};
          setVal("classificacao_ElaboracaoCadastro", ed.classificacao_ElaboracaoCadastro || "");
          setVal("tipo_venda_prazo_ou_vista_ElaboracaoCadastro", ed.tipo_venda_prazo_ou_vista_ElaboracaoCadastro || "");
          // Limite de crédito: passa o valor bruto, a máscara formata
          setVal("limite_credito_ElaboracaoCadastro", ed.limite_credito_ElaboracaoCadastro || "");
          setVal("data_vencimento_ElaboracaoCadastro", ed.data_vencimento_ElaboracaoCadastro || "");
          setVal("vendedor_ElaboracaoCadastro", ed.vendedor_ElaboracaoCadastro || "");
          setVal("gerente_insumos_ElaboracaoCadastro", ed.gerente_insumos_ElaboracaoCadastro || "");
          setVal("gerente_pet_ElaboracaoCadastro", ed.gerente_pet_ElaboracaoCadastro || "");
          setVal("pre_posto_ElaboracaoCadastro", ed.pre_posto_ElaboracaoCadastro || "");
          setVal("local_carregamento_ElaboracaoCadastro", ed.local_carregamento_ElaboracaoCadastro || "");
          // Listas dinâmicas (JSONB)
          renderizarLista('indicacoes', 5, dados.indicacoes_clientes || []);
          renderizarLista('grupos_economicos', 3, dados.grupos_economicos || []);
          renderizarLista('referencias_comerciais', 3, dados.referencias_comerciais || []);
          renderizarLista('referencias_bancarias', 3, dados.referencias_bancarias || []);
          renderizarLista('bens_imoveis', 3, dados.bens_imoveis || []);

          let listBensMoveis = dados.bens_moveis || [];
          if (listBensMoveis.length === 0) {
            if (ed.placa_veiculo_ElaboracaoCadastro || ed.proprietario_veiculo_ElaboracaoCadastro) {
              listBensMoveis = [{
                marca: "",
                modelo: "",
                valor: "",
                alienado: "",
                placa: ed.placa_veiculo_ElaboracaoCadastro || "",
                proprietario: ed.proprietario_veiculo_ElaboracaoCadastro || ""
              }];
            }
          } else {
            if (listBensMoveis[0] && typeof listBensMoveis[0] === 'object') {
              if (!listBensMoveis[0].placa && ed.placa_veiculo_ElaboracaoCadastro) {
                listBensMoveis[0].placa = ed.placa_veiculo_ElaboracaoCadastro;
              }
              if (!listBensMoveis[0].proprietario && ed.proprietario_veiculo_ElaboracaoCadastro) {
                listBensMoveis[0].proprietario = ed.proprietario_veiculo_ElaboracaoCadastro;
              }
            }
          }
          renderizarLista('bens_moveis', 3, listBensMoveis);
          renderizarLista('planteis_animais', 3, dados.planteis_animais || []);

          // Bloco: supervisores
          const sup = dados.supervisores || {};
          setVal("codigo_insumo_ElaboracaoCadastro", sup.codigo_insumo_ElaboracaoCadastro || "");
          setVal("nome_insumos_ElaboracaoCadastro", sup.nome_insumos_ElaboracaoCadastro || "");
          setVal("codigo_pet_ElaboracaoCadastro", sup.codigo_pet_ElaboracaoCadastro || "");
          setVal("nome_pet_ElaboracaoCadastro", sup.nome_pet_ElaboracaoCadastro || "");

           const cd = dados.comissao_dispet || {};
          setVal("insumos_ElaboracaoCadastro", cd.insumos_ElaboracaoCadastro || "");
          setVal("pet_ElaboracaoCadastro", cd.pet_ElaboracaoCadastro || "");
          setVal("observacoes_ElaboracaoCadastro", cd.observacoes_ElaboracaoCadastro || "");
          
          const chkPet = document.getElementById("comissao_pet_dispet_flag");
          if (chkPet) chkPet.checked = cd.comissao_pet_dispet_flag !== false;
          
          const chkInsumos = document.getElementById("comissao_insumos_dispet_flag");
          if (chkInsumos) chkInsumos.checked = cd.comissao_insumos_dispet_flag !== false;

          const cv = dados.canal_venda_cliente || {};
          setVal("canal_pet_ElaboracaoCadastro",     cv.canal_pet_ElaboracaoCadastro || "");
          setVal("canal_frost_ElaboracaoCadastro",   cv.canal_frost_ElaboracaoCadastro || "");
          setVal("canal_insumos_ElaboracaoCadastro", cv.canal_insumos_ElaboracaoCadastro || "");

          const oi = dados.outras_informacoes || {};
          setVal("outras_observacoes", oi.observacao || "");
          renderizarLista('veiculos_terceiros', 2, oi.veiculos_terceiros || []);

          setViewState('SELECTED');
        }


        function openTab(event, tabName) {
          const tabs = document.querySelectorAll('.tab-content');
          tabs.forEach(tab => tab.style.display = 'none');

          const buttons = document.querySelectorAll('.tab');
          buttons.forEach(btn => btn.classList.remove('active'));

          const selectedTab = document.getElementById(tabName);
          if (selectedTab) selectedTab.style.display = 'block';

          // Add active class to the button that opened the tab if event is provided
          if (event && event.currentTarget) {
            event.currentTarget.classList.add('active');
          }
        }

        // --- API Integration Functions ---

        async function buscarCep(event, tipo) {
          const cep = event.target.value.replace(/\D/g, '');
          if (cep.length !== 8) return;

          try {
            // Visual feedback (optional: change cursor or disable input temp)
            event.target.style.cursor = 'wait';

            const response = await axios.get(`https://brasilapi.com.br/api/cep/v2/${cep}`);
            const data = response.data;

            // Mapping based on 'tipo' (faturamento, EnderecoEntrega, EnderecoCobranca)
            // Note: The HTML IDs use 'faturamento' (lowercase) but 'EnderecoEntrega'/'EnderecoCobranca' (CamelCase) suffix.
            // We need to map the incoming 'tipo' argument to the correct suffix used in IDs.

            let suffix = "";
            if (tipo === 'faturamento') suffix = "_faturamento";
            else if (tipo === 'entrega') suffix = "_EnderecoEntrega";
            else if (tipo === 'cobranca') suffix = "_EnderecoCobranca";

            if (!suffix) return;

            const setVal = (fieldPrefix, value) => {
              const el = document.getElementById(`${fieldPrefix}${suffix}`);
              if (el) el.value = value;
            };

            setVal('endereco', data.street);
            setVal('bairro', data.neighborhood);
            setVal('municipio', data.city);
            setVal('estado', data.state);
            
            // Disparar evento para as máscaras atualizarem (ex: se houver máscara no campo preenchido)
            ['endereco', 'bairro', 'municipio', 'estado'].forEach(f => {
                const el = document.getElementById(`${f}${suffix}`);
                if (el) el.dispatchEvent(new Event('input'));
            });

            if (tipo === 'faturamento') {
              buscarSupervisorPetEInsumos();
            }

          } catch (error) {
            console.error("Erro ao buscar CEP:", error);
            alert("Erro ao buscar CEP. Verifique se está correto.");
          } finally {
            event.target.style.cursor = 'default';
          }
        }

        async function buscarCnpj() {
          const cnpjInput = document.getElementById("cnpj");
          const cnpj = cnpjInput.value.replace(/\D/g, '');

          if (cnpj.length !== 14) return;

          try {
            cnpjInput.style.cursor = 'wait';

            const response = await axios.get(`https://brasilapi.com.br/api/cnpj/v1/${cnpj}`);
            const data = response.data;

            // Helper to set value
            const setVal = (id, val) => {
              const el = document.getElementById(id);
              if (el) el.value = val;
            };

            // Helper to handle Selects (add option if not exists to ensure it's selected)
            const setSelect = (id, value) => {
              const select = document.getElementById(id);
              if (!select) return;

              // Normaliza para comparação (ex: remove acentos ou uppercase se necessário, mas aqui vamos tentar direto)
              // Verifica se já existe a opção
              let exists = false;
              for (let i = 0; i < select.options.length; i++) {
                if (select.options[i].value === value || select.options[i].text === value) {
                  select.selectedIndex = i;
                  exists = true;
                  break;
                }
              }

              // Se não existe, cria uma nova opção temporária
              if (!exists && value) {
                const option = document.createElement("option");
                option.value = value;
                option.text = value; // Exibe o texto vindo da API
                select.appendChild(option);
                select.value = value;
              }
            };

            setVal('nome_cliente', data.razao_social); // Razão Social

            // Limpeza: Muitas vezes (principalmente MEI) a Razão Social vem com o CNPJ no início (ex: "12.345.678 NOME DA PESSOA").
            // Vamos remover isso se existir para ficar mais limpo.
            let nomeLimpo = data.razao_social;
            const cnpjRootFormatado = data.cnpj.substring(0, 8).replace(/^(\d{2})(\d{3})(\d{3}).*/, "$1.$2.$3");
            if (nomeLimpo.startsWith(cnpjRootFormatado)) {
              nomeLimpo = nomeLimpo.substring(cnpjRootFormatado.length).trim();
              // Remove hifens ou caracteres soltos que possam ter sobrado
              nomeLimpo = nomeLimpo.replace(/^[-]\s*/, "");
            }
            setVal('nome_cliente', nomeLimpo);

            setVal('nome_fantasia', data.nome_fantasia || nomeLimpo);

            // Mapeamentos Específicos

            // 1. Situação: BrasilAPI retorna "ATIVA", "BAIXADA", etc.
            // Tenta mapear "ATIVA" -> "Ativo" se o select esperar isso, ou usa o valor direto.
            let situacao = data.descricao_situacao_cadastral;
            if (situacao === "ATIVA") situacao = "Ativo"; // Tentativa de normalização comum
            setSelect('situacao', situacao);

            // 2. Atividade Principal e Ramo de Atividade
            // A API retorna `cnae_fiscal_descricao_principal`. Vamos preencher ambos os campos com isso por padrão.
            const atividade = data.cnae_fiscal_descricao_principal;
            setSelect('atividade_principal', atividade);
            setSelect('ramo_de_atividade', atividade);

            // Address Info -> Mapped to Faturamento and Entrega
            const enderecoFull = `${data.logradouro}, ${data.numero}${data.complemento ? ' - ' + data.complemento : ''}`;
            
            // Faturamento
            setVal('cep_faturamento', data.cep);
            setVal('endereco_faturamento', enderecoFull);
            setVal('bairro_faturamento', data.bairro);
            setVal('municipio_faturamento', data.municipio);
            setVal('estado_faturamento', data.uf);

            // Entrega
            setVal('cep_EnderecoEntrega', data.cep);
            setVal('endereco_EnderecoEntrega', enderecoFull);
            setVal('bairro_EnderecoEntrega', data.bairro);
            setVal('municipio_EnderecoEntrega', data.municipio);
            setVal('estado_EnderecoEntrega', data.uf);

            // Contact
            setVal('email_resposavel', data.email);
            
            // Disparar evento para as máscaras atualizarem
            [
              'nome_cliente', 'nome_fantasia', 
              'cep_faturamento', 'endereco_faturamento', 'bairro_faturamento', 'municipio_faturamento', 'estado_faturamento',
              'cep_EnderecoEntrega', 'endereco_EnderecoEntrega', 'bairro_EnderecoEntrega', 'municipio_EnderecoEntrega', 'estado_EnderecoEntrega'
            ].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.dispatchEvent(new Event('input'));
            });

            // [NEW] Após preencher o CEP e Município via CNPJ, busca os supervisores
            if (data.municipio) {
               buscarSupervisorPetEInsumos();
            }

            // Nota sobre Inscrição Estadual:
            // A API pública de CNPJ (Receita Federal) NÃO retorna Inscrição Estadual (dado estadual).
            // Portanto, esse campo deve ser preenchido manualmente ou via API paga (Sintegra).

          } catch (error) {
            console.error("Erro ao buscar CNPJ:", error);
          } finally {
            cnpjInput.style.cursor = 'default';
          }
        }

        // Helpers auto-preenchimento Catalogo

        // Carrega todas as opções de Canal de Venda (ID - Tipo) nos 3 selects
        async function carregarOpcoesCanal() {
          const token = localStorage.getItem("ordersync_token");
          const api = window.API_BASE || "http://127.0.0.1:8000";
          const selectIds = [
            "canal_pet_ElaboracaoCadastro",
            "canal_frost_ElaboracaoCadastro",
            "canal_insumos_ElaboracaoCadastro"
          ];
          try {
            const res = await fetch(`${api}/catalogo/canal-venda`, {
              headers: { "Authorization": `Bearer ${token}` }
            });
            if (!res.ok) return;
            const canais = await res.json();
            selectIds.forEach(selId => {
              const sel = document.getElementById(selId);
              if (!sel) return;
              // mantém apenas a opção placeholder
              sel.innerHTML = '<option value="">-- Selecione --</option>';
              canais.forEach(c => {
                const label = `${c.Id} - ${c.tipo}`;
                const opt = document.createElement("option");
                opt.value = label;
                opt.textContent = label;
                sel.appendChild(opt);
              });
            });
          } catch (e) {
            console.error("Erro ao carregar canais de venda:", e);
          }
        }

        async function buscarSupervisorPetEInsumos() {
          const municipio = document.getElementById("municipio_faturamento").value;
          if (!municipio) return;

          const token = localStorage.getItem("ordersync_token");
          try {
            const api = window.API_BASE || "http://127.0.0.1:8000";
            const res = await fetch(`${api}/catalogo/cidade-supervisor/buscar?municipio=${encodeURIComponent(municipio)}`, {
               headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
              const data = await res.json();
              document.getElementById("codigo_insumo_ElaboracaoCadastro").value = data.codigo_insumo || "";
              document.getElementById("nome_insumos_ElaboracaoCadastro").value = data.nome_insumos || "";
              document.getElementById("codigo_pet_ElaboracaoCadastro").value = data.codigo_pet || "";
              document.getElementById("nome_pet_ElaboracaoCadastro").value = data.nome_pet || "";
              document.getElementById("gerente_insumos_ElaboracaoCadastro").value = data.gerente_insumos || "";
              document.getElementById("gerente_pet_ElaboracaoCadastro").value = data.gerente_pet || "";
              
              const dispetDef = window._dispetDefault || "";
              document.getElementById("insumos_ElaboracaoCadastro").value = dispetDef;
              document.getElementById("pet_ElaboracaoCadastro").value = dispetDef;
            }
          } catch (e) {
            console.error(e);
          }
        }

        // ==========================================
        //  FUNÇÕES DE LOOKUP E INTEGRAÇÃO (NOVO)
        // ==========================================

        let lookupTimeout = null;
        async function buscarClienteLookup(inputElement) {
            const query = inputElement.value.trim();
            const wrapper = inputElement.parentElement;
            const resultsDiv = wrapper.querySelector('.lookup-results');
            if (!resultsDiv) return;

            if (query.length < 2) {
                resultsDiv.style.display = 'none';
                return;
            }

            if(lookupTimeout) clearTimeout(lookupTimeout);
            
            lookupTimeout = setTimeout(async () => {
                const api = window.API_BASE || "http://127.0.0.1:8000";
                const token = window.Auth ? window.Auth.getToken() : localStorage.getItem('ordersync_token');
                if (!token) return;

                try {
                    const res = await axios.get(`${api}/cliente/lookup?query=${encodeURIComponent(query)}`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    
                    const clientes = res.data;
                    resultsDiv.innerHTML = '';
                    
                    if (clientes.length === 0) {
                        resultsDiv.innerHTML = '<div class="lookup-item" style="color: #6b7280;">Nenhum cliente encontrado</div>';
                    } else {
                        clientes.forEach(c => {
                            const itemDiv = document.createElement('div');
                            itemDiv.className = 'lookup-item';
                            itemDiv.textContent = `${c.codigo} - ${c.nome_empresarial}`;
                            
                            // Ao clicar no resultado
                            itemDiv.onmousedown = function (e) {
                                e.preventDefault(); // Evita que o input perca o foco antes do clique
                                inputElement.value = c.codigo;
                                
                                // Preencher o campo de 'nome_empresarial' que está na mesma row (mesmo dataset.index)
                                const bloco = inputElement.closest('.item-dinamico-bloco');
                                if (bloco) {
                                    const nomeInput = bloco.querySelector('input[data-key="nome"]');
                                    if (nomeInput) nomeInput.value = c.nome_empresarial;
                                }
                                resultsDiv.style.display = 'none';
                            };
                            
                            resultsDiv.appendChild(itemDiv);
                        });
                    }
                    resultsDiv.style.display = 'block';
                } catch (error) {
                    console.error("Erro na busca do lookup:", error);
                }
            }, 500); // 500ms debounce
        }

        async function carregarOpcoesReferencia() {
            const api = window.API_BASE || "http://127.0.0.1:8000";
            const token = window.Auth ? window.Auth.getToken() : localStorage.getItem('ordersync_token');
            if (!token) return;
            try {
                const res = await axios.get(`${api}/catalogo/referencias`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                window._listaReferencias = res.data; // Armazenar para uso ao preencher
                
                document.querySelectorAll('.select-referencia').forEach(select => {
                    const valAtual = select.value;
                    select.innerHTML = '<option value="">-- Selecione a Empresa --</option>';
                    res.data.forEach(ref => {
                        const opt = document.createElement('option');
                        opt.value = ref.empresa;
                        opt.textContent = `${ref.empresa}${ref.contato ? ' - ' + ref.contato : ''}`;
                        select.appendChild(opt);
                    });
                    if (valAtual) select.value = valAtual;
                });
            } catch (err) {
                console.error("Erro ao carregar lista de referências:", err);
            }
        }

        function preencherDadosReferencia(selectElement) {
            const empresa = selectElement.value;
            const bloco = selectElement.closest('.item-dinamico-bloco');
            if (!bloco) return;
            
            const campoCidade = bloco.querySelector('input[data-key="cidade"]');
            const campoTelefone = bloco.querySelector('input[data-key="telefone"]');
            const campoContato = bloco.querySelector('input[data-key="contato"]');
            
            if (empresa && window._listaReferencias) {
                const ref = window._listaReferencias.find(r => r.empresa === empresa);
                if (ref) {
                    if (campoCidade) campoCidade.value = ref.cidade || '';
                    if (campoTelefone) campoTelefone.value = ref.telefone || '';
                    if (campoContato) campoContato.value = ref.contato || '';
                    return;
                }
            }
            
            // Limpa se não achar
            if (campoCidade) campoCidade.value = '';
            if (campoTelefone) campoTelefone.value = '';
            if (campoContato) campoContato.value = '';
        }
        
        async function carregarOpcoesPlantel() {
            const api = window.API_BASE || "http://127.0.0.1:8000";
            const token = window.Auth ? window.Auth.getToken() : localStorage.getItem('ordersync_token');
            if (!token) return;
            try {
                const res = await axios.get(`${api}/catalogo/plantel-animais`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                window._listaPlantel = res.data;
                document.querySelectorAll('.select-plantel').forEach(select => {
                    const valAtual = select.value;
                    select.innerHTML = '<option value="">-- Selecione --</option>';
                    res.data.forEach(p => {
                        const opt = document.createElement('option');
                        opt.value = p.plantel_animais;
                        opt.textContent = p.plantel_animais;
                        select.appendChild(opt);
                    });
                    if (valAtual) select.value = valAtual;
                });
            } catch (err) {
                console.error("Erro ao carregar lista de plantel_animais:", err);
            }
        }

        function calcConsumoMensal(element) {
            const bloco = element.closest('.item-dinamico-bloco');
            if (!bloco) return;
            const campoMensal = bloco.querySelector('input[data-key="consumo_mensal"]');
            if (!campoMensal) return;
            
            const diarioStr = element.value.replace(',', '.');
            const diario = parseFloat(diarioStr);
            
            if (!isNaN(diario)) {
                campoMensal.value = (diario * 30).toFixed(2);
            } else {
                campoMensal.value = '';
            }
        }

        // Disponibiliza para o modal chamar
        window.preencherFormulario = preencherFormularioCliente;
        window.buscarSupervisorPetEInsumos = buscarSupervisorPetEInsumos;

        // Inicialização de Máscaras Globais
        function initGlobalMasks() {
          if (!window.IMask) return;

          const applyMask = (el, maskOptions) => {
            if (el && !el.maskInstance) {
              el.maskInstance = IMask(el, maskOptions);
            }
          };

          // CPF / CNPJ
          applyMask(document.getElementById('cpf'), { mask: '000.000.000-00' });
          applyMask(document.getElementById('cnpj'), { mask: '00.000.000/0000-00' });

          // CEPs
          ['cep_faturamento', 'cep_EnderecoEntrega', 'cep_EnderecoCobranca'].forEach(id => {
            applyMask(document.getElementById(id), { mask: '00000-000' });
          });

          // Telefones/Celulares Estáticos
          ['celular_responsavel', 'telefone_fixo_responsavel',
            'celular_RepresentanteLegal', 'celular_ResponsavelRecebimento',
            'celular_ResponsavelCobranca'
          ].forEach(id => {
            const el = document.getElementById(id);
            if (el && !el.phoneMaskApplied) {
              applyPhoneMask(el);
              el.phoneMaskApplied = true;
            }
          });
        }

        // --- Execução Inicial ---
        document.addEventListener('DOMContentLoaded', () => {
          // Inicializa máscaras globais (estáticas)
          initGlobalMasks();
          
          // Carrega lista de referências e plantel para preencher selects dinâmicos
          carregarOpcoesReferencia();
          carregarOpcoesPlantel();
          
          // Adiciona listener para campos de busca de CEP para formatar após preenchimento automático
          document.querySelectorAll('input[id*="cep"]').forEach(el => {
              el.addEventListener('input', (e) => {
                  // Se o valor for colado ou preenchido auto, o IMask cuida da formatação se já inicializado
                  // mas garantimos um dispatchEvent(new Event('input')) dentro das funções buscarCep e buscarCnpj
              });
          });
        });
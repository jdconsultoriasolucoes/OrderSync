let clientes = [];
        let filtrados = [];
        let currentPage = 1;
        const itemsPerPage = 20;

        function fmtDoc(s) {
            const d = String(s || '').replace(/\D/g, '');
            if (d.length === 14) return d.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
            if (d.length === 11) return d.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, '$1.$2.$3-$4');
            return s || '';
        }

        // Carrega os clientes do backend
        const token = localStorage.getItem('ordersync_token');
        const api = window.API_BASE || "http://127.0.0.1:8000";

        axios.get(`${api}/cliente`, {
            headers: { 'Authorization': `Bearer ${token}` }
        })
            .then(res => {
                clientes = res.data;
                filtrados = [...clientes];
                renderizarTabela();
            })
            .catch(error => {
                alert(`Erro ao buscar clientes: ${error.message || error}`);
                console.error(error);
            });

        function renderizarTabela() {
            const tbody = document.querySelector("#tabela-clientes tbody");
            tbody.innerHTML = "";

            const startIndex = (currentPage - 1) * itemsPerPage;
            const endIndex = startIndex + itemsPerPage;
            const paginaAtualClientes = filtrados.slice(startIndex, endIndex);

            paginaAtualClientes.forEach(cliente => {
                const tr = document.createElement("tr");

                // Toggle expansão no mobile
                tr.addEventListener("click", function (e) {
                    // Evita expandir/retrair se clicar diretamente no botão "Selecionar"
                    if (e.target.tagName !== "BUTTON") {
                        this.classList.toggle("expanded");
                    }
                });

                const btn = document.createElement("button");
                btn.textContent = "Selecionar";
                btn.className = "os-btn os-btn-primary os-btn-sm";
                btn.addEventListener("click", () => selecionarCliente(cliente));

                tr.innerHTML = `
          <td data-label="ID">${cliente.cadastrocliente?.id || ''}</td>
          <td data-label="Nome">${cliente.cadastrocliente?.nome_cliente || ''} <span class="mobile-chevron">▼</span></td>
          <td data-label="CPF">${fmtDoc(cliente.cadastrocliente?.cpf)}</td>
          <td data-label="CNPJ">${fmtDoc(cliente.cadastrocliente?.cnpj)}</td>
          <td data-label="Email">${cliente.responsavel_compras?.email_resposavel || ''}</td>
          <td data-label="Estado">${cliente.endereco_entrega?.estado_EnderecoEntrega || ''}</td>
          <td data-label="Ativo"><span class="os-badge ${cliente.cadastrocliente?.ativo ? 'os-badge-success' : 'os-badge-error'}">${cliente.cadastrocliente?.ativo ? 'Sim' : 'Não'}</span></td>
        `;

                const tdBtn = document.createElement("td");
                tdBtn.dataset.label = "Ação";
                tdBtn.appendChild(btn);
                tr.appendChild(tdBtn);
                tbody.appendChild(tr);
            });

            atualizarBotoesPaginacao();
        }

        function atualizarBotoesPaginacao() {
            const btnPrev = document.getElementById("btn-prev");
            const btnNext = document.getElementById("btn-next");
            const pageInfo = document.getElementById("page-info");

            const totalPages = Math.ceil(filtrados.length / itemsPerPage) || 1;

            pageInfo.textContent = `Página ${currentPage} de ${totalPages}`;
            btnPrev.disabled = currentPage === 1;
            btnNext.disabled = currentPage === totalPages;
        }

        function nextPage() {
            const totalPages = Math.ceil(filtrados.length / itemsPerPage);
            if (currentPage < totalPages) {
                currentPage++;
                renderizarTabela();
            }
        }

        function prevPage() {
            if (currentPage > 1) {
                currentPage--;
                renderizarTabela();
            }
        }

        function voltarParaCadastro() {
            localStorage.removeItem('Ordersync_ClienteSelecionadoIdListar'); // ensure clear state
            window.location.href = "cliente.html";
        }

        function selecionarCliente(cliente) {
            if (cliente && cliente.cadastrocliente && cliente.cadastrocliente.id) {
                // Saving the selected client ID into local storage to intercept it automatically in the form screen
                localStorage.setItem('Ordersync_ClienteSelecionadoIdListar', cliente.cadastrocliente.id);
                window.location.href = "cliente.html";
            } else {
                alert("Erro: Este cliente não possui um ID válido.");
            }
        }

        // Filtro ao digitar
        document.getElementById("filtro").addEventListener("input", function () {
            const termo = this.value.toLowerCase().trim();

            filtrados = clientes.filter(c => {
                const id = String(c.cadastrocliente?.id || '');
                const codigo = String(c.cadastrocliente?.codigo_da_empresa || '').toLowerCase(); // Novo
                const nome = c.cadastrocliente?.nome_cliente?.toLowerCase() || '';
                const fantasia = c.cadastrocliente?.nome_fantasia?.toLowerCase() || ''; // Novo
                const cpf = (c.cadastrocliente?.cpf || '').replace(/\D/g, ''); // Somente números
                const cnpj = (c.cadastrocliente?.cnpj || '').replace(/\D/g, ''); // Somente números
                const email = c.responsavel_compras?.email_resposavel?.toLowerCase() || '';
                const uf = c.endereco_entrega?.estado_EnderecoEntrega?.toLowerCase() || '';

                // Termo limpo para comparação numérica
                const termoNumerico = termo.replace(/\D/g, '');

                return (
                    id.includes(termo) ||
                    codigo.includes(termo) ||
                    nome.includes(termo) ||
                    fantasia.includes(termo) ||
                    email.includes(termo) ||
                    uf.includes(termo) ||
                    (termoNumerico && (cpf.includes(termoNumerico) || cnpj.includes(termoNumerico)))
                );
            });

            currentPage = 1; // Reseta a página após aplicar o filtro
            renderizarTabela();
        });
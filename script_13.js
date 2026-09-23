let _blocoReferenciaAtivo = null;

        function abrirModalReferencia(inputEl) {
          const container = document.getElementById('container-referencias_comerciais');
          
          if (inputEl) {
            _blocoReferenciaAtivo = inputEl.closest('.item-dinamico-bloco');
          } else {
            _blocoReferenciaAtivo = null;
            
            // Se clicou no botão geral, verifica o limite de preenchidos
            const blocos = container.querySelectorAll('.item-dinamico-bloco');
            let preenchidos = 0;
            blocos.forEach(b => {
              const emp = b.querySelector('input[data-key="empresa"]')?.value;
              if (emp) preenchidos++;
            });
            
            if (preenchidos >= 3) {
              alert('Limite máximo de 3 referências comerciais atingido.');
              return;
            }
          }
          
          document.getElementById('input-busca-ref').value = '';
          renderizarTabelaReferencias(window._listaReferencias || []);
          document.getElementById('modal-busca-referencia').classList.add('active');
        }

        function fecharModalReferencia() {
          document.getElementById('modal-busca-referencia').classList.remove('active');
          _blocoReferenciaAtivo = null;
        }

        function renderizarTabelaReferencias(lista) {
          const tbody = document.getElementById('tbody-busca-referencia');
          const msgVazia = document.getElementById('msg-sem-referencia');
          tbody.innerHTML = '';
          
          if (!lista || lista.length === 0) {
            msgVazia.style.display = 'block';
            return;
          }
          msgVazia.style.display = 'none';

          lista.forEach((ref, index) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td>${ref.empresa || '-'}</td>
              <td>${ref.contato || '-'}</td>
              <td>${ref.cidade || '-'}</td>
              <td class="tar">
                <button class="os-btn os-btn-primary os-btn-sm" onclick="selecionarReferenciaModal(${index})">Selecionar</button>
              </td>
            `;
            tbody.appendChild(tr);
          });
        }

        function filtrarReferenciasModal() {
          const termo = document.getElementById('input-busca-ref').value.toLowerCase();
          const listaTotal = window._listaReferencias || [];
          
          if (!termo) {
            renderizarTabelaReferencias(listaTotal);
            return;
          }

          const filtrada = listaTotal.filter(ref => {
            const empresa = (ref.empresa || '').toLowerCase();
            const cidade = (ref.cidade || '').toLowerCase();
            const contato = (ref.contato || '').toLowerCase();
            return empresa.includes(termo) || cidade.includes(termo) || contato.includes(termo);
          });

          const tbody = document.getElementById('tbody-busca-referencia');
          const msgVazia = document.getElementById('msg-sem-referencia');
          tbody.innerHTML = '';
          
          if (filtrada.length === 0) {
            msgVazia.style.display = 'block';
            return;
          }
          msgVazia.style.display = 'none';

          filtrada.forEach((ref) => {
            // Buscando o indice original
            const originalIndex = listaTotal.indexOf(ref);
            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td>${ref.empresa || '-'}</td>
              <td>${ref.contato || '-'}</td>
              <td>${ref.cidade || '-'}</td>
              <td class="tar">
                <button class="os-btn os-btn-primary os-btn-sm" onclick="selecionarReferenciaModal(${originalIndex})">Selecionar</button>
              </td>
            `;
            tbody.appendChild(tr);
          });
        }

        function selecionarReferenciaModal(indexOriginal) {
          const ref = window._listaReferencias[indexOriginal];
          if (!ref) return;

          const container = document.getElementById('container-referencias_comerciais');
          
          // Se tiver um bloco ativo (clicado diretamente), preenche ele
          let blocoDestino = _blocoReferenciaAtivo;
          
          // Se não tiver bloco ativo (clicou no botão "+ Adicionar"), procura o primeiro bloco vazio
          if (!blocoDestino) {
            const blocos = container.querySelectorAll('.item-dinamico-bloco');
            for (const b of blocos) {
              const emp = b.querySelector('input[data-key="empresa"]')?.value;
              if (!emp) {
                blocoDestino = b;
                break;
              }
            }
          }

          if (blocoDestino) {
            const inputs = blocoDestino.querySelectorAll('input');
            inputs.forEach(inp => {
              const key = inp.dataset.key;
              if (key === 'empresa') inp.value = ref.empresa || '';
              if (key === 'cidade') inp.value = ref.cidade || '';
              if (key === 'telefone') inp.value = ref.telefone || '';
              if (key === 'contato') inp.value = ref.contato || '';
            });
          } else {
            // Se não houver bloco destino e nem vazio, cria um novo
            const atual = container.querySelectorAll('.item-dinamico-bloco').length;
            if (atual >= 3) {
              alert('Limite máximo de 3 referências comerciais atingido.');
              fecharModalReferencia();
              return;
            }
            const bloco = criarBlocoItem('referencias_comerciais', atual, {
              empresa: ref.empresa || '',
              cidade: ref.cidade || '',
              telefone: ref.telefone || '',
              contato: ref.contato || ''
            });
            container.appendChild(bloco);
          }

          const btnAdd = document.getElementById('btn-add-referencias_comerciais');
          if (btnAdd) {
            const totalPreenchidos = Array.from(container.querySelectorAll('.item-dinamico-bloco'))
              .filter(b => b.querySelector('input[data-key="empresa"]')?.value).length;
            if (totalPreenchidos >= 3) {
              btnAdd.style.opacity = '0.5';
            } else {
              btnAdd.style.opacity = '1';
            }
          }

          atualizarContador('referencias_comerciais');
          fecharModalReferencia();
        }
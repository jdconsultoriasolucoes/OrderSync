/**
 * Utilitário Global para Tratamento de Erros de API
 * Depende da biblioteca SweetAlert2 para exibição visual.
 */

const ErrorUtils = {
    /**
     * Mapeamento de nomes de campos técnicos (FastAPI/Pydantic) para nomes amigáveis ao usuário
     */
    fieldMap: {
        "cadastrocliente": "Cadastro do Cliente",
        "codigo_da_empresa": "Código da Empresa",
        "limite_credito": "Limite de Crédito",
        "bens_imoveis": "Bens Imóveis",
        "bens_moveis": "Bens Móveis",
        "valor": "Valor (R$)",
        "nome_cliente": "Nome do Cliente",
        "cpf": "CPF",
        "cnpj": "CNPJ",
        "email_resposavel": "E-mail do Responsável",
        "data_vencimento_ElaboracaoCadastro": "Data de Vencimento"
        // Adicione mais mapeamentos conforme necessário
    },

    /**
     * Mapeia o erro de validação (type) para uma mensagem descritiva
     */
    typeMap: {
        "type_error.float": "deve ser um número válido",
        "type_error.integer": "deve ser um número inteiro",
        "value_error.missing": "é obrigatório",
        "value_error.any_str.min_length": "está muito curto",
        "value_error.email": "precisa ser um e-mail válido",
        "type_error.none.not_allowed": "não pode ficar vazio"
    },

    /**
     * Exibe um modal de erro na tela (requer ação do usuário para fechar)
     */
    showError: function (title, message) {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: 'error',
                title: title || 'Ops! Algo deu errado',
                html: message || 'Ocorreu um erro inesperado.',
                confirmButtonText: 'OK',
                confirmButtonColor: '#2563eb', // Cor base do projeto
                allowOutsideClick: false, // Espera o usuário fechar
                allowEscapeKey: true
            });
        } else {
            // Fallback caso SweetAlert2 não tenha carregado
            alert(`${title}\n\n${message}`);
        }
    },

    /**
     * Exibe um modal de sucesso na tela
     */
    showSuccess: function (title, message) {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: 'success',
                title: title || 'Sucesso',
                text: message || 'Operação realizada com sucesso.',
                confirmButtonText: 'OK',
                confirmButtonColor: '#10b981', // Verde sucesso
                timer: 3000,
                timerProgressBar: true
            });
        } else {
            alert(`${title}\n\n${message}`);
        }
    },

    /**
     * Recebe um objeto de Erro (Axios) ou Resposta (Fetch) e processa o corpo do erro, 
     * exibindo a mensagem visualmente.
     */
    handleApiError: async function (errorOrResponse) {
        try {
            let status, data;

            // Identifica se é um erro do Axios (error.response) ou um Response do Fetch
            if (errorOrResponse.response && errorOrResponse.response.data) {
                // Axios Error
                status = errorOrResponse.response.status;
                data = errorOrResponse.response.data;
            } else if (typeof errorOrResponse.json === 'function') {
                // Fetch Response
                status = errorOrResponse.status;
                data = await errorOrResponse.json();
            } else {
                // Outro tipo de erro
                console.error(errorOrResponse);
                this.showError('Erro', 'Ocorreu um erro desconhecido.');
                return;
            }
            
            // 422 - Unprocessable Entity (Erros do Pydantic)
            if (status === 422 && data.detail && Array.isArray(data.detail)) {
                let errorMessages = '<ul style="text-align: left; margin-top: 10px; font-size: 0.9em; max-height: 200px; overflow-y: auto;">';
                
                data.detail.forEach(err => {
                    const locs = err.loc.filter(l => l !== 'body'); 
                    const fieldName = locs.map(l => {
                        if (typeof l === 'number') return `[${l + 1}]`;
                        return this.fieldMap[l] || l;
                    }).join(' > ').replace(' > [', ' [');
                    
                    const issue = this.typeMap[err.type] || err.msg;
                    errorMessages += `<li><b>${fieldName}</b>: ${issue}</li>`;
                });
                
                errorMessages += '</ul>';
                
                this.showError('Erro de Validação (422)', `Os seguintes dados precisam ser corrigidos:<br>${errorMessages}`);
                return;
            }

            // Tratamento de detalhes em string (400, 401, 403, 404, 500)
            if (data.detail && typeof data.detail === 'string') {
                this.showError(`Erro ${status}`, data.detail);
                return;
            }
            
            if (data.message) {
                this.showError(`Erro ${status}`, data.message);
                return;
            }

            // Fallback Genérico JSON
            this.showError(`Falha (${status})`, 'O servidor retornou um erro, mas nenhuma descrição detalhada foi fornecida.');
            
        } catch (e) {
            console.error("Error parsing API Error:", e, errorOrResponse);
            this.showError('Erro no Servidor', 'O servidor retornou um formato inesperado ou ocorreu uma falha de rede.');
        }
    }
};

window.ErrorUtils = ErrorUtils;

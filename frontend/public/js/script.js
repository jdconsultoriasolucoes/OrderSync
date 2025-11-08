// script.js atualizado para cliente_simples.html

(function ensureApiBase(){
  if (window.API_BASE) { window.API_BASE = window.API_BASE.replace(/\/+$/, ""); return; }
  if (window.__CFG && window.__CFG.API_BASE_URL) {
    window.API_BASE = String(window.__CFG.API_BASE_URL).replace(/\/+$/, "");
  } else {
    window.API_BASE = "";
  }
})();

function apiUrlCliente(id = "") {
  const base = window.API_BASE || "";
  const path = id ? `/api/cliente/${encodeURIComponent(id)}` : `/api/cliente`;
  return base ? `${base}${path}` : path;
}

// Aplica máscaras
window.addEventListener("DOMContentLoaded", () => {
  if (window.IMask) {
    IMask(document.getElementById("cpf"), { mask: "000.000.000-00" });
    IMask(document.getElementById("cnpj"), { mask: "00.000.000/0000-00" });
    IMask(document.getElementById("telefone"), { mask: "(00) 0000-0000" });
    IMask(document.getElementById("celular"), { mask: "(00) 00000-0000" });
  }
});

let clienteOriginal = null;
let clienteEditando = false;

function obterDadosFormulario() {
  return { 
      cadastrocliente: {
      codigo_da_empresa: document.getElementById("codigo_da_empresa")?.value || "",
      ativo: document.getElementById("ativo")?.checked || false,
      tipo_cliente: document.getElementById("tipo_cliente")?.value || "",
      tipo_venda: document.getElementById("tipo_venda")?.value || "",
      tipo_compra: document.getElementById("tipo_compra")?.value || "",
      limite_credito: parseFloat(document.getElementById("limite_credito")?.value || 0),
      nome_cliente: document.getElementById("nome_cliente")?.value || "",
      nome_fantasia: document.getElementById("nome_fantasia")?.value || "",
      cnpj: document.getElementById("cnpj")?.value || "",
      inscricao_estadual: document.getElementById("inscricao_estadual")?.value || "",
      cpf: document.getElementById("cpf")?.value || "",
      situacao: document.getElementById("situacao")?.value || "",
      indicacao_cliente: document.getElementById("indicacao_cliente")?.value || "",
      ramo_de_atividade: document.getElementById("ramo_de_atividade")?.value || "",
      atividade_principal: document.getElementById("atividade_principal")?.value || ""
    },
    responsavel_compras: {
      nome_responsavel: document.getElementById("nome_responsavel")?.value || "",
      celular_responsavel: document.getElementById("celular_responsavel")?.value || "",
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
      email_danfe_faturamento: document.getElementById("email_danfe_faturamento")?.value || ""
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
      observacao_motorista_EnderecoEntrega: document.getElementById("observacao_motorista_EnderecoEntrega")?.value || ""
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
      limite_credito_ElaboracaoCadastro: parseFloat(document.getElementById("limite_credito_ElaboracaoCadastro")?.value || 0),
      data_vencimento_ElaboracaoCadastro: document.getElementById("data_vencimento_ElaboracaoCadastro")?.value || ""
    },
    grupo_economico: {
      codigo_ElaboracaoCadastro: document.getElementById("codigo_ElaboracaoCadastro")?.value || "",
      nome_empresarial_ElaboracaoCadastro: document.getElementById("nome_empresarial_ElaboracaoCadastro")?.value || ""
    },
    referencia_comercial: {
      empresa_ElaboracaoCadastro: document.getElementById("empresa_ElaboracaoCadastro")?.value || "",
      cidade_ElaboracaoCadastro: document.getElementById("cidade_ElaboracaoCadastro")?.value || "",
      telefone_ElaboracaoCadastro: document.getElementById("telefone_ElaboracaoCadastro")?.value || "",
      contato_ElaboracaoCadastro: document.getElementById("contato_ElaboracaoCadastro")?.value || ""
    },
    referencia_bancaria: {
      banco_ElaboracaoCadastro: document.getElementById("banco_ElaboracaoCadastro")?.value || "",
      agencia_ElaboracaoCadastro: document.getElementById("agencia_ElaboracaoCadastro")?.value || "",
      conta_corrente_ElaboracaoCadastro: document.getElementById("conta_corrente_ElaboracaoCadastro")?.value || ""
    },
    bem_imovel: {
      imovel_ElaboracaoCadastro: document.getElementById("imovel_ElaboracaoCadastro")?.value || "",
      localizacao_ElaboracaoCadastro: document.getElementById("localizacao_ElaboracaoCadastro")?.value || "",
      area_ElaboracaoCadastro: document.getElementById("area_ElaboracaoCadastro")?.value || "",
      valor_ElaboracaoCadastro: parseFloat(document.getElementById("valor_ElaboracaoCadastro")?.value || 0),
      hipotecado_ElaboracaoCadastro: document.getElementById("hipotecado_ElaboracaoCadastro")?.value || ""
    },
    bem_movel: {
      marca_ElaboracaoCadastro: document.getElementById("marca_ElaboracaoCadastro")?.value || "",
      modelo_ElaboracaoCadastro: document.getElementById("modelo_ElaboracaoCadastro")?.value || "",
      alienado_ElaboracaoCadastro: document.getElementById("alienado_ElaboracaoCadastro")?.value || ""
    },
    plantel_animal: {
      especie_ElaboracaoCadastro: document.getElementById("especie_ElaboracaoCadastro")?.value || "",
      numero_de_animais_ElaboracaoCadastro: parseInt(document.getElementById("numero_de_animais_ElaboracaoCadastro")?.value || 0),
      consumo_diario_ElaboracaoCadastro: parseFloat(document.getElementById("consumo_diario_ElaboracaoCadastro")?.value || 0),
      consumo_mensal_ElaboracaoCadastro: parseFloat(document.getElementById("consumo_mensal_ElaboracaoCadastro")?.value || 0)
    },
    supervisores: {
      codigo_insumo_ElaboracaoCadastro: document.getElementById("codigo_insumo_ElaboracaoCadastro")?.value || "",
      nome_insumos_ElaboracaoCadastro: document.getElementById("nome_insumos_ElaboracaoCadastro")?.value || "",
      codigo_pet_ElaboracaoCadastro: document.getElementById("codigo_pet_ElaboracaoCadastro")?.value || "",
      nome_pet_ElaboracaoCadastro: document.getElementById("nome_pet_ElaboracaoCadastro")?.value || ""
    },
    comissao_dispet: {
      insumos_ElaboracaoCadastro: document.getElementById("insumos_ElaboracaoCadastro")?.value || "",
      pet_ElaboracaoCadastro: document.getElementById("pet_ElaboracaoCadastro")?.value || "",
      observacoes_ElaboracaoCadastro: document.getElementById("observacoes_ElaboracaoCadastro")?.value || ""
    }
}

function preencherFormularioCliente(cliente) {
  const dados = cliente || {};

  // Bloco: cadastrocliente
  const c = dados.cadastrocliente || {};
  document.getElementById("id").value = c.id || "";
  document.getElementById("codigo_da_empresa").value = c.codigo_da_empresa || "";
  document.getElementById("ativo").checked = c.ativo ?? true;
  document.getElementById("tipo_cliente").value = c.tipo_cliente || "";
  document.getElementById("tipo_venda").value = c.tipo_venda || "";
  document.getElementById("tipo_compra").value = c.tipo_compra || "";
  document.getElementById("limite_credito").value = c.limite_credito || "";
  document.getElementById("nome_cliente").value = c.nome_cliente || "";
  document.getElementById("nome_fantasia").value = c.nome_fantasia || "";
  document.getElementById("cnpj").value = c.cnpj || "";
  document.getElementById("inscricao_estadual").value = c.inscricao_estadual || "";
  document.getElementById("cpf").value = c.cpf || "";
  document.getElementById("situacao").value = c.situacao || "";
  document.getElementById("indicacao_cliente").value = c.indicacao_cliente || "";
  document.getElementById("ramo_de_atividade").value = c.ramo_de_atividade || "";
  document.getElementById("atividade_principal").value = c.atividade_principal || "";

  // Bloco: responsavel_compras
  const rc = dados.responsavel_compras || {};
  document.getElementById("nome_responsavel").value = rc.nome_responsavel || "";
  document.getElementById("celular_responsavel").value = rc.celular_responsavel || "";
  document.getElementById("email_resposavel").value = rc.email_resposavel || "";
  document.getElementById("data_nascimento_resposavel").value = rc.data_nascimento_resposavel || "";
  document.getElementById("observacoes_responsavel").value = rc.observacoes_responsavel || "";
  document.getElementById("filial_resposavel").value = rc.filial_resposavel || "";

  // Bloco: endereco_faturamento
  const ef = dados.endereco_faturamento || {};
  document.getElementById("endereco_faturamento").value = ef.endereco_faturamento || "";
  document.getElementById("bairro_faturamento").value = ef.bairro_faturamento || "";
  document.getElementById("cep_faturamento").value = ef.cep_faturamento || "";
  document.getElementById("localizacao_faturamento").value = ef.localizacao_faturamento || "";
  document.getElementById("municipio_faturamento").value = ef.municipio_faturamento || "";
  document.getElementById("estado_faturamento").value = ef.estado_faturamento || "";
  document.getElementById("email_danfe_faturamento").value = ef.email_danfe_faturamento || "";

  // Bloco: representante_legal
  const rl = dados.representante_legal || {};
  document.getElementById("nome_RepresentanteLegal").value = rl.nome_RepresentanteLegal || "";
  document.getElementById("celular_RepresentanteLegal").value = rl.celular_RepresentanteLegal || "";
  document.getElementById("email_RepresentanteLegal").value = rl.email_RepresentanteLegal || "";
  document.getElementById("data_nascimento_RepresentanteLegal").value = rl.data_nascimento_RepresentanteLegal || "";
  document.getElementById("observacoes_RepresentanteLegal").value = rl.observacoes_RepresentanteLegal || "";

  // Bloco: endereco_entrega
  const ee = dados.endereco_entrega || {};
  document.getElementById("endereco_EnderecoEntrega").value = ee.endereco_EnderecoEntrega || "";
  document.getElementById("bairro_EnderecoEntrega").value = ee.bairro_EnderecoEntrega || "";
  document.getElementById("cep_EnderecoEntrega").value = ee.cep_EnderecoEntrega || "";
  document.getElementById("localizacao_EnderecoEntrega").value = ee.localizacao_EnderecoEntrega || "";
  document.getElementById("municipio_EnderecoEntrega").value = ee.municipio_EnderecoEntrega || "";
  document.getElementById("estado_EnderecoEntrega").value = ee.estado_EnderecoEntrega || "";
  document.getElementById("rota_principal_EnderecoEntrega").value = ee.rota_principal_EnderecoEntrega || "";
  document.getElementById("rota_de_aproximacao_EnderecoEntrega").value = ee.rota_de_aproximacao_EnderecoEntrega || "";
  document.getElementById("observacao_motorista_EnderecoEntrega").value = ee.observacao_motorista_EnderecoEntrega || "";

  // Bloco: responsavel_recebimento
  const rr = dados.responsavel_recebimento || {};
  document.getElementById("nome_ResponsavelRecebimento").value = rr.nome_ResponsavelRecebimento || "";
  document.getElementById("celular_ResponsavelRecebimento").value = rr.celular_ResponsavelRecebimento || "";
  document.getElementById("email_ResponsavelRecebimento").value = rr.email_ResponsavelRecebimento || "";
  document.getElementById("data_nascimento_ResponsavelRecebimento").value = rr.data_nascimento_ResponsavelRecebimento || "";
  document.getElementById("observacoes_ResponsavelRecebimento").value = rr.observacoes_ResponsavelRecebimento || "";

  // Bloco: endereco_cobranca
  const ec = dados.endereco_cobranca || {};
  document.getElementById("endereco_EnderecoCobranca").value = ec.endereco_EnderecoCobranca || "";
  document.getElementById("bairro_EnderecoCobranca").value = ec.bairro_EnderecoCobranca || "";
  document.getElementById("cep_EnderecoCobranca").value = ec.cep_EnderecoCobranca || "";
  document.getElementById("localizacao_EnderecoCobranca").value = ec.localizacao_EnderecoCobranca || "";
  document.getElementById("municipio_EnderecoCobranca").value = ec.municipio_EnderecoCobranca || "";
  document.getElementById("estado_EnderecoCobranca").value = ec.estado_EnderecoCobranca || "";

  // Bloco: responsavel_cobranca
  const rcob = dados.responsavel_cobranca || {};
  document.getElementById("nome_ResponsavelCobranca").value = rcob.nome_ResponsavelCobranca || "";
  document.getElementById("celular_ResponsavelCobranca").value = rcob.celular_ResponsavelCobranca || "";
  document.getElementById("email_ResponsavelCobranca").value = rcob.email_ResponsavelCobranca || "";
  document.getElementById("data_nascimento_ResponsavelCobranca").value = rcob.data_nascimento_ResponsavelCobranca || "";
  document.getElementById("observacoes_ResponsavelCobranca").value = rcob.observacoes_ResponsavelCobranca || "";

  // Bloco: dados_ultimas_compras
  const comp = dados.dados_ultimas_compras || {};
  document.getElementById("numero_danfe_Compras").value = comp.numero_danfe_Compras || "";
  document.getElementById("emissao_Compras").value = comp.emissao_Compras || "";
  document.getElementById("valor_total_Compras").value = comp.valor_total_Compras || "";
  document.getElementById("valor_frete_Compras").value = comp.valor_frete_Compras || "";
  document.getElementById("valor_frete_padrao_Compras").value = comp.valor_frete_padrao_Compras || "";
  document.getElementById("valor_ultimo_frete_to_Compras").value = comp.valor_ultimo_frete_to_Compras || "";
  document.getElementById("lista_tabela_Compras").value = comp.lista_tabela_Compras || "";
  document.getElementById("condicoes_pagamento_Compras").value = comp.condicoes_pagamento_Compras || "";
  document.getElementById("cliente_calcula_st_Compras").value = comp.cliente_calcula_st_Compras || "";
  document.getElementById("prazo_medio_compra_Compras").value = comp.prazo_medio_compra_Compras || "";
  document.getElementById("previsao_proxima_compra_Compras").value = comp.previsao_proxima_compra_Compras || "";

  // Bloco: observacoes_nao_compra
  const obs = dados.observacoes_nao_compra || {};
  document.getElementById("observacoes_Compras").value = obs.observacoes_Compras || "";

  // Bloco: dados_elaboracao_cadastro
  const ed = dados.dados_elaboracao_cadastro || {};
  document.getElementById("classificacao_ElaboracaoCadastro").value = ed.classificacao_ElaboracaoCadastro || "";
  document.getElementById("tipo_venda_prazo_ou_vista_ElaboracaoCadastro").value = ed.tipo_venda_prazo_ou_vista_ElaboracaoCadastro || "";
  document.getElementById("limite_credito_ElaboracaoCadastro").value = ed.limite_credito_ElaboracaoCadastro || "";
  document.getElementById("data_vencimento_ElaboracaoCadastro").value = ed.data_vencimento_ElaboracaoCadastro || "";

  // Bloco: grupo_economico
  const grupo = dados.grupo_economico || {};
  document.getElementById("codigo_ElaboracaoCadastro").value = grupo.codigo_ElaboracaoCadastro || "";
  document.getElementById("nome_empresarial_ElaboracaoCadastro").value = grupo.nome_empresarial_ElaboracaoCadastro || "";

  // Bloco: referencia_comercial
  const refcom = dados.referencia_comercial || {};
  document.getElementById("empresa_ElaboracaoCadastro").value = refcom.empresa_ElaboracaoCadastro || "";
  document.getElementById("cidade_ElaboracaoCadastro").value = refcom.cidade_ElaboracaoCadastro || "";
  document.getElementById("telefone_ElaboracaoCadastro").value = refcom.telefone_ElaboracaoCadastro || "";
  document.getElementById("contato_ElaboracaoCadastro").value = refcom.contato_ElaboracaoCadastro || "";

  // Bloco: referencia_bancaria
  const refbanco = dados.referencia_bancaria || {};
  document.getElementById("banco_ElaboracaoCadastro").value = refbanco.banco_ElaboracaoCadastro || "";
  document.getElementById("agencia_ElaboracaoCadastro").value = refbanco.agencia_ElaboracaoCadastro || "";
  document.getElementById("conta_corrente_ElaboracaoCadastro").value = refbanco.conta_corrente_ElaboracaoCadastro || "";

  // Bloco: bem_imovel
  const imovel = dados.bem_imovel || {};
  document.getElementById("imovel_ElaboracaoCadastro").value = imovel.imovel_ElaboracaoCadastro || "";
  document.getElementById("localizacao_ElaboracaoCadastro").value = imovel.localizacao_ElaboracaoCadastro || "";
  document.getElementById("area_ElaboracaoCadastro").value = imovel.area_ElaboracaoCadastro || "";
  document.getElementById("valor_ElaboracaoCadastro").value = imovel.valor_ElaboracaoCadastro || "";
  document.getElementById("hipotecado_ElaboracaoCadastro").value = imovel.hipotecado_ElaboracaoCadastro || "";

  // Bloco: bem_movel
  const movel = dados.bem_movel || {};
  document.getElementById("marca_ElaboracaoCadastro").value = movel.marca_ElaboracaoCadastro || "";
  document.getElementById("modelo_ElaboracaoCadastro").value = movel.modelo_ElaboracaoCadastro || "";
  document.getElementById("alienado_ElaboracaoCadastro").value = movel.alienado_ElaboracaoCadastro || "";

  // Bloco: plantel_animal
  const plantel = dados.plantel_animal || {};
  document.getElementById("especie_ElaboracaoCadastro").value = plantel.especie_ElaboracaoCadastro || "";
  document.getElementById("numero_de_animais_ElaboracaoCadastro").value = plantel.numero_de_animais_ElaboracaoCadastro || "";
  document.getElementById("consumo_diario_ElaboracaoCadastro").value = plantel.consumo_diario_ElaboracaoCadastro || "";
  document.getElementById("consumo_mensal_ElaboracaoCadastro").value = plantel.consumo_mensal_ElaboracaoCadastro || "";

  // Bloco: supervisores
  const sup = dados.supervisores || {};
  document.getElementById("codigo_insumo_ElaboracaoCadastro").value = sup.codigo_insumo_ElaboracaoCadastro || "";
  document.getElementById("nome_insumos_ElaboracaoCadastro").value = sup.nome_insumos_ElaboracaoCadastro || "";
  document.getElementById("codigo_pet_ElaboracaoCadastro").value = sup.codigo_pet_ElaboracaoCadastro || "";
  document.getElementById("nome_pet_ElaboracaoCadastro").value = sup.nome_pet_ElaboracaoCadastro || "";

  // Bloco: comissao_dispet
  const com = dados.comissao_dispet || {};
  document.getElementById("insumos_ElaboracaoCadastro").value = com.insumos_ElaboracaoCadastro || "";
  document.getElementById("pet_ElaboracaoCadastro").value = com.pet_ElaboracaoCadastro || "";
  document.getElementById("observacoes_ElaboracaoCadastro").value = com.observacoes_ElaboracaoCadastro || "";
}

function novoCliente() {
  document.getElementById("formCliente").reset();
  document.getElementById("id").value = "";
  document.getElementById("ativo").checked = true;
}

async function salvarCliente() {
  const dados = obterDadosFormulario();
  const id = dados?.cadastrocliente?.codigo_da_empresa;
  const metodo = id ? "PUT" : "POST";
  const url = id ? `${API_URL}/${id}` : API_URL;

  try {
    const res = await fetch(url, {
      method: metodo,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados)
    });

    if (!res.ok) throw new Error(`Erro ${res.status}`);
    alert("Cliente salvo com sucesso!");
    preencherFormularioCliente(dados); // modo leitura
  } catch (e) {
    alert("Erro ao salvar cliente.");
    console.error(e);
  }
}

async function excluirCliente() {
  const codigo = document.getElementById("codigo_da_empresa").value;
  if (!codigo || !confirm("Deseja excluir o cliente?")) return;

  try {
    const res = await fetch(`${API_URL}/${codigo}`, { method: "DELETE" });
    if (!res.ok) throw new Error(`Erro ${res.status}`);
    alert("Cliente excluído.");
    novoCliente();
  } catch (e) {
    alert("Erro ao excluir.");
    console.error(e);
  }
}

function editarCliente() {
  preencherFormularioCliente(clienteOriginal, true);
}

function cancelarEdicao() {
  preencherFormularioCliente(clienteOriginal, false);
}

function listarClientes() {
  window.open("modal_clientes.html", "popup", "width=800,height=600");
}

function openTab(event, tabName) {
  const tabs = document.querySelectorAll('.tab-content');
  tabs.forEach(tab => tab.style.display = 'none');

  const buttons = document.querySelectorAll('.tab');
  buttons.forEach(btn => btn.classList.remove('active'));

  const selectedTab = document.getElementById(tabName);
  if (selectedTab) selectedTab.style.display = 'block';

  event.currentTarget.classList.add('active');
}


// Disponibiliza globalmente para o modal chamar
window.preencherFormulario = preencherFormularioCliente;
window.salvarCliente = salvarCliente;
window.excluirCliente = excluirCliente;
window.editarCliente = editarCliente;
window.cancelarEdicao = cancelarEdicao;
window.listarClientes = listarClientes;
"""
backend/services/excel_supra_service.py
Preenche o template XLSX da Alisul com os dados do cliente e retorna bytes.
Refatoração Sênior: Tratamento de exceções, formatação padronizada e logs.
"""
import io
import os
import logging
import unicodedata
from datetime import datetime
from pathlib import Path
import openpyxl
from openpyxl.styles import Font

# Configuração de Logs para auditoria
logger = logging.getLogger("ordersync.excel_supra")

# Tenta carregar do ENV ou usa o caminho relativo ao projeto (Seguro para o Render)
TEMPLATE_PATH_DEFAULT = Path(__file__).resolve().parent.parent / "assets" / "template_supra.xlsx"
TEMPLATE_PATH = Path(os.getenv("SUPRA_TEMPLATE_PATH", str(TEMPLATE_PATH_DEFAULT)))

# Mapeamento de Finalidade por Tipo de Cliente (Linha 42)
FINALIDADE_MAP = {
    "produtor rural": "Produtor Rural = (Vai Usar na Pecuaria ou Consumo Proprio)",
    "revenda": "Lojista = (Produto para Comercializar / Revender)",
    "consumidor final pf": "Consumidor Final - Pessoa Fisica = (Consumo Proprio)",
    "consumidor final pj": "Consumidor Final - Pessoa Juridica = (Consumo Proprio)",
}


def _br_number(value, decimals=2) -> str:
    """Formata número no padrão brasileiro (1.234,56)."""
    if value is None:
        return "0,00"
    try:
        value = float(value)
        return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "0,00"


def _s(value, default="") -> str:
    """Converte valor para string segura, tratando nulos."""
    if value is None:
        return default
    return str(value).strip()


def _normalize(text: str) -> str:
    """Remove acentos e converte para lowercase."""
    normalized = unicodedata.normalize('NFD', text)
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn').lower().strip()


def gerar_nome_arquivo(cliente) -> str:
    """
    Gera o nome do arquivo no padrão: Cidade_NomeDoCliente
    Sem extensão (adicionada pelo router).
    """
    cidade = _s(getattr(cliente, 'faturamento_municipio', '')) or "SemCidade"
    nome = _s(getattr(cliente, 'cadastro_nome_cliente', '')) or "SemNome"
    # Limpa caracteres especiais para nome de arquivo
    cidade_safe = cidade.replace(" ", "_").replace("/", "-")
    nome_safe = nome.replace(" ", "_").replace("/", "-")
    return f"{cidade_safe}_{nome_safe}"


def gerar_excel_cliente_supra(cliente) -> bytes:
    """
    Recebe o objeto ClienteModelV2 e gera o xlsx preenchido.
    Lança exceção amigável em caso de falha no template ou IO.
    """
    logger.info(f"Iniciando geração de Excel para cliente ID: {cliente.id} (Cód: {cliente.cadastro_codigo_da_empresa})")
    
    if not TEMPLATE_PATH.exists():
        msg = f"ERRO CRÍTICO: Template não encontrado em {TEMPLATE_PATH}. Verifique se o arquivo existe e se o backend tem permissão de leitura."
        logger.error(msg)
        raise FileNotFoundError(msg)

    try:
        # Abrir em modo leitura primeiro para testar acesso
        with open(TEMPLATE_PATH, "rb") as f:
            pass
        
        # Carregar Workbook
        wb = openpyxl.load_workbook(str(TEMPLATE_PATH))
        logger.info("Template carregado com sucesso.")
    except PermissionError:
        msg = f"ERRO DE PERMISSÃO: O arquivo {TEMPLATE_PATH} pode estar aberto em outro programa. Feche o Excel e tente novamente."
        logger.error(msg)
        raise RuntimeError(msg)
    except Exception as e:
        msg = f"ERRO INESPERADO ao carregar template: {str(e)}"
        logger.error(msg, exc_info=True)
        raise RuntimeError(msg)

    try:
        # =========================================================
        # ABA 1: Cadastro Parte 1
        # =========================================================
        ws1 = wb["Cadastro Parte 1"]

        # --- Identificação ---
        ws1["A8"] = f"Nome do Cliente:  {_s(cliente.cadastro_nome_cliente)}"
        ws1["A9"] = f"Denominação Comercial/Fantasia:   {_s(cliente.cadastro_nome_fantasia)}"

        # Contatos Responsável
        celular = _s(getattr(cliente, 'compras_celular_responsavel', ''))
        telefone = _s(getattr(cliente, 'compras_telefone_fixo_responsavel', ''))
        email    = _s(getattr(cliente, 'compras_email_resposavel', ''))
        ws1["A10"] = f"Telefone:  {telefone}"
        ws1["A11"] = f"Celular:  {celular}"
        ws1["E11"] = f"E-mail:  {email}"

        # Documentos
        ws1["A12"] = f"CNPJ:  {_s(cliente.cadastro_cnpj)}"
        ws1["A13"] = f"CPF:    {_s(cliente.cadastro_cpf)}"
        ws1["E13"] = f"INSCR.  ESTADUAL:  {_s(cliente.cadastro_inscricao_estadual)}"

        # Lógica de Checkboxes (Tipo de Cliente)
        tipo = _normalize(_s(cliente.cadastro_tipo_cliente))
        
        tipo_map = [
            (["revendedor", "revenda"], "C17"),
            (["atacado", "atacadista"], "E18"),
            (["direto"], "E17"),
            (["pequeno"], "G18"),
            (["redes", "rede"], "G17"),
            (["pet shop", "petshop", "pet"], "I18"),
            (["clinica", "vet"], "I17"),
            (["lojista", "loja"], "C18")
        ]
        
        for chaves, coord in tipo_map:
            if any(k in tipo for k in chaves):
                orig = ws1[coord].value or ""
                if "(XX)" not in str(orig):
                    ws1[coord] = f"{str(orig).split(':')[0]}:  (XX)"
                break

        # --- Endereços (Entrega e Cobrança) ---
        ws1["A21"] = f"Av./Rua/Nro:  {_s(cliente.entrega_endereco)}"
        ws1["I21"] = f"CEP:  {_s(cliente.entrega_cep)}"
        ws1["A22"] = f"Bairro:  {_s(cliente.entrega_bairro)}"
        ws1["F22"] = f"Cidade:  {_s(cliente.entrega_municipio)}"
        ws1["I22"] = f"Estado:  {_s(cliente.entrega_estado)}"

        ws1["A25"] = f"Av./Rua/Nro:  {_s(cliente.cobranca_endereco)}"
        ws1["I25"] = f"CEP:  {_s(cliente.cobranca_cep)}"
        ws1["A26"] = f"Bairro:  {_s(cliente.cobranca_bairro)}"
        ws1["F26"] = f"Cidade:   {_s(cliente.cobranca_municipio)}"
        ws1["I26"] = f"Estado:   {_s(cliente.cobranca_estado)}"

        # --- C/Vendas e P/Cobranças ---
        ws1["A29"] = f"C/Vendas:  {_s(getattr(cliente, 'compras_nome_responsavel', ''))}"
        ws1["F29"] = f"Telefones:  {_s(getattr(cliente, 'compras_celular_responsavel', ''))}"
        ws1["A30"] = f"P/Cobranças:  {_s(getattr(cliente, 'cobranca_resp_nome', ''))}"
        ws1["F30"] = f"Telefones:  {_s(getattr(cliente, 'cobranca_resp_celular', ''))}"

        # --- Referências e Bancos ---
        refs_bancarias = cliente.referencias_bancarias if isinstance(cliente.referencias_bancarias, list) else []
        for i, ref_b in enumerate(refs_bancarias[:4]):
            if not isinstance(ref_b, dict): continue
            row = 34 + i
            ws1[f"A{row}"] = _s(ref_b.get("banco"))
            ws1[f"C{row}"] = _s(ref_b.get("agencia"))
            ws1[f"E{row}"] = _s(ref_b.get("conta_corrente"))

        refs_comerciais = cliente.referencias_comerciais if isinstance(cliente.referencias_comerciais, list) else []
        for i, ref_c in enumerate(refs_comerciais[:4]):
            if not isinstance(ref_c, dict): continue
            row = 40 + i
            ws1[f"A{row}"] = _s(ref_c.get("empresa"))
            ws1[f"E{row}"] = _s(ref_c.get("cidade"))
            ws1[f"G{row}"] = _s(ref_c.get("telefone"))
            ws1[f"I{row}"] = _s(ref_c.get("contato"))

        # --- Bens Imóveis e Móveis ---
        bens_imoveis = cliente.bens_imoveis if isinstance(cliente.bens_imoveis, list) else []
        for i, bem_i in enumerate(bens_imoveis[:3]):
            if not isinstance(bem_i, dict): continue
            row = 46 + i
            ws1[f"A{row}"] = _s(bem_i.get("imovel"))
            ws1[f"C{row}"] = _s(bem_i.get("localizacao"))
            ws1[f"F{row}"] = _s(bem_i.get("area"))
            ws1[f"H{row}"] = bem_i.get("valor") or 0
            ws1[f"J{row}"] = _s(bem_i.get("hipotecado"))

        bens_moveis = cliente.bens_moveis if isinstance(cliente.bens_moveis, list) else []
        for i, bem_m in enumerate(bens_moveis[:3]):
            if not isinstance(bem_m, dict): continue
            row = 57 + i
            ws1[f"A{row}"] = _s(bem_m.get("marca"))
            ws1[f"E{row}"] = _s(bem_m.get("modelo"))
            ws1[f"G{row}"] = bem_m.get("valor") or 0
            # Converte alienado para "Sim" ou "Não" independente do formato original
            alienado_raw = bem_m.get("alienado")
            if isinstance(alienado_raw, bool):
                alienado_str = "Sim" if alienado_raw else "Não"
            elif isinstance(alienado_raw, str):
                alienado_str = "Sim" if alienado_raw.lower() in ("sim", "true", "1", "s", "yes") else "Não"
            else:
                alienado_str = "Não"
            ws1[f"I{row}"] = alienado_str

        # --- Plantel ---
        planteis = cliente.planteis_animais if isinstance(cliente.planteis_animais, list) else []
        for i, plantel in enumerate(planteis[:3]):
            if not isinstance(plantel, dict): continue
            row = 51 + i
            ws1[f"A{row}"] = _s(plantel.get("especie"))
            ws1[f"F{row}"] = plantel.get("numero_de_animais") or 0
            ws1[f"H{row}"] = plantel.get("consumo_diario") or 0
            ws1[f"J{row}"] = plantel.get("consumo_mensal") or 0

        # --- Local e Data (Cidade do Cliente + Data Atual) ---
        cidade_cliente = _s(cliente.faturamento_municipio)
        ws1["C61"] = f"{cidade_cliente}, {datetime.now().strftime('%d/%m/%Y')}"

        # =========================================================
        # ABA 2: Uso Interno
        # =========================================================
        ws2 = wb["Cadastro Parte 2"]
        ws2["E7"] = _s(cliente.cadastro_nome_cliente)
        ws2["E8"] = _s(cliente.cadastro_nome_fantasia)

        # Canais Segmentados
        ws2["C14"] = _s(cliente.canal_pet)
        ws2["C15"] = _s(cliente.canal_frost)
        ws2["C16"] = _s(cliente.canal_insumos)

        # Comissões — texto padrão em vermelho
        _DISPET_RED = Font(color="FF0000")
        cell_pet    = ws2["C20"]
        cell_ins    = ws2["C21"]
        cell_pet.value = _s(cliente.comissao_pet)
        cell_ins.value = _s(cliente.comissao_insumos)
        cell_pet.font  = _DISPET_RED
        cell_ins.font  = _DISPET_RED

        # Supervisores — Nome (linha 25) e Código (linha 26)
        ws2["E25"] = _s(cliente.supervisor_nome_pet)
        ws2["H25"] = _s(cliente.supervisor_nome_insumo)
        ws2["E26"] = _s(getattr(cliente, 'supervisor_codigo_pet', ''))
        ws2["H26"] = _s(getattr(cliente, 'supervisor_codigo_insumo', ''))

        # Gerentes — Insumos e Pet (novas linhas no template)
        ws2["E27"] = _s(getattr(cliente, 'elaboracao_gerente_pet', ''))
        ws2["H27"] = _s(getattr(cliente, 'elaboracao_gerente_insumos', ''))

        # Financeiro e Recomendações
        ws2["D35"] = cliente.elaboracao_limite_credito or 0

        # --- LINHA 41: Status do Cliente (Lógica de Classificação) ---
        codigo_empresa = _s(cliente.cadastro_codigo_da_empresa)
        cliente_inativo = not cliente.cadastro_ativo if cliente.cadastro_ativo is not None else False

        if not codigo_empresa:
            status_text = "Cliente Novo"
        elif cliente_inativo:
            status_text = f"Recadastro do Cliente Código => {codigo_empresa}"
        else:
            status_text = _s(cliente.elaboracao_classificacao) or "CLIENTE NOVO"
        ws2["A41"] = status_text

        # --- LINHA 42: Mapeamento de Finalidade por Tipo de Cliente ---
        tipo_raw = _normalize(_s(cliente.cadastro_tipo_cliente))
        finalidade = FINALIDADE_MAP.get(tipo_raw, "")
        ws2["A42"] = finalidade

        # --- LINHA 43: Tipo de Venda (mapeamento de pagamento) ---
        tipo_venda_raw = _normalize(_s(cliente.elaboracao_tipo_venda))
        if "vista" in tipo_venda_raw:
            tipo_venda_excel = "Venda à vista"
        elif "prazo" in tipo_venda_raw:
            tipo_venda_excel = "Venda antecipada"
        else:
            tipo_venda_excel = _s(cliente.elaboracao_tipo_venda) or "Venda a Prazo"
        ws2["A43"] = tipo_venda_excel

        # Garante que abra na primeira guia por padrão
        wb.active = 0

        # Exportação segura para buffer de memória
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.read()

    except Exception as e:
        logger.error(f"Erro durante preenchimento do Excel para cliente {cliente.id}: {e}")
        raise RuntimeError(f"Erro técnico ao processar os dados do cliente no Excel: {str(e)}")

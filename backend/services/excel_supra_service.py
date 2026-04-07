"""
backend/services/excel_supra_service.py
Preenche o template XLSX da Alisul com os dados do cliente e retorna bytes.
Refatoração Sênior: Tratamento de exceções, formatação padronizada e logs.
"""
import io
import os
import logging
from datetime import datetime
from pathlib import Path
import openpyxl

# Configuração de Logs para auditoria
logger = logging.getLogger("ordersync.excel_supra")

# Tenta carregar do ENV ou usa o caminho relativo ao projeto (Seguro para o Render)
TEMPLATE_PATH_DEFAULT = Path(__file__).resolve().parent.parent / "assets" / "template_supra.xlsx"
TEMPLATE_PATH = Path(os.getenv("SUPRA_TEMPLATE_PATH", str(TEMPLATE_PATH_DEFAULT)))


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
        tipo = _s(cliente.cadastro_tipo_cliente).lower()
        tipo_map = {
            "revendedor": "C17", "atacado": "E18", "cli direto": "E17",
            "pequeno": "G18", "redes": "G17", "pet shop": "I18",
            "clínica": "I17", "lojista": "C18",
        }
        for key, coord in tipo_map.items():
            if key in tipo:
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

        # --- Referências e Bens ---
        ref_b = cliente.referencias_bancarias[0] if cliente.referencias_bancarias else {}
        ws1["A34"] = _s(ref_b.get("banco"))
        ws1["C34"] = _s(ref_b.get("agencia"))
        ws1["E34"] = _s(ref_b.get("conta_corrente"))

        ref_c = cliente.referencias_comerciais[0] if cliente.referencias_comerciais else {}
        ws1["A40"] = _s(ref_c.get("empresa"))
        ws1["E40"] = _s(ref_c.get("cidade"))
        ws1["G40"] = _s(ref_c.get("telefone"))
        ws1["I40"] = _s(ref_c.get("contato"))

        bem_i = cliente.bens_imoveis[0] if cliente.bens_imoveis else {}
        ws1["A46"] = _s(bem_i.get("imovel"))
        ws1["H46"] = bem_i.get("valor") or 0
        ws1["J46"] = _s(bem_i.get("hipotecado"))

        # --- Plantel ---
        plantel = cliente.planteis_animais[0] if cliente.planteis_animais else {}
        ws1["A51"] = _s(plantel.get("especie"))
        ws1["F51"] = plantel.get("numero_de_animais") or 0
        ws1["H51"] = plantel.get("consumo_diario") or 0

        # --- Local e Data (Auditoria de Geração) ---
        cidade_fat = _s(cliente.faturamento_municipio) or "SÃO ROQUE"
        estado_fat = _s(cliente.faturamento_estado) or "SP"
        ws1["C61"] = f"{cidade_fat}/{estado_fat}, {datetime.now().strftime('%d/%m/%Y')}"

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

        # Comissões
        ws2["C20"] = _s(cliente.comissao_pet)
        ws2["C21"] = _s(cliente.comissao_insumos)

        # Supervisores
        ws2["E25"] = _s(cliente.supervisor_nome_pet)
        ws2["H25"] = _s(cliente.supervisor_nome_insumo)

        # Financeiro e Recomendações
        ws2["D35"] = cliente.elaboracao_limite_credito or 0
        ws2["A41"] = _s(cliente.elaboracao_classificacao) or "CLIENTE NOVO"
        ws2["A43"] = _s(cliente.elaboracao_tipo_venda) or "Venda a Prazo"

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

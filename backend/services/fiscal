# services/fiscal.py
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# =========================
# Helpers de arredondamento
# =========================
TWO = Decimal("0.01")

def D(x) -> Decimal:
    """Converte para Decimal de forma segura."""
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x)) if x is not None else Decimal("0")

def money(x: Decimal) -> Decimal:
    """Arredonda com HALF_UP para 2 casas."""
    return D(x).quantize(TWO, rounding=ROUND_HALF_UP)


# ==============
# Modelos (I/O)
# ==============
class ClienteInfo(BaseModel):
    codigo: Optional[int] = Field(default=None, description="Código do cliente (opcional em texto livre)")
    ramo_juridico: Optional[str] = Field(default=None, description="Ex.: 'Revenda', 'Consumidor Final'")

class ProdutoInfo(BaseModel):
    familia: Optional[str] = Field(default=None, description="Ex.: 'PET', 'RACAO', etc.")
    peso_kg: Optional[Decimal] = Field(default=None, description="Peso em kg da unidade comercializada")

class ParametrosFiscais(BaseModel):
    aliquota_ipi: Decimal = Field(default=Decimal("0.00"), description="Ex.: 0.065 para 6,5%")
    aliquota_icms: Decimal = Field(default=Decimal("0.18"), description="Ex.: 0.18 para 18%")
    iva_st: Decimal = Field(default=Decimal("0.00"), description="Ex.: 0.5834 para 58,34%")
    considerar_desconto_nas_bases: bool = Field(default=True, description="Se verdadeiro, desconto reduz bases de IPI/ICMS")
    frete_comp_bases: bool = Field(default=True, description="Se verdadeiro, frete compõe base IPI e ICMS")

class LinhaFiscalIn(BaseModel):
    cliente: ClienteInfo
    produto: ProdutoInfo
    parametros: ParametrosFiscais

    preco_unit: Decimal = Field(description="Preço unitário da mercadoria (sem impostos)")
    quantidade: Decimal = Field(description="Quantidade")
    desconto_linha: Decimal = Field(default=Decimal("0.00"), description="Desconto incondicional da linha")
    frete_linha: Decimal = Field(default=Decimal("0.00"), description="Frete rateado para a linha")

class LinhaFiscalOut(BaseModel):
    # Flags/regra
    aplica_iva_st: bool
    motivos_iva_st: List[str] = []

    # Componentes de mercadoria
    subtotal_mercadoria: Decimal

    # IPI
    base_ipi: Decimal
    ipi: Decimal

    # ICMS próprio
    base_icms_proprio: Decimal
    icms_proprio: Decimal

    # ICMS-ST
    base_st: Decimal
    icms_st_cheio: Decimal
    icms_st_reter: Decimal

    # Outros componentes declarados
    desconto_linha: Decimal
    frete_linha: Decimal

    # Política de composição do total
    composicao_total: Literal["A_inclui_IPI_e_ST", "B_inclui_somente_IPI"]

    # Totais
    total_linha: Decimal
    total_impostos_linha: Decimal


# ===========================
# Regras e cálculos principais
# ===========================
def _normaliza_txt(v: Optional[str]) -> str:
    return (v or "").strip().lower()

def aplica_regra_iva_st(ramo_juridico: Optional[str], familia: Optional[str], peso_kg: Optional[Decimal]) -> tuple[bool, List[str]]:
    """Regra pedida: produto família PET, peso < 10 kg e cliente 'Revenda'."""
    motivos: List[str] = []
    is_pet = _normaliza_txt(familia) == "pet"
    if is_pet:
        motivos.append("familia=PET")

    peso_ok = (peso_kg is not None) and (D(peso_kg) < D(10))
    if peso_ok:
        motivos.append("peso<10kg")

    is_revenda = _normaliza_txt(ramo_juridico) == "revenda"
    if is_revenda:
        motivos.append("cliente=Revenda")

    ok = is_pet and peso_ok and is_revenda
    return ok, motivos


def calcular_componentes_linha(
    entrada: LinhaFiscalIn,
    composicao_total: Literal["A_inclui_IPI_e_ST", "B_inclui_somente_IPI"] = "A_inclui_IPI_e_ST",
) -> LinhaFiscalOut:
    """
    Calcula os componentes fiscais e o total da linha.
    Política A: total = subtotal_mercadoria + frete + IPI + ICMS_ST_reter
    Política B: total = subtotal_mercadoria + frete + IPI
    (ICMS próprio nunca é somado ao total; é "por dentro")
    """
    p = entrada.parametros

    # Subtotal mercadoria (desconto reduz o subtotal; se considerar_desconto_nas_bases=True, reduzirá bases tb)
    preco_unit = D(entrada.preco_unit)
    qtd = D(entrada.quantidade)
    desconto = D(entrada.desconto_linha)
    frete = D(entrada.frete_linha)

    bruto = preco_unit * qtd
    subtotal_mercadoria = money(bruto - desconto)

    # Bases
    base_merc = subtotal_mercadoria if p.considerar_desconto_nas_bases else money(bruto)
    comp_frete = frete if p.frete_comp_bases else D(0)

    # IPI
    base_ipi = money(base_merc + comp_frete)
    ipi = money(base_ipi * p.aliquota_ipi)

    # ICMS próprio (sem IPI na base, segundo seu exemplo)
    base_icms_proprio = money(base_merc + comp_frete)
    icms_proprio = money(base_icms_proprio * p.aliquota_icms)

    # Regra IVA_ST
    aplica_st, motivos = aplica_regra_iva_st(
        entrada.cliente.ramo_juridico, entrada.produto.familia, entrada.produto.peso_kg
    )

    # ICMS-ST
    if aplica_st and p.iva_st > 0:
        base_st = money((base_merc + comp_frete + ipi) * (D(1) + p.iva_st))
        icms_st_cheio = money(base_st * p.aliquota_icms)
        icms_st_reter = money(icms_st_cheio - icms_proprio)
        # Nunca deixar ST negativa (pode ocorrer em margens pequenas)
        if icms_st_reter < 0:
            icms_st_reter = D(0)
    else:
        base_st = D(0)
        icms_st_cheio = D(0)
        icms_st_reter = D(0)

    # Composição do total (política)
    if composicao_total == "A_inclui_IPI_e_ST":
        total_linha = money(subtotal_mercadoria + frete + ipi + icms_st_reter)
    else:  # "B_inclui_somente_IPI"
        total_linha = money(subtotal_mercadoria + frete + ipi)

    total_impostos = money(ipi + icms_st_reter)  # se quiser incluir outros, ajustar aqui

    return LinhaFiscalOut(
        aplica_iva_st=aplica_st,
        motivos_iva_st=motivos,
        subtotal_mercadoria=subtotal_mercadoria,
        base_ipi=base_ipi,
        ipi=ipi,
        base_icms_proprio=base_icms_proprio,
        icms_proprio=icms_proprio,
        base_st=base_st,
        icms_st_cheio=icms_st_cheio,
        icms_st_reter=icms_st_reter,
        desconto_linha=money(desconto),
        frete_linha=money(frete),
        composicao_total=composicao_total,
        total_linha=total_linha,
        total_impostos_linha=total_impostos,
    )

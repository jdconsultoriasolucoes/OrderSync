from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Tuple, List

TWO = Decimal("0.01")

def D(x) -> Decimal:
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x)) if x is not None else Decimal("0")

def money(x) -> Decimal:
    return D(x).quantize(TWO, rounding=ROUND_HALF_UP)

def _norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()

def decide_st(
    tipo: Optional[str],
    tipo_cliente: Optional[str],
    forcar_iva_st: bool
) -> Tuple[bool, List[str]]:
    motivos: List[str] = []

    # normaliza tudo para comparação
    is_pet = _norm(tipo) == "pet" or _norm(tipo) == "insumos"
    if is_pet:
        motivos.append(f"tipo={tipo}")

    is_revenda = _norm(tipo_cliente) == "revenda"   # <<--- usar lower-case
    if is_revenda:
        motivos.append("cliente=Revenda")

    # Se forçar via UI e cliente NÃO cadastrado: ainda exige que o produto
    
    if forcar_iva_st and not tipo_cliente:
        aplica_forcado = is_pet
        if aplica_forcado:
            motivos.extend(["forcado_ui", "cliente_sem_cadastro"])
        else:
            motivos.append("forcado_ui_invalido")  # ajuda no debug
        return aplica_forcado, motivos

    aplica = is_pet and is_revenda
    return aplica, motivos

def calcular_linha(
    preco_unit: Decimal,
    quantidade: Decimal,
    desconto_linha: Decimal,
    frete_linha: Decimal,
    ipi: Decimal,          # alíquota de IPI (ex.: 0.065)
    icms: Decimal,         # alíquota de ICMS (ex.: 0.18)
    iva_st: Decimal,       # margem ST do produto (ex.: 0.5834)
    aplica_st: bool
) -> dict:
    """
    Bases segundo o que você pediu:
    - vl_mercadoria = (preço * qtd) - desconto
    - base IPI = vl_mercadoria + frete
    - base ICMS próprio = vl_mercadoria + frete   (sem IPI na base)
    - base ST = (vl_mercadoria + frete + IPI) * (1 + IVA_ST)  [se aplica ST]
    Totais:
    - total_sem_st = vl_mercadoria + frete + IPI
    - total_com_st = total_sem_st + ICMS_ST_reter
    """
    bruto = D(preco_unit) * D(quantidade)
    subtotal = money(bruto - D(desconto_linha))

    base_ipi = money(subtotal + D(frete_linha))
    valor_ipi = money(base_ipi * D(ipi))

    base_icms = money(subtotal + D(frete_linha))
    icms_proprio = money(base_icms * D(icms))

    if aplica_st and D(iva_st) > 0:
        base_st = money((subtotal + D(frete_linha) + valor_ipi) * (D(1) + D(iva_st)))
        icms_st_cheio = money(base_st * D(icms))
        icms_st_reter = money(icms_st_cheio - icms_proprio)
        if icms_st_reter < 0:
            icms_st_reter = D(0)
    else:
        base_st = D(0)
        icms_st_cheio = D(0)
        icms_st_reter = D(0)

    total_sem_st = money(subtotal + D(frete_linha) + valor_ipi)
    total_com_st = money(total_sem_st + icms_st_reter)

    return {
        "subtotal": subtotal,
        "base_ipi": base_ipi,
        "ipi": valor_ipi,
        "base_icms": base_icms,
        "icms_proprio": icms_proprio,
        "base_st": base_st,
        "icms_st_cheio": icms_st_cheio,
        "icms_st_reter": icms_st_reter,
        "total_sem_st": total_sem_st,
        "total_com_st": total_com_st,
        "total_impostos": money(valor_ipi + icms_st_reter),
    }

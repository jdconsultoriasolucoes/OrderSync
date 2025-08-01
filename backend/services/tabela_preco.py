from typing import List, Dict

def calcular_valor_liquido(valor: float, plano_percentual: float, fator_comissao: float) -> dict:
    """
    Calcula os valores de acréscimo, desconto e valor líquido para um produto.
    """
    acrescimo = valor * plano_percentual
    desconto = valor * fator_comissao
    valor_liquido = valor + acrescimo - desconto

    return {
        "acrescimo": round(acrescimo, 4),
        "desconto": round(desconto, 4),
        "valor_liquido": round(valor_liquido, 2)
    }


def aplicar_regra_em_lote(produtos: list, plano_percentual: float, fator_comissao: float, frete_kg: float, fornecedor: str) -> list:
    """
    Aplica o cálculo de valores em todos os produtos retornados do banco,
    atualizando os campos necessários com base nas regras de negócio.
    """
    resultado = []

    for p in produtos:
        calculo = calcular_valor_liquido(p["valor"], plano_percentual, fator_comissao)

        resultado.append({
            **p,
            "acrescimo": calculo["acrescimo"],
            "desconto": calculo["desconto"],
            "valor_liquido": calculo["valor_liquido"],
            "frete_kg": frete_kg,
            "fator_comissao": fator_comissao,
            "fornecedor": fornecedor,
        })

    return resultado
from typing import List
from schemas.tabela_preco import ParametrosCalculo, ProdutoCalculado


def calcular_valores_dos_produtos(payload: ParametrosCalculo) -> List[ProdutoCalculado]:
    resultado = []

    for produto in payload.produtos:
        valor = produto.valor
        peso = produto.peso_liquido or 0.0
        is_pet = (str(produto.tipo or "").strip().lower() == "pet")
        ipi_item = (produto.ipi or 0.0) if (is_pet and peso <= 10) else 0.0
        
        
        iva_st = produto.iva_st or 0.0

        frete_kg = (payload.frete_unitario / 1000) * peso
        ajuste_pagamento = valor * payload.acrescimo_pagamento
        comissao_aplicada = valor * payload.fator_comissao

        base = valor + frete_kg + ajuste_pagamento - comissao_aplicada 
        valor_liquido = base + ((base * ipi_item) + (base * iva_st))

        resultado.append(ProdutoCalculado(
            **produto.dict(),
            frete_kg=round(frete_kg, 4),
            ajuste_pagamento=round(ajuste_pagamento, 4),
            comissao_aplicada=round(comissao_aplicada, 4),
            valor_liquido=round(valor_liquido, 2),
            ))

    return resultado

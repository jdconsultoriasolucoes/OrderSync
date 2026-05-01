import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from models.background_task import BackgroundTaskModel
from models.produto import ProdutoV2, ImpostoV2
from models.tabela_preco import TabelaPreco
from services.fiscal import calcular_linha

logger = logging.getLogger("worker_recalculo")

def processar_recalculo_massivo(db: Session, task: BackgroundTaskModel, codigos_alterados: List[str]):
    if not codigos_alterados:
        task.status = "CONCLUIDO"
        task.progresso = 100
        task.mensagem_status = "Nenhum produto alterado."
        db.commit()
        return

    try:
        task.status = "PROCESSANDO"
        task.mensagem_status = "Identificando tabelas de preço impactadas..."
        db.commit()

        # Encontrar todas as tabelas (id_tabela) que possuem algum dos produtos alterados
        # e que estão ativas
        tabelas_afetadas = db.query(TabelaPreco.id_tabela).filter(
            TabelaPreco.codigo_produto_supra.in_(codigos_alterados),
            TabelaPreco.ativo == True
        ).distinct().all()

        ids_tabelas = [t[0] for t in tabelas_afetadas]
        total_tabelas = len(ids_tabelas)

        task.total_passos = total_tabelas
        task.mensagem_status = f"Encontradas {total_tabelas} tabelas afetadas."
        db.commit()

        if total_tabelas == 0:
            task.status = "CONCLUIDO"
            task.progresso = 100
            db.commit()
            return

        passos_concluidos = 0

        # Para otimizar, pré-carregar os dados completos (produto + impostos) dos códigos alterados
        produtos_db = db.query(ProdutoV2).filter(ProdutoV2.codigo_supra.in_(codigos_alterados)).all()
        produtos_map = {p.codigo_supra: p for p in produtos_db}

        # Carregar impostos
        impostos_db = db.query(ImpostoV2).filter(ImpostoV2.produto_id.in_([p.id for p in produtos_db])).all()
        impostos_map = {imp.produto_id: imp for imp in impostos_db}

        # Itera tabela por tabela
        for id_tabela in ids_tabelas:
            # Buscar todas as linhas dessa tabela que são de produtos alterados
            linhas = db.query(TabelaPreco).filter(
                TabelaPreco.id_tabela == id_tabela,
                TabelaPreco.codigo_produto_supra.in_(codigos_alterados),
                TabelaPreco.ativo == True
            ).all()

            for row in linhas:
                produto = produtos_map.get(row.codigo_produto_supra)
                if not produto:
                    continue

                imposto = impostos_map.get(produto.id)
                tax_ipi = imposto.ipi if imposto else 0.0
                tax_icms = imposto.icms if imposto else 0.0
                tax_iva_st = imposto.iva_st if imposto else 0.0

                # 1. Derivar Fatores antigos
                valor_antigo = float(row.valor_produto)
                comissao_antiga = float(row.comissao_aplicada)
                ajuste_antigo = float(row.ajuste_pagamento)

                fator_comissao = (comissao_antiga / valor_antigo) if valor_antigo > 0 else 0.0
                liquido_antigo = max(0, valor_antigo - comissao_antiga)
                taxa_condicao = (ajuste_antigo / liquido_antigo) if liquido_antigo > 0 else 0.0

                # 2. Dados novos
                novo_valor = float(produto.preco or 0)
                peso_bruto = float(produto.peso_bruto or 0)
                peso_liquido_prod = float(produto.peso or 0)
                peso_para_frete = peso_bruto if peso_bruto > 0 else peso_liquido_prod
                if peso_para_frete <= 0:
                    peso_para_frete = float(row.peso_liquido)

                # 3. Lógica Comercial
                nova_comissao = novo_valor * fator_comissao
                novo_liquido = max(0, novo_valor - nova_comissao)
                novo_ajuste = novo_liquido * taxa_condicao
                preco_fiscal_unit = novo_liquido + novo_ajuste
                
                # O frete aplicado (R$) NÃO deve ser alterado durante o processo de atualização de preços.
                # Lemos o valor que já está persistido na linha para usá-lo como base nos cálculos fiscais (ST).
                frete_total = float(row.valor_frete_aplicado or 0)

                # 4. Lógica Fiscal
                res_fiscal = calcular_linha(
                    preco_unit=preco_fiscal_unit,
                    quantidade=1,
                    desconto_linha=0,
                    frete_linha=frete_total,
                    ipi=tax_ipi,
                    icms=tax_icms,
                    iva_st=tax_iva_st,
                    aplica_st=row.calcula_st
                )

                # 5. Lógica de Markup
                markup_pct = float(row.markup or 0)
                factor = 1.0 + (markup_pct / 100.0)
                
                total_fiscal = float(res_fiscal["total_com_st"])
                total_comercial = total_fiscal # mesmo valor em js
                total_sem_frete = max(0, total_comercial - frete_total)

                val_fin_mk = round(total_comercial * factor, 2)
                val_sem_mk = round(total_sem_frete * factor, 2)

                # 6. Atualizar Linha
                row.valor_produto = novo_valor
                row.peso_liquido = peso_liquido_prod if peso_liquido_prod > 0 else row.peso_liquido
                row.comissao_aplicada = nova_comissao
                row.ajuste_pagamento = novo_ajuste
                # row.valor_frete_aplicado = round(frete_total, 2) # REMOVIDO: Não alterar o frete durante atualização de preços
                
                # Campos de totais compatíveis com tela
                row.valor_frete = round(total_comercial, 2)  # na verdade guarda o total com ST (JS: item._totalComercial)
                row.valor_s_frete = round(total_sem_frete, 2)

                row.ipi = float(res_fiscal["ipi"]) # Valor em R$
                row.icms_st = float(res_fiscal["icms_proprio"]) # Legado JS
                row.iva_st = float(res_fiscal["base_st"]) # Legado JS

                row.valor_final_markup = val_fin_mk
                row.valor_s_frete_markup = val_sem_mk

            db.commit() # commita a cada tabela para não perder progresso

            passos_concluidos += 1
            task.progresso = int((passos_concluidos / total_tabelas) * 100)
            task.mensagem_status = f"Recalculadas {passos_concluidos} de {total_tabelas} tabelas."
            db.commit()

        task.status = "CONCLUIDO"
        task.progresso = 100
        task.mensagem_status = "Recálculo massivo concluído com sucesso."
        db.commit()

    except Exception as e:
        logger.exception("Erro no recálculo massivo")
        db.rollback()
        task.status = "ERRO"
        task.erro = str(e)
        task.mensagem_status = f"Falha: {str(e)[:100]}"
        db.commit()

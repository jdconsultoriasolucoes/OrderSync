import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from models.background_task import BackgroundTaskModel
from models.produto import ProdutoV2, ImpostoV2
from models.tabela_preco import TabelaPreco
from services.fiscal import calcular_linha
from services.tabela_preco import cliente_calcula_st

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

        # Carregar flags de ST de todos os clientes cadastrados para otimizar
        clientes_db = db.execute(text("""
            SELECT cadastro_codigo_da_empresa as codigo_cliente, 
                   ultimas_compras_cliente_calcula_st as calcula_st_flag,
                   cadastro_tipo_cliente as ramo
            FROM t_cadastro_cliente_v2
        """)).mappings().all()
        
        clientes_st_map = {}
        for c in clientes_db:
            cod = str(c["codigo_cliente"]).strip()
            flag = str(c["calcula_st_flag"] or "").strip().upper()
            ramo = str(c["ramo"] or "").strip().upper()
            
            calcs_st = False
            if flag in ["SIM", "YES", "TRUE", "S", "1"]:
                calcs_st = True
            elif flag in ["NAO", "NO", "FALSE", "N", "0"]:
                calcs_st = False
            elif "REVENDA" in ramo or "DISTRIBUIDORA" in ramo:
                calcs_st = True
                
            clientes_st_map[cod] = calcs_st

        # Carregar condições de pagamento (taxas) para mapeamento direto de juros/ajuste
        condicoes_db = db.execute(text("""
            SELECT codigo_prazo, custo as taxa_condicao
            FROM t_condicoes_pagamento
            WHERE ativo IS TRUE
        """)).mappings().all()
        
        mapa_condicoes = {}
        for row_c in condicoes_db:
            cod = str(row_c["codigo_prazo"]).strip().upper()
            mapa_condicoes[cod] = float(row_c["taxa_condicao"] or 0.0)

        # Carregar descontos/fatores de comissão ativos
        descontos_db = db.execute(text("""
            SELECT id_desconto, fator_comissao
            FROM t_desconto
            WHERE ativo IS TRUE
        """)).mappings().all()

        mapa_descontos = {}
        for row_d in descontos_db:
            cod = str(row_d["id_desconto"]).strip().upper()
            mapa_descontos[cod] = float(row_d["fator_comissao"] or 0.0)

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

                # Mantém o calcula_st já salvo na tabela (preserva decisões manuais do vendedor)

                imposto = impostos_map.get(produto.id)
                tax_ipi = imposto.ipi if imposto else 0.0
                tax_icms = imposto.icms if imposto else 0.0
                tax_iva_st = imposto.iva_st if imposto else 0.0

                # 1. Derivar Fatores das colunas da própria linha de forma precisa
                valor_antigo = float(row.valor_produto)
                comissao_antiga = float(row.comissao_aplicada)
                ajuste_antigo = float(row.ajuste_pagamento)

                # --- DESCONTO / FATOR ---
                fator_comissao = None
                desc_fator_str = str(row.descricao_fator_comissao or "").strip()
                if desc_fator_str:
                    # Trata chaves compostas "CODIGO - DESC" ou apenas "CODIGO"
                    cod_desc = desc_fator_str.split(" - ")[0].strip().upper()
                    if cod_desc in mapa_descontos:
                        fator_comissao = mapa_descontos[cod_desc]
                    elif desc_fator_str.upper() in mapa_descontos:
                        fator_comissao = mapa_descontos[desc_fator_str.upper()]

                # Fallback de segurança se não encontrar nos cadastros ativos
                if fator_comissao is None:
                    fator_comissao = (comissao_antiga / valor_antigo) if valor_antigo > 0 else 0.0

                # --- CONDIÇÃO DE PAGAMENTO ---
                taxa_condicao = None
                cod_plano_str = str(row.codigo_plano_pagamento or "").strip()
                if cod_plano_str:
                    # Trata chaves compostas "CODIGO - DESC" ou apenas "CODIGO"
                    cod_plano = cod_plano_str.split(" - ")[0].strip().upper()
                    if cod_plano in mapa_condicoes:
                        taxa_condicao = mapa_condicoes[cod_plano]
                    elif cod_plano_str.upper() in mapa_condicoes:
                        taxa_condicao = mapa_condicoes[cod_plano_str.upper()]

                # Se a condição de pagamento não existir ativamente, não atualizamos a linha (preserva o valor antigo)
                if taxa_condicao is None:
                    logger.warning(
                        f"Condicao de pagamento '{cod_plano_str}' nao encontrada ou inativa na tabela {id_tabela} "
                        f"para o produto {row.codigo_produto_supra}. Ignorando recálculo desta linha."
                    )
                    continue

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
                
                # O frete na linha (seja preenchido globalmente ou manualmente pelo usuário) sempre representa o valor por Tonelada.
                # Portanto, como o peso do produto pode ter sido atualizado no PDF, SEMPRE recalculamos o valor R$ (frete_total)
                frete_kg = float(row.frete_kg or 0)
                frete_total = (frete_kg / 1000.0) * peso_para_frete

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
                row.valor_frete_aplicado = round(frete_total, 4)
                
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

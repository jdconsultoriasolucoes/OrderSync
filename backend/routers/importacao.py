from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
import pandas as pd
import io
import unicodedata
import logging
from datetime import datetime

router = APIRouter(prefix="/api/importacao", tags=["Importacao"])
logger = logging.getLogger("ordersync.importacao")

def normalize_text(text_val):
    """Remove acentos, converte para minúsculas e remove espaços das extremidades."""
    if pd.isna(text_val) or text_val is None:
        return ""
    val_str = str(text_val)
    normalized = unicodedata.normalize('NFKD', val_str).encode('ascii', 'ignore').decode('utf-8')
    return normalized.lower().strip()

def clean_numeric_code(val):
    """Garante que códigos numéricos fiquem sem ponto decimal (ex: 237.001 ou 237001.0 -> 237001)."""
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).strip()
    if not val_str:
        return ""
    # Se terminar com .0 (padrão de leitura de floats no Pandas), remove
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    # Remove qualquer ponto restante (ex: 237.001)
    val_str = val_str.replace(".", "")
    return val_str

def normalizar_pedido_supra(pedido_supra_str: str, data_referencia=None) -> str:
    """
    Garante que o pedido_supra seja gravado no banco sempre com 10 dígitos (YYYY + 6 dígitos com zero padding).
    Ex: '2111' -> '2026002111' (usando o ano da data_referencia ou o ano atual do sistema).
    Ex: '2026002111' -> '2026002111' (mantém intacto).
    """
    if not pedido_supra_str:
        return ""
    
    # Remove qualquer caractere não numérico
    digits = "".join(filter(str.isdigit, str(pedido_supra_str)))
    if not digits:
        return ""
    
    # Se já tem 10 dígitos, retorna direto
    if len(digits) == 10:
        return digits
        
    # Se tiver menos que 10 dígitos (ex: 2111), completa com o ano
    # Determina o ano a partir da data de referência ou do ano atual do sistema local (2026)
    ano = "2026"
    if data_referencia:
        try:
            if hasattr(data_referencia, 'year'):
                ano = str(data_referencia.year)
            else:
                match = str(data_referencia).strip()[:4]
                if match.isdigit() and len(match) == 4:
                    ano = match
        except:
            pass
            
    # Limpa zeros à esquerda do sufixo para fazer o lpad correto de 6 dígitos
    sufixo = digits.lstrip('0')
    if not sufixo:
        sufixo = "0"
    
    # Trunca se passar de 6 dígitos
    if len(sufixo) > 6:
        sufixo = sufixo[-6:]
        
    return f"{ano}{sufixo.zfill(6)}"

def clean_currency(val):
    """
    Processa valores monetários suportando vírgula como separador decimal.
    Ex: 'R$ 1.500,50' ou '1500,50' ou 1500.5
    """
    if pd.isna(val) or val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    
    val_str = str(val).replace("R$", "").strip()
    if not val_str:
        return 0.0
        
    # Se houver vírgula, trata-se do padrão brasileiro onde a vírgula separa centavos.
    if "," in val_str:
        # 1.500,50 -> 1500,50 -> 1500.50
        val_str = val_str.replace(".", "").replace(",", ".")
        
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def find_column(df, keywords):
    """Busca o nome de uma coluna no dataframe baseada em keywords normalizadas."""
    for col in df.columns:
        norm_col = normalize_text(col)
        # Todas as palavras-chaves devem estar presentes na string normalizada
        if all(kw in norm_col for kw in keywords):
            return col
    return None

@router.post("/pedidos")
async def importar_pedidos_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.xlsm', '.xlsx')):
        raise HTTPException(status_code=400, detail="Formato de arquivo inválido. Apenas .xlsm ou .xlsx são suportados.")
    
    try:
        contents = await file.read()
        file_bytes = io.BytesIO(contents)
        
        # 1. Leitura das Abas
        try:
            df_bd = pd.read_excel(file_bytes, sheet_name="Banco_Dados", skiprows=1)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao ler a aba Banco_Dados: {e}")
            
        try:
            file_bytes.seek(0)
            df_danfes = pd.read_excel(file_bytes, sheet_name="Danfes")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao ler a aba Danfes: {e}")
            
        # 2. Identificação Dinâmica de Colunas (Resiliente a trocas de posição)
        col_pedido = find_column(df_bd, ["pedido"]) 
        col_emissao = find_column(df_bd, ["emissao"])
        col_retira = find_column(df_bd, ["retira"])
        col_peso = find_column(df_bd, ["peso"])
        col_valor = find_column(df_bd, ["valor", "pedido"])
        col_danfe = find_column(df_bd, ["danfe"])
        col_codigo = find_column(df_bd, ["codigo"])
        col_data_pedido = find_column(df_bd, ["data", "pedido"])
        # Busca flexível e resiliente de data de faturamento/danfe
        col_data_danfe = None
        for col in df_bd.columns:
            norm_col = normalize_text(col)
            if "data" in norm_col or "dt" in norm_col or "date" in norm_col:
                if "danfe" in norm_col or "fatur" in norm_col:
                    col_data_danfe = col
                    break
        if not col_data_danfe:
            col_data_danfe = (
                find_column(df_bd, ["data", "faturamento"]) or
                find_column(df_bd, ["data", "danfe"]) or
                find_column(df_bd, ["dt", "faturamento"]) or
                find_column(df_bd, ["dt", "danfe"]) or
                find_column(df_bd, ["faturamento"]) or
                find_column(df_bd, ["danfe"])
            )

        
        if not col_pedido:
            raise HTTPException(status_code=400, detail="Coluna de identificação do Pedido não encontrada na aba Banco_Dados.")
            
        # Extração fixa por índices da aba Danfes
        if len(df_danfes.columns) < 11:
            raise HTTPException(status_code=400, detail="Aba Danfes estruturalmente incorreta (não possui colunas I e K).")
            
        df_danfes_clean = pd.DataFrame({
            'pedido_supra': df_danfes.iloc[:, 8].apply(lambda x: normalizar_pedido_supra(clean_numeric_code(x))),
            'status_excel': df_danfes.iloc[:, 10].apply(lambda x: str(x).strip() if pd.notna(x) else "")
        })
        df_danfes_clean = df_danfes_clean[df_danfes_clean['pedido_supra'] != ""]
        
        resumo = {
            "lidos": 0,
            "sucesso": 0,
            "ajustados": 0,
            "erros": 0,
            "sem_alteracao": 0,
            "valor_total_ajustes": 0.0
        }
        itens_resposta = []
        
        # 3. Processamento Linha a Linha
        for index, row in df_bd.iterrows():
            pedido_val = row.get(col_pedido) if col_pedido else None
            pedido_supra_raw = clean_numeric_code(pedido_val)
            
            if not pedido_supra_raw or str(pedido_supra_raw).lower() == 'nan':
                continue
                
            resumo["lidos"] += 1
            
            codigo_cliente = clean_numeric_code(row.get(col_codigo)) if col_codigo else ""
            peso = clean_currency(row.get(col_peso)) if col_peso else 0.0
            valor_pedido = clean_currency(row.get(col_valor)) if col_valor else 0.0
            
            danfe = str(row.get(col_danfe)).strip() if col_danfe and pd.notna(row.get(col_danfe)) else ""
            if danfe.endswith(".0"): danfe = danfe[:-2]
            if danfe.lower() == 'nan': danfe = ""
            
            emissao_val = row.get(col_emissao) if col_emissao else None
            emissao_dt = pd.to_datetime(emissao_val, errors='coerce', dayfirst=True) if pd.notna(emissao_val) else None
            
            data_pedido_val = row.get(col_data_pedido) if col_data_pedido else None
            data_pedido_dt = pd.to_datetime(data_pedido_val, errors='coerce', dayfirst=True) if pd.notna(data_pedido_val) else None
            
            data_danfe_val = row.get(col_data_danfe) if col_data_danfe else None
            data_danfe_dt = pd.to_datetime(data_danfe_val, errors='coerce', dayfirst=True) if pd.notna(data_danfe_val) else None
            
            dt_ref = emissao_dt or data_pedido_dt or data_danfe_dt or datetime.now()
            pedido_supra = normalizar_pedido_supra(pedido_supra_raw, dt_ref)
            
            cliente_retira = str(row.get(col_retira)).strip() if col_retira and pd.notna(row.get(col_retira)) else ""
            
            # Cruzamento Danfes (Nº do pedido)
            danfes_row = df_danfes_clean[df_danfes_clean['pedido_supra'] == pedido_supra]
            status_excel = danfes_row['status_excel'].iloc[0] if not danfes_row.empty else ""
            
            detalhes = []
            status_proc = "SUCESSO"
            ajuste_gerado = 0.0
            status_novo_pedido = None
            
            # 4. Validação e Persistência no Banco (Cruzamento Resiliente Temporal e Cura de Códigos Supra)
            check_exist = db.execute(text("""
                SELECT id_pedido, nota_fiscal, total_pedido, peso_total_kg, codigo_cliente, status, data_faturamento, pedido_supra 
                FROM public.tb_pedidos 
                WHERE pedido_supra = :p
                   OR (
                      pedido_supra IS NOT NULL AND pedido_supra != '' AND
                      CASE 
                        WHEN length(pedido_supra) = 10 THEN pedido_supra
                        ELSE to_char(COALESCE(created_at, confirmado_em, now()), 'YYYY') || lpad(ltrim(pedido_supra, '0'), 6, '0')
                      END = :p
                   )
            """), {"p": pedido_supra}).fetchone()
            
            id_pedido = None
            if not check_exist:
                status_proc = "ERRO_NAO_ENCONTRADO"
                detalhes.append("Pedido não encontrado no OrderSync.")
                resumo["erros"] += 1
                peso_db = 0.0
                total_db = 0.0
            else:
                id_pedido, nf_db, total_db, peso_db, cod_cli_db, status_db, data_fat_db, supra_db = check_exist
                total_db = float(total_db) if total_db is not None else 0.0
                peso_db = float(peso_db) if peso_db is not None else 0.0

                
                # Auto-cura: Se o peso no cabeçalho do banco for 0, mas os itens/cadastro de produtos tiverem peso, recalculamos
                if peso_db <= 0.001:
                    peso_calculado = db.execute(text("""
                        SELECT SUM(c.quantidade * COALESCE(NULLIF(c.peso_kg, 0), prod.peso, 0))
                        FROM public.tb_pedidos_itens c
                        LEFT JOIN (
                          SELECT codigo_supra, MAX(peso) as peso
                          FROM public.t_cadastro_produto_v2
                          GROUP BY codigo_supra
                        ) prod ON prod.codigo_supra = c.codigo
                        WHERE c.id_pedido = :id_pedido AND c.quantidade > 0
                    """), {"id_pedido": id_pedido}).scalar()
                    
                    if peso_calculado and peso_calculado > 0:
                        peso_db = float(peso_calculado)
                        db.execute(text("UPDATE public.tb_pedidos SET peso_total_kg = :peso WHERE id_pedido = :id_pedido"), {"peso": peso_db, "id_pedido": id_pedido})
                
                # Consulta para calcular dinamicamente o peso líquido total do pedido a partir de seus itens e do cadastro de produtos
                peso_liquido_calculado = db.execute(text("""
                    SELECT SUM(c.quantidade * COALESCE(prod.peso, 0))
                    FROM public.tb_pedidos_itens c
                    LEFT JOIN (
                      SELECT codigo_supra, MAX(peso) as peso
                      FROM public.t_cadastro_produto_v2
                      GROUP BY codigo_supra
                    ) prod ON prod.codigo_supra = c.codigo
                    WHERE c.id_pedido = :id_pedido AND c.quantidade > 0
                """), {"id_pedido": id_pedido}).scalar()
                
                peso_liquido_db = float(peso_liquido_calculado) if peso_liquido_calculado is not None else 0.0
                
                # Regras de Status Dinâmicas (Calculadas primeiro para verificar se houve alteração)
                if normalize_text(status_excel) == "pedido nao completo":
                    status_novo_pedido = 'PEDIDO_NAO_COMPLETO'
                elif danfe:
                    status_novo_pedido = 'FATURADO_SUPRA'
                else:
                    status_novo_pedido = None
                
                # Helper para comparar datas de faturamento de forma resiliente
                def is_same_date(dt1, dt2):
                    t1 = pd.to_datetime(dt1) if pd.notna(dt1) else None
                    t2 = pd.to_datetime(dt2) if pd.notna(dt2) else None
                    if t1 is None and t2 is None:
                        return True
                    if t1 is None or t2 is None:
                        return False
                    return t1.date() == t2.date()

                # Verificar se o pedido já está 100% atualizado com os mesmos dados (SEM_ALTERACAO)
                is_nf_same = (nf_db or "") == danfe
                is_val_same = abs(valor_pedido - total_db) <= 0.01
                is_peso_same = abs(peso - peso_liquido_db) <= 0.01
                is_cli_same = clean_numeric_code(cod_cli_db) == codigo_cliente
                is_status_same = (status_novo_pedido is None) or (status_db == status_novo_pedido)
                is_date_same = is_same_date(data_danfe_dt, data_fat_db)
                is_supra_same = (supra_db or "") == pedido_supra

                if is_nf_same and is_val_same and is_peso_same and is_cli_same and is_status_same and is_date_same and is_supra_same:
                    status_proc = "SEM_ALTERACAO"
                    detalhes.append("Pedido já importado anteriormente (Sem alterações).")
                    resumo["sem_alteracao"] += 1
                else:
                    # Validações Físicas e Comerciais se houver alguma divergência ou alteração
                    if cod_cli_db and clean_numeric_code(cod_cli_db) != codigo_cliente:
                        detalhes.append(f"Divergência de Cliente (Planilha: {codigo_cliente}, Banco: {cod_cli_db}).")
                    
                    if abs(peso - peso_liquido_db) > 0.01:
                        detalhes.append(f"Divergência de Peso Líquido (Planilha: {peso:.2f}kg, Banco (Líquido): {peso_liquido_db:.2f}kg).")
                        
                    diff_valor = valor_pedido - total_db
                    if abs(diff_valor) > 0.01:
                        ajuste_gerado = diff_valor
                        status_proc = "AJUSTADO"
                        detalhes.append(f"Ajuste financeiro aplicado. (Planilha: {valor_pedido:.2f}, Banco: {total_db:.2f}).")
                        resumo["ajustados"] += 1
                        resumo["valor_total_ajustes"] += abs(ajuste_gerado)
                    else:
                        resumo["sucesso"] += 1
                        
                    # Aplicando os ajustes e curando/salvando o pedido_supra no formato completo de 10 dígitos
                    update_sql = "UPDATE public.tb_pedidos SET valor_ajuste = :ajuste, total_pedido = :total, pedido_supra = :ped_completo, atualizado_em = now()"
                    params = {"ajuste": ajuste_gerado, "total": valor_pedido, "ped_completo": pedido_supra, "id_pedido": id_pedido}
                    
                    if danfe:
                        update_sql += ", nota_fiscal = :danfe"
                        params["danfe"] = danfe
                    if pd.notna(data_danfe_dt):
                        update_sql += ", data_faturamento = :data_fat"
                        params["data_fat"] = data_danfe_dt
                    if status_novo_pedido:
                        update_sql += ", status = :novo_status"
                        params["novo_status"] = status_novo_pedido
                        
                    update_sql += " WHERE id_pedido = :id_pedido"
                    db.execute(text(update_sql), params)
                
            # Log Histórico Permanente
            db.execute(text("""
                INSERT INTO public.tb_pedidos_importados (
                    pedido_supra, emissao, cliente_retira, peso, valor_pedido, danfe,
                    codigo_cliente, data_pedido, status_pedido_excel, status_processamento,
                    ajuste_gerado, detalhes_processamento
                ) VALUES (
                    :ped, :em, :ret, :peso, :val, :danfe, :cod, :dt, :st_ex, :st_proc, :ajuste, :detalhes
                )
            """), {
                "ped": pedido_supra,
                "em": emissao_dt if pd.notna(emissao_dt) else None,
                "ret": cliente_retira,
                "peso": peso,
                "val": valor_pedido,
                "danfe": danfe,
                "cod": codigo_cliente,
                "dt": data_pedido_dt if pd.notna(data_pedido_dt) else None,
                "st_ex": status_excel,
                "st_proc": status_proc,
                "ajuste": ajuste_gerado,
                "detalhes": " | ".join(detalhes) if detalhes else "Validado com sucesso."
            })
            
            itens_resposta.append({
                "id_pedido": id_pedido,
                "danfe": danfe,
                "pedido_supra": pedido_supra,
                "cliente_codigo": codigo_cliente,
                "data_pedido": data_pedido_dt.strftime('%d/%m/%Y') if pd.notna(data_pedido_dt) else (emissao_dt.strftime('%d/%m/%Y') if pd.notna(emissao_dt) else "-"),
                "data_faturamento": data_danfe_dt.strftime('%d/%m/%Y') if pd.notna(data_danfe_dt) else "-",
                "valor_planilha": valor_pedido,
                "valor_sistema": total_db,
                "peso_planilha": peso,
                "peso_sistema": peso_liquido_db,
                "ajuste_gerado": ajuste_gerado,
                "status": status_proc,
                "novo_status_pedido": status_novo_pedido or "N/A",
                "detalhes": detalhes
            })

        db.commit()
        
        # Verificar se todas as linhas lidas não tiveram alterações (Duplicidade do Arquivo)
        if resumo["sem_alteracao"] == resumo["lidos"] and resumo["lidos"] > 0:
            resumo["aviso"] = "Atenção: Todos os pedidos deste arquivo já foram processados anteriormente e não houve novas alterações."
            
        return {
            "resumo": resumo,
            "itens": itens_resposta
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Erro processando planilha xlsm: {e}")
        raise HTTPException(status_code=500, detail=f"Falha interna ao processar planilha: {str(e)}")

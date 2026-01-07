# services/produto_pdf_data.py

from __future__ import annotations

import re
from datetime import date
from typing import BinaryIO, Optional

import pdfplumber
import pandas as pd


def normalize_num(s):
    """
    Converte valores do PDF para número, entendendo:
      - 3.457      -> 3457
      - 3.457,89   -> 3457.89
      - 3457       -> 3457
      - "3 457,00" -> 3457.00
    """
    if s is None:
        return 0.0
    s = str(s).strip()
    if not s:
        return 0.0

    # remove espaços “esquisitos”
    s = s.replace(" ", "")

    # remove pontos de milhar e troca vírgula por ponto
    s = s.replace(".", "").replace(",", ".")

    try:
        return float(s)
    except ValueError:
        return 0.0


def clean_markers(s: Optional[str]) -> Optional[str]:
    """
    Remove marcações tipo (*), (**), (***), (****) e parênteses vazios.
    """
    if s is None:
        return None

    # remove (*), (**), (***), (****)
    s = re.sub(r"\(\*{1,4}\)", "", s)

    # remove () vazio ou ( ) com espaço
    s = re.sub(r"\(\s*\)", "", s)

    return s.strip()


def parse_lista_precos(
    file_obj: BinaryIO,
    tipo_lista: Optional[str] = None,  # "INSUMOS" ou "PET"
    filename: Optional[str] = None,
) -> pd.DataFrame:
    """
    Lê o PDF da lista de preços (INS/PET VOTORANTIM 15) a partir de um file-like.
    Prioriza Filename para identificar Fornecedor/Lista, depois Header.
    """
    linhas = []

    # Sequence tracking
    last_familia = None
    filhos_seq = 0

    with pdfplumber.open(file_obj) as pdf:
        # === Leitura Inicial (Header) ===
    # === Leitura Inicial (Header) ===
        header_text = pdf.pages[0].extract_text() or ""
        m = re.search(
            r"LISTA:\s*(.+?)(?:\s{2,}|VALIDADE|BATIDA|PÁG|$)",
            header_text,
            flags=re.IGNORECASE,
        )
        raw_lista = m.group(1).strip() if m else ""
        up_lista = raw_lista.upper()

        # === 1. Definição do TIPO (INSUMOS/PET) ===
        lista = None
        if tipo_lista:
            lista = tipo_lista.upper()
        
        # Fallback pelo Filename
        if not lista and filename:
            fname_up = filename.upper()
            if "PET" in fname_up:
                lista = "PET"
            elif "INS" in fname_up:
                lista = "INSUMOS"

        # Fallback pelo Header
        if not lista:
            if "PET" in up_lista:
                lista = "PET"
            elif "INS" in up_lista:
                lista = "INSUMOS"
        
        # Default final
        if not lista:
            lista = "INSUMOS"

        # === 2. Definição do FORNECEDOR ===
        fornecedor = None
        
        # Estrategia A: Filename (Prioridade Solicitada)
        if filename:
            # Tenta pegar tudo antes de ".pdf" ou numeros finais
            # Ex: "PET ALISUL 15.pdf" -> ALISUL
            clean_fn = re.sub(r"\.pdf$", "", filename, flags=re.IGNORECASE)
            # Remove prefixos comuns
            clean_fn = re.sub(r"^(INS|PET|INSUMOS)\s+", "", clean_fn, flags=re.IGNORECASE)
            # Remove digitos finais (ex: 15)
            clean_fn = re.sub(r"\s+\d+$", "", clean_fn)
            
            cand = clean_fn.strip().upper()
            if cand:
                fornecedor = cand

        # Estrategia B: Header (Fallback)
        if not fornecedor:
            if "VOTORANTIM" in up_lista or "VOTORANTIM" in header_text.upper():
                fornecedor = "VOTORANTIM"
            elif "ALISUL" in up_lista or "ALISUL" in header_text.upper():
                fornecedor = "ALISUL"
            elif "RIO CLARO" in up_lista or "RIO CLARO" in header_text.upper():
                fornecedor = "RIO CLARO"
            elif up_lista and "LISTA" not in up_lista:
                fornecedor = up_lista

        # === 3. Extração de Dados ===
        for page_idx, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            if not tables:
                continue

            for table in tables:
                if not table or len(table[0]) < 2:
                    continue

                familia_atual: Optional[str] = None

                for row in table:
                    # Normaliza row
                    row_safe = list(row) + [None] * (max(0, 6 - len(row)))
                    c0 = (row_safe[0] or "").strip()
                    c1 = (row_safe[1] or "").strip()
                    c2 = (row_safe[2] or "").strip()
                    c3 = (row_safe[3] or "").strip()

                    # Linha vazia?
                    if not any([c0, c1, c2, c3]):
                        continue

                    joined_upper = " ".join(x for x in [c0, c1, c2, c3] if x).upper()

                    # --- FILTRO DE RODAPÉ (IGNORE TERMS) ---
                    IGNORE_TERMS = [
                        "ATENDIMENTO AO CONSUMIDOR",
                        "GERÊNCIA DE VENDAS", 
                        "CONTATO:", "EMAIL:", "FONE:",
                        "VOTORANTIM@ALISUL", "PÁG:", "PAGINA",
                        "OBSERVAÇÕES", " PEDIDO MÍNIMO"
                    ]
                    if any(term in joined_upper for term in IGNORE_TERMS):
                        continue

                    # Familia Header
                    # Logica melhorada: Se c0 tem texto, c1/c2/c3 vazios, e contem "FAMILIA" ou parece titulo
                    if c0 and not c1 and not c2 and not c3:
                        # Se contiver "FAMILIA", é batata
                        if "FAMÍLIA" in c0.upper() or "FAMILIA" in c0.upper():
                            familia_atual = clean_markers(c0)
                            continue
                        
                        # Se for um texto longo sem numeros, pode ser familia (ex: FROST GATOS)
                        # Mas evitar confundir com "ATENDIMENTO..." (já filtrado acima)
                        if len(c0) > 3 and not re.search(r"\d", c0):
                             familia_atual = clean_markers(c0)
                             continue

                    # Table Header Skip
                    if ("COD" in joined_upper or "CÓD" in joined_upper) and ("PROD" in joined_upper):
                        continue

                    # === Lógica Diferenciada por TIPO ===
                    codigo = clean_markers(c0)
                    descricao = clean_markers(c1)
                    preco_ton = None
                    preco_sc = None
                    
                    if not codigo or not re.match(r"^[0-9A-Z]", codigo):
                        continue

                    # FILTRO DE LIXO / TABELAS DE PRAZO
                    code_upper = codigo.upper()
                    if (
                        "PRAZO" in code_upper 
                        or "COEF" in code_upper 
                        or re.search(r"\d+\s*DD", code_upper)
                        or re.search(r"\d+/\d+", code_upper)
                    ):
                        continue

                    if lista == "PET":
                        # Layout PET: COL2=Embalagem, COL3=Preço(7DD)
                        emb = c2
                        if emb and emb not in descricao:
                            descricao = f"{descricao} - {emb}"
                        
                        preco_sc = normalize_num(c3)
                        preco_ton = None
                    else:
                        # Layout INSUMOS (Default)
                        preco_ton = normalize_num(c2)
                        preco_sc = normalize_num(c3)

                    # Sequence Logic
                    if familia_atual != last_familia:
                        last_familia = familia_atual
                        filhos_seq = 1
                    else:
                        filhos_seq += 1

                    linhas.append(
                        {
                            "fornecedor": fornecedor,
                            "lista": lista,
                            "familia": familia_atual,
                            "codigo": codigo,
                            "descricao": descricao,
                            "preco_ton": preco_ton,
                            "preco_sc": preco_sc,
                            "page": page_idx,
                            "filhos": filhos_seq,
                        }
                    )

    df = pd.DataFrame(linhas)

    if not df.empty:
        df["lista"] = df["lista"].fillna(value=lista or "DESCONHECIDO")
        df["fornecedor"] = df["fornecedor"].fillna(value=fornecedor or "DESCONHECIDO")
        df["data_ingestao"] = date.today()

    return df


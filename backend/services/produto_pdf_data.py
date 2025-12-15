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
        return None
    s = str(s).strip()
    if not s:
        return None

    # remove espaços “esquisitos”
    s = s.replace(" ", "")

    # remove pontos de milhar e troca vírgula por ponto
    s = s.replace(".", "").replace(",", ".")

    try:
        return float(s)
    except ValueError:
        return None


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

    with pdfplumber.open(file_obj) as pdf:
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
            match_fn = re.search(r"(?:INS|PET|INSUMOS)\s+(.+?)(?:\s+\d+|\.pdf|$)", filename, re.IGNORECASE)
            if match_fn:
                cand = match_fn.group(1).strip().upper()
                cand = re.sub(r"\s+\d+$", "", cand) 
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
                    # === Lógica Diferenciada por TIPO ===
                    codigo = clean_markers(c0)
                    descricao = clean_markers(c1)
                    preco_ton = None
                    preco_sc = None
                    # Linha vazia?
                    if not any([c0, c1, c2, c3]):
                        continue

                    # DEBUG TEMPORÁRIO
                    debug_cods = ["302P25", "787F30", "002T25", "241F40"]
                    # === Lógica de Colunas Inteligente ===
                    # Se tivermos mais de 4 colunas, provavelmente a descrição quebrou em várias
                    # A suposição é: Col 0 = Código. Últimas cols = Preços. O meio = Descrição.
                    
                    row_len = len([x for x in row if x and str(x).strip()])
                    
                    # C0 é sempre Código
                    codigo = clean_markers(c0)
                    
                    if not codigo or not re.match(r"^[0-9A-Z]", codigo):
                         continue

                    descricao = ""
                    preco_ton = None
                    preco_sc = None

                    if lista == "PET":
                        # Layout PET: COL2=Embalagem, COL3=Preço(7DD)
                        emb = c2
                        if emb and emb not in descricao:
                            descricao = f"{descricao} - {emb}"
                        
                        preco_sc = normalize_num(c3)
                        preco_ton = None
                    else:
                        # Layout INSUMOS (Default)
                        # Assume colunas fixas: 0=Cod, 1=Desc, 2=Ton, 3=SC
                        preco_ton = normalize_num(c2)
                        preco_sc = normalize_num(c3)
                    
                    # Se não tiver preço, considera 0 (Sob Consulta) em vez de pular
                    # Isso evita inativar produtos que apenas perderam o preço na lista
                    # if preco_ton is None and preco_sc is None:
                    #    continue

    if not df.empty:
        df["lista"] = df["lista"].fillna(value=lista or "DESCONHECIDO")
        df["fornecedor"] = df["fornecedor"].fillna(value=fornecedor or "DESCONHECIDO")
        df["data_ingestao"] = date.today()

    return df

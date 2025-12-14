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
) -> pd.DataFrame:
    """
    Lê o PDF da lista de preços (INS/PET VOTORANTIM 15) a partir de um file-like
    (ex.: UploadFile.file) e devolve um DataFrame no formato da tabela
    t_preco_produto_pdf.

    Colunas geradas:
      - fornecedor
      - lista
      - familia
      - codigo
      - descricao
      - preco_ton
      - preco_sc
      - page
      - data_ingestao
    """
    linhas = []

    with pdfplumber.open(file_obj) as pdf:
        # === pega texto bruto da LISTA (primeira página) ===
        header_text = pdf.pages[0].extract_text() or ""
        m = re.search(
            r"LISTA:\s*(.+?)(?:\s{2,}|VALIDADE|BATIDA|PÁG|$)",
            header_text,
            flags=re.IGNORECASE,
        )
        raw_lista = m.group(1).strip() if m else ""
        up_lista = raw_lista.upper()

        # --- define "lista" (INSUMOS / PET) ---
        lista = None
        if tipo_lista:
            lista = tipo_lista.upper()
        else:
            # fallback: tenta inferir pelo cabeçalho
            if "INS" in up_lista:
                lista = "INSUMOS"
            if "PET" in up_lista:
                lista = "PET"

        # --- fornecedor padronizado ---
        if "VOTORANTIM" in up_lista:
            fornecedor = "VOTORANTIM"
        else:
            fornecedor = up_lista if up_lista else None

        # === percorre páginas/tabelas ===
        for page_idx, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            if not tables:
                continue

            for table in tables:
                if not table or len(table[0]) < 2:
                    continue

                familia_atual: Optional[str] = None

                for row in table:
                    # garante 4 colunas (para layout INS e PET simplificado)
                    row = list(row) + [None] * (4 - len(row))
                    c0 = (row[0] or "").strip()
                    c1 = (row[1] or "").strip()
                    c2 = (row[2] or "").strip()
                    c3 = (row[3] or "").strip()

                    # linha toda vazia
                    if not any([c0, c1, c2, c3]):
                        continue

                    joined = " ".join(x for x in [c0, c1, c2, c3] if x).upper()

                    # --- linha de família ---
                    if (
                        c0
                        and not c1
                        and not c2
                        and not c3
                        and not any(
                            k in joined
                            for k in ["CÓD", "COD", "PRODUTO", "R$/TON", "R$/SC"]
                        )
                    ):
                        familia_atual = clean_markers(c0)
                        continue

                    # --- cabeçalho da tabela ---
                    if ("CÓD" in joined or "COD" in joined) and "PROD" in joined:
                        # ex.: CÓD. | PRODUTO | R$/TON | R$/SC
                        continue

                    # --- item ---
                    codigo = clean_markers(c0)
                    descricao = clean_markers(c1)
                    preco_ton = normalize_num(c2)
                    preco_sc = normalize_num(c3)

                    # filtros básicos
                    if not codigo or not descricao:
                        continue
                    if not re.match(r"^[0-9A-Z]", codigo):
                        continue
                    if preco_ton is None and preco_sc is None:
                        continue

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
                        }
                    )

    df = pd.DataFrame(linhas)

    if not df.empty:
        df["lista"] = df["lista"].fillna(value=lista or "DESCONHECIDO")
        df["fornecedor"] = df["fornecedor"].fillna(value=fornecedor or "DESCONHECIDO")
        df["data_ingestao"] = date.today()

    return df

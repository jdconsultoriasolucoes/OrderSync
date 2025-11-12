import pdfplumber
import pandas as pd
import re

def normalize_num(s):
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None

def clean_markers(s: str):
    if s is None:
        return None
    # remove (*), (**), (***), (****)
    s = re.sub(r"\(\*{1,4}\)", "", s)
    # remove () vazio ou ( ) com espaço
    s = re.sub(r"\(\s*\)", "", s)
    return s.strip()

def parse_lista_precos(pdf_path: str) -> pd.DataFrame:
    linhas = []

    with pdfplumber.open(pdf_path) as pdf:
        header_text = pdf.pages[0].extract_text() or ""
        m = re.search(
            r"LISTA:\s*(.+?)(?:\s{2,}|VALIDADE|BATIDA|PÁG|$)",
            header_text,
            flags=re.IGNORECASE,
        )
        raw_lista = m.group(1).strip() if m else ""

        lista = None
        up_lista = raw_lista.upper()
        if "INS" in up_lista:
            lista = "INSUMOS"
        if "PET" in up_lista:
            lista = "PET"

        fornecedor = None
        if "VOTORANTIM" in up_lista:
            fornecedor = "VOTORANTIM"
        else:
            fornecedor = up_lista if up_lista else None

        for page_idx, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table[0]) < 2:
                    continue

                familia_atual = None

                for row in table:
                    row = list(row) + [None] * (4 - len(row))
                    c0 = (row[0] or "").strip()
                    c1 = (row[1] or "").strip()
                    c2 = (row[2] or "").strip()
                    c3 = (row[3] or "").strip()

                    if not any([c0, c1, c2, c3]):
                        continue

                    joined = " ".join(
                        x for x in [c0, c1, c2, c3] if x
                    ).upper()

                    # linha de família
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

                    # cabeçalho
                    if ("CÓD" in joined or "COD" in joined) and "PROD" in joined:
                        continue

                    # item
                    codigo = clean_markers(c0)
                    descricao = clean_markers(c1)
                    preco_ton = normalize_num(c2)
                    preco_sc = normalize_num(c3)

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

    return pd.DataFrame(linhas)

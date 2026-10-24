# services/produto_pdf_data.py

from __future__ import annotations

import re
from datetime import date
from typing import BinaryIO, Optional

import pdfplumber
import pandas as pd

import zlib

def _apply_pdfminer_fix():
    """
    Corrige o bug do pdfminer.six quando o PDF possui criptografia Standard
    mas alguns streams (como ToUnicode CMaps gerados pelo DynaPDF) foram gravados sem criptografia.
    """
    try:
        from pdfminer.pdftypes import (
            PDFStream,
            LITERALS_FLATE_DECODE,
            LITERALS_LZW_DECODE,
            LITERALS_ASCII85_DECODE,
            LITERALS_ASCIIHEX_DECODE,
            LITERALS_RUNLENGTH_DECODE,
            LITERALS_CCITTFAX_DECODE,
            LITERALS_DCT_DECODE,
            LITERALS_JBIG2_DECODE,
            LITERALS_JPX_DECODE,
            LITERAL_CRYPT,
            lzwdecode,
            ascii85decode,
            asciihexdecode,
            rldecode,
            ccittfaxdecode,
            int_value,
            apply_tiff_predictor,
            apply_png_predictor,
            decompress_corrupted,
        )
        from pdfminer.pdfexceptions import PDFException, PDFNotImplementedError
        from pdfminer import settings
    except ImportError:
        return

    if getattr(PDFStream, "_ordersync_patched", False):
        return

    def decode(self: PDFStream) -> None:
        assert self.data is None and self.rawdata is not None, str(
            (self.data, self.rawdata),
        )
        data = self.rawdata
        raw_saved = self.rawdata
        if self.decipher:
            assert self.objid is not None
            assert self.genno is not None
            data = self.decipher(self.objid, self.genno, data, self.attrs)
        filters = self.get_filters()
        if not filters:
            self.data = data
            self.rawdata = None
            return
        for f, params in filters:
            if f in LITERALS_FLATE_DECODE:
                try:
                    data = zlib.decompress(data)
                except zlib.error as e:
                    # Fallback para streams gravados sem criptografia no documento
                    try:
                        data = zlib.decompress(raw_saved)
                    except zlib.error:
                        if settings.STRICT:
                            error_msg = f"Invalid zlib bytes: {e!r}, {data!r}"
                            raise PDFException(error_msg) from e
                        try:
                            data = decompress_corrupted(data)
                        except zlib.error:
                            data = b""

            elif f in LITERALS_LZW_DECODE:
                data = lzwdecode(data)
            elif f in LITERALS_ASCII85_DECODE:
                data = ascii85decode(data)
            elif f in LITERALS_ASCIIHEX_DECODE:
                data = asciihexdecode(data)
            elif f in LITERALS_RUNLENGTH_DECODE:
                data = rldecode(data)
            elif f in LITERALS_CCITTFAX_DECODE:
                data = ccittfaxdecode(data, params)
            elif f in LITERALS_DCT_DECODE:
                pass
            elif f in LITERALS_JBIG2_DECODE or f in LITERALS_JPX_DECODE:
                pass
            elif f == LITERAL_CRYPT:
                raise PDFNotImplementedError("/Crypt filter is unsupported")
            else:
                raise PDFNotImplementedError(f"Unsupported filter: {f!r}")

            if params and "Predictor" in params:
                pred = int_value(params["Predictor"])
                if pred == 1:
                    pass
                elif pred == 2:
                    colors = int_value(params.get("Colors", 1))
                    columns = int_value(params.get("Columns", 1))
                    raw_bits_per_component = params.get("BitsPerComponent", 8)
                    bitspercomponent = int_value(raw_bits_per_component)
                    data = apply_tiff_predictor(
                        colors,
                        columns,
                        bitspercomponent,
                        data,
                    )
                elif pred >= 10:
                    colors = int_value(params.get("Colors", 1))
                    columns = int_value(params.get("Columns", 1))
                    raw_bits_per_component = params.get("BitsPerComponent", 8)
                    bitspercomponent = int_value(raw_bits_per_component)
                    data = apply_png_predictor(
                        pred,
                        colors,
                        columns,
                        bitspercomponent,
                        data,
                    )
                else:
                    error_msg = f"Unsupported predictor: {pred!r}"
                    raise PDFNotImplementedError(error_msg)

        self.data = data
        self.rawdata = None

    PDFStream.decode = decode
    PDFStream._ordersync_patched = True

_apply_pdfminer_fix()


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
    fornecedor_selecionado: Optional[str] = None,
) -> pd.DataFrame:
    """
    Lê o PDF da lista de preços (INS/PET VOTORANTIM 15) a partir de um file-like.
    Usa o Fornecedor Selecionado pelo usuário.
    """
    linhas = []

    # Sequence tracking
    last_familia = None
    filhos_seq = 0

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
        
        # Fallback pelo Filename (apenas para TIPO, se necessário, mas o user passou tipo_lista)
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
        # FORÇADO pelo input do usuário
        fornecedor = fornecedor_selecionado
        
        if not fornecedor:
             # Fallback Header se o usuário não selecionou (caso raro se o front obrigar)
             # Mas removemos a lógica do filename conforme solicitado.
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


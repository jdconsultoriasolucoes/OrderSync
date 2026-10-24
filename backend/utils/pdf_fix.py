"""
Utilitário para corrigir o bug de descompressão do pdfminer.six
quando o PDF possui criptografia padrão (Standard Security Handler),
mas alguns streams específicos (como mapas ToUnicode CMap gerados pelo DynaPDF)
foram gravados em texto claro (sem criptografia).
"""
import zlib
import pdfminer.pdftypes
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


def patch_pdfminer_stream_decode() -> None:
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
                    # Fallback: alguns geradores (ex: DynaPDF) não criptografam certos streams
                    # (como fontes e ToUnicode CMaps), apesar de declararem criptografia no documento.
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

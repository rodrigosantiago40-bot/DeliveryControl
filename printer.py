"""
Módulo de impressão térmica do Delivery Control.

Responsável por:

- gerar cupom ESC/POS;
- enviar RAW diretamente para a impressora Windows;
- ser utilizado pelo aplicativo desktop e pelo servidor Flask.
"""

import textwrap
import time
from dataclasses import asdict, is_dataclass

from PIL import Image, ImageDraw, ImageFont

try:
    import win32print
except ImportError:
    win32print = None


# ==========================================================
# CONFIGURAÇÃO
# ==========================================================

COLUNAS_80MM = 40
COLUNAS_58MM = 32

# O cupom gráfico é maior que o texto simples. Blocos de 64 bytes com
# pausa de 30 ms tornavam o envio desnecessariamente lento (mais de 1.000
# pausas por cupom). Impressoras térmicas RAW aceitam blocos maiores.
TAMANHO_BLOCO = 4096
PAUSA_ENTRE_BLOCOS = 0.001

# O formato gráfico abaixo é o novo padrão de teste. O gerador textual
# continua preservado em gerar_texto_cupom(), permitindo reversão simples.
USAR_LAYOUT_GRAFICO = True


# ==========================================================
# ESC/POS
# ==========================================================

_ESC = "\x1b"
_GS = "\x1d"


# ----------------------------------------------------------
# Inicialização
# ----------------------------------------------------------

_INICIALIZAR = _ESC + "@"


# ----------------------------------------------------------
# Negrito
# ----------------------------------------------------------

_NEGRITO_ON = _ESC + "E" + "\x01"
_NEGRITO_OFF = _ESC + "E" + "\x00"


# ----------------------------------------------------------
# FONTE NORMAL
#
# ESC ! 0
# ----------------------------------------------------------

_FONTE_NORMAL = _ESC + "!" + "\x00"


# ----------------------------------------------------------
# FONTE 2X
#
# ESC ! 48
#
# Bit 4 = altura dupla
# Bit 5 = largura dupla
#
# 16 + 32 = 48 = 0x30
# ----------------------------------------------------------

_FONTE_2X = _ESC + "!" + "\x30"


# ----------------------------------------------------------
# DESTAQUE
#
# Negrito + fonte 2X
# ----------------------------------------------------------

_DESTAQUE_ON = (
    _NEGRITO_ON
    + _FONTE_2X
)

_DESTAQUE_OFF = (
    _FONTE_NORMAL
    + _NEGRITO_OFF
)


# ----------------------------------------------------------
# Corte total
# ----------------------------------------------------------

_CORTE_TOTAL = _GS + "V" + "\x00"


# ==========================================================
# CONVERSÃO DO PEDIDO
# ==========================================================

def _para_dict(pedido):
    """Converte o pedido para dicionário."""

    if isinstance(pedido, dict):
        return pedido

    if is_dataclass(pedido):
        return asdict(pedido)

    campos = (
        "numero_pedido",
        "tipo_pedido",
        "cliente",
        "telefone",
        "endereco",
        "pagamento",
        "forma_pagamento",
        "produto",
        "valor",
        "observacao",
        "vendedor",
        "data",
        "hora",
        "entregador",
        "status",
    )

    return {
        campo: getattr(pedido, campo, "")
        for campo in campos
    }


# ==========================================================
# QUEBRA DE TEXTO
# ==========================================================

def _quebrar(texto, largura):
    """Quebra o texto respeitando a largura da bobina."""

    return textwrap.wrap(
        str(texto or ""),
        width=largura,
        break_long_words=True,
        break_on_hyphens=False
    ) or [""]


def _fonte(tamanho, negrito=False):
    """Carrega uma fonte legível do Windows, com fallback seguro."""
    caminho = r"C:\Windows\Fonts\arialbd.ttf" if negrito else r"C:\Windows\Fonts\arial.ttf"
    try:
        return ImageFont.truetype(caminho, tamanho)
    except OSError:
        return ImageFont.load_default()


def _linhas_graficas(texto, fonte, largura, limite):
    """Quebra texto de acordo com a largura real desenhada pela fonte."""
    palavras = str(texto or "").split() or [""]
    linhas, atual = [], ""
    for palavra in palavras:
        candidata = f"{atual} {palavra}".strip()
        if atual and limite < largura.textlength(candidata, font=fonte):
            linhas.append(atual)
            atual = palavra
        else:
            atual = candidata
    linhas.append(atual)
    return linhas


def gerar_imagem_cupom(pedido, largura_mm=80):
    """Monta o novo cupom gráfico em preto e branco para impressora térmica."""
    p = _para_dict(pedido)
    largura = 576 if int(largura_mm or 80) != 58 else 384
    margem = 24 if largura == 576 else 16
    escala = largura / 576
    def s(valor): return max(1, round(valor * escala))

    f_titulo = _fonte(s(38), True)
    f_secao = _fonte(s(23), True)
    # Ajuste leve de legibilidade para os textos comuns, sem alterar
    # títulos, produto, total ou demais elementos de destaque.
    f_texto = _fonte(s(24))
    f_cliente = _fonte(s(26))
    f_telefone = _fonte(s(21))
    f_produto = _fonte(s(27), True)
    f_destaque = _fonte(s(28), True)
    f_total = _fonte(s(52), True)
    f_pequena = _fonte(s(16), True)
    f_rodape = _fonte(s(15))

    numero = str(p.get("numero_pedido") or "").zfill(5)
    tipo = str(p.get("tipo_pedido") or "Entrega").upper()
    cliente = str(p.get("cliente") or "Não informado")
    telefone = str(p.get("telefone") or "")
    endereco = str(p.get("endereco") or "Não informado")
    produto = str(p.get("produto") or "Não informado").upper()
    pagamento = str(p.get("pagamento") or "Não informado").upper()
    forma_pagamento = str(p.get("forma_pagamento") or "").upper()
    observacao = str(p.get("observacao") or "").strip()
    vendedor = str(p.get("vendedor") or "Celular").upper()
    data = str(p.get("data") or "")
    hora = str(p.get("hora") or "")
    try:
        valor = float(p.get("valor") or 0)
    except (TypeError, ValueError):
        valor = 0.0

    # A altura inicial ampla permite um cupom de tamanho variável; recortamos ao final.
    imagem = Image.new("L", (largura, s(1600)), 255)
    desenho = ImageDraw.Draw(imagem)
    y = margem
    linha_larga = s(3)
    interno = s(14)

    def texto_centralizado(texto, fonte, y_atual):
        caixa = desenho.textbbox((0, 0), texto, font=fonte)
        desenho.text(((largura - (caixa[2] - caixa[0])) / 2, y_atual), texto, font=fonte, fill=0)

    def separador(y_atual, pontilhado=False):
        if pontilhado:
            for x in range(margem, largura - margem, s(11)):
                desenho.line((x, y_atual, min(x + s(6), largura - margem), y_atual), fill=0, width=s(2))
        else:
            desenho.line((margem, y_atual, largura - margem, y_atual), fill=0, width=linha_larga)

    def bloco(rotulo, valor_bloco, y_atual, detalhe="", fonte_valor=None, fonte_detalhe=None):
        fonte_valor = fonte_valor or f_texto
        fonte_detalhe = fonte_detalhe or f_pequena
        separador(y_atual)
        y_atual += s(18)
        desenho.text((margem + s(42), y_atual), rotulo, font=f_secao, fill=0)
        desenho.ellipse((margem, y_atual + s(5), margem + s(24), y_atual + s(29)), fill=0)
        y_atual += s(34)
        for linha_texto in _linhas_graficas(valor_bloco, fonte_valor, desenho, largura - margem * 2 - s(42)):
            desenho.text((margem + s(42), y_atual), linha_texto, font=fonte_valor, fill=0)
            y_atual += (desenho.textbbox((0, 0), linha_texto, font=fonte_valor)[3] + s(7))
        if detalhe:
            # Mantém uma distância visual entre o nome do cliente e o telefone.
            y_atual += s(8)
            desenho.text((margem + s(42), y_atual), detalhe, font=fonte_detalhe, fill=0)
            y_atual += (desenho.textbbox((0, 0), detalhe, font=fonte_detalhe)[3] + s(7))
        return y_atual + s(14)

    separador(y, True); y += s(20)
    texto_centralizado(f"PEDIDO Nº {numero}", f_titulo, y); y += s(54)
    texto_centralizado(f"{tipo}", f_destaque, y); y += s(40)
    separador(y, True); y += s(16)
    desenho.text((margem + s(36), y), f"DATA  {data}", font=f_secao, fill=0)
    desenho.line((largura // 2, y, largura // 2, y + s(27)), fill=0, width=s(2))
    desenho.text((largura // 2 + s(20), y), f"HORA  {hora}", font=f_secao, fill=0)
    y += s(40)

    y = bloco(
        "CLIENTE", cliente, y,
        f"TELEFONE: {telefone}" if telefone else "",
        fonte_valor=f_cliente,
        fonte_detalhe=f_telefone,
    )
    y = bloco("ENDEREÇO", endereco, y)
    separador(y); y += s(16)
    desenho.text((margem + s(42), y), "PRODUTO(S)", font=f_secao, fill=0)
    y += s(34)
    linhas_produto = _linhas_graficas(produto, f_produto, desenho, largura - margem * 2 - s(32))
    altura_produto = s(22) + len(linhas_produto) * s(37)
    desenho.rounded_rectangle(
        (margem, y, largura - margem, y + altura_produto),
        radius=s(8), outline=0, width=linha_larga
    )
    y += s(11)
    for linha_texto in linhas_produto:
        desenho.text((margem + s(16), y), linha_texto, font=f_produto, fill=0)
        y += s(37)
    y += s(12)

    altura_total = s(104)
    desenho.rounded_rectangle((margem, y, largura - margem, y + altura_total), radius=s(10), outline=0, width=linha_larga)
    texto_centralizado("TOTAL DO PEDIDO", f_secao, y + s(12))
    texto_centralizado(f"R$ {valor:.2f}".replace(".", ","), f_total, y + s(39))
    y += altura_total + s(14)

    # Os dois cartões reproduzem a leitura rápida do modelo de referência.
    altura_cartao = s(92)
    tem_status_pagamento = bool(forma_pagamento)
    metade = (largura - margem * 2 - s(10)) // 2 if tem_status_pagamento else largura - margem * 2
    desenho.rounded_rectangle((margem, y, margem + metade, y + altura_cartao), radius=s(8), outline=0, width=linha_larga)
    desenho.text((margem + interno, y + s(12)), "FORMA DE PAGAMENTO", font=f_pequena, fill=0)
    texto_centralizado_x = margem + metade / 2
    caixa = desenho.textbbox((0, 0), pagamento, font=f_destaque)
    desenho.text((texto_centralizado_x - (caixa[2] - caixa[0]) / 2, y + s(46)), pagamento, font=f_destaque, fill=0)

    if tem_status_pagamento:
        x2 = margem + metade + s(10)
        desenho.rounded_rectangle((x2, y, largura - margem, y + altura_cartao), radius=s(8), outline=0, width=linha_larga)
        desenho.text((x2 + interno, y + s(12)), "STATUS DO PAGAMENTO", font=f_pequena, fill=0)
        caixa = desenho.textbbox((0, 0), forma_pagamento, font=f_pequena)
        desenho.rectangle((x2 + interno, y + s(45), largura - margem - interno, y + s(76)), fill=0)
        desenho.text(((x2 + largura - margem - (caixa[2] - caixa[0])) / 2, y + s(51)), forma_pagamento, font=f_pequena, fill=255)
    y += altura_cartao + s(18)

    if observacao:
        y = bloco("OBSERVAÇÃO", observacao, y)

    separador(y, True); y += s(15)
    desenho.text((margem + s(10), y), f"VENDEDOR: {vendedor}", font=f_secao, fill=0); y += s(38)
    desenho.rounded_rectangle((margem, y, largura - margem, y + s(96)), radius=s(8), outline=0, width=linha_larga)
    texto_centralizado("ATENÇÃO, ENTREGADOR!", f_secao, y + s(15))
    texto_centralizado("NÃO ESQUEÇA DE TRAZER ESTE CUPOM", f_pequena, y + s(45))
    texto_centralizado("DE VOLTA APÓS A ENTREGA.", f_pequena, y + s(66))
    y += s(116)
    separador(y, True); y += s(10)
    texto_centralizado("OBRIGADO!", f_secao, y); y += s(42)
    texto_centralizado("Sistema Desenvolvido por Gustavo Fernandes", f_rodape, y)
    y += s(24)
    return imagem.crop((0, 0, largura, y))


def gerar_cupom_grafico(pedido, largura_mm=80):
    """Converte a imagem do cupom para o comando raster ESC/POS GS v 0."""
    imagem = gerar_imagem_cupom(pedido, largura_mm).convert("1")
    largura, altura = imagem.size
    bytes_linha = (largura + 7) // 8
    pixels = imagem.load()
    dados = bytearray()
    for y in range(altura):
        for bloco in range(bytes_linha):
            byte = 0
            for bit in range(8):
                x = bloco * 8 + bit
                if x < largura and pixels[x, y] == 0:
                    byte |= 0x80 >> bit
            dados.append(byte)
    return (_INICIALIZAR.encode("ascii") + b"\x1dv0\x00" +
            bytes((bytes_linha & 0xFF, bytes_linha >> 8, altura & 0xFF, altura >> 8)) +
            bytes(dados) + b"\n\n\n\n" + _CORTE_TOTAL.encode("ascii"))


# ==========================================================
# GERAÇÃO DO CUPOM
# ==========================================================

def gerar_texto_cupom(pedido, largura_mm=80):

    print(">>> GERANDO CUPOM PELO PRINTER.PY <<<")

    p = _para_dict(pedido)

    # ------------------------------------------------------
    # Largura da bobina
    # ------------------------------------------------------

    try:
        largura_mm = int(largura_mm or 80)
    except (ValueError, TypeError):
        largura_mm = 80

    if largura_mm == 58:
        largura = COLUNAS_58MM
    else:
        largura = COLUNAS_80MM

    # ------------------------------------------------------
    # Quando a fonte fica 2X, cabem aproximadamente metade
    # dos caracteres na mesma linha.
    # ------------------------------------------------------

    largura_grande = max(
        largura // 2,
        8
    )

    # ------------------------------------------------------
    # Dados do pedido
    # ------------------------------------------------------

    numero = str(
        p.get("numero_pedido") or ""
    ).zfill(5)

    tipo = str(
        p.get("tipo_pedido") or "Entrega"
    ).upper()

    cliente = str(
        p.get("cliente") or ""
    )

    endereco = str(
        p.get("endereco") or "Não informado"
    )

    produto = str(
        p.get("produto") or ""
    ).upper()

    pagamento = str(
        p.get("pagamento") or ""
    ).upper()

    forma_pagamento = str(
        p.get("forma_pagamento") or "PAGO"
    ).upper()

    vendedor = str(
        p.get("vendedor") or "Celular"
    )

    observacao = str(
        p.get("observacao") or ""
    )

    data = str(
        p.get("data") or ""
    )

    hora = str(
        p.get("hora") or ""
    )

    try:
        valor = float(
            p.get("valor") or 0
        )
    except (ValueError, TypeError):
        valor = 0.0

    linha = "-" * largura

    cupom = []

    # ======================================================
    # INICIALIZAÇÃO
    # ======================================================

    cupom.append(
        _INICIALIZAR
    )

    # Garantia inicial de fonte normal
    cupom.append(
        _FONTE_NORMAL
    )

    cupom.append(
        _NEGRITO_OFF
    )

    # ======================================================
    # CABEÇALHO
    # ======================================================

    cupom.append(
        f"PEDIDO N° {numero}".center(largura)
        + "\n"
    )

    cupom.append(
        f"*** {tipo} ***".center(largura)
        + "\n"
    )

    cupom.append(
        f"DATA: {data}".center(largura)
        + "\n"
    )

    cupom.append(
        f"HORA: {hora}".center(largura)
        + "\n"
    )

    cupom.append(
        linha
        + "\n"
    )

    # ======================================================
    # CLIENTE
    # ======================================================

    cupom.append(
        "CLIENTE:\n"
    )

    for texto in _quebrar(
        cliente,
        largura
    ):
        cupom.append(
            texto + "\n"
        )

    cupom.append(
        "\n"
    )

    # ======================================================
    # ENDEREÇO
    # ======================================================

    cupom.append(
        "ENDEREÇO:\n"
    )

    for texto in _quebrar(
        endereco,
        largura
    ):
        cupom.append(
            texto + "\n"
        )

    cupom.append(
        linha
        + "\n"
    )

    # ======================================================
    # PRODUTO
    # ======================================================

    # Garantia de fonte NORMAL antes do título
    cupom.append(
        _FONTE_NORMAL
    )

    cupom.append(
        _NEGRITO_OFF
    )

    cupom.append(
        "PRODUTO(S):\n"
    )

    # ------------------------------------------------------
    # ATIVA FONTE GRANDE 2X
    # ------------------------------------------------------

    cupom.append(
        _DESTAQUE_ON
    )

    for texto in _quebrar(
        produto,
        largura_grande
    ):
        cupom.append(
            texto + "\n"
        )

    # ------------------------------------------------------
    # DESATIVA FONTE GRANDE
    # VOLTA PARA NORMAL
    # ------------------------------------------------------

    cupom.append(
        _DESTAQUE_OFF
    )

    cupom.append(
        linha
        + "\n"
    )

    # ======================================================
    # TOTAL
    # ======================================================

    # Garantia de fonte normal
    cupom.append(
        _FONTE_NORMAL
    )

    cupom.append(
        _NEGRITO_OFF
    )

    cupom.append(
        "TOTAL:\n"
    )

    # ------------------------------------------------------
    # TOTAL EM 2X
    # ------------------------------------------------------

    cupom.append(
        _DESTAQUE_ON
    )

    cupom.append(
        f"R$ {valor:.2f}\n"
    )

    # ------------------------------------------------------
    # VOLTA PARA NORMAL
    # ------------------------------------------------------

    cupom.append(
        _DESTAQUE_OFF
    )

    # Situação do pagamento, imediatamente abaixo do valor do pedido.
    # Pedidos anteriores à criação desse campo permanecem sem essa linha.
    if forma_pagamento:
        cupom.append(
            f"PAGAMENTO: {forma_pagamento}\n"
        )

    cupom.append(
        linha
        + "\n"
    )

    # ======================================================
    # PAGAMENTO
    # ======================================================

    cupom.append(
        _FONTE_NORMAL
    )

    cupom.append(
        _NEGRITO_OFF
    )

    cupom.append(
        "PAGAMENTO:\n"
    )

    # ------------------------------------------------------
    # PAGAMENTO EM 2X
    # ------------------------------------------------------

    cupom.append(
        _DESTAQUE_ON
    )

    for texto in _quebrar(
        pagamento,
        largura_grande
    ):
        cupom.append(
            texto + "\n"
        )

    # ------------------------------------------------------
    # VOLTA PARA NORMAL
    # ------------------------------------------------------

    cupom.append(
        _DESTAQUE_OFF
    )

    cupom.append(
        linha
        + "\n"
    )

    # ======================================================
    # OBSERVAÇÃO
    # ======================================================

    if observacao:

        cupom.append(
            _FONTE_NORMAL
        )

        cupom.append(
            _NEGRITO_OFF
        )

        cupom.append(
            "OBSERVAÇÃO:\n"
        )

        for texto in _quebrar(
            observacao,
            largura
        ):
            cupom.append(
                texto + "\n"
            )

        cupom.append(
            linha
            + "\n"
        )

    # ======================================================
    # VENDEDOR
    # ======================================================

    cupom.append(
        _FONTE_NORMAL
    )

    cupom.append(
        _NEGRITO_OFF
    )

    cupom.append(
        f"Vendedor: {vendedor}\n"
    )

    # ======================================================
    # FINAL
    # ======================================================

    # Sempre termina em fonte normal
    cupom.append(
        _FONTE_NORMAL
    )

    cupom.append(
        _NEGRITO_OFF
    )

    # Avanço do papel
    cupom.append(
        "\n\n\n\n"
    )

    # Corte
    cupom.append(
        _CORTE_TOTAL
    )

    resultado = "".join(cupom)

    print(
        f">>> CUPOM GERADO: {len(resultado)} CARACTERES <<<"
    )

    return resultado


# ==========================================================
# ENVIO RAW PARA WINDOWS
# ==========================================================

def _enviar_para_windows(
    texto,
    nome_impressora=None
):

    if win32print is None:
        raise RuntimeError(
            "pywin32 não está instalado."
        )

    if nome_impressora:
        impressora = nome_impressora
    else:
        impressora = win32print.GetDefaultPrinter()

    print(
        f">>> IMPRESSORA RAW: {impressora} <<<"
    )

    dados = texto if isinstance(texto, bytes) else texto.encode("cp860", errors="replace")

    print(
        f">>> BYTES RAW: {len(dados)} <<<"
    )

    h_printer = win32print.OpenPrinter(
        impressora
    )

    try:

        win32print.StartDocPrinter(
            h_printer,
            1,
            (
                "Delivery Control",
                None,
                "RAW"
            )
        )

        try:

            win32print.StartPagePrinter(
                h_printer
            )

            try:

                for inicio in range(
                    0,
                    len(dados),
                    TAMANHO_BLOCO
                ):

                    bloco = dados[
                        inicio:
                        inicio + TAMANHO_BLOCO
                    ]

                    win32print.WritePrinter(
                        h_printer,
                        bloco
                    )

                    time.sleep(
                        PAUSA_ENTRE_BLOCOS
                    )

            finally:

                win32print.EndPagePrinter(
                    h_printer
                )

        finally:

            win32print.EndDocPrinter(
                h_printer
            )

    finally:

        win32print.ClosePrinter(
            h_printer
        )

    print(
        ">>> RAW ENVIADO <<<"
    )


# ==========================================================
# IMPRESSÃO PRINCIPAL
# ==========================================================

def imprimir_pedido(
    pedido,
    nome_impressora=None,
    largura_mm=80
):

    try:

        print("")
        print(
            "=========================================="
        )
        print(
            ">>> IMPRESSÃO DO PEDIDO <<<"
        )
        print(
            f">>> IMPRESSORA: {nome_impressora} <<<"
        )
        print(
            f">>> LARGURA: {largura_mm} mm <<<"
        )
        print(
            "=========================================="
        )

        texto = (gerar_cupom_grafico(pedido, largura_mm)
                 if USAR_LAYOUT_GRAFICO else gerar_texto_cupom(pedido, largura_mm))

        _enviar_para_windows(
            texto,
            nome_impressora
        )

        print(
            ">>> IMPRESSÃO CONCLUÍDA <<<"
        )

        print(
            "=========================================="
        )
        print("")

        return True, "Impresso com sucesso"

    except Exception as erro:

        print(
            f">>> ERRO DE IMPRESSÃO: {erro} <<<"
        )

        return False, str(erro)


# ==========================================================
# CLASSE DESKTOP
# ==========================================================

class Impressora:

    def __init__(
        self,
        nome_impressora=None,
        largura_mm=80
    ):

        self.nome_impressora = (
            nome_impressora
        )

        self.largura_mm = largura_mm

    def imprimir(
        self,
        pedido
    ):

        sucesso, mensagem = imprimir_pedido(
            pedido,
            nome_impressora=self.nome_impressora,
            largura_mm=self.largura_mm
        )

        if not sucesso:
            raise RuntimeError(
                mensagem
            )

        return sucesso

    @staticmethod
    def listar_impressoras():

        if win32print is None:
            return []

        impressoras = win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL
            | win32print.PRINTER_ENUM_CONNECTIONS
        )

        return [
            impressora[2]
            for impressora in impressoras
        ]

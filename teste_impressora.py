import win32print

IMPRESSORA = "ELGIN I8 REDE"

ESC = "\x1b"
GS = "\x1d"

dados = (
    ESC + "@"
    + ESC + "E" + "\x01"
    + "TESTE DIRETO DELIVERY CONTROL\n"
    + ESC + "E" + "\x00"
    + "--------------------------------\n"
    + "TEXTO NORMAL\n"
    + GS + "!" + "\x11"
    + "TEXTO GRANDE 2X\n"
    + GS + "!" + "\x00"
    + "--------------------------------\n"
    + "ESTE TESTE NAO PASSA PELO FLASK\n"
    + "\n\n\n\n"
    + GS + "V" + "\x00"
)

print("Abrindo:", IMPRESSORA)

h = win32print.OpenPrinter(IMPRESSORA)

try:
    win32print.StartDocPrinter(
        h,
        1,
        ("TESTE DIRETO", None, "RAW")
    )

    try:
        win32print.StartPagePrinter(h)

        try:
            win32print.WritePrinter(
                h,
                dados.encode("cp860", errors="replace")
            )

        finally:
            win32print.EndPagePrinter(h)

    finally:
        win32print.EndDocPrinter(h)

finally:
    win32print.ClosePrinter(h)

print("TESTE ENVIADO COM SUCESSO")
"""
watchdog_servidor.py
----------------------
"Vigia" do servidor web do Delivery Control.

Responsabilidade:
    Verificar se o servidor (app.py) esta respondendo de verdade.
    Se nao responder dentro do tempo limite, forca o reinicio do
    servico do Windows (instalado via nssm), mesmo que o processo
    nao tenha "morrido" de vez - so travado.

Como e usado:
    Este script NAO fica rodando o tempo todo sozinho. Ele e chamado
    periodicamente pelo Agendador de Tarefas do Windows (a cada poucos
    minutos), faz a verificacao, e termina. E o Agendador que cuida
    de chamar de novo na proxima vez.
"""

import subprocess
from datetime import datetime
from urllib import request as urllib_request
from urllib.error import URLError

URL_SAUDE = "http://127.0.0.1:5000/api/saude"
TIMEOUT_SEGUNDOS = 8

NOME_SERVICO = "DeliveryControlServidor"
CAMINHO_NSSM = r"C:\Projetos\DeliveryControl\nssm.exe"
ARQUIVO_LOG = r"C:\Projetos\DeliveryControl\watchdog_log.txt"


def registrar(mensagem: str):
    """Adiciona uma linha com data/hora no log do vigia."""
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    try:
        with open(ARQUIVO_LOG, "a", encoding="utf-8") as arquivo:
            arquivo.write(f"[{agora}] {mensagem}\n")
    except Exception:
        pass  # se nem o log der certo, nao ha nada mais a fazer aqui


def servidor_esta_respondendo() -> bool:
    """Tenta acessar a rota de saude do servidor, com tempo limite curto."""
    try:
        with urllib_request.urlopen(URL_SAUDE, timeout=TIMEOUT_SEGUNDOS) as resposta:
            return resposta.status == 200
    except (URLError, OSError, TimeoutError):
        return False


def forcar_reinicio_do_servico():
    """Pede ao nssm para reiniciar o servico do servidor web."""
    subprocess.run(
        [CAMINHO_NSSM, "restart", NOME_SERVICO],
        capture_output=True,
        timeout=30,
    )


def main():
    if servidor_esta_respondendo():
        # Nao registra nada quando esta tudo bem, para o log nao
        # encher de linhas repetidas - so os problemas ficam registrados.
        return

    registrar("Servidor nao respondeu a tempo - reiniciando o servico.")
    forcar_reinicio_do_servico()
    registrar("Comando de reinicio enviado.")


if __name__ == "__main__":
    main()

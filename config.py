"""
config.py
---------
Configuracoes gerais do sistema Delivery Control.
"""

import json
import os

# Caminho raiz fixo para garantir que o .exe e a Web usem o mesmo local
_PASTA_INSTALACAO = r"C:\Projetos\DeliveryControl"

if os.path.isdir(_PASTA_INSTALACAO):
    BASE_DIR = _PASTA_INSTALACAO
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Pasta "data" onde o banco e as configurações ficam
PASTA_DATA = os.path.join(BASE_DIR, "data")
if not os.path.exists(PASTA_DATA):
    os.makedirs(PASTA_DATA, exist_ok=True)

# Caminho do arquivo de banco de dados
DATABASE_PATH = os.path.join(PASTA_DATA, "delivery.db")

# Caminho do arquivo de preferencias do usuario
CONFIG_PATH = os.path.join(PASTA_DATA, "configuracoes.json")

CONFIGURACOES_PADRAO = {
    "impressora": None,   # None = usa a impressora padrao do Windows
    "largura_mm": 80,     # 58 ou 80
}


def carregar_configuracoes() -> dict:
    """
    Le as preferencias salvas em disco.
    """
    if not os.path.exists(CONFIG_PATH):
        salvar_configuracoes(CONFIGURACOES_PADRAO)
        return dict(CONFIGURACOES_PADRAO)

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as arquivo:
            dados_salvos = json.load(arquivo)

        configuracoes = dict(CONFIGURACOES_PADRAO)
        configuracoes.update(dados_salvos)
        return configuracoes
    except Exception:
        return dict(CONFIGURACOES_PADRAO)


def salvar_configuracoes(configuracoes: dict):
    """Grava as preferencias em disco."""
    if not os.path.exists(PASTA_DATA):
        os.makedirs(PASTA_DATA, exist_ok=True)

    with open(CONFIG_PATH, "w", encoding="utf-8") as arquivo:
        json.dump(configuracoes, arquivo, ensure_ascii=False, indent=2)
"""
database.py
-----------
Camada de acesso ao banco de dados SQLite.

Responsabilidade:
    Este e o UNICO arquivo do sistema autorizado a "conversar"
    diretamente com o banco de dados SQLite. Nenhuma tela (views/)
    nem o servidor web (app.py) devem acessar o SQLite diretamente -
    todos usam os metodos da classe Database abaixo.

Importante:
    O caminho do banco vem sempre de config.DATABASE_PATH (um
    caminho fixo, que nao depende de onde o programa foi aberto).
    Isso e essencial: o app desktop, o main.exe e o servidor web
    (app.py) precisam gravar sempre no MESMO arquivo.
"""

import sqlite3
from datetime import datetime
from typing import List, Optional

import config
from models import Pedido, STATUS_AGUARDANDO


class Database:
    """
    Camada de acesso ao banco de dados.

    Cada metodo publico representa uma operacao que as telas (ou o
    servidor web) podem solicitar. Assim, ninguem mais precisa saber
    como o SQLite funciona por dentro.
    """

    def __init__(self, caminho_banco: Optional[str] = None):
        self.caminho_banco = caminho_banco or config.DATABASE_PATH
        self._criar_tabela()

    # ------------------------------------------------------------------
    # Preparacao do banco
    # ------------------------------------------------------------------

    def _conectar(self) -> sqlite3.Connection:
        # timeout=10: se dois processos (ex: o app desktop e o servidor
        # web) tentarem gravar ao mesmo tempo, o SQLite espera ate 10
        # segundos antes de desistir, em vez de falhar na hora.
        return sqlite3.connect(self.caminho_banco, timeout=10)

    def get_connection(self) -> sqlite3.Connection:
        """
        Conexao "crua" com o banco, para casos especiais que precisam
        rodar uma consulta SQL propria (ex: o endpoint web de listagem,
        que monta um JSON customizado). Fora desses casos, prefira os
        metodos abaixo.
        """
        return self._conectar()

    def _criar_tabela(self):
        """Cria a tabela de pedidos, caso ainda nao exista."""
        with self._conectar() as conexao:
            conexao.execute("""
                CREATE TABLE IF NOT EXISTS pedidos (
                    numero_pedido INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL,
                    hora TEXT NOT NULL,
                    produto TEXT NOT NULL,
                    valor REAL NOT NULL,
                    pagamento TEXT NOT NULL,
                    vendedor TEXT NOT NULL,
                    cliente TEXT NOT NULL,
                    endereco TEXT NOT NULL,
                    observacao TEXT,
                    status TEXT NOT NULL
                )
            """)
            
            # --- MIGRACAO AUTOMATICA ---
            # Adiciona as colunas novas caso o banco de dados ja exista
            cursor = conexao.execute("PRAGMA table_info(pedidos)")
            colunas_existentes = [coluna[1] for coluna in cursor.fetchall()]
            
            if 'tipo_pedido' not in colunas_existentes:
                conexao.execute("ALTER TABLE pedidos ADD COLUMN tipo_pedido TEXT DEFAULT 'Entrega'")
            if 'entregador' not in colunas_existentes:
                conexao.execute("ALTER TABLE pedidos ADD COLUMN entregador TEXT")
            if 'forma_pagamento' not in colunas_existentes:
                conexao.execute(
                    "ALTER TABLE pedidos ADD COLUMN forma_pagamento TEXT NOT NULL DEFAULT ''"
                )
            if 'telefone' not in colunas_existentes:
                conexao.execute("ALTER TABLE pedidos ADD COLUMN telefone TEXT DEFAULT ''")

    # ------------------------------------------------------------------
    # Operacoes com pedidos
    # ------------------------------------------------------------------

    def inserir_pedido(self, pedido: Pedido) -> int:
        """Salva um novo pedido e retorna o numero de pedido gerado."""
        agora = datetime.now()
        data = pedido.data or agora.strftime("%d/%m/%Y")
        hora = pedido.hora or agora.strftime("%H:%M")

        with self._conectar() as conexao:
            cursor = conexao.execute("""
                INSERT INTO pedidos
                    (data, hora, produto, valor, pagamento,
                     vendedor, cliente, telefone, endereco, observacao, forma_pagamento,
                     status, tipo_pedido, entregador)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data, hora, pedido.produto, pedido.valor, pedido.pagamento,
                pedido.vendedor, pedido.cliente, pedido.telefone, pedido.endereco,
                pedido.observacao, pedido.forma_pagamento,
                pedido.status or STATUS_AGUARDANDO,
                pedido.tipo_pedido, pedido.entregador
            ))
            return cursor.lastrowid

    def listar_pedidos(self) -> List[Pedido]:
        """Retorna todos os pedidos, do mais recente para o mais antigo."""
        with self._conectar() as conexao:
            conexao.row_factory = sqlite3.Row
            linhas = conexao.execute(
                "SELECT * FROM pedidos ORDER BY numero_pedido DESC"
            ).fetchall()
        return [self._linha_para_pedido(linha) for linha in linhas]

    def buscar_por_numero(self, numero_pedido) -> Optional[Pedido]:
        """Busca um pedido especifico pelo numero dele."""
        with self._conectar() as conexao:
            conexao.row_factory = sqlite3.Row
            linha = conexao.execute(
                "SELECT * FROM pedidos WHERE numero_pedido = ?",
                (numero_pedido,)
            ).fetchone()
        return self._linha_para_pedido(linha) if linha else None

    def atualizar_pedido(self, pedido: Pedido):
        """Atualiza os dados de um pedido ja existente (mantem o status)."""
        with self._conectar() as conexao:
            conexao.execute("""
                UPDATE pedidos SET
                    produto=?, valor=?, pagamento=?, vendedor=?,
                    cliente=?, telefone=?, endereco=?, observacao=?, forma_pagamento=?,
                    tipo_pedido=?, entregador=?
                WHERE numero_pedido=?
            """, (
                pedido.produto, pedido.valor, pedido.pagamento,
                pedido.vendedor, pedido.cliente, pedido.telefone, pedido.endereco,
                pedido.observacao, pedido.forma_pagamento,
                pedido.tipo_pedido, pedido.entregador,
                pedido.numero_pedido,
            ))

    def atualizar_status(self, numero_pedido, novo_status: str):
        """Altera apenas o status de um pedido (ex: marcar como Entregue)."""
        with self._conectar() as conexao:
            conexao.execute(
                "UPDATE pedidos SET status=? WHERE numero_pedido=?",
                (novo_status, numero_pedido)
            )

    def excluir_pedido(self, numero_pedido):
        """Remove definitivamente um pedido do banco de dados."""
        with self._conectar() as conexao:
            conexao.execute(
                "DELETE FROM pedidos WHERE numero_pedido=?",
                (numero_pedido,)
            )

    # ------------------------------------------------------------------
    # Relatorio / fechamento por periodo
    # ------------------------------------------------------------------

    def listar_pedidos_hoje(self) -> List[Pedido]:
        """Retorna apenas os pedidos cadastrados no dia de hoje."""
        hoje_str = datetime.now().strftime("%d/%m/%Y")
        hoje_iso = self._formatar_data_iso(hoje_str)

        pedidos_hoje = []
        for pedido in self.listar_pedidos():
            if pedido.data == hoje_str or self._formatar_data_iso(pedido.data) == hoje_iso:
                pedidos_hoje.append(pedido)
        return pedidos_hoje

    def gerar_relatorio(self, data_inicio: str, data_fim: str) -> dict:
        """
        Monta um resumo de vendas entre duas datas (inclusive):
        quantidade de pedidos, faturamento total, total por forma de
        pagamento, e a lista de pedidos do periodo.
        """
        d_ini_iso = self._formatar_data_iso(data_inicio)
        d_fim_iso = self._formatar_data_iso(data_fim)

        pedidos_filtrados = []
        total_vendas = 0.0
        detalhe_pagamento = {}

        for pedido in self.listar_pedidos():
            p_data_iso = self._formatar_data_iso(pedido.data)

            if d_ini_iso <= p_data_iso <= d_fim_iso:
                pedidos_filtrados.append(pedido)
                total_vendas += pedido.valor

                if pedido.pagamento in detalhe_pagamento:
                    detalhe_pagamento[pedido.pagamento] += pedido.valor
                else:
                    detalhe_pagamento[pedido.pagamento] = pedido.valor

        return {
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "qtd_pedidos": len(pedidos_filtrados),
            "total_vendas": total_vendas,
            "detalhe_pagamento": detalhe_pagamento,
            "pedidos": pedidos_filtrados,
        }

    @staticmethod
    def _formatar_data_iso(data_str: str) -> str:
        """Converte 'DD/MM/AAAA' (ou 'DDMMAAAA') para 'AAAA-MM-DD',
        para permitir comparar datas como texto corretamente."""
        if not data_str:
            return ""

        limpo = "".join(filter(str.isdigit, data_str))
        if len(limpo) == 8:
            data_str = f"{limpo[:2]}/{limpo[2:4]}/{limpo[4:]}"

        try:
            return datetime.strptime(data_str.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            return data_str

    # ------------------------------------------------------------------
    # Auxiliar interno
    # ------------------------------------------------------------------

    def _linha_para_pedido(self, linha: sqlite3.Row) -> Pedido:
        """Converte uma linha do banco de dados em um objeto Pedido."""
        # Extraimos os dados usando as chaves para evitar erros caso a ordem mude
        dados = dict(linha)
        
        return Pedido(
            numero_pedido=dados["numero_pedido"],
            data=dados["data"],
            hora=dados["hora"],
            produto=dados["produto"],
            valor=dados["valor"],
            pagamento=dados["pagamento"],
            vendedor=dados["vendedor"],
            cliente=dados["cliente"],
            telefone=dados.get("telefone") or "",
            endereco=dados["endereco"],
            observacao=dados["observacao"],
            forma_pagamento=dados.get("forma_pagamento") or "",
            status=dados["status"],
            tipo_pedido=dados.get("tipo_pedido", "Entrega"),
            entregador=dados.get("entregador")
        )

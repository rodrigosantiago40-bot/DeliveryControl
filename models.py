"""
models.py
---------
Define a estrutura de dados usada pelo sistema.

Responsabilidade:
    Descrever "o que e" um Pedido, sem se preocupar em como ele
    e salvo (isso e responsabilidade do database.py) ou como e
    exibido na tela (isso e responsabilidade das views/).

Usamos uma @dataclass: um recurso do Python para classes que
existem apenas para guardar dados, sem comportamento proprio.
"""

from dataclasses import dataclass
from typing import Optional

# --- Status possiveis de um pedido ---
STATUS_AGUARDANDO = "Aguardando"
STATUS_SAIU_ENTREGA = "Saiu para entrega"
STATUS_ENTREGUE = "Entregue"
STATUS_CANCELADO = "Cancelado"

STATUS_VALIDOS = [
    STATUS_AGUARDANDO,
    STATUS_SAIU_ENTREGA,
    STATUS_ENTREGUE,
    STATUS_CANCELADO,
]


@dataclass
class Pedido:
    """
    Representa um pedido de entrega.

    Campos sem valor padrao (obrigatorios ao criar um pedido):
        produto, valor, pagamento, vendedor, cliente, endereco

    Campos com valor padrao (preenchidos automaticamente ou opcionais):
        telefone, observacao, forma_pagamento, status, numero_pedido, data, hora,
        tipo_pedido, entregador
    """

    produto: str
    valor: float
    pagamento: str
    vendedor: str
    cliente: str
    endereco: str

    telefone: str = ""
    observacao: str = ""
    forma_pagamento: str = ""
    status: str = STATUS_AGUARDANDO
    
    # Novos campos para controle de entregas
    tipo_pedido: str = "Entrega"  
    entregador: Optional[str] = None 

    # Preenchidos automaticamente pelo banco de dados ao salvar
    numero_pedido: Optional[int] = None
    data: Optional[str] = None
    hora: Optional[str] = None

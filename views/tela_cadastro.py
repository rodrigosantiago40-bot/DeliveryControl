"""
views/tela_cadastro.py
------------------------
Tela de cadastro de um novo pedido.

Responsabilidade:
    Coletar os dados de um pedido, validar o preenchimento e
    solicitar ao banco de dados (via Database) que o salve.

    Esta tela NUNCA acessa o SQLite diretamente - ela apenas chama
    metodos da classe Database recebida no construtor.
"""

from tkinter import messagebox

import customtkinter as ctk

import config
from models import Pedido
from printer import Impressora


class TelaCadastro(ctk.CTkToplevel):
    """
    Janela (pop-up) de cadastro de pedido.

    E aberta por cima da janela principal (CTkToplevel), permitindo
    cadastrar um pedido sem sair da tela em que o usuario esta.
    """

    OPCOES_PAGAMENTO = ["Dinheiro", "Cartao", "Pix", "Outro"]
    OPCOES_FORMA_PAGAMENTO = ["", "PAGO", "RECEBER NA ENTREGA"]
    OPCOES_TIPO_PEDIDO = ["Entrega", "Retirada"]

    def __init__(self, master, banco, ao_salvar=None, pedido=None):
        """
        master: janela "pai" (a janela principal ou a lista de pedidos)
        banco: instancia de Database, usada para salvar o pedido
        ao_salvar: funcao opcional, chamada apos salvar com sucesso
                   (usada para atualizar a lista de pedidos)
        pedido: se informado, a tela abre em modo de EDICAO, preenchida
                com os dados desse pedido, em vez de criar um novo
        """
        super().__init__(master)
        self.banco = banco
        self.ao_salvar = ao_salvar
        self.pedido_editando = pedido

        self.title(
            f"Editar Pedido Nº {pedido.numero_pedido:05d}" if pedido else "Novo Pedido"
        )
        self.geometry("600x780")

        # Torna a janela "modal": o usuario precisa fechar ou salvar
        # este formulario antes de voltar a interagir com a janela principal.
        self.transient(master)
        self.grab_set()

        self._montar_layout()

        # Atalhos de teclado: Enter salva, Esc cancela.
        self.bind("<Return>", lambda evento: self._salvar())
        self.bind("<Escape>", lambda evento: self.destroy())

        self.entry_produto.focus()

    def _montar_layout(self):
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=20)

        fonte_label = ctk.CTkFont(size=15)
        fonte_campo = ctk.CTkFont(size=16)

        def campo_texto(rotulo):
            ctk.CTkLabel(container, text=rotulo, font=fonte_label, anchor="w").pack(
                fill="x", pady=(12, 4)
            )
            entrada = ctk.CTkEntry(container, height=40, font=fonte_campo)
            entrada.pack(fill="x")
            return entrada

        self.entry_produto = campo_texto("Produto *")
        self.entry_valor = campo_texto("Valor (R$) *")

        ctk.CTkLabel(container, text="Pagamento *", font=fonte_label, anchor="w").pack(
            fill="x", pady=(12, 4)
        )
        self.opcao_pagamento = ctk.CTkOptionMenu(
            container, values=self.OPCOES_PAGAMENTO, height=40, font=fonte_campo
        )
        self.opcao_pagamento.pack(fill="x")

        ctk.CTkLabel(container, text="Situação do pagamento *", font=fonte_label, anchor="w").pack(
            fill="x", pady=(12, 4)
        )
        self.opcao_forma_pagamento = ctk.CTkOptionMenu(
            container, values=self.OPCOES_FORMA_PAGAMENTO, height=40, font=fonte_campo
        )
        self.opcao_forma_pagamento.pack(fill="x")

        self.entry_vendedor = campo_texto("Vendedor *")
        self.entry_cliente = campo_texto("Cliente *")
        self.entry_telefone = campo_texto("Telefone")
        self.entry_endereco = campo_texto("Endereco *")

        ctk.CTkLabel(container, text="Tipo de pedido", font=fonte_label, anchor="w").pack(
            fill="x", pady=(12, 4)
        )
        self.opcao_tipo_pedido = ctk.CTkOptionMenu(
            container, values=self.OPCOES_TIPO_PEDIDO, height=40, font=fonte_campo
        )
        self.opcao_tipo_pedido.pack(fill="x")

        self.entry_entregador = campo_texto("Entregador / Motoboy")

        ctk.CTkLabel(container, text="Observacao", font=fonte_label, anchor="w").pack(
            fill="x", pady=(12, 4)
        )
        self.texto_observacao = ctk.CTkTextbox(container, height=80, font=fonte_campo)
        self.texto_observacao.pack(fill="x")

        aviso = ctk.CTkLabel(
            container,
            text="* campos obrigatorios",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        aviso.pack(anchor="w", pady=(10, 0))

        frame_botoes = ctk.CTkFrame(container, fg_color="transparent")
        frame_botoes.pack(fill="x", pady=(25, 10))

        botao_salvar = ctk.CTkButton(
            frame_botoes,
            text="Salvar Pedido (Enter)",
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._salvar,
        )
        botao_salvar.pack(fill="x", pady=(0, 8))

        botao_cancelar = ctk.CTkButton(
            frame_botoes,
            text="Cancelar (Esc)",
            height=40,
            fg_color="transparent",
            border_width=1,
            command=self.destroy,
        )
        botao_cancelar.pack(fill="x")

        if self.pedido_editando:
            self._preencher_com_pedido_existente()

    def _preencher_com_pedido_existente(self):
        """Preenche o formulario com os dados do pedido em edicao."""
        pedido = self.pedido_editando
        self.entry_produto.insert(0, pedido.produto)
        self.entry_valor.insert(0, str(pedido.valor).replace(".", ","))
        self.opcao_pagamento.set(pedido.pagamento)
        self.opcao_forma_pagamento.set(pedido.forma_pagamento or "")
        self.entry_vendedor.insert(0, pedido.vendedor)
        self.entry_cliente.insert(0, pedido.cliente)
        self.entry_telefone.insert(0, pedido.telefone or "")
        self.entry_endereco.insert(0, pedido.endereco)
        self.opcao_tipo_pedido.set(pedido.tipo_pedido or "Entrega")
        self.entry_entregador.insert(0, pedido.entregador or "")
        self.texto_observacao.insert("1.0", pedido.observacao or "")

    def _salvar(self):
        produto = self.entry_produto.get().strip()
        valor_texto = self.entry_valor.get().strip().replace(",", ".")
        pagamento = self.opcao_pagamento.get()
        forma_pagamento = self.opcao_forma_pagamento.get()
        vendedor = self.entry_vendedor.get().strip()
        cliente = self.entry_cliente.get().strip()
        telefone = self.entry_telefone.get().strip()
        endereco = self.entry_endereco.get().strip()
        tipo_pedido = self.opcao_tipo_pedido.get()
        entregador = self.entry_entregador.get().strip() or None
        observacao = self.texto_observacao.get("1.0", "end").strip()

        campos_obrigatorios = {
            "Produto": produto,
            "Vendedor": vendedor,
            "Cliente": cliente,
            "Endereco": endereco,
        }
        faltando = [nome for nome, valor in campos_obrigatorios.items() if not valor]
        if faltando:
            messagebox.showwarning(
                "Campos obrigatorios",
                "Preencha os seguintes campos:\n- " + "\n- ".join(faltando),
            )
            return

        try:
            valor = float(valor_texto)
            if valor <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Valor invalido",
                "Digite um valor numerico valido, maior que zero (ex: 45,90).",
            )
            return

        if self.pedido_editando:
            # Modo edicao: atualiza o pedido existente, mantendo
            # numero, data, hora e status originais.
            pedido = self.pedido_editando
            pedido.produto = produto
            pedido.valor = valor
            pedido.pagamento = pagamento
            pedido.forma_pagamento = forma_pagamento
            pedido.vendedor = vendedor
            pedido.cliente = cliente
            pedido.telefone = telefone
            pedido.endereco = endereco
            pedido.tipo_pedido = tipo_pedido
            pedido.entregador = entregador
            pedido.observacao = observacao

            self.banco.atualizar_pedido(pedido)

            if self.ao_salvar:
                self.ao_salvar()

            messagebox.showinfo(
                "Pedido atualizado",
                f"Pedido Nº {pedido.numero_pedido:05d} atualizado com sucesso.",
            )
            self.destroy()
            return

        pedido = Pedido(
            produto=produto,
            valor=valor,
            pagamento=pagamento,
            forma_pagamento=forma_pagamento,
            vendedor=vendedor,
            cliente=cliente,
            telefone=telefone,
            endereco=endereco,
            tipo_pedido=tipo_pedido,
            entregador=entregador,
            observacao=observacao,
        )

        numero_pedido = self.banco.inserir_pedido(pedido)
        pedido_salvo = self.banco.buscar_por_numero(numero_pedido)

        if self.ao_salvar:
            self.ao_salvar()

        self._imprimir_comanda(pedido_salvo)

        messagebox.showinfo(
            "Pedido salvo", f"Pedido Nº {numero_pedido:05d} cadastrado com sucesso."
        )
        self.destroy()

    def _imprimir_comanda(self, pedido):
        """
        Imprime a comanda automaticamente apos o cadastro.

        Se a impressao falhar (impressora desligada, sem papel, nao
        configurada, etc.), o pedido continua salvo normalmente - so
        avisamos o usuario, sem travar o sistema.
        """
        try:
            configuracoes = config.carregar_configuracoes()
            impressora = Impressora(
                nome_impressora=configuracoes.get("impressora"),
                largura_mm=configuracoes.get("largura_mm", 80),
            )
            impressora.imprimir(pedido)
        except Exception as erro:
            messagebox.showwarning(
                "Impressão",
                "O pedido foi salvo, mas não foi possível imprimir a comanda "
                f"automaticamente.\n\nDetalhe: {erro}",
            )

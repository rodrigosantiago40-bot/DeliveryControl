"""
views/tela_lista.py
----------------------
Tela de listagem, pesquisa, edicao, exclusao e alteracao de status
dos pedidos cadastrados.

Responsabilidade:
    Exibir os pedidos em formato de tabela e dar acesso rapido as
    acoes principais do dia a dia. Assim como as demais telas, nunca
    acessa o SQLite diretamente - so chama metodos de Database.
"""

import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk

import config
from printer import Impressora
from views.tela_cadastro import TelaCadastro
from views.tela_status import TelaStatus

COLUNAS = ("numero", "data", "hora", "produto", "valor", "pagamento", "cliente", "tipo", "entregador", "status")

TITULOS_COLUNAS = {
    "numero": "Nº",
    "data": "Data",
    "hora": "Hora",
    "produto": "Produto",
    "valor": "Valor",
    "pagamento": "Pagamento",
    "cliente": "Cliente",
    "tipo": "Modalidade",
    "entregador": "Entregador",
    "status": "Status",
}

LARGURAS_COLUNAS = {
    "numero": 70,
    "data": 90,
    "hora": 70,
    "produto": 160,
    "valor": 90,
    "pagamento": 100,
    "cliente": 130,
    "tipo": 100,
    "entregador": 120,
    "status": 140,
}


class TelaLista(ctk.CTkToplevel):
    def __init__(self, master, banco):
        super().__init__(master)
        self.banco = banco

        self.title("Lista de Pedidos")
        self.minsize(950, 500)
        
        # Centraliza a janela na tela para não cortar a parte inferior
        self._centralizar_janela(1250, 650)

        self.transient(master)
        self.grab_set()

        # Mapeia a tecla ESC para fechar a tela de lista de pedidos
        self.bind("<Escape>", lambda event: self.destroy())

        self._configurar_estilo_tabela()
        self._montar_layout()
        self._carregar_pedidos()

        self.entry_busca.focus()

    def _centralizar_janela(self, largura, altura):
        """Calcula a posição central da tela e posiciona a janela perfeitamente."""
        self.update_idletasks()
        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()

        pos_x = (largura_tela // 2) - (largura // 2)
        pos_y = (altura_tela // 2) - (altura // 2)

        # Garante que a barra de tarefas do Windows não cubra o topo da janela
        pos_y = max(20, pos_y - 20)

        self.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")

    # ------------------------------------------------------------------
    # Montagem da interface
    # ------------------------------------------------------------------

    def _configurar_estilo_tabela(self):
        """
        O Treeview e um componente do Tkinter "puro", entao precisa
        ser estilizado manualmente para combinar com o tema escuro
        usado no restante do sistema.
        """
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure(
            "Treeview",
            background="#2b2b2b",
            foreground="white",
            fieldbackground="#2b2b2b",
            rowheight=32,
            font=("Segoe UI", 12),
            borderwidth=0,
        )
        estilo.configure(
            "Treeview.Heading",
            background="#1f1f1f",
            foreground="white",
            font=("Segoe UI", 12, "bold"),
            borderwidth=0,
        )
        estilo.map("Treeview", background=[("selected", "#1f6aa5")])

    def _montar_layout(self):
        # --- Barra de pesquisa ---
        frame_busca = ctk.CTkFrame(self, fg_color="transparent")
        frame_busca.pack(fill="x", padx=20, pady=(15, 10))

        self.entry_busca = ctk.CTkEntry(
            frame_busca,
            placeholder_text="Pesquisar por numero, cliente ou produto...",
            height=40,
            font=ctk.CTkFont(size=15),
        )
        self.entry_busca.pack(side="left", fill="x", expand=True)
        self.entry_busca.bind("<Return>", lambda evento: self._pesquisar())

        ctk.CTkButton(
            frame_busca, text="Pesquisar", width=110, height=40, command=self._pesquisar
        ).pack(side="left", padx=(10, 0))

        ctk.CTkButton(
            frame_busca,
            text="Limpar",
            width=90,
            height=40,
            fg_color="transparent",
            border_width=1,
            command=self._limpar_pesquisa,
        ).pack(side="left", padx=(10, 0))

        # --- Tabela de pedidos ---
        frame_tabela = ctk.CTkFrame(self)
        frame_tabela.pack(fill="both", expand=True, padx=20, pady=10)

        self.tree = ttk.Treeview(
            frame_tabela, columns=COLUNAS, show="headings", selectmode="browse"
        )
        for coluna in COLUNAS:
            self.tree.heading(coluna, text=TITULOS_COLUNAS[coluna])
            self.tree.column(coluna, width=LARGURAS_COLUNAS[coluna], anchor="w")

        barra_rolagem = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=barra_rolagem.set)

        self.tree.pack(side="left", fill="both", expand=True)
        barra_rolagem.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda evento: self._editar())

        # --- Barra de acoes ---
        frame_acoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_acoes.pack(fill="x", padx=20, pady=(5, 15))

        ctk.CTkButton(
            frame_acoes, text="Editar", height=42, command=self._editar
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            frame_acoes, text="Alterar Status", height=42, command=self._alterar_status
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            frame_acoes, text="Reimprimir", height=42, command=self._reimprimir
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            frame_acoes,
            text="Excluir",
            height=42,
            fg_color="#8b2020",
            hover_color="#6b1818",
            command=self._excluir,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            frame_acoes,
            text="Atualizar Lista",
            height=42,
            fg_color="transparent",
            border_width=1,
            command=self._carregar_pedidos,
        ).pack(side="right")

    # ------------------------------------------------------------------
    # Carregamento e pesquisa
    # ------------------------------------------------------------------

    def _carregar_pedidos(self, filtro=None):
        self.tree.delete(*self.tree.get_children())
        pedidos = self.banco.listar_pedidos()

        if filtro:
            filtro = filtro.lower()
            pedidos = [
                pedido for pedido in pedidos
                if filtro in pedido.cliente.lower()
                or filtro in pedido.produto.lower()
                or filtro in (pedido.entregador or "").lower()
                or filtro in str(pedido.numero_pedido)
            ]

        for pedido in pedidos:
            self.tree.insert(
                "", "end", iid=str(pedido.numero_pedido),
                values=(
                    f"{pedido.numero_pedido:05d}",
                    pedido.data,
                    pedido.hora,
                    pedido.produto,
                    f"R$ {pedido.valor:.2f}",
                    pedido.pagamento,
                    pedido.cliente,
                    pedido.tipo_pedido or "Entrega",
                    pedido.entregador or "-",
                    pedido.status,
                ),
            )

    def _pesquisar(self):
        texto = self.entry_busca.get().strip()
        self._carregar_pedidos(filtro=texto if texto else None)

    def _limpar_pesquisa(self):
        self.entry_busca.delete(0, "end")
        self._carregar_pedidos()

    # ------------------------------------------------------------------
    # Acoes sobre o pedido selecionado
    # ------------------------------------------------------------------

    def _pedido_selecionado(self):
        selecao = self.tree.selection()
        if not selecao:
            messagebox.showinfo("Selecione um pedido", "Selecione um pedido na lista primeiro.")
            return None
        numero = int(selecao[0])
        return self.banco.buscar_por_numero(numero)

    def _editar(self):
        pedido = self._pedido_selecionado()
        if pedido:
            TelaCadastro(self, self.banco, ao_salvar=self._carregar_pedidos, pedido=pedido)

    def _alterar_status(self):
        pedido = self._pedido_selecionado()
        if pedido:
            TelaStatus(self, self.banco, pedido, ao_salvar=self._carregar_pedidos)

    def _reimprimir(self):
        pedido = self._pedido_selecionado()
        if not pedido:
            return
        try:
            configuracoes = config.carregar_configuracoes()
            impressora = Impressora(
                nome_impressora=configuracoes.get("impressora"),
                largura_mm=configuracoes.get("largura_mm", 80),
            )
            impressora.imprimir(pedido)
        except Exception as erro:
            messagebox.showwarning(
                "Impressão", f"Não foi possível imprimir a comanda.\n\nDetalhe: {erro}"
            )

    def _excluir(self):
        pedido = self._pedido_selecionado()
        if not pedido:
            return
        confirma = messagebox.askyesno(
            "Confirmar exclusao",
            f"Excluir definitivamente o pedido Nº {pedido.numero_pedido:05d}?",
        )
        if confirma:
            self.banco.excluir_pedido(pedido.numero_pedido)
            self._carregar_pedidos()

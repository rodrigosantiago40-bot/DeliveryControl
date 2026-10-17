"""Painel desktop para despacho, acompanhamento e historico de entregas."""

from tkinter import messagebox, ttk

import customtkinter as ctk

from models import STATUS_AGUARDANDO, STATUS_ENTREGUE, STATUS_SAIU_ENTREGA


class TelaEntregas(ctk.CTkToplevel):
    def __init__(self, master, banco):
        super().__init__(master)
        self.banco = banco
        self.title("Controle de Entregas")
        self.geometry("1120x650")
        self.minsize(900, 520)
        self.transient(master)
        self.grab_set()
        self._montar_layout()
        self._carregar()

    def _montar_layout(self):
        ctk.CTkLabel(self, text="CONTROLE DE ENTREGAS", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(18, 10))
        abas = ctk.CTkTabview(self)
        abas.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        self.aba_aguardando = abas.add("Aguardando despacho")
        self.aba_rota = abas.add("Em rota")
        self.aba_historico = abas.add("Historico")
        self.tree_aguardando = self._criar_tabela(self.aba_aguardando)
        self.tree_rota = self._criar_tabela(self.aba_rota)
        self.tree_historico = self._criar_tabela(self.aba_historico)

        acoes_aguardando = ctk.CTkFrame(self.aba_aguardando, fg_color="transparent")
        acoes_aguardando.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(acoes_aguardando, text="Despachar para entregador", command=self._despachar).pack(side="left")
        ctk.CTkButton(acoes_aguardando, text="Atualizar", fg_color="transparent", border_width=1, command=self._carregar).pack(side="right")

        acoes_rota = ctk.CTkFrame(self.aba_rota, fg_color="transparent")
        acoes_rota.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(acoes_rota, text="Marcar como entregue", command=self._concluir).pack(side="left")
        ctk.CTkButton(acoes_rota, text="Atualizar", fg_color="transparent", border_width=1, command=self._carregar).pack(side="right")

    def _criar_tabela(self, parent):
        colunas = ("numero", "cliente", "endereco", "valor", "entregador", "status")
        tabela = ttk.Treeview(parent, columns=colunas, show="headings", selectmode="browse")
        titulos = ("Nº", "Cliente", "Endereco", "Valor", "Entregador", "Status")
        larguras = (80, 180, 330, 100, 160, 150)
        for coluna, titulo, largura in zip(colunas, titulos, larguras):
            tabela.heading(coluna, text=titulo)
            tabela.column(coluna, width=largura, anchor="w")
        tabela.pack(fill="both", expand=True, padx=10, pady=10)
        return tabela

    def _carregar(self):
        for tabela in (self.tree_aguardando, self.tree_rota, self.tree_historico):
            tabela.delete(*tabela.get_children())
        for pedido in self.banco.listar_pedidos():
            if (pedido.tipo_pedido or "Entrega") != "Entrega":
                continue
            valores = (f"{pedido.numero_pedido:05d}", pedido.cliente, pedido.endereco,
                       f"R$ {pedido.valor:.2f}", pedido.entregador or "-", pedido.status)
            if pedido.status == STATUS_AGUARDANDO:
                destino = self.tree_aguardando
            elif pedido.status == STATUS_SAIU_ENTREGA:
                destino = self.tree_rota
            elif pedido.status == STATUS_ENTREGUE:
                destino = self.tree_historico
            else:
                continue
            destino.insert("", "end", iid=str(pedido.numero_pedido), values=valores)

    @staticmethod
    def _selecionado(tabela):
        selecao = tabela.selection()
        return int(selecao[0]) if selecao else None

    def _despachar(self):
        numero = self._selecionado(self.tree_aguardando)
        if not numero:
            messagebox.showinfo("Selecione um pedido", "Selecione um pedido aguardando despacho.")
            return
        janela = ctk.CTkInputDialog(text="Nome do entregador:", title="Despachar pedido")
        entregador = janela.get_input()
        if not entregador or not entregador.strip():
            return
        pedido = self.banco.buscar_por_numero(numero)
        pedido.entregador = entregador.strip()
        self.banco.atualizar_pedido(pedido)
        self.banco.atualizar_status(numero, STATUS_SAIU_ENTREGA)
        self._carregar()

    def _concluir(self):
        numero = self._selecionado(self.tree_rota)
        if not numero:
            messagebox.showinfo("Selecione um pedido", "Selecione um pedido que esta em rota.")
            return
        self.banco.atualizar_status(numero, STATUS_ENTREGUE)
        self._carregar()

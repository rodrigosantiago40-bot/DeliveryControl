"""
views/tela_status.py
----------------------
Janela rapida para alterar o status de um pedido.

Responsabilidade:
    Permitir trocar o status (Aguardando / Saiu para entrega /
    Entregue / Cancelado) de forma agil, sem abrir o formulario
    completo de edicao.
"""

import customtkinter as ctk

from models import STATUS_VALIDOS


class TelaStatus(ctk.CTkToplevel):
    def __init__(self, master, banco, pedido, ao_salvar=None):
        super().__init__(master)
        self.banco = banco
        self.pedido = pedido
        self.ao_salvar = ao_salvar

        self.title(f"Alterar Status - Pedido Nº {pedido.numero_pedido:05d}")
        self.geometry("420x260")
        self.transient(master)
        self.grab_set()

        self._montar_layout()
        self.bind("<Return>", lambda evento: self._confirmar())
        self.bind("<Escape>", lambda evento: self.destroy())

    def _montar_layout(self):
        ctk.CTkLabel(
            self,
            text=f"Pedido Nº {self.pedido.numero_pedido:05d}",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(25, 5))

        ctk.CTkLabel(
            self, text=f"Cliente: {self.pedido.cliente}", text_color="gray"
        ).pack(pady=(0, 20))

        self.opcao_status = ctk.CTkOptionMenu(
            self, values=STATUS_VALIDOS, height=40, font=ctk.CTkFont(size=15)
        )
        self.opcao_status.set(self.pedido.status)
        self.opcao_status.pack(fill="x", padx=30)

        botao_confirmar = ctk.CTkButton(
            self,
            text="Confirmar (Enter)",
            height=45,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._confirmar,
        )
        botao_confirmar.pack(fill="x", padx=30, pady=(25, 10))

        botao_cancelar = ctk.CTkButton(
            self,
            text="Cancelar (Esc)",
            height=35,
            fg_color="transparent",
            border_width=1,
            command=self.destroy,
        )
        botao_cancelar.pack(fill="x", padx=30)

    def _confirmar(self):
        novo_status = self.opcao_status.get()
        self.banco.atualizar_status(self.pedido.numero_pedido, novo_status)
        if self.ao_salvar:
            self.ao_salvar()
        self.destroy()

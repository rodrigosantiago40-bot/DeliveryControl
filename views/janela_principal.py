"""
views/janela_principal.py
--------------------------
Janela principal do sistema Delivery Control.
"""

import customtkinter as ctk

from database import Database
from views.tela_cadastro import TelaCadastro
from views.tela_configuracoes import TelaConfiguracoes
from views.tela_lista import TelaLista
from views.tela_relatorio import TelaRelatorio
from views.tela_entregas import TelaEntregas


class JanelaPrincipal(ctk.CTk):
    def __init__(self, banco=None):
        super().__init__()

        self.banco = banco if banco is not None else Database()

        self.title("Delivery Control")
        self.geometry("1000x650")
        self.minsize(900, 600)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self._montar_layout()

    def _montar_layout(self):
        titulo = ctk.CTkLabel(
            self,
            text="DELIVERY CONTROL",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        titulo.pack(pady=(40, 10))

        subtitulo = ctk.CTkLabel(
            self,
            text="Controle de pedidos de entrega",
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        subtitulo.pack(pady=(0, 30))

        frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_botoes.pack(expand=True)

        botoes = [
            ("Novo Pedido", self._abrir_novo_pedido),
            ("Lista de Pedidos", self._abrir_lista_pedidos),
            ("Controle de Entregas", self._abrir_controle_entregas),
            ("Relatório de Vendas", self._abrir_relatorio),
            ("Configurações", self._abrir_configuracoes),
        ]

        for texto, comando in botoes:
            botao = ctk.CTkButton(
                frame_botoes,
                text=texto,
                width=300,
                height=55,
                font=ctk.CTkFont(size=18, weight="bold"),
                command=comando
            )
            botao.pack(pady=8)

    def _abrir_novo_pedido(self):
        TelaCadastro(self, self.banco)

    def _abrir_lista_pedidos(self):
        TelaLista(self, self.banco)

    def _abrir_relatorio(self):
        TelaRelatorio(self, self.banco)

    def _abrir_controle_entregas(self):
        TelaEntregas(self, self.banco)

    def _abrir_configuracoes(self):
        TelaConfiguracoes(self)


if __name__ == "__main__":
    app = JanelaPrincipal()
    app.mainloop()

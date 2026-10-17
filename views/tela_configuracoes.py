"""
views/tela_configuracoes.py
------------------------------
Tela de configuracao da impressora termica.

Responsabilidade:
    Permitir escolher qual impressora do Windows usar e a largura
    da bobina (58mm ou 80mm), salvando essa escolha via config.py.
"""

from tkinter import messagebox

import customtkinter as ctk

import config
from printer import Impressora


class TelaConfiguracoes(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Configurações")
        self.geometry("500x430")
        self.transient(master)
        self.grab_set()

        # Mapeia a tecla ESC para fechar a janela de configurações
        self.bind("<Escape>", lambda event: self.destroy())

        self.configuracoes = config.carregar_configuracoes()
        self._montar_layout()

    def _montar_layout(self):
        ctk.CTkLabel(
            self, text="Configuração da Impressora", font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(30, 25))

        ctk.CTkLabel(self, text="Impressora", anchor="w", font=ctk.CTkFont(size=14)).pack(
            fill="x", padx=30
        )

        try:
            impressoras_disponiveis = Impressora.listar_impressoras()
        except Exception:
            # Em um sistema sem impressoras instaladas, ou fora do
            # Windows, evitamos que a tela quebre.
            impressoras_disponiveis = []

        if not impressoras_disponiveis:
            impressoras_disponiveis = ["(nenhuma impressora encontrada)"]

        self.opcao_impressora = ctk.CTkOptionMenu(
            self, values=impressoras_disponiveis, height=40, font=ctk.CTkFont(size=14)
        )
        impressora_atual = self.configuracoes.get("impressora")
        if impressora_atual and impressora_atual in impressoras_disponiveis:
            self.opcao_impressora.set(impressora_atual)
        self.opcao_impressora.pack(fill="x", padx=30, pady=(6, 20))

        ctk.CTkLabel(self, text="Largura da bobina", anchor="w", font=ctk.CTkFont(size=14)).pack(
            fill="x", padx=30
        )
        self.opcao_largura = ctk.CTkOptionMenu(
            self, values=["58mm", "80mm"], height=40, font=ctk.CTkFont(size=14)
        )
        self.opcao_largura.set(f"{self.configuracoes.get('largura_mm', 80)}mm")
        self.opcao_largura.pack(fill="x", padx=30, pady=(6, 30))

        ctk.CTkButton(
            self,
            text="Salvar",
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._salvar,
        ).pack(fill="x", padx=30)

    def _salvar(self):
        impressora = self.opcao_impressora.get()
        largura_mm = int(self.opcao_largura.get().replace("mm", ""))

        config.salvar_configuracoes({
            "impressora": impressora,
            "largura_mm": largura_mm,
        })

        messagebox.showinfo("Configurações salvas", "As configurações da impressora foram salvas.")
        self.destroy()
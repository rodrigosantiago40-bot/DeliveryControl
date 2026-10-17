"""
main.py
--------
Ponto de entrada do sistema Delivery Control.

Responsabilidade:
    Iniciar a aplicação. Este arquivo NÃO deve conter regras de negócio:
    ele apenas prepara o banco de dados e abre a janela principal.
"""

from database import Database
from views.janela_principal import JanelaPrincipal


def main():
    # Garante que o banco de dados e a tabela de pedidos existem
    # antes de qualquer tela ser aberta.
    banco = Database()

    app = JanelaPrincipal(banco)

    # Função para atualizar a lista de pedidos a cada 3 segundos (3000ms)
    def auto_refresh():
        # Procura os métodos mais comuns de atualização na janela
        if hasattr(app, 'carregar_pedidos'):
            app.carregar_pedidos()
        elif hasattr(app, 'atualizar_tabela'):
            app.atualizar_tabela()
        elif hasattr(app, 'atualizar'):
            app.atualizar()
            
        # Reagenda para rodar novamente daqui a 3 segundos
        app.after(3000, auto_refresh)

    # Inicia a primeira verificação após 1 segundo
    app.after(1000, auto_refresh)

    app.mainloop()


if __name__ == "__main__":
    main()
# TODO - Delivery Control

## Concluido (app desktop)
- [x] Etapa 1 - Preparacao do ambiente
- [x] Etapa 2 - Estrutura do projeto
- [x] Etapa 3 - Janela principal (CustomTkinter, tema escuro)
- [x] Etapa 4 - Banco de dados SQLite (models.py + database.py)
- [x] Etapa 5 - Cadastro de pedidos
- [x] Etapa 6 - Lista de pedidos (editar, excluir, status, pesquisar)
- [x] Etapa 7 - Impressao termica (58mm e 80mm)
- [x] Relatorio de Vendas em PDF (filtro por periodo)

## Concluido (acesso pela rede - web)
- [x] Servidor Flask (`app.py`) rodando na rede local, para
      lancamento de pedidos pelo navegador/celular
- [x] Impressao unificada: pedidos feitos pela web imprimem igual
      aos do desktop (mesma formatacao, mesma impressora configurada)
- [x] Tema escuro no frontend web, parecido com o desktop
- [x] Lista de Pedidos pela web: ver, pesquisar, editar, alterar
      status e excluir

## Pendente / proximos passos possiveis
- [ ] Gerar o `.exe` novamente (`pyinstaller main.spec`), incorporando
      todas as correcoes feitas depois da ultima geracao (printer.py,
      config.py, database.py)
- [ ] Resolver de forma definitiva a concorrencia do SQLite (hoje so
      tem um `timeout=10` como paliativo) - so vira problema real com
      uso simultaneo intenso
- [ ] Limpar arquivos soltos que nao sao mais usados: `database.db`
      (vazio, raiz), `delivery_control.db` (do bug corrigido),
      `Novo Documento de Texto.txt`, `teste.py`
- [ ] Filtro por status na Lista de Pedidos (web e/ou desktop), alem
      da busca por numero/cliente/produto
- [ ] Autenticacao minima no acesso web (hoje qualquer aparelho na
      mesma rede local consegue lancar/editar/excluir pedidos)

## Removido do escopo (a pedido do usuario)
- Fechamento do Dia (funcionalidade original do desktop)
- Backup e restauracao (funcionalidade original do desktop)

---
Projeto em uso ativo, nao esta "fechado" - continue adicionando itens
aqui conforme surgirem novas necessidades.

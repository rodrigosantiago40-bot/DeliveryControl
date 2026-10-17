# Changelog - Delivery Control

Todas as etapas de desenvolvimento do sistema serao registradas aqui,
em ordem cronologica.

## [Etapa 1] - Preparacao do ambiente
- Definidas as tecnologias do projeto: Python 3.14, CustomTkinter, SQLite,
  PyInstaller, pywin32, Pillow.
- Ambiente virtual (venv) configurado.

## [Etapa 2] - Estrutura do projeto
- Criada a estrutura de pastas e arquivos base do sistema.
- Definida a separacao de responsabilidades:
  main.py, config.py, models.py, database.py, printer.py, views/.
- Ajuste de nomenclatura: pasta de dados renomeada para `data/`
  (para nao conflitar com o arquivo `database.py`).

## [Etapa 3] - Janela principal
- Criada a janela principal (`views/janela_principal.py`), em tema
  escuro, com CustomTkinter.
- Botoes grandes para as funcionalidades principais (ainda sem acao
  real: Novo Pedido, Lista de Pedidos, Fechamento do Dia, Backup,
  Configuracoes).
- `main.py` atualizado para abrir a janela principal.

## [Etapa 4] - Banco de dados SQLite
- Decisao de projeto: numeracao do pedido definida como sempre
  crescente, nunca reinicia (aproveitando o autoincremento nativo
  do SQLite como numero do pedido).
- Criada a classe `Pedido` (dataclass) em `models.py`, com os status
  validos: Aguardando, Saiu para entrega, Entregue, Cancelado.
- Implementada a classe `Database` em `database.py`, com criacao
  automatica da tabela e operacoes: inserir, listar, buscar por
  numero, atualizar, atualizar status, excluir.
- `main.py` atualizado para inicializar o banco de dados ao abrir
  o sistema.
- Testado localmente: insercao, listagem, atualizacao de status
  e exclusao funcionando corretamente.

## [Etapa 5] - Cadastro de pedidos
- Criada a tela `views/tela_cadastro.py`, aberta como janela
  modal (pop-up) por cima da janela principal.
- Campos: Produto, Valor, Pagamento (lista: Dinheiro, Cartao, Pix,
  Outro), Vendedor, Cliente, Endereco, Observacao.
- Validacao de campos obrigatorios e de valor numerico (aceitando
  virgula como separador decimal).
- Atalhos de teclado: Enter salva o pedido, Esc cancela.
- Botao "Novo Pedido" da janela principal conectado a esta tela.
- Ao salvar, o pedido e gravado no banco via `Database.inserir_pedido`.

## [Etapa 6] - Lista de pedidos
- Criada a tela `views/tela_lista.py`, com tabela (Treeview) exibindo
  todos os pedidos, estilizada para combinar com o tema escuro.
- Pesquisa por numero do pedido, cliente ou produto.
- Acoes: Editar, Alterar Status, Excluir, Atualizar Lista.
- Duplo-clique em um pedido abre a edicao diretamente.
- Criada a tela `views/tela_status.py`, janela rapida para trocar
  o status de um pedido sem abrir o formulario completo.
- `views/tela_cadastro.py` adaptada para funcionar tambem em modo
  de edicao (reaproveitando o mesmo formulario do cadastro).
- Botao "Lista de Pedidos" da janela principal conectado a esta tela.

## [Ajuste de escopo]
- Removidas do projeto as funcionalidades de Fechamento do Dia e
  Backup/Restauracao, a pedido do usuario.
- Tela principal simplificada para 3 botoes: Novo Pedido, Lista de
  Pedidos, Configuracoes.
- Renumeracao das etapas restantes: Etapa 7 - Impressao termica,
  Etapa 8 - Gerar executavel.

## [Etapa 7] - Impressao termica
- Implementada a classe `Impressora` em `printer.py`, com montagem
  do texto da comanda ajustado a largura da bobina (32 colunas para
  58mm, 48 colunas para 80mm) e envio via win32print (pywin32).
- `config.py` ganhou `carregar_configuracoes()` / `salvar_configuracoes()`,
  persistindo a impressora escolhida e a largura da bobina em
  `data/configuracoes.json`.
- Criada `views/tela_configuracoes.py`, para escolher a impressora
  (lista as instaladas no Windows) e a largura da bobina.
- Impressao automatica da comanda ao cadastrar um novo pedido
  (`views/tela_cadastro.py`), com aviso (sem travar o sistema) caso
  a impressao falhe.
- Botao "Reimprimir" adicionado a `views/tela_lista.py`.
- Botao "Configuracoes" da janela principal conectado a nova tela.
- Testado localmente: montagem do texto da comanda, com quebra de
  linha automatica, validada para 58mm e 80mm.

## [Correção] - Unificação da impressão (desktop + web)
- Identificado bug critico: `printer.py` havia sido reescrito (fora
  deste fluxo de desenvolvimento) sem a classe `Impressora`, quebrando
  a importacao em `tela_cadastro.py`, `tela_lista.py` e
  `tela_configuracoes.py` (o app desktop nao abria mais).
- `printer.py` corrigido: classe `Impressora` restaurada, com negrito,
  fonte em dobro de altura para produto/valor, texto sempre maiusculo
  no produto, e corte automatico do papel.
- Mantida a funcao `imprimir_pedido(pedido_id)` para compatibilidade
  com `app.py` (Flask), agora reaproveitando a mesma classe
  `Impressora` e as mesmas configuracoes salvas em
  `data/configuracoes.json` - antes, a impressao pelo navegador usava
  um formato proprio e ignorava a impressora/largura configuradas.
- Resultado: pedidos cadastrados pelo app desktop ou pelo navegador
  agora imprimem com a mesma formatacao, na mesma impressora
  configurada.

## [Correção] - Caminho do banco de dados fixo (bug de dois bancos separados)
- Identificado bug critico: `config.py` usava um caminho relativo
  (`"data/delivery.db"`), que dependia de onde o programa era aberto.
  Rodando pelo navegador (`app.py`, a partir da pasta raiz), o banco
  usado era `data/delivery.db`. Abrindo o `main.exe` de dentro da
  pasta `dist/`, o Windows tratava o caminho relativo como
  `dist/data/delivery.db` - um arquivo **diferente**. Resultado:
  pedidos feitos pelo navegador nao apareciam no app desktop.
- `config.py` corrigido: `DATABASE_PATH` e `CONFIG_PATH` agora usam
  um caminho absoluto e fixo (`C:\Projetos\DeliveryControl\data\...`),
  com fallback automatico para ambientes de desenvolvimento fora dessa
  pasta.
- Definido `data/delivery.db` (o da raiz do projeto, com os pedidos
  feitos pelo navegador) como o banco de dados oficial do sistema,
  a pedido do usuario.

## [Correção crítica] - database.py reescrito quebrou o sistema
- Identificado: `database.py` foi totalmente reescrito (durante a
  implementacao do Relatorio de Vendas) e, sem intencao, causou 3
  problemas:
  1. Voltou a ignorar `config.py`, usando um nome de arquivo fixo
     (`delivery_control.db`) - mesmo tipo de bug corrigido antes.
  2. Faltavam os metodos `listar_pedidos`, `atualizar_status` e
     `excluir_pedido`, usados pela Lista de Pedidos - a tela
     provavelmente travava/dava erro ao tentar abrir.
  3. A tabela criada pelo novo codigo nao tinha a coluna `status`,
     incompativel com o banco de dados existente.
- `database.py` corrigido: volta a usar `config.DATABASE_PATH`,
  restaura os metodos que faltavam, e mantem a coluna `status`.
  As funcoes `listar_pedidos_hoje` e `gerar_relatorio` (criadas para
  o Relatorio de Vendas) foram preservadas e adaptadas para
  reaproveitar `listar_pedidos()`, sem duplicar logica de acesso ao
  banco.
- Confirmado com os dados reais do usuario: os 14 pedidos existentes
  em `data/delivery.db` continuam intactos; inserir, editar, alterar
  status, excluir e gerar relatorio testados e funcionando.

## [Ajuste] - PDF do relatório passa a abrir para visualização
- `views/tela_relatorio.py`: o PDF gerado deixou de ser salvo direto
  na Área de Trabalho. Agora e gerado em uma pasta temporaria e aberto
  no visualizador de PDF padrao do Windows, para o usuario decidir ali
  mesmo se quer imprimir, salvar em outro lugar, ou so visualizar.

## [Ajuste] - Digitação de data sem barra no relatório
- Campos "De" e "Até" da tela de Relatório agora aceitam so numeros
  (ex: "050826") e se formatam sozinhos para "05/08/2026" ao sair do
  campo ou ao clicar em "Filtrar". Tambem aceita 8 digitos
  ("05082026") com o ano completo.

## [Ajuste] - Tema escuro no frontend web (a pedido do usuário)
- `templates/index.html`: paleta de cores trocada para tema escuro
  (fundo, cards e campos escuros, azul de destaque), para ficar
  visualmente parecido com o app desktop. So o CSS foi alterado -
  nenhuma logica de JavaScript ou dos endpoints foi tocada.

## [Novo] - Lista de Pedidos pelo navegador
- `app.py`: adicionado o endpoint `DELETE /api/pedidos/<numero>` para
  excluir um pedido pela web (os demais endpoints ja existiam).
- `templates/index.html`: adicionada uma aba "Lista de Pedidos", com:
  - Pesquisa por numero, cliente ou produto
  - Troca de status por uma lista suspensa em cada pedido
  - Botao de excluir (com confirmacao)
  - A aba "Novo Pedido" continua como estava, com a pre-visualizacao
    dos ultimos 10 pedidos.

## [Novo] - Edição de pedidos pelo navegador
- `app.py`: adicionado o endpoint `PUT /api/pedidos/<numero>` para
  editar produto, valor, pagamento, vendedor, cliente, endereco e
  observacao de um pedido existente.
- `templates/index.html`: botao "Editar" em cada pedido da Lista de
  Pedidos, que transforma o item num formulario preenchido com os
  dados atuais (Salvar/Cancelar), sem precisar de uma pagina separada.

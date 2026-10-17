"""
app.py
------
Servidor Web Flask do sistema Delivery Control.
Integrado com a tabela 'pedidos' e a coluna 'numero_pedido'.
"""

from flask import Flask, render_template, request, jsonify, redirect
import config
from database import Database
from models import Pedido, STATUS_AGUARDANDO
from printer import imprimir_pedido

app = Flask(__name__)
banco = Database()


@app.route('/')
def index():
    """Carrega a página principal do lançamento web."""
    return render_template('index.html')


@app.route('/api/saude', methods=['GET'])
def verificar_saude():
    """
    Endpoint bem leve, usado pelo vigia (watchdog_servidor.py) para
    checar se o servidor esta respondendo. Nao consulta o banco de
    dados de proposito - se o servidor como um todo estiver travado,
    ate essa rota simples deixa de responder, e e isso que o vigia
    detecta.
    """
    return jsonify({"status": "ok"}), 200


@app.route('/api/pedidos', methods=['GET'])
def listar_pedidos():
    """Retorna todos os pedidos ordenados por numero_pedido."""
    try:
        conn = banco.get_connection()
        cursor = conn.cursor()
        
        # Seleciona garantindo alias 'id' para compatibilidade com a interface web
        cursor.execute("""
            SELECT 
                numero_pedido AS id,
                numero_pedido,
                data,
                hora,
                produto,
                valor,
                valor AS total,
                pagamento,
                forma_pagamento,
                vendedor,
                cliente,
                telefone,
                endereco,
                observacao,
                status,
                tipo_pedido,
                entregador
            FROM pedidos 
            ORDER BY numero_pedido DESC
        """)
        
        colunas = [column[0] for column in cursor.description]
        pedidos_raw = cursor.fetchall()
        conn.close()

        lista_pedidos = [dict(zip(colunas, p)) for p in pedidos_raw]
        return jsonify(lista_pedidos), 200

    except Exception as e:
        print(f"[ERRO GET /api/pedidos]: {e}")
        return jsonify({"erro": str(e)}), 500


@app.route('/api/pedidos', methods=['POST'])
def criar_pedido():
    """Recebe um novo pedido via Web, grava no banco e dispara a impressão."""
    dados = request.get_json() or {}

    if not dados:
        return jsonify({"erro": "Dados inválidos."}), 400

    try:
        prod = dados.get('produto')
        if not prod and 'itens' in dados:
            itens_txt = []
            for item in dados.get('itens', []):
                p_nome = item.get('produto') or item.get('nome') or ''
                p_qtd = item.get('quantidade') or 1
                itens_txt.append(f"{p_qtd}x {p_nome}")
            prod = ", ".join(itens_txt)

        novo_pedido = Pedido(
            produto=prod or 'Diversos',
            valor=float(dados.get('valor') or dados.get('total') or 0.0),
            pagamento=dados.get('pagamento') or 'Dinheiro',
            forma_pagamento=dados.get('forma_pagamento') or '',
            vendedor=dados.get('vendedor') or 'Web',
            cliente=dados.get('cliente') or 'Balcão',
            telefone=dados.get('telefone') or '',
            endereco=dados.get('endereco') or 'Retirada',
            observacao=dados.get('observacao') or dados.get('obs') or '',
            status=dados.get('status') or STATUS_AGUARDANDO,
            tipo_pedido=dados.get('tipo_pedido', 'Entrega')
        )

        numero_gerado = banco.inserir_pedido(novo_pedido)

        # Dispara a impressão automática no servidor
        try:
            pedido_salvo = banco.buscar_por_numero(numero_gerado)
            conf = config.carregar_configuracoes()
            imprimir_pedido(
                pedido_salvo,
                nome_impressora=conf.get("impressora"),
                largura_mm=conf.get("largura_mm", 80),
            )
        except Exception as err_print:
            print(f"[AVISO IMPRESSÃO]: {err_print}")

        return jsonify({
            "sucesso": True,
            "mensagem": "Pedido registrado com sucesso!",
            "numero_pedido": numero_gerado,
            "id": numero_gerado
        }), 201

    except Exception as e:
        print(f"[ERRO POST /api/pedidos]: {e}")
        return jsonify({"erro": f"Erro ao salvar: {str(e)}"}), 500


# --- ROTA DE REIMPRESSÃO PARA O PRINTER.PY ---
@app.route('/api/imprimir', methods=['POST'])
def rota_imprimir():
    """Recebe os dados do pedido do front-end e aciona a reimpressão térmica."""
    try:
        dados = request.get_json() or {}
        numero_pedido = dados.get('numero_pedido')
        
        if not numero_pedido:
            return jsonify({"status": "erro", "mensagem": "Número do pedido não informado."}), 400

        pedido = banco.buscar_por_numero(numero_pedido)
        if not pedido:
            return jsonify({"status": "erro", "mensagem": "Pedido não encontrado."}), 404

        conf = config.carregar_configuracoes()
        sucesso, mensagem = imprimir_pedido(
            pedido,
            nome_impressora=conf.get("impressora"),
            largura_mm=conf.get("largura_mm", 80),
        )
        if not sucesso:
            return jsonify({"status": "erro", "mensagem": mensagem}), 500

        return jsonify({"status": "sucesso", "mensagem": "Impresso com sucesso"}), 200
    except Exception as e:
        print(f"[ERRO /api/imprimir]: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


@app.route('/api/pedidos/<int:numero_pedido>', methods=['PUT'])
def editar_pedido(numero_pedido):
    """Atualiza os dados de um pedido existente (produto, valor, etc)."""
    dados = request.get_json() or {}

    try:
        pedido = banco.buscar_por_numero(numero_pedido)
        if not pedido:
            return jsonify({"erro": "Pedido não encontrado"}), 404

        pedido.produto = dados.get('produto', pedido.produto)
        pedido.valor = float(dados.get('valor', pedido.valor))
        pedido.pagamento = dados.get('pagamento', pedido.pagamento)
        pedido.forma_pagamento = dados.get('forma_pagamento', pedido.forma_pagamento)
        pedido.vendedor = dados.get('vendedor', pedido.vendedor)
        pedido.cliente = dados.get('cliente', pedido.cliente)
        pedido.telefone = dados.get('telefone', pedido.telefone)
        pedido.endereco = dados.get('endereco', pedido.endereco)
        pedido.observacao = dados.get('observacao', pedido.observacao)
        pedido.tipo_pedido = dados.get('tipo_pedido', getattr(pedido, 'tipo_pedido', 'Entrega'))

        banco.atualizar_pedido(pedido)
        return jsonify({"sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route('/api/pedidos/<int:numero_pedido>/status', methods=['PUT'])
def atualizar_status(numero_pedido):
    """Atualiza o status do pedido."""
    dados = request.get_json() or {}
    novo_status = dados.get('status')

    if not novo_status:
        return jsonify({"erro": "Status não informado"}), 400

    try:
        banco.atualizar_status(numero_pedido, novo_status)
        return jsonify({"sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route('/api/pedidos/<int:numero_pedido>', methods=['DELETE'])
def excluir_pedido(numero_pedido):
    """Exclui definitivamente um pedido."""
    try:
        banco.excluir_pedido(numero_pedido)
        return jsonify({"sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# --- ROTAS DE CONTROLE DE ENTREGAS ---

@app.route('/controle-entregas')
def controle_entregas():
    """Tela de controle de entregas."""
    try:
        conn = banco.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT numero_pedido AS id, cliente, endereco, valor 
            FROM pedidos 
            WHERE tipo_pedido = 'Entrega' AND status = 'Aguardando'
        """)
        colunas_pend = [column[0] for column in cursor.description]
        pendentes = [dict(zip(colunas_pend, p)) for p in cursor.fetchall()]

        cursor.execute("""
            SELECT numero_pedido AS id, cliente, endereco, entregador 
            FROM pedidos 
            WHERE tipo_pedido = 'Entrega' AND status = 'Saiu para entrega'
        """)
        colunas_rota = [column[0] for column in cursor.description]
        em_rota = [dict(zip(colunas_rota, p)) for p in cursor.fetchall()]

        conn.close()

        return render_template('controle_entregas.html', pendentes=pendentes, em_rota=em_rota)
    except Exception as e:
        return f"Erro ao carregar controle de entregas: {e}"


@app.route('/despachar/<int:numero_pedido>', methods=['POST'])
def despachar_pedido(numero_pedido):
    """Atribui um motoboy e muda o status para Saiu para entrega."""
    entregador_selecionado = request.form.get('entregador')
    try:
        conn = banco.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE pedidos 
            SET status = 'Saiu para entrega', entregador = ? 
            WHERE numero_pedido = ?
        """, (entregador_selecionado, numero_pedido))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro ao despachar: {e}")
        
    return redirect('/controle-entregas')


@app.route('/concluir_entrega/<int:numero_pedido>', methods=['POST'])
def concluir_entrega(numero_pedido):
    """Marca o pedido como Entregue quando o motoboy retorna."""
    try:
        banco.atualizar_status(numero_pedido, 'Entregue')
    except Exception as e:
        print(f"Erro ao concluir: {e}")
        
    return redirect('/controle-entregas')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

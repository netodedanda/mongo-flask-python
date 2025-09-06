from flask import Flask, jsonify, request
from sqlalchemy.orm import joinedload
from datetime import datetime
from config import SQLALCHEMY_DATABASE_URI


import sql_service
from nosql_service import (
    registrar_dashboard_total,
    obter_dashboard_total,
    registrar_documento,
    obter_documento
)
from models import db, Cliente, Produto, Venda
from config import SQLALCHEMY_DATABASE_URI

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
db.init_app(app)

# ---------- CLIENTES ----------

@app.route("/clientes", methods=["GET"])
def listar_clientes_route():
    clientes = sql_service.listar_clientes()
    return jsonify([
        {
            "id_cliente": c.id_cliente,
            "nome": c.nome,
            "email": c.email,
            "cpf": c.cpf,
            "data_nascimento": c.data_nascimento.strftime("%Y-%m-%d") if c.data_nascimento else None
        } for c in clientes
    ])

@app.route("/clientes", methods=["POST"])
def criar_cliente_route():
    data = request.json
    if not all(k in data for k in ("nome", "email")):
        return jsonify({"erro": "Campos obrigatórios: nome, email"}), 400

    cliente = sql_service.criar_cliente(
        nome=data["nome"],
        email=data["email"],
        cpf=data.get("cpf"),
        data_nascimento=data.get("data_nascimento", "2000-01-01")
    )

    # Atualiza dashboard MongoDB
    total_clientes = len(sql_service.listar_clientes())
    registrar_dashboard_total(total_clientes)
    registrar_documento("dashboard", {"_id": "total_clientes"}, {"total": total_clientes})

    return jsonify({"id": cliente.id_cliente, "mensagem": "Cliente criado com sucesso"}), 201

@app.route("/clientes/<int:cliente_id>", methods=["GET"])
def obter_cliente_route(cliente_id):
    cliente = sql_service.obter_cliente(cliente_id)
    if not cliente:
        return jsonify({"erro": "Cliente não encontrado"}), 404
    return jsonify({
        "id_cliente": cliente.id_cliente,
        "nome": cliente.nome,
        "email": cliente.email,
        "cpf": cliente.cpf,
        "data_nascimento": cliente.data_nascimento.strftime("%Y-%m-%d") if cliente.data_nascimento else None
    })

@app.route("/clientes/<int:cliente_id>", methods=["PUT"])
def atualizar_cliente_route(cliente_id):
    data = request.json
    cliente = sql_service.atualizar_cliente(
        cliente_id,
        nome=data.get("nome"),
        email=data.get("email"),
        cpf=data.get("cpf"),
        data_nascimento=data.get("data_nascimento")
    )
    if not cliente:
        return jsonify({"erro": "Cliente não encontrado"}), 404
    return jsonify({"mensagem": "Cliente atualizado com sucesso"})

@app.route("/clientes/<int:cliente_id>", methods=["DELETE"])
def deletar_cliente_route(cliente_id):
    cliente = sql_service.deletar_cliente(cliente_id)
    if not cliente:
        return jsonify({"erro": "Cliente não encontrado"}), 404

    total_clientes = len(sql_service.listar_clientes())
    registrar_dashboard_total(total_clientes)
    registrar_documento("dashboard", {"_id": "total_clientes"}, {"total": total_clientes})

    return jsonify({"mensagem": "Cliente deletado com sucesso"})


# ---------- PRODUTOS ----------

@app.route("/produtos", methods=["GET"])
def listar_produtos_route():
    produtos = sql_service.listar_produtos()
    return jsonify([
        {
            "id_produto": p.id_produto,
            "nome": p.nome,
            "preco": p.preco,
            "descricao": p.descricao,
            "categoria": p.categoria
        } for p in produtos
    ])

@app.route("/produtos", methods=["POST"])
def criar_produto_route():
    data = request.json
    produto = sql_service.criar_produto(
        nome=data["nome"],
        preco=data["preco"],
        descricao=data.get("descricao"),
        categoria=data.get("categoria")
    )

    # Atualiza dashboard MongoDB
    total_produtos = len(sql_service.listar_produtos())
    registrar_documento("dashboard", {"_id": "total_produtos"}, {"total": total_produtos})

    return jsonify({"id": produto.id_produto, "mensagem": "Produto criado com sucesso"}), 201

@app.route("/produtos/<int:produto_id>", methods=["DELETE"])
def deletar_produto_route(produto_id):
    produto = sql_service.deletar_produto(produto_id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado"}), 404

    total_produtos = len(sql_service.listar_produtos())
    registrar_documento("dashboard", {"_id": "total_produtos"}, {"total": total_produtos})

    return jsonify({"mensagem": "Produto deletado com sucesso"})


# ---------- VENDAS ----------

@app.route("/vendas", methods=["GET"])
def listar_vendas_route():
    vendas = Venda.query.options(joinedload(Venda.cliente), joinedload(Venda.produto)).all()
    return jsonify([
        {
            "id_pedido": v.id_pedido,
            "data_pedido": v.data_pedido.strftime("%Y-%m-%d %H:%M:%S"),
            "cliente": v.cliente.nome if v.cliente else None,
            "produto": v.produto.nome if v.produto else None,
            "valor_total": v.valor_total
        } for v in vendas
    ])

@app.route("/vendas", methods=["POST"])
def criar_venda_route():
    data = request.json
    cliente = sql_service.obter_cliente(data["id_cliente"])
    produto = Produto.query.get(data["id_produto"])
    if not cliente or not produto:
        return jsonify({"erro": "Cliente ou Produto inexistente"}), 400

    venda = sql_service.criar_venda(
        id_cliente=cliente.id_cliente,
        id_produto=produto.id_produto,
        valor_total=data["valor_total"]
    )

    # Atualiza dashboard MongoDB
    total_vendas = len(Venda.query.all())
    receita_total = sum(v.valor_total for v in Venda.query.all())
    registrar_documento("dashboard", {"_id": "total_vendas"}, {"total": total_vendas, "receita": receita_total})

    return jsonify({"id": venda.id_pedido, "mensagem": "Venda criada com sucesso"}), 201


# ---------- DASHBOARD ----------

@app.route("/dashboard/total_clientes", methods=["GET"])
def dashboard_total_clientes():
    total = obter_dashboard_total()
    return jsonify({"total_clientes": total})

@app.route("/dashboard/total_produtos", methods=["GET"])
def dashboard_total_produtos():
    doc = obter_documento("dashboard", {"_id": "total_produtos"})
    return jsonify({"total_produtos": doc["total"] if doc else 0})

@app.route("/dashboard/total_vendas", methods=["GET"])
def dashboard_total_vendas():
    doc = obter_documento("dashboard", {"_id": "total_vendas"})
    return jsonify({
        "total_vendas": doc["total"] if doc else 0,
        "receita": doc["receita"] if doc else 0
    })


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

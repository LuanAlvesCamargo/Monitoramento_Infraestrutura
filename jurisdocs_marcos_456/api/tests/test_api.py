import uuid

from app import create_app


def document_payload(number):
    return {
        "numero": number,
        "titulo": "Documento de teste automatizado",
        "tipo": "Parecer",
        "descricao": "Registro temporario criado exclusivamente pela suite de testes.",
        "status": "Em analise",
        "tags": ["teste", "cache"],
    }


def test_crud_and_cache_aside():
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()
    number = f"DOC-TESTE-{uuid.uuid4().hex[:10].upper()}"
    created_id = None
    try:
        created = client.post("/api/documentos", json=document_payload(number))
        assert created.status_code == 201
        created_id = created.get_json()["id"]
        first = client.get(f"/api/documentos/{created_id}")
        assert first.status_code == 200
        assert first.headers["X-Cache"] == "MISS"
        second = client.get(f"/api/documentos/{created_id}")
        assert second.status_code == 200
        assert second.headers["X-Cache"] == "HIT"
        changed = client.put(f"/api/documentos/{created_id}", json={"status": "Ativo", "tags": ["teste", "atualizado"]})
        assert changed.status_code == 200
        after_write = client.get(f"/api/documentos/{created_id}")
        assert after_write.status_code == 200
        assert after_write.headers["X-Cache"] == "MISS"
        assert after_write.get_json()["status"] == "Ativo"
        removed = client.delete(f"/api/documentos/{created_id}")
        assert removed.status_code == 204
        assert client.get(f"/api/documentos/{created_id}").status_code == 404
    finally:
        if created_id:
            app.extensions["mongo_client"][app.config["MONGO_DATABASE"]]["documentos"].delete_one({"numero": number})

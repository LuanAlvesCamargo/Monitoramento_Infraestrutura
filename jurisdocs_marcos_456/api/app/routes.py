import hashlib
import json
from datetime import datetime, timezone

from bson import ObjectId
from flask import Blueprint, current_app, jsonify, request
from pymongo import DESCENDING, ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError
from redis.exceptions import RedisError

api = Blueprint("api", __name__)

REQUIRED_FIELDS = {"numero", "titulo", "tipo", "descricao", "status"}
EDITABLE_FIELDS = REQUIRED_FIELDS | {"tags"}
CACHE_TTL_SECONDS = 60


def collection():
    client = current_app.extensions["mongo_client"]
    return client[current_app.config["MONGO_DATABASE"]]["documentos"]


def redis_client():
    return current_app.extensions["redis_client"]


def document_cache_key(document_id: str) -> str:
    return f"jurisdocs:documento:{document_id}"


def listing_cache_key() -> str:
    normalized = "&".join(f"{key}={value}" for key, value in sorted(request.args.items()))
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"jurisdocs:listagem:v1:{digest}"


def cached_json(key: str):
    try:
        value = redis_client().get(key)
        if value is None:
            return None, "MISS"
        return json.loads(value), "HIT"
    except (RedisError, json.JSONDecodeError, TypeError):
        return None, "BYPASS"


def store_cached_json(key: str, value: dict) -> str:
    try:
        redis_client().set(key, json.dumps(value, ensure_ascii=False), ex=CACHE_TTL_SECONDS)
        return "MISS"
    except RedisError:
        return "BYPASS"


def invalidate_documents(document_id: str | None = None) -> None:
    try:
        client = redis_client()
        keys = [document_cache_key(document_id)] if document_id else []
        keys.extend(client.scan_iter(match="jurisdocs:listagem:v1:*", count=100))
        if keys:
            client.delete(*keys)
    except RedisError:
        return


def json_response(body: dict, cache_status: str, status: int = 200):
    response = jsonify(body)
    response.status_code = status
    response.headers["X-Cache"] = cache_status
    response.headers["Cache-Control"] = "no-store"
    return response


def error(message: str, status: int):
    return jsonify({"erro": message}), status


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def serialize(document: dict) -> dict:
    return {
        "id": str(document["_id"]),
        "numero": document["numero"],
        "titulo": document["titulo"],
        "tipo": document["tipo"],
        "descricao": document["descricao"],
        "status": document["status"],
        "tags": document.get("tags", []),
        "dataCriacao": document["dataCriacao"].isoformat(),
        "dataAtualizacao": document["dataAtualizacao"].isoformat(),
    }


def payload(partial: bool = False):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, "O corpo da requisicao deve ser um objeto JSON."

    unknown = set(data) - EDITABLE_FIELDS
    if unknown:
        return None, f"Campos nao permitidos: {', '.join(sorted(unknown))}."

    if not partial:
        missing = REQUIRED_FIELDS - set(data)
        if missing:
            return None, f"Campos obrigatorios ausentes: {', '.join(sorted(missing))}."

    result = {}
    for field in REQUIRED_FIELDS:
        if field in data:
            if not isinstance(data[field], str) or not data[field].strip():
                return None, f"O campo '{field}' deve ser um texto nao vazio."
            result[field] = data[field].strip()

    if "tags" in data:
        if not isinstance(data["tags"], list) or any(
            not isinstance(tag, str) or not tag.strip() for tag in data["tags"]
        ):
            return None, "O campo 'tags' deve ser uma lista de textos nao vazios."
        result["tags"] = sorted({tag.strip() for tag in data["tags"]})

    if partial and not result:
        return None, "Informe pelo menos um campo editavel."

    if not partial and "tags" not in result:
        result["tags"] = []

    return result, None


def object_id(value: str):
    try:
        return ObjectId(value)
    except Exception:
        return None


@api.get("/health")
def health():
    status = {"api": "ok", "mongodb": "indisponivel", "redis": "indisponivel"}

    try:
        current_app.extensions["mongo_client"].admin.command("ping")
        status["mongodb"] = "ok"
    except PyMongoError:
        pass

    try:
        current_app.extensions["redis_client"].ping()
        status["redis"] = "ok"
    except RedisError:
        pass

    http_status = 200 if all(value == "ok" for value in status.values()) else 503
    return jsonify(status), http_status


@api.get("/documentos")
def list_documents():
    try:
        page = int(request.args.get("pagina", 1))
        limit = int(request.args.get("limite", 10))
    except ValueError:
        return error("pagina e limite devem ser numeros inteiros.", 400)

    if page < 1 or not 1 <= limit <= 100:
        return error("pagina deve ser maior que zero e limite deve estar entre 1 e 100.", 400)

    key = listing_cache_key()
    cached, cache_status = cached_json(key)
    if cached is not None:
        return json_response(cached, cache_status)

    query = {}
    search = request.args.get("q", "").strip()
    if search:
        query["$text"] = {"$search": search}
    for field in ("tipo", "status"):
        value = request.args.get(field, "").strip()
        if value:
            query[field] = value
    tag = request.args.get("tag", "").strip()
    if tag:
        query["tags"] = tag

    cursor = collection().find(query)
    if search:
        cursor = cursor.sort([("score", {"$meta": "textScore"})])
    else:
        cursor = cursor.sort("dataCriacao", DESCENDING)
    documents = list(cursor.skip((page - 1) * limit).limit(limit))
    total = collection().count_documents(query)

    body = {
        "itens": [serialize(document) for document in documents],
        "paginacao": {"pagina": page, "limite": limit, "total": total},
    }
    return json_response(body, store_cached_json(key, body))


@api.post("/documentos")
def create_document():
    document, message = payload()
    if message:
        return error(message, 400)

    now = utc_now()
    document["dataCriacao"] = now
    document["dataAtualizacao"] = now

    try:
        result = collection().insert_one(document)
    except DuplicateKeyError:
        return error("Ja existe um documento com este numero.", 409)

    created = collection().find_one({"_id": result.inserted_id})
    invalidate_documents()
    return jsonify(serialize(created)), 201


@api.get("/documentos/<document_id>")
def get_document(document_id: str):
    identifier = object_id(document_id)
    if not identifier:
        return error("Identificador de documento invalido.", 400)

    key = document_cache_key(document_id)
    cached, cache_status = cached_json(key)
    if cached is not None:
        return json_response(cached, cache_status)

    document = collection().find_one({"_id": identifier})
    if not document:
        return error("Documento nao encontrado.", 404)
    body = serialize(document)
    return json_response(body, store_cached_json(key, body))


@api.put("/documentos/<document_id>")
def update_document(document_id: str):
    identifier = object_id(document_id)
    if not identifier:
        return error("Identificador de documento invalido.", 400)

    updates, message = payload(partial=True)
    if message:
        return error(message, 400)
    updates["dataAtualizacao"] = utc_now()

    try:
        document = collection().find_one_and_update(
            {"_id": identifier},
            {"$set": updates},
            return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError:
        return error("Ja existe um documento com este numero.", 409)

    if not document:
        return error("Documento nao encontrado.", 404)
    invalidate_documents(document_id)
    return jsonify(serialize(document))


@api.delete("/documentos/<document_id>")
def delete_document(document_id: str):
    identifier = object_id(document_id)
    if not identifier:
        return error("Identificador de documento invalido.", 400)

    result = collection().delete_one({"_id": identifier})
    if result.deleted_count == 0:
        return error("Documento nao encontrado.", 404)
    invalidate_documents(document_id)
    return "", 204

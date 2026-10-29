#!/usr/bin/env python3
"""Configura o host Fedora e os itens HTTP do laboratório via API do Zabbix."""

import getpass
import json
import sys
import urllib.request
import urllib.error


API_URL = "http://127.0.0.1:8081/api_jsonrpc.php"
HOST_NAME = "Fedora-monitorado"


def api(method, params, auth=None, request_id=1):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": request_id}
    if auth:
        payload["auth"] = auth
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json-rpc"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode())
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Não foi possível acessar a API do Zabbix: {exc}") from exc
    if "error" in result:
        error = result["error"]
        raise RuntimeError(f"API {method}: {error.get('data', error.get('message'))}")
    return result["result"]


def main():
    print("Configuração automática do Zabbix local")
    user = input("Usuário do Zabbix [Admin]: ").strip() or "Admin"
    password = getpass.getpass("Senha atual do Zabbix: ")
    auth = api("user.login", {"username": user, "password": password})

    groups = api("hostgroup.get", {"output": ["groupid", "name"], "filter": {"name": ["Linux servers"]}}, auth)
    if not groups:
        groups = api("hostgroup.get", {"output": ["groupid", "name"], "filter": {"name": ["Linux servers"]}}, auth)
    if not groups:
        raise RuntimeError("O grupo 'Linux servers' não foi encontrado no Zabbix.")
    group_id = groups[0]["groupid"]

    hosts = api("host.get", {"output": ["hostid", "host", "name"], "filter": {"host": [HOST_NAME]}}, auth)
    if hosts:
        host_id = hosts[0]["hostid"]
        print(f"Host já existe: {HOST_NAME} ({host_id})")
    else:
        created = api("host.create", {
            "host": HOST_NAME,
            "name": HOST_NAME,
            "groups": [{"groupid": group_id}],
            "tags": [{"tag": "laboratorio", "value": "monitoramento"}],
        }, auth)
        host_id = created["hostids"][0]
        print(f"Host criado: {HOST_NAME} ({host_id})")

    base_url = "http://prometheus:9090/api/v1/query"
    items = [
        ("CPU utilizada", "fedora.cpu.usage", '100 - (100 * avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])))', 0, "%"),
        ("Memória utilizada", "fedora.memory.usage", "100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))", 0, "%"),
        ("Disco utilizado", "fedora.disk.usage", '100 * (1 - (node_filesystem_avail_bytes{mountpoint="/",fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes{mountpoint="/",fstype!~"tmpfs|overlay"}))', 0, "%"),
        ("Disponibilidade do Node Exporter", "fedora.node.up", 'up{job="fedora-node"}', 3, ""),
        ("Rede recebida", "fedora.network.receive", 'sum(rate(node_network_receive_bytes_total{device!="lo"}[5m]))', 0, "Bps"),
        ("Rede transmitida", "fedora.network.transmit", 'sum(rate(node_network_transmit_bytes_total{device!="lo"}[5m]))', 0, "Bps"),
    ]

    existing = api("item.get", {"output": ["itemid", "key_", "name"], "hostids": [host_id], "filter": {"key_": [item[1] for item in items]}}, auth)
    by_key = {item["key_"]: item["itemid"] for item in existing}
    for name, key, query, value_type, units in items:
        data = {
            "name": name,
            "key_": key,
            "hostid": host_id,
            "type": 19,
            "value_type": value_type,
            "delay": "60s",
            "url": base_url,
            "query_fields": [{"name": "query", "value": query}],
            "output_format": 0,
            "preprocessing": [{"type": 12, "params": "$.data.result[0].value[1]", "error_handler": 0, "error_handler_params": ""}],
            "tags": [{"tag": "componente", "value": "fedora"}],
        }
        if units:
            data["units"] = units
        if key in by_key:
            data["itemid"] = by_key[key]
            api("item.update", data, auth)
            print(f"Item atualizado: {name}")
        else:
            api("item.create", data, auth)
            print(f"Item criado: {name}")

    triggers = [
        ("CPU do Fedora acima de 80%", "last(/Fedora-monitorado/fedora.cpu.usage)>80", "warning"),
        ("Node Exporter do Fedora indisponível", "last(/Fedora-monitorado/fedora.node.up)=0", "high"),
    ]
    for description, expression, priority in triggers:
        found = api("trigger.get", {"output": ["triggerid", "description"], "filter": {"description": [description]}}, auth)
        priority_num = {"warning": 2, "high": 4}[priority]
        data = {"description": description, "expression": expression, "priority": priority_num, "status": 0}
        if found:
            data["triggerid"] = found[0]["triggerid"]
            api("trigger.update", data, auth)
            print(f"Trigger atualizada: {description}")
        else:
            api("trigger.create", data, auth)
            print(f"Trigger criada: {description}")

    api("user.logout", [], auth)
    print("Configuração concluída. Verifique Monitoring > Latest data no frontend.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, KeyboardInterrupt) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        sys.exit(1)

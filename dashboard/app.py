import os
import time
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, render_template


app = Flask(__name__)

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
ZABBIX_API_URL = os.getenv("ZABBIX_API_URL", "http://zabbix-web:8080/api_jsonrpc.php")
ZABBIX_USER = os.getenv("ZABBIX_API_USER", "Admin")
ZABBIX_PASSWORD = os.getenv("ZABBIX_API_PASSWORD", "")
JUICE_SHOP_URL = os.getenv("JUICE_SHOP_URL", "http://juice-shop:3000/")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "5"))


def prometheus_query(query):
    response = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": query},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") != "success":
        raise RuntimeError(payload.get("error", "Prometheus query failed"))
    return payload["data"].get("result", [])


def prometheus_scalar(query):
    result = prometheus_query(query)
    if not result:
        return None
    return float(result[0]["value"][1])


def prometheus_range(query, minutes=30, step=60):
    end = time.time()
    start = end - (minutes * 60)
    response = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query_range",
        params={"query": query, "start": start, "end": end, "step": step},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") != "success":
        raise RuntimeError(payload.get("error", "Prometheus range query failed"))
    result = payload["data"].get("result", [])
    if not result:
        return []
    return [[float(point[0]), float(point[1])] for point in result[0].get("values", [])]


def prometheus_targets():
    response = requests.get(f"{PROMETHEUS_URL}/api/v1/targets", timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()["data"].get("activeTargets", [])


def zabbix_call(method, params, auth=None):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    if auth:
        payload["auth"] = auth
    response = requests.post(ZABBIX_API_URL, json=payload, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    body = response.json()
    if "error" in body:
        raise RuntimeError(body["error"].get("data", body["error"].get("message", "Zabbix API error")))
    return body["result"]


def zabbix_data():
    if not ZABBIX_PASSWORD:
        return {"available": False, "message": "Credencial ZABBIX_API_PASSWORD não configurada"}
    auth = zabbix_call("user.login", {"username": ZABBIX_USER, "password": ZABBIX_PASSWORD})
    hosts = zabbix_call(
        "host.get",
        {"output": ["hostid", "host", "name", "status", "available"], "filter": {"host": ["Fedora-monitorado"]}},
        auth,
    )
    problems = zabbix_call(
        "problem.get",
        {"output": ["eventid", "name", "severity", "clock"], "recent": True, "sortfield": ["eventid"], "sortorder": "DESC", "limit": 10},
        auth,
    )
    items = []
    if hosts:
        items = zabbix_call(
            "item.get",
            {"output": ["name", "key_", "lastvalue", "lastclock", "units", "state"], "hostids": [hosts[0]["hostid"]], "sortfield": "name"},
            auth,
        )
    return {"available": True, "hosts": hosts, "items": items, "problems": problems}


def juice_shop_status():
    started = time.perf_counter()
    try:
        response = requests.get(JUICE_SHOP_URL, timeout=REQUEST_TIMEOUT)
        return {"available": response.ok, "status_code": response.status_code, "latency_ms": round((time.perf_counter() - started) * 1000, 1)}
    except requests.RequestException as exc:
        return {"available": False, "message": str(exc), "latency_ms": None}


def safe(call, fallback=None):
    try:
        return call()
    except Exception as exc:  # Dashboard should keep showing the other sources.
        return {"error": str(exc), "value": fallback}


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/dashboard")
def dashboard_data():
    return jsonify({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "prometheus": {
            "cpu_percent": safe(lambda: prometheus_scalar('100 - (100 * avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[1m])))')),
            "memory_percent": safe(lambda: prometheus_scalar("100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))")),
            "disk_percent": safe(lambda: prometheus_scalar('100 * (1 - (node_filesystem_avail_bytes{mountpoint="/",fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes{mountpoint="/",fstype!~"tmpfs|overlay"}))')),
            "network_receive_bps": safe(lambda: prometheus_scalar('sum(rate(node_network_receive_bytes_total{device!="lo"}[1m]))')),
            "network_transmit_bps": safe(lambda: prometheus_scalar('sum(rate(node_network_transmit_bytes_total{device!="lo"}[1m]))')),
            "node_up": safe(lambda: prometheus_scalar('up{job="fedora-node"}')),
            "cpu_series": safe(lambda: prometheus_range('100 - (100 * avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[1m])))'), []),
            "memory_series": safe(lambda: prometheus_range("100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))"), []),
            "targets": safe(prometheus_targets, []),
        },
        "zabbix": safe(zabbix_data, {"available": False}),
        "juice_shop": juice_shop_status(),
    })


@app.get("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

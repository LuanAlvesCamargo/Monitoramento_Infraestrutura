#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
COMPOSE=(podman compose -p jurisdocs)
API_URL="http://127.0.0.1:5050/api/documentos?limite=1&q=contrato"
restore_redis() { "${COMPOSE[@]}" start redis >/dev/null 2>&1 || true; }
trap restore_redis EXIT
echo '[1/4] Leitura normal para preparar o cache.'
curl --fail --silent --show-error -D /tmp/jurisdocs-cache.headers -o /dev/null "$API_URL"
grep -i '^X-Cache:' /tmp/jurisdocs-cache.headers || true
echo '[2/4] Parando somente o Redis para validar degradacao controlada.'
"${COMPOSE[@]}" stop redis
echo '[3/4] A API deve continuar listando dados do MongoDB com X-Cache: BYPASS.'
curl --fail --silent --show-error -D /tmp/jurisdocs-bypass.headers -o /dev/null "$API_URL"
grep -qi '^X-Cache: BYPASS' /tmp/jurisdocs-bypass.headers
grep -i '^X-Cache:' /tmp/jurisdocs-bypass.headers
echo '[4/4] Restaurando Redis e aguardando healthcheck.'
"${COMPOSE[@]}" start redis
for _ in $(seq 1 20); do
  if [ "$(podman inspect -f '{{.State.Health.Status}}' jurisdocs-redis 2>/dev/null || true)" = healthy ]; then
    echo 'Validacao concluida: fallback confirmado e Redis restaurado.'
    exit 0
  fi
  sleep 2
done
echo 'Redis nao ficou saudavel no tempo esperado.' >&2
exit 1

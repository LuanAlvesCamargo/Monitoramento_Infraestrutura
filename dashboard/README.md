# Dashboard centralizado Flask

O dashboard é um serviço do `compose.yaml` acessível em
`http://localhost:3300`. Ele consulta as APIs internas, sem fazer scraping das
páginas HTML abertas no navegador.

## Fontes

| Área | Fonte exibida no dashboard |
|---|---|
| CPU, memória, disco e rede | Prometheus API, com dados do Node Exporter do Fedora |
| Targets e disponibilidade do coletor | Prometheus `/api/v1/targets` |
| Itens e problemas | Zabbix API, host `Fedora-monitorado` |
| Disponibilidade do Juice Shop | Verificação HTTP do Flask para `juice-shop:3000` |

Cada cartão, gráfico e tabela possui uma nota de fonte na própria interface.

## Credencial do Zabbix

O dashboard precisa consultar a API do Zabbix. No `.env` local, adicione a
senha atual do usuário administrador:

```text
ZABBIX_API_USER=Admin
ZABBIX_API_PASSWORD=coloque-a-senha-atual-aqui
DASHBOARD_PORT=3300
```

O `.env` está no `.gitignore` e não deve ser versionado.

## Execução

```bash
podman compose up -d --build dashboard
```

Verificar:

```bash
curl http://localhost:3300/health
```

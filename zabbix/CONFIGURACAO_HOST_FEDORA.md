# Configuração do Fedora no Zabbix

## Estratégia utilizada

Neste ambiente o Fedora não possui o pacote `zabbix-agent2` disponível nos
repositórios padrão. Para manter o laboratório sem instalar dependências no
sistema, o Zabbix Server consulta o Prometheus pela rede interna do Compose.

O fluxo fica:

```text
Fedora -> Node Exporter -> Prometheus -> Zabbix HTTP agent items
```

O Zabbix Server alcança os serviços pelos nomes internos:

```text
http://node-exporter:9100/metrics
http://prometheus:9090/api/v1/query
```

## Criar o host

1. Acesse `http://localhost:8081`.
2. Abra **Data collection > Hosts**.
3. Clique em **Create host**.
4. Preencha:
   - Host name: `Fedora-monitorado`
   - Host groups: `Linux servers`
   - Interfaces: não é necessário adicionar interface de agente para os itens HTTP.
5. Salve o host.

## Criar os itens HTTP

Em cada item, use:

- Type: `HTTP agent`
- Update interval: `30s`
- Type of information: `Numeric (float)`
- History storage period: `7d`

Use esta URL base em todos os itens:

```text
http://prometheus:9090/api/v1/query
```

Na seção **Query fields** de cada item, clique em `Add` e informe:

```text
Name: query
Value: a consulta PromQL da tabela abaixo, sem codificação percentuada
```

Após criar cada item, em **Preprocessing**, adicione:

```text
JSONPath: $.data.result[0].value[1]
```

Os itens são:

| Nome | Key | Consulta PromQL codificada |
|---|---|---|
| CPU utilizada | `fedora.cpu.usage` | `100 - (100 * avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])))` |
| Memória utilizada | `fedora.memory.usage` | `100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))` |
| Disco utilizado | `fedora.disk.usage` | `100 * (1 - (node_filesystem_avail_bytes{mountpoint="/",fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes{mountpoint="/",fstype!~"tmpfs|overlay"}))` |
| Disponibilidade Node Exporter | `fedora.node.up` | `up{job="fedora-node"}` |
| Rede recebida | `fedora.network.receive` | `sum(rate(node_network_receive_bytes_total{device!="lo"}[5m]))` |
| Rede transmitida | `fedora.network.transmit` | `sum(rate(node_network_transmit_bytes_total{device!="lo"}[5m]))` |

Para os itens de CPU, memória e disco, use a unidade `%`. Para rede, use
`Bps`. Para disponibilidade, use `Numeric (unsigned)` em vez de float.

## Criar triggers

Em **Data collection > Hosts > Fedora-monitorado > Triggers**, crie:

### CPU alta

```text
Name: CPU do Fedora acima de 80%
Expression: last(/Fedora-monitorado/fedora.cpu.usage)>80
Severity: Warning
```

### Fedora indisponível

```text
Name: Node Exporter do Fedora indisponível
Expression: last(/Fedora-monitorado/fedora.node.up)=0
Severity: High
```

## Validar

Após aguardar aproximadamente um minuto:

1. Acesse **Monitoring > Latest data**.
2. Filtre pelo host `Fedora-monitorado`.
3. Confirme valores para CPU, memória, disco, rede e disponibilidade.
4. Acesse **Monitoring > Problems** para verificar triggers.

As consultas também podem ser conferidas diretamente no Prometheus em
`http://localhost:9091/query`.

## Configuração automática pelo CLI

O script `scripts/configurar_zabbix.py` cria ou atualiza o host, os seis itens
HTTP e as duas triggers. A senha é solicitada de forma interativa e não é
gravada no projeto.

Na raiz do repositório, execute:

```bash
podman run --rm -it \
  --network host \
  -v "$PWD/scripts:/scripts:ro,z" \
  docker.io/library/python:3.12-alpine \
  python /scripts/configurar_zabbix.py
```

Informe o usuário do Zabbix e a senha atual. Ao terminar, confira o resultado
em `Monitoring > Latest data`.

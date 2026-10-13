# Tutorial de execução no Fedora

Este tutorial descreve a execução do laboratório de monitoramento usando Podman Compose. Os comandos devem ser executados na raiz do repositório.

## 1. Pré-requisitos

Confirmar que o sistema possui:

- Fedora atualizado;
- Podman;
- Podman Compose ou `podman compose`;
- Git;
- navegador web;
- acesso local à máquina com permissões para instalar serviços do host.

Verificar as versões:

```bash
podman --version
podman compose version
git --version
uname -a
```

Se `podman compose version` não funcionar, testar:

```bash
podman-compose --version
```

O tutorial usará `podman compose` como forma principal. Quando a instalação utilizar `podman-compose`, basta substituir o comando equivalente.

## 2. Conferir portas antes de começar

A captura recebida mostra containers associados às portas `3306`, `9000`, `9443`, `5432`, `6379` e `5540`. O projeto não usará essas portas.

Verificar as portas reservadas:

```bash
ss -ltn '( sport = :3100 or sport = :3200 or sport = :8081 or sport = :9091 or sport = :9101 )'
podman ps --all --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

As portas planejadas são:

| Serviço | Endereço local |
|---|---|
| Juice Shop | `http://localhost:3100` |
| Grafana | `http://localhost:3200` |
| Prometheus | `http://localhost:9091` |
| Zabbix Web | `http://localhost:8081` |
| Node Exporter | `http://localhost:9101/metrics`, se publicado |

Mesmo que os containers da imagem apareçam como `Exited`, as portas exibidas serão evitadas para não depender do estado atual deles.

## 3. Preparar o diretório do projeto

Criar os diretórios que serão utilizados:

```bash
mkdir -p app/juice-shop
mkdir -p clientes
mkdir -p prometheus/rules
mkdir -p grafana/provisioning/datasources
mkdir -p grafana/provisioning/dashboards
mkdir -p grafana/dashboards
mkdir -p zabbix/exports
mkdir -p scripts evidencias relatorio
```

## 4. Obter a aplicação

Clonar o repositório oficial do OWASP Juice Shop:

```bash
git clone --depth 1 https://github.com/juice-shop/juice-shop.git app/juice-shop
```

A aplicação é propositalmente vulnerável e deve ser usada somente localmente. Não configurar encaminhamento de porta para uma interface pública nem abrir essa porta no firewall para a rede externa.

## 5. Arquitetura do Compose

O arquivo `compose.yaml` deverá conter os seguintes serviços:

- `juice-shop`;
- `cliente-1`;
- `cliente-2`;
- `prometheus`;
- `grafana`;
- `zabbix-server`;
- `zabbix-web`;
- `zabbix-db`.

Todos os serviços devem compartilhar uma rede interna, por exemplo `monitoramento`. Dentro dessa rede, os containers devem acessar uns aos outros pelos nomes dos serviços, e não por `localhost`.

As portas externas planejadas são:

```yaml
ports:
  - "3100:3000" # Juice Shop
  - "3200:3000" # Grafana
  - "9091:9090" # Prometheus
  - "8081:8080" # Zabbix Web
```

O PostgreSQL e o Zabbix Server não precisam publicar portas para o host, pois serão acessados somente pela rede interna do Compose.

## 6. Criar o arquivo de configuração do Prometheus

Criar `prometheus/prometheus.yml` com os seguintes alvos conceituais:

```yaml
global:
  scrape_interval: 15s

rule_files:
  - /etc/prometheus/rules/*.yml

scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: ["prometheus:9090"]

  - job_name: node
    static_configs:
      - targets: ["host.containers.internal:9101"]

  - job_name: juice-shop
    metrics_path: /metrics
    static_configs:
      - targets: ["juice-shop:3000"]
```

O alvo do Juice Shop deverá ser ajustado caso a aplicação não exponha métricas Prometheus. Nesse caso, a disponibilidade HTTP será tratada pelo Zabbix ou por um exporter específico, e as métricas de infraestrutura continuarão vindo do Node Exporter.

## 7. Criar a regra de alerta do Prometheus

Criar `prometheus/rules/cpu.yml`:

```yaml
groups:
  - name: infraestrutura
    rules:
      - alert: CPUAlta
        expr: 100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[2m])) * 100) > 80
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: CPU acima de 80%
          description: O host {{ $labels.instance }} está com utilização elevada de CPU.
```

Depois de iniciar o Prometheus, verificar a regra em `http://localhost:9091/alerts`.

## 8. Configurar o Node Exporter no Fedora

O Node Exporter precisa observar o host Fedora. Ele não deve ser tratado como se fosse um exporter comum do container do Juice Shop.

Antes de escolher instalação nativa ou container, verificar a opção disponível no ambiente. Caso seja utilizado container, ele deverá receber as montagens e permissões necessárias para observar o host. Caso seja instalado nativamente, o serviço deverá escutar na porta local `9101` ou em outra porta livre.

Validar o funcionamento:

```bash
curl http://localhost:9101/metrics | head
```

Depois, a partir da rede do Compose, validar o nome `host.containers.internal`:

```bash
podman run --rm --network monitoramento docker.io/curlimages/curl:latest \
  http://host.containers.internal:9101/metrics
```

Se o nome não resolver, será necessário ajustar o `extra_hosts` do Compose para apontar `host.containers.internal` ao gateway do host.

## 9. Configurar o Zabbix

O Zabbix será composto por:

- PostgreSQL para armazenar os dados;
- Zabbix Server;
- frontend web;
- Zabbix Agent no Fedora.

O banco será utilizado somente pelo Zabbix e não deverá reutilizar o PostgreSQL da captura. O serviço do Zabbix Server deverá acessar o banco pelo nome do serviço Compose, por exemplo `zabbix-db:5432`.

No frontend, acessar:

```text
http://localhost:8081
```

Na primeira configuração:

1. confirmar a conexão com o banco;
2. entrar com a conta administrativa definida no Compose;
3. cadastrar o Fedora como host;
4. associar o template Linux apropriado;
5. informar o endereço do Zabbix Agent;
6. confirmar que o host ficou disponível;
7. verificar CPU, memória, disco e rede;
8. criar uma trigger de CPU acima de 80% por dois minutos.

As credenciais deverão ser definidas por variáveis em um arquivo `.env` local. Esse arquivo não deverá ser versionado.

## 10. Iniciar o ambiente

Na raiz do projeto:

```bash
podman compose config
podman compose pull
podman compose up -d
podman compose ps
```

Se for utilizada a ferramenta separada:

```bash
podman-compose config
podman-compose pull
podman-compose up -d
podman-compose ps
```

Consultar os logs quando algum serviço não iniciar:

```bash
podman compose logs --tail=100 juice-shop
podman compose logs --tail=100 prometheus
podman compose logs --tail=100 grafana
podman compose logs --tail=100 zabbix-server
podman compose logs --tail=100 zabbix-web
```

## 11. Validar a aplicação

Abrir no navegador:

```text
http://localhost:3100
```

Validar por terminal:

```bash
curl -I http://localhost:3100
```

Também conferir a rede interna:

```bash
podman network ls
podman network inspect monitoramento
```

## 12. Gerar requisições com dois clientes

Os clientes deverão permanecer dentro da rede Compose e executar requisições em intervalos controlados. O primeiro cliente poderá consultar a página principal e o segundo poderá consultar endpoints da API.

Exemplo conceitual de comando dentro de um cliente:

```bash
while true; do
  curl -s -o /dev/null -w "%{http_code}\n" http://juice-shop:3000/
  sleep 1
done
```

O teste deverá ter duração limitada. Não iniciar loops infinitos sem uma forma documentada de interrompê-los.

Verificar os logs e o consumo:

```bash
podman stats
podman compose logs --tail=50 cliente-1 cliente-2
```

## 13. Configurar o Grafana

Acessar:

```text
http://localhost:3200
```

Adicionar o Prometheus como fonte de dados usando a URL interna:

```text
http://prometheus:9090
```

O Grafana deve acessar o Prometheus pelo nome do serviço, e não por `localhost`.

Depois:

1. instalar ou habilitar a integração com Zabbix;
2. cadastrar o endereço interno do Zabbix Server/Web conforme o plugin exigir;
3. importar ou criar o dashboard;
4. salvar o dashboard como JSON em `grafana/dashboards/`;
5. testar painéis das duas fontes.

## 14. Executar o teste de alta CPU

Antes do teste, capturar o estado normal:

- dashboard do Grafana;
- dashboard do Zabbix;
- página de regras do Prometheus;
- estado dos containers.

Executar uma carga controlada por tempo limitado, preferencialmente dentro de um container com limite de CPU. Registrar o horário de início e término.

Durante o teste:

```bash
podman stats
top
curl http://localhost:9091/api/v1/query?query=up
```

Observar:

- aumento da CPU no Fedora;
- mudança no painel do Prometheus;
- mudança no item/trend do Zabbix;
- acionamento das duas condições de alerta;
- recuperação após interromper a carga.

## 15. Testar indisponibilidade

Parar somente o Juice Shop:

```bash
podman compose stop juice-shop
curl -I http://localhost:3100
```

Verificar o evento nos clientes e no Zabbix. Depois restaurar:

```bash
podman compose start juice-shop
curl -I http://localhost:3100
```

## 16. Exportar configurações

Salvar no repositório, sem senhas:

- `prometheus/prometheus.yml`;
- `prometheus/rules/`;
- JSON do dashboard do Grafana;
- exportação do host/template do Zabbix;
- configuração do Compose;
- scripts de carga;
- README com versões e comandos.

Não versionar:

- senhas reais;
- tokens;
- dumps desnecessários;
- credenciais administrativas;
- arquivos privados do usuário.

## 17. Capturas e vídeos

Capturar pelo menos:

1. containers funcionando;
2. Juice Shop acessível;
3. host cadastrado no Zabbix;
4. métricas no Zabbix;
5. Prometheus coletando dados;
6. Grafana com dashboard;
7. alerta de CPU;
8. estado durante alta CPU;
9. recuperação após o teste.

Gravar dois vídeos curtos:

- vídeo da instalação/subida dos serviços;
- vídeo da demonstração do monitoramento e do teste de carga.

## 18. Parar e limpar o ambiente

Para apenas os serviços do projeto:

```bash
podman compose down
```

Para remover também os volumes criados pelo projeto, somente quando for realmente necessário apagar os dados do laboratório:

```bash
podman compose down -v
```

O segundo comando remove o banco e os dados persistidos do Zabbix/Grafana definidos como volumes do projeto. Não utilizar comandos globais de limpeza do Podman, pois eles podem afetar os containers existentes na máquina.


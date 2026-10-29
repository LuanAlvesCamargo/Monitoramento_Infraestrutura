# Projeto de Monitoramento de Infraestrutura

## 1. Visão geral

Este projeto implementará um laboratório de monitoramento de infraestrutura utilizando a máquina Fedora como ambiente principal. Não será utilizada máquina virtual nem Ubuntu Server físico. Os serviços serão executados com Podman e Compose sempre que isso for tecnicamente adequado.

O projeto terá uma aplicação web baseada no OWASP Juice Shop, dois clientes e um bot de tráfego gerando requisições, Prometheus, Grafana e Zabbix. A aplicação será executada pela imagem oficial pré-construída do Juice Shop, evitando instalar dependências no Fedora. A mesma infraestrutura será observada por Zabbix e Prometheus, permitindo uma comparação prática entre as ferramentas.

## 2. Objetivo geral

Implementar e comparar duas abordagens open source de monitoramento de infraestrutura, observando CPU, memória, disco, rede, disponibilidade e comportamento durante uma situação controlada de alta utilização de CPU.

## 3. Objetivos específicos

- Executar uma aplicação web em container.
- Gerar tráfego por meio de dois containers clientes e um bot de navegação HTTP.
- Coletar métricas do Fedora com Prometheus e Node Exporter.
- Monitorar o host Fedora com Zabbix Server usando itens HTTP baseados nas métricas do Node Exporter/Prometheus.
- Criar alertas equivalentes nas duas ferramentas.
- Visualizar dados no frontend do Zabbix.
- Centralizar no Grafana informações do Prometheus e do Zabbix.
- Realizar um teste de carga e registrar o comportamento observado.
- Entregar configurações, evidências, relatório e vídeos da execução.

## 4. Arquitetura proposta

```text
                              Navegador
                         /       |        \
                        /        |         \
                 Grafana      Zabbix Web  Juice Shop
                   :3200         :8081       :3100
                    |              |            |
                    |         Zabbix Server     |
                    |              |            |
                    +------ Prometheus --------+
                           /          \
                    Node Exporter
                         |
                         +--- Fedora
                              |
                         Prometheus
                              |
                         Zabbix HTTP agent

             cliente-1  -----------+
             cliente-2  -----------+--> Juice Shop
             bot-trafego ----------+
```

### Serviços em Compose

Os seguintes componentes ficarão no arquivo `compose.yaml`:

- Juice Shop;
- cliente de carga 1;
- cliente de carga 2;
- bot de tráfego HTTP;
- Prometheus;
- Grafana;
- Zabbix Server;
- frontend web do Zabbix;
- dashboard Flask centralizado;
- banco PostgreSQL exclusivo do Zabbix.

### Coleta do host Fedora

O Node Exporter será executado pelo Compose com montagens somente leitura de `/proc`, `/sys` e `/`, além de acesso ao namespace do host. Assim, ele observará o Fedora, e não apenas o container do Juice Shop. Como o Fedora não disponibiliza o pacote `zabbix-agent2` nos repositórios padrão usados neste laboratório, o Zabbix Server consultará o Prometheus pela rede interna usando itens do tipo HTTP agent.

## 5. Portas reservadas

A captura fornecida mostra referências às portas `3306`, `9000`, `9443`, `5432`, `6379` e `5540`. Elas não serão utilizadas pelo projeto.

| Serviço | Porta no host | Porta no container | Uso |
|---|---:|---:|---|
| Juice Shop | 3100 | 3000 | Aplicação monitorada |
| Grafana | 3200 | 3000 | Dashboard centralizado |
| Prometheus | 9091 | 9090 | Consultas e métricas |
| Zabbix Web | 8081 | 8080 | Frontend do Zabbix |
| Zabbix Server | Apenas rede Compose | 10051 | Comunicação interna |
| PostgreSQL do Zabbix | Apenas rede Compose | 5432 | Banco interno |
| Node Exporter | 9101, se necessário | 9100 | Métricas do Fedora |
| Zabbix HTTP agent | Apenas rede Compose | — | Consulta Prometheus |

Antes da execução, as portas deverão ser confirmadas com `ss` e `podman ps`. Se alguma estiver ocupada, a alteração deverá ser feita somente na porta do host; as portas internas dos containers permanecem iguais.

## 6. Fluxo de dados

1. Os clientes enviam requisições ao Juice Shop.
2. O Fedora executa os containers e consome recursos de CPU, memória, disco e rede.
3. O Node Exporter expõe métricas do Fedora em formato Prometheus.
4. O Prometheus coleta essas métricas periodicamente.
5. O Zabbix Server consulta o Prometheus por itens do tipo HTTP agent.
6. O Grafana consulta o Prometheus e, posteriormente, o Zabbix.
7. O Zabbix Web apresenta hosts, itens, histórico, problemas e triggers.

## 7. Métricas e alertas

### Métricas principais

- Percentual de uso de CPU;
- memória utilizada e disponível;
- espaço utilizado no disco;
- bytes recebidos e transmitidos pela rede;
- disponibilidade do host;
- disponibilidade HTTP do Juice Shop;
- quantidade de requisições geradas pelos clientes;
- duração do teste de alta CPU.

### Alertas equivalentes

O primeiro alerta será CPU acima de 80% por dois minutos.

- No Zabbix: trigger baseada no item de CPU do host.
- No Prometheus: regra PromQL baseada no `node_cpu_seconds_total`.
- No Grafana: painel exibindo o estado das duas fontes.

Também poderá ser criado um alerta de indisponibilidade HTTP para o Juice Shop.

## 8. Dashboard centralizado no Grafana

O dashboard terá, no mínimo:

1. CPU do Fedora via Prometheus;
2. CPU do Fedora via Zabbix;
3. memória utilizada;
4. disco utilizado;
5. tráfego de rede;
6. disponibilidade do host;
7. disponibilidade do Juice Shop;
8. status dos alertas;
9. comparação durante o teste de alta CPU.

O Zabbix continuará sendo acessível pelo próprio frontend. O Grafana será usado como visão unificada e comparativa.

## 8.1 Situação atual da implementação

Já implementado e validado:

- Juice Shop acessível em `http://localhost:3100`;
- dois clientes e o `bot-trafego` gerando requisições HTTP;
- Node Exporter coletando métricas do Fedora;
- Prometheus com os alvos `prometheus` e `fedora-node` como `UP`;
- regra de CPU carregada no Prometheus;
- Grafana com datasource Prometheus e dashboard provisionados;
- Zabbix Server, frontend web e PostgreSQL executando em Compose.
- Dashboard Flask criado no Compose, com indicação da fonte em cada cartão,
  gráfico e tabela.

Ainda pendente:

- validar o host Fedora e os itens pela API do Zabbix;
- criar ou importar a visão do Zabbix no Grafana;
- preencher a credencial da API do Zabbix no `.env` e validar o dashboard Flask;
- executar e registrar o teste de alta CPU;
- exportar configurações, capturas e relatório final.

## 9. Testes práticos

### Teste 1 — funcionamento normal

- iniciar todos os serviços;
- acessar o Juice Shop;
- confirmar que os clientes estão gerando requisições;
- validar os dados no Prometheus, Zabbix e Grafana;
- capturar as telas do estado normal.

### Teste 2 — alta utilização de CPU

- iniciar uma carga controlada no Fedora;
- manter a carga por aproximadamente 90 segundos;
- observar a elevação da CPU;
- registrar quando Zabbix e Prometheus detectarem a condição;
- interromper a carga;
- observar a recuperação;
- guardar as capturas para o relatório.

### Teste 3 — indisponibilidade da aplicação

- parar o container do Juice Shop;
- verificar o erro nos clientes;
- observar o check HTTP no Zabbix e/ou Prometheus;
- iniciar novamente o container;
- registrar a recuperação.

## 10. Entregáveis do repositório

```text
compose.yaml
prometheus/prometheus.yml
prometheus/rules.yml
grafana/provisioning/
grafana/dashboards/
zabbix/exports/
clientes/
scripts/
evidencias/
relatorio/
README.md
```

Também deverão ser preservados:

- exportação do host/template do Zabbix;
- JSON do dashboard do Grafana;
- configurações de alertas;
- versões dos componentes;
- comandos utilizados;
- capturas de tela;
- vídeos da instalação e da demonstração.

## 11. Critérios de sucesso

O projeto será considerado funcional quando:

- todos os serviços puderem ser iniciados com Compose;
- a aplicação responder no navegador;
- dois clientes gerarem tráfego simultaneamente;
- Prometheus coletar métricas do Fedora;
- Zabbix monitorar o mesmo Fedora;
- CPU, memória, disco, rede e disponibilidade forem visualizados;
- pelo menos um alerta funcionar em cada ferramenta;
- o teste de alta CPU for detectado;
- o dashboard comparativo estiver disponível;
- a solução puder ser explicada e reproduzida a partir dos arquivos entregues.

## 12. Limites do projeto

Não serão incluídos inicialmente Kubernetes, CI/CD, Loki, Alertmanager, banco da aplicação ou exposição pública na Internet. Esses recursos podem ser adicionados apenas se houver tempo e se não prejudicarem a demonstração principal.

O Juice Shop é uma aplicação propositalmente vulnerável. Ela deverá permanecer restrita ao ambiente local e não deverá ser publicada em uma interface acessível pela Internet.

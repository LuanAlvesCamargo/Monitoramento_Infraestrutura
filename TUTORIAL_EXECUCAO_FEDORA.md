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

## 4. Obter a aplicação (opcional)

O repositório pode ser clonado apenas para consulta e estudo do código:

```bash
git clone --depth 1 https://github.com/juice-shop/juice-shop.git app/juice-shop
```

A pasta `app/juice-shop/` está no `.gitignore` porque não será versionada no projeto principal. O Compose utilizará a imagem oficial pré-construída, evitando instalar Node.js/npm no Fedora e evitando reconstruir as dependências localmente.

A aplicação é propositalmente vulnerável e deve ser usada somente localmente. Não configurar encaminhamento de porta para uma interface pública nem abrir essa porta no firewall para a rede externa.

## 5. Arquitetura do Compose

O arquivo `compose.yaml` deverá conter os seguintes serviços:

- `juice-shop`;
- `cliente-1`;
- `cliente-2`;
- `bot-trafego`;
- `prometheus`;
- `grafana`;
- `zabbix-server`;
- `zabbix-web`;
- `zabbix-db`.

Para o Juice Shop, a configuração inicial utiliza a imagem oficial:

```yaml
juice-shop:
  image: docker.io/bkimminich/juice-shop:latest
  ports:
    - "3100:3000"
```

Não usar `npm install` nem `podman compose build juice-shop` no Fedora nesta etapa.

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

## 6. Configurar o Prometheus

O arquivo `prometheus/prometheus.yml` já está criado com dois alvos:

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
```

O alvo `fedora-node` representa o host Fedora. O Juice Shop não será coletado diretamente pelo Prometheus nesta etapa porque sua aplicação não é o coletor de infraestrutura. A disponibilidade HTTP será adicionada posteriormente com o Zabbix ou um exporter específico.

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

## 8. Executar o Node Exporter no Fedora

O Node Exporter precisa observar o host Fedora. Ele não deve ser tratado como se fosse um exporter comum do container do Juice Shop.

Nesta etapa, o Node Exporter é executado pelo Compose com montagens somente leitura de `/proc`, `/sys` e `/`. Essas montagens permitem que ele observe o Fedora, em vez de medir apenas o container do Juice Shop.

O serviço usa internamente a porta `9100` e publica a porta `9101` no host.

Validar o funcionamento:

```bash
curl http://localhost:9101/metrics | head
```

Depois, a partir do container do Prometheus, validar o alvo:

```bash
podman exec monitoramento-prometheus \
  wget -q -O - http://host.containers.internal:9101/metrics | head
```

Se esse comando não resolver o nome do host, verificar os logs do Prometheus e, se necessário, adicionar um mapeamento `extra_hosts` no serviço `prometheus`.

## 9. Configurar o Zabbix

O Zabbix será composto por:

- PostgreSQL para armazenar os dados;
- Zabbix Server;
- frontend web;
- Zabbix Agent no Fedora.

O banco será utilizado somente pelo Zabbix e não deverá reutilizar o PostgreSQL da captura. O serviço do Zabbix Server acessa o banco pelo nome do serviço Compose `zabbix-db:5432`.

Subir a parte do Zabbix com:

```bash
podman compose pull zabbix-db zabbix-server zabbix-web
podman compose up -d zabbix-db zabbix-server zabbix-web
podman compose ps
```

No frontend, acessar:

```text
http://localhost:8081
```

Credenciais iniciais padrão do frontend:

```text
Usuário: Admin
Senha: zabbix
```

Alterar a senha após o primeiro acesso. A senha do banco está no `.env` local e não deve ser commitada.

Na primeira configuração:

1. entrar com a conta administrativa padrão;
2. cadastrar o Fedora como host;
3. associar o template Linux apropriado;
4. informar o endereço do Zabbix Agent;
5. confirmar que o host ficou disponível;
6. verificar CPU, memória, disco e rede;
7. criar uma trigger de CPU acima de 80% por dois minutos.

As credenciais deverão ser definidas por variáveis em um arquivo `.env` local. Esse arquivo não deverá ser versionado.

## 10. Iniciar o ambiente

Na raiz do projeto:

```bash
podman compose config
podman compose pull prometheus node-exporter grafana zabbix-db zabbix-server zabbix-web
podman compose up -d prometheus node-exporter grafana zabbix-db zabbix-server zabbix-web
podman compose ps
```

Aguarde pelo menos 15 segundos, que é o intervalo definido em `scrape_interval`, antes de verificar os alvos.

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
podman compose logs --tail=100 node-exporter
podman compose logs --tail=100 grafana
podman compose logs --tail=100 zabbix-server
podman compose logs --tail=100 zabbix-web
```

O pacote oficial do Zabbix não oferece uma instalação específica para Fedora nas opções principais documentadas. Por isso, o Zabbix Server, o frontend e o banco ficam em containers. A instalação do agente que observará diretamente o Fedora será definida separadamente, sem tratar um agente comum de container como se fosse o host.

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

## 12. Gerar requisições com dois clientes e um bot

Os clientes permanecem dentro da rede Compose e não publicam portas no Fedora. A configuração atual utiliza dois containers Alpine:

- `cliente-1` pesquisa `apple` na API a cada dois segundos;
- `cliente-2` pesquisa `banana` na API a cada três segundos.
- `bot-trafego` simula uma navegação contínua, acessando a página inicial e buscas diferentes aproximadamente uma vez por segundo.

Eles podem ser iniciados com:

```bash
podman compose up -d cliente-1 cliente-2 bot-trafego
```

Validar os containers:

```bash
podman compose ps
```

Os clientes acessam a API de busca em `http://juice-shop:3000/rest/products/search`, usando o nome do serviço na rede interna, e não `localhost`.

No navegador, a busca aparece como `http://localhost:3100/#/search`. O trecho depois de `#` é uma rota do frontend e não é enviado diretamente ao servidor HTTP; a aplicação executa a chamada da API de busca por trás da tela. Por isso, os clientes usam o endpoint REST correspondente.

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
podman compose logs --tail=50 cliente-1 cliente-2 bot-trafego
```

### Manter o bot em execução

O serviço `bot-trafego` possui `restart: unless-stopped`. Para iniciá-lo ou
recriá-lo:

```bash
podman compose up -d bot-trafego
```

Para confirmar que está ativo:

```bash
podman ps --filter name=monitoramento-bot-trafego
```

Para parar somente o bot:

```bash
podman compose stop bot-trafego
```

O texto `monitoramento-bot-trafego Up` exibido pelo `podman ps` é um status,
e não deve ser digitado como comando. O parâmetro `-f` em `podman logs -f`
acompanha os logs continuamente; `Ctrl+C` encerra apenas o acompanhamento.

Depois de reiniciar o Fedora, os serviços podem ser restaurados com:

```bash
podman compose up -d
```

Essa execução manual será automatizada posteriormente com `systemd --user`,
caso seja necessário iniciar o laboratório automaticamente no login.

## 13. Configurar o Grafana

Acessar:

```text
http://localhost:3200
```

Login inicial definido no `.env` local:

```text
Usuário: admin
Senha: monitoramento-local-2026
```

O Prometheus e o dashboard são provisionados automaticamente pelos arquivos:

```text
grafana/provisioning/datasources/prometheus.yml
grafana/provisioning/dashboards/dashboards.yml
grafana/dashboards/infraestrutura-prometheus.json
```

A fonte de dados usa a URL interna:

```text
http://prometheus:9090
```

O Grafana deve acessar o Prometheus pelo nome do serviço, e não por `localhost`.

Depois:

1. abrir o dashboard na pasta `Infraestrutura`;
2. confirmar os painéis de CPU, memória, disco, rede e targets;
3. instalar a integração com Zabbix quando o servidor estiver cadastrado;
4. testar os painéis das duas fontes.

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

## 19. Dashboard Flask centralizado

O projeto possui um dashboard próprio em:

```text
http://localhost:3300
```

Ele consulta as APIs internas do Prometheus e do Zabbix e verifica a
disponibilidade do Juice Shop. Cada cartão, gráfico e tabela identifica sua
fonte de dados.

Para construir ou atualizar o container:

```bash
podman compose up -d --build dashboard
```

Para validar:

```bash
curl http://localhost:3300/health
```

Para exibir dados do Zabbix, inclua no `.env` local:

```text
ZABBIX_API_USER=Admin
ZABBIX_API_PASSWORD=senha-atual-do-zabbix
DASHBOARD_PORT=3300
```

Não versionar o `.env`.

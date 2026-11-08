# Planejamento — JurisDocs

## 1. Identificação

**Título:** JurisDocs — gerenciamento de documentos jurídicos fictícios com MongoDB e Redis.

O JurisDocs será uma aplicação web acadêmica para cadastrar e consultar documentos jurídicos fictícios. Não armazenará dados pessoais ou documentos reais e não prestará aconselhamento jurídico.

O ambiente será executado integralmente em containers com Podman e `podman compose`, no Fedora. Python, Node.js, MongoDB e Redis não serão instalados no sistema hospedeiro para executar a aplicação.

## 2. Delimitação acadêmica

O trabalho exige uma tecnologia NoSQL aplicada de forma prática, pesquisa técnica, instalação e configuração, organização de dados, CRUD completo e evidências.

- **MongoDB:** tecnologia NoSQL principal e fonte persistente de verdade.
- **Redis:** tecnologia complementar, usada somente como cache de consultas frequentes.
- O MongoDB continuará sendo consultável e persistente mesmo após a expiração ou a invalidação do cache Redis.

Essa divisão deve ser apresentada ao professor: o MongoDB atende ao requisito de banco escolhido; o Redis demonstra uma otimização de infraestrutura, não substitui o banco principal.

## 3. Objetivos

### Objetivo geral

Desenvolver uma aplicação web conteinerizada para gerenciamento de documentos jurídicos fictícios usando MongoDB como banco principal e Redis como cache.

### Objetivos específicos

- Pesquisar modelo de documentos, recursos, limitações, segurança, licenciamento e ecossistema do MongoDB.
- Criar ambiente reproduzível com Podman Compose.
- Executar MongoDB, Redis, API Flask e frontend React em containers independentes.
- Implementar CRUD completo, filtros, paginação e busca textual.
- Criar ao menos cinco documentos fictícios.
- Demonstrar `HIT`, `MISS`, expiração e invalidação do cache Redis.
- Produzir testes, evidências e documentação técnica para o relatório.

## 4. Arquitetura

```text
Navegador
    │
    ▼
Frontend React + Nginx
    │ /api
    ▼
API Flask
 ┌──┴───────────────┐
 ▼                  ▼
Redis             MongoDB
Cache             Persistência principal
```

| Serviço | Função | Persistência |
|---|---|---|
| `frontend` | Interface React entregue por Nginx | Não necessária |
| `api` | API, validação, CRUD e cache-aside | Não necessária |
| `mongodb` | Banco principal | Volume `mongodb-data` |
| `redis` | Cache temporário | Volume `redis-data`, com AOF |

Portas iniciais propostas, sujeitas a verificação antes da execução: React `5174`, API `5050`, MongoDB `27018` e Redis `6380`.

## 5. Tecnologias

| Camada | Tecnologia | Justificativa |
|---|---|---|
| Orquestração | Podman + Podman Compose | Ambiente local reproduzível e compatível com Compose |
| Banco principal | MongoDB | Modelo flexível de documentos, adequado a cadastros e metadados |
| Cache | Redis | Respostas de baixa latência para leituras repetidas |
| Backend | Python + Flask | API simples, didática e compatível com o escopo |
| Acesso a dados | PyMongo e redis-py | Clientes Python para MongoDB e Redis |
| Frontend | React + Vite | Interface reativa para CRUD e filtros |
| Servidor web | Nginx | Entrega do frontend e proxy para `/api` |
| Testes | Pytest | Validação do CRUD e do cache |

## 6. Dados e índices

Coleção principal: `documentos`.

```json
{
  "numero": "DOC-2026-0001",
  "titulo": "Contrato fictício de prestação de serviços",
  "tipo": "Contrato",
  "descricao": "Registro criado para demonstração acadêmica.",
  "status": "Ativo",
  "tags": ["contrato", "servicos", "demonstracao"],
  "dataCriacao": "Date BSON",
  "dataAtualizacao": "Date BSON"
}
```

Índices previstos:

- `numero` único;
- índice textual em `titulo`, `descricao` e `tags`;
- índice composto em `tipo`, `status` e `dataCriacao`.

Dados iniciais mínimos: contrato, petição inicial, parecer jurídico, termo de confidencialidade e notificação extrajudicial — todos fictícios e com estados variados.

## 7. API Flask

| Método | Rota | Finalidade |
|---|---|---|
| `GET` | `/api/health` | Verificar API, MongoDB e Redis |
| `GET` | `/api/documentos` | Listagem com filtros e paginação |
| `POST` | `/api/documentos` | Criar documento |
| `GET` | `/api/documentos/:id` | Consultar por identificador |
| `PUT` | `/api/documentos/:id` | Atualizar documento |
| `DELETE` | `/api/documentos/:id` | Excluir documento |
| `GET` | `/api/estatisticas` | Totalizações, se implementado |

Filtros: texto, tipo, status, tag, intervalo de datas, página e limite. A API usará `400` para validação inválida, `404` para recurso ausente e `409` para número duplicado.

## 8. Cache Redis

Será usado o padrão **cache-aside**:

1. A API procura a consulta no Redis.
2. Se encontrada, retorna `HIT`.
3. Se ausente, consulta o MongoDB, armazena o resultado e retorna `MISS`.
4. Criação, atualização e exclusão invalidam chaves relacionadas.
5. Falha do Redis não interrompe a API: a leitura ocorre no MongoDB com `BYPASS`.

Chaves previstas:

```text
jurisdocs:documento:{id}
jurisdocs:listagem:v1:{hash-dos-filtros}
jurisdocs:estatisticas:v1
```

O TTL inicial será de 60 segundos. A origem da resposta será visível em `X-Cache` e/ou `_meta.cache`.

## 9. Interface React

A interface terá listagem, filtros, formulário de criação/edição, detalhes, confirmação de exclusão, notificações e indicação da origem da leitura (`MongoDB`, `Redis`, `HIT` ou `MISS`). O Nginx encaminhará `/api` para o container Flask, evitando CORS no ambiente local.

## 10. Estrutura prevista

```text
JurisDocs/
├── api/
├── frontend/
├── mongo/init/
├── redis/
├── scripts/
├── tests/
├── evidencias/
├── compose.yaml
├── .env.example
├── .gitignore
├── README.md
├── PLANEJAMENTO_JURISDOCS.md
└── TUTORIAL_EXECUCAO_PODMAN.md
```

Credenciais locais ficarão em `.env`, ignorado pelo Git. O arquivo `.env.example` conterá apenas valores de exemplo sem segredo real.

## 11. Etapas

1. Preparar Compose, variáveis e configurações dos bancos.
2. Subir MongoDB e Redis e registrar evidências de conexão e persistência.
3. Desenvolver a API Flask e validar CRUD por terminal/API.
4. Implementar e demonstrar o cache Redis.
5. Criar o frontend React integrado.
6. Executar testes automatizados e testes manuais.
7. Produzir documentação, capturas e relatório técnico-científico.

## 12. Evidências previstas

| Evidência | Demonstração |
|---|---|
| Ambiente | versões de Fedora, Podman, Compose e Git |
| Containers | serviços em execução no `podman compose ps` |
| MongoDB | banco, coleção, índices e documentos persistidos |
| Redis | `PING`, chaves, TTL e cache |
| CRUD | criação, leitura, filtro, atualização, exclusão e prova de persistência |
| Cache | primeira consulta `MISS` e repetição `HIT` |
| Interface | React integrado à API |
| Testes | execução e resultado dos testes |

Capturas não deverão exibir senhas, URIs com credenciais ou dados reais.

## 13. Critérios de aceite

- Um único comando sobe os quatro containers.
- Há ao menos cinco documentos fictícios persistidos.
- CRUD e filtros funcionam pela API e interface.
- O cache demonstra `HIT`, `MISS`, TTL e invalidação após escrita.
- A API continua respondendo pelo MongoDB caso o Redis esteja indisponível.
- Os testes principais passam e as evidências estão catalogadas.

## 14. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Conflito de portas ou Redis existente | Conferir portas e identificar o container exato antes de removê-lo/criar o novo |
| Credenciais expostas | Usar `.env` ignorado e ocultar valores em capturas |
| Cache desatualizado | TTL e invalidação em toda escrita |
| Redis indisponível | Fallback para MongoDB com `BYPASS` |
| Aumento de escopo | Priorizar CRUD, cache, testes e evidências |

## 15. Situação atual da infraestrutura

| Item | Situação | Evidência |
|---|---|---|
| Script de infraestrutura | Concluído | `scripts/01_subir_infraestrutura.sh` |
| MongoDB | Em execução e saudável | Porta local `27018` e volume persistente |
| Redis | Em execução e saudável | Porta local `6380` e volume persistente |
| Rede interna | Criada | `jurisdocs_jurisdocs-net` |
| Evidências de infraestrutura | Coletadas localmente | `evidencias/infraestrutura/` (ignorada pelo Git) |
| API Flask | Não iniciada | Próxima etapa de desenvolvimento |
| Frontend React | Não iniciado | Dependente da API |

Os bancos foram instalados com apenas o usuário administrador do MongoDB e a senha do Redis. A coleção, o usuário específico da API, os índices e os dados fictícios ainda não foram criados.

## 16. Roteiro de desenvolvimento pós-infraestrutura

O desenvolvimento seguirá os marcos abaixo. Cada marco terá uma verificação objetiva antes do início do seguinte.

### Marco 1 — Configuração acadêmica dos bancos

**Objetivo:** preparar MongoDB e Redis para uso pela aplicação sem criar a API ainda.

- Criar o usuário MongoDB `jurisdocs_api` com permissão limitada de leitura e escrita no banco `jurisdocs`.
- Criar a coleção `documentos`.
- Criar índices: `numero` único; texto em título, descrição e tags; composto para filtros.
- Inserir cinco documentos jurídicos exclusivamente fictícios.
- Validar conexão com administrador e com o usuário da aplicação.
- Validar Redis com `PING`, escrita, leitura, expiração de chave e persistência AOF.

**Evidências:** comandos `mongosh`, listagem dos cinco documentos, listagem de índices, saída `PONG`, valor e TTL de uma chave Redis.

**Critério de aprovação:** dados persistem após reiniciar ambos os containers e nenhuma senha aparece nas capturas.

> Observação: os scripts de inicialização automática do MongoDB só são executados em um volume vazio. Como o volume já foi criado, essa configuração será realizada por um script administrativo idempotente, sem apagar o banco.

### Marco 2 — Base da API Flask

**Objetivo:** criar o container Flask e a estrutura da aplicação.

- Criar `api/Dockerfile`, dependências Python e estrutura modular da API.
- Adicionar o serviço `api` ao `compose.yaml`, dependente dos healthchecks dos bancos.
- Configurar variáveis de conexão internas: `mongodb:27017` e `redis:6379`.
- Implementar `GET /api/health` verificando API, MongoDB e Redis.
- Criar validação de payload, serialização de `ObjectId` e tratamento padronizado de erros.

**Evidências:** container da API saudável, resposta JSON de `/api/health` e logs sem credenciais.

**Critério de aprovação:** a API consulta os dois serviços pelo nome interno da rede, sem depender de `localhost` dentro do container.

### Marco 3 — CRUD MongoDB

**Objetivo:** cumprir integralmente as operações exigidas no projeto.

- `POST /api/documentos`: criar documento e validar campos obrigatórios.
- `GET /api/documentos`: listar, paginar, filtrar e pesquisar.
- `GET /api/documentos/<id>`: obter um documento.
- `PUT /api/documentos/<id>`: atualizar e registrar `dataAtualizacao`.
- `DELETE /api/documentos/<id>`: excluir e confirmar ausência.
- Retornar `400`, `404` e `409` adequadamente.

**Evidências:** uma captura ou resposta para Create, Read geral, Read por ID/filtro, Update, Delete e prova de persistência no MongoDB.

**Critério de aprovação:** todos os endpoints respondem corretamente e as alterações são comprovadas por consulta direta ao MongoDB.

### Marco 4 — Cache-aside com Redis

**Objetivo:** integrar o Redis sem transformá-lo em fonte primária de dados.

- Cachear consulta por ID, listagens filtradas e estatísticas.
- Usar TTL de 60 segundos.
- Incluir `X-Cache: HIT`, `MISS` ou `BYPASS` nas respostas de leitura.
- Invalidar chaves relacionadas em Create, Update e Delete.
- Permitir que a API continue pelo MongoDB quando Redis estiver indisponível.

**Evidências:** primeira consulta `MISS`, repetição `HIT`, TTL Redis, invalidação após alteração e comportamento `BYPASS` controlado.

**Critério de aprovação:** resposta após escrita nunca apresenta valor antigo do cache.

### Marco 5 — Frontend React

**Objetivo:** construir uma interface gráfica que consuma exclusivamente a API Flask.

- Criar projeto React e imagem de produção entregue por Nginx.
- Adicionar serviço `frontend` ao Compose.
- Criar listagem, filtros, formulário de inclusão/edição, detalhes e exclusão com confirmação.
- Mostrar mensagens de erro/sucesso e indicação visual da origem do cache.
- Encaminhar `/api` por proxy Nginx para a API, evitando CORS no ambiente local.

**Evidências:** tela de listagem, filtro, criação, edição, exclusão e indicador `HIT`/`MISS`.

**Critério de aprovação:** a aplicação é utilizável pelo navegador em uma única URL local e não acessa MongoDB ou Redis diretamente pelo frontend.

### Marco 6 — Testes e robustez

**Objetivo:** demonstrar que a solução funciona além da interface visual.

- Criar testes Pytest do healthcheck, CRUD, validações e invalidação de cache.
- Verificar reinício dos containers e persistência dos dados.
- Verificar parada controlada do Redis e resposta `BYPASS` da API.
- Revisar logs, `.gitignore` e ausência de credenciais no Git.

**Evidências:** saída dos testes, `podman compose ps`, verificação de persistência e captura do fallback.

**Critério de aprovação:** testes essenciais passam e nenhum segredo é versionado.

### Marco 7 — Documentação e entrega

**Objetivo:** preparar material técnico/científico e demonstração prática.

- Criar `README.md` com visão geral, arquitetura, pré-requisitos e comandos principais.
- Criar `TUTORIAL_EXECUCAO_PODMAN.md` com roteiro reproduzível e pontos de captura.
- Atualizar este planejamento com resultados obtidos e decisões finais.
- Organizar evidências, legenda das imagens e comparação crítica entre MongoDB e Redis.
- Produzir o relatório final conforme a estrutura acadêmica solicitada.

**Critério de aprovação:** qualquer integrante consegue subir o ambiente a partir do repositório, sem utilizar dados reais ou expor senhas.

## 17. Ordem obrigatória de execução

```text
Marco 1: bancos configurados
        ↓
Marco 2: API e healthcheck
        ↓
Marco 3: CRUD persistente
        ↓
Marco 4: cache Redis
        ↓
Marco 5: interface React
        ↓
Marco 6: testes e tolerância a falhas
        ↓
Marco 7: documentação e relatório
```

O desenvolvimento não deve avançar de marco enquanto seu critério de aprovação não estiver confirmado.

## 18. Próximos passos de implementação

Os marcos 1 a 3 foram concluídos e os marcos 4 a 6 foram aprovados. O avanço ocorre agora com cache-aside Redis, interface React local e testes de robustez.

## 19. Registro de execução — Marcos 1 a 3

**Data da execução:** 02 de novembro de 2026.

### Marco 1 — Configuração dos bancos

**Situação: concluído e validado.**

- O script `scripts/02_configurar_bancos.sh` foi criado de forma idempotente.
- O usuário `jurisdocs_api` foi criado com permissão `readWrite` somente no banco `jurisdocs`.
- A coleção `documentos` recebeu os índices `uq_documentos_numero`, `idx_documentos_texto` e `idx_tipo_status_data`.
- Foram inseridos cinco documentos jurídicos fictícios.
- Redis respondeu a `PING` com `PONG`, aceitou escrita e informou TTL de 60 segundos para a chave de verificação.
- MongoDB e Redis foram reiniciados; os cinco documentos continuaram disponíveis.

### Marco 2 — Base da API Flask

**Situação: concluído e validado.**

- O serviço `api` foi adicionado ao `compose.yaml` e exposto somente em `127.0.0.1:5050`.
- A imagem é construída a partir de `api/Dockerfile` com Python 3.13, Flask, Gunicorn, PyMongo e redis-py.
- A API conecta-se internamente a `mongodb:27017` e `redis:6379` pela rede `jurisdocs-net`.
- O endpoint `GET /api/health` retornou HTTP 200 com `api`, `mongodb` e `redis` no estado `ok`.
- A compilação dos módulos Python foi validada dentro do container.

### Marco 3 — CRUD persistente

**Situação: concluído e validado.**

- `POST /api/documentos` criou um registro fictício de teste.
- `GET /api/documentos/<id>` recuperou o registro criado.
- `GET /api/documentos` validou filtro por tipo e status; a busca textual por `contrato` retornou o documento correspondente.
- `PUT /api/documentos/<id>` alterou status e tags, preservando a data de criação e atualizando a data de modificação.
- `DELETE /api/documentos/<id>` retornou HTTP 204; a consulta posterior retornou HTTP 404.
- Após remover o registro de teste, a API confirmou exatamente cinco documentos semeados.

### Evidências locais

Os logs de instalação, configuração e validação foram salvos em `evidencias/infraestrutura/`. A pasta permanece ignorada pelo Git para evitar versionar capturas locais ou informações transitórias.

## 20. Registro de execução — Marcos 4 a 6

**Data da execução:** 02 de novembro de 2026.

### Marco 4 — Cache-aside Redis

**Situação: concluído e validado.**

- TTL de 60 segundos para listagens e consultas individuais.
- Cabeçalho `X-Cache` com os estados `MISS`, `HIT` e `BYPASS`.
- Invalidação de chaves de lista e do documento afetado após criação, edição ou exclusão.
- A indisponibilidade do Redis é tratada como degradação controlada, sem bloquear o CRUD do MongoDB.

### Marco 5 — Interface React

**Situação: concluído e validado.**

- React é compilado no contêiner e servido por Nginx.
- O proxy Nginx encaminha somente `/api` para Flask na rede interna.
- A interface apresenta listagem, filtros, criação, edição, exclusão e o último estado do cache.
- A porta local planejada é `127.0.0.1:5174`.

### Marco 6 — Testes e tolerância a falhas

**Situação: concluído e validado.**

- Teste Pytest cobre CRUD e a sequência `MISS → HIT → MISS` após uma escrita.
- O script `scripts/03_validar_fallback_redis.sh` interrompe somente Redis, confirma `BYPASS` e o restaura com healthcheck.
- A validação final inclui os serviços, testes, fallback e a interface pelo navegador.

### Resultados consolidados

- O teste automatizado retornou `1 passed`, cobrindo criação, consulta, `MISS`, `HIT`, atualização, invalidação e exclusão.
- A simulação de indisponibilidade temporária do Redis retornou `X-Cache: BYPASS`; a listagem continuou disponível pelo MongoDB e o Redis foi restaurado saudável.
- MongoDB, Redis, Flask e Nginx/React finalizaram com healthchecks saudáveis.
- A interface local foi conferida em navegador com os cinco documentos fictícios, filtros, ações de CRUD e indicador de cache disponíveis.

## 21. Registro de execução — Marco 7

**Data da execução:** 02 de novembro de 2026.

**Situação: concluído e validado.**

- `README.md` foi atualizado com arquitetura, serviços, URLs, início rápido, validações e estrutura do repositório.
- `TUTORIAL_EXECUCAO_PODMAN.md` documenta o roteiro reproduzível, os comandos de teste, a persistência e os pontos para captura de evidências.
- O relatório `relatorio/Relatorio_Tecnico_Cientifico_JurisDocs.docx` foi produzido com 13 páginas, fundamentação, metodologia, implementação, resultados, limitações, referências, figuras e apêndice.
- Foi adicionada uma captura real da interface local, além das evidências existentes de contêineres, volumes, rede e testes.
- A versão final foi renderizada e revisada visualmente; não foram identificados cortes de texto, tabelas ilegíveis ou figuras fora da página.
- A validação final confirmou healthcheck HTTP 200, busca textual por contrato, `X-Cache: MISS` seguido de `X-Cache: HIT`, Pytest com `1 passed`, quatro serviços saudáveis e `.env` ignorado pelo Git.

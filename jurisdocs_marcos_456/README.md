# JurisDocs

JurisDocs é um projeto acadêmico de Banco de Dados NoSQL para catalogar documentos jurídicos fictícios. A aplicação usa MongoDB como base principal, Redis como cache complementar, Flask como API e React como interface web. Todo o ambiente executa localmente com Podman Compose.

> Os registros são inteiramente fictícios e não constituem informação jurídica, processo real ou orientação profissional.

## Arquitetura

```text
Navegador
   │ http://127.0.0.1:5174
   ▼
React + Nginx ── /api ──► Flask + Gunicorn
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
            MongoDB 8.0                    Redis 7.4
          dados persistentes          cache-aside com TTL
```

O MongoDB mantém a coleção `documentos`, índices de unicidade, busca textual e filtros. O Redis armazena temporariamente consultas e respostas por documento. A API informa o resultado do cache no cabeçalho `X-Cache`: `MISS`, `HIT` ou `BYPASS`.

## Serviços e URLs

| Serviço | Finalidade | Endereço local |
|---|---|---|
| Frontend | Interface React servida por Nginx | http://127.0.0.1:5174 |
| API Flask | Endpoints REST e healthcheck | http://127.0.0.1:5050/api/health |
| MongoDB | Banco de documentos | 127.0.0.1:27018 |
| Redis | Cache persistente AOF | 127.0.0.1:6380 |

As portas de banco são vinculadas a `127.0.0.1`; não ficam expostas para a rede local.

## Início rápido

```bash
cd /home/luancamargo/Documentos/GitHub/JurisDocs
./scripts/01_subir_infraestrutura.sh
./scripts/02_configurar_bancos.sh
podman compose -p jurisdocs up -d --build
podman compose -p jurisdocs ps
```

## Validação

```bash
podman compose -p jurisdocs exec -T api python -m pytest -q
./scripts/03_validar_fallback_redis.sh
curl http://127.0.0.1:5050/api/health
```

O segundo comando interrompe somente o Redis por alguns segundos, confirma que leituras continuam disponíveis pelo MongoDB com `X-Cache: BYPASS` e restaura o serviço automaticamente.

## Funcionalidades

- cadastro, listagem, busca textual, filtros, edição e remoção de documentos;
- cinco registros fictícios semeados de forma idempotente;
- número do documento único;
- cache-aside com TTL de 60 segundos e invalidação após escrita;
- healthchecks de MongoDB, Redis, API e frontend;
- persistência por volumes nomeados;
- teste automatizado de CRUD, cache e invalidação.

## Estrutura

```text
api/            API Flask, regras de cache e testes
frontend/       React, Vite e Nginx
scripts/        instalação, configuração e validação
evidencias/     capturas locais ignoradas pelo Git
relatorio/      relatório técnico-científico final
compose.yaml    definição dos serviços Podman Compose
```

Leia [TUTORIAL_EXECUCAO_PODMAN.md](TUTORIAL_EXECUCAO_PODMAN.md) para o roteiro completo e [PLANEJAMENTO_JURISDOCS.md](PLANEJAMENTO_JURISDOCS.md) para as decisões do projeto.

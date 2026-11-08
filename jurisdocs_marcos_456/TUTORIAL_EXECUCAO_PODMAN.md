# Tutorial de execução do JurisDocs com Podman

## 1. Pré-requisitos

Confirme Podman e o provedor Compose:

```bash
podman --version
podman compose version
```

O projeto foi validado em Fedora Linux. Não é necessário instalar MongoDB, Redis, Python, Node.js ou Nginx no sistema hospedeiro: essas dependências estão nos contêineres.

## 2. Preparar o ambiente

Na raiz do repositório:

```bash
chmod +x scripts/*.sh
./scripts/01_subir_infraestrutura.sh
./scripts/02_configurar_bancos.sh
podman compose -p jurisdocs up -d --build
```

O primeiro script cria `.env` caso ele não exista e sobe MongoDB e Redis. O segundo cria usuário com escopo restrito, índices e cinco documentos fictícios. A configuração é idempotente: pode ser executada novamente sem duplicar a massa inicial.

## 3. Confirmar os serviços

```bash
podman compose -p jurisdocs ps
curl http://127.0.0.1:5050/api/health
```

Resultado esperado para o healthcheck:

```json
{"api":"ok","mongodb":"ok","redis":"ok"}
```

Todos os contêineres devem aparecer como `healthy`.

## 4. Abrir a interface

Abra `http://127.0.0.1:5174` no navegador. A tela permite:

1. consultar os cinco documentos fictícios;
2. buscar texto e filtrar por tipo e status;
3. cadastrar um documento pelo botão **Novo documento**;
4. editar ou excluir um registro;
5. observar o indicador de cache Redis no topo.

## 5. Demonstrar a API

```bash
curl -i 'http://127.0.0.1:5050/api/documentos?limite=5'
curl -i 'http://127.0.0.1:5050/api/documentos?limite=5'
```

A primeira chamada normalmente traz `X-Cache: MISS`; a segunda, antes de 60 segundos, traz `X-Cache: HIT`. Qualquer POST, PUT ou DELETE invalida as listagens afetadas.

## 6. Executar testes

```bash
podman compose -p jurisdocs exec -T api python -m pytest -q
./scripts/03_validar_fallback_redis.sh
```

O teste Pytest cobre o CRUD e a sequência `MISS → HIT → MISS` após atualização. O script de fallback faz uma parada temporária apenas do Redis, valida `X-Cache: BYPASS` e restaura o serviço.

## 7. Encerrar e retomar

```bash
podman compose -p jurisdocs stop
podman compose -p jurisdocs start
```

Volumes nomeados preservam MongoDB e Redis. Para remover contêineres sem apagar os dados:

```bash
podman compose -p jurisdocs down
```

Não use `down -v` se quiser manter a massa persistida.

## 8. Pontos para captura de evidências

- `podman compose -p jurisdocs ps` com quatro serviços saudáveis;
- interface em `http://127.0.0.1:5174`;
- duas consultas consecutivas com `X-Cache: MISS` e `X-Cache: HIT`;
- saída de `pytest -q`;
- saída de `scripts/03_validar_fallback_redis.sh` com `X-Cache: BYPASS`.

# Pool Ensemble

[English](README.md)

Pool Ensemble transforma o champion pool de um jogador de League of Legends em um card compartilhável de elenco. Informe um Riot ID e uma região para montar o pool ponderado pela maestria de campeões, extrair o vetor de estilo e classificar de forma determinística em um arquétipo com imagem pronta para postar.

## Como funciona

O backend consulta o PUUID da conta via Account-v1 e a maestria via Champion-Mastery-v4, ponderando os principais campeões por pontos de maestria e recência (`lastPlayTime`). O domínio calcula o vetor de características do pool, pontua contra os arquétipos em YAML usando similaridade de cosseno e regras explícitas, escolhe frases com semente derivada do hash do PUUID e renderiza o PNG no servidor.

## Rodar localmente

Pré-requisitos: Python 3.12, `uv`, Node.js 22 e opcionalmente Docker.

```bash
cp .env.example .env
cd apps/api && uv sync --dev && uv run uvicorn pool_ensemble.main:app --reload
cd apps/web && npm install && npm run dev
```

Ou suba a stack completa com Docker Compose:

```bash
cp .env.example .env
docker compose up --build
```

Para rodar lint, tipos e testes nos dois apps:

```bash
make check
```

## Estrutura do repositório

```text
apps/api/     Serviço FastAPI, domínio puro, cliente Riot e renderizador de card
apps/web/     SPA em React + TypeScript + Vite
data/         Perfis de campeões, arquétipos e bancos de frases em YAML
scripts/      Validação de conteúdo, sync com Data Dragon e simulação de pools
docs/         Arquitetura, ADRs, algoritmo de classificação e conformidade
```

## Contribuição

Contribuições com novos arquétipos, perfis de campeão, frases e correções são bem-vindas. Leia [CONTRIBUTING.md](CONTRIBUTING.md) antes de abrir um pull request.

## Aviso legal

Pool Ensemble não é endossado pela Riot Games e não reflete as visões ou opiniões da Riot Games ou de qualquer pessoa oficialmente envolvida na produção ou gerenciamento de propriedades da Riot Games. Riot Games e todas as propriedades associadas são marcas comerciais ou marcas registradas da Riot Games, Inc.

Pool Ensemble foi criado sob a política "Legal Jibber Jabber" da Riot Games utilizando ativos de propriedade da Riot Games. A Riot Games não endossa nem patrocina este projeto. Consulte [docs/legal.md](docs/legal.md) para detalhes sobre conformidade e privacidade.

## Licença

MIT. Veja [LICENSE](LICENSE).

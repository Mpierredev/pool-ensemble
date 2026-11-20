# Contributing

Thanks for helping improve Pool Ensemble.

## Prerequisites

- Python 3.12 and `uv`
- Node.js 22 LTS and `npm`

## Local setup

```bash
cp .env.example .env
cd apps/api && uv sync --dev
cd ../web && npm install
```

Run all checks from the repository root before opening a pull request:

```bash
make check
```

## Code and content standards

- Keep `apps/api/src/pool_ensemble/domain/` pure (no network calls, Redis, or global clock access).
- Keep code, technical documentation, and commit messages in English.
- Interface copy and card phrases live in `data/` and `apps/web/src/i18n/` in both `pt-BR` and `en`.
- Keep changes focused and include tests for new domain logic or bug fixes.
- Do not include API keys, tokens, or real player PUUIDs in code, tests, or fixtures.

## Commit style

Use short imperative messages in English, starting with a lowercase letter, up to 72 characters, and without a trailing period:

- `add two-window rate limiter`
- `fix region mapping for oce`
- `split card layout from palette`

Keep one logical change per commit.

## Pull requests

1. Ensure `make check` passes locally.
2. Describe what changed and why in the pull request template.
3. Update relevant documentation when changing public behavior or YAML schemas.

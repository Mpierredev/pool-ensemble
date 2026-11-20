# Pool Ensemble

[Português (pt-BR)](README.pt-BR.md)

Pool Ensemble turns a League of Legends champion pool into a shareable cast card. Enter a Riot ID and region, and the app builds a weighted pool from champion mastery, extracts playstyle features, and maps it deterministically to an archetype with a matching card image.

## How it works

The backend looks up the account PUUID via Riot Account-v1 and champion mastery via Champion-Mastery-v4, weighting the top champions by mastery points and recency (`lastPlayTime`). A pure domain pipeline computes the pool feature vector, scores it against versioned YAML archetype definitions using cosine similarity plus explicit requirement rules, selects seeded copy from YAML banks, and renders a PNG card on the server.

## Run locally

Prerequisites: Python 3.12, `uv`, Node.js 22, and optionally Docker.

```bash
cp .env.example .env
cd apps/api && uv sync --dev && uv run uvicorn pool_ensemble.main:app --reload
cd apps/web && npm install && npm run dev
```

Or run the full stack with Docker Compose:

```bash
cp .env.example .env
docker compose up --build
```

Run checks across both apps:

```bash
make check
```

## Repository layout

```text
apps/api/     FastAPI service, domain pipeline, Riot client, card renderer
apps/web/     React + TypeScript + Vite SPA
data/         Champion profiles, archetypes, and copy banks in YAML
scripts/      Content validation, Data Dragon sync, and pool balance simulation
docs/         Architecture notes, ADRs, classification details, and compliance
```

## Contributing

Contributions for new archetypes, champion profiles, copy lines, and bug fixes are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## Legal disclaimer

Pool Ensemble is not endorsed by Riot Games and does not reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games and all associated properties are trademarks or registered trademarks of Riot Games, Inc.

Pool Ensemble was created under Riot Games' "Legal Jibber Jabber" policy using assets owned by Riot Games. Riot Games does not endorse or sponsor this project. See [docs/legal.md](docs/legal.md) for details on compliance and data handling.

## License

MIT. See [LICENSE](LICENSE).

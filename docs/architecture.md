# Architecture

Pool Ensemble is structured as a modular monolith in Python (`apps/api`) paired with a static React SPA (`apps/web`) and versioned YAML content (`data/`).

## Overview

```text
Browser (SPA)
   |  POST /api/analyze {riot_id, region}
   v
FastAPI Service (apps/api)
   |-- Per-IP RateLimiter
   |-- ResultCache (Redis)  --hit--> response
   |-- RiotClient (httpx async + global limiter + retry)
   |        |-- Account-v1 (regional routing)
   |        '-- Champion-Mastery-v4 (platform routing)
   |-- PoolBuilder       -> weighted champion pool
   |-- FeatureExtractor  -> feature vector
   |-- Classifier        -> primary/secondary archetypes + percentages
   |-- CopyEngine        -> seeded title, subtitle, and line
   |-- CardRenderer      -> PNG card (Pillow)
   '-- ResultStore (Redis, TTL) -> /p/{id}

Versioned static data
   data/champions/*.yaml        champion playstyle profiles
   data/archetypes/*.yaml       archetype weight vectors and rules
   data/copy/{pt-BR,en}/*.yaml  localized phrase banks
```

## Module boundaries

- `pool_ensemble.domain`: Pure functions and frozen data models. No network calls, no Redis access, no global clock reads. External inputs such as timestamps or hashes enter explicitly as parameters.
- `pool_ensemble.content`: Pydantic schemas and loaders for YAML data in `data/`. Adding champions, archetypes, or phrases never requires code changes.
- `pool_ensemble.riot`: Single integration point for Riot Games APIs, including region-to-platform routing tables, two-window rate limiting, and retry handling.
- `pool_ensemble.render`: Server-side PNG card rendering using Pillow and locally bundled fonts and icons.
- `pool_ensemble.storage`: Ephemeral Redis storage for cached results, share payloads, and aggregate counters using pipelined commands and TTLs.
- `pool_ensemble.share`: Minimal HTML page at `/p/{id}` with Open Graph and Twitter Card tags plus browser redirect to the SPA.
- `pool_ensemble.api`: HTTP routes, request validation, rate limiting, and error mapping.

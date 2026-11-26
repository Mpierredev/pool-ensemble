# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Pydantic content schemas, YAML loaders, 173 champion profiles (`16.23.1`), and 13 archetypes under `data/`.
- Pure domain pipeline (`build_pool`, `extract_features`, `classify_pool`, `detect_traits`, `analyze_pool`).
- Data Dragon sync, offline content validation, and 5,000-pool balance simulation scripts (`scripts/`).
- FastAPI backend (`apps/api`) with typed settings, CORS configuration, and `/health` endpoint.
- React, TypeScript, and Vite frontend (`apps/web`) with `pt-BR`/`en` i18n and Riot Games legal notice.
- GitHub Actions CI for linting, type checking, content validation, tests, and frontend build.

# ADR-007: Content as schema-validated YAML data

## Status

Accepted

## Context

The value of Pool Ensemble relies on champion coverage, balanced archetypes, and varied humor across languages. Hardcoding definitions in Python makes community contributions harder and mixes domain logic with editorial copy.

## Decision

Store all champion profiles, archetype definitions, and localized copy lines in `data/` as YAML files validated by Pydantic schemas during startup and in CI (`validate_content.py`).

## Consequences

- Adding a new archetype or updating copy requires only a YAML pull request with no Python edits.
- CI catches missing champion profiles, broken schemas, or incomplete translations before merge.
